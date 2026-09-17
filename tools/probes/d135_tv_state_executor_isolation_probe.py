#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

JSON_REL = Path("logs/tv/d135_tv_state_executor_isolation_probe.json")
TEXT_REL = Path("logs/tv/d135_tv_state_executor_isolation_probe.txt")
SESSION_REL = Path("logs/tv/d135_tv_state_executor_isolation_session.json")

D134_RE = re.compile(
    r"D134_TV_PAGE\s+session=(?P<session>\d+)\s+stage=(?P<stage>[a-z_]+)(?P<rest>.*)$"
)
D135_PAGE_RE = re.compile(
    r"D135_TV_PAGE\s+session=(?P<session>\d+)\s+stage=executor_start(?P<rest>.*)$"
)
D131_RE = re.compile(
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
        if (
            len(parts) >= 2
            and parts[1] == "device"
            and not parts[0].startswith("emulator-")
        ):
            devices.append(parts[0])
    return devices[0] if len(devices) == 1 else None


def clear_logcat(serial: str) -> None:
    subprocess.run(
        ["adb", "-s", serial, "logcat", "-c"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )


def read_logcat(serial: str) -> str:
    result = subprocess.run(
        ["adb", "-s", serial, "logcat", "-d", "-v", "brief", "PrivyHub:I", "*:S"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=15,
    )
    return result.stdout


def fields(rest: str) -> dict[str, str]:
    return {key: value for key, value in FIELD_RE.findall(rest)}


def parse(text: str) -> dict[str, Any]:
    pages: dict[str, dict[str, dict[str, str]]] = {}
    queue_waits: dict[str, int] = {}
    tv_entries: dict[str, dict[str, dict[str, str]]] = {}

    for raw in text.splitlines():
        match = D134_RE.search(raw)
        if match:
            session = match.group("session")
            pages.setdefault(session, {})[match.group("stage")] = fields(
                match.group("rest")
            )
            continue

        match = D135_PAGE_RE.search(raw)
        if match:
            session = match.group("session")
            values = fields(match.group("rest"))
            try:
                queue_waits[session] = int(values["queue_wait_ms"])
            except Exception:
                pass
            continue

        match = D131_RE.search(raw)
        if match:
            session = match.group("session")
            tv_entries.setdefault(session, {})[match.group("stage")] = fields(
                match.group("rest")
            )

    return {
        "pages": pages,
        "queue_waits": queue_waits,
        "tv_entries": tv_entries,
    }


def int_field(stages: dict[str, dict[str, str]], stage: str, key: str) -> int | None:
    try:
        return int(stages[stage][key])
    except Exception:
        return None


def latest_favorites(parsed: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    candidates = []
    for session, stages in parsed["pages"].items():
        if stages.get("page_begin", {}).get("mode") != "favorites":
            continue
        if "ui_ready" not in stages:
            continue
        candidates.append((int(session), session, stages))
    if not candidates:
        return None
    _, session, stages = max(candidates)
    return session, stages


def latest_tv_entry(parsed: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    candidates = []
    for session, stages in parsed["tv_entries"].items():
        if "state_sync_complete" not in stages or "sync_reconciled" not in stages:
            continue
        candidates.append((int(session), session, stages))
    if not candidates:
        return None
    _, session, stages = max(candidates)
    return session, stages


def classify(parsed: dict[str, Any]) -> dict[str, Any]:
    page = latest_favorites(parsed)
    entry = latest_tv_entry(parsed)

    if page is None:
        return {"classification": "D135_FAVORITES_PAGE_NOT_OBSERVED"}

    page_session, page_stages = page
    queue_wait_ms = parsed["queue_waits"].get(page_session)
    total_ms = int_field(page_stages, "ui_ready", "total_ms")

    named_stage_values = [
        int_field(page_stages, "count", "elapsed_ms"),
        int_field(page_stages, "query", "elapsed_ms"),
        int_field(page_stages, "prefetch", "elapsed_ms"),
        int_field(page_stages, "rejected_prefetch", "elapsed_ms"),
        int_field(page_stages, "hydrate", "elapsed_ms"),
        int_field(page_stages, "ui_ready", "elapsed_ms"),
    ]
    named_sum_ms = sum(value for value in named_stage_values if value is not None)
    residual_ms = None if total_ms is None else max(0, total_ms - named_sum_ms)

    sync_complete = False
    sync_reconciled = False
    sync_action = ""
    sync_ms = None
    page_ready_before_sync_complete = None

    if entry is not None:
        entry_session, entry_stages = entry
        sync_complete = "state_sync_complete" in entry_stages
        sync_reconciled = "sync_reconciled" in entry_stages
        sync_action = entry_stages.get("state_sync_complete", {}).get("action", "")
        sync_ms = int_field(entry_stages, "state_sync_complete", "elapsed_ms")

        sync_total = int_field(entry_stages, "state_sync_complete", "total_ms")
        if total_ms is not None and sync_total is not None:
            page_ready_abs = int(page_session) + total_ms
            sync_complete_abs = int(entry_session) + sync_total
            page_ready_before_sync_complete = page_ready_abs < sync_complete_abs

    if queue_wait_ms is None:
        classification = "D135_QUEUE_WAIT_MARKER_MISSING"
    elif not sync_complete or not sync_reconciled:
        classification = "D135_STATE_SYNC_NOT_COMPLETE"
    elif queue_wait_ms <= 1500 and total_ms is not None and total_ms <= 5000:
        classification = "D135_FAVORITES_QUEUE_CONTENTION_REMOVED"
    elif queue_wait_ms > 5000:
        classification = "D135_FAVORITES_QUEUE_WAIT_STILL_HIGH"
    else:
        classification = "D135_FAVORITES_INTERNAL_WORK_STILL_SLOW"

    return {
        "classification": classification,
        "favorites_total_ms": total_ms,
        "favorites_queue_wait_ms": queue_wait_ms,
        "favorites_named_stage_sum_ms": named_sum_ms,
        "favorites_residual_ms": residual_ms,
        "state_sync_complete": sync_complete,
        "state_sync_reconciled": sync_reconciled,
        "state_sync_action": sync_action,
        "state_sync_ms": sync_ms,
        "favorites_ready_before_state_sync_complete": page_ready_before_sync_complete,
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
        "PrivyHub D-135 TV-state executor isolation probe",
        f"Classification: {report.get('classification')}",
        "",
        "FAVORITES",
        f"  total_ms: {report.get('favorites_total_ms')}",
        f"  queue_wait_ms: {report.get('favorites_queue_wait_ms')}",
        f"  named_stage_sum_ms: {report.get('favorites_named_stage_sum_ms')}",
        f"  residual_ms: {report.get('favorites_residual_ms')}",
        "",
        "TV STATE",
        f"  state_sync_complete: {report.get('state_sync_complete', False)}",
        f"  state_sync_reconciled: {report.get('state_sync_reconciled', False)}",
        f"  state_sync_action: {report.get('state_sync_action', '')}",
        f"  state_sync_ms: {report.get('state_sync_ms')}",
        f"  favorites_ready_before_state_sync_complete: {report.get('favorites_ready_before_state_sync_complete')}",
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
    synthetic = "\n".join([
        "I/PrivyHub: D131_TV_ENTRY session=1000 stage=entry_begin total_ms=0",
        "I/PrivyHub: D131_TV_ENTRY session=1000 stage=ui_ready elapsed_ms=300 total_ms=330",
        "I/PrivyHub: D134_TV_PAGE session=1400 stage=page_begin mode=favorites total_ms=0",
        "I/PrivyHub: D135_TV_PAGE session=1400 stage=executor_start queue_wait_ms=20",
        "I/PrivyHub: D134_TV_PAGE session=1400 stage=count elapsed_ms=20 total_ms=40 count=20",
        "I/PrivyHub: D134_TV_PAGE session=1400 stage=query elapsed_ms=1 total_ms=41 channels=20",
        "I/PrivyHub: D134_TV_PAGE session=1400 stage=prefetch elapsed_ms=180 total_ms=221 queued=10",
        "I/PrivyHub: D134_TV_PAGE session=1400 stage=rejected_prefetch elapsed_ms=2 total_ms=223 queued=0",
        "I/PrivyHub: D134_TV_PAGE session=1400 stage=hydrate elapsed_ms=480 total_ms=703 hydrated=1",
        "I/PrivyHub: D134_TV_PAGE session=1400 stage=ui_ready elapsed_ms=850 total_ms=1553",
        "I/PrivyHub: D131_TV_ENTRY session=1000 stage=state_sync_complete elapsed_ms=24000 total_ms=24700 action=pulled local_changed=true",
        "I/PrivyHub: D131_TV_ENTRY session=1000 stage=sync_reconciled total_ms=25000 action=pulled local_changed=true",
    ])

    report = classify(parse(synthetic))
    assert report["classification"] == "D135_FAVORITES_QUEUE_CONTENTION_REMOVED"
    assert report["favorites_queue_wait_ms"] == 20
    assert report["favorites_total_ms"] == 1553
    assert report["state_sync_reconciled"] is True
    assert report["favorites_ready_before_state_sync_complete"] is True

    slow = synthetic.replace(
        "queue_wait_ms=20",
        "queue_wait_ms=12000",
    ).replace(
        "stage=ui_ready elapsed_ms=850 total_ms=1553",
        "stage=ui_ready elapsed_ms=850 total_ms=13533",
    )
    assert classify(parse(slow))["classification"] == "D135_FAVORITES_QUEUE_WAIT_STILL_HIGH"

    print("D135_PROBE_SELF_TEST_OK")
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
        return write_report(repo, {"classification": "D135_ADB_UNAVAILABLE"})

    session_path = repo / SESSION_REL
    session_path.parent.mkdir(parents=True, exist_ok=True)

    if args.prepare:
        clear_logcat(serial)
        session_path.write_text(
            json.dumps({"prepared_at_ms": int(time.time() * 1000)}, indent=2) + "\n",
            encoding="utf-8",
        )
        return write_report(
            repo,
            {"classification": "D135_EXECUTOR_ISOLATION_TEST_PREPARED"},
        )

    if not session_path.is_file():
        return write_report(repo, {"classification": "D135_PREPARE_REQUIRED"})

    deadline = time.monotonic() + 35.0
    latest_report = {"classification": "D135_FAVORITES_PAGE_NOT_OBSERVED"}

    while time.monotonic() < deadline:
        try:
            parsed = parse(read_logcat(serial))
            latest_report = classify(parsed)
        except Exception:
            latest_report = {"classification": "D135_LOGCAT_READ_FAILED"}

        if latest_report.get("classification") in {
            "D135_FAVORITES_QUEUE_CONTENTION_REMOVED",
            "D135_FAVORITES_QUEUE_WAIT_STILL_HIGH",
            "D135_FAVORITES_INTERNAL_WORK_STILL_SLOW",
        }:
            return write_report(repo, latest_report)

        time.sleep(0.5)

    return write_report(repo, latest_report)


if __name__ == "__main__":
    raise SystemExit(main())
