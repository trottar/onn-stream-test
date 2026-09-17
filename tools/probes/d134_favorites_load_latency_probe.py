#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

JSON_REL = Path("logs/tv/d134_favorites_load_latency_probe.json")
TEXT_REL = Path("logs/tv/d134_favorites_load_latency_probe.txt")
SESSION_REL = Path("logs/tv/d134_favorites_load_latency_session.json")

LINE_RE = re.compile(
    r"D134_TV_PAGE\s+session=(?P<session>\d+)\s+stage=(?P<stage>[a-z_]+)(?P<rest>.*)$"
)
FIELD_RE = re.compile(r"([a-z_]+)=([^\s]+)")
REQUIRED = [
    "page_begin", "count", "query", "prefetch",
    "rejected_prefetch", "hydrate", "ui_ready",
]


def adb_serial() -> str | None:
    try:
        result = subprocess.run(
            ["adb", "devices"], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=10,
        )
    except Exception:
        return None
    devices = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device" and not parts[0].startswith("emulator-"):
            devices.append(parts[0])
    return devices[0] if len(devices) == 1 else None


def clear_logcat(serial: str) -> None:
    subprocess.run(
        ["adb", "-s", serial, "logcat", "-c"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
    )


def read_logcat(serial: str) -> str:
    result = subprocess.run(
        ["adb", "-s", serial, "logcat", "-d", "-v", "brief", "PrivyHub:I", "*:S"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=15,
    )
    return result.stdout


def parse_sessions(text: str) -> dict[str, dict[str, dict[str, str]]]:
    sessions = {}
    for raw in text.splitlines():
        match = LINE_RE.search(raw)
        if not match:
            continue
        session = match.group("session")
        stage = match.group("stage")
        fields = {k: v for k, v in FIELD_RE.findall(match.group("rest"))}
        sessions.setdefault(session, {})[stage] = fields
    return sessions


def int_field(stages, stage, name):
    try:
        return int(stages[stage][name])
    except Exception:
        return None


def classify(stages: dict[str, dict[str, str]]) -> dict[str, Any]:
    missing = [stage for stage in REQUIRED if stage not in stages]
    mode = stages.get("page_begin", {}).get("mode", "")

    timings = {
        "count_ms": int_field(stages, "count", "elapsed_ms"),
        "query_ms": int_field(stages, "query", "elapsed_ms"),
        "prefetch_ms": int_field(stages, "prefetch", "elapsed_ms"),
        "rejected_prefetch_ms": int_field(stages, "rejected_prefetch", "elapsed_ms"),
        "hydrate_ms": int_field(stages, "hydrate", "elapsed_ms"),
        "ui_render_ms": int_field(stages, "ui_ready", "elapsed_ms"),
        "total_ms": int_field(stages, "ui_ready", "total_ms"),
    }

    dominant_stage = ""
    dominant_ms = None

    if missing:
        classification = "D134_FAVORITES_LOAD_INCOMPLETE"
    elif mode != "favorites":
        classification = "D134_NON_FAVORITES_PAGE_OBSERVED"
    else:
        pairs = [
            ("count_ms", timings["count_ms"]),
            ("query_ms", timings["query_ms"]),
            ("prefetch_ms", timings["prefetch_ms"]),
            ("rejected_prefetch_ms", timings["rejected_prefetch_ms"]),
            ("hydrate_ms", timings["hydrate_ms"]),
            ("ui_render_ms", timings["ui_render_ms"]),
        ]
        valid = [(name, value) for name, value in pairs if value is not None]
        dominant_stage, dominant_ms = max(valid, key=lambda item: item[1])

        if dominant_stage == "hydrate_ms":
            classification = "D134_FAVORITES_HYDRATE_DOMINANT"
        elif dominant_stage in {"prefetch_ms", "rejected_prefetch_ms"}:
            classification = "D134_FAVORITES_PREFETCH_DOMINANT"
        elif dominant_stage in {"count_ms", "query_ms"}:
            classification = "D134_FAVORITES_DATABASE_DOMINANT"
        elif dominant_stage == "ui_render_ms":
            classification = "D134_FAVORITES_UI_RENDER_DOMINANT"
        else:
            classification = "D134_FAVORITES_MIXED_LATENCY"

    return {
        "classification": classification,
        "mode": mode,
        "missing_stages": missing,
        **timings,
        "dominant_stage": dominant_stage,
        "dominant_stage_ms": dominant_ms,
        "channel_count": int_field(stages, "query", "channels"),
        "prefetch_queued": int_field(stages, "prefetch", "queued"),
        "rejected_prefetch_queued": int_field(stages, "rejected_prefetch", "queued"),
        "hydrated_count": int_field(stages, "hydrate", "hydrated"),
    }


def write_report(repo: Path, report: dict[str, Any]) -> int:
    json_path = repo / JSON_REL
    text_path = repo / TEXT_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "PrivyHub D-134 Favorites load latency probe",
        f"Classification: {report.get('classification')}",
        "",
        "FAVORITES TIMING",
        f"  total_ms: {report.get('total_ms')}",
        f"  count_ms: {report.get('count_ms')}",
        f"  query_ms: {report.get('query_ms')}",
        f"  prefetch_ms: {report.get('prefetch_ms')}",
        f"  rejected_prefetch_ms: {report.get('rejected_prefetch_ms')}",
        f"  hydrate_ms: {report.get('hydrate_ms')}",
        f"  ui_render_ms: {report.get('ui_render_ms')}",
        "",
        "WORK",
        f"  channel_count: {report.get('channel_count')}",
        f"  prefetch_queued: {report.get('prefetch_queued')}",
        f"  rejected_prefetch_queued: {report.get('rejected_prefetch_queued')}",
        f"  hydrated_count: {report.get('hydrated_count')}",
        f"  dominant_stage: {report.get('dominant_stage')}",
        f"  dominant_stage_ms: {report.get('dominant_stage_ms')}",
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
        "I/PrivyHub: D134_TV_PAGE session=100 stage=page_begin mode=favorites total_ms=0",
        "I/PrivyHub: D134_TV_PAGE session=100 stage=count elapsed_ms=2 total_ms=2 count=21",
        "I/PrivyHub: D134_TV_PAGE session=100 stage=query elapsed_ms=3 total_ms=5 channels=21",
        "I/PrivyHub: D134_TV_PAGE session=100 stage=prefetch elapsed_ms=12 total_ms=17 queued=5",
        "I/PrivyHub: D134_TV_PAGE session=100 stage=rejected_prefetch elapsed_ms=1 total_ms=18 queued=0",
        "I/PrivyHub: D134_TV_PAGE session=100 stage=hydrate elapsed_ms=16000 total_ms=16018 hydrated=3",
        "I/PrivyHub: D134_TV_PAGE session=100 stage=ui_ready elapsed_ms=250 total_ms=16268",
    ])
    stages = parse_sessions(synthetic)["100"]
    report = classify(stages)
    assert report["classification"] == "D134_FAVORITES_HYDRATE_DOMINANT"
    assert report["hydrate_ms"] == 16000
    assert report["total_ms"] == 16268
    assert report["channel_count"] == 21

    incomplete = dict(stages)
    incomplete.pop("hydrate")
    assert classify(incomplete)["classification"] == "D134_FAVORITES_LOAD_INCOMPLETE"
    print("D134_PROBE_SELF_TEST_OK")
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
        return write_report(repo, {"classification": "D134_ADB_UNAVAILABLE"})

    session_path = repo / SESSION_REL
    session_path.parent.mkdir(parents=True, exist_ok=True)

    if args.prepare:
        clear_logcat(serial)
        session_path.write_text(
            json.dumps({"prepared_at_ms": int(time.time() * 1000)}, indent=2) + "\n",
            encoding="utf-8",
        )
        return write_report(repo, {"classification": "D134_FAVORITES_LOAD_TEST_PREPARED"})

    if not session_path.is_file():
        return write_report(repo, {"classification": "D134_PREPARE_REQUIRED"})

    try:
        sessions = parse_sessions(read_logcat(serial))
    except Exception:
        sessions = {}

    selected = None
    for session_id in sorted(sessions, key=lambda value: int(value), reverse=True):
        stages = sessions[session_id]
        if stages.get("page_begin", {}).get("mode") == "favorites":
            selected = stages
            break

    if selected is None:
        return write_report(repo, {"classification": "D134_FAVORITES_PAGE_NOT_OBSERVED"})

    return write_report(repo, classify(selected))


if __name__ == "__main__":
    raise SystemExit(main())
