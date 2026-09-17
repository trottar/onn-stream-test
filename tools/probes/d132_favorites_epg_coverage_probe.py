#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

PACKAGE = "com.safeiot.privyhub"
CONTROL_BASE = "http://127.0.0.1:8765"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024

CLASS_COMPLETE = "D132_FAVORITES_GUIDE_COVERAGE_COMPLETE"
CLASS_GAPS = "D132_FAVORITES_GUIDE_GAPS_CLASSIFIED"
CLASS_NONE = "D132_NO_VISIBLE_FAVORITES"


def adb_target() -> str:
    adb = shutil.which("adb")
    if not adb:
        raise RuntimeError("adb not found")
    result = subprocess.run(
        [adb, "devices"],
        check=True,
        text=True,
        capture_output=True,
        timeout=10,
    )
    devices = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if (
            len(parts) >= 2
            and parts[1] == "device"
            and not parts[0].startswith("emulator-")
        ):
            devices.append(parts[0])
    if len(devices) != 1:
        raise RuntimeError(
            f"expected exactly one physical ADB target, found {len(devices)}"
        )
    return devices[0]


def adb_cat(serial: str, rel: str) -> bytes | None:
    adb = shutil.which("adb")
    if not adb:
        return None
    result = subprocess.run(
        [adb, "-s", serial, "exec-out", "run-as", PACKAGE, "cat", rel],
        capture_output=True,
        timeout=20,
    )
    return result.stdout if result.returncode == 0 else None


def snapshot_db(serial: str, db_name: str, temp: Path) -> Path:
    main = adb_cat(serial, f"databases/{db_name}")
    if not main or not main.startswith(b"SQLite format 3\x00"):
        raise RuntimeError(f"Android database unavailable: {db_name}")
    path = temp / db_name
    path.write_bytes(main)
    wal = adb_cat(serial, f"databases/{db_name}-wal")
    if wal:
        (temp / f"{db_name}-wal").write_bytes(wal)
    shm = adb_cat(serial, f"databases/{db_name}-shm")
    if shm:
        (temp / f"{db_name}-shm").write_bytes(shm)
    return path


