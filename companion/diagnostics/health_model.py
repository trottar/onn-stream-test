from __future__ import annotations

from typing import Any

HEALTH_SCHEMA = "privyhub_diagnostics_health_v1"
RESOURCE_SCHEMA = "privyhub_resource_snapshot_v1"
CLASSIFIER_ID = "privyhub_health_rules_v1"

HEALTH_VALUES = {
    "healthy",
    "degraded",
    "unavailable",
    "idle",
    "unknown",
}
SEVERITY_VALUES = {
    "info",
    "warning",
    "error",
}

_RESOURCE_UNAVAILABLE_METRICS = (
    "gpu_utilization_percent",
    "encoder_engine_utilization_percent",
    "host_total_memory_mib",
    "host_available_memory_mib",
    "host_storage_io_mib_s",
    "host_network_goodput_mbps",
)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _number(
    value: Any,
) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return None


def _nonnegative_int(
    value: Any,
) -> int:
    number = _number(value)
    if number is None:
        return 0
    try:
        return max(0, int(number))
    except (TypeError, ValueError, OverflowError):
        return 0


def _clean_text(
    value: Any,
) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _component(
    *,
    subsystem: str,
    component: str,
    health: str,
    severity: str,
    event_code: str,
    summary: str,
    measurements: dict[str, Any] | None = None,
    basis: list[str] | None = None,
) -> dict[str, Any]:
    if health not in HEALTH_VALUES:
        raise ValueError(
            f"Unsupported health value: {health}"
        )
    if severity not in SEVERITY_VALUES:
        raise ValueError(
            f"Unsupported severity value: {severity}"
        )

    return {
        "subsystem": subsystem,
        "component": component,
        "health": health,
        "severity": severity,
        "event_code": event_code,
        "summary": summary,
        "measurements": dict(
            measurements or {}
        ),
        "classification": {
            "classifier": CLASSIFIER_ID,
            "basis": list(
                basis or []
            ),
        },
    }


def _process_aggregate(
    value: Any,
) -> dict[str, Any]:
    process = _dict(value)
    result: dict[str, Any] = {}

    for key in (
        "cpu_one_core_percent",
        "cpu_total_host_percent",
        "working_set_mib",
        "private_mib",
    ):
        stats = _dict(
            process.get(key)
        )
        avg = _number(
            stats.get("avg")
        )
        maximum = _number(
            stats.get("max")
        )

        if avg is None and maximum is None:
            continue

        result[key] = {
            "avg": avg,
            "max": maximum,
        }

    return result


def _latest_process_sample(
    sample: Any,
) -> dict[str, Any]:
    source = _dict(sample)
    result: dict[str, Any] = {}

    for key in (
        "cpu_one_core_percent",
        "cpu_total_host_percent",
        "working_set_mib",
        "private_mib",
        "peak_working_set_mib",
    ):
        value = _number(
            source.get(key)
        )
        if value is not None:
            result[key] = value

    return result


def _safe_wgc(
    value: Any,
) -> dict[str, Any]:
    source = _dict(value)
    result: dict[str, Any] = {}

    for key in (
        "callbacks",
        "emitted_frames",
        "duplicated_emits",
        "overwritten_frames",
        "size_mismatch_frames",
        "normalized_size_frames",
        "normalization_failures",
        "copy_time_avg_ms",
        "copy_time_max_ms",
        "write_time_avg_ms",
        "write_time_max_ms",
        "frame_bytes",
        "raw_bytes_emitted",
    ):
        number = _number(
            source.get(key)
        )
        if number is not None:
            result[key] = number

    return result


