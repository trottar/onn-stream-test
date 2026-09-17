#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

PACKAGE = "com.safeiot.privyhub"
CONTROL_BASE = "http://127.0.0.1:8765"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
CLASS_OK = "D127_INCORRECT_GUIDE_DURABILITY_CONFIRMED"
CLASS_NONE = "D127_NO_MARKED_GUIDE_FOUND"
CLASS_MISMATCH = "D127_DURABLE_STATE_MISMATCH"


def classify(android_rows: list[dict[str, Any]], linux_state: dict[str, Any]) -> dict[str, Any]:
    marked = [row for row in android_rows if int(row.get("guide_incorrect") or 0) == 1]
    linux_channels = {
        str(item.get("stream_id") or ""): item
        for item in linux_state.get("channels", [])
        if isinstance(item, dict)
    }
    report: dict[str, Any] = {
        "android_marked_count": len(marked),
        "matched": [],
        "problems": [],
    }
    if not marked:
        report["classification"] = CLASS_NONE
        return report

    for row in marked:
        stream_id = str(row.get("stream_id") or "")
        source_key = str(row.get("rejected_guide_source_key") or "")
        at_ms = int(row.get("guide_incorrect_at_ms") or 0)
        remote = linux_channels.get(stream_id)
        item = {
            "stream_id": stream_id,
            "manual_hidden": int(row.get("manual_hidden") or 0),
            "auto_hidden": int(row.get("auto_hidden") or 0),
            "source_key_present": bool(source_key),
            "timestamp_present": at_ms > 0,
            "linux_match": bool(
                remote
                and remote.get("guide_incorrect") is True
                and str(remote.get("rejected_guide_source_key") or "") == source_key
                and int(remote.get("guide_incorrect_at_ms") or 0) == at_ms
            ),
        }
        report["matched"].append(item)
        if item["manual_hidden"] != 0 or item["auto_hidden"] != 0:
            report["problems"].append(f"{stream_id}: channel is hidden")
        if not item["source_key_present"]:
            report["problems"].append(f"{stream_id}: rejected source key is blank")
        if not item["timestamp_present"]:
            report["problems"].append(f"{stream_id}: incorrect-guide timestamp is missing")
        if not item["linux_match"]:
            report["problems"].append(f"{stream_id}: Linux durable state does not match Android")

    report["classification"] = CLASS_OK if not report["problems"] else CLASS_MISMATCH
    return report


def adb_target() -> str:
    adb = shutil.which("adb")
    if not adb:
        raise RuntimeError("adb not found")
    result = subprocess.run([adb, "devices"], check=True, text=True, capture_output=True)
    devices = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device" and not parts[0].startswith("emulator-"):
            devices.append(parts[0])
    if len(devices) != 1:
        raise RuntimeError(f"expected exactly one physical ADB target, found {len(devices)}")
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


def read_android_rows(db_path: Path) -> list[dict[str, Any]]:
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT stream_id, manual_hidden, auto_hidden, guide_incorrect,
                   rejected_guide_source_key, guide_incorrect_at_ms
            FROM streams
            WHERE guide_incorrect = 1
            ORDER BY stream_id
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def read_response(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "PrivyHub-D127-Probe/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE_BYTES + 1)
        raise RuntimeError(f"TV-state endpoint returned HTTP {exc.code}") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError("TV-state response exceeds probe cap")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("TV-state response root is not an object")
    return payload


def read_linux_state() -> dict[str, Any]:
    envelope = read_response(CONTROL_BASE + "/plugins/tv_state/state")
    if not envelope.get("ok") or not envelope.get("initialized"):
        raise RuntimeError("Linux TV-state authority is not initialized")
    state = envelope.get("state")
    if not isinstance(state, dict):
        raise RuntimeError("Linux TV-state envelope has no state object")
    if state.get("schema") != "privyhub_tv_user_state_v2":
        raise RuntimeError(f"unexpected Linux TV-state schema: {state.get('schema')!r}")
    return state


def self_test() -> int:
    android = [{
        "stream_id": "tv_stream_test",
        "manual_hidden": 0,
        "auto_hidden": 0,
        "guide_incorrect": 1,
        "rejected_guide_source_key": "companion:test",
        "guide_incorrect_at_ms": 123,
    }]
    linux = {
        "schema": "privyhub_tv_user_state_v2",
        "channels": [{
            "stream_id": "tv_stream_test",
            "guide_incorrect": True,
            "rejected_guide_source_key": "companion:test",
            "guide_incorrect_at_ms": 123,
        }],
    }
    assert classify(android, linux)["classification"] == CLASS_OK
    linux["channels"][0]["rejected_guide_source_key"] = "other"
    assert classify(android, linux)["classification"] == CLASS_MISMATCH
    assert classify([], {"channels": []})["classification"] == CLASS_NONE
    print("D127_PROBE_SELF_TEST_OK")
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
    output = log_dir / "d127_incorrect_guide_probe.txt"

    serial = adb_target()
    with tempfile.TemporaryDirectory(prefix="d127_probe_") as td:
        db_path = snapshot_db(serial, "privyhub_tv.db", Path(td))
        android_rows = read_android_rows(db_path)

    linux_state = read_linux_state()
    report = classify(android_rows, linux_state)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"log = {output}")
    return 0 if report["classification"] == CLASS_OK else 1


if __name__ == "__main__":
    raise SystemExit(main())
