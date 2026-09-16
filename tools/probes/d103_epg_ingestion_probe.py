#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

GUIDES_URL = "https://iptv-org.github.io/api/guides.json"
ENGLISH_PLAYLIST_URL = "https://iptv-org.github.io/iptv/languages/eng.m3u"
APP_ID = "com.safeiot.privyhub"
USER_AGENT_ANDROID_EPG = "PrivyHub/1.0"
USER_AGENT_ANDROID_TV = "PrivyHub/1.0 AndroidTV"
FETCH_TIMEOUT = 20.0
MAX_GUIDE_BYTES = 32 * 1024 * 1024
MAX_PLAYLIST_BYTES = 12 * 1024 * 1024
MAX_XML_BYTES = 64 * 1024 * 1024
MAX_XML_SAMPLE_MAPPINGS = 5
MAX_XML_SAMPLE_URLS = 3
IP_RE = re.compile(r"(?<![0-9A-Fa-f:])(?:\d{1,3}\.){3}\d{1,3}(?![0-9])")


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sanitize_text(value: str, limit: int = 400) -> str:
    clean = IP_RE.sub("<redacted-address>", value or "")
    clean = re.sub(r"\b[0-9A-Fa-f]{16,}\b", "<redacted-id>", clean)
    clean = " ".join(clean.split())
    return clean[:limit]


def url_descriptor(url: str) -> dict[str, Any]:
    try:
        parsed = urlsplit(url)
        return {
            "scheme": parsed.scheme.lower(),
            "host": parsed.hostname or "",
            "path_tail": Path(parsed.path).name[-120:],
            "query_present": bool(parsed.query),
            "url_sha256": hashlib.sha256(url.encode("utf-8", errors="replace")).hexdigest(),
        }
    except Exception:
        return {"parse_error": True, "url_sha256": hashlib.sha256(url.encode()).hexdigest()}


def fetch_bytes(url: str, *, user_agent: str, max_bytes: int) -> tuple[bytes | None, dict[str, Any]]:
    started = time.monotonic()
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Cache-Control": "no-cache",
        },
        method="GET",
    )
    meta: dict[str, Any] = {"url": url_descriptor(url), "max_bytes": max_bytes}
    try:
        with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT) as response:
            status = getattr(response, "status", None)
            headers = response.headers
            meta.update(
                {
                    "ok": status is None or 200 <= int(status) < 300,
                    "http_status": int(status) if status is not None else None,
                    "content_type": headers.get("Content-Type", ""),
                    "content_encoding": headers.get("Content-Encoding", ""),
                    "content_length_header": headers.get("Content-Length", ""),
                }
            )
            length_header = headers.get("Content-Length")
            if length_header:
                try:
                    if int(length_header) > max_bytes:
                        meta["error"] = "content_length_exceeds_probe_cap"
                        return None, meta
                except ValueError:
                    pass
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