def build_resource_snapshot(
    native_stream: Any,
    host_telemetry_payload: Any = None,
) -> dict[str, Any]:
    native = _dict(
        native_stream
    )
    telemetry_status = _dict(
        native.get("host_telemetry")
    )
    payload = _dict(
        host_telemetry_payload
    )

    stream_active = bool(
        native.get("active", False)
    )
    telemetry_active = bool(
        telemetry_status.get(
            "active",
            False,
        )
    )
    status_error = _clean_text(
        telemetry_status.get("error")
    )
    payload_error = _clean_text(
        payload.get("error")
    )

    samples = (
        payload.get("samples")
        if isinstance(
            payload.get("samples"),
            list,
        )
        else []
    )
    latest = (
        _dict(samples[-1])
        if samples
        else {}
    )

    process_aggregates = _dict(
        payload.get("processes")
    )
    capture_aggregate = (
        _process_aggregate(
            process_aggregates.get(
                "capture"
            )
        )
    )
    encoder_aggregate = (
        _process_aggregate(
            process_aggregates.get(
                "ffmpeg"
            )
        )
    )

    capture_latest = (
        _latest_process_sample(
            latest.get(
                "capture_process"
            )
        )
    )
    encoder_latest = (
        _latest_process_sample(
            latest.get(
                "ffmpeg_process"
            )
        )
    )

    latest_wgc = _safe_wgc(
        payload.get("latest_wgc")
    )
    if not latest_wgc:
        latest_wgc = _safe_wgc(
            latest.get("wgc")
        )

    logical_cpu_count = _nonnegative_int(
        payload.get(
            "logical_cpu_count",
            0,
        )
    )

    status_samples = _nonnegative_int(
        telemetry_status.get(
            "samples",
            0,
        )
    )
    payload_samples = _nonnegative_int(
        payload.get(
            "sample_count",
            len(samples),
        )
    )
    sample_count = max(
        status_samples,
        payload_samples,
        len(samples),
    )

    interval = _number(
        telemetry_status.get(
            "sample_interval_seconds"
        )
    )
    if interval is None:
        interval = _number(
            payload.get(
                "sample_interval_seconds"
            )
        )

    payload_available = bool(
        capture_aggregate
        or encoder_aggregate
        or capture_latest
        or encoder_latest
        or latest_wgc
        or sample_count > 0
    )

    if status_error or payload_error:
        availability = "degraded"
    elif payload_available:
        availability = "available"
    elif telemetry_active:
        availability = "warming_up"
    elif stream_active:
        availability = "unknown"
    else:
        availability = "idle"

    return {
        "schema": RESOURCE_SCHEMA,
        "availability": availability,
        "measurement_scope": (
            "current_session"
            if telemetry_active
            else (
                "last_session"
                if payload_available
                else "none"
            )
        ),
        "source": (
            "existing_native_host_telemetry"
        ),
        "sampling": {
            "active": telemetry_active,
            "sample_interval_seconds": (
                interval
            ),
            "sample_count": sample_count,
        },
        "logical_cpu_count": (
            logical_cpu_count
            if logical_cpu_count > 0
            else None
        ),
        "processes": {
            "capture": {
                "aggregate": (
                    capture_aggregate
                ),
                "latest": (
                    capture_latest
                ),
            },
            "encoder": {
                "aggregate": (
                    encoder_aggregate
                ),
                "latest": (
                    encoder_latest
                ),
            },
        },
        "capture_pipeline": (
            latest_wgc
        ),
        "telemetry_error_present": bool(
            status_error
            or payload_error
        ),
        "unavailable_metrics": list(
            _RESOURCE_UNAVAILABLE_METRICS
        ),
        "optimization": {
            "capacity_classification": (
                "unclassified"
            ),
            "stream_profile_fit": (
                "unclassified"
            ),
            "benchmark_thresholds_applied": (
                False
            ),
            "threshold_source": (
                "phase_e_benchmark_pending"
            ),
        },
    }


def _component_companion(
    status: dict[str, Any],
) -> dict[str, Any]:
    service = _clean_text(
        status.get("service")
    )

    if service.casefold() == "privyhub":
        return _component(
            subsystem="system",
            component="companion",
            health="healthy",
            severity="info",
            event_code="SYSTEM-COMPANION-READY",
            summary=(
                "PrivyHub companion API responded."
            ),
            measurements={
                "api_version": (
                    status.get(
                        "api_version"
                    )
                ),
            },
            basis=[
                "companion_status.service",
            ],
        )

    return _component(
        subsystem="system",
        component="companion",
        health="unknown",
        severity="warning",
        event_code="SYSTEM-COMPANION-UNKNOWN",
        summary=(
            "Companion status was present but "
            "could not be positively identified."
        ),
        basis=[
            "companion_status.service",
        ],
    )


def _component_media_server(
    status: dict[str, Any],
) -> dict[str, Any]:
    server = _dict(
        status.get("server")
    )
    running = bool(
        server.get(
            "running",
            False,
        )
    )

    if running:
        return _component(
            subsystem="media",
            component="media_server",
            health="healthy",
            severity="info",
            event_code="MEDIA-SERVER-RUNNING",
            summary=(
                "PrivyHub media server is running."
            ),
            measurements={
                "running": True,
            },
            basis=[
                "companion_status.server.running",
            ],
        )

    return _component(
        subsystem="media",
        component="media_server",
        health="degraded",
        severity="warning",
        event_code="MEDIA-SERVER-STOPPED",
        summary=(
            "Companion is reachable but the media "
            "server is not running."
        ),
        measurements={
            "running": False,
        },
        basis=[
            "companion_status.server.running",
        ],
    )


