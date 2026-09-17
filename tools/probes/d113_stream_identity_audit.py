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
import urllib.parse
import urllib.request

from collections import defaultdict
from pathlib import Path
from typing import Any

APP_ID = "com.safeiot.privyhub"
BUILTIN_PROVIDER_ID = "iptv_org"

FEEDS_URL = "https://iptv-org.github.io/api/feeds.json"
STREAMS_URL = "https://iptv-org.github.io/api/streams.json"

FETCH_TIMEOUT = 30.0
MAX_FEEDS_BYTES = 12 * 1024 * 1024
MAX_STREAMS_BYTES = 64 * 1024 * 1024

TARGET_BASE_CHANNEL = "10Bold.au"
TARGET_BAD_URL_SHA256 = (
    "3abb5a9b35973ed3ddf6f49b8b56e01d982deecc1d9ab380ea4ad53105de8500"
)

IPV4_RE = re.compile(r"(?<![0-9A-Fa-f:])(?:\d{1,3}\.){3}\d{1,3}(?![0-9])")
IPV6_RE = re.compile(
    r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{1,4}:){2,7}[0-9A-Fa-f]{0,4}(?![0-9A-Fa-f:])"
)
WORD_RE = re.compile(r"[a-z0-9]+")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def clean(value: str, limit: int = 500) -> str:
    text = IPV4_RE.sub("<redacted-address>", value or "")
    text = IPV6_RE.sub("<redacted-address>", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def normalize_words(value: str) -> tuple[str, ...]:
    return tuple(WORD_RE.findall((value or "").casefold()))


def contains_label(text: str, label: str) -> bool:
    label_words = normalize_words(label)
    if not label_words:
        return False
    # Short generic feed names like HD/SD are too noisy for a contradiction
    # classifier. They remain visible in raw feed metadata but are not used
    # for semantic display-name inference.
    if len("".join(label_words)) < 4:
        return False

    text_words = normalize_words(text)
    if len(label_words) == 1:
        return label_words[0] in text_words

    width = len(label_words)
    return any(
        text_words[i : i + width] == label_words
        for i in range(0, max(0, len(text_words) - width + 1))
    )


def canonical_id(channel: str, feed: str | None) -> str:
    channel = (channel or "").strip()
    feed = (feed or "").strip()
    if not channel:
        return ""
    return f"{channel}@{feed}" if feed else channel


def split_canonical(channel_id: str) -> tuple[str, str]:
    value = (channel_id or "").strip()
    if "@" not in value:
        return value, ""
    return tuple(value.rsplit("@", 1))  # type: ignore[return-value]


def fetch_json(url: str, max_bytes: int) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    started = time.monotonic()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PrivyHub-D113/1.0",
            "Cache-Control": "no-cache",
        },
        method="GET",
    )
    meta: dict[str, Any] = {"ok": False, "max_bytes": max_bytes}

    try:
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as response:
            status = getattr(response, "status", None)
            total = 0
            chunks: list[bytes] = []
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    meta["error"] = "response_exceeds_probe_cap"
                    return None, meta
                chunks.append(chunk)

            raw = b"".join(chunks)
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, list):
                raise ValueError("JSON root is not an array")

            rows = [item for item in payload if isinstance(item, dict)]
            meta.update(
                {
                    "ok": status is None or 200 <= int(status) < 300,
                    "http_status": int(status) if status is not None else None,
                    "bytes": len(raw),
                    "sha256": sha256_bytes(raw),
                    "rows": len(rows),
                    "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
                }
            )
            return rows, meta

    except urllib.error.HTTPError as exc:
        meta["http_status"] = exc.code
        meta["error"] = "http_error"
        meta["detail"] = clean(str(exc.reason))
    except Exception as exc:
        meta["error"] = exc.__class__.__name__
        meta["detail"] = clean(str(exc))

    meta["elapsed_ms"] = round((time.monotonic() - started) * 1000, 1)
    return None, meta


def adb_serial() -> tuple[str | None, dict[str, Any]]:
    adb = shutil.which("adb")
    if not adb:
        return None, {"adb_available": False, "reason": "adb_not_found"}

    proc = subprocess.run(
        [adb, "devices"],
        capture_output=True,
        text=True,
        timeout=15,
    )

    if proc.returncode != 0:
        return None, {
            "adb_available": True,
            "reason": "adb_devices_failed",
        }

    serials: list[str] = []
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
            "reason": (
                "ready"
                if len(serials) == 1
                else "need_exactly_one_authorized_device"
            ),
        },
    )