def parse_guides_android_semantics(data: bytes) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    stats: dict[str, Any] = {
        "android_rule": "channel nonblank + sources array + prefer valid XML, otherwise valid GZIP; JSON unsupported; dedupe exact channel; prefer lang=en",
    }
    try:
        payload = json.loads(data.decode("utf-8"))
    except Exception as exc:
        stats.update({"parse_ok": False, "error": exc.__class__.__name__, "detail": sanitize_text(str(exc))})
        return {}, stats
    if not isinstance(payload, list):
        stats.update({"parse_ok": False, "error": "top_level_not_array", "top_level_type": type(payload).__name__})
        return {}, stats

    counts = Counter()
    formats = Counter()
    languages = Counter()
    best: dict[str, dict[str, str]] = {}
    duplicate_candidates = 0
    english_replacements = 0

    for item in payload:
        counts["entries_total"] += 1
        if not isinstance(item, dict):
            counts["entry_not_object"] += 1
            continue
        channel = str(item.get("channel", "") or "").strip()
        if not channel:
            counts["channel_blank"] += 1
            continue
        counts["channel_nonblank"] += 1
        language = str(item.get("lang", "") or "").strip()
        languages[language or "<blank>"] += 1
        site_id = str(item.get("site_id", "") or "").strip()
        sources = item.get("sources")
        if not isinstance(sources, list):
            counts["sources_missing_or_not_array"] += 1
            continue
        if not sources:
            counts["sources_empty"] += 1
            continue

        xml_url = None
        gzip_url = None
        for source in sources:
            counts["sources_seen"] += 1
            if not isinstance(source, dict):
                counts["source_not_object"] += 1
                continue
            fmt = str(source.get("format", "") or "").strip()
            formats[fmt or "<blank>"] += 1
            url = str(source.get("url", "") or "").strip()
            valid_url = url.startswith("http://") or url.startswith("https://")
            lower = fmt.lower()
            if lower == "xml":
                counts["format_xml"] += 1
                if valid_url:
                    counts["valid_xml_sources"] += 1
                    if xml_url is None:
                        xml_url = url
                else:
                    counts["xml_invalid_url"] += 1
            elif lower == "gzip":
                counts["format_gzip"] += 1
                if valid_url:
                    counts["valid_gzip_sources"] += 1
                    if gzip_url is None:
                        gzip_url = url
                else:
                    counts["gzip_invalid_url"] += 1
            elif lower == "json":
                counts["format_json_unsupported"] += 1
            else:
                counts["format_other_unsupported"] += 1

        selected_url = xml_url or gzip_url
        selected_format = "XML" if xml_url else ("GZIP" if gzip_url else "")
        if xml_url:
            counts["entries_selected_xml"] += 1
        elif gzip_url:
            counts["entries_selected_gzip"] += 1
        else:
            counts["entries_without_supported_source"] += 1
            continue
        counts["entries_with_supported_source"] += 1

        candidate = {
            "channel_id": channel,
            "site_id": site_id,
            "source_url": selected_url,
            "source_format": selected_format,
            "language": language,
        }
        existing = best.get(channel)
        if existing is not None:
            duplicate_candidates += 1
        if existing is None or (
            existing.get("language", "").lower() != "en" and language.lower() == "en"
        ):
            if existing is not None:
                english_replacements += 1
            best[channel] = candidate

    stats.update(
        {
            "parse_ok": True,
            "counts": dict(counts),
            "format_distribution": dict(formats.most_common(30)),
            "language_distribution": dict(languages.most_common(30)),
            "duplicate_channel_candidates": duplicate_candidates,
            "english_preference_replacements": english_replacements,
            "accepted_unique_mappings": len(best),
            "accepted_format_distribution": dict(
                Counter(v.get("source_format", "") for v in best.values()).most_common()
            ),
            "accepted_source_hosts": dict(
                Counter((urlsplit(v["source_url"]).hostname or "") for v in best.values()).most_common(30)
            ),
        }
    )
    return best, stats


ATTR_RE = re.compile(r'([A-Za-z0-9_-]+)="([^"]*)"')


def parse_playlist_channel_ids(data: bytes) -> tuple[set[str], dict[str, Any]]:
    text = data.decode("utf-8", errors="replace")
    ids: set[str] = set()
    counts = Counter()
    country = Counter()
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("#EXTINF:"):
            continue
        counts["extinf_entries"] += 1
        attrs = {m.group(1).lower(): m.group(2) for m in ATTR_RE.finditer(line)}
        channel_id = attrs.get("tvg-id", "").strip()
        if channel_id:
            counts["tvg_id_nonblank"] += 1
            ids.add(channel_id)
        else:
            counts["tvg_id_blank"] += 1
        c = attrs.get("tvg-country", "").strip().upper()
        if c:
            country[c] += 1
    return ids, {
        "parse_ok": True,
        "counts": dict(counts),
        "unique_nonblank_tvg_ids": len(ids),
        "country_distribution": dict(country.most_common(20)),
    }