def _component_game_session(
    games: dict[str, Any],
) -> dict[str, Any]:
    if not games:
        return _component(
            subsystem="games",
            component="game_session",
            health="unknown",
            severity="warning",
            event_code="GAME-STATUS-UNAVAILABLE",
            summary=(
                "Games status was unavailable."
            ),
            basis=[
                "games_status",
            ],
        )

    active = bool(
        games.get(
            "active",
            False,
        )
    )
    paused = bool(
        games.get(
            "paused",
            False,
        )
    )

    if active:
        return _component(
            subsystem="games",
            component="game_session",
            health="healthy",
            severity="info",
            event_code=(
                "GAME-SESSION-PAUSED"
                if paused
                else "GAME-SESSION-ACTIVE"
            ),
            summary=(
                "Game session is paused safely."
                if paused
                else "Game session is active."
            ),
            measurements={
                "active": True,
                "paused": paused,
            },
            basis=[
                "games_status.active",
                "games_status.paused",
            ],
        )

    return _component(
        subsystem="games",
        component="game_session",
        health="idle",
        severity="info",
        event_code="GAME-SESSION-IDLE",
        summary=(
            "No active game session."
        ),
        measurements={
            "active": False,
            "paused": paused,
        },
        basis=[
            "games_status.active",
        ],
    )


def _component_native_stream(
    native: dict[str, Any],
) -> dict[str, Any]:
    ready = bool(
        native.get(
            "ready",
            False,
        )
    )
    active = bool(
        native.get(
            "active",
            False,
        )
    )

    measurements = {
        "ready": ready,
        "active": active,
        "width": native.get(
            "width"
        ),
        "height": native.get(
            "height"
        ),
        "fps": native.get(
            "fps"
        ),
        "source_bitrate_kbps": (
            native.get(
                "source_bitrate_kbps"
            )
        ),
        "fec_enabled": bool(
            native.get(
                "fec_enabled",
                False,
            )
        ),
        "fec_group_size": (
            native.get(
                "fec_group_size"
            )
        ),
    }

    if not ready:
        return _component(
            subsystem="stream",
            component="native_stream",
            health="unavailable",
            severity="error",
            event_code="STREAM-HOST-UNAVAILABLE",
            summary=(
                "Native stream host is not ready."
            ),
            measurements=measurements,
            basis=[
                "games_status.native_stream.ready",
            ],
        )

    if active:
        return _component(
            subsystem="stream",
            component="native_stream",
            health="healthy",
            severity="info",
            event_code="STREAM-HOST-ACTIVE",
            summary=(
                "Native stream host is active."
            ),
            measurements=measurements,
            basis=[
                "games_status.native_stream.ready",
                "games_status.native_stream.active",
            ],
        )

    return _component(
        subsystem="stream",
        component="native_stream",
        health="idle",
        severity="info",
        event_code="STREAM-HOST-IDLE",
        summary=(
            "Native stream host is ready and idle."
        ),
        measurements=measurements,
        basis=[
            "games_status.native_stream.ready",
            "games_status.native_stream.active",
        ],
    )


def _component_capture(
    native: dict[str, Any],
) -> dict[str, Any]:
    stream_active = bool(
        native.get(
            "active",
            False,
        )
    )
    runtime_found = bool(
        native.get(
            "wgc_runtime_found",
            False,
        )
    )
    target_present = bool(
        _dict(
            native.get(
                "capture_target"
            )
        )
    )

    measurements = {
        "runtime_found": runtime_found,
        "stream_active": stream_active,
        "capture_target_present": (
            target_present
        ),
        "capture_backend": (
            native.get(
                "capture_backend"
            )
        ),
    }

    if not runtime_found:
        return _component(
            subsystem="stream.video",
            component="capture",
            health="unavailable",
            severity="error",
            event_code="VIDEO-CAPTURE-RUNTIME-MISSING",
            summary=(
                "Native capture runtime is unavailable."
            ),
            measurements=measurements,
            basis=[
                "native_stream.wgc_runtime_found",
            ],
        )

    if stream_active and not target_present:
        return _component(
            subsystem="stream.video",
            component="capture",
            health="degraded",
            severity="warning",
            event_code="VIDEO-CAPTURE-TARGET-UNKNOWN",
            summary=(
                "Stream is active but capture target "
                "metadata is unavailable."
            ),
            measurements=measurements,
            basis=[
                "native_stream.active",
                "native_stream.capture_target",
            ],
        )

    if stream_active:
        return _component(
            subsystem="stream.video",
            component="capture",
            health="healthy",
            severity="info",
            event_code="VIDEO-CAPTURE-ACTIVE",
            summary=(
                "Managed native capture is active."
            ),
            measurements=measurements,
            basis=[
                "native_stream.active",
                "native_stream.capture_target",
            ],
        )

    return _component(
        subsystem="stream.video",
        component="capture",
        health="idle",
        severity="info",
        event_code="VIDEO-CAPTURE-IDLE",
        summary=(
            "Capture runtime is available and idle."
        ),
        measurements=measurements,
        basis=[
            "native_stream.wgc_runtime_found",
            "native_stream.active",
        ],
    )


