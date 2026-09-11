#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b1_b2_completion_gap_audit_v1"
CLASSIFICATION = "B1_B2_COMPLETION_GAPS_CAPTURED"

TARGETS = {
    "diagnostics_activity": (
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
        "diagnostics/DiagnosticsActivity.kt"
    ),
    "health_model": "companion/diagnostics/health_model.py",
    "runtime_health": "companion/diagnostics/runtime_health.py",
    "client_feedback": "companion/diagnostics/client_feedback.py",
    "retention": "companion/diagnostics/retention.py",
    "companion_service": "companion/privyhub_service.py",
    "debug_bundle": "tools/privyhub_debug_bundle.py",
    "debug_harness": "tools/run_privyhub_debug.ps1",
}

EVENT_TOKENS = (
    "deque(",
    "maxlen=",
    "event_history",
    "diagnostic_event",
    "event_code",
    "remediation",
    "causal",
    "privacy_classification",
)

GUI_BUNDLE_TOKENS = (
    "COLLECT DIAGNOSTICS",
    "Collect Diagnostics",
    "privyhub_debug_bundle",
    "SHARE_ME",
)

SELF_TEST_TOKENS = (
    "RUN SELF-TEST",
    "Health contract",
    "Component model",
    "Resource sampling contract",
    "Benchmark threshold guard",
    "Live client feedback",
    "storage",
    "writable",
    "ADB",
    "controller",
    "audio",
    "RetroArch",
)

BUNDLE_TOKENS = (
    "IPV4_RE",
    "IPV6_CANDIDATE_RE",
    "MAC_RE",
    "SHARE_ME",
    "manifest",
    "sha256",
    "pktmon.etl",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )


