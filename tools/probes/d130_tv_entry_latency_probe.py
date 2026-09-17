#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

SESSION_REL = Path("logs/tv/d130_tv_entry_latency_session.json")
JSON_REL = Path("logs/tv/d130_tv_entry_latency_probe.json")
TEXT_REL = Path("logs/tv/d130_tv_entry_latency_probe.txt")

MARKER = "D130_TV_ENTRY"
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


def run_adb(serial: str, args: list[str], timeout: int = 20) -> str:
    result = subprocess.run(
        ["adb", "-s", serial, *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
    return result.stdout


def parse_events(text: str) -> dict[int, list[dict[str, str]]]:
    sessions: dict[int, list[dict[str, str]]] = {}
    for line in text.splitlines():
        if MARKER not in line:
            continue
        marker_text = line.split(MARKER, 1)[1]
        fields = dict(FIELD_RE.findall(marker_text))
        try:
            session = int(fields.get("session", ""))
        except ValueError:
            continue
        if not fields.get("stage"):
            continue
        sessions.setdefault(session, []).append(fields)
    return sessions


def latest_complete(sessions: dict[int, list[dict[str, str]]]) -> tuple[int, list[dict[str, str]]] | None:
    complete = []
    for session, events in sessions.items():
        stages = {item.get("stage") for item in events}
        if "entry_begin" in stages and "ui_ready" in stages:
            complete.append((session, events))
    if not complete:
        return None
    return max(complete, key=lambda item: item[0])


def as_int(value: str | None, default: int = 0) -> int:
    try:
        return int(value or "")
    except ValueError:
        return default


def summarize(events: list[dict[str, str]]) -> dict[str, Any]:
    by_stage = {item["stage"]: item for item in events}
    catalog = as_int(by_stage.get("ensure_catalog", {}).get("elapsed_ms"))
    sync = as_int(by_stage.get("state_sync", {}).get("elapsed_ms"))
    recatalog = as_int(by_stage.get("post_sync_catalog", {}).get("elapsed_ms"))
    ui = as_int(by_stage.get("ui_ready", {}).get("elapsed_ms"))
    total = as_int(by_stage.get("ui_ready", {}).get("total_ms"))
    cached = by_stage.get("ensure_catalog", {}).get("cached", "unknown")
    local_changed = by_stage.get("state_sync", {}).get("local_changed", "unknown")
    sync_action = by_stage.get("state_sync", {}).get("action", "unknown")

    stages = {
        "ensure_catalog_ms": catalog,
        "state_sync_ms": sync,
        "post_sync_catalog_ms": recatalog,
        "ui_render_ms": ui,
    }
    dominant_name, dominant_ms = max(stages.items(), key=lambda item: item[1])

    if total <= 0:
        classification = "D130_TV_ENTRY_TIMING_INCOMPLETE"
    elif dominant_ms >= max(250, int(total * 0.50)):
        mapping = {
            "ensure_catalog_ms": "D130_TV_ENTRY_CATALOG_DOMINANT",
            "state_sync_ms": "D130_TV_ENTRY_STATE_SYNC_DOMINANT",
            "post_sync_catalog_ms": "D130_TV_ENTRY_POST_SYNC_CATALOG_DOMINANT",
            "ui_render_ms": "D130_TV_ENTRY_UI_RENDER_DOMINANT",
        }
        classification = mapping[dominant_name]
    else:
        classification = "D130_TV_ENTRY_MIXED_LATENCY"

    return {
        "classification": classification,
        "total_entry_ms": total,
        **stages,
        "initial_catalog_cached": cached,
        "state_sync_action": sync_action,
        "state_sync_local_changed": local_changed,
        "dominant_stage": dominant_name,
        "dominant_stage_ms": dominant_ms,
    }


def write_report(repo: Path, report: dict[str, Any]) -> int:
    json_path = repo / JSON_REL
    text_path = repo / TEXT_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "PrivyHub D-130 TV-entry latency probe",
        f"Classification: {report.get('classification')}",
        "",
        "ENTRY TIMING",
        f"  total_entry_ms: {report.get('total_entry_ms', 0)}",
        f"  ensure_catalog_ms: {report.get('ensure_catalog_ms', 0)}",
        f"  state_sync_ms: {report.get('state_sync_ms', 0)}",
        f"  post_sync_catalog_ms: {report.get('post_sync_catalog_ms', 0)}",
        f"  ui_render_ms: {report.get('ui_render_ms', 0)}",
        "",
        "STATE",
        f"  initial_catalog_cached: {report.get('initial_catalog_cached', 'unknown')}",
        f"  state_sync_action: {report.get('state_sync_action', 'unknown')}",
        f"  state_sync_local_changed: {report.get('state_sync_local_changed', 'unknown')}",
        f"  dominant_stage: {report.get('dominant_stage', 'unknown')}",
        f"  dominant_stage_ms: {report.get('dominant_stage_ms', 0)}",
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
    sample = """
I/PrivyHub: D130_TV_ENTRY session=1000 stage=entry_begin total_ms=0
I/PrivyHub: D130_TV_ENTRY session=1000 stage=ensure_catalog elapsed_ms=12 total_ms=12 cached=true
I/PrivyHub: D130_TV_ENTRY session=1000 stage=state_sync elapsed_ms=2820 total_ms=2832 action=pulled local_changed=true
I/PrivyHub: D130_TV_ENTRY session=1000 stage=post_sync_catalog elapsed_ms=18 total_ms=2850 cached=true
I/PrivyHub: D130_TV_ENTRY session=1000 stage=ui_ready elapsed_ms=15 total_ms=2865
"""
    sessions = parse_events(sample)
    selected = latest_complete(sessions)
    assert selected is not None
    _, events = selected
    report = summarize(events)
    assert report["classification"] == "D130_TV_ENTRY_STATE_SYNC_DOMINANT"
    assert report["total_entry_ms"] == 2865
    assert report["state_sync_ms"] == 2820
    assert report["initial_catalog_cached"] == "true"
    print("D130_PROBE_SELF_TEST_OK")
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
    session_path = repo / SESSION_REL
    session_path.parent.mkdir(parents=True, exist_ok=True)
    serial = adb_serial()
    if serial is None:
        return write_report(repo, {"classification": "D130_ADB_UNAVAILABLE"})

    if args.prepare:
        try:
            run_adb(serial, ["logcat", "-c"])
        except Exception:
            return write_report(repo, {"classification": "D130_LOGCAT_CLEAR_FAILED"})
        session_path.write_text(
            json.dumps({"prepared_at_ms": int(time.time() * 1000)}, indent=2) + "\n",
            encoding="utf-8",
        )
        print("D130_TV_ENTRY_TEST_PREPARED")
        print("Open TV once from the top-level PrivyHub screen and wait for TV home.")
        return 0

    if not session_path.is_file():
        return write_report(repo, {"classification": "D130_PREPARE_REQUIRED"})

    try:
        text = run_adb(serial, ["logcat", "-d", "-v", "brief", "PrivyHub:I", "*:S"], timeout=30)
    except Exception:
        return write_report(repo, {"classification": "D130_LOGCAT_READ_FAILED"})

    sessions = parse_events(text)
    selected = latest_complete(sessions)
    if selected is None:
        return write_report(repo, {"classification": "D130_TV_ENTRY_SESSION_NOT_OBSERVED"})
    _, events = selected
    return write_report(repo, summarize(events))


if __name__ == "__main__":
    raise SystemExit(main())
