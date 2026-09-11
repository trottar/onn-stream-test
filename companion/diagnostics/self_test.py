from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time

from pathlib import Path
from typing import Any

SELF_TEST_SCHEMA = "privyhub_diagnostics_self_test_v1"


def _check(
    *,
    check_id: str,
    status: str,
    event_code: str,
    summary: str,
    measurements: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": status,
        "event_code": event_code,
        "summary": summary,
        "measurements": dict(
            measurements or {}
        ),
    }


def _storage_writability(
    project_root: Path,
) -> dict[str, Any]:
    directory = (
        project_root
        / "logs"
        / "diagnostics"
    )

    try:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        fd, raw_path = tempfile.mkstemp(
            prefix=".privyhub_self_test_",
            suffix=".tmp",
            dir=directory,
        )

        path = Path(raw_path)

        try:
            with os.fdopen(
                fd,
                "wb",
            ) as handle:
                handle.write(
                    b"privyhub-self-test"
                )
                handle.flush()
                os.fsync(
                    handle.fileno()
                )

            if path.stat().st_size <= 0:
                raise OSError(
                    "Self-test write produced an empty file"
                )

        finally:
            path.unlink(
                missing_ok=True
            )

        return _check(
            check_id="storage_writability",
            status="PASS",
            event_code="STORAGE-WRITE-READY",
            summary=(
                "Diagnostics storage accepted a temporary write and cleanup."
            ),
            measurements={
                "temporary_bytes": len(
                    b"privyhub-self-test"
                ),
                "cleanup_confirmed": (
                    not path.exists()
                ),
            },
        )

    except Exception as exc:
        return _check(
            check_id="storage_writability",
            status="FAIL",
            event_code="STORAGE-WRITE-FAILED",
            summary=(
                "Diagnostics storage writability check failed."
            ),
            measurements={
                "error_class": type(
                    exc
                ).__name__,
            },
        )


def _local_properties_sdk(
    project_root: Path,
) -> Path | None:
    path = (
        project_root
        / "PrivyHub"
        / "local.properties"
    )

    if not path.is_file():
        return None

    try:
        lines = path.read_text(
            encoding="utf-8-sig",
            errors="replace",
        ).splitlines()
    except OSError:
        return None

    for line in lines:
        stripped = line.strip()

        if not stripped.startswith(
            "sdk.dir="
        ):
            continue

        raw = stripped.split(
            "=",
            1,
        )[1].strip()

        raw = raw.replace(
            "\\:",
            ":",
        ).replace(
            "\\\\",
            "\\",
        )

        if raw:
            return Path(raw)

    return None


def _resolve_adb(
    project_root: Path,
) -> Path | None:
    for name in (
        "adb.exe",
        "adb",
    ):
        found = shutil.which(
            name
        )

        if found:
            return Path(
                found
            )

    roots: list[Path] = []

    for key in (
        "ANDROID_SDK_ROOT",
        "ANDROID_HOME",
    ):
        value = os.environ.get(
            key
        )

        if value:
            roots.append(
                Path(
                    value
                )
            )

    local_sdk = _local_properties_sdk(
        project_root
    )

    if local_sdk is not None:
        roots.append(
            local_sdk
        )

    for root in roots:
        for name in (
            "adb.exe",
            "adb",
        ):
            candidate = (
                root
                / "platform-tools"
                / name
            )

            if candidate.is_file():
                return candidate

    return None


