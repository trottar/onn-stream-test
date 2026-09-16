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

GUIDES_URL = "https://iptv-org.github.io/api/guides.json"
ENGLISH_PLAYLIST_URL = "https://iptv-org.github.io/iptv/languages/eng.m3u"
APP_ID = "com.safeiot.privyhub"
BUILTIN_PROVIDER_ID = "iptv_org"
FREE_TV_PROVIDER_ID = "free_tv"
FREECASTHUB_PROVIDER_ID = "freecasthub"
FETCH_TIMEOUT = 20.0
MAX_GUIDES_BYTES = 32 * 1024 * 1024
MAX_PLAYLIST_BYTES = 12 * 1024 * 1024
ATTR_RE = re.compile(r'([A-Za-z0-9_-]+)="([^"]*)"')
IPV4_RE = re.compile(r"(?<![0-9A-Fa-f:])(?:\d{1,3}\.){3}\d{1,3}(?![0-9])")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def clean(value: str, limit: int = 300) -> str:
    value = IPV4_RE.sub("<redacted-address>", value or "")
    return re.sub(r"\s+", " ", value).strip()[:limit]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, max_bytes: int) -> tuple[bytes | None, dict[str, Any]]:
    started = time.monotonic()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PrivyHub-D106/1.0", "Cache-Control": "no-cache"},
        method="GET",
    )
    meta: dict[str, Any] = {"ok": False, "max_bytes": max_bytes}
    try:
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as response:
            status = getattr(response, "status", None)
            meta["http_status"] = int(status) if status is not None else None
            meta["content_type"] = response.headers.get("Content-Type", "")
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
            meta["ok"] = status is None or 200 <= int(status) < 300
            meta["bytes"] = len(data)
            meta["sha256"] = sha256(data)
            meta["elapsed_ms"] = round((time.monotonic() - started) * 1000, 1)
            return data, meta
    except urllib.error.HTTPError as exc:
        meta["http_status"] = exc.code
        meta["error"] = "http_error"
        meta["detail"] = clean(str(exc.reason))
    except Exception as exc:
        meta["error"] = exc.__class__.__name__
        meta["detail"] = clean(str(exc))
    meta["elapsed_ms"] = round((time.monotonic() - started) * 1000, 1)
    return None, meta


def meaningful(channel_id: str) -> bool:
    cid = (channel_id or "").strip()
    return bool(cid) and not cid.startswith("tv_stream_")


def provider_label(provider_id: str) -> str:
    pid = (provider_id or "").strip()
    if pid in {BUILTIN_PROVIDER_ID, FREE_TV_PROVIDER_ID, FREECASTHUB_PROVIDER_ID}:
        return pid
    digest = hashlib.sha256(pid.encode("utf-8", errors="replace")).hexdigest()[:8]
    return f"custom_{digest}"


def parse_guides(data: bytes) -> dict[str, Any]:
    payload = json.loads(data.decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("guides top level is not an array")

    all_ids: set[str] = set()
    english_ids: set[str] = set()
    rows = 0
    english_rows = 0
    for item in payload:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("channel", "") or "").strip()
        if not cid:
            continue
        rows += 1
        all_ids.add(cid)
        if str(item.get("lang", "") or "").strip().lower() == "en":
            english_rows += 1
            english_ids.add(cid)
    return {
        "rows_with_channel_id": rows,
        "english_rows_with_channel_id": english_rows,
        "all_ids": all_ids,
        "english_ids": english_ids,
    }


def parse_playlist(data: bytes) -> dict[str, Any]:
    ids: set[str] = set()
    extinf = 0
    nonblank = 0
    blank = 0
    for raw in data.decode("utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line.startswith("#EXTINF:"):
            continue
        extinf += 1
        attrs = {m.group(1).lower(): m.group(2) for m in ATTR_RE.finditer(line)}
        cid = attrs.get("tvg-id", "").strip()
        if cid:
            nonblank += 1
            ids.add(cid)
        else:
            blank += 1
    return {
        "extinf_rows": extinf,
        "nonblank_tvg_id_rows": nonblank,
        "blank_tvg_id_rows": blank,
        "unique_ids": ids,
    }


def adb_serial() -> tuple[str | None, dict[str, Any]]:
    adb = shutil.which("adb")
    if not adb:
        return None, {"adb_available": False, "reason": "adb_not_found"}
    proc = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=10)
    if proc.returncode != 0:
        return None, {"adb_available": True, "reason": "adb_devices_failed"}
    serials = []
    for line in proc.stdout.splitlines()[1:]:
        if "\t" not in line:
            continue
        serial, state = line.split("\t", 1)
        if state.strip() == "device":
            serials.append(serial.strip())
    return (
        serials[0] if len(serials) == 1 else None,
        {
            "adb_available": True,
            "authorized_device_count": len(serials),
            "reason": "ready" if len(serials) == 1 else "need_exactly_one_authorized_device",
        },
    )


