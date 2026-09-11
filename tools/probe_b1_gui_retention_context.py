#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b1_gui_retention_context_v1"
CLASSIFICATION = "B1_GUI_SELF_TEST_RETENTION_CONTEXT_CAPTURED"

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

SOURCE_TARGETS = {
    "main_activity": (
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt"
    ),
    "manifest": (
        "PrivyHub/app/src/main/AndroidManifest.xml"
    ),
    "udp_forward_activity": (
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
        "diagnostics/UdpTransportProbeActivity.kt"
    ),
    "udp_reverse_activity": (
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
        "diagnostics/UdpReverseTransportProbeActivity.kt"
    ),
    "udp_loopback_activity": (
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
        "diagnostics/UdpLoopbackProbeActivity.kt"
    ),
    "companion_service": "companion/privyhub_service.py",
    "health_model": "companion/diagnostics/health_model.py",
    "runtime_health": "companion/diagnostics/runtime_health.py",
    "debug_harness": "tools/run_privyhub_debug.ps1",
    "debug_bundle": "tools/privyhub_debug_bundle.py",
}

LOG_FAMILIES = (
    ("diagnostics", "logs/diagnostics"),
    ("decoder_sessions", "logs/games/decoder_sessions"),
    ("host_telemetry", "logs/games/host_telemetry"),
    ("audio_timing", "logs/games/audio_timing"),
    ("capture_diagnostics", "logs/games/capture_diagnostics"),
    ("debug_bundles", "logs/debug_bundles"),
    ("transport_forward", "logs/transport_probe"),
    ("transport_reverse", "logs/transport_reverse"),
    ("transport_loopback", "logs/transport_loopback"),
    ("repo_audit", "logs/repo_audit"),
    ("android_diagnostics", "logs/android"),
)

UI_TOKENS = (
    "Diagnostics",
    "Developer",
    "Settings",
    "Troubleshoot",
    "Debug",
    "UdpTransportProbeActivity",
    "UdpReverseTransportProbeActivity",
    "UdpLoopbackProbeActivity",
    "startActivity(",
    "Intent(",
    "setOnClickListener",
    "LinearLayout",
    "ScrollView",
    "Button(",
)

RETENTION_TOKENS = (
    "retention",
    "max_age",
    "max_count",
    "max_bytes",
    "MAX_SAMPLES",
    "unlink(",
    "rmtree(",
    "glob(",
)

HARNESS_TOKENS = (
    "GameSmear",
    "CollectLatest",
    "TransportHistory",
    "AudioHistory",
    "SHARE_ME",
    "IPV4_RE",
    "IPV6_CANDIDATE_RE",
    "MAC_RE",
    "pktmon.etl",
)

METHOD_RE = re.compile(
    r"\b(?:private|protected|public|internal)?\s*"
    r"(?:suspend\s+)?fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
)

ACTIVITY_NAME_RE = re.compile(
    r"\b([A-Z][A-Za-z0-9_]*Activity)\b"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )


def line_numbers(
    source: str,
    token: str,
    *,
    limit: int = 16,
) -> list[int]:
    folded = token.casefold()
    result = []

    for index, line in enumerate(
        source.splitlines(),
        1,
    ):
        if folded in line.casefold():
            result.append(index)
            if len(result) >= limit:
                break

    return result


def token_rows(
    source: str,
    tokens: tuple[str, ...],
) -> dict[str, Any]:
    folded = source.casefold()
    result = {}

    for token in tokens:
        count = folded.count(
            token.casefold()
        )
        result[token] = {
            "count": count,
            "lines": line_numbers(
                source,
                token,
            ),
        }

    return result


def methods(source: str) -> list[str]:
    return sorted(
        set(
            METHOD_RE.findall(
                source
            )
        )
    )


def activity_names(source: str) -> list[str]:
    return sorted(
        set(
            ACTIVITY_NAME_RE.findall(
                source
            )
        )
    )


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

    source = text(
        path
    )

    return {
        "path": rel,
        "exists": True,
        "bytes": path.stat().st_size,
        "line_count": len(
            source.splitlines()
        ),
        "sha256": sha256(
            path
        ),
        "methods": methods(
            source
        ),
        "activity_names": activity_names(
            source
        ),
        "ui_tokens": token_rows(
            source,
            UI_TOKENS,
        ),
        "retention_tokens": token_rows(
            source,
            RETENTION_TOKENS,
        ),
        "harness_tokens": token_rows(
            source,
            HARNESS_TOKENS,
        ),
    }