def adb_device() -> tuple[list[str], dict[str, Any]]:
    info: dict[str, Any] = {"adb_available": False, "authorized_device_count": 0}
    adb = shutil.which("adb")
    if not adb:
        info["reason"] = "adb_not_found"
        return [], info
    info["adb_available"] = True
    proc = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=10)
    if proc.returncode != 0:
        info["reason"] = "adb_devices_failed"
        info["detail"] = sanitize_text(proc.stderr)
        return [], info
    serials = []
    unauthorized = 0
    for line in proc.stdout.splitlines()[1:]:
        if not line.strip() or "\t" not in line:
            continue
        serial, state = line.split("\t", 1)
        if state.strip() == "device":
            serials.append(serial.strip())
        else:
            unauthorized += 1
    info["authorized_device_count"] = len(serials)
    info["non_authorized_device_count"] = unauthorized
    if len(serials) != 1:
        info["reason"] = "need_exactly_one_authorized_device"
    else:
        info["reason"] = "ready"
    return serials, info


def adb_exec_out(serial: str, remote_path: str) -> tuple[bytes | None, str]:
    adb = shutil.which("adb")
    assert adb
    proc = subprocess.run(
        [adb, "-s", serial, "exec-out", "run-as", APP_ID, "cat", remote_path],
        capture_output=True,
        timeout=20,
    )
    if proc.returncode != 0:
        return None, "run_as_or_file_unavailable"
    return proc.stdout, "ok"


def snapshot_db(serial: str, db_name: str, temp_dir: Path) -> tuple[Path | None, dict[str, Any]]:
    result: dict[str, Any] = {"db_name": db_name, "snapshot_ok": False}
    main, status = adb_exec_out(serial, f"databases/{db_name}")
    if main is None or not main.startswith(b"SQLite format 3\x00"):
        result["reason"] = status if main is None else "not_sqlite_header"
        return None, result
    path = temp_dir / db_name
    path.write_bytes(main)
    result["db_bytes"] = len(main)
    result["db_sha256"] = sha256_bytes(main)
    wal, wal_status = adb_exec_out(serial, f"databases/{db_name}-wal")
    if wal:
        (temp_dir / f"{db_name}-wal").write_bytes(wal)
        result["wal_bytes"] = len(wal)
        result["wal_sha256"] = sha256_bytes(wal)
    else:
        result["wal_status"] = wal_status
    shm, _ = adb_exec_out(serial, f"databases/{db_name}-shm")
    if shm:
        (temp_dir / f"{db_name}-shm").write_bytes(shm)
        result["shm_bytes"] = len(shm)
    result["snapshot_ok"] = True
    return path, result


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return row is not None


def analyze_epg_db(path: Path) -> tuple[set[str], dict[str, Any]]:
    out: dict[str, Any] = {"read_ok": False}
    mappings: set[str] = set()
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            out["journal_mode"] = conn.execute("PRAGMA journal_mode").fetchone()[0]
            if table_exists(conn, "guide_mappings"):
                rows = conn.execute(
                    "SELECT channel_id, site_id, source_url, language, updated_at FROM guide_mappings"
                ).fetchall()
                mappings = {str(r[0]) for r in rows if r[0]}
                out["mapping_rows"] = len(rows)
                out["mapping_unique_channel_ids"] = len(mappings)
                out["mapping_languages"] = dict(Counter(str(r[3] or "") for r in rows).most_common(20))
                out["mapping_source_hosts"] = dict(
                    Counter((urlsplit(str(r[2] or "")).hostname or "") for r in rows).most_common(20)
                )
                timestamps = [int(r[4] or 0) for r in rows if int(r[4] or 0) > 0]
                if timestamps:
                    out["mapping_updated_at_min_ms"] = min(timestamps)
                    out["mapping_updated_at_max_ms"] = max(timestamps)
            if table_exists(conn, "programmes"):
                out["programme_rows"] = conn.execute("SELECT COUNT(*) FROM programmes").fetchone()[0]
                out["programme_distinct_channels"] = conn.execute(
                    "SELECT COUNT(DISTINCT channel_id) FROM programmes"
                ).fetchone()[0]
            if table_exists(conn, "meta"):
                rows = conn.execute("SELECT key, value FROM meta").fetchall()
                safe_meta = {}
                for key, value in rows:
                    key = str(key)
                    if key == "guide_mappings_refreshed_at" or key.startswith("programme_refresh_"):
                        if key == "guide_mappings_refreshed_at":
                            safe_meta[key] = str(value)
                out["meta"] = safe_meta
            out["read_ok"] = True
        finally:
            conn.close()
    except Exception as exc:
        out["error"] = exc.__class__.__name__
        out["detail"] = sanitize_text(str(exc))
    return mappings, out


