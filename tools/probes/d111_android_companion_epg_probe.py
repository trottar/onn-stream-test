#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from typing import Any

APP_ID = "com.safeiot.privyhub"

META_KEYS = (
    "companion_epg_last_success_channel",
    "companion_epg_last_success_at_ms",
    "companion_epg_last_programme_count",
    "companion_epg_last_response_cached",
    "companion_epg_last_response_stale",
)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def inspect_db(serial: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="d111_epgdb_") as td:
        temp = Path(td)
        main = adb_cat(serial, "databases/privyhub_epg.db")

        if not main or not main.startswith(b"SQLite format 3\x00"):
            return {
                "snapshot_ok": False,
                "reason": "epg_db_unavailable",
            }

        db_path = temp / "privyhub_epg.db"
        db_path.write_bytes(main)

        wal = adb_cat(serial, "databases/privyhub_epg.db-wal")
        if wal:
            (temp / "privyhub_epg.db-wal").write_bytes(wal)

        shm = adb_cat(serial, "databases/privyhub_epg.db-shm")
        if shm:
            (temp / "privyhub_epg.db-shm").write_bytes(shm)

        try:
            conn = sqlite3.connect(
                f"file:{db_path}?mode=ro",
                uri=True,
            )
            try:
                meta: dict[str, str] = {}
                for key in META_KEYS:
                    row = conn.execute(
                        "SELECT value FROM meta WHERE key = ?",
                        (key,),
                    ).fetchone()
                    if row:
                        meta[key] = str(row[0])

                channel = meta.get(
                    "companion_epg_last_success_channel",
                    "",
                ).strip()

                total_programmes = int(
                    conn.execute(
                        "SELECT COUNT(*) FROM programmes"
                    ).fetchone()[0]
                )

                channel_programmes = 0
                if channel:
                    channel_programmes = int(
                        conn.execute(
                            "SELECT COUNT(*) FROM programmes WHERE channel_id = ?",
                            (channel,),
                        ).fetchone()[0]
                    )
            finally:
                conn.close()

        except Exception as exc:
            return {
                "snapshot_ok": False,
                "reason": "sqlite_read_failed",
                "detail": str(exc)[:300],
            }

        return {
            "snapshot_ok": True,
            "db_bytes": len(main),
            "db_sha256": sha256(main),
            "meta": meta,
            "last_success_channel": channel,
            "total_programmes": total_programmes,
            "last_success_channel_programmes": channel_programmes,
        }


def classify(snapshot: dict[str, Any]) -> str:
    if not snapshot.get("snapshot_ok"):
        return "D111_EPG_DB_SNAPSHOT_FAILED"

    meta = snapshot.get("meta") or {}
    channel = str(
        meta.get("companion_epg_last_success_channel", "")
    ).strip()

    try:
        declared = int(
            meta.get("companion_epg_last_programme_count", "0")
        )
    except ValueError:
        declared = 0

    rows = int(
        snapshot.get("last_success_channel_programmes") or 0
    )

    if channel and declared > 0 and rows > 0:
        return "D111_ANDROID_COMPANION_EPG_RUNTIME_VALIDATED"

    return "D111_ANDROID_COMPANION_EPG_NOT_OBSERVED"


def render(report: dict[str, Any]) -> str:
    snapshot = report.get("epg_snapshot", {})
    meta = snapshot.get("meta") or {}

    lines = [
        "PrivyHub D-111 D5.3 Android companion-EPG runtime probe",
        f"Generated: {report.get('generated_at')}",
        f"Classification: {report.get('classification')}",
        "",
        "ADB / EPG SNAPSHOT",
        f"  adb_status: {report.get('adb', {}).get('reason')}",
        f"  snapshot_ok: {snapshot.get('snapshot_ok')}",
        f"  total_programmes: {snapshot.get('total_programmes')}",
        "",
        "COMPANION SUCCESS MARKER",
        f"  channel_id: {snapshot.get('last_success_channel') or None}",
        f"  success_at_ms: {meta.get('companion_epg_last_success_at_ms')}",
        f"  declared_programme_count: {meta.get('companion_epg_last_programme_count')}",
        f"  db_programme_rows_for_channel: {snapshot.get('last_success_channel_programmes')}",
        f"  companion_response_cached: {meta.get('companion_epg_last_response_cached')}",
        f"  companion_response_stale: {meta.get('companion_epg_last_response_stale')}",
        "",
        "No onn database was modified.",
        f"JSON: {report.get('json_path')}",
        f"TEXT: {report.get('text_path')}",
    ]

    return "\n".join(lines) + "\n"


def self_test() -> int:
    good = {
        "snapshot_ok": True,
        "meta": {
            "companion_epg_last_success_channel": "Example.us@SD",
            "companion_epg_last_programme_count": "12",
        },
        "last_success_channel_programmes": 12,
    }
    assert classify(good) == "D111_ANDROID_COMPANION_EPG_RUNTIME_VALIDATED"

    missing = {
        "snapshot_ok": True,
        "meta": {},
        "last_success_channel_programmes": 0,
    }
    assert classify(missing) == "D111_ANDROID_COMPANION_EPG_NOT_OBSERVED"

    print("D111_PROBE_SELF_TEST_OK")
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

    serial, adb_info = adb_serial()

    if serial:
        snapshot = inspect_db(serial)
    else:
        snapshot = {
            "snapshot_ok": False,
            "reason": adb_info.get("reason"),
        }

    report = {
        "generated_at": now_iso(),
        "adb": adb_info,
        "epg_snapshot": snapshot,
    }
    report["classification"] = classify(snapshot)

    json_path = logs / "d111_android_companion_epg_probe.json"
    text_path = logs / "d111_android_companion_epg_probe.txt"
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