def adb_cat(serial: str, rel: str) -> bytes | None:
    adb = shutil.which("adb")
    if not adb:
        return None

    proc = subprocess.run(
        [
            adb,
            "-s",
            serial,
            "exec-out",
            "run-as",
            APP_ID,
            "cat",
            rel,
        ],
        capture_output=True,
        timeout=20,
    )
    return proc.stdout if proc.returncode == 0 else None


def snapshot_db(serial: str, db_name: str, temp: Path) -> tuple[Path | None, dict[str, Any]]:
    main = adb_cat(serial, f"databases/{db_name}")
    if not main or not main.startswith(b"SQLite format 3\x00"):
        return None, {
            "snapshot_ok": False,
            "reason": f"{db_name}_unavailable",
        }

    db_path = temp / db_name
    db_path.write_bytes(main)

    wal = adb_cat(serial, f"databases/{db_name}-wal")
    if wal:
        (temp / f"{db_name}-wal").write_bytes(wal)

    shm = adb_cat(serial, f"databases/{db_name}-shm")
    if shm:
        (temp / f"{db_name}-shm").write_bytes(shm)

    return db_path, {
        "snapshot_ok": True,
        "db_bytes": len(main),
        "db_sha256": sha256_bytes(main),
    }


def read_tv_streams(serial: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="d113_tvdb_") as td:
        temp = Path(td)
        db_path, meta = snapshot_db(serial, "privyhub_tv.db", temp)
        if db_path is None:
            return [], meta

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    """
                    SELECT
                        stream_id,
                        channel_id,
                        name,
                        url,
                        provider_id,
                        custom_name,
                        custom_url,
                        label,
                        country,
                        quality,
                        success_count,
                        failure_count,
                        consecutive_failures,
                        last_success,
                        last_failure
                    FROM streams
                    WHERE provider_id = ?
                    ORDER BY name COLLATE NOCASE, stream_id
                    """,
                    (BUILTIN_PROVIDER_ID,),
                ).fetchall()
            finally:
                conn.close()
        except Exception as exc:
            return [], {
                **meta,
                "snapshot_ok": False,
                "reason": "sqlite_read_failed",
                "detail": clean(str(exc)),
            }

        streams: list[dict[str, Any]] = []
        for row in rows:
            raw_url = str(row["url"] or "").strip()
            custom_url = str(row["custom_url"] or "").strip()
            effective_url = custom_url or raw_url
            raw_name = str(row["name"] or "").strip()
            custom_name = str(row["custom_name"] or "").strip()
            streams.append(
                {
                    "stream_id_hash": sha256_text(str(row["stream_id"] or ""))[:16],
                    "channel_id": str(row["channel_id"] or "").strip(),
                    "name": raw_name,
                    "effective_name": custom_name or raw_name,
                    "url_sha256": sha256_text(effective_url),
                    "url_host": urllib.parse.urlsplit(effective_url).hostname or "",
                    "has_custom_name": bool(custom_name),
                    "has_custom_url": bool(custom_url),
                    "label": str(row["label"] or "").strip(),
                    "country": str(row["country"] or "").strip(),
                    "quality": str(row["quality"] or "").strip(),
                    "success_count": int(row["success_count"] or 0),
                    "failure_count": int(row["failure_count"] or 0),
                    "consecutive_failures": int(row["consecutive_failures"] or 0),
                    "last_success": int(row["last_success"] or 0),
                    "last_failure": int(row["last_failure"] or 0),
                }
            )

        return streams, {
            **meta,
            "stream_rows": len(streams),
        }


def feed_indexes(
    rows: list[dict[str, Any]],
) -> tuple[
    dict[tuple[str, str], dict[str, Any]],
    dict[str, list[dict[str, Any]]],
]:
    exact: dict[tuple[str, str], dict[str, Any]] = {}
    by_channel: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for item in rows:
        channel = str(item.get("channel", "") or "").strip()
        feed_id = str(item.get("id", "") or "").strip()
        if not channel or not feed_id:
            continue
        exact[(channel, feed_id)] = item
        by_channel[channel].append(item)

    return exact, by_channel