def analyze_tv_db(path: Path) -> tuple[set[str], dict[str, Any]]:
    out: dict[str, Any] = {"read_ok": False}
    ids: set[str] = set()
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            if table_exists(conn, "streams"):
                out["stream_rows"] = conn.execute("SELECT COUNT(*) FROM streams").fetchone()[0]
                rows = conn.execute(
                    "SELECT DISTINCT channel_id FROM streams WHERE channel_id <> ''"
                ).fetchall()
                ids = {str(r[0]) for r in rows if r[0]}
                out["distinct_nonblank_channel_ids"] = len(ids)
                out["favorite_rows"] = conn.execute(
                    "SELECT COUNT(*) FROM streams WHERE favorite = 1"
                ).fetchone()[0]
                out["hidden_rows"] = conn.execute(
                    "SELECT COUNT(*) FROM streams WHERE manual_hidden = 1 OR auto_hidden = 1"
                ).fetchone()[0]
            if table_exists(conn, "providers"):
                out["provider_rows"] = conn.execute("SELECT COUNT(*) FROM providers").fetchone()[0]
                out["enabled_provider_rows"] = conn.execute(
                    "SELECT COUNT(*) FROM providers WHERE enabled = 1"
                ).fetchone()[0]
            out["read_ok"] = True
        finally:
            conn.close()
    except Exception as exc:
        out["error"] = exc.__class__.__name__
        out["detail"] = sanitize_text(str(exc))
    return ids, out


def parse_xmltv_date(raw: str) -> int:
    value = (raw or "").strip()
    if not value:
        return 0
    patterns = [
        ("%Y%m%d%H%M%S %z", True),
        ("%Y%m%d%H%M %z", True),
        ("%Y%m%d%H%M%S", False),
        ("%Y%m%d%H%M", False),
    ]
    for pattern, has_tz in patterns:
        try:
            parsed = dt.datetime.strptime(value, pattern)
            if not has_tz:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return int(parsed.timestamp() * 1000)
        except ValueError:
            pass
    return 0