def _component_transport(
    native: dict[str, Any],
) -> dict[str, Any]:
    stream_active = bool(
        native.get(
            "active",
            False,
        )
    )
    fec = _dict(
        native.get("fec")
    )
    running = bool(
        fec.get(
            "running",
            False,
        )
    )
    send_errors = _nonnegative_int(
        fec.get(
            "send_errors",
            0,
        )
    )

    measurements = {
        "running": running,
        "group_size": (
            fec.get(
                "group_size"
            )
        ),
        "rtp_packets": (
            _nonnegative_int(
                fec.get(
                    "rtp_packets",
                    0,
                )
            )
        ),
        "rtp_bytes": (
            _nonnegative_int(
                fec.get(
                    "rtp_bytes",
                    0,
                )
            )
        ),
        "parity_packets": (
            _nonnegative_int(
                fec.get(
                    "parity_packets",
                    0,
                )
            )
        ),
        "parity_bytes": (
            _nonnegative_int(
                fec.get(
                    "parity_bytes",
                    0,
                )
            )
        ),
        "skipped_packets": (
            _nonnegative_int(
                fec.get(
                    "skipped_packets",
                    0,
                )
            )
        ),
        "send_errors": send_errors,
    }

    if not stream_active:
        return _component(
            subsystem="stream.transport",
            component="video_transport",
            health="idle",
            severity="info",
            event_code="NET-VIDEO-IDLE",
            summary=(
                "Video transport is idle."
            ),
            measurements=measurements,
            basis=[
                "native_stream.active",
            ],
        )

    if running and send_errors == 0:
        return _component(
            subsystem="stream.transport",
            component="video_transport",
            health="healthy",
            severity="info",
            event_code="NET-VIDEO-SENDER-HEALTHY",
            summary=(
                "Video/FEC sender is running with no "
                "reported send errors."
            ),
            measurements=measurements,
            basis=[
                "native_stream.fec.running",
                "native_stream.fec.send_errors",
            ],
        )

    if running:
        return _component(
            subsystem="stream.transport",
            component="video_transport",
            health="degraded",
            severity="warning",
            event_code="NET-VIDEO-SEND-ERRORS",
            summary=(
                "Video/FEC sender is running but "
                "reported send errors."
            ),
            measurements=measurements,
            basis=[
                "native_stream.fec.running",
                "native_stream.fec.send_errors",
            ],
        )

    return _component(
        subsystem="stream.transport",
        component="video_transport",
        health="unavailable",
        severity="error",
        event_code="NET-VIDEO-SENDER-STOPPED",
        summary=(
            "Native stream is active but the video/FEC "
            "sender is not running."
        ),
        measurements=measurements,
        basis=[
            "native_stream.active",
            "native_stream.fec.running",
        ],
    )


def _component_audio(
    native: dict[str, Any],
) -> dict[str, Any]:
    stream_active = bool(
        native.get(
            "active",
            False,
        )
    )
    audio = _dict(
        native.get("audio")
    )
    active = bool(
        audio.get(
            "active",
            False,
        )
    )
    error = _clean_text(
        audio.get("error")
    )
    send_errors = _nonnegative_int(
        audio.get(
            "send_errors",
            0,
        )
    )

    measurements = {
        "active": active,
        "sample_rate": (
            audio.get(
                "sample_rate"
            )
        ),
        "channels": (
            audio.get(
                "channels"
            )
        ),
        "packet_ms": (
            audio.get(
                "packet_ms"
            )
        ),
        "packets_sent": (
            _nonnegative_int(
                audio.get(
                    "packets_sent",
                    0,
                )
            )
        ),
        "send_errors": send_errors,
        "error_present": bool(
            error
        ),
    }

    if not stream_active:
        return _component(
            subsystem="stream.audio",
            component="audio",
            health="idle",
            severity="info",
            event_code="AUDIO-STREAM-IDLE",
            summary=(
                "Game audio stream is idle."
            ),
            measurements=measurements,
            basis=[
                "native_stream.active",
            ],
        )

    if error or send_errors > 0:
        return _component(
            subsystem="stream.audio",
            component="audio",
            health="degraded",
            severity="warning",
            event_code="AUDIO-STREAM-DEGRADED",
            summary=(
                "Game audio reported an error condition."
            ),
            measurements=measurements,
            basis=[
                "native_stream.audio.error",
                "native_stream.audio.send_errors",
            ],
        )

    if active:
        return _component(
            subsystem="stream.audio",
            component="audio",
            health="healthy",
            severity="info",
            event_code="AUDIO-STREAM-ACTIVE",
            summary=(
                "Game audio stream is active."
            ),
            measurements=measurements,
            basis=[
                "native_stream.audio.active",
            ],
        )

    return _component(
        subsystem="stream.audio",
        component="audio",
        health="degraded",
        severity="warning",
        event_code="AUDIO-STREAM-INACTIVE",
        summary=(
            "Native video stream is active but audio is "
            "not reporting active."
        ),
        measurements=measurements,
        basis=[
            "native_stream.active",
            "native_stream.audio.active",
        ],
    )