def visible_favorites(tv_db: Path) -> list[dict[str, Any]]:
    con = sqlite3.connect(f"file:{tv_db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            """
            SELECT
                stream_id,
                channel_id,
                COALESCE(NULLIF(custom_name, ''), name) AS display_name,
                guide_incorrect
            FROM streams
            WHERE favorite = 1
              AND manual_hidden = 0
              AND auto_hidden = 0
            ORDER BY favorite_group, favorite_order, display_name COLLATE NOCASE
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def epg_state(epg_db: Path, channel_id: str, now_ms: int) -> dict[str, Any]:
    con = sqlite3.connect(f"file:{epg_db}?mode=ro", uri=True)
    try:
        current = con.execute(
            """
            SELECT COUNT(*)
            FROM programmes
            WHERE channel_id = ?
              AND start_ms <= ?
              AND stop_ms > ?
            """,
            (channel_id, now_ms, now_ms),
        ).fetchone()[0]
        future = con.execute(
            """
            SELECT COUNT(*)
            FROM programmes
            WHERE channel_id = ?
              AND start_ms > ?
            """,
            (channel_id, now_ms),
        ).fetchone()[0]
        past = con.execute(
            """
            SELECT COUNT(*)
            FROM programmes
            WHERE channel_id = ?
              AND stop_ms <= ?
            """,
            (channel_id, now_ms),
        ).fetchone()[0]
        mapping = con.execute(
            "SELECT COUNT(*) FROM guide_mappings WHERE channel_id = ?",
            (channel_id,),
        ).fetchone()[0]
        return {
            "current_count": int(current),
            "future_count": int(future),
            "past_count": int(past),
            "legacy_mapping_present": bool(mapping),
        }
    finally:
        con.close()


def read_response(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "PrivyHub-D132-Probe/1.0",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=4) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError("EPG response exceeds probe cap")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("EPG response root is not an object")
    return payload


def companion_state(channel_id: str, now_ms: int) -> dict[str, Any]:
    encoded = urllib.parse.quote(channel_id, safe="")
    url = f"{CONTROL_BASE}/plugins/epg/guide?channel_id={encoded}"
    try:
        payload = read_response(url)
    except Exception as exc:
        return {
            "reachable": False,
            "programme_count": 0,
            "current_count": 0,
            "cached": None,
            "stale": None,
            "error_class": type(exc).__name__,
        }

    programmes = payload.get("programmes")
    if not isinstance(programmes, list):
        programmes = []

    current_count = 0
    for item in programmes:
        if not isinstance(item, dict):
            continue
        start = item.get("start_ms")
        stop = item.get("stop_ms")
        try:
            start_i = int(start)
            stop_i = int(stop)
        except Exception:
            continue
        if start_i <= now_ms < stop_i:
            current_count += 1

    return {
        "reachable": True,
        "programme_count": len(programmes),
        "current_count": current_count,
        "cached": payload.get("cached"),
        "stale": payload.get("stale"),
        "error_class": "",
    }


def classify_channel(
    row: dict[str, Any],
    local: dict[str, Any],
    companion: dict[str, Any] | None,
) -> str:
    if int(row.get("guide_incorrect") or 0) == 1:
        return "marked_incorrect"

    channel_id = str(row.get("channel_id") or "").strip()
    if not channel_id or channel_id.startswith("tv_stream_"):
        return "synthetic_or_unmatchable_identity"

    if int(local.get("current_count") or 0) > 0:
        return "android_current_programme"

    if companion is None:
        if int(local.get("future_count") or 0) > 0:
            return "android_future_only_gap"
        if int(local.get("past_count") or 0) > 0:
            return "android_stale_only"
        return "android_no_programmes"

    if not companion.get("reachable"):
        if int(local.get("future_count") or 0) > 0:
            return "android_future_only_companion_unreachable"
        if int(local.get("past_count") or 0) > 0:
            return "android_stale_only_companion_unreachable"
        return "companion_unreachable"

    if int(companion.get("current_count") or 0) > 0:
        return "companion_current_available_android_missing"

    if int(companion.get("programme_count") or 0) > 0:
        return "companion_programmes_no_current"

    if int(local.get("future_count") or 0) > 0:
        return "android_future_only_companion_empty"

    if int(local.get("past_count") or 0) > 0:
        return "android_stale_only_companion_empty"

    if local.get("legacy_mapping_present"):
        return "legacy_mapping_but_no_programmes"

    return "no_known_guide_coverage"


def build_report(
    favorites: list[dict[str, Any]],
    local_states: dict[str, dict[str, Any]],
    companion_states: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    items = []
    counts: dict[str, int] = {}

    for row in favorites:
        channel_id = str(row.get("channel_id") or "").strip()
        local = local_states.get(channel_id, {
            "current_count": 0,
            "future_count": 0,
            "past_count": 0,
            "legacy_mapping_present": False,
        })
        companion = companion_states.get(channel_id)
        reason = classify_channel(row, local, companion)
        counts[reason] = counts.get(reason, 0) + 1
        items.append({
            "display_name": str(row.get("display_name") or ""),
            "channel_id": channel_id,
            "guide_incorrect": bool(int(row.get("guide_incorrect") or 0)),
            "reason": reason,
            "android_current_count": int(local.get("current_count") or 0),
            "android_future_count": int(local.get("future_count") or 0),
            "android_past_count": int(local.get("past_count") or 0),
            "legacy_mapping_present": bool(local.get("legacy_mapping_present")),
            "companion_reachable": (
                None if companion is None else bool(companion.get("reachable"))
            ),
            "companion_programme_count": (
                None if companion is None
                else int(companion.get("programme_count") or 0)
            ),
            "companion_current_count": (
                None if companion is None
                else int(companion.get("current_count") or 0)
            ),
        })

    if not favorites:
        classification = CLASS_NONE
    else:
        unresolved = [
            item for item in items
            if item["reason"] not in {
                "android_current_programme",
                "marked_incorrect",
            }
        ]
        classification = CLASS_COMPLETE if not unresolved else CLASS_GAPS

    return {
        "classification": classification,
        "visible_favorite_count": len(favorites),
        "reason_counts": counts,
        "items": items,
    }


def self_test() -> int:
    favorites = [
        {
            "display_name": "A",
            "channel_id": "a.test",
            "guide_incorrect": 0,
        },
        {
            "display_name": "B",
            "channel_id": "b.test",
            "guide_incorrect": 0,
        },
        {
            "display_name": "C",
            "channel_id": "tv_stream_x",
            "guide_incorrect": 0,
        },
    ]
    local = {
        "a.test": {
            "current_count": 1,
            "future_count": 2,
            "past_count": 1,
            "legacy_mapping_present": False,
        },
        "b.test": {
            "current_count": 0,
            "future_count": 0,
            "past_count": 0,
            "legacy_mapping_present": False,
        },
        "tv_stream_x": {
            "current_count": 0,
            "future_count": 0,
            "past_count": 0,
            "legacy_mapping_present": False,
        },
    }
    companion = {
        "b.test": {
            "reachable": True,
            "programme_count": 5,
            "current_count": 1,
        }
    }
    report = build_report(favorites, local, companion)
    assert report["classification"] == CLASS_GAPS
    assert report["reason_counts"]["android_current_programme"] == 1
    assert report["reason_counts"][
        "companion_current_available_android_missing"
    ] == 1
    assert report["reason_counts"]["synthetic_or_unmatchable_identity"] == 1
    assert build_report([], {}, {})["classification"] == CLASS_NONE
    print("D132_PROBE_SELF_TEST_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    repo = Path(args.repo).resolve()
    log_dir = repo / "logs" / "tv"
    log_dir.mkdir(parents=True, exist_ok=True)
    text_path = log_dir / "d132_favorites_epg_coverage_probe.txt"
    json_path = log_dir / "d132_favorites_epg_coverage_probe.json"

    serial = adb_target()
    now_ms = int(time.time() * 1000)

    with tempfile.TemporaryDirectory(prefix="d132_probe_") as td:
        temp = Path(td)
        tv_db = snapshot_db(serial, "privyhub_tv.db", temp)
        epg_db = snapshot_db(serial, "privyhub_epg.db", temp)
        favorites = visible_favorites(tv_db)

        local_states: dict[str, dict[str, Any]] = {}
        companion_states: dict[str, dict[str, Any]] = {}

        for row in favorites:
            channel_id = str(row.get("channel_id") or "").strip()
            if channel_id not in local_states:
                local_states[channel_id] = epg_state(
                    epg_db,
                    channel_id,
                    now_ms,
                )

        # Companion checks are bounded to rows that do not already have a current
        # Android programme and have a canonical EPG-matchable identity.
        checked = 0
        for row in favorites:
            channel_id = str(row.get("channel_id") or "").strip()
            if (
                checked >= 16
                or int(row.get("guide_incorrect") or 0) == 1
                or not channel_id
                or channel_id.startswith("tv_stream_")
                or int(local_states[channel_id].get("current_count") or 0) > 0
                or channel_id in companion_states
            ):
                continue
            companion_states[channel_id] = companion_state(channel_id, now_ms)
            checked += 1

    report = build_report(
        favorites,
        local_states,
        companion_states,
    )
    report["companion_checks"] = len(companion_states)

    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "PrivyHub D-132 Favorites EPG coverage probe",
        f"Classification: {report['classification']}",
        "",
        "SUMMARY",
        f"  visible_favorite_count: {report['visible_favorite_count']}",
        f"  companion_checks: {report['companion_checks']}",
        "",
        "REASON COUNTS",
    ]
    for reason, count in sorted(report["reason_counts"].items()):
        lines.append(f"  {reason}: {count}")

    lines.extend(["", "CHANNELS"])
    for item in report["items"]:
        lines.append(
            "  "
            + item["display_name"]
            + " | "
            + item["reason"]
            + f" | android_current={item['android_current_count']}"
            + f" future={item['android_future_count']}"
            + f" companion_programmes={item['companion_programme_count']}"
        )

    lines.extend([
        "",
        "No network address or device identifier is written to this report.",
        f"JSON: {json_path}",
        f"TEXT: {text_path}",
    ])

    text = "\n".join(lines) + "\n"
    text_path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
