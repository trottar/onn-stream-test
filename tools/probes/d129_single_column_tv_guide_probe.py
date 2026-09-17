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

SESSION_REL = Path("logs/tv/d129_single_column_tv_guide_session.json")
JSON_REL = Path("logs/tv/d129_single_column_tv_guide_probe.json")
TEXT_REL = Path("logs/tv/d129_single_column_tv_guide_probe.txt")

BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
TIME = r"(?:\d{1,2}:\d{2}(?:\s*[AP]M)?|\d{1,2}(?:\s*[AP]M))"
NOW_RE = re.compile(rf"\bNow:\s+{TIME}\s*-\s*{TIME}\s+\S+", re.IGNORECASE)


def adb_serial() -> str | None:
    try:
        result = subprocess.run(
            ["adb", "devices"], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=10,
        )
    except Exception:
        return None
    devices: list[str] = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices[0] if len(devices) == 1 else None


def dump_ui(serial: str) -> str:
    remote = "/sdcard/privyhub_d129_ui.xml"
    subprocess.run(
        ["adb", "-s", serial, "shell", "uiautomator", "dump", remote],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
    )
    result = subprocess.run(
        ["adb", "-s", serial, "exec-out", "cat", remote],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
    )
    return result.stdout.decode("utf-8", errors="replace")


def parse_bounds(value: str) -> tuple[int, int, int, int] | None:
    match = BOUNDS_RE.fullmatch(value.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def classify_xml(xml_text: str) -> dict[str, Any]:
    root = ET.fromstring(xml_text)
    all_bounds: list[tuple[int, int, int, int]] = []
    guide_rows: list[dict[str, Any]] = []

    for node in root.iter():
        bounds = parse_bounds(node.attrib.get("bounds", ""))
        if bounds is not None:
            all_bounds.append(bounds)
        if node.attrib.get("content-desc", "").strip() != "TV guide row":
            continue
        text = " ".join(node.attrib.get("text", "").split())
        guide_rows.append({"text": text, "bounds": bounds})

    screen_width = max((item[2] for item in all_bounds), default=0)
    full_width_count = 0
    vertical_slots: set[tuple[int, int]] = set()
    now_row_count = 0
    unavailable_count = 0
    marked_count = 0

    for row in guide_rows:
        bounds = row["bounds"]
        text = row["text"]
        if bounds is not None:
            left, top, right, bottom = bounds
            width = max(0, right - left)
            if screen_width > 0 and width >= int(screen_width * 0.72):
                full_width_count += 1
            vertical_slots.add((top, bottom))
        if NOW_RE.search(text):
            now_row_count += 1
        if "Guide data unavailable" in text:
            unavailable_count += 1
        if "Guide marked incorrect" in text:
            marked_count += 1

    row_count = len(guide_rows)
    one_column = (
        row_count >= 2
        and full_width_count == row_count
        and len(vertical_slots) == row_count
    )

    if one_column and now_row_count > 0:
        classification = "D129_SINGLE_COLUMN_TV_GUIDE_RUNTIME_VALIDATED"
    elif one_column:
        classification = "D129_SINGLE_COLUMN_TV_GUIDE_LAYOUT_VALIDATED_NO_PROGRAMMES"
    else:
        classification = "D129_SINGLE_COLUMN_TV_GUIDE_NOT_OBSERVED"

    return {
        "classification": classification,
        "guide_row_count": row_count,
        "full_width_row_count": full_width_count,
        "one_column": one_column,
        "now_row_count": now_row_count,
        "guide_unavailable_row_count": unavailable_count,
        "marked_incorrect_visible_count": marked_count,
        "screen_width": screen_width,
    }


def write_report(repo: Path, report: dict[str, Any]) -> int:
    json_path = repo / JSON_REL
    text_path = repo / TEXT_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "PrivyHub D-129 single-column TV guide probe",
        f"Classification: {report.get('classification')}",
        "",
        "GUIDE LAYOUT",
        f"  guide_row_count: {report.get('guide_row_count', 0)}",
        f"  full_width_row_count: {report.get('full_width_row_count', 0)}",
        f"  one_column: {report.get('one_column', False)}",
        "",
        "GUIDE DATA",
        f"  now_row_count: {report.get('now_row_count', 0)}",
        f"  guide_unavailable_row_count: {report.get('guide_unavailable_row_count', 0)}",
        f"  marked_incorrect_visible_count: {report.get('marked_incorrect_visible_count', 0)}",
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
    xml = '''<hierarchy>
      <node bounds="[0,0][1920,1080]" />
      <node content-desc="TV guide row" text="★ Example One&#10;Now: 3:00 PM - 4:00 PM  Example Show" bounds="[30,120][1890,220]" />
      <node content-desc="TV guide row" text="Example Two&#10;Guide data unavailable" bounds="[30,230][1890,330]" />
      <node content-desc="TV guide row" text="Example Three&#10;Guide marked incorrect" bounds="[30,340][1890,440]" />
    </hierarchy>'''
    report = classify_xml(xml)
    assert report["classification"] == "D129_SINGLE_COLUMN_TV_GUIDE_RUNTIME_VALIDATED"
    assert report["guide_row_count"] == 3
    assert report["full_width_row_count"] == 3
    assert report["one_column"] is True
    assert report["now_row_count"] == 1
    assert report["guide_unavailable_row_count"] == 1
    assert report["marked_incorrect_visible_count"] == 1

    bad = '''<hierarchy><node bounds="[0,0][1920,1080]" />
      <node content-desc="TV guide row" text="A" bounds="[20,100][620,200]" />
      <node content-desc="TV guide row" text="B" bounds="[650,100][1250,200]" />
    </hierarchy>'''
    bad_report = classify_xml(bad)
    assert bad_report["classification"] == "D129_SINGLE_COLUMN_TV_GUIDE_NOT_OBSERVED"
    print("D129_PROBE_SELF_TEST_OK")
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
            "classification": "D129_SINGLE_COLUMN_TV_GUIDE_TEST_PREPARED",
            "guide_row_count": 0,
            "full_width_row_count": 0,
            "one_column": False,
            "now_row_count": 0,
            "guide_unavailable_row_count": 0,
            "marked_incorrect_visible_count": 0,
        })

    if not session.is_file():
        return write_report(repo, {"classification": "D129_PREPARE_REQUIRED"})

    serial = adb_serial()
    if serial is None:
        return write_report(repo, {"classification": "D129_ADB_UNAVAILABLE"})

    try:
        report = classify_xml(dump_ui(serial))
    except Exception:
        report = {"classification": "D129_UI_SNAPSHOT_FAILED"}
    return write_report(repo, report)


if __name__ == "__main__":
    raise SystemExit(main())