def _component_controller(
    native: dict[str, Any],
    games: dict[str, Any],
) -> dict[str, Any]:
    game_active = bool(
        games.get(
            "active",
            False,
        )
    )
    controller = _dict(
        native.get("controller")
    )
    active = bool(
        controller.get(
            "active",
            False,
        )
    )
    error = _clean_text(
        controller.get("error")
    )

    measurements = {
        "active": active,
        "players": (
            controller.get(
                "players"
            )
        ),
        "packets_received": (
            _nonnegative_int(
                controller.get(
                    "packets_received",
                    0,
                )
            )
        ),
        "lost_packets": (
            _nonnegative_int(
                controller.get(
                    "lost_packets",
                    0,
                )
            )
        ),
        "rejected_packets": (
            _nonnegative_int(
                controller.get(
                    "rejected_packets",
                    0,
                )
            )
        ),
        "bad_packets": (
            _nonnegative_int(
                controller.get(
                    "bad_packets",
                    0,
                )
            )
        ),
        "vigem_updates": (
            _nonnegative_int(
                controller.get(
                    "vigem_updates",
                    0,
                )
            )
        ),
        "error_present": bool(
            error
        ),
    }

    if error:
        return _component(
            subsystem="stream.input",
            component="controller_bridge",
            health="degraded",
            severity="warning",
            event_code="GAME-INPUT-BRIDGE-ERROR",
            summary=(
                "Controller bridge reported an error."
            ),
            measurements=measurements,
            basis=[
                "native_stream.controller.error",
            ],
        )

    if game_active and active:
        return _component(
            subsystem="stream.input",
            component="controller_bridge",
            health="healthy",
            severity="info",
            event_code="GAME-INPUT-BRIDGE-ACTIVE",
            summary=(
                "Controller bridge is active."
            ),
            measurements=measurements,
            basis=[
                "games_status.active",
                "native_stream.controller.active",
            ],
        )

    if game_active:
        return _component(
            subsystem="stream.input",
            component="controller_bridge",
            health="degraded",
            severity="warning",
            event_code="GAME-INPUT-BRIDGE-INACTIVE",
            summary=(
                "A game session is active but the "
                "controller bridge is not active."
            ),
            measurements=measurements,
            basis=[
                "games_status.active",
                "native_stream.controller.active",
            ],
        )

    return _component(
        subsystem="stream.input",
        component="controller_bridge",
        health="idle",
        severity="info",
        event_code="GAME-INPUT-IDLE",
        summary=(
            "Controller bridge is idle."
        ),
        measurements=measurements,
        basis=[
            "games_status.active",
        ],
    )


