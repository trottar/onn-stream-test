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


def canonical_id(channel: str, feed: str) -> str:
    channel = (channel or "").strip()
    feed = (feed or "").strip()
    if not channel:
        return ""
    return f"{channel}@{feed}" if feed else channel


def split_stream_id(stream_id: str) -> tuple[str, str]:
    stream_id = (stream_id or "").strip()
    if not stream_id:
        return "", ""
    if "@" not in stream_id:
        return stream_id, ""
    channel, feed = stream_id.split("@", 1)
    return channel.strip(), feed.strip()


def meaningful(stream_id: str) -> bool:
    value = (stream_id or "").strip()
    return bool(value) and not value.startswith("tv_stream_")


def provider_label(provider_id: str) -> str:
    pid = (provider_id or "").strip()
    if pid in {BUILTIN_PROVIDER_ID, FREE_TV_PROVIDER_ID, FREECASTHUB_PROVIDER_ID}:
        return pid
    digest = hashlib.sha256(pid.encode("utf-8", errors="replace")).hexdigest()[:8]
    return f"custom_{digest}"


def fetch(url: str, max_bytes: int) -> tuple[bytes | None, dict[str, Any]]:
    started = time.monotonic()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PrivyHub-D107/1.0", "Cache-Control": "no-cache"},
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