def stream_indexes(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in rows:
        url = str(item.get("url", "") or "").strip()
        if url:
            by_url[sha256_text(url)].append(item)
    return by_url


def feed_labels(feed: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for value in (
        str(feed.get("id", "") or ""),
        str(feed.get("name", "") or ""),
    ):
        value = value.strip()
        if value:
            values.append(value)

    alt = feed.get("alt_names")
    if isinstance(alt, list):
        for value in alt:
            text = str(value or "").strip()
            if text:
                values.append(text)

    # Keep order but drop case-insensitive duplicates.
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def detect_feed_name_conflict(
    display_name: str,
    channel_id: str,
    exact_feeds: dict[tuple[str, str], dict[str, Any]],
    feeds_by_channel: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    base, feed_id = split_canonical(channel_id)
    if not base or not feed_id:
        return {
            "applicable": False,
            "reason": "channel_has_no_feed",
        }

    expected = exact_feeds.get((base, feed_id))
    if expected is None:
        return {
            "applicable": True,
            "feed_known": False,
            "conflict": False,
            "base_channel": base,
            "feed_id": feed_id,
        }

    expected_labels = feed_labels(expected)
    expected_mentions = [
        label for label in expected_labels if contains_label(display_name, label)
    ]

    conflicting_mentions: list[dict[str, str]] = []
    for other in feeds_by_channel.get(base, []):
        other_id = str(other.get("id", "") or "").strip()
        if not other_id or other_id == feed_id:
            continue
        for label in feed_labels(other):
            if contains_label(display_name, label):
                conflicting_mentions.append(
                    {
                        "feed_id": other_id,
                        "feed_name": str(other.get("name", "") or "").strip(),
                        "matched_label": label,
                    }
                )
                break

    return {
        "applicable": True,
        "feed_known": True,
        "conflict": bool(conflicting_mentions and not expected_mentions),
        "base_channel": base,
        "feed_id": feed_id,
        "feed_name": str(expected.get("name", "") or "").strip(),
        "expected_name_mentions": expected_mentions,
        "conflicting_mentions": conflicting_mentions,
    }


def official_stream_matches(
    stream: dict[str, Any],
    api_by_url: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    matches = []
    for item in api_by_url.get(str(stream["url_sha256"]), []):
        channel = str(item.get("channel", "") or "").strip()
        feed = str(item.get("feed", "") or "").strip()
        matches.append(
            {
                "canonical_id": canonical_id(channel, feed),
                "title": str(item.get("title", "") or "").strip(),
                "quality": str(item.get("quality", "") or "").strip(),
                "label": str(item.get("label", "") or "").strip(),
            }
        )
    return matches


def epg_cache_summary(repo: Path, channel_id: str) -> dict[str, Any] | None:
    digest = hashlib.sha256(channel_id.encode("utf-8")).hexdigest()
    path = repo / "data" / "epg" / "cache" / f"{digest}.json"
    if not path.is_file():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "read_ok": False,
            "error": exc.__class__.__name__,
        }

    programmes = payload.get("programmes")
    if not isinstance(programmes, list):
        programmes = []

    now_ms = int(time.time() * 1000)
    current = None
    for item in programmes:
        if not isinstance(item, dict):
            continue
        try:
            start = int(item.get("start_ms") or 0)
            stop = int(item.get("stop_ms") or 0)
        except (TypeError, ValueError):
            continue
        if start <= now_ms < stop:
            current = {
                "title": str(item.get("title", "") or "").strip(),
                "start_ms": start,
                "stop_ms": stop,
            }
            break

    source = payload.get("source")
    if not isinstance(source, dict):
        source = None

    return {
        "read_ok": True,
        "refreshed_at_ms": int(payload.get("refreshed_at_ms") or 0),
        "programme_count": len(programmes),
        "source": source,
        "current_programme": current,
    }


def audit(
    streams: list[dict[str, Any]],
    feeds: list[dict[str, Any]],
    api_streams: list[dict[str, Any]],
    repo: Path,
) -> dict[str, Any]:
    exact_feeds, feeds_by_channel = feed_indexes(feeds)
    api_by_url = stream_indexes(api_streams)

    feed_bearing = 0
    known_feed = 0
    conflicts: list[dict[str, Any]] = []
    target_rows: list[dict[str, Any]] = []
    official_url_matches = 0

    for stream in streams:
        channel_id = str(stream["channel_id"])
        base, feed_id = split_canonical(channel_id)
        if feed_id:
            feed_bearing += 1

        detection = detect_feed_name_conflict(
            str(stream["effective_name"]),
            channel_id,
            exact_feeds,
            feeds_by_channel,
        )
        if detection.get("feed_known"):
            known_feed += 1

        official = official_stream_matches(stream, api_by_url)
        if official:
            official_url_matches += 1

        item = {
            "channel_id": channel_id,
            "name": stream["name"],
            "effective_name": stream["effective_name"],
            "url_sha256": stream["url_sha256"],
            "url_host": stream["url_host"],
            "label": stream["label"],
            "quality": stream["quality"],
            "has_custom_name": stream["has_custom_name"],
            "has_custom_url": stream["has_custom_url"],
            "feed_check": detection,
            "official_stream_api_matches": official,
        }

        if detection.get("conflict"):
            conflicts.append(item)

        if base == TARGET_BASE_CHANNEL:
            item["matches_known_bad_url_hash"] = (
                stream["url_sha256"] == TARGET_BAD_URL_SHA256
            )
            item["epg_cache"] = epg_cache_summary(repo, channel_id)
            target_rows.append(item)

    conflicts.sort(
        key=lambda item: (
            str(item["channel_id"]).casefold(),
            str(item["effective_name"]).casefold(),
        )
    )

    target_conflict = any(
        item.get("feed_check", {}).get("conflict")
        for item in target_rows
    )
    target_bad_url = any(
        item.get("matches_known_bad_url_hash")
        for item in target_rows
    )

    return {
        "builtin_stream_rows": len(streams),
        "feed_bearing_stream_rows": feed_bearing,
        "feed_known_stream_rows": known_feed,
        "official_api_exact_url_matches": official_url_matches,
        "feed_name_conflict_rows": len(conflicts),
        "conflicts": conflicts,
        "target_10bold_rows": target_rows,
        "target_10bold_feed_conflict": target_conflict,
        "target_10bold_known_bad_url_hash_match": target_bad_url,
    }


def classify(report: dict[str, Any]) -> str:
    if not report.get("feeds_fetch", {}).get("ok"):
        return "D113_FEEDS_FETCH_FAILED"
    if not report.get("streams_fetch", {}).get("ok"):
        return "D113_STREAMS_FETCH_FAILED"
    if not report.get("tv_snapshot", {}).get("snapshot_ok"):
        return "D113_ONN_TV_SNAPSHOT_UNAVAILABLE"

    audit_data = report.get("audit") or {}
    if audit_data.get("target_10bold_feed_conflict"):
        return "D113_CONFIRMED_UPSTREAM_STREAM_IDENTITY_CONTRADICTION"
    if int(audit_data.get("feed_name_conflict_rows") or 0) > 0:
        return "D113_CATALOG_FEED_NAME_CONTRADICTIONS_PRESENT"
    return "D113_NO_FEED_NAME_CONTRADICTIONS_DETECTED"


def render(report: dict[str, Any]) -> str:
    audit_data = report.get("audit") or {}
    lines = [
        "PrivyHub D-113 D5 stream-identity audit",
        f"Generated: {report.get('generated_at')}",
        f"Classification: {report.get('classification')}",
        "",
        "UPSTREAM API",
        f"  feeds_fetch_ok: {report.get('feeds_fetch', {}).get('ok')}",
        f"  feeds_rows: {report.get('feeds_fetch', {}).get('rows')}",
        f"  streams_fetch_ok: {report.get('streams_fetch', {}).get('ok')}",
        f"  streams_rows: {report.get('streams_fetch', {}).get('rows')}",
        "",
        "ONN BUILT-IN IPTV-ORG CATALOG",
        f"  adb_status: {report.get('adb', {}).get('reason')}",
        f"  snapshot_ok: {report.get('tv_snapshot', {}).get('snapshot_ok')}",
        f"  builtin_stream_rows: {audit_data.get('builtin_stream_rows')}",
        f"  feed_bearing_stream_rows: {audit_data.get('feed_bearing_stream_rows')}",
        f"  feed_known_stream_rows: {audit_data.get('feed_known_stream_rows')}",
        f"  official_api_exact_url_matches: {audit_data.get('official_api_exact_url_matches')}",
        f"  feed_name_conflict_rows: {audit_data.get('feed_name_conflict_rows')}",
        "",
        "10 BOLD TARGET",
    ]

    targets = audit_data.get("target_10bold_rows") or []
    if not targets:
        lines.append("  <no current built-in 10Bold.au rows>")
    else:
        for item in targets:
            feed_check = item.get("feed_check") or {}
            official = item.get("official_stream_api_matches") or []
            cache = item.get("epg_cache")
            lines.extend(
                [
                    f"  name: {item.get('effective_name')}",
                    f"    channel_id: {item.get('channel_id')}",
                    f"    expected_feed_name: {feed_check.get('feed_name')}",
                    f"    conflicting_feed_mentions: {feed_check.get('conflicting_mentions')}",
                    f"    feed_name_conflict: {feed_check.get('conflict')}",
                    f"    official_api_matches: {official}",
                    f"    known_bad_url_hash_match: {item.get('matches_known_bad_url_hash')}",
                    f"    url_host: {item.get('url_host')}",
                    f"    epg_cache: {cache}",
                ]
            )

    lines += [
        "",
        "FIRST FEED-NAME CONTRADICTIONS",
    ]
    conflicts = audit_data.get("conflicts") or []
    if not conflicts:
        lines.append("  <none>")
    else:
        for item in conflicts[:20]:
            check = item.get("feed_check") or {}
            lines.append(
                "  "
                + f"{item.get('effective_name')} -> {item.get('channel_id')} "
                + f"(expected {check.get('feed_name')}, "
                + f"mentions {check.get('conflicting_mentions')})"
            )

    lines += [
        "",
        "Interpretation:",
        "  This probe checks catalog/feed metadata consistency only.",
        "  A playable stream is not automatically the channel its metadata claims it is.",
        "  No TV or EPG database/cache was modified.",
        f"JSON: {report.get('json_path')}",
        f"TEXT: {report.get('text_path')}",
    ]
    return "\n".join(lines) + "\n"


def self_test() -> int:
    feeds = [
        {
            "channel": "10Bold.au",
            "id": "Adelaide",
            "name": "Adelaide",
            "alt_names": [],
        },
        {
            "channel": "10Bold.au",
            "id": "Sydney",
            "name": "Sydney",
            "alt_names": [],
        },
    ]
    exact, by_channel = feed_indexes(feeds)

    bad = detect_feed_name_conflict(
        "10 Bold Adelaide",
        "10Bold.au@Sydney",
        exact,
        by_channel,
    )
    assert bad["conflict"] is True
    assert bad["feed_name"] == "Sydney"
    assert bad["conflicting_mentions"][0]["feed_id"] == "Adelaide"

    good = detect_feed_name_conflict(
        "10 Bold Sydney",
        "10Bold.au@Sydney",
        exact,
        by_channel,
    )
    assert good["conflict"] is False
    assert good["expected_name_mentions"] == ["Sydney"]

    neutral = detect_feed_name_conflict(
        "10 Bold",
        "10Bold.au@Sydney",
        exact,
        by_channel,
    )
    assert neutral["conflict"] is False

    assert canonical_id("10Bold.au", "Sydney") == "10Bold.au@Sydney"
    assert split_canonical("10Bold.au@Sydney") == ("10Bold.au", "Sydney")

    print("D113_PROBE_SELF_TEST_OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    repo = Path(args.repo).resolve()
    report: dict[str, Any] = {
        "generated_at": now_iso(),
    }

    serial, adb_info = adb_serial()
    report["adb"] = adb_info

    if serial:
        streams, tv_meta = read_tv_streams(serial)
    else:
        streams = []
        tv_meta = {
            "snapshot_ok": False,
            "reason": adb_info.get("reason"),
        }
    report["tv_snapshot"] = tv_meta

    feeds, feeds_meta = fetch_json(FEEDS_URL, MAX_FEEDS_BYTES)
    api_streams, streams_meta = fetch_json(STREAMS_URL, MAX_STREAMS_BYTES)
    report["feeds_fetch"] = feeds_meta
    report["streams_fetch"] = streams_meta

    if (
        tv_meta.get("snapshot_ok")
        and feeds is not None
        and api_streams is not None
    ):
        report["audit"] = audit(
            streams,
            feeds,
            api_streams,
            repo,
        )
    else:
        report["audit"] = {}

    report["classification"] = classify(report)

    logs = repo / "logs" / "tv"
    logs.mkdir(parents=True, exist_ok=True)
    json_path = logs / "d113_stream_identity_audit.json"
    text_path = logs / "d113_stream_identity_audit.txt"

    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)

    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    text = render(report)
    text_path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
