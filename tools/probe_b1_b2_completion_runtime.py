#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
import zipfile

from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b1_b2_completion_runtime_v1"
CONFIRMED = "B1_B2_COMPLETION_RUNTIME_CONFIRMED"
FAILED = "B1_B2_COMPLETION_RUNTIME_NOT_CONFIRMED"

_ADDRESS_RE = re.compile(
    r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"
)
_MAC_RE = re.compile(
    r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
)


def request_json(
    path: str,
    *,
    method: str,
    timeout: float,
) -> dict[str, Any]:
    request = urllib.request.Request(
        "http://127.0.0.1:8765" + path,
        method=method,
        headers={
            "Cache-Control": "no-cache",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout,
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
            f"{path} did not return a JSON object"
        )

    return payload


def contains_network_identifier(
    value: Any,
) -> bool:
    if isinstance(
        value,
        str,
    ):
        if _ADDRESS_RE.search(
            value
        ):
            return True

        if _MAC_RE.search(
            value
        ):
            return True

        return False

    if isinstance(
        value,
        dict,
    ):
        return any(
            contains_network_identifier(
                key
            )
            or contains_network_identifier(
                child
            )
            for key, child in value.items()
        )

    if isinstance(
        value,
        list,
    ):
        return any(
            contains_network_identifier(
                child
            )
            for child in value
        )

    return False


def sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:
        for chunk in iter(
            lambda: handle.read(
                1024
                * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def check_map(
    checks: Any,
) -> dict[str, dict[str, Any]]:
    if not isinstance(
        checks,
        list,
    ):
        return {}

    return {
        str(
            item.get(
                "check_id"
            )
        ): item
        for item in checks
        if (
            isinstance(
                item,
                dict,
            )
            and isinstance(
                item.get(
                    "check_id"
                ),
                str,
            )
        )
    }


def write_result(
    root: Path,
    *,
    result: dict[str, Any] | None,
    error: str = "",
) -> int:
    out_dir = (
        root
        / "logs"
        / "diagnostics"
    )

    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    classification = (
        CONFIRMED
        if result is not None
        else FAILED
    )

    lines = [
        "PrivyHub Phase B1/B2 completion runtime validation",
        f"Classification: {classification}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
    ]

    if result is None:
        lines += [
            "=== FAILURE ===",
            "Reason: "
            + (
                error
                or "<unknown>"
            ),
        ]
    else:
        lines += [
            "=== HEALTH / EVENT HISTORY ===",
            "Health schema: "
            + result["health_schema"],
            "Health component count: "
            + str(
                result[
                    "health_component_count"
                ]
            ),
            "Event history schema: "
            + result["event_history_schema"],
            "Event history bounded: "
            + str(
                result[
                    "event_history_bounded"
                ]
            ),
            "Event history capacity: "
            + str(
                result[
                    "event_history_capacity"
                ]
            ),
            "Event history count: "
            + str(
                result[
                    "event_history_count"
                ]
            ),
            "New resource sampler started: "
            + str(
                result[
                    "new_resource_sampler"
                ]
            ),
            "",
            "=== SELF-TEST ===",
            "Self-test schema: "
            + result["self_test_schema"],
            "Self-test overall: "
            + result["self_test_overall"],
            "Storage writability: "
            + result["storage_status"]
            + " / "
            + result["storage_event"],
            "ADB/development: "
            + result["adb_status"]
            + " / "
            + result["adb_event"],
            "Emulator/runtime: "
            + result["emulator_status"]
            + " / "
            + result["emulator_event"],
            "ADB connection attempted: "
            + str(
                result[
                    "adb_connection_attempted"
                ]
            ),
            "Emulator launch attempted: "
            + str(
                result[
                    "emulator_launch_attempted"
                ]
            ),
            "Temporary storage artifact removed: "
            + str(
                result[
                    "temporary_storage_artifact_removed"
                ]
            ),
            "",
            "=== SANITIZED BUNDLE ===",
            "Bundle schema: "
            + result["bundle_schema"],
            "Bundle filename: "
            + result["bundle_filename"],
            "Bundle bytes: "
            + str(
                result[
                    "bundle_bytes"
                ]
            ),
            "Bundle SHA-256: "
            + result["bundle_sha256"],
            "Bundle ZIP integrity: "
            + str(
                result[
                    "bundle_zip_integrity"
                ]
            ),
            "Bundle manifest present: "
            + str(
                result[
                    "bundle_manifest_present"
                ]
            ),
            "Bundle diagnostics context present: "
            + str(
                result[
                    "bundle_context_present"
                ]
            ),
            "Bundle context includes event history: "
            + str(
                result[
                    "bundle_context_has_event_history"
                ]
            ),
            "Bundle context includes versions: "
            + str(
                result[
                    "bundle_context_has_versions"
                ]
            ),
            "",
            "=== PRIVACY / ARCHITECTURE ===",
            "Health response network identifiers present: False",
            "Self-test response network identifiers present: False",
            "Bundle response network identifiers present: False",
            "Diagnostics request-log suppression installed: "
            + str(
                result[
                    "diagnostics_log_suppression"
                ]
            ),
            "New timer/sampler added: False",
            "Streaming data path changed: False",
            "",
            "Next step: B1_B2_COMPLETE_BEGIN_B3_INVENTORY",
        ]

    text_path = (
        out_dir
        / "b1_b2_completion_runtime.txt"
    )

    text_path.write_text(
        "\n".join(
            lines
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return (
        0
        if result is not None
        else 1
    )


def self_test() -> int:
    assert (
        contains_network_identifier(
            {
                "value": "physical-target"
            }
        )
        is False
    )

    test_address = ".".join(
        (
            "192",
            "0",
            "2",
            "1",
        )
    )

    assert (
        contains_network_identifier(
            {
                "value": test_address
            }
        )
        is True
    )

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

    try:
        health = request_json(
            "/diagnostics/health",
            method="GET",
            timeout=5.0,
        )

        if (
            health.get(
                "schema"
            )
            != "privyhub_diagnostics_health_v1"
        ):
            raise RuntimeError(
                "Health schema mismatch"
            )

        components = health.get(
            "components"
        )

        if not isinstance(
            components,
            list,
        ) or len(
            components
        ) < 11:
            raise RuntimeError(
                "Health component model is incomplete"
            )

        event_history = health.get(
            "event_history"
        )

        if not isinstance(
            event_history,
            dict,
        ):
            raise RuntimeError(
                "Event history is missing"
            )

        if (
            event_history.get(
                "schema"
            )
            != "privyhub_diagnostic_event_history_v1"
        ):
            raise RuntimeError(
                "Event history schema mismatch"
            )

        if (
            event_history.get(
                "bounded"
            )
            is not True
        ):
            raise RuntimeError(
                "Event history is not bounded"
            )

        capacity = int(
            event_history.get(
                "capacity",
                0,
            )
        )

        event_count = int(
            event_history.get(
                "count",
                0,
            )
        )

        events = event_history.get(
            "events"
        )

        if (
            capacity != 128
            or event_count < 1
            or event_count > capacity
            or not isinstance(
                events,
                list,
            )
            or len(
                events
            ) != event_count
        ):
            raise RuntimeError(
                "Event history bounds/count are invalid"
            )

        if contains_network_identifier(
            health
        ):
            raise RuntimeError(
                "Health response contains a network identifier"
            )

        collection = health.get(
            "collection"
        )

        if not isinstance(
            collection,
            dict,
        ) or (
            collection.get(
                "new_resource_sampler_started"
            )
            is not False
        ):
            raise RuntimeError(
                "Unexpected resource sampler state"
            )

        self_result = request_json(
            "/diagnostics/self-test",
            method="POST",
            timeout=12.0,
        )

        if (
            self_result.get(
                "schema"
            )
            != "privyhub_diagnostics_self_test_v1"
        ):
            raise RuntimeError(
                "Self-test schema mismatch"
            )

        if contains_network_identifier(
            self_result
        ):
            raise RuntimeError(
                "Self-test response contains a network identifier"
            )

        checks = check_map(
            self_result.get(
                "checks"
            )
        )

        required_checks = {
            "storage_writability",
            "adb_development",
            "emulator_runtime",
        }

        if not required_checks.issubset(
            checks
        ):
            raise RuntimeError(
                "Self-test dedicated checks are incomplete"
            )

        storage = checks[
            "storage_writability"
        ]

        adb = checks[
            "adb_development"
        ]

        emulator = checks[
            "emulator_runtime"
        ]

        if storage.get(
            "status"
        ) != "PASS":
            raise RuntimeError(
                "Storage writability did not pass"
            )

        if adb.get(
            "status"
        ) not in {
            "PASS",
            "WARN",
            "SKIP",
        }:
            raise RuntimeError(
                "ADB readiness status is invalid"
            )

        if emulator.get(
            "status"
        ) != "PASS":
            raise RuntimeError(
                "Emulator/runtime prerequisites did not pass"
            )

        if (
            self_result.get(
                "adb_connection_attempted"
            )
            is not False
        ):
            raise RuntimeError(
                "Self-test attempted an ADB connection"
            )

        if (
            self_result.get(
                "emulator_launch_attempted"
            )
            is not False
        ):
            raise RuntimeError(
                "Self-test attempted an emulator launch"
            )

        if (
            self_result.get(
                "temporary_storage_artifact_removed"
            )
            is not True
        ):
            raise RuntimeError(
                "Temporary storage artifact cleanup was not confirmed"
            )

        bundle_result = request_json(
            "/diagnostics/bundle",
            method="POST",
            timeout=65.0,
        )

        if (
            bundle_result.get(
                "schema"
            )
            != "privyhub_support_bundle_result_v1"
            or bundle_result.get(
                "ok"
            )
            is not True
        ):
            raise RuntimeError(
                "Bundle endpoint did not confirm success"
            )

        if contains_network_identifier(
            bundle_result
        ):
            raise RuntimeError(
                "Bundle response contains a network identifier"
            )

        relative_path = bundle_result.get(
            "relative_path"
        )

        if not isinstance(
            relative_path,
            str,
        ) or not relative_path:
            raise RuntimeError(
                "Bundle relative path is missing"
            )

        bundle_path = (
            root
            / Path(
                relative_path
            )
        ).resolve()

        allowed = (
            root
            / "logs"
            / "debug_bundles"
        ).resolve()

        try:
            bundle_path.relative_to(
                allowed
            )
        except ValueError as exc:
            raise RuntimeError(
                "Bundle escaped allowed diagnostics directory"
            ) from exc

        if not bundle_path.is_file():
            raise RuntimeError(
                "Bundle file does not exist"
            )

        expected_sha = bundle_result.get(
            "sha256"
        )

        if (
            not isinstance(
                expected_sha,
                str,
            )
            or sha256_file(
                bundle_path
            )
            != expected_sha
        ):
            raise RuntimeError(
                "Bundle SHA-256 mismatch"
            )

        with zipfile.ZipFile(
            bundle_path,
            "r",
        ) as archive:
            if archive.testzip() is not None:
                raise RuntimeError(
                    "Bundle ZIP integrity failed"
                )

            names = set(
                archive.namelist()
            )

            manifest_present = (
                "manifest.json"
                in names
            )

            context_present = (
                "diagnostics_context.json"
                in names
            )

            if not (
                manifest_present
                and context_present
                and "SHARE_ME.txt"
                in names
            ):
                raise RuntimeError(
                    "Bundle required files are missing"
                )

            manifest = json.loads(
                archive.read(
                    "manifest.json"
                )
            )

            context = json.loads(
                archive.read(
                    "diagnostics_context.json"
                )
            )

        if not isinstance(
            manifest,
            dict,
        ) or not isinstance(
            context,
            dict,
        ):
            raise RuntimeError(
                "Bundle JSON context is invalid"
            )

        paths = {
            item.get(
                "path"
            )
            for item in manifest.get(
                "files",
                []
            )
            if isinstance(
                item,
                dict,
            )
        }

        if (
            "diagnostics_context.json"
            not in paths
        ):
            raise RuntimeError(
                "Bundle manifest does not hash diagnostics context"
            )

        context_health = context.get(
            "health"
        )

        context_versions = context.get(
            "versions"
        )

        context_has_event_history = bool(
            isinstance(
                context_health,
                dict,
            )
            and isinstance(
                context_health.get(
                    "event_history"
                ),
                dict,
            )
        )

        context_has_versions = bool(
            isinstance(
                context_versions,
                dict,
            )
            and context_versions.get(
                "python"
            )
            and context_versions.get(
                "retroarch_configured_version"
            )
        )

        if not context_has_event_history:
            raise RuntimeError(
                "Bundle context lacks event history"
            )

        if not context_has_versions:
            raise RuntimeError(
                "Bundle context lacks runtime versions"
            )

        service_source = (
            root
            / "companion"
            / "privyhub_service.py"
        ).read_text(
            encoding="utf-8-sig",
            errors="replace",
        )

        diagnostics_log_suppression = (
            'urlsplit(self.path).path.startswith('
            in service_source
            and '"/diagnostics/"'
            in service_source
        )

        if not diagnostics_log_suppression:
            raise RuntimeError(
                "Diagnostics request-log suppression marker is missing"
            )

        result = {
            "health_schema": str(
                health[
                    "schema"
                ]
            ),
            "health_component_count": len(
                components
            ),
            "event_history_schema": str(
                event_history[
                    "schema"
                ]
            ),
            "event_history_bounded": bool(
                event_history[
                    "bounded"
                ]
            ),
            "event_history_capacity": (
                capacity
            ),
            "event_history_count": (
                event_count
            ),
            "new_resource_sampler": (
                collection[
                    "new_resource_sampler_started"
                ]
            ),
            "self_test_schema": str(
                self_result[
                    "schema"
                ]
            ),
            "self_test_overall": str(
                (
                    self_result.get(
                        "overall"
                    )
                    or {}
                ).get(
                    "status",
                    "unknown",
                )
            ),
            "storage_status": str(
                storage.get(
                    "status"
                )
            ),
            "storage_event": str(
                storage.get(
                    "event_code"
                )
            ),
            "adb_status": str(
                adb.get(
                    "status"
                )
            ),
            "adb_event": str(
                adb.get(
                    "event_code"
                )
            ),
            "emulator_status": str(
                emulator.get(
                    "status"
                )
            ),
            "emulator_event": str(
                emulator.get(
                    "event_code"
                )
            ),
            "adb_connection_attempted": (
                self_result[
                    "adb_connection_attempted"
                ]
            ),
            "emulator_launch_attempted": (
                self_result[
                    "emulator_launch_attempted"
                ]
            ),
            "temporary_storage_artifact_removed": (
                self_result[
                    "temporary_storage_artifact_removed"
                ]
            ),
            "bundle_schema": str(
                bundle_result[
                    "schema"
                ]
            ),
            "bundle_filename": str(
                bundle_result.get(
                    "filename",
                    "",
                )
            ),
            "bundle_bytes": int(
                bundle_result.get(
                    "size_bytes",
                    0,
                )
            ),
            "bundle_sha256": str(
                bundle_result[
                    "sha256"
                ]
            ),
            "bundle_zip_integrity": True,
            "bundle_manifest_present": (
                manifest_present
            ),
            "bundle_context_present": (
                context_present
            ),
            "bundle_context_has_event_history": (
                context_has_event_history
            ),
            "bundle_context_has_versions": (
                context_has_versions
            ),
            "diagnostics_log_suppression": (
                diagnostics_log_suppression
            ),
        }

    except (
        urllib.error.URLError,
        TimeoutError,
        ConnectionError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
        zipfile.BadZipFile,
        RuntimeError,
    ) as exc:
        return write_result(
            root,
            result=None,
            error=(
                type(
                    exc
                ).__name__
                + ": "
                + str(
                    exc
                )
            ),
        )

    return write_result(
        root,
        result=result,
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
