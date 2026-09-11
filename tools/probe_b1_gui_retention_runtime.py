#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b1_gui_retention_foundation_runtime_v1"
CONFIRMED = "B1_GUI_RETENTION_FOUNDATION_CONFIRMED"
FAILED = "B1_GUI_RETENTION_FOUNDATION_NOT_CONFIRMED"
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

ROOT_FROM_SCRIPT = Path(__file__).resolve().parents[1]
COMPANION_DIR = ROOT_FROM_SCRIPT / "companion"

if str(COMPANION_DIR) not in sys.path:
    sys.path.insert(0, str(COMPANION_DIR))

from diagnostics.retention import (  # noqa: E402
    build_retention_plan,
    policy_sha256,
    public_plan,
)


def request_health() -> dict[str, Any]:
    request = urllib.request.Request(
        "http://127.0.0.1:8765/diagnostics/health",
        headers={"Cache-Control": "no-cache"},
        method="GET",
    )

    with urllib.request.urlopen(
        request,
        timeout=3.0,
    ) as response:
        payload = json.loads(
            response.read().decode("utf-8")
        )

    if not isinstance(payload, dict):
        raise RuntimeError(
            "Health endpoint did not return an object"
        )

    return payload


def android_activity_registered(root: Path) -> bool:
    path = root / "PrivyHub/app/src/main/AndroidManifest.xml"
    tree = ET.parse(path)
    expected = ".diagnostics.DiagnosticsActivity"

    for node in tree.findall(".//activity"):
        name = node.attrib.get(ANDROID_NS + "name")
        if name == expected:
            exported = node.attrib.get(ANDROID_NS + "exported")
            return exported == "false"

    return False


def source_marker(path: Path, marker: str) -> bool:
    if not path.is_file():
        return False

    return marker in path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )


def write_result(
    root: Path,
    *,
    result: dict[str, Any] | None,
    error: str = "",
) -> int:
    out_dir = root / "logs" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)

    confirmed = result is not None
    classification = CONFIRMED if confirmed else FAILED

    lines = [
        "PrivyHub Phase B1.9 Diagnostics GUI + retention foundation runtime probe",
        f"Classification: {classification}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "Retention files deleted by probe: 0",
        "",
    ]

    if result is None:
        lines += [
            "=== FAILURE ===",
            "Reason: " + (error or "<unknown>"),
        ]
    else:
        lines += [
            "=== GUI FOUNDATION ===",
            "Diagnostics activity source installed: "
            + str(result["activity_source"]),
            "Diagnostics activity registered exported=false: "
            + str(result["activity_registered"]),
            "Main Settings Diagnostics navigation installed: "
            + str(result["main_navigation"]),
            "Health endpoint available: True",
            "Health schema: " + str(result["health_schema"]),
            "Health component count: " + str(result["component_count"]),
            "New resource sampler started: "
            + str(result["new_resource_sampler"]),
            "",
            "=== RETENTION FOUNDATION ===",
            "Mode: DRY_RUN",
            "Policy SHA-256: " + str(result["policy_sha256"]),
            "Automatic retention enabled: False",
            "Durable memory in scope: False",
            "Patch backups in scope: False",
            "Files deleted: 0",
        ]

        for item in result["families"]:
            lines.append(
                f"{item['family']}: "
                f"files={item['file_count']} "
                f"bytes={item['total_bytes']} "
                f"limit_bytes={item['max_bytes']} "
                f"protected={item['protected_count']} "
                f"would_delete={item['candidate_count']} "
                f"would_free_bytes={item['candidate_bytes']} "
                f"projected_bytes={item['projected_bytes']} "
                f"blocked={item['blocked_by_protected_evidence']}"
            )

        lines += [
            "",
            "Total would delete: "
            + str(result["total_candidate_count"]),
            "Total would free bytes: "
            + str(result["total_candidate_bytes"]),
            "",
            "Next step: MANUAL_GUI_CHECK_AND_REVIEW_RETENTION_DRY_RUN",
        ]

    (out_dir / "b1_gui_retention_runtime.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return 0 if confirmed else 1


def self_test() -> int:
    assert len(policy_sha256()) == 64
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()

    try:
        activity_source = source_marker(
            root
            / (
                "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
                "diagnostics/DiagnosticsActivity.kt"
            ),
            "PRIVYHUB_B1_DIAGNOSTICS_ACTIVITY_V1",
        )
        main_navigation = source_marker(
            root
            / (
                "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
                "MainActivity.kt"
            ),
            "PRIVYHUB_B1_DIAGNOSTICS_NAV_V1",
        )
        registered = android_activity_registered(root)

        if not (
            activity_source
            and main_navigation
            and registered
        ):
            raise RuntimeError(
                "Android diagnostics activity/navigation installation is incomplete"
            )

        health = request_health()

        if health.get("schema") != "privyhub_diagnostics_health_v1":
            raise RuntimeError("Health schema mismatch")

        components = (
            health.get("components")
            if isinstance(health.get("components"), list)
            else []
        )

        if len(components) < 11:
            raise RuntimeError(
                "Health component model is incomplete"
            )

        collection = (
            health.get("collection")
            if isinstance(health.get("collection"), dict)
            else {}
        )

        if collection.get("new_resource_sampler_started") is not False:
            raise RuntimeError(
                "Unexpected resource sampler state"
            )

        plan = public_plan(
            build_retention_plan(root)
        )

        if plan.get("automatic") is not False:
            raise RuntimeError(
                "Retention unexpectedly automatic"
            )

        if plan.get("durable_memory_in_scope") is not False:
            raise RuntimeError(
                "Durable memory entered retention scope"
            )

        result = {
            "activity_source": activity_source,
            "activity_registered": registered,
            "main_navigation": main_navigation,
            "health_schema": health.get("schema"),
            "component_count": len(components),
            "new_resource_sampler": collection.get(
                "new_resource_sampler_started"
            ),
            "policy_sha256": plan["policy_sha256"],
            "families": plan["families"],
            "total_candidate_count": plan["total_candidate_count"],
            "total_candidate_bytes": plan["total_candidate_bytes"],
        }

    except (
        urllib.error.URLError,
        TimeoutError,
        ConnectionError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        RuntimeError,
        ET.ParseError,
    ) as exc:
        return write_result(
            root,
            result=None,
            error=type(exc).__name__ + ": " + str(exc),
        )

    return write_result(root, result=result)


if __name__ == "__main__":
    raise SystemExit(main())