def manifest_activities(
    root: Path,
) -> list[dict[str, Any]]:
    path = root / SOURCE_TARGETS[
        "manifest"
    ]

    if not path.is_file():
        return []

    try:
        tree = ET.parse(
            path
        )
    except ET.ParseError:
        return []

    result = []

    for node in tree.findall(
        ".//activity"
    ):
        name = (
            node.attrib.get(
                ANDROID_NS + "name",
                "",
            )
        )
        if not name:
            continue

        if (
            "diagnostic" not in name.casefold()
            and "probe" not in name.casefold()
        ):
            continue

        result.append(
            {
                "name": name,
                "exported": node.attrib.get(
                    ANDROID_NS + "exported"
                ),
            }
        )

    return result


def request_health() -> dict[str, Any]:
    request = urllib.request.Request(
        "http://127.0.0.1:8765"
        "/diagnostics/health",
        headers={
            "Cache-Control": "no-cache",
        },
        method="GET",
    )

    with urllib.request.urlopen(
        request,
        timeout=3.0,
    ) as response:
        payload = json.loads(
            response.read().decode(
                "utf-8"
            )
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise RuntimeError(
            "Health endpoint did not return a JSON object"
        )

    return payload


def health_shape() -> dict[str, Any]:
    try:
        payload = request_health()
    except (
        urllib.error.URLError,
        TimeoutError,
        ConnectionError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        RuntimeError,
    ) as exc:
        return {
            "available": False,
            "error_class": type(
                exc
            ).__name__,
        }

    components = (
        payload.get(
            "components"
        )
        if isinstance(
            payload.get(
                "components"
            ),
            list,
        )
        else []
    )

    component_rows = []
    for item in components:
        if not isinstance(
            item,
            dict,
        ):
            continue
        component_rows.append(
            {
                "component": item.get(
                    "component"
                ),
                "health": item.get(
                    "health"
                ),
                "severity": item.get(
                    "severity"
                ),
                "event_code": item.get(
                    "event_code"
                ),
            }
        )

    overall = (
        payload.get(
            "overall"
        )
        if isinstance(
            payload.get(
                "overall"
            ),
            dict,
        )
        else {}
    )

    resources = (
        payload.get(
            "resources"
        )
        if isinstance(
            payload.get(
                "resources"
            ),
            dict,
        )
        else {}
    )

    collection = (
        payload.get(
            "collection"
        )
        if isinstance(
            payload.get(
                "collection"
            ),
            dict,
        )
        else {}
    )

    return {
        "available": True,
        "schema": payload.get(
            "schema"
        ),
        "overall_health": overall.get(
            "health"
        ),
        "overall_severity": overall.get(
            "severity"
        ),
        "component_count": len(
            component_rows
        ),
        "components": component_rows,
        "resource_schema": resources.get(
            "schema"
        ),
        "resource_scope": resources.get(
            "measurement_scope"
        ),
        "client_feedback_available": collection.get(
            "client_feedback_available"
        ),
        "client_feedback_fresh": collection.get(
            "client_feedback_fresh"
        ),
        "client_feedback_payload_bytes": collection.get(
            "client_feedback_payload_bytes"
        ),
        "new_resource_sampler_started": collection.get(
            "new_resource_sampler_started"
        ),
    }


def family_stats(
    root: Path,
    name: str,
    rel: str,
) -> dict[str, Any]:
    directory = root / rel

    result: dict[str, Any] = {
        "name": name,
        "path": rel,
        "exists": directory.is_dir(),
        "file_count": 0,
        "total_bytes": 0,
        "extensions": {},
        "oldest_age_seconds": None,
        "newest_age_seconds": None,
        "largest_file_bytes": 0,
    }

    if not directory.is_dir():
        return result

    files = [
        path
        for path in directory.rglob(
            "*"
        )
        if path.is_file()
    ]

    result[
        "file_count"
    ] = len(
        files
    )
    result[
        "total_bytes"
    ] = sum(
        path.stat().st_size
        for path in files
    )
    result[
        "extensions"
    ] = dict(
        sorted(
            Counter(
                path.suffix.lower()
                or "<none>"
                for path in files
            ).items()
        )
    )

    if files:
        mtimes = [
            path.stat().st_mtime
            for path in files
        ]
        now = time.time()
        result[
            "oldest_age_seconds"
        ] = round(
            max(
                0.0,
                now - min(
                    mtimes
                ),
            ),
            3,
        )
        result[
            "newest_age_seconds"
        ] = round(
            max(
                0.0,
                now - max(
                    mtimes
                ),
            ),
            3,
        )
        result[
            "largest_file_bytes"
        ] = max(
            path.stat().st_size
            for path in files
        )

    return result


def retention_candidates(
    families: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []

    for item in families:
        bytes_total = int(
            item.get(
                "total_bytes",
                0,
            )
        )
        count = int(
            item.get(
                "file_count",
                0,
            )
        )

        if (
            bytes_total <= 0
            and count <= 0
        ):
            pressure = "none"
        elif (
            bytes_total >=
            100 * 1024 * 1024
        ):
            pressure = "high"
        elif (
            bytes_total >=
            20 * 1024 * 1024
            or count >= 100
        ):
            pressure = "moderate"
        else:
            pressure = "low"

        rows.append(
            {
                "name": item[
                    "name"
                ],
                "path": item[
                    "path"
                ],
                "pressure": pressure,
                "file_count": count,
                "total_bytes": bytes_total,
            }
        )

    return rows


def classify_gui(
    states: dict[str, Any],
    manifest_rows: list[dict[str, Any]],
    health: dict[str, Any],
) -> dict[str, Any]:
    main = states[
        "main_activity"
    ]

    line_count = int(
        main.get(
            "line_count",
            0,
        )
        or 0
    )

    diagnostics_activity_count = len(
        manifest_rows
    )

    health_ready = bool(
        health.get(
            "available",
            False,
        )
        and health.get(
            "schema"
        )
        == "privyhub_diagnostics_health_v1"
    )

    if (
        line_count >= 8_000
        and diagnostics_activity_count > 0
        and health_ready
    ):
        disposition = (
            "STANDALONE_DIAGNOSTICS_ACTIVITY_PREFERRED"
        )
        reason = (
            "MainActivity is already large, standalone diagnostics activities "
            "already exist, and the read-only health endpoint is available."
        )
    elif health_ready:
        disposition = (
            "HEALTH_ENDPOINT_READY_GUI_ANCHOR_NEEDS_CONTEXT"
        )
        reason = (
            "The backend contract is ready, but Android navigation context "
            "needs a narrower integration decision."
        )
    else:
        disposition = (
            "GUI_BLOCKED_ON_HEALTH_ENDPOINT"
        )
        reason = (
            "Do not build GUI diagnostics until the health endpoint is available."
        )

    return {
        "disposition": disposition,
        "reason": reason,
        "main_activity_line_count": (
            line_count
        ),
        "manifest_diagnostics_activity_count": (
            diagnostics_activity_count
        ),
        "health_endpoint_ready": (
            health_ready
        ),
    }


def git_head(
    root: Path,
) -> str:
    proc = subprocess.run(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return (
        proc.stdout.strip()
        if proc.returncode == 0
        else "<unknown>"
    )


def build_report(
    root: Path,
) -> dict[str, Any]:
    states = {
        name: source_state(
            root,
            rel,
        )
        for name, rel in SOURCE_TARGETS.items()
    }

    manifest_rows = (
        manifest_activities(
            root
        )
    )
    health = health_shape()

    families = [
        family_stats(
            root,
            name,
            rel,
        )
        for name, rel in LOG_FAMILIES
    ]

    retention = (
        retention_candidates(
            families
        )
    )

    gui = classify_gui(
        states,
        manifest_rows,
        health,
    )

    harness = states[
        "debug_harness"
    ]
    bundle = states[
        "debug_bundle"
    ]

    existing_self_test_inputs = {
        "health_endpoint": bool(
            health.get(
                "available",
                False,
            )
        ),
        "debug_harness": bool(
            harness.get(
                "exists",
                False,
            )
        ),
        "sanitized_bundle": bool(
            bundle.get(
                "exists",
                False,
            )
        ),
        "android_probe_activities": (
            len(
                manifest_rows
            )
        ),
    }

    high_pressure = [
        item[
            "name"
        ]
        for item in retention
        if item[
            "pressure"
        ]
        == "high"
    ]

    moderate_pressure = [
        item[
            "name"
        ]
        for item in retention
        if item[
            "pressure"
        ]
        == "moderate"
    ]

    return {
        "schema": SCHEMA,
        "classification": (
            CLASSIFICATION
        ),
        "production_files_modified_by_probe": (
            "NONE"
        ),
        "network_addresses_collected_or_logged": (
            "NONE"
        ),
        "retention_files_deleted": 0,
        "git_head": git_head(
            root
        ),
        "source": states,
        "manifest_diagnostics_activities": (
            manifest_rows
        ),
        "health_endpoint": health,
        "gui": gui,
        "self_test_inputs": (
            existing_self_test_inputs
        ),
        "log_families": families,
        "retention": {
            "candidates": retention,
            "high_pressure": (
                high_pressure
            ),
            "moderate_pressure": (
                moderate_pressure
            ),
            "deletion_performed": False,
            "policy_applied": False,
            "curated_evidence_excluded_from_deletion_design": True,
            "raw_memory_evidence_excluded_from_deletion_design": True,
        },
        "recommended_next_step": (
            "BUILD_STANDALONE_DIAGNOSTICS_ACTIVITY_AND_SAFE_RETENTION_POLICY"
            if (
                gui[
                    "disposition"
                ]
                == "STANDALONE_DIAGNOSTICS_ACTIVITY_PREFERRED"
            )
            else "INSPECT_GUI_ANCHOR_BEFORE_PRODUCTION_PATCH"
        ),
    }


def format_token_section(
    label: str,
    values: dict[str, Any],
) -> list[str]:
    lines = [
        label
    ]

    emitted = False
    for token, info in values.items():
        count = int(
            info.get(
                "count",
                0,
            )
        )
        if count <= 0:
            continue

        emitted = True
        locations = ",".join(
            str(value)
            for value in info.get(
                "lines",
                []
            )
        )

        lines.append(
            f"{token}: count={count} "
            f"lines={locations or '<none>'}"
        )

    if not emitted:
        lines.append(
            "<none>"
        )

    return lines


def mib(
    value: int,
) -> float:
    return (
        float(
            value
        )
        / 1024.0
        / 1024.0
    )


def format_text(
    report: dict[str, Any],
) -> str:
    lines = [
        "PrivyHub Phase B1.8 GUI/Self-Test + retention context audit",
        f"Classification: {report['classification']}",
        f"Schema: {report['schema']}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "Retention files deleted: 0",
        "",
        "=== CHECKPOINT ===",
        f"Git HEAD: {report['git_head']}",
        "",
        "=== EXACT SOURCE CONTEXT ===",
    ]

    for name, item in report[
        "source"
    ].items():
        if not item.get(
            "exists",
            False,
        ):
            lines.append(
                f"{name}: MISSING "
                f"path={item['path']}"
            )
            continue

        lines.append(
            f"{name}: sha256={item['sha256']} "
            f"bytes={item['bytes']} "
            f"lines={item['line_count']} "
            f"path={item['path']}"
        )

    main = report[
        "source"
    ][
        "main_activity"
    ]

    lines += [
        "",
        *format_token_section(
            "=== MAIN ACTIVITY UI/NAVIGATION TOKENS ===",
            main.get(
                "ui_tokens",
                {},
            ),
        ),
        "",
        "=== EXISTING DIAGNOSTICS ACTIVITIES ===",
    ]

    activities = report[
        "manifest_diagnostics_activities"
    ]

    if activities:
        for item in activities:
            lines.append(
                f"{item['name']}: "
                f"exported={item['exported']}"
            )
    else:
        lines.append(
            "<none>"
        )

    health = report[
        "health_endpoint"
    ]

    lines += [
        "",
        "=== HEALTH ENDPOINT GUI INPUT ===",
        f"Available: {health.get('available', False)}",
        f"Schema: {health.get('schema', '<none>')}",
        f"Overall health: {health.get('overall_health', '<unknown>')}",
        f"Overall severity: {health.get('overall_severity', '<unknown>')}",
        f"Component count: {health.get('component_count', 0)}",
        "Resource scope: "
        + str(
            health.get(
                "resource_scope",
                "<unknown>",
            )
        ),
        "Client feedback available: "
        + str(
            health.get(
                "client_feedback_available",
                "<unknown>",
            )
        ),
        "Client feedback fresh: "
        + str(
            health.get(
                "client_feedback_fresh",
                "<unknown>",
            )
        ),
        "Client feedback payload bytes: "
        + str(
            health.get(
                "client_feedback_payload_bytes",
                "<unknown>",
            )
        ),
        "New resource sampler started: "
        + str(
            health.get(
                "new_resource_sampler_started",
                "<unknown>",
            )
        ),
        "",
        "=== GUI ARCHITECTURE ===",
        "Disposition: "
        + report[
            "gui"
        ][
            "disposition"
        ],
        "MainActivity line count: "
        + str(
            report[
                "gui"
            ][
                "main_activity_line_count"
            ]
        ),
        "Manifest diagnostics activity count: "
        + str(
            report[
                "gui"
            ][
                "manifest_diagnostics_activity_count"
            ]
        ),
        "Health endpoint ready: "
        + str(
            report[
                "gui"
            ][
                "health_endpoint_ready"
            ]
        ),
        "Reason: "
        + report[
            "gui"
        ][
            "reason"
        ],
        "",
        "=== SELF-TEST INPUTS ===",
    ]

    for key, value in report[
        "self_test_inputs"
    ].items():
        lines.append(
            f"{key}: {value}"
        )

    lines += [
        "",
        "=== DIAGNOSTIC STORAGE / RETENTION PRESSURE ===",
    ]

    for item in report[
        "retention"
    ][
        "candidates"
    ]:
        lines.append(
            f"{item['name']}: "
            f"pressure={item['pressure']} "
            f"files={item['file_count']} "
            f"bytes={item['total_bytes']} "
            f"MiB={mib(item['total_bytes']):.3f} "
            f"path={item['path']}"
        )

    lines += [
        "",
        "High-pressure families: "
        + (
            ", ".join(
                report[
                    "retention"
                ][
                    "high_pressure"
                ]
            )
            or "<none>"
        ),
        "Moderate-pressure families: "
        + (
            ", ".join(
                report[
                    "retention"
                ][
                    "moderate_pressure"
                ]
            )
            or "<none>"
        ),
        "Retention policy applied: False",
        "Curated docs/memory evidence eligible for automatic deletion: False",
        "Local raw docs/memory evidence eligible for this retention policy: False",
        "",
        "=== NEXT STEP ===",
        report[
            "recommended_next_step"
        ],
        "",
        "Return this file before the GUI/retention production patch.",
    ]

    return "\n".join(
        lines
    ) + "\n"


def self_test() -> int:
    fake = """
class MainActivity {
    fun openThing() {
        val button = Button(this)
        button.setOnClickListener {
            startActivity(
                Intent(
                    this,
                    UdpTransportProbeActivity::class.java
                )
            )
        }
    }
}
"""
    rows = token_rows(
        fake,
        UI_TOKENS,
    )

    assert rows[
        "Button("
    ][
        "count"
    ] == 1

    assert (
        "UdpTransportProbeActivity"
        in activity_names(
            fake
        )
    )

    fake_family = [
        {
            "name": "x",
            "path": "logs/x",
            "file_count": 5,
            "total_bytes": (
                150
                * 1024
                * 1024
            ),
        }
    ]

    assert retention_candidates(
        fake_family
    )[0][
        "pressure"
    ] == "high"

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=".",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    root = Path(
        args.root
    ).resolve()

    if not (
        root
        / ".git"
    ).exists():
        raise SystemExit(
            "PrivyHub repository root not found"
        )

    report = build_report(
        root
    )

    out_dir = (
        root
        / "logs"
        / "diagnostics"
    )
    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        out_dir
        / "b1_gui_retention_context.json"
    )
    text_path = (
        out_dir
        / "b1_gui_retention_context.txt"
    )

    json_path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    text_path.write_text(
        format_text(
            report
        ),
        encoding="utf-8",
        newline="\n",
    )

    print(
        CLASSIFICATION
    )
    print(
        "Text:",
        text_path,
    )
    print(
        "JSON:",
        json_path,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
