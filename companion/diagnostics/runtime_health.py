from __future__ import annotations

import json
import time

from pathlib import Path
from typing import Any

from diagnostics.health_model import (
    build_health_snapshot,
)

from diagnostics.event_history import (
    DiagnosticEventHistory,
)


DIAGNOSTIC_EVENT_HISTORY = DiagnosticEventHistory(
    capacity=128
)


MAX_HOST_TELEMETRY_BYTES = (
    8
    * 1024
    * 1024
)

HOST_TELEMETRY_SCHEMA = (
    "privyhub_native_host_telemetry_v1"
)


def _safe_host_telemetry_file(
    project_root: Path,
    candidate: Path,
) -> Path | None:
    allowed = (
        project_root
        / "logs"
        / "games"
        / "host_telemetry"
    ).resolve()

    try:
        resolved = (
            candidate.resolve()
        )
        resolved.relative_to(
            allowed
        )
    except (
        OSError,
        ValueError,
    ):
        return None

    try:
        if (
            not resolved.is_file()
            or resolved.stat().st_size
            > MAX_HOST_TELEMETRY_BYTES
        ):
            return None
    except OSError:
        return None

    return resolved


def _read_host_telemetry(
    path: Path,
) -> dict[str, Any] | None:
    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return None

    if not isinstance(
        payload,
        dict,
    ):
        return None

    if (
        payload.get(
            "schema"
        )
        != HOST_TELEMETRY_SCHEMA
    ):
        return None

    return payload


def load_host_telemetry_payload(
    *,
    project_root: Path,
    games_status: Any,
) -> tuple[
    dict[str, Any] | None,
    str,
]:
    root = (
        project_root.resolve()
    )
    games = (
        games_status
        if isinstance(
            games_status,
            dict,
        )
        else {}
    )
    native = (
        games.get(
            "native_stream"
        )
        if isinstance(
            games.get(
                "native_stream"
            ),
            dict,
        )
        else {}
    )
    telemetry = (
        native.get(
            "host_telemetry"
        )
        if isinstance(
            native.get(
                "host_telemetry"
            ),
            dict,
        )
        else {}
    )

    raw_path = (
        telemetry.get(
            "path"
        )
    )

    if (
        isinstance(
            raw_path,
            str,
        )
        and raw_path.strip()
    ):
        safe = (
            _safe_host_telemetry_file(
                root,
                Path(
                    raw_path
                ),
            )
        )

        if safe is not None:
            payload = (
                _read_host_telemetry(
                    safe
                )
            )

            if payload is not None:
                return (
                    payload,
                    "current_status_path",
                )

    history = (
        root
        / "logs"
        / "games"
        / "host_telemetry"
    )

    if not history.is_dir():
        return (
            None,
            "none",
        )

    try:
        candidates = sorted(
            (
                path
                for path
                in history.glob(
                    "*.json"
                )
                if path.is_file()
            ),
            key=lambda path: (
                path.stat().st_mtime_ns
            ),
            reverse=True,
        )
    except OSError:
        return (
            None,
            "none",
        )

    for candidate in candidates[
        :32
    ]:
        safe = (
            _safe_host_telemetry_file(
                root,
                candidate,
            )
        )
        if safe is None:
            continue

        payload = (
            _read_host_telemetry(
                safe
            )
        )

        if payload is not None:
            return (
                payload,
                "latest_history",
            )

    return (
        None,
        "none",
    )


def build_live_health_snapshot(
    *,
    project_root: Path,
    companion_status: Any,
    games_plugin: Any,
    client_health_feedback: Any = None,
) -> dict[str, Any]:
    games_status: dict[
        str,
        Any,
    ] = {}
    games_error_class = ""

    if games_plugin is None:
        games_error_class = (
            "GamesPluginUnavailable"
        )
    else:
        try:
            payload = (
                games_plugin.handle(
                    "status",
                    "",
                )
            )

            if isinstance(
                payload,
                dict,
            ):
                games_status = (
                    payload
                )
            else:
                games_error_class = (
                    "GamesStatusNotObject"
                )
        except Exception as exc:
            games_error_class = (
                type(
                    exc
                ).__name__
            )

    (
        host_payload,
        host_payload_source,
    ) = (
        load_host_telemetry_payload(
            project_root=(
                project_root
            ),
            games_status=(
                games_status
            ),
        )
    )

    snapshot = (
        build_health_snapshot(
            companion_status=(
                companion_status
            ),
            games_status=(
                games_status
            ),
            host_telemetry_payload=(
                host_payload
            ),
            client_feedback=(
                client_health_feedback
            ),
            generated_unix_ms=int(
                time.time()
                * 1000.0
            ),
        )
    )

    missing_cores = (
        games_status.get(
            "missing_cores"
        )
        if isinstance(
            games_status.get(
                "missing_cores"
            ),
            list,
        )
        else []
    )

    snapshot[
        "runtime_prerequisites"
    ] = {
        "games_status_available": bool(
            games_status
        ),
        "ready": bool(
            games_status.get(
                "ready",
                False,
            )
        ),
        "retroarch_installed": bool(
            games_status.get(
                "retroarch_installed",
                False,
            )
        ),
        "retroarch_configured": bool(
            games_status.get(
                "retroarch_configured",
                False,
            )
        ),
        "missing_core_count": len(
            missing_cores
        ),
    }

    snapshot[
        "collection"
    ] = {
        "games_status_available": bool(
            games_status
        ),
        "games_status_error_class": (
            games_error_class
        ),
        "host_telemetry_payload_available": (
            host_payload
            is not None
        ),
        "host_telemetry_payload_source": (
            host_payload_source
        ),
        "new_resource_sampler_started": (
            False
        ),
        "client_feedback_available": bool(
            isinstance(
                client_health_feedback,
                dict,
            )
            and client_health_feedback.get(
                "available",
                False,
            )
        ),
        "client_feedback_fresh": bool(
            isinstance(
                client_health_feedback,
                dict,
            )
            and client_health_feedback.get(
                "fresh",
                False,
            )
        ),
        "client_feedback_payload_bytes": (
            client_health_feedback.get(
                "payload_bytes",
                0,
            )
            if isinstance(
                client_health_feedback,
                dict,
            )
            else 0
        ),
    }

    # PRIVYHUB_B1_EVENT_HISTORY_V1
    DIAGNOSTIC_EVENT_HISTORY.observe_snapshot(
        snapshot,
        games_status=games_status,
    )

    snapshot[
        "event_history"
    ] = (
        DIAGNOSTIC_EVENT_HISTORY.snapshot()
    )

    return snapshot