def inspect_xml_sources(
    mappings: dict[str, dict[str, str]],
    catalog_ids: set[str],
) -> dict[str, Any]:
    matched = [m for cid, m in sorted(mappings.items()) if cid in catalog_ids]
    selected = matched[:MAX_XML_SAMPLE_MAPPINGS]
    if not selected:
        return {"attempted": False, "reason": "no_mapping_catalog_intersection"}

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for mapping in selected:
        if len(groups) >= MAX_XML_SAMPLE_URLS and mapping["source_url"] not in groups:
            continue
        groups[mapping["source_url"]].append(mapping)

    result: dict[str, Any] = {
        "attempted": True,
        "selected_mapping_count": sum(len(v) for v in groups.values()),
        "unique_source_url_count": len(groups),
        "sources": [],
    }
    now_ms = int(time.time() * 1000)
    earliest = now_ms - 2 * 60 * 60 * 1000
    latest = now_ms + 48 * 60 * 60 * 1000

    for source_url, source_mappings in groups.items():
        data, fetch_meta = fetch_bytes(
            source_url, user_agent=USER_AGENT_ANDROID_EPG, max_bytes=MAX_XML_BYTES
        )
        row: dict[str, Any] = {
            "source": url_descriptor(source_url),
            "fetch": fetch_meta,
            "mapping_count": len(source_mappings),
            "mappings": [],
        }
        if data is None:
            result["sources"].append(row)
            continue

        raw_is_gzip = data.startswith(b"\x1f\x8b")
        row["raw_gzip_magic"] = raw_is_gzip
        xml_data = data
        if raw_is_gzip:
            try:
                xml_data = gzip.decompress(data)
                row["gzip_decode_ok"] = True
                row["decoded_bytes"] = len(xml_data)
                if len(xml_data) > MAX_XML_BYTES:
                    row["parse_error"] = "decoded_xml_exceeds_probe_cap"
                    result["sources"].append(row)
                    continue
            except Exception as exc:
                row["gzip_decode_ok"] = False
                row["parse_error"] = exc.__class__.__name__
                result["sources"].append(row)
                continue

        wanted: dict[str, list[dict[str, str]]] = defaultdict(list)
        for m in source_mappings:
            wanted[m["channel_id"]].append(m)
            if m["site_id"]:
                wanted[m["site_id"]].append(m)
        per = {
            m["channel_id"]: {
                "channel_id_sha256": hashlib.sha256(m["channel_id"].encode()).hexdigest(),
                "site_id_present": bool(m["site_id"]),
                "programme_matches_total": 0,
                "programme_matches_window": 0,
                "date_parse_failures": 0,
            }
            for m in source_mappings
        }
        try:
            programme_seen = 0
            for event, elem in ET.iterparse(io.BytesIO(xml_data), events=("end",)):
                if elem.tag == "programme":
                    programme_seen += 1
                    xml_channel = elem.attrib.get("channel", "")
                    candidates = wanted.get(xml_channel, [])
                    if candidates:
                        start_ms = parse_xmltv_date(elem.attrib.get("start", ""))
                        stop_ms = parse_xmltv_date(elem.attrib.get("stop", ""))
                        for m in candidates:
                            stat = per[m["channel_id"]]
                            stat["programme_matches_total"] += 1
                            if start_ms <= 0:
                                stat["date_parse_failures"] += 1
                            if start_ms > 0 and stop_ms > earliest and start_ms < latest:
                                stat["programme_matches_window"] += 1
                    elem.clear()
            row["xml_parse_ok"] = True
            row["programme_elements_seen"] = programme_seen
        except Exception as exc:
            row["xml_parse_ok"] = False
            row["parse_error"] = exc.__class__.__name__
            row["parse_detail"] = sanitize_text(str(exc))
        row["mappings"] = list(per.values())
        result["sources"].append(row)
    return result