def parse_guides(data: bytes) -> dict[str, Any]:
    payload = json.loads(data.decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("guides top level is not an array")

    canonical_all: set[str] = set()
    canonical_en: set[str] = set()
    bare_channels: set[str] = set()
    bare_channels_en: set[str] = set()
    feeds_by_channel: dict[str, set[str]] = defaultdict(set)
    english_feeds_by_channel: dict[str, set[str]] = defaultdict(set)
    sites_by_canonical: dict[str, set[str]] = defaultdict(set)
    source_backed_canonical: set[str] = set()

    counts = Counter()
    for item in payload:
        counts["entries_total"] += 1
        if not isinstance(item, dict):
            counts["entry_not_object"] += 1
            continue
        channel = str(item.get("channel", "") or "").strip()
        if not channel:
            counts["channel_blank"] += 1
            continue
        feed = str(item.get("feed", "") or "").strip()
        lang = str(item.get("lang", "") or "").strip().lower()
        site = clean(str(item.get("site", "") or "").strip() or "<blank>")
        cid = canonical_id(channel, feed)

        counts["channel_nonblank"] += 1
        if feed:
            counts["feed_nonblank_rows"] += 1
        else:
            counts["feed_blank_rows"] += 1

        canonical_all.add(cid)
        bare_channels.add(channel)
        feeds_by_channel[channel].add(feed)
        sites_by_canonical[cid].add(site)

        if lang == "en":
            counts["english_rows"] += 1
            canonical_en.add(cid)
            bare_channels_en.add(channel)
            english_feeds_by_channel[channel].add(feed)

        sources = item.get("sources")
        supported_source = False
        if isinstance(sources, list):
            for source in sources:
                if not isinstance(source, dict):
                    continue
                fmt = str(source.get("format", "") or "").strip().lower()
                url = str(source.get("url", "") or "").strip()
                if fmt in {"xml", "gzip"} and (
                    url.startswith("http://") or url.startswith("https://")
                ):
                    supported_source = True
                    break
        if supported_source:
            counts["source_backed_rows"] += 1
            source_backed_canonical.add(cid)

    return {
        "counts": dict(counts),
        "canonical_all": canonical_all,
        "canonical_en": canonical_en,
        "bare_channels": bare_channels,
        "bare_channels_en": bare_channels_en,
        "feeds_by_channel": feeds_by_channel,
        "english_feeds_by_channel": english_feeds_by_channel,
        "sites_by_canonical": sites_by_canonical,
        "source_backed_canonical": source_backed_canonical,
    }


def parse_playlist(data: bytes) -> dict[str, Any]:
    ids: set[str] = set()
    counts = Counter()
    for raw in data.decode("utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line.startswith("#EXTINF:"):
            continue
        counts["extinf_rows"] += 1
        attrs = {m.group(1).lower(): m.group(2) for m in ATTR_RE.finditer(line)}
        stream_id = attrs.get("tvg-id", "").strip()
        if not stream_id:
            counts["blank_tvg_id_rows"] += 1
            continue
        counts["nonblank_tvg_id_rows"] += 1
        channel, feed = split_stream_id(stream_id)
        if feed:
            counts["feed_bearing_rows"] += 1
        else:
            counts["channel_only_rows"] += 1
        ids.add(stream_id)
    return {"ids": ids, "counts": dict(counts)}


def identity_metrics(ids: set[str], guides: dict[str, Any]) -> dict[str, Any]:
    meaningful_ids = {x for x in ids if meaningful(x)}
    exact = meaningful_ids & guides["canonical_all"]
    exact_en = meaningful_ids & guides["canonical_en"]
    raw_bare = meaningful_ids & guides["bare_channels"]

    base_any: set[str] = set()
    blank_feed_fallback: set[str] = set()
    other_feed_only: set[str] = set()
    feed_bearing: set[str] = set()
    exact_feed_bearing: set[str] = set()
    channel_only: set[str] = set()
    exact_channel_only: set[str] = set()

    for stream_id in meaningful_ids:
        channel, feed = split_stream_id(stream_id)
        if not channel:
            continue
        if feed:
            feed_bearing.add(stream_id)
        else:
            channel_only.add(stream_id)

        feeds = guides["feeds_by_channel"].get(channel)
        if feeds is not None:
            base_any.add(stream_id)

        if stream_id in exact:
            if feed:
                exact_feed_bearing.add(stream_id)
            else:
                exact_channel_only.add(stream_id)
            continue

        if feeds is not None:
            if "" in feeds:
                blank_feed_fallback.add(stream_id)
            else:
                other_feed_only.add(stream_id)

    top_sites = Counter()
    for stream_id in exact:
        for site in guides["sites_by_canonical"].get(stream_id, set()):
            top_sites[site] += 1

    return {
        "unique_ids": len(ids),
        "unique_meaningful_ids": len(meaningful_ids),
        "unique_synthetic_ids": len(ids - meaningful_ids),
        "feed_bearing_ids": len(feed_bearing),
        "channel_only_ids": len(channel_only),
        "exact_canonical_matches": len(exact),
        "english_exact_canonical_matches": len(exact_en),
        "raw_bare_channel_exact_matches": len(raw_bare),
        "base_channel_has_any_guide": len(base_any),
        "blank_feed_fallback_candidates": len(blank_feed_fallback),
        "other_feed_only_candidates": len(other_feed_only),
        "feed_bearing_exact_matches": len(exact_feed_bearing),
        "channel_only_exact_matches": len(exact_channel_only),
        "exact_canonical_coverage_fraction": (
            round(len(exact) / len(meaningful_ids), 6) if meaningful_ids else None
        ),
        "english_exact_canonical_coverage_fraction": (
            round(len(exact_en) / len(meaningful_ids), 6) if meaningful_ids else None
        ),
        "feed_bearing_exact_coverage_fraction": (
            round(len(exact_feed_bearing) / len(feed_bearing), 6)
            if feed_bearing else None
        ),
        "base_channel_any_guide_coverage_fraction": (
            round(len(base_any) / len(meaningful_ids), 6) if meaningful_ids else None
        ),
        "top_sites_for_exact_canonical_matches": [
            {"site": site, "matched_ids": count}
            for site, count in top_sites.most_common(20)
        ],
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


def read_tv_db(serial: str) -> tuple[list[tuple[str, str]], dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="d107_tvdb_") as td:
        temp = Path(td)
        main = adb_cat(serial, "databases/privyhub_tv.db")
        if not main or not main.startswith(b"SQLite format 3\x00"):
            return [], {"snapshot_ok": False, "reason": "tv_db_unavailable"}
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
            finally:
                conn.close()
        except Exception as exc:
            return [], {
                "snapshot_ok": False,
                "reason": "sqlite_read_failed",
                "detail": clean(str(exc)),
            }
        streams = [(str(p or ""), str(c or "")) for p, c in rows]
        return streams, {
            "snapshot_ok": True,
            "stream_rows": len(streams),
            "db_bytes": len(main),
            "db_sha256": sha256(main),
        }


def provider_metrics(
    streams: list[tuple[str, str]],
    guides: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, set[str]] = defaultdict(set)
    all_ids: set[str] = set()
    for provider_id, stream_id in streams:
        stream_id = stream_id.strip()
        if not stream_id:
            continue
        grouped[provider_id].add(stream_id)
        all_ids.add(stream_id)

    providers = []
    for provider_id, ids in grouped.items():
        row = identity_metrics(ids, guides)
        row["provider"] = provider_label(provider_id)
        providers.append(row)
    providers.sort(key=lambda r: (-int(r["unique_ids"]), str(r["provider"])))

    return providers, identity_metrics(all_ids, guides)


def classify(playlist_metrics: dict[str, Any]) -> str:
    coverage = float(playlist_metrics.get("exact_canonical_coverage_fraction") or 0.0)
    bare = int(playlist_metrics.get("raw_bare_channel_exact_matches") or 0)
    canonical = int(playlist_metrics.get("exact_canonical_matches") or 0)
    if canonical > bare and coverage >= 0.50:
        return "D107_FEED_AWARE_CANONICAL_COVERAGE_HIGH"
    if canonical > bare and coverage >= 0.10:
        return "D107_FEED_AWARE_CANONICAL_COVERAGE_PARTIAL"
    if canonical > bare:
        return "D107_FEED_AWARE_CANONICALIZATION_MATERIAL_BUT_LOW"
    if canonical == 0:
        return "D107_FEED_AWARE_IDENTITY_INTERSECTION_ABSENT"
    return "D107_FEED_AWARE_IDENTITY_STILL_LOW"


def render(report: dict[str, Any]) -> str:
    g = report["guides"]
    p = report["english_playlist"]
    o = report["onn_catalog"]
    lines = [
        "PrivyHub D-107 D5.3 EPG feed-aware identity probe",
        f"Generated: {report['generated_at']}",
        f"Classification: {report['classification']}",
        "",
        "GUIDE IDENTITY MODEL",
        f"  fetch_ok: {report['guides_fetch'].get('ok')}",
        f"  entries_total: {g.get('entries_total')}",
        f"  unique_canonical_ids: {g.get('unique_canonical_ids')}",
        f"  unique_english_canonical_ids: {g.get('unique_english_canonical_ids')}",
        f"  unique_bare_channels: {g.get('unique_bare_channels')}",
        f"  feed_nonblank_rows: {g.get('feed_nonblank_rows')}",
        f"  feed_blank_rows: {g.get('feed_blank_rows')}",
        f"  source_backed_canonical_ids: {g.get('source_backed_canonical_ids')}",
        "",
        "BUILT-IN IPTV-ORG ENGLISH PLAYLIST",
        f"  fetch_ok: {report['playlist_fetch'].get('ok')}",
        f"  unique_tvg_ids: {p.get('unique_ids')}",
        f"  feed_bearing_ids: {p.get('feed_bearing_ids')}",
        f"  channel_only_ids: {p.get('channel_only_ids')}",
        f"  D106_raw_bare_channel_exact_matches: {p.get('raw_bare_channel_exact_matches')}",
        f"  feed_aware_exact_canonical_matches: {p.get('exact_canonical_matches')}",
        f"  english_exact_canonical_matches: {p.get('english_exact_canonical_matches')}",
        f"  exact_canonical_coverage_fraction: {p.get('exact_canonical_coverage_fraction')}",
        f"  feed_bearing_exact_coverage_fraction: {p.get('feed_bearing_exact_coverage_fraction')}",
        f"  base_channel_has_any_guide: {p.get('base_channel_has_any_guide')}",
        f"  blank_feed_fallback_candidates: {p.get('blank_feed_fallback_candidates')}",
        f"  other_feed_only_candidates: {p.get('other_feed_only_candidates')}",
        "",
        "ONN CATALOG",
        f"  adb_status: {report['adb'].get('reason')}",
        f"  tv_snapshot_ok: {report['tv_snapshot'].get('snapshot_ok')}",
        f"  unique_meaningful_ids: {o.get('unique_meaningful_ids')}",
        f"  unique_synthetic_ids: {o.get('unique_synthetic_ids')}",
        f"  feed_aware_exact_canonical_matches: {o.get('exact_canonical_matches')}",
        f"  exact_canonical_coverage_fraction: {o.get('exact_canonical_coverage_fraction')}",
        f"  base_channel_has_any_guide: {o.get('base_channel_has_any_guide')}",
        "",
        "PROVIDER BREAKDOWN",
    ]
    for row in report["providers"]:
        lines.append(
            f"  {row['provider']}: ids={row['unique_ids']}, meaningful={row['unique_meaningful_ids']}, "
            f"feed_ids={row['feed_bearing_ids']}, canonical_matches={row['exact_canonical_matches']}, "
            f"coverage={row['exact_canonical_coverage_fraction']}, "
            f"base_any={row['base_channel_has_any_guide']}"
        )
    lines += [
        "",
        "TOP SITES FOR BUILT-IN EXACT CANONICAL MATCHES",
    ]
    for row in p.get("top_sites_for_exact_canonical_matches", [])[:12]:
        lines.append(f"  {row['site']}: {row['matched_ids']} matched IDs")
    lines += [
        "",
        "Raw measurements outrank the classifier.",
        "No TV/EPG database was modified.",
        f"JSON: {report['json_path']}",
        f"TEXT: {report['text_path']}",
    ]
    return "\n".join(lines) + "\n"


def self_test() -> int:
    fixture = [
        {
            "channel": "A.us",
            "feed": "East",
            "lang": "en",
            "site": "alpha.example",
            "sources": [],
        },
        {
            "channel": "A.us",
            "feed": "West",
            "lang": "en",
            "site": "alpha.example",
            "sources": [],
        },
        {
            "channel": "B.us",
            "feed": None,
            "lang": "en",
            "site": "beta.example",
            "sources": [{"format": "XML", "url": "https://example.test/b.xml"}],
        },
    ]
    guides = parse_guides(json.dumps(fixture).encode())
    assert guides["canonical_all"] == {"A.us@East", "A.us@West", "B.us"}
    assert guides["bare_channels"] == {"A.us", "B.us"}
    assert guides["source_backed_canonical"] == {"B.us"}

    playlist = (
        '#EXTM3U\n'
        '#EXTINF:-1 tvg-id="A.us@East",A East\nhttps://a\n'
        '#EXTINF:-1 tvg-id="A.us@Other",A Other\nhttps://ao\n'
        '#EXTINF:-1 tvg-id="B.us@SD",B Feed\nhttps://b\n'
        '#EXTINF:-1 tvg-id="B.us",B Main\nhttps://bm\n'
    ).encode()
    parsed = parse_playlist(playlist)
    metrics = identity_metrics(parsed["ids"], guides)
    assert metrics["raw_bare_channel_exact_matches"] == 1
    assert metrics["exact_canonical_matches"] == 2
    assert metrics["feed_bearing_exact_matches"] == 1
    assert metrics["blank_feed_fallback_candidates"] == 1
    assert metrics["other_feed_only_candidates"] == 1
    assert metrics["base_channel_has_any_guide"] == 4
    assert classify(metrics).startswith("D107_FEED_AWARE_")

    assert canonical_id("BBCOne.uk", "EastMidlandsHD") == "BBCOne.uk@EastMidlandsHD"
    assert split_stream_id("BBCOne.uk@EastMidlandsHD") == ("BBCOne.uk", "EastMidlandsHD")
    assert split_stream_id("BBCOne.uk") == ("BBCOne.uk", "")

    print("D107_PROBE_SELF_TEST_OK")
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
    json_path = logs / "d107_epg_feed_identity_probe.json"
    text_path = logs / "d107_epg_feed_identity_probe.txt"

    guide_data, guide_fetch = fetch(GUIDES_URL, MAX_GUIDES_BYTES)
    playlist_data, playlist_fetch = fetch(ENGLISH_PLAYLIST_URL, MAX_PLAYLIST_BYTES)
    if not guide_data or not playlist_data:
        raise SystemExit("D-107 required upstream inputs could not be fetched")

    guides = parse_guides(guide_data)
    playlist = parse_playlist(playlist_data)
    playlist_metrics = identity_metrics(playlist["ids"], guides)

    serial, adb_info = adb_serial()
    if not serial:
        raise SystemExit("D-107 requires exactly one authorized ADB device")
    streams, tv_meta = read_tv_db(serial)
    if not tv_meta.get("snapshot_ok"):
        raise SystemExit("D-107 could not read the onn TV DB snapshot")
    providers, overall = provider_metrics(streams, guides)

    counts = guides["counts"]
    report = {
        "generated_at": now_iso(),
        "classification": classify(playlist_metrics),
        "guides_fetch": guide_fetch,
        "playlist_fetch": playlist_fetch,
        "adb": adb_info,
        "tv_snapshot": tv_meta,
        "guides": {
            "entries_total": counts.get("entries_total", 0),
            "unique_canonical_ids": len(guides["canonical_all"]),
            "unique_english_canonical_ids": len(guides["canonical_en"]),
            "unique_bare_channels": len(guides["bare_channels"]),
            "feed_nonblank_rows": counts.get("feed_nonblank_rows", 0),
            "feed_blank_rows": counts.get("feed_blank_rows", 0),
            "source_backed_canonical_ids": len(guides["source_backed_canonical"]),
        },
        "english_playlist": {
            **playlist["counts"],
            **playlist_metrics,
        },
        "onn_catalog": overall,
        "providers": providers,
    }
    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text = render(report)
    text_path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