def token_info(
    text: str,
    tokens: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    lines = text.splitlines()

    for token in tokens:
        locations = [
            index
            for index, line in enumerate(lines, 1)
            if token.casefold() in line.casefold()
        ]
        result[token] = {
            "count": text.casefold().count(token.casefold()),
            "lines": locations[:20],
        }

    return result


def source_state(
    root: Path,
    rel: str,
) -> dict[str, Any]:
    path = root / rel
    if not path.is_file():
        return {
            "path": rel,
            "exists": False,
        }

    text = read_text(path)
    return {
        "path": rel,
        "exists": True,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "lines": len(text.splitlines()),
        "event_tokens": token_info(text, EVENT_TOKENS),
        "gui_bundle_tokens": token_info(text, GUI_BUNDLE_TOKENS),
        "self_test_tokens": token_info(text, SELF_TEST_TOKENS),
        "bundle_tokens": token_info(text, BUNDLE_TOKENS),
    }


def bool_token(
    state: dict[str, Any],
    group: str,
    token: str,
) -> bool:
    info = (
        state.get(group, {})
        if isinstance(state.get(group), dict)
        else {}
    )
    row = info.get(token, {})
    return bool(
        isinstance(row, dict)
        and int(row.get("count", 0)) > 0
    )


def build_report(root: Path) -> dict[str, Any]:
    states = {
        name: source_state(root, rel)
        for name, rel in TARGETS.items()
    }

    diagnostics_dir = root / "companion/diagnostics"
    combined_diagnostics = ""

    if diagnostics_dir.is_dir():
        chunks = []
        for path in sorted(diagnostics_dir.glob("*.py")):
            try:
                chunks.append(read_text(path))
            except OSError:
                continue
        combined_diagnostics = "\n".join(chunks)

    event_info = token_info(
        combined_diagnostics,
        EVENT_TOKENS,
    )

    bounded_event_history = (
        event_info["deque("]["count"] > 0
        and event_info["maxlen="]["count"] > 0
        and (
            event_info["event_history"]["count"] > 0
            or event_info["diagnostic_event"]["count"] > 0
        )
    )

    activity = states["diagnostics_activity"]
    debug_bundle = states["debug_bundle"]

    gui_bundle_action = any(
        bool_token(
            activity,
            "gui_bundle_tokens",
            token,
        )
        for token in GUI_BUNDLE_TOKENS
    )

    sanitized_bundle_tool = (
        debug_bundle.get("exists", False)
        and any(
            bool_token(
                debug_bundle,
                "bundle_tokens",
                token,
            )
            for token in (
                "IPV4_RE",
                "IPV6_CANDIDATE_RE",
                "MAC_RE",
            )
        )
        and bool_token(
            debug_bundle,
            "bundle_tokens",
            "SHARE_ME",
        )
    )

    self_test_present = bool_token(
        activity,
        "self_test_tokens",
        "RUN SELF-TEST",
    )

    dedicated_storage_test = (
        bool_token(
            activity,
            "self_test_tokens",
            "writable",
        )
        or bool_token(
            activity,
            "self_test_tokens",
            "storage",
        )
    )

    dedicated_adb_test = bool_token(
        activity,
        "self_test_tokens",
        "ADB",
    )

    component_derived_audio = bool_token(
        activity,
        "self_test_tokens",
        "audio",
    )
    component_derived_controller = bool_token(
        activity,
        "self_test_tokens",
        "controller",
    )
    component_derived_retroarch = bool_token(
        activity,
        "self_test_tokens",
        "RetroArch",
    )

    gaps = []

    if not bounded_event_history:
        gaps.append(
            "ROADMAP_B1_3_BOUNDED_COMMON_EVENT_HISTORY"
        )

    if not gui_bundle_action:
        gaps.append(
            "ROADMAP_B2_2_GUI_SANITIZED_BUNDLE_ACTION"
        )

    if not dedicated_storage_test:
        gaps.append(
            "ROADMAP_B2_1_STORAGE_WRITABILITY_SELF_TEST"
        )

    if not dedicated_adb_test:
        gaps.append(
            "ROADMAP_B2_1_ADB_DEVELOPMENT_SELF_TEST"
        )

    if gaps:
        disposition = (
            "COMPLETE_REMAINING_B1_B2_REQUIREMENTS_BEFORE_B3"
        )
    else:
        disposition = "B1_B2_COMPLETE_READY_FOR_B3"

    return {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "production_files_modified_by_probe": "NONE",
        "network_addresses_collected_or_logged": "NONE",
        "source": states,
        "roadmap_checks": {
            "health_snapshot": True,
            "gui_diagnostics": activity.get("exists", False),
            "self_test_present": self_test_present,
            "bounded_common_event_history": bounded_event_history,
            "sanitized_bundle_tool_exists": sanitized_bundle_tool,
            "gui_sanitized_bundle_action": gui_bundle_action,
            "dedicated_storage_writability_check": dedicated_storage_test,
            "dedicated_adb_development_check": dedicated_adb_test,
            "audio_visible_to_self_test": component_derived_audio,
            "controller_visible_to_self_test": component_derived_controller,
            "retroarch_visible_to_self_test": component_derived_retroarch,
        },
        "event_history_tokens": event_info,
        "remaining_gaps": gaps,
        "disposition": disposition,
        "recommended_sequence": [
            "ADD_BOUNDED_COMMON_DIAGNOSTIC_EVENT_HISTORY",
            "WIRE_GUI_COLLECT_DIAGNOSTICS_TO_SANITIZED_BUNDLE",
            "ADD_MISSING_BOUNDED_SELF_TEST_CHECKS_WHERE_APPLICABLE",
            "RUNTIME_VALIDATE_B1_B2_COMPLETION",
            "BEGIN_B3_SUNSHINE_MOONLIGHT_INVENTORY",
        ],
    }


def format_text(report: dict[str, Any]) -> str:
    checks = report["roadmap_checks"]

    lines = [
        "PrivyHub Phase B1/B2 completion-gap audit",
        f"Classification: {report['classification']}",
        f"Schema: {report['schema']}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== EXACT SOURCE HASHES ===",
    ]

    for name, state in report["source"].items():
        if not state.get("exists", False):
            lines.append(
                f"{name}: MISSING path={state['path']}"
            )
            continue

        lines.append(
            f"{name}: sha256={state['sha256']} "
            f"bytes={state['bytes']} lines={state['lines']} "
            f"path={state['path']}"
        )

    lines += [
        "",
        "=== ROADMAP COMPLETION CHECK ===",
        f"Health snapshot present: {checks['health_snapshot']}",
        f"GUI Diagnostics present: {checks['gui_diagnostics']}",
        f"Self-Test present: {checks['self_test_present']}",
        "Bounded common diagnostic event history present: "
        + str(checks["bounded_common_event_history"]),
        "Sanitized bundle tool exists: "
        + str(checks["sanitized_bundle_tool_exists"]),
        "GUI Collect Diagnostics action present: "
        + str(checks["gui_sanitized_bundle_action"]),
        "Dedicated storage-writability Self-Test check present: "
        + str(checks["dedicated_storage_writability_check"]),
        "Dedicated ADB/development Self-Test check present: "
        + str(checks["dedicated_adb_development_check"]),
        "Audio visible to Self-Test: "
        + str(checks["audio_visible_to_self_test"]),
        "Controller visible to Self-Test: "
        + str(checks["controller_visible_to_self_test"]),
        "RetroArch visible to Self-Test: "
        + str(checks["retroarch_visible_to_self_test"]),
        "",
        "=== EVENT-HISTORY SIGNALS ===",
    ]

    for token, info in report["event_history_tokens"].items():
        lines.append(
            f"{token}: count={info['count']} "
            f"lines={','.join(str(v) for v in info['lines']) or '<none>'}"
        )

    lines += [
        "",
        "=== REMAINING GAPS ===",
    ]

    if report["remaining_gaps"]:
        lines.extend(
            f"- {value}"
            for value in report["remaining_gaps"]
        )
    else:
        lines.append("<none>")

    lines += [
        "",
        "Disposition: " + report["disposition"],
        "",
        "=== RECOMMENDED SEQUENCE ===",
    ]

    lines.extend(
        f"{index}. {value}"
        for index, value in enumerate(
            report["recommended_sequence"],
            1,
        )
    )

    lines += [
        "",
        "Return this file before beginning B3.",
    ]

    return "\n".join(lines) + "\n"


def self_test() -> int:
    fixture = """
from collections import deque
_event_history = deque(maxlen=128)
def add_diagnostic_event(event_code):
    pass
"""
    info = token_info(fixture, EVENT_TOKENS)
    assert info["deque("]["count"] == 1
    assert info["maxlen="]["count"] == 1
    assert info["event_history"]["count"] == 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()
    report = build_report(root)

    out_dir = root / "logs/diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "b1_b2_completion_gaps.json").write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    (out_dir / "b1_b2_completion_gaps.txt").write_text(
        format_text(report),
        encoding="utf-8",
        newline="\n",
    )

    print(CLASSIFICATION)
    print(
        "Text:",
        out_dir / "b1_b2_completion_gaps.txt",
    )
    print(
        "JSON:",
        out_dir / "b1_b2_completion_gaps.json",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