def adb_cat(serial: str, rel: str) -> bytes | None:
    adb = shutil.which("adb")
    if not adb:
        return None
    proc = subprocess.run(
        [adb, "-s", serial, "exec-out", "run-as", APP_ID, "cat", rel],
        capture_output=True,
        timeout=20,
    )
    return proc.stdout if proc.returncode == 0 else None


def read_tv_db(serial: str) -> tuple[list[tuple[str, str]], dict[str, int], dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="d106_tvdb_") as td:
        temp = Path(td)
        main = adb_cat(serial, "databases/privyhub_tv.db")
        if not main or not main.startswith(b"SQLite format 3\x00"):
            return [], {}, {"snapshot_ok": False, "reason": "tv_db_unavailable"}
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
                    "SELECT provider_id, channel_id FROM streams"
                ).fetchall()
                enabled_rows = conn.execute(
                    "SELECT provider_id, enabled FROM providers"
                ).fetchall()
            finally:
                conn.close()
        except Exception as exc:
            return [], {}, {
                "snapshot_ok": False,
                "reason": "sqlite_read_failed",
                "detail": clean(str(exc)),
            }
        streams = [(str(p or ""), str(c or "")) for p, c in rows]
        enabled = {str(p or ""): int(e or 0) for p, e in enabled_rows}
        return streams, enabled, {
            "snapshot_ok": True,
            "stream_rows": len(streams),
            "db_bytes": len(main),
            "db_sha256": sha256(main),
        }