def _component_resources(
    resource: dict[str, Any],
    stream_active: bool,
) -> dict[str, Any]:
    availability = _clean_text(
        resource.get(
            "availability"
        )
    )

    measurements = {
        "availability": availability,
        "measurement_scope": (
            resource.get(
                "measurement_scope"
            )
        ),
        "sample_count": (
            _dict(
                resource.get(
                    "sampling"
                )
            ).get(
                "sample_count"
            )
        ),
        "sample_interval_seconds": (
            _dict(
                resource.get(
                    "sampling"
                )
            ).get(
                "sample_interval_seconds"
            )
        ),
        "logical_cpu_count": (
            resource.get(
                "logical_cpu_count"
            )
        ),
        "benchmark_thresholds_applied": (
            _dict(
                resource.get(
                    "optimization"
                )
            ).get(
                "benchmark_thresholds_applied"
            )
        ),
    }

    if availability == "degraded":
        return _component(
            subsystem="resources",
            component="host_resources",
            health="degraded",
            severity="warning",
            event_code="RESOURCE-TELEMETRY-DEGRADED",
            summary=(
                "Existing host resource telemetry "
                "reported an error."
            ),
            measurements=measurements,
            basis=[
                "resource_snapshot.availability",
            ],
        )

    if availability == "available":
        return _component(
            subsystem="resources",
            component="host_resources",
            health="healthy",
            severity="info",
            event_code="RESOURCE-TELEMETRY-AVAILABLE",
            summary=(
                "Existing host resource telemetry is "
                "available. Capacity thresholds are not "
                "applied yet."
            ),
            measurements=measurements,
            basis=[
                "resource_snapshot.availability",
                "resource_snapshot.optimization",
            ],
        )

    if stream_active:
        return _component(
            subsystem="resources",
            component="host_resources",
            health="unknown",
            severity="info",
            event_code="RESOURCE-TELEMETRY-WARMING",
            summary=(
                "Native streaming is active but resource "
                "telemetry has not produced a usable "
                "sample yet."
            ),
            measurements=measurements,
            basis=[
                "resource_snapshot.availability",
            ],
        )

    return _component(
        subsystem="resources",
        component="host_resources",
        health="idle",
        severity="info",
        event_code="RESOURCE-TELEMETRY-IDLE",
        summary=(
            "Resource telemetry is session-scoped and "
            "currently idle."
        ),
        measurements=measurements,
        basis=[
            "resource_snapshot.availability",
        ],
    )