def classify(report: dict[str, Any]) -> str:
    guide_fetch = report["upstream"]["guides_fetch"]
    guide_parse = report["upstream"]["guides_parse"]
    if not guide_fetch.get("ok"):
        return "D103_GUIDES_FETCH_FAILED"
    if not guide_parse.get("parse_ok"):
        return "D103_GUIDES_PARSE_FAILED"

    total = guide_parse.get("counts", {}).get("entries_total", 0)
    accepted = guide_parse.get("accepted_unique_mappings", 0)
    if accepted <= 10 or (total >= 100 and accepted < max(10, int(total * 0.01))):
        return "D103_MAPPING_SOURCE_SCHEMA_OR_FORMAT_DIVERGENCE"

    adb = report.get("onn_snapshot", {})
    epg = adb.get("epg_db", {})
    if epg.get("read_ok"):
        local_count = epg.get("mapping_rows", 0)
        if local_count <= 10 and accepted >= 100:
            return "D103_ONN_MAPPING_CACHE_DIVERGED_FROM_UPSTREAM"

    identity = report["identity"]
    base_intersection = identity.get("guide_to_effective_catalog_intersection", 0)
    catalog_count = identity.get("effective_catalog_unique_ids", 0)
    if catalog_count >= 100 and base_intersection < max(5, int(catalog_count * 0.01)):
        return "D103_CATALOG_GUIDE_IDENTITY_MISMATCH"

    xml = report.get("xml_sample", {})
    if xml.get("attempted"):
        sources = xml.get("sources", [])
        fetched = [s for s in sources if s.get("fetch", {}).get("ok")]
        if sources and not fetched:
            return "D103_XML_SOURCE_FETCH_FAILURE"
        parsed = [s for s in fetched if s.get("xml_parse_ok")]
        if fetched and not parsed:
            return "D103_XML_SOURCE_FORMAT_FAILURE"
        if parsed:
            window_matches = sum(
                m.get("programme_matches_window", 0)
                for s in parsed for m in s.get("mappings", [])
            )
            if window_matches == 0:
                return "D103_XML_PROGRAMME_IDENTITY_OR_WINDOW_MISMATCH"
            if epg.get("read_ok") and epg.get("programme_rows", 0) == 0:
                return "D103_UPSTREAM_EPG_HEALTHY_ONN_CACHE_OR_RUNTIME_FAILURE"
            return "D103_UPSTREAM_EPG_PATH_HEALTHY"
    return "D103_EPG_BOUNDARY_NOT_CLASSIFIED"


def render_text(report: dict[str, Any]) -> str:
    gp = report["upstream"]["guides_parse"]
    pp = report["upstream"]["playlist_parse"]
    ident = report["identity"]
    onn = report.get("onn_snapshot", {})
    epg = onn.get("epg_db", {})
    tv = onn.get("tv_db", {})
    lines = [
        "PrivyHub D-103 D5.2 EPG ingestion probe",
        f"Generated: {report['generated_at']}",
        f"Classification: {report['classification']}",
        "",
        "GUIDES INPUT",
        f"  fetch_ok: {report['upstream']['guides_fetch'].get('ok')}",
        f"  entries_total: {gp.get('counts', {}).get('entries_total')}",
        f"  entries_with_supported_source: {gp.get('counts', {}).get('entries_with_supported_source')}",
        f"  entries_selected_xml: {gp.get('counts', {}).get('entries_selected_xml')}",
        f"  entries_selected_gzip: {gp.get('counts', {}).get('entries_selected_gzip')}",
        f"  accepted_unique_mappings: {gp.get('accepted_unique_mappings')}",
        f"  sources_missing_or_not_array: {gp.get('counts', {}).get('sources_missing_or_not_array')}",
        f"  entries_without_supported_source: {gp.get('counts', {}).get('entries_without_supported_source')}",
        "",
        "CATALOG IDENTITY",
        f"  playlist_fetch_ok: {report['upstream']['playlist_fetch'].get('ok')}",
        f"  playlist_unique_nonblank_tvg_ids: {pp.get('unique_nonblank_tvg_ids')}",
        f"  effective_catalog_source: {ident.get('effective_catalog_source')}",
        f"  effective_catalog_unique_ids: {ident.get('effective_catalog_unique_ids')}",
        f"  guide_to_effective_catalog_intersection: {ident.get('guide_to_effective_catalog_intersection')}",
        f"  intersection_case_insensitive: {ident.get('intersection_case_insensitive')}",
        "",
        "ONN READ-ONLY SNAPSHOT",
        f"  adb_status: {onn.get('adb', {}).get('reason')}",
        f"  epg_snapshot_ok: {onn.get('epg_snapshot', {}).get('snapshot_ok')}",
        f"  epg_mapping_rows: {epg.get('mapping_rows')}",
        f"  epg_programme_rows: {epg.get('programme_rows')}",
        f"  tv_snapshot_ok: {onn.get('tv_snapshot', {}).get('snapshot_ok')}",
        f"  tv_stream_rows: {tv.get('stream_rows')}",
        f"  tv_distinct_nonblank_channel_ids: {tv.get('distinct_nonblank_channel_ids')}",
        "",
        "XML SAMPLE",
        f"  attempted: {report.get('xml_sample', {}).get('attempted')}",
        f"  unique_source_url_count: {report.get('xml_sample', {}).get('unique_source_url_count')}",
    ]
    if report.get("notes"):
        lines += ["", "NOTES"] + [f"  - {x}" for x in report["notes"]]
    lines += [
        "",
        "Raw JSON retains detailed counters, source-format distributions, fetch metadata,",
        "and sampled programme-match measurements. No onn database was modified.",
    ]
    return "\n".join(lines) + "\n"


