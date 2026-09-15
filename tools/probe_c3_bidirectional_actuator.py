#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any


CONTROL_BASE = "http://127.0.0.1:8765"
PROFILE_ID = "native_game_720p60_reference"
STATE_SCHEMA = "privyhub_c3_bidirectional_actuator_probe_state_v1"
TRANSITION_SCHEMA = "privyhub_c3_validated_bitrate_transition_v1"
TEXT_LOG = Path(
    "logs/streaming/c3_bidirectional_actuator_probe.txt"
)
JSON_LOG = Path(
    "logs/streaming/c3_bidirectional_actuator_probe.json"
)
STATE_PATH = Path(
    "logs/streaming/c3_bidirectional_actuator_probe_state.json"
)
DECODER_ROOT = Path(
    "logs/games/decoder_sessions"
)

CLEAN_SAMPLE_TARGET = 2
SAMPLE_TIMEOUT_SECONDS = 14.0
MIN_RECENT_FPS = 45.0
MAX_OUTPUT_GAP_MS = 120
MAX_RX_TO_DECODE_MS = 150


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _request_json(
    path: str,
    *,
    method: str = "GET",
    timeout: float = 8.0,
) -> dict[str, Any]:
    request = urllib.request.Request(
        CONTROL_BASE + path,
        data=(b"" if method == "POST" else None),
        method=method,
        headers={
            "Cache-Control": "no-cache",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            payload = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode(
                "utf-8",
                errors="replace",
            )
        except Exception:
            detail = ""
        raise RuntimeError(
            "Companion diagnostic request failed "
            f"with HTTP {exc.code}: {detail[:700]}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            "Companion diagnostic request failed: "
            + type(exc).__name__
        ) from exc

    if not isinstance(payload, dict):
        raise RuntimeError(
            "Companion diagnostic response was not an object"
        )

    return payload


def _decoder_files() -> list[str]:
    if not DECODER_ROOT.is_dir():
        return []

    return sorted(
        path.name
        for path in DECODER_ROOT.glob(
            "native_decoder_*.json"
        )
        if path.is_file()
    )


def _write(
    *,
    result: str,
    details: list[str],
    measurements: dict[str, Any],
    problems: list[str],
    payload: dict[str, Any],
) -> None:
    TEXT_LOG.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = [
        "PrivyHub C3 bidirectional bitrate actuator probe",
        f"Result: {result}",
        "",
        "Privacy:",
        "- Network addresses printed: NO",
        "- Endpoint identity persisted: NO",
        "",
        "Details:",
        *(
            [f"- {item}" for item in details]
            if details
            else ["<none>"]
        ),
        "",
        "Measurements:",
        *[
            f"- {key}: {value}"
            for key, value in measurements.items()
        ],
        "",
        "Problems:",
        *(
            [f"- {item}" for item in problems]
            if problems
            else ["<none>"]
        ),
    ]

    TEXT_LOG.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    JSON_LOG.write_text(
        json.dumps(
            {
                "result": result,
                "details": details,
                "measurements": measurements,
                "problems": problems,
                "payload": payload,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print("\n".join(lines))


def _sample_clean(
    telemetry: dict[str, Any],
) -> bool:
    receiver = _dict(
        telemetry.get("receiver")
    )
    decoder = _dict(
        telemetry.get("decoder")
    )
    latency = _dict(
        telemetry.get("latency")
    )

    recent_fps = _number(
        receiver.get("recent_fps")
    )
    rendered = _int(
        decoder.get("rendered_frames_delta")
    )
    dropped = _int(
        decoder.get("dropped_frames_delta")
    )
    overflow = _int(
        decoder.get(
            "queue_overflow_drops_delta"
        )
    )
    queue_depth = _int(
        decoder.get("queue_depth")
    )
    output_gap = _int(
        latency.get("output_gap_ms")
    )
    rx_decode = _int(
        latency.get("receive_to_decode_ms")
    )

    return (
        bool(telemetry.get("available", False))
        and bool(telemetry.get("fresh", False))
        and bool(
            telemetry.get(
                "delta_available",
                False,
            )
        )
        and receiver.get(
            "waiting_for_idr"
        )
        is False
        and recent_fps is not None
        and recent_fps >= MIN_RECENT_FPS
        and rendered > 0
        and dropped == 0
        and overflow == 0
        and queue_depth == 0
        and output_gap <= MAX_OUTPUT_GAP_MS
        and rx_decode <= MAX_RX_TO_DECODE_MS
    )


def _collect_transition_samples(
    *,
    after_elapsed_ms: int,
) -> tuple[list[dict[str, Any]], int]:
    samples: list[dict[str, Any]] = []
    seen: set[int] = set()
    consecutive_clean = 0
    best_clean = 0

    deadline = (
        time.monotonic()
        + SAMPLE_TIMEOUT_SECONDS
    )

    while time.monotonic() < deadline:
        telemetry = _request_json(
            "/diagnostics/stream-telemetry"
        )

        elapsed = _int(
            telemetry.get(
                "session_elapsed_ms"
            )
        )

        if (
            elapsed > after_elapsed_ms
            and elapsed not in seen
        ):
            seen.add(elapsed)
            samples.append(telemetry)

            if _sample_clean(telemetry):
                consecutive_clean += 1
                best_clean = max(
                    best_clean,
                    consecutive_clean,
                )
            else:
                consecutive_clean = 0

            if (
                consecutive_clean
                >= CLEAN_SAMPLE_TARGET
            ):
                break

        time.sleep(0.5)

    return samples, best_clean


def _transition(
    *,
    target_kbps: int,
    after_elapsed_ms: int,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    int,
]:
    cycle = _request_json(
        "/plugins/games/"
        "c3-validated-bitrate-transition"
        f"?target={target_kbps}",
        method="POST",
        timeout=15.0,
    )

    samples, clean_count = (
        _collect_transition_samples(
            after_elapsed_ms=after_elapsed_ms
        )
    )

    return cycle, samples, clean_count


def _sample_measurements(
    prefix: str,
    samples: list[dict[str, Any]],
) -> dict[str, Any]:
    if not samples:
        return {
            f"{prefix}_sample_count": 0,
        }

    max_output_gap = 0
    max_rx_decode = 0
    rendered = 0
    dropped = 0
    overflow = 0
    lost = 0
    unrecoverable = 0

    for telemetry in samples:
        decoder = _dict(
            telemetry.get("decoder")
        )
        latency = _dict(
            telemetry.get("latency")
        )
        receiver = _dict(
            telemetry.get("receiver")
        )
        fec = _dict(
            telemetry.get("fec")
        )

        max_output_gap = max(
            max_output_gap,
            _int(
                latency.get(
                    "output_gap_ms"
                )
            ),
        )
        max_rx_decode = max(
            max_rx_decode,
            _int(
                latency.get(
                    "receive_to_decode_ms"
                )
            ),
        )
        rendered += max(
            0,
            _int(
                decoder.get(
                    "rendered_frames_delta"
                )
            ),
        )
        dropped += max(
            0,
            _int(
                decoder.get(
                    "dropped_frames_delta"
                )
            ),
        )
        overflow += max(
            0,
            _int(
                decoder.get(
                    "queue_overflow_drops_delta"
                )
            ),
        )
        lost += max(
            0,
            _int(
                receiver.get(
                    "lost_packets_delta"
                )
            ),
        )
        unrecoverable += max(
            0,
            _int(
                fec.get(
                    "unrecoverable_groups_delta"
                )
            ),
        )

    return {
        f"{prefix}_sample_count": len(samples),
        f"{prefix}_rendered_delta": rendered,
        f"{prefix}_dropped_delta": dropped,
        f"{prefix}_overflow_delta": overflow,
        f"{prefix}_lost_packets_delta": lost,
        f"{prefix}_unrecoverable_fec_groups_delta": unrecoverable,
        f"{prefix}_max_output_gap_ms": max_output_gap,
        f"{prefix}_max_rx_to_decode_ms": max_rx_decode,
    }


def _validate_cycle(
    *,
    cycle: dict[str, Any],
    expected_from: int,
    expected_target: int,
    label: str,
    problems: list[str],
) -> None:
    if cycle.get("schema") != TRANSITION_SCHEMA:
        problems.append(
            f"{label}: unexpected transition schema"
        )

    if not bool(
        cycle.get("ok", False)
    ):
        problems.append(
            f"{label}: host transition did not report ok"
        )

    if _int(
        cycle.get("from_bitrate_kbps")
    ) != expected_from:
        problems.append(
            f"{label}: unexpected source bitrate"
        )

    if _int(
        cycle.get("target_bitrate_kbps")
    ) != expected_target:
        problems.append(
            f"{label}: unexpected target bitrate"
        )

    for section, keys in (
        (
            "fec",
            (
                "running_before",
                "running_mid_cycle",
                "running_after",
            ),
        ),
        (
            "audio",
            (
                "active_before",
                "active_mid_cycle",
                "active_after",
            ),
        ),
        (
            "controller",
            (
                "active_before",
                "active_mid_cycle",
                "active_after",
            ),
        ),
    ):
        payload = _dict(
            cycle.get(section)
        )

        if not all(
            bool(
                payload.get(
                    key,
                    False,
                )
            )
            for key in keys
        ):
            problems.append(
                f"{label}: {section} continuity failed"
            )


def _trigger() -> int:
    problems: list[str] = []
    details: list[str] = []
    measurements: dict[str, Any] = {}

    telemetry_before = _request_json(
        "/diagnostics/stream-telemetry"
    )
    status_before = _request_json(
        "/plugins/games/native-stream-status"
    )
    game_before = _request_json(
        "/plugins/games/status"
    )

    if not bool(
        telemetry_before.get(
            "available",
            False,
        )
    ):
        problems.append(
            "stream telemetry unavailable before probe"
        )

    if not bool(
        telemetry_before.get(
            "fresh",
            False,
        )
    ):
        problems.append(
            "stream telemetry stale before probe"
        )

    if not bool(
        telemetry_before.get(
            "delta_available",
            False,
        )
    ):
        problems.append(
            "stream telemetry delta unavailable before probe"
        )

    if telemetry_before.get(
        "profile_id"
    ) != PROFILE_ID:
        problems.append(
            "reference profile is not active"
        )

    if not bool(
        status_before.get(
            "active",
            False,
        )
    ):
        problems.append(
            "native video stream is not active"
        )

    if _int(
        status_before.get(
            "bitrate_kbps"
        )
    ) != 7000:
        problems.append(
            "probe requires a 7000 kbps starting stream"
        )

    if not bool(
        _dict(
            status_before.get(
                "fec"
            )
        ).get(
            "running",
            False,
        )
    ):
        problems.append(
            "FEC relay is not active"
        )

    if not bool(
        _dict(
            status_before.get(
                "audio"
            )
        ).get(
            "active",
            False,
        )
    ):
        problems.append(
            "process audio is not active"
        )

    if not bool(
        _dict(
            status_before.get(
                "controller"
            )
        ).get(
            "active",
            False,
        )
    ):
        problems.append(
            "controller bridge is not active"
        )

    if not bool(
        game_before.get(
            "active",
            False,
        )
    ):
        problems.append(
            "game session is not active"
        )

    if bool(
        game_before.get(
            "paused",
            False,
        )
    ):
        problems.append(
            "game session is paused"
        )

    if problems:
        _write(
            result=(
                "C3_BIDIRECTIONAL_ACTUATOR_TRIGGER_BLOCKED"
            ),
            details=details,
            measurements=measurements,
            problems=problems,
            payload={
                "telemetry_before": telemetry_before,
                "status_before": status_before,
            },
        )
        return 2

    before_files = _decoder_files()
    pre_elapsed = _int(
        telemetry_before.get(
            "session_elapsed_ms"
        )
    )

    down, down_samples, down_clean = (
        _transition(
            target_kbps=6000,
            after_elapsed_ms=pre_elapsed,
        )
    )

    _validate_cycle(
        cycle=down,
        expected_from=7000,
        expected_target=6000,
        label="downshift",
        problems=problems,
    )

    measurements.update(
        {
            "down_host_first_rtp_resume_ms": (
                _dict(
                    down.get("video")
                ).get(
                    "first_rtp_resume_ms"
                )
            ),
            "down_host_verified_ms": (
                _dict(
                    down.get("video")
                ).get(
                    "host_verified_ms"
                )
            ),
            "down_consecutive_clean_samples": (
                down_clean
            ),
        }
    )
    measurements.update(
        _sample_measurements(
            "down",
            down_samples,
        )
    )

    if (
        down_clean
        < CLEAN_SAMPLE_TARGET
    ):
        problems.append(
            "downshift did not reach two consecutive clean telemetry samples; "
            "upshift was not attempted"
        )

        state = {
            "schema": STATE_SCHEMA,
            "decoder_files_before": before_files,
            "telemetry_before": telemetry_before,
            "down_transition": down,
            "down_samples": down_samples,
            "up_transition": None,
            "up_samples": [],
            "trigger_problems": problems,
        }

        STATE_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        STATE_PATH.write_text(
            json.dumps(
                state,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

        _write(
            result=(
                "C3_BIDIRECTIONAL_ACTUATOR_DOWNSHIFT_RECOVERY_FAILED"
            ),
            details=[
                "7000 -> 6000 transition invoked",
                "6000 -> 7000 transition intentionally not attempted",
                "automatic adaptation remains disabled",
            ],
            measurements=measurements,
            problems=problems,
            payload=state,
        )
        return 2

    down_last_elapsed = max(
        [
            _int(
                sample.get(
                    "session_elapsed_ms"
                )
            )
            for sample in down_samples
        ]
        or [pre_elapsed]
    )

    up, up_samples, up_clean = (
        _transition(
            target_kbps=7000,
            after_elapsed_ms=down_last_elapsed,
        )
    )

    _validate_cycle(
        cycle=up,
        expected_from=6000,
        expected_target=7000,
        label="upshift",
        problems=problems,
    )

    measurements.update(
        {
            "up_host_first_rtp_resume_ms": (
                _dict(
                    up.get("video")
                ).get(
                    "first_rtp_resume_ms"
                )
            ),
            "up_host_verified_ms": (
                _dict(
                    up.get("video")
                ).get(
                    "host_verified_ms"
                )
            ),
            "up_consecutive_clean_samples": (
                up_clean
            ),
        }
    )
    measurements.update(
        _sample_measurements(
            "up",
            up_samples,
        )
    )

    if (
        up_clean
        < CLEAN_SAMPLE_TARGET
    ):
        problems.append(
            "upshift did not reach two consecutive clean telemetry samples"
        )

    status_after = _request_json(
        "/plugins/games/native-stream-status"
    )
    game_after = _request_json(
        "/plugins/games/status"
    )

    if not bool(
        status_after.get(
            "active",
            False,
        )
    ):
        problems.append(
            "native stream is not active after upshift"
        )

    if _int(
        status_after.get(
            "bitrate_kbps"
        )
    ) != 7000:
        problems.append(
            "final active bitrate is not 7000 kbps"
        )

    if not bool(
        game_after.get(
            "active",
            False,
        )
    ):
        problems.append(
            "game session is not active after transitions"
        )

    if bool(
        game_after.get(
            "paused",
            False,
        )
    ):
        problems.append(
            "game session became paused during transitions"
        )

    state = {
        "schema": STATE_SCHEMA,
        "decoder_files_before": before_files,
        "telemetry_before": telemetry_before,
        "down_transition": down,
        "down_samples": down_samples,
        "up_transition": up,
        "up_samples": up_samples,
        "status_after": status_after,
        "game_after": game_after,
        "trigger_problems": problems,
    }

    STATE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    STATE_PATH.write_text(
        json.dumps(
            state,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    details.extend(
        [
            "7000 -> 6000 -> 7000 sequence invoked",
            "two consecutive clean telemetry samples required before upshift",
            "FEC relay restart requested: NO",
            "process-audio restart requested: NO",
            "controller restart requested: NO",
            "automatic adaptation remains disabled",
            "session-end decoder report still required",
        ]
    )

    result = (
        "C3_BIDIRECTIONAL_ACTUATOR_TRIGGERED"
        if not problems
        else "C3_BIDIRECTIONAL_ACTUATOR_TRIGGERED_WITH_FINDINGS"
    )

    _write(
        result=result,
        details=details,
        measurements=measurements,
        problems=problems,
        payload=state,
    )

    return 0


def _finalize() -> int:
    if not STATE_PATH.is_file():
        _write(
            result=(
                "C3_BIDIRECTIONAL_ACTUATOR_FINALIZE_BLOCKED"
            ),
            details=[],
            measurements={},
            problems=[
                "trigger state is missing"
            ],
            payload={},
        )
        return 2

    state = json.loads(
        STATE_PATH.read_text(
            encoding="utf-8"
        )
    )

    if (
        not isinstance(state, dict)
        or state.get("schema")
        != STATE_SCHEMA
    ):
        raise RuntimeError(
            "C3 bidirectional actuator trigger state is invalid"
        )

    before = set(
        state.get(
            "decoder_files_before",
            [],
        )
    )

    candidates = (
        [
            path
            for path in DECODER_ROOT.glob(
                "native_decoder_*.json"
            )
            if (
                path.is_file()
                and path.name not in before
            )
        ]
        if DECODER_ROOT.is_dir()
        else []
    )

    if not candidates:
        _write(
            result=(
                "C3_BIDIRECTIONAL_ACTUATOR_FINALIZE_NEEDS_SESSION_END"
            ),
            details=[
                "No new decoder-session report was found."
            ],
            measurements={},
            problems=[
                "End the normal game session before finalizing."
            ],
            payload=state,
        )
        return 2

    latest = max(
        candidates,
        key=lambda path: (
            path.stat().st_mtime_ns
        ),
    )

    document = json.loads(
        latest.read_text(
            encoding="utf-8"
        )
    )

    report = _dict(
        _dict(document).get("report")
    )
    video = _dict(
        report.get("video")
    )
    decoder = _dict(
        report.get("decoder")
    )
    audio = _dict(
        report.get("audio")
    )
    controller = _dict(
        report.get("controller")
    )

    measurements = {
        "session_duration_ms": report.get(
            "duration_ms"
        ),
        "sequence_resyncs": video.get(
            "sequence_resyncs"
        ),
        "ssrc_changes": video.get(
            "ssrc_changes"
        ),
        "packets_dropped_waiting_for_idr": (
            video.get(
                "packets_dropped_waiting_for_idr"
            )
        ),
        "resync_to_idr_ms": video.get(
            "resync_to_idr_ms"
        ),
        "max_resync_to_idr_ms": video.get(
            "max_resync_to_idr_ms"
        ),
        "waiting_for_idr_at_end": video.get(
            "waiting_for_idr"
        ),
        "lost_packets": video.get(
            "lost_packets"
        ),
        "fec_recovered_packets": video.get(
            "fec_recovered_packets"
        ),
        "fec_unrecoverable_groups": video.get(
            "fec_unrecoverable_groups"
        ),
        "decoder_rendered_frames": decoder.get(
            "rendered_frames"
        ),
        "decoder_dropped_frames": decoder.get(
            "dropped_frames"
        ),
        "decoder_queue_overflow_drops": (
            decoder.get(
                "queue_overflow_drops"
            )
        ),
        "decoder_max_output_gap_ms": (
            decoder.get(
                "max_output_gap_ms"
            )
        ),
        "decoder_max_rx_to_decode_ms": (
            decoder.get(
                "max_rx_to_decode_ms"
            )
        ),
        "audio_lost_packets": audio.get(
            "lost_packets"
        ),
        "audio_write_errors": audio.get(
            "write_errors"
        ),
        "audio_underruns": audio.get(
            "underruns"
        ),
        "controller_packets_sent": controller.get(
            "packets_sent"
        ),
        "controller_send_errors": controller.get(
            "send_errors"
        ),
    }

    problems = list(
        state.get(
            "trigger_problems",
            [],
        )
    )

    if bool(
        video.get(
            "waiting_for_idr",
            False,
        )
    ):
        problems.append(
            "receiver was still waiting for IDR at session end"
        )

    if _int(
        video.get(
            "sequence_resyncs"
        )
    ) < 2:
        problems.append(
            "fewer than two sequence resyncs were recorded for two transitions"
        )

    if _int(
        video.get(
            "ssrc_changes"
        )
    ) < 2:
        problems.append(
            "fewer than two SSRC changes were recorded for two transitions"
        )

    if _int(
        audio.get(
            "write_errors"
        )
    ) > 0:
        problems.append(
            "audio write errors were recorded"
        )

    if _int(
        controller.get(
            "send_errors"
        )
    ) > 0:
        problems.append(
            "controller send errors were recorded"
        )

    if _int(
        decoder.get(
            "dropped_frames"
        )
    ) > 0:
        problems.append(
            "decoder dropped frames were recorded"
        )

    if _int(
        decoder.get(
            "queue_overflow_drops"
        )
    ) > 0:
        problems.append(
            "decoder queue-overflow drops were recorded"
        )

    details = [
        "7000 -> 6000 -> 7000 host transition evidence retained",
        f"decoder-session report: {latest.name}",
        "audio burst/gap counters are observational and remain separately deferred",
        "manual gameplay smoothness/transition observation still required",
        "automatic adaptation remains disabled",
    ]

    payload = {
        **state,
        "decoder_session_file": latest.name,
        "decoder_session_report": report,
    }

    result = (
        "C3_BIDIRECTIONAL_ACTUATOR_EVIDENCE_CAPTURED"
        if not problems
        else "C3_BIDIRECTIONAL_ACTUATOR_EVIDENCE_CAPTURED_WITH_FINDINGS"
    )

    _write(
        result=result,
        details=details,
        measurements=measurements,
        problems=problems,
        payload=payload,
    )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the C3 video-only actuator in both directions "
            "using the fixed 7000/6000 ladder points."
        )
    )
    parser.add_argument(
        "--finalize",
        action="store_true",
        help=(
            "Read the new decoder-session report after normal End."
        ),
    )
    args = parser.parse_args()

    if args.finalize:
        return _finalize()

    return _trigger()


if __name__ == "__main__":
    raise SystemExit(main())
