#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

GUIDES_URL = "https://iptv-org.github.io/api/guides.json"
ENGLISH_PLAYLIST_URL = "https://iptv-org.github.io/iptv/languages/eng.m3u"
PUBLIC_GUIDES_STATUS_URL = "https://raw.githubusercontent.com/iptv-org/epg/master/GUIDES.md"
APP_ID = "com.safeiot.privyhub"
FETCH_TIMEOUT = 20.0
MAX_GUIDES_BYTES = 32 * 1024 * 1024
MAX_PLAYLIST_BYTES = 12 * 1024 * 1024
MAX_STATUS_BYTES = 1024 * 1024
IPV4_RE = re.compile(r"(?<![0-9A-Fa-f:])(?:\d{1,3}\.){3}\d{1,3}(?![0-9])")
ATTR_RE = re.compile(r'([A-Za-z0-9_-]+)="([^"]*)"')


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sanitize_text(value: str, limit: int = 300) -> str:
    value = IPV4_RE.sub("<redacted-address>", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def url_descriptor(url: str) -> dict[str, Any]:
    parsed = urlsplit(url)
    host = sanitize_text(parsed.hostname or "")
    return {
        "scheme": parsed.scheme.lower(),
        "host": host,
        "path_tail": Path(parsed.path).name[-100:],
        "query_present": bool(parsed.query),
        "url_sha256": hashlib.sha256(url.encode("utf-8", errors="replace")).hexdigest(),
    }


def fetch_bytes(url: str, max_bytes: int) -> tuple[bytes | None, dict[str, Any]]:
    started = time.monotonic()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PrivyHub-D105/1.0", "Cache-Control": "no-cache"},
        method="GET",
    )
    meta: dict[str, Any] = {"url": url_descriptor(url), "max_bytes": max_bytes}
    try:
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as response:
            status = getattr(response, "status", None)
            meta.update(
                {
                    "ok": status is None or 200 <= int(status) < 300,
                    "http_status": int(status) if status is not None else None,
                    "content_type": response.headers.get("Content-Type", ""),
                    "content_encoding": response.headers.get("Content-Encoding", ""),
                }
            )
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = response.read(min(1024 * 1024, max_bytes + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > max_bytes:
                    meta["error"] = "response_exceeds_probe_cap"
                    return None, meta
            data = b"".join(chunks)
            meta["bytes"] = len(data)
            meta["sha256"] = sha256_bytes(data)
            meta["elapsed_ms"] = round((time.monotonic() - started) * 1000, 1)
            return data, meta
    except urllib.error.HTTPError as exc:
        meta.update(
            {
                "ok": False,
                "http_status": exc.code,
                "error": "http_error",
                "detail": sanitize_text(str(exc.reason)),
                "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
            }
        )
    except Exception as exc:
        meta.update(
            {
                "ok": False,
                "error": exc.__class__.__name__,
                "detail": sanitize_text(str(exc)),
                "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
            }
        )
    return None, meta


def parse_playlist_ids(data: bytes) -> set[str]:
    ids: set[str] = set()
    for raw in data.decode("utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line.startswith("#EXTINF:"):
            continue
        attrs = {m.group(1).lower(): m.group(2) for m in ATTR_RE.finditer(line)}
        cid = attrs.get("tvg-id", "").strip()
        if cid:
            ids.add(cid)
    return ids


def adb_device() -> tuple[str | None, dict[str, Any]]:
    info: dict[str, Any] = {"adb_available": False}
    adb = shutil.which("adb")
    if not adb:
        info["reason"] = "adb_not_found"
        return None, info
    info["adb_available"] = True
    proc = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=10)
    if proc.returncode != 0:
        info["reason"] = "adb_devices_failed"
        return None, info
    serials = []
    for line in proc.stdout.splitlines()[1:]:
        if "\t" not in line:
            continue
        serial, state = line.split("\t", 1)
        if state.strip() == "device":
            serials.append(serial.strip())
    info["authorized_device_count"] = len(serials)
    if len(serials) != 1:
        info["reason"] = "need_exactly_one_authorized_device"
        return None, info
    info["reason"] = "ready"
    return serials[0], info


def adb_cat(serial: str, remote_path: str) -> bytes | None:
    adb = shutil.which("adb")
    if not adb:
        return None
    proc = subprocess.run(
        [adb, "-s", serial, "exec-out", "run-as", APP_ID, "cat", remote_path],
        capture_output=True,
        timeout=20,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def snapshot_tv_catalog_ids(serial: str) -> tuple[set[str], dict[str, Any]]:
    result: dict[str, Any] = {"snapshot_ok": False}
    with tempfile.TemporaryDirectory(prefix="d105_tvdb_") as td:
        temp = Path(td)
        main = adb_cat(serial, "databases/privyhub_tv.db")
        if not main or not main.startswith(b"SQLite format 3\x00"):
            result["reason"] = "tv_db_unavailable"
            return set(), result
        db = temp / "privyhub_tv.db"
        db.write_bytes(main)
        wal = adb_cat(serial, "databases/privyhub_tv.db-wal")
        if wal:
            (temp / "privyhub_tv.db-wal").write_bytes(wal)
        shm = adb_cat(serial, "databases/privyhub_tv.db-shm")
        if shm:
            (temp / "privyhub_tv.db-shm").write_bytes(shm)
        try:
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            try:
                rows = conn.execute(
                    "SELECT channel_id FROM streams WHERE channel_id IS NOT NULL AND TRIM(channel_id) <> ''"
                ).fetchall()
            finally:
                conn.close()
        except Exception as exc:
            result["reason"] = "sqlite_read_failed"
            result["detail"] = sanitize_text(str(exc))
            return set(), result
        ids = {str(row[0]).strip() for row in rows if row and str(row[0]).strip()}
        result.update(
            {
                "snapshot_ok": True,
                "stream_rows_with_nonblank_channel_id": len(rows),
                "unique_nonblank_channel_ids": len(ids),
                "db_bytes": len(main),
                "db_sha256": sha256_bytes(main),
            }
        )
        return ids, result


def parse_public_guides_status(data: bytes | None) -> dict[str, Any]:
    if not data:
        return {"parse_ok": False}
    text = data.decode("utf-8", errors="replace")
    rows = re.findall(r"<tr>(.*?)</tr>", text, flags=re.S)
    green_workers = 0
    green_channels = 0
    listed_workers = 0
    red_workers = 0
    for row in rows:
        if "<td>" not in row:
            continue
        listed_workers += 1
        if "🟢" in row:
            green_workers += 1
            m = re.search(r'<td align="right">(\d+)</td>', row)
            if m:
                green_channels += int(m.group(1))
        elif "🔴" in row:
            red_workers += 1
    return {
        "parse_ok": True,
        "listed_workers": listed_workers,
        "green_workers": green_workers,
        "green_worker_channels": green_channels,
        "red_workers": red_workers,
    }


def source_is_supported(source: Any) -> bool:
    if not isinstance(source, dict):
        return False
    fmt = str(source.get("format", "") or "").strip().lower()
    url = str(source.get("url", "") or "").strip()
    return fmt in {"xml", "gzip"} and (url.startswith("http://") or url.startswith("https://"))


def analyze_guides(data: bytes, catalog_ids: set[str]) -> dict[str, Any]:
    payload = json.loads(data.decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("guides top level is not an array")

    catalog_lower = {x.lower(): x for x in catalog_ids}
    entries_total = 0
    channel_nonblank = 0
    unique_guide_ids: set[str] = set()
    exact_match_ids: set[str] = set()
    ci_match_ids: set[str] = set()
    english_exact_ids: set[str] = set()
    supported_source_exact_ids: set[str] = set()
    metadata_rows_exact = 0
    supported_rows_exact = 0
    sites_unique_ids: dict[str, set[str]] = defaultdict(set)
    sites_rows = Counter()
    langs_rows = Counter()
    formats = Counter()
    rows_with_any_source = 0
    rows_with_supported_source = 0

    for item in payload:
        entries_total += 1
        if not isinstance(item, dict):
            continue
        cid = str(item.get("channel", "") or "").strip()
        if not cid:
            continue
        channel_nonblank += 1
        unique_guide_ids.add(cid)

        site = sanitize_text(str(item.get("site", "") or "").strip() or "<blank>")
        lang = str(item.get("lang", "") or "").strip().lower()
        sources = item.get("sources")
        supported = False
        if isinstance(sources, list) and sources:
            rows_with_any_source += 1
            for source in sources:
                if isinstance(source, dict):
                    fmt = str(source.get("format", "") or "").strip() or "<blank>"
                    formats[fmt] += 1
                if source_is_supported(source):
                    supported = True
            if supported:
                rows_with_supported_source += 1

        if cid in catalog_ids:
            metadata_rows_exact += 1
            exact_match_ids.add(cid)
            sites_unique_ids[site].add(cid)
            sites_rows[site] += 1
            langs_rows[lang or "<blank>"] += 1
            if lang == "en":
                english_exact_ids.add(cid)
            if supported:
                supported_rows_exact += 1
                supported_source_exact_ids.add(cid)
        elif cid.lower() in catalog_lower:
            ci_match_ids.add(catalog_lower[cid.lower()])

    top_sites = [
        {
            "site": site,
            "unique_catalog_channels": len(ids),
            "matching_rows": sites_rows[site],
        }
        for site, ids in sorted(
            sites_unique_ids.items(),
            key=lambda kv: (-len(kv[1]), kv[0].lower()),
        )[:30]
    ]

    return {
        "entries_total": entries_total,
        "channel_nonblank": channel_nonblank,
        "unique_guide_channel_ids": len(unique_guide_ids),
        "rows_with_any_source": rows_with_any_source,
        "rows_with_supported_xml_or_gzip_source": rows_with_supported_source,
        "source_format_distribution": dict(formats.most_common(20)),
        "catalog_unique_ids": len(catalog_ids),
        "metadata_rows_exact_catalog_match": metadata_rows_exact,
        "metadata_unique_exact_catalog_match": len(exact_match_ids),
        "metadata_unique_case_insensitive_additional_match": len(ci_match_ids - exact_match_ids),
        "english_metadata_unique_exact_catalog_match": len(english_exact_ids),
        "supported_source_rows_exact_catalog_match": supported_rows_exact,
        "supported_source_unique_exact_catalog_match": len(supported_source_exact_ids),
        "exact_catalog_coverage_fraction": (
            round(len(exact_match_ids) / len(catalog_ids), 6) if catalog_ids else None
        ),
        "english_exact_catalog_coverage_fraction": (
            round(len(english_exact_ids) / len(catalog_ids), 6) if catalog_ids else None
        ),
        "top_sites_by_unique_catalog_channels": top_sites,
        "matched_language_distribution": dict(langs_rows.most_common(20)),
    }


def classify(analysis: dict[str, Any], public_status: dict[str, Any]) -> str:
    matched = int(analysis.get("metadata_unique_exact_catalog_match") or 0)
    live = int(analysis.get("supported_source_unique_exact_catalog_match") or 0)
    if matched <= 0:
        return "D105_METADATA_INTERSECTION_ABSENT"
    if live <= 0:
        return "D105_METADATA_MATCHES_BUT_PUBLIC_SOURCES_UNAVAILABLE"
    if public_status.get("parse_ok") and int(public_status.get("green_worker_channels") or 0) <= 2:
        return "D105_METADATA_MATCHES_PUBLIC_SOURCE_COVERAGE_MINIMAL"
    return "D105_PUBLIC_SOURCE_INTERSECTION_PRESENT"


def render_text(result: dict[str, Any]) -> str:
    a = result.get("analysis", {})
    p = result.get("public_guides_status", {})
    adb = result.get("adb", {})
    tv = result.get("tv_snapshot", {})
    lines = [
        "PrivyHub D-105 D5.3 EPG local-source viability probe",
        f"Generated: {result.get('generated_at')}",
        f"Classification: {result.get('classification')}",
        "",
        "UPSTREAM GUIDE METADATA",
        f"  fetch_ok: {result.get('guides_fetch', {}).get('ok')}",
        f"  entries_total: {a.get('entries_total')}",
        f"  unique_guide_channel_ids: {a.get('unique_guide_channel_ids')}",
        f"  rows_with_any_source: {a.get('rows_with_any_source')}",
        f"  rows_with_supported_xml_or_gzip_source: {a.get('rows_with_supported_xml_or_gzip_source')}",
        "",
        "EFFECTIVE CATALOG",
        f"  source: {result.get('effective_catalog_source')}",
        f"  unique_channel_ids: {a.get('catalog_unique_ids')}",
        f"  adb_status: {adb.get('reason')}",
        f"  onn_tv_snapshot_ok: {tv.get('snapshot_ok')}",
        "",
        "METADATA COVERAGE BEFORE SOURCE AVAILABILITY FILTER",
        f"  exact_unique_catalog_matches: {a.get('metadata_unique_exact_catalog_match')}",
        f"  exact_coverage_fraction: {a.get('exact_catalog_coverage_fraction')}",
        f"  english_exact_unique_catalog_matches: {a.get('english_metadata_unique_exact_catalog_match')}",
        f"  english_coverage_fraction: {a.get('english_exact_catalog_coverage_fraction')}",
        f"  supported_source_unique_catalog_matches: {a.get('supported_source_unique_exact_catalog_match')}",
        "",
        "PUBLIC EPG WORKER STATUS",
        f"  fetch_ok: {result.get('public_status_fetch', {}).get('ok')}",
        f"  listed_workers: {p.get('listed_workers')}",
        f"  green_workers: {p.get('green_workers')}",
        f"  green_worker_channels: {p.get('green_worker_channels')}",
        f"  red_workers: {p.get('red_workers')}",
        "",
        "TOP GUIDE SITES BY MATCHED CATALOG CHANNELS",
    ]
    for row in (a.get("top_sites_by_unique_catalog_channels") or [])[:12]:
        lines.append(
            f"  {row.get('site')}: {row.get('unique_catalog_channels')} unique channels "
            f"({row.get('matching_rows')} rows)"
        )
    lines += [
        "",
        "Raw JSON retains full counters and top-site coverage. No onn database was modified.",
        f"JSON: {result.get('json_path')}",
        f"TEXT: {result.get('text_path')}",
    ]
    return "\n".join(lines) + "\n"


def self_test() -> int:
    fixture = [
        {
            "channel": "A.us",
            "site": "alpha.example",
            "lang": "en",
            "sources": [],
        },
        {
            "channel": "A.us",
            "site": "beta.example",
            "lang": "es",
            "sources": [{"format": "JSON", "url": "https://example.test/a.json"}],
        },
        {
            "channel": "B.us",
            "site": "alpha.example",
            "lang": "en",
            "sources": [{"format": "GZIP", "url": "https://example.test/b.xml.gz"}],
        },
        {
            "channel": "C.us",
            "site": "gamma.example",
            "lang": "en",
            "sources": [{"format": "XML", "url": "https://example.test/c.xml"}],
        },
    ]
    a = analyze_guides(json.dumps(fixture).encode(), {"A.us", "B.us", "Z.us"})
    assert a["metadata_unique_exact_catalog_match"] == 2
    assert a["english_metadata_unique_exact_catalog_match"] == 2
    assert a["supported_source_unique_exact_catalog_match"] == 1
    assert a["top_sites_by_unique_catalog_channels"][0]["site"] == "alpha.example"
    status = parse_public_guides_status(
        b'<tr><td>x</td><td align="center">\xf0\x9f\x9f\xa2</td><td align="right">2</td></tr>'
    )
    assert status["green_workers"] == 1
    assert status["green_worker_channels"] == 2
    assert classify(a, status) == "D105_METADATA_MATCHES_PUBLIC_SOURCE_COVERAGE_MINIMAL"
    print("D105_PROBE_SELF_TEST_OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    repo = Path(args.repo).resolve()
    logs = repo / "logs/tv"
    logs.mkdir(parents=True, exist_ok=True)
    json_path = logs / "d105_epg_local_source_viability_probe.json"
    text_path = logs / "d105_epg_local_source_viability_probe.txt"

    guides_data, guides_meta = fetch_bytes(GUIDES_URL, MAX_GUIDES_BYTES)
    status_data, status_meta = fetch_bytes(PUBLIC_GUIDES_STATUS_URL, MAX_STATUS_BYTES)
    public_status = parse_public_guides_status(status_data)

    serial, adb_info = adb_device()
    tv_ids: set[str] = set()
    tv_meta: dict[str, Any] = {"snapshot_ok": False, "reason": "adb_not_ready"}
    if serial:
        tv_ids, tv_meta = snapshot_tv_catalog_ids(serial)

    effective_ids = tv_ids
    effective_source = "onn_tv_db" if tv_ids else "none"
    playlist_meta: dict[str, Any] = {"ok": None, "reason": "not_needed"}
    if not effective_ids:
        playlist_data, playlist_meta = fetch_bytes(ENGLISH_PLAYLIST_URL, MAX_PLAYLIST_BYTES)
        if playlist_data:
            effective_ids = parse_playlist_ids(playlist_data)
            effective_source = "english_playlist_fallback"

    if not guides_data:
        result = {
            "generated_at": utc_now_iso(),
            "classification": "D105_GUIDES_FETCH_FAILED",
            "guides_fetch": guides_meta,
            "public_status_fetch": status_meta,
            "public_guides_status": public_status,
            "adb": adb_info,
            "tv_snapshot": tv_meta,
            "playlist_fetch": playlist_meta,
            "effective_catalog_source": effective_source,
            "analysis": {},
        }
    elif not effective_ids:
        result = {
            "generated_at": utc_now_iso(),
            "classification": "D105_EFFECTIVE_CATALOG_UNAVAILABLE",
            "guides_fetch": guides_meta,
            "public_status_fetch": status_meta,
            "public_guides_status": public_status,
            "adb": adb_info,
            "tv_snapshot": tv_meta,
            "playlist_fetch": playlist_meta,
            "effective_catalog_source": effective_source,
            "analysis": {},
        }
    else:
        analysis = analyze_guides(guides_data, effective_ids)
        result = {
            "generated_at": utc_now_iso(),
            "classification": classify(analysis, public_status),
            "guides_fetch": guides_meta,
            "public_status_fetch": status_meta,
            "public_guides_status": public_status,
            "adb": adb_info,
            "tv_snapshot": tv_meta,
            "playlist_fetch": playlist_meta,
            "effective_catalog_source": effective_source,
            "analysis": analysis,
        }

    result["json_path"] = str(json_path)
    result["text_path"] = str(text_path)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text = render_text(result)
    text_path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
