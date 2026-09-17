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

SESSION_REL = Path("logs/tv/d128_guide_style_ui_session.json")
JSON_REL = Path("logs/tv/d128_guide_style_ui_probe.json")
TEXT_REL = Path("logs/tv/d128_guide_style_ui_probe.txt")

TIME = r"(?:\d{1,2}:\d{2}(?:\s*[AP]M)?|\d{1,2}(?:\s*[AP]M))"
NOW_RE = re.compile(rf"\bNow:\s+{TIME}\s*-\s*{TIME}\s+\S+", re.IGNORECASE)
NEXT_RE = re.compile(rf"\bNext:\s+{TIME}\s*-\s*{TIME}\s+\S+", re.IGNORECASE)


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


def dump_ui(serial: str) -> str:
    subprocess.run(
        ["adb", "-s", serial, "shell", "uiautomator", "dump", "/sdcard/privyhub_d128_ui.xml"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    result = subprocess.run(
        ["adb", "-s", serial, "exec-out", "cat", "/sdcard/privyhub_d128_ui.xml"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    return result.stdout.decode("utf-8", errors="replace")


def extract_texts(xml_text: str) -> list[str]:
    root = ET.fromstring(xml_text)
    out: list[str] = []
    for node in root.iter():
        for key in ("text", "content-desc"):
            value = node.attrib.get(key, "").strip()
            if value:
                out.append(" ".join(value.split()))
    return out


def classify_texts(texts: list[str]) -> dict[str, Any]:
    joined = "\n".join(texts)
    now_matches = NOW_RE.findall(joined)
    next_matches = NEXT_RE.findall(joined)
    marked = sum(1 for value in texts if "Guide marked incorrect" in value)
    ok = bool(now_matches) and bool(next_matches)
    return {
        "classification": (
            "D128_GUIDE_STYLE_FAVORITES_RUNTIME_VALIDATED"
            if ok else "D128_GUIDE_STYLE_ROWS_NOT_OBSERVED"
        ),
        "now_row_count": len(now_matches),
        "next_row_count": len(next_matches),
        "marked_incorrect_visible_count": marked,
        "now_rows_present": bool(now_matches),
        "next_rows_present": bool(next_matches),
    }


def write_report(repo: Path, report: dict[str, Any]) -> int:
    json_path = repo / JSON_REL
    text_path = repo / TEXT_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "PrivyHub D-128 guide-style UI probe",
        f"Classification: {report.get('classification')}",
        "",
        "VISIBLE GUIDE ROWS",
        f"  now_row_count: {report.get('now_row_count', 0)}",
        f"  next_row_count: {report.get('next_row_count', 0)}",
        f"  marked_incorrect_visible_count: {report.get('marked_incorrect_visible_count', 0)}",
        "",
        "CHECKS",
        f"  now_rows_present: {report.get('now_rows_present', False)}",
        f"  next_rows_present: {report.get('next_rows_present', False)}",
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
    xml = '''<hierarchy><node text="★ Example Channel&#10;Now: 3:00 PM - 4:00 PM  Example Show&#10;Next: 4:00 PM - 5:00 PM  Next Show"/><node text="Guide marked incorrect"/></hierarchy>'''
    texts = extract_texts(xml)
    report = classify_texts(texts)
    assert report["classification"] == "D128_GUIDE_STYLE_FAVORITES_RUNTIME_VALIDATED"
    assert report["now_row_count"] == 1
    assert report["next_row_count"] == 1
    assert report["marked_incorrect_visible_count"] == 1
    bad = classify_texts(["Channel without guide"])
    assert bad["classification"] == "D128_GUIDE_STYLE_ROWS_NOT_OBSERVED"
    print("D128_PROBE_SELF_TEST_OK")
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
            "classification": "D128_GUIDE_STYLE_TEST_PREPARED",
            "now_row_count": 0,
            "next_row_count": 0,
            "marked_incorrect_visible_count": 0,
            "now_rows_present": False,
            "next_rows_present": False,
        })

    if not session.is_file():
        return write_report(repo, {"classification": "D128_PREPARE_REQUIRED"})

    serial = adb_serial()
    if serial is None:
        return write_report(repo, {"classification": "D128_ADB_UNAVAILABLE"})

    try:
        xml_text = dump_ui(serial)
        texts = extract_texts(xml_text)
        report = classify_texts(texts)
    except Exception:
        report = {"classification": "D128_UI_SNAPSHOT_FAILED"}
    return write_report(repo, report)


if __name__ == "__main__":
    raise SystemExit(main())