def _client_feedback_parts(
    client_feedback: Any,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    store = _dict(client_feedback)
    report = _dict(store.get("report"))
    delta = _dict(store.get("delta"))
    return store, report, delta


def _component_network_path(
    stream_active: bool,
    client_feedback: Any,
) -> dict[str, Any]:
    store, report, delta = _client_feedback_parts(client_feedback)
    available = bool(store.get("available", False))
    fresh = bool(store.get("fresh", False))
    delta_available = bool(store.get("delta_available", False))
    video = _dict(report.get("video"))
    video_delta = _dict(delta.get("video"))

    measurements = {
        "client_feedback_available": available,
        "client_feedback_fresh": fresh,
        "client_feedback_age_ms": store.get("age_ms"),
        "client_feedback_payload_bytes": store.get("payload_bytes", 0),
        "client_feedback_interval_ms": report.get("interval_ms"),
        "client_feedback_sequence": report.get("sequence"),
        "delta_available": delta_available,
        "recent_fps": video.get("recent_fps"),
        "recent_mbps": video.get("recent_mbps"),
        "waiting_for_idr": video.get("waiting_for_idr"),
        "delta_lost_packets": video_delta.get("lost_packets"),
        "delta_dropped_frames": video_delta.get("dropped_frames"),
        "delta_fec_recovered_packets": video_delta.get("fec_recovered_packets"),
        "delta_fec_unrecoverable_groups": video_delta.get("fec_unrecoverable_groups"),
        "delta_late_or_reordered_packets": video_delta.get("late_or_reordered_packets"),
        "adaptive_thresholds_applied": False,
    }

    if not stream_active:
        return _component(
            subsystem="network",
            component="end_to_end_path",
            health="idle",
            severity="info",
            event_code="NET-PATH-IDLE",
            summary="No active stream requires end-to-end path health classification.",
            measurements=measurements,
            basis=["native_stream.active"],
        )

    if not available:
        return _component(
            subsystem="network",
            component="end_to_end_path",
            health="unknown",
            severity="info",
            event_code="NET-PATH-FEEDBACK-PENDING",
            summary="Active stream has no client path-health feedback yet.",
            measurements=measurements,
            basis=["client_feedback.available"],
        )

    if not fresh:
        return _component(
            subsystem="network",
            component="end_to_end_path",
            health="unknown",
            severity="warning",
            event_code="NET-PATH-FEEDBACK-STALE",
            summary="Client path-health feedback is stale.",
            measurements=measurements,
            basis=["client_feedback.fresh"],
        )

    if not delta_available:
        return _component(
            subsystem="network",
            component="end_to_end_path",
            health="unknown",
            severity="info",
            event_code="NET-PATH-FEEDBACK-WARMING",
            summary="Fresh client feedback is available; one more sample is required for deltas.",
            measurements=measurements,
            basis=["client_feedback.delta_available"],
        )

    waiting_for_idr = bool(video.get("waiting_for_idr", False))
    unrecoverable = _nonnegative_int(video_delta.get("fec_unrecoverable_groups", 0))
    dropped = _nonnegative_int(video_delta.get("dropped_frames", 0))
    recovered = _nonnegative_int(video_delta.get("fec_recovered_packets", 0))

    if waiting_for_idr or unrecoverable > 0 or dropped > 0:
        return _component(
            subsystem="network",
            component="end_to_end_path",
            health="degraded",
            severity="warning",
            event_code="NET-PATH-CLIENT-DEGRADED",
            summary="Fresh client feedback observed an unrecovered video-path impairment.",
            measurements=measurements,
            basis=[
                "client_feedback.video_delta",
                "client_feedback.video.waiting_for_idr",
            ],
        )

    return _component(
        subsystem="network",
        component="end_to_end_path",
        health="healthy",
        severity="info",
        event_code=(
            "NET-PATH-FEC-RECOVERED"
            if recovered > 0
            else "NET-PATH-CLIENT-HEALTHY"
        ),
        summary="Fresh client feedback reports a healthy video path.",
        measurements=measurements,
        basis=["client_feedback.video_delta"],
    )


def _component_decoder(
    stream_active: bool,
    client_feedback: Any,
) -> dict[str, Any]:
    store, report, delta = _client_feedback_parts(client_feedback)
    available = bool(store.get("available", False))
    fresh = bool(store.get("fresh", False))
    delta_available = bool(store.get("delta_available", False))
    decoder = _dict(report.get("decoder"))
    decoder_delta = _dict(delta.get("decoder"))

    measurements = {
        "client_feedback_available": available,
        "client_feedback_fresh": fresh,
        "client_feedback_age_ms": store.get("age_ms"),
        "client_feedback_sequence": report.get("sequence"),
        "delta_available": delta_available,
        "hardware_accelerated": decoder.get("hardware_accelerated"),
        "vendor_codec": decoder.get("vendor_codec"),
        "low_latency_enabled": decoder.get("low_latency_enabled"),
        "queue_depth": decoder.get("queue_depth"),
        "latest_rx_to_decode_ms": decoder.get("latest_rx_to_decode_ms"),
        "latest_output_gap_ms": decoder.get("latest_output_gap_ms"),
        "delta_dropped_frames": decoder_delta.get("dropped_frames"),
        "delta_queue_overflow_drops": decoder_delta.get("queue_overflow_drops"),
        "delta_stale_output_drops": decoder_delta.get("stale_output_drops"),
    }

    if not stream_active:
        return _component(
            subsystem="client.video",
            component="decoder",
            health="idle",
            severity="info",
            event_code="VIDEO-DECODER-IDLE",
            summary="No active native stream requires decoder health classification.",
            measurements=measurements,
            basis=["native_stream.active"],
        )

    if not available:
        return _component(
            subsystem="client.video",
            component="decoder",
            health="unknown",
            severity="info",
            event_code="VIDEO-DECODER-FEEDBACK-PENDING",
            summary="Active stream has no client decoder feedback yet.",
            measurements=measurements,
            basis=["client_feedback.available"],
        )

    if not fresh:
        return _component(
            subsystem="client.video",
            component="decoder",
            health="unknown",
            severity="warning",
            event_code="VIDEO-DECODER-FEEDBACK-STALE",
            summary="Client decoder feedback is stale.",
            measurements=measurements,
            basis=["client_feedback.fresh"],
        )

    if not delta_available:
        return _component(
            subsystem="client.video",
            component="decoder",
            health="unknown",
            severity="info",
            event_code="VIDEO-DECODER-FEEDBACK-WARMING",
            summary="Fresh decoder feedback is available; one more sample is required for deltas.",
            measurements=measurements,
            basis=["client_feedback.delta_available"],
        )

    hardware = bool(decoder.get("hardware_accelerated", False))
    dropped = _nonnegative_int(decoder_delta.get("dropped_frames", 0))
    overflow = _nonnegative_int(decoder_delta.get("queue_overflow_drops", 0))
    stale = _nonnegative_int(decoder_delta.get("stale_output_drops", 0))
    rendered = _nonnegative_int(decoder_delta.get("rendered_frames", 0))
    queued = _nonnegative_int(decoder_delta.get("queued_frames", 0))

    measurements["delta_rendered_frames"] = rendered
    measurements["delta_queued_frames"] = queued
    measurements["stale_output_shedding_observed"] = stale > 0

    if not hardware:
        return _component(
            subsystem="client.video",
            component="decoder",
            health="degraded",
            severity="warning",
            event_code="VIDEO-DECODER-HARDWARE-UNAVAILABLE",
            summary="Fresh client feedback reports that hardware decoding is unavailable.",
            measurements=measurements,
            basis=[
                "client_feedback.decoder.hardware_accelerated",
            ],
        )

    if dropped > 0 or overflow > 0:
        return _component(
            subsystem="client.video",
            component="decoder",
            health="degraded",
            severity="warning",
            event_code="VIDEO-DECODER-LOCAL-DROPS",
            summary="Fresh client feedback observed decoder-local frame loss or queue overflow.",
            measurements=measurements,
            basis=[
                "client_feedback.decoder_delta.dropped_frames",
                "client_feedback.decoder_delta.queue_overflow_drops",
            ],
        )

    if stale > 0:
        return _component(
            subsystem="client.video",
            component="decoder",
            health="healthy",
            severity="info",
            event_code="VIDEO-DECODER-LOW-LATENCY-SHEDDING",
            summary="Hardware decoder is healthy; stale outputs were discarded by the low-latency policy without decoder-local drops or queue overflow.",
            measurements=measurements,
            basis=[
                "client_feedback.decoder.hardware_accelerated",
                "client_feedback.decoder_delta.stale_output_drops",
                "client_feedback.decoder_delta.dropped_frames",
                "client_feedback.decoder_delta.queue_overflow_drops",
            ],
        )

    return _component(
        subsystem="client.video",
        component="decoder",
        health="healthy",
        severity="info",
        event_code="VIDEO-DECODER-CLIENT-HEALTHY",
        summary="Fresh client feedback reports a healthy hardware decoder path.",
        measurements=measurements,
        basis=[
            "client_feedback.decoder",
            "client_feedback.decoder_delta",
        ],
    )


def _overall(
    components: list[dict[str, Any]],
) -> dict[str, Any]:
    error_components = [
        item
        for item in components
        if item.get("severity") == "error"
    ]
    warning_components = [
        item
        for item in components
        if item.get("severity") == "warning"
    ]

    if error_components:
        return {
            "health": "unavailable",
            "severity": "error",
            "event_code": (
                "SYSTEM-HEALTH-ERROR"
            ),
            "summary": (
                "One or more required components are "
                "unavailable."
            ),
        }

    if warning_components:
        return {
            "health": "degraded",
            "severity": "warning",
            "event_code": (
                "SYSTEM-HEALTH-DEGRADED"
            ),
            "summary": (
                "No fatal condition is classified, but "
                "one or more components are degraded."
            ),
        }

    return {
        "health": "healthy",
        "severity": "info",
        "event_code": (
            "SYSTEM-HEALTH-HEALTHY"
        ),
        "summary": (
            "No known error or warning condition is "
            "classified."
        ),
    }


def build_health_snapshot(
    *,
    companion_status: Any,
    games_status: Any,
    host_telemetry_payload: Any = None,
    client_feedback: Any = None,
    generated_unix_ms: int | None = None,
) -> dict[str, Any]:
    companion = _dict(
        companion_status
    )
    games = _dict(
        games_status
    )
    native = _dict(
        games.get(
            "native_stream"
        )
    )

    resource = build_resource_snapshot(
        native,
        host_telemetry_payload,
    )

    components = [
        _component_companion(
            companion
        ),
        _component_media_server(
            companion
        ),
        _component_game_session(
            games
        ),
        _component_native_stream(
            native
        ),
        _component_capture(
            native
        ),
        _component_transport(
            native
        ),
        _component_audio(
            native
        ),
        _component_controller(
            native,
            games,
        ),
        _component_resources(
            resource,
            bool(
                native.get(
                    "active",
                    False,
                )
            ),
        ),
        _component_network_path(
            bool(
                native.get(
                    "active",
                    False,
                )
            ),
            client_feedback,
        ),
        _component_decoder(
            bool(
                native.get(
                    "active",
                    False,
                )
            ),
            client_feedback,
        ),
    ]

    counts = {
        health: sum(
            1
            for item in components
            if item.get(
                "health"
            ) == health
        )
        for health in sorted(
            HEALTH_VALUES
        )
    }

    return {
        "schema": HEALTH_SCHEMA,
        "classifier": {
            "id": CLASSIFIER_ID,
            "version": 1,
        },
        "generated_unix_ms": (
            int(generated_unix_ms)
            if generated_unix_ms is not None
            else None
        ),
        "session": {
            "game_active": bool(
                games.get(
                    "active",
                    False,
                )
            ),
            "paused": bool(
                games.get(
                    "paused",
                    False,
                )
            ),
            "native_stream_active": bool(
                native.get(
                    "active",
                    False,
                )
            ),
        },
        "overall": _overall(
            components
        ),
        "coverage": {
            "component_count": len(
                components
            ),
            "health_counts": counts,
            "unknown_is_not_failure": True,
        },
        "components": components,
        "resources": resource,
        "client_feedback": _dict(
            client_feedback
        ),
    }