def self_test() -> int:
    sample = json.dumps(
        [
            {"channel": "A.us", "site_id": "a", "lang": "fr", "sources": [{"format": "XML", "url": "https://example.test/a.xml"}]},
            {"channel": "A.us", "site_id": "a2", "lang": "en", "sources": [{"format": "XML", "url": "https://example.test/a-en.xml"}]},
            {"channel": "B.us", "site_id": "b", "lang": "en", "sources": [{"format": "GZIP", "url": "https://example.test/b.xml.gz"}]},
            {"channel": "C.us", "site_id": "c", "lang": "en", "sources": [{"format": "JSON", "url": "https://example.test/c.json"}]},
            {"channel": "D.us", "site_id": "d", "lang": "en", "sources": [{"format": "GZIP", "url": "https://example.test/d.xml.gz"}, {"format": "XML", "url": "https://example.test/d.xml"}]},
            {"channel": "", "site_id": "", "lang": "en", "sources": [{"format": "XML", "url": "https://example.test/x.xml"}]},
        ]
    ).encode()
    mappings, stats = parse_guides_android_semantics(sample)
    assert list(mappings) == ["A.us", "B.us", "D.us"]
    assert mappings["A.us"]["language"] == "en"
    assert mappings["B.us"]["source_format"] == "GZIP"
    assert mappings["D.us"]["source_format"] == "XML"
    assert mappings["D.us"]["source_url"].endswith("/d.xml")
    assert stats["accepted_unique_mappings"] == 3
    playlist = b'#EXTM3U\n#EXTINF:-1 tvg-id="A.us" tvg-country="US",A\nhttps://x\n#EXTINF:-1,B\nhttps://y\n'
    ids, pstats = parse_playlist_channel_ids(playlist)
    assert ids == {"A.us"}
    assert pstats["counts"]["tvg_id_blank"] == 1
    assert parse_xmltv_date("20260916120000 +0000") > 0
    print("D103_PROBE_SELF_TEST_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="D-103 read-only D5.2 EPG ingestion diagnostic")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    repo = Path(args.repo).resolve()
    log_dir = repo / "logs" / "tv"
    log_dir.mkdir(parents=True, exist_ok=True)
    json_path = log_dir / "d103_epg_ingestion_probe.json"
    text_path = log_dir / "d103_epg_ingestion_probe.txt"

    report: dict[str, Any] = {
        "schema": 1,
        "probe": "D-103",
        "generated_at": utc_now_iso(),
        "read_only": True,
        "upstream": {},
        "identity": {},
        "onn_snapshot": {},
        "notes": [],
    }

    guide_data, guide_fetch = fetch_bytes(GUIDES_URL, user_agent=USER_AGENT_ANDROID_EPG, max_bytes=MAX_GUIDE_BYTES)
    report["upstream"]["guides_fetch"] = guide_fetch
    mappings: dict[str, dict[str, str]] = {}
    if guide_data is not None:
        mappings, guide_parse = parse_guides_android_semantics(guide_data)
    else:
        guide_parse = {"parse_ok": False, "error": "fetch_unavailable"}
    report["upstream"]["guides_parse"] = guide_parse

    playlist_data, playlist_fetch = fetch_bytes(
        ENGLISH_PLAYLIST_URL, user_agent=USER_AGENT_ANDROID_TV, max_bytes=MAX_PLAYLIST_BYTES
    )
    report["upstream"]["playlist_fetch"] = playlist_fetch
    playlist_ids: set[str] = set()
    if playlist_data is not None:
        playlist_ids, playlist_parse = parse_playlist_channel_ids(playlist_data)
    else:
        playlist_parse = {"parse_ok": False, "error": "fetch_unavailable"}
    report["upstream"]["playlist_parse"] = playlist_parse

    serials, adb_info = adb_device()
    report["onn_snapshot"]["adb"] = adb_info
    local_epg_ids: set[str] = set()
    local_tv_ids: set[str] = set()

    if len(serials) == 1:
        with tempfile.TemporaryDirectory(prefix="privyhub_d103_") as td:
            temp_dir = Path(td)
            epg_path, epg_snap = snapshot_db(serials[0], "privyhub_epg.db", temp_dir)
            report["onn_snapshot"]["epg_snapshot"] = epg_snap
            if epg_path is not None:
                local_epg_ids, epg_info = analyze_epg_db(epg_path)
                report["onn_snapshot"]["epg_db"] = epg_info
            else:
                report["onn_snapshot"]["epg_db"] = {"read_ok": False}

            tv_path, tv_snap = snapshot_db(serials[0], "privyhub_tv.db", temp_dir)
            report["onn_snapshot"]["tv_snapshot"] = tv_snap
            if tv_path is not None:
                local_tv_ids, tv_info = analyze_tv_db(tv_path)
                report["onn_snapshot"]["tv_db"] = tv_info
            else:
                report["onn_snapshot"]["tv_db"] = {"read_ok": False}
    else:
        report["onn_snapshot"]["epg_snapshot"] = {"snapshot_ok": False, "reason": "adb_not_ready"}
        report["onn_snapshot"]["tv_snapshot"] = {"snapshot_ok": False, "reason": "adb_not_ready"}
        report["onn_snapshot"]["epg_db"] = {"read_ok": False}
        report["onn_snapshot"]["tv_db"] = {"read_ok": False}

    effective_catalog = local_tv_ids if local_tv_ids else playlist_ids
    report["identity"] = {
        "effective_catalog_source": "onn_tv_db" if local_tv_ids else "iptv_org_english_playlist",
        "effective_catalog_unique_ids": len(effective_catalog),
        "guide_accepted_unique_ids": len(mappings),
        "guide_to_effective_catalog_intersection": len(set(mappings).intersection(effective_catalog)),
        "intersection_case_insensitive": len(
            {x.casefold() for x in mappings}.intersection({x.casefold() for x in effective_catalog})
        ),
        "onn_epg_mapping_to_onn_tv_intersection": (
            len(local_epg_ids.intersection(local_tv_ids)) if local_epg_ids and local_tv_ids else None
        ),
        "onn_epg_mapping_unique_ids": len(local_epg_ids) if local_epg_ids else None,
    }

    report["xml_sample"] = inspect_xml_sources(mappings, effective_catalog) if mappings and effective_catalog else {
        "attempted": False,
        "reason": "mapping_or_catalog_unavailable",
    }

    if not local_tv_ids:
        report["notes"].append("onn TV DB snapshot was unavailable; catalog identity used the same upstream English playlist as Android.")
    if not local_epg_ids:
        report["notes"].append("onn EPG DB snapshot was unavailable or contained no mappings; upstream measurements remain valid.")
    report["classification"] = classify(report)

    json_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    text = render_text(report)
    json_path.write_text(json_text, encoding="utf-8")
    text_path.write_text(text, encoding="utf-8")

    print(text, end="")
    print(f"JSON: {json_path}")
    print(f"TEXT: {text_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