def _adb_development(
    project_root: Path,
) -> dict[str, Any]:
    applicable = (
        (
            project_root
            / "PrivyHub"
        ).is_dir()
        and (
            project_root
            / "tools"
            / "build_install_onn.ps1"
        ).is_file()
    )

    if not applicable:
        return _check(
            check_id="adb_development",
            status="SKIP",
            event_code="ADB-DEV-NOT-APPLICABLE",
            summary=(
                "Android development tooling is not part of this installation."
            ),
            measurements={
                "applicable": False,
            },
        )

    adb = _resolve_adb(
        project_root
    )

    if adb is None:
        return _check(
            check_id="adb_development",
            status="WARN",
            event_code="ADB-DEV-TOOL-MISSING",
            summary=(
                "ADB development tooling is applicable but adb was not found."
            ),
            measurements={
                "applicable": True,
                "tool_available": False,
                "authorized_physical_targets": 0,
            },
        )

    creationflags = 0

    if (
        os.name == "nt"
        and hasattr(
            subprocess,
            "CREATE_NO_WINDOW",
        )
    ):
        creationflags = int(
            subprocess.CREATE_NO_WINDOW
        )

    try:
        completed = subprocess.run(
            [
                str(
                    adb
                ),
                "devices",
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=4.0,
            creationflags=creationflags,
            check=False,
        )
    except Exception as exc:
        return _check(
            check_id="adb_development",
            status="WARN",
            event_code="ADB-DEV-CHECK-FAILED",
            summary=(
                "ADB was found, but the bounded readiness check did not complete."
            ),
            measurements={
                "applicable": True,
                "tool_available": True,
                "authorized_physical_targets": 0,
                "error_class": type(
                    exc
                ).__name__,
            },
        )

    authorized = 0
    nonready = 0

    for raw_line in completed.stdout.splitlines()[
        1:
    ]:
        line = raw_line.strip()

        if not line:
            continue

        parts = line.split()

        if len(parts) < 2:
            continue

        serial = parts[0]
        state = parts[1].casefold()

        if serial.casefold().startswith(
            "emulator-"
        ):
            continue

        if state == "device":
            authorized += 1
        else:
            nonready += 1

    if (
        completed.returncode == 0
        and authorized > 0
    ):
        return _check(
            check_id="adb_development",
            status="PASS",
            event_code="ADB-DEV-READY",
            summary=(
                "ADB is available and at least one physical Android target is ready."
            ),
            measurements={
                "applicable": True,
                "tool_available": True,
                "authorized_physical_targets": authorized,
                "nonready_physical_targets": nonready,
                "command_returncode": (
                    completed.returncode
                ),
            },
        )

    return _check(
        check_id="adb_development",
        status="WARN",
        event_code=(
            "ADB-DEV-NO-TARGET"
            if completed.returncode == 0
            else "ADB-DEV-CHECK-FAILED"
        ),
        summary=(
            "ADB tooling is available but no ready physical Android target was observed."
        ),
        measurements={
            "applicable": True,
            "tool_available": True,
            "authorized_physical_targets": authorized,
            "nonready_physical_targets": nonready,
            "command_returncode": (
                completed.returncode
            ),
        },
    )


def _emulator_runtime(
    health_snapshot: dict[str, Any],
) -> dict[str, Any]:
    prerequisites = health_snapshot.get(
        "runtime_prerequisites"
    )

    if not isinstance(
        prerequisites,
        dict,
    ) or (
        prerequisites.get(
            "games_status_available"
        )
        is not True
    ):
        return _check(
            check_id="emulator_runtime",
            status="WARN",
            event_code="EMULATOR-STATUS-UNAVAILABLE",
            summary=(
                "Emulator runtime readiness could not be read from the Games status path."
            ),
            measurements={
                "games_status_available": False,
            },
        )

    ready = (
        prerequisites.get(
            "ready"
        )
        is True
    )

    return _check(
        check_id="emulator_runtime",
        status=(
            "PASS"
            if ready
            else "FAIL"
        ),
        event_code=(
            "EMULATOR-RUNTIME-READY"
            if ready
            else "EMULATOR-RUNTIME-INCOMPLETE"
        ),
        summary=(
            "Games status reports the configured RetroArch runtime and cores ready."
            if ready
            else "Games status reports incomplete RetroArch runtime prerequisites."
        ),
        measurements={
            "games_status_available": True,
            "ready": ready,
            "retroarch_installed": bool(
                prerequisites.get(
                    "retroarch_installed",
                    False,
                )
            ),
            "retroarch_configured": bool(
                prerequisites.get(
                    "retroarch_configured",
                    False,
                )
            ),
            "missing_core_count": max(
                0,
                int(
                    prerequisites.get(
                        "missing_core_count",
                        0,
                    )
                ),
            ),
        },
    )


def run_diagnostics_self_test(
    *,
    project_root: Path,
    health_snapshot: dict[str, Any],
) -> dict[str, Any]:
    checks = [
        _storage_writability(
            project_root
        ),
        _adb_development(
            project_root
        ),
        _emulator_runtime(
            health_snapshot
        ),
    ]

    components = health_snapshot.get(
        "components"
    )

    if not isinstance(
        components,
        list,
    ):
        components = []

    health_failures = sum(
        1
        for item in components
        if (
            isinstance(
                item,
                dict,
            )
            and item.get(
                "severity"
            ) == "error"
        )
    )

    health_warnings = sum(
        1
        for item in components
        if (
            isinstance(
                item,
                dict,
            )
            and item.get(
                "severity"
            ) == "warning"
        )
    )

    fail_count = (
        health_failures
        + sum(
            1
            for item in checks
            if item.get(
                "status"
            ) == "FAIL"
        )
    )

    warning_count = (
        health_warnings
        + sum(
            1
            for item in checks
            if item.get(
                "status"
            ) == "WARN"
        )
    )

    overall = (
        "FAIL"
        if fail_count
        else (
            "WARN"
            if warning_count
            else "PASS"
        )
    )

    return {
        "schema": SELF_TEST_SCHEMA,
        "generated_unix_ms": int(
            time.time()
            * 1000.0
        ),
        "overall": {
            "status": overall,
            "failures": fail_count,
            "warnings": warning_count,
        },
        "health": health_snapshot,
        "checks": checks,
        "production_state_changed": False,
        "temporary_storage_artifact_removed": True,
        "adb_connection_attempted": False,
        "emulator_launch_attempted": False,
    }