def provider_stats(
    streams: list[tuple[str, str]],
    enabled_map: dict[str, int],
    guide_ids: set[str],
    english_guide_ids: set[str],
    playlist_ids: set[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for provider_id, channel_id in streams:
        grouped[provider_id].append(channel_id)

    all_nonblank: set[str] = set()
    all_meaningful: set[str] = set()
    all_synthetic: set[str] = set()
    result: list[dict[str, Any]] = []

    guide_lower = {x.lower() for x in guide_ids}
    for provider_id, ids in grouped.items():
        nonblank = [x.strip() for x in ids if x.strip()]
        meaningful_ids = {x for x in nonblank if meaningful(x)}
        synthetic_ids = {x for x in nonblank if x.startswith("tv_stream_")}
        unique_nonblank = set(nonblank)
        all_nonblank.update(unique_nonblank)
        all_meaningful.update(meaningful_ids)
        all_synthetic.update(synthetic_ids)

        exact = meaningful_ids & guide_ids
        english_exact = meaningful_ids & english_guide_ids
        ci_additional = {
            cid for cid in meaningful_ids
            if cid not in guide_ids and cid.lower() in guide_lower
        }
        playlist_overlap = meaningful_ids & playlist_ids

        result.append(
            {
                "provider": provider_label(provider_id),
                "enabled": bool(enabled_map.get(provider_id, 1)),
                "stream_rows": len(ids),
                "nonblank_id_rows": len(nonblank),
                "unique_nonblank_ids": len(unique_nonblank),
                "synthetic_id_rows": sum(1 for x in nonblank if x.startswith("tv_stream_")),
                "unique_synthetic_ids": len(synthetic_ids),
                "meaningful_id_rows": sum(1 for x in nonblank if meaningful(x)),
                "unique_meaningful_ids": len(meaningful_ids),
                "exact_guide_matches": len(exact),
                "english_exact_guide_matches": len(english_exact),
                "case_insensitive_additional_matches": len(ci_additional),
                "english_playlist_id_overlap": len(playlist_overlap),
                "guide_coverage_of_meaningful_fraction": (
                    round(len(exact) / len(meaningful_ids), 6)
                    if meaningful_ids else None
                ),
            }
        )

    result.sort(key=lambda x: (-int(x["stream_rows"]), str(x["provider"])))

    overall_exact = all_meaningful & guide_ids
    overall_english = all_meaningful & english_guide_ids
    return result, {
        "unique_nonblank_ids": len(all_nonblank),
        "unique_meaningful_ids": len(all_meaningful),
        "unique_synthetic_ids": len(all_synthetic),
        "synthetic_fraction_of_unique_nonblank": (
            round(len(all_synthetic) / len(all_nonblank), 6)
            if all_nonblank else None
        ),
        "exact_guide_matches": len(overall_exact),
        "english_exact_guide_matches": len(overall_english),
        "guide_coverage_of_meaningful_fraction": (
            round(len(overall_exact) / len(all_meaningful), 6)
            if all_meaningful else None
        ),
    }


def classify(
    builtin_playlist: dict[str, Any],
    providers: list[dict[str, Any]],
    overall: dict[str, Any],
) -> str:
    playlist_ids: set[str] = builtin_playlist["unique_ids"]
    playlist_exact = int(builtin_playlist["exact_guide_matches"])
    playlist_fraction = (
        playlist_exact / len(playlist_ids) if playlist_ids else 0.0
    )
    synthetic_fraction = float(overall.get("synthetic_fraction_of_unique_nonblank") or 0.0)

    if playlist_ids and playlist_fraction < 0.10:
        return "D106_BUILTIN_GUIDE_METADATA_COVERAGE_SPARSE"
    if synthetic_fraction >= 0.50:
        return "D106_SYNTHETIC_IDENTITY_DOMINATES_CATALOG"
    builtin = next((x for x in providers if x["provider"] == BUILTIN_PROVIDER_ID), None)
    if builtin and (builtin.get("guide_coverage_of_meaningful_fraction") or 0) >= 0.25:
        return "D106_PROVIDER_MIX_DILUTES_GUIDE_IDENTITY"
    return "D106_MIXED_GUIDE_IDENTITY_LIMITATION"


def render(report: dict[str, Any]) -> str:
    g = report["guides"]
    p = report["english_playlist"]
    o = report["overall_catalog"]
    lines = [
        "PrivyHub D-106 D5.3 EPG provider/identity probe",
        f"Generated: {report['generated_at']}",
        f"Classification: {report['classification']}",
        "",
        "GUIDE METADATA",
        f"  fetch_ok: {report['guides_fetch'].get('ok')}",
        f"  unique_guide_channel_ids: {g.get('unique_guide_channel_ids')}",
        f"  unique_english_guide_channel_ids: {g.get('unique_english_guide_channel_ids')}",
        "",
        "BUILT-IN IPTV-ORG ENGLISH PLAYLIST",
        f"  fetch_ok: {report['playlist_fetch'].get('ok')}",
        f"  extinf_rows: {p.get('extinf_rows')}",
        f"  unique_tvg_ids: {p.get('unique_tvg_ids')}",
        f"  blank_tvg_id_rows: {p.get('blank_tvg_id_rows')}",
        f"  exact_guide_matches: {p.get('exact_guide_matches')}",
        f"  english_exact_guide_matches: {p.get('english_exact_guide_matches')}",
        f"  exact_guide_coverage_fraction: {p.get('exact_guide_coverage_fraction')}",
        "",
        "ONN CATALOG IDENTITY QUALITY",
        f"  adb_status: {report['adb'].get('reason')}",
        f"  tv_snapshot_ok: {report['tv_snapshot'].get('snapshot_ok')}",
        f"  stream_rows: {report['tv_snapshot'].get('stream_rows')}",
        f"  unique_nonblank_ids: {o.get('unique_nonblank_ids')}",
        f"  unique_meaningful_ids: {o.get('unique_meaningful_ids')}",
        f"  unique_synthetic_ids: {o.get('unique_synthetic_ids')}",
        f"  synthetic_fraction_of_unique_nonblank: {o.get('synthetic_fraction_of_unique_nonblank')}",
        f"  exact_guide_matches: {o.get('exact_guide_matches')}",
        f"  guide_coverage_of_meaningful_fraction: {o.get('guide_coverage_of_meaningful_fraction')}",
        "",
        "PROVIDER BREAKDOWN",
    ]
    for row in report["providers"]:
        lines += [
            f"  {row['provider']}: streams={row['stream_rows']}, "
            f"meaningful_unique={row['unique_meaningful_ids']}, "
            f"synthetic_unique={row['unique_synthetic_ids']}, "
            f"guide_matches={row['exact_guide_matches']}, "
            f"coverage={row['guide_coverage_of_meaningful_fraction']}, "
            f"playlist_overlap={row['english_playlist_id_overlap']}"
        ]
    lines += [
        "",
        "No TV/EPG database was modified.",
        f"JSON: {report['json_path']}",
        f"TEXT: {report['text_path']}",
    ]
    return "\n".join(lines) + "\n"


def self_test() -> int:
    guides = [
        {"channel": "A.us", "lang": "en"},
        {"channel": "B.us", "lang": "en"},
        {"channel": "C.fr", "lang": "fr"},
    ]
    parsed = parse_guides(json.dumps(guides).encode())
    assert parsed["all_ids"] == {"A.us", "B.us", "C.fr"}
    assert parsed["english_ids"] == {"A.us", "B.us"}

    playlist = (
        '#EXTM3U\n'
        '#EXTINF:-1 tvg-id="A.us",A\nhttps://a\n'
        '#EXTINF:-1 tvg-id="",No ID\nhttps://x\n'
        '#EXTINF:-1 tvg-id="Z.us",Z\nhttps://z\n'
    ).encode()
    pl = parse_playlist(playlist)
    assert pl["extinf_rows"] == 3
    assert pl["blank_tvg_id_rows"] == 1
    assert pl["unique_ids"] == {"A.us", "Z.us"}

    streams = [
        ("iptv_org", "A.us"),
        ("iptv_org", "tv_stream_123"),
        ("free_tv", "B.us"),
        ("custom", "tv_stream_456"),
    ]
    providers, overall = provider_stats(
        streams, {"iptv_org": 1, "free_tv": 1, "custom": 1},
        parsed["all_ids"], parsed["english_ids"], pl["unique_ids"]
    )
    assert overall["unique_nonblank_ids"] == 4
    assert overall["unique_meaningful_ids"] == 2
    assert overall["unique_synthetic_ids"] == 2
    assert overall["exact_guide_matches"] == 2

    built = dict(pl)
    built["exact_guide_matches"] = len(pl["unique_ids"] & parsed["all_ids"])
    built["english_exact_guide_matches"] = len(pl["unique_ids"] & parsed["english_ids"])
    assert classify(built, providers, overall) != ""
    print("D106_PROBE_SELF_TEST_OK")
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
    json_path = logs / "d106_epg_provider_identity_probe.json"
    text_path = logs / "d106_epg_provider_identity_probe.txt"

    guide_data, guide_fetch = fetch(GUIDES_URL, MAX_GUIDES_BYTES)
    playlist_data, playlist_fetch = fetch(ENGLISH_PLAYLIST_URL, MAX_PLAYLIST_BYTES)
    if not guide_data or not playlist_data:
        raise SystemExit("D-106 required upstream inputs could not be fetched")

    guides = parse_guides(guide_data)
    playlist = parse_playlist(playlist_data)

    serial, adb_info = adb_serial()
    if not serial:
        raise SystemExit("D-106 requires exactly one authorized ADB device")
    streams, enabled_map, tv_meta = read_tv_db(serial)
    if not tv_meta.get("snapshot_ok"):
        raise SystemExit("D-106 could not read the onn TV DB snapshot")

    providers, overall = provider_stats(
        streams,
        enabled_map,
        guides["all_ids"],
        guides["english_ids"],
        playlist["unique_ids"],
    )

    playlist_exact = playlist["unique_ids"] & guides["all_ids"]
    playlist_english_exact = playlist["unique_ids"] & guides["english_ids"]
    builtin_playlist = {
        "extinf_rows": playlist["extinf_rows"],
        "nonblank_tvg_id_rows": playlist["nonblank_tvg_id_rows"],
        "blank_tvg_id_rows": playlist["blank_tvg_id_rows"],
        "unique_tvg_ids": len(playlist["unique_ids"]),
        "unique_ids": playlist["unique_ids"],
        "exact_guide_matches": len(playlist_exact),
        "english_exact_guide_matches": len(playlist_english_exact),
        "exact_guide_coverage_fraction": (
            round(len(playlist_exact) / len(playlist["unique_ids"]), 6)
            if playlist["unique_ids"] else None
        ),
        "english_guide_coverage_fraction": (
            round(len(playlist_english_exact) / len(playlist["unique_ids"]), 6)
            if playlist["unique_ids"] else None
        ),
    }

    report = {
        "generated_at": now_iso(),
        "guides_fetch": guide_fetch,
        "playlist_fetch": playlist_fetch,
        "adb": adb_info,
        "tv_snapshot": tv_meta,
        "guides": {
            "rows_with_channel_id": guides["rows_with_channel_id"],
            "english_rows_with_channel_id": guides["english_rows_with_channel_id"],
            "unique_guide_channel_ids": len(guides["all_ids"]),
            "unique_english_guide_channel_ids": len(guides["english_ids"]),
        },
        "english_playlist": {
            k: v for k, v in builtin_playlist.items() if k != "unique_ids"
        },
        "overall_catalog": overall,
        "providers": providers,
    }
    report["classification"] = classify(builtin_playlist, providers, overall)
    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text = render(report)
    text_path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
