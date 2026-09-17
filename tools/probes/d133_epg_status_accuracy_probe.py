#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

SESSION_REL = Path("logs/tv/d133_epg_status_accuracy_session.json")
JSON_REL = Path("logs/tv/d133_epg_status_accuracy_probe.json")
TEXT_REL = Path("logs/tv/d133_epg_status_accuracy_probe.txt")
BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


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
    devices: list[str] = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device" and not parts[0].startswith("emulator-"):
            devices.append(parts[0])
    return devices[0] if len(devices) == 1 else None


def dump_ui(serial: str) -> str:
    remote = "/sdcard/privyhub_d133_ui.xml"
    subprocess.run(
        ["adb", "-s", serial, "shell", "uiautomator", "dump", remote],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    result = subprocess.run(
        ["adb", "-s", serial, "exec-out", "cat", remote],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    return result.stdout.decode("utf-8", errors="replace")


def parse_bounds(value: str) -> tuple[int, int, int, int] | None:
    match = BOUNDS_RE.fullmatch(value.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def classify_xml(xml_text: str) -> dict[str, Any]:
    root = ET.fromstring(xml_text)
    rows: list[dict[str, Any]] = []
    all_bounds: list[tuple[int, int, int, int]] = []

    for node in root.iter():
        bounds = parse_bounds(node.attrib.get("bounds", ""))
        if bounds is not None:
            all_bounds.append(bounds)
        if node.attrib.get("content-desc", "").strip() != "TV guide row":
            continue
        text = " ".join(node.attrib.get("text", "").split())
        rows.append({"text": text, "bounds": bounds})

    screen_width = max((item[2] for item in all_bounds), default=0)
    full_width_count = 0
    schedule_gap_rows = 0
    schedule_gap_with_next = 0
    mislabeled_gap_rows = 0
    unavailable_rows = 0
    now_rows = 0

    for row in rows:
        text = row["text"]
        bounds = row["bounds"]

        if bounds is not None:
            left, _, right, _ = bounds
            width = max(0, right - left)
            if screen_width > 0 and width >= int(screen_width * 0.72):
                full_width_count += 1

        if "Now:" in text:
            now_rows += 1
        if "Guide data unavailable" in text:
            unavailable_rows += 1
        if "No current listing" in text:
            schedule_gap_rows += 1
            if "Next:" in text:
                schedule_gap_with_next += 1
        if "Guide data unavailable" in text and "Next:" in text:
            mislabeled_gap_rows += 1

    row_count = len(rows)
    one_column_full_width = row_count >= 2 and full_width_count == row_count

    if (
        one_column_full_width
        and schedule_gap_rows > 0
        and schedule_gap_with_next == schedule_gap_rows
        and mislabeled_gap_rows == 0
    ):
        classification = "D133_EPG_STATUS_ACCURACY_RUNTIME_VALIDATED"
    elif mislabeled_gap_rows > 0:
        classification = "D133_SCHEDULE_GAP_STILL_MISLABELED"
    elif schedule_gap_rows == 0:
        classification = "D133_NO_SCHEDULE_GAP_ROW_VISIBLE"
    else:
        classification = "D133_GUIDE_LAYOUT_REGRESSION_OR_INCOMPLETE_STATUS"

    return {
        "classification": classification,
        "guide_row_count": row_count,
        "full_width_row_count": full_width_count,
        "one_column_full_width": one_column_full_width,
        "now_row_count": now_rows,
        "schedule_gap_row_count": schedule_gap_rows,
        "schedule_gap_with_next_count": schedule_gap_with_next,
        "mislabeled_gap_row_count": mislabeled_gap_rows,
        "guide_unavailable_row_count": unavailable_rows,
    }


def write_report(repo: Path, report: dict[str, Any]) -> int:
    json_path = repo / JSON_REL
    text_path = repo / TEXT_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "PrivyHub D-133 EPG status accuracy probe",
        f"Classification: {report.get('classification')}",
        "",
        "GUIDE LAYOUT",
        f"  guide_row_count: {report.get('guide_row_count', 0)}",
        f"  full_width_row_count: {report.get('full_width_row_count', 0)}",
        f"  one_column_full_width: {report.get('one_column_full_width', False)}",
        "",
        "GUIDE STATUS",
        f"  now_row_count: {report.get('now_row_count', 0)}",
        f"  schedule_gap_row_count: {report.get('schedule_gap_row_count', 0)}",
        f"  schedule_gap_with_next_count: {report.get('schedule_gap_with_next_count', 0)}",
        f"  mislabeled_gap_row_count: {report.get('mislabeled_gap_row_count', 0)}",
        f"  guide_unavailable_row_count: {report.get('guide_unavailable_row_count', 0)}",
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
    good = '<hierarchy><node bounds="[0,0][1920,1080]" />' \
           '<node content-desc="TV guide row" text="A&#10;Now: 3:00 PM - 4:00 PM  Show" bounds="[30,120][1890,220]" />' \
           '<node content-desc="TV guide row" text="B&#10;No current listing&#10;Next: 4:00 PM - 5:00 PM  Later" bounds="[30,230][1890,350]" />' \
           '<node content-desc="TV guide row" text="C&#10;Guide data unavailable" bounds="[30,360][1890,460]" />' \
           '</hierarchy>'
    report = classify_xml(good)
    assert report["classification"] == "D133_EPG_STATUS_ACCURACY_RUNTIME_VALIDATED"
    assert report["schedule_gap_row_count"] == 1
    assert report["mislabeled_gap_row_count"] == 0

    old = '<hierarchy><node bounds="[0,0][1920,1080]" />' \
          '<node content-desc="TV guide row" text="A&#10;Guide data unavailable&#10;Next: 4:00 PM - 5:00 PM  Later" bounds="[30,120][1890,240]" />' \
          '<node content-desc="TV guide row" text="B&#10;Now: 3:00 PM - 4:00 PM  Show" bounds="[30,250][1890,350]" />' \
          '</hierarchy>'
    old_report = classify_xml(old)
    assert old_report["classification"] == "D133_SCHEDULE_GAP_STILL_MISLABELED"
    print("D133_PROBE_SELF_TEST_OK")
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
    session = repo / SESSION_REL
    session.parent.mkdir(parents=True, exist_ok=True)

    if args.prepare:
        session.write_text(
            json.dumps({"prepared_at_ms": int(time.time() * 1000)}, indent=2) + "\n",
            encoding="utf-8",
        )
        return write_report(repo, {
            "classification": "D133_EPG_STATUS_ACCURACY_TEST_PREPARED",
            "guide_row_count": 0,
            "full_width_row_count": 0,
            "one_column_full_width": False,
            "now_row_count": 0,
            "schedule_gap_row_count": 0,
            "schedule_gap_with_next_count": 0,
            "mislabeled_gap_row_count": 0,
            "guide_unavailable_row_count": 0,
        })

    if not session.is_file():
        return write_report(repo, {"classification": "D133_PREPARE_REQUIRED"})

    serial = adb_serial()
    if serial is None:
        return write_report(repo, {"classification": "D133_ADB_UNAVAILABLE"})

    try:
        report = classify_xml(dump_ui(serial))
    except Exception:
        report = {"classification": "D133_UI_SNAPSHOT_FAILED"}
    return write_report(repo, report)


if __name__ == "__main__":
    raise SystemExit(main())
