#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

JSON_REL = Path("logs/tv/d131_tv_entry_nonblocking_probe.json")
TEXT_REL = Path("logs/tv/d131_tv_entry_nonblocking_probe.txt")
SESSION_REL = Path("logs/tv/d131_tv_entry_nonblocking_session.json")

LINE_RE = re.compile(
    r"D131_TV_ENTRY\s+session=(?P<session>\d+)\s+stage=(?P<stage>[a-z_]+)(?P<rest>.*)$"
)
FIELD_RE = re.compile(r"([a-z_]+)=([^\s]+)")


def adb_serial() -> str | None:
    try:
        result = subprocess.run(
            ["adb", "devices"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
    except Exception:
        return None
    devices = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices[0] if len(devices) == 1 else None


def logcat(serial: str) -> str:
    result = subprocess.run(
        ["adb", "-s", serial, "logcat", "-d", "-v", "brief", "PrivyHub:I", "*:S"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=15,
    )
    return result.stdout


def clear_logcat(serial: str) -> None:
    subprocess.run(
        ["adb", "-s", serial, "logcat", "-c"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )


def parse_sessions(text: str) -> dict[str, dict[str, dict[str, str]]]:
    sessions: dict[str, dict[str, dict[str, str]]] = {}
    for raw in text.splitlines():
        match = LINE_RE.search(raw)
        if not match:
            continue
        session = match.group("session")
        stage = match.group("stage")
        fields = {k: v for k, v in FIELD_RE.findall(match.group("rest"))}
        sessions.setdefault(session, {})[stage] = fields
    return sessions


def int_field(stages: dict[str, dict[str, str]], stage: str, name: str) -> int | None:
    try:
        return int(stages[stage][name])
    except Exception:
        return None


def classify(stages: dict[str, dict[str, str]]) -> dict[str, Any]:
    ui_total = int_field(stages, "ui_ready", "total_ms")
    catalog_ms = int_field(stages, "ensure_catalog", "elapsed_ms")
    sync_ms = int_field(stages, "state_sync_complete", "elapsed_ms")
    sync_total = int_field(stages, "state_sync_complete", "total_ms")
    reconcile_total = int_field(stages, "sync_reconciled", "total_ms")
    action = stages.get("state_sync_complete", {}).get("action", "")
    local_changed = stages.get("state_sync_complete", {}).get("local_changed", "")

    complete = (
        ui_total is not None
        and catalog_ms is not None
        and sync_ms is not None
        and sync_total is not None
        and reconcile_total is not None
    )

    if not complete:
        classification = "D131_TV_ENTRY_SYNC_NOT_COMPLETE"
    elif ui_total <= 2000:
        classification = "D131_TV_ENTRY_NONBLOCKING_SYNC_VALIDATED"
    else:
        classification = "D131_TV_ENTRY_STILL_SLOW"

    return {
        "classification": classification,
        "ui_ready_total_ms": ui_total,
        "ensure_catalog_ms": catalog_ms,
        "state_sync_ms": sync_ms,
        "state_sync_total_ms": sync_total,
        "sync_reconciled_total_ms": reconcile_total,
        "state_sync_action": action,
        "state_sync_local_changed": local_changed,
        "ui_ready_before_sync_complete": (
            ui_total is not None
            and sync_total is not None
            and ui_total < sync_total
        ),
    }


def write_report(repo: Path, report: dict[str, Any]) -> int:
    json_path = repo / JSON_REL
    text_path = repo / TEXT_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "PrivyHub D-131 non-blocking TV-entry sync probe",
        f"Classification: {report.get('classification')}",
        "",
        "ENTRY TIMING",
        f"  ui_ready_total_ms: {report.get('ui_ready_total_ms')}",
        f"  ensure_catalog_ms: {report.get('ensure_catalog_ms')}",
        f"  state_sync_ms: {report.get('state_sync_ms')}",
        f"  state_sync_total_ms: {report.get('state_sync_total_ms')}",
        f"  sync_reconciled_total_ms: {report.get('sync_reconciled_total_ms')}",
        "",
        "STATE",
        f"  state_sync_action: {report.get('state_sync_action', '')}",
        f"  state_sync_local_changed: {report.get('state_sync_local_changed', '')}",
        f"  ui_ready_before_sync_complete: {report.get('ui_ready_before_sync_complete', False)}",
        "",
        "No network address or device identifier is written to this report.",
        f"JSON: {json_path}",
        f"TEXT: {text_path}",
    ]
    text = "\n".join(lines) + "\n"
    text_path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


def self_test() -> int:
    synthetic = """
I/PrivyHub: D131_TV_ENTRY session=100 stage=entry_begin total_ms=0
I/PrivyHub: D131_TV_ENTRY session=100 stage=ensure_catalog elapsed_ms=7 total_ms=9 cached=true
I/PrivyHub: D131_TV_ENTRY session=100 stage=ui_ready elapsed_ms=290 total_ms=310
I/PrivyHub: D131_TV_ENTRY session=100 stage=state_sync_complete elapsed_ms=24214 total_ms=24530 action=pulled local_changed=true
I/PrivyHub: D131_TV_ENTRY session=100 stage=post_sync_catalog elapsed_ms=3 total_ms=24534 cached=true
I/PrivyHub: D131_TV_ENTRY session=100 stage=sync_reconciled total_ms=24540 action=pulled local_changed=true
"""
    sessions = parse_sessions(synthetic)
    report = classify(sessions["100"])
    assert report["classification"] == "D131_TV_ENTRY_NONBLOCKING_SYNC_VALIDATED"
    assert report["ui_ready_total_ms"] == 310
    assert report["state_sync_ms"] == 24214
    assert report["ui_ready_before_sync_complete"] is True

    slow = dict(sessions["100"])
    slow["ui_ready"] = {"elapsed_ms": "10", "total_ms": "2501"}
    assert classify(slow)["classification"] == "D131_TV_ENTRY_STILL_SLOW"

    incomplete = {
        "ensure_catalog": {"elapsed_ms": "7", "total_ms": "9"},
        "ui_ready": {"elapsed_ms": "200", "total_ms": "250"},
    }
    assert classify(incomplete)["classification"] == "D131_TV_ENTRY_SYNC_NOT_COMPLETE"
    print("D131_PROBE_SELF_TEST_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.prepare == args.verify:
        print("Use exactly one of --prepare or --verify")
        return 2

    repo = Path(args.repo).resolve()
    serial = adb_serial()
    if serial is None:
        return write_report(repo, {"classification": "D131_ADB_UNAVAILABLE"})

    session_path = repo / SESSION_REL
    session_path.parent.mkdir(parents=True, exist_ok=True)

    if args.prepare:
        clear_logcat(serial)
        session_path.write_text(
            json.dumps({"prepared_at_ms": int(time.time() * 1000)}, indent=2) + "\n",
            encoding="utf-8",
        )
        return write_report(repo, {"classification": "D131_TV_ENTRY_TEST_PREPARED"})

    if not session_path.is_file():
        return write_report(repo, {"classification": "D131_PREPARE_REQUIRED"})

    deadline = time.monotonic() + 35.0
    selected: dict[str, dict[str, str]] | None = None

    while time.monotonic() < deadline:
        try:
            sessions = parse_sessions(logcat(serial))
        except Exception:
            sessions = {}
        for session_id in sorted(sessions, key=lambda x: int(x), reverse=True):
            stages = sessions[session_id]
            if "ui_ready" in stages:
                selected = stages
                if "sync_reconciled" in stages:
                    return write_report(repo, classify(stages))
                break
        time.sleep(0.5)

    if selected is None:
        return write_report(repo, {"classification": "D131_TV_ENTRY_NOT_OBSERVED"})
    return write_report(repo, classify(selected))


if __name__ == "__main__":
    raise SystemExit(main())
