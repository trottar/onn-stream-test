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
STATE_SCHEMA = "privyhub_c3_actuator_probe_state_v1"
TEXT_LOG = Path(
    "logs/streaming/c3_actuator_continuity_probe.txt"
)
JSON_LOG = Path(
    "logs/streaming/c3_actuator_continuity_probe.json"
)
STATE_PATH = Path(
    "logs/streaming/c3_actuator_continuity_probe_state.json"
)
DECODER_ROOT = Path(
    "logs/games/decoder_sessions"
)


def _request_json(
    path: str,
    *,
    method: str = "GET",
    timeout: float = 5.0,
) -> dict[str, Any]:
    request = urllib.request.Request(
        CONTROL_BASE + path,
        data=(
            b""
            if method == "POST"
            else None
        ),
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
            f"with HTTP {exc.code}: {detail[:500]}"
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


def _number(
    value: Any,
) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _dict(
    value: Any,
) -> dict[str, Any]:
    return (
        value
        if isinstance(value, dict)
        else {}
    )


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
        "PrivyHub C3 actuator continuity probe",
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
                "measurements": (
                    measurements
                ),
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

    print(
        "\n".join(lines)
    )


def _trigger() -> int:
    problems: list[str] = []
    details: list[str] = []
    measurements: dict[str, Any] = {}

    telemetry_before = (
        _request_json(
            "/diagnostics/stream-telemetry"
        )
    )
    status_before = (
        _request_json(
            "/plugins/games/native-stream-status"
        )
    )

    receiver_before = _dict(
        telemetry_before.get("receiver")
    )
    decoder_before = _dict(
        telemetry_before.get("decoder")
    )
    fec_status = _dict(
        status_before.get("fec")
    )
    audio_status = _dict(
        status_before.get("audio")
    )
    controller_status = _dict(
        status_before.get("controller")
    )

    if not bool(
        telemetry_before.get(
            "available",
            False,
        )
    ):
        problems.append(
            "stream telemetry unavailable before cycle"
        )

    if not bool(
        telemetry_before.get(
            "fresh",
            False,
        )
    ):
        problems.append(
            "stream telemetry stale before cycle"
        )

    if (
        telemetry_before.get("profile_id")
        != PROFILE_ID
    ):
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

    if int(
        status_before.get(
            "bitrate_kbps",
            0,
        )
        or 0
    ) != 7000:
        problems.append(
            "native video bitrate is not 7000 kbps"
        )

    if not bool(
        fec_status.get(
            "running",
            False,
        )
    ):
        problems.append(
            "FEC relay is not active"
        )

    if not bool(
        audio_status.get(
            "active",
            False,
        )
    ):
        problems.append(
            "process audio is not active"
        )

    if not bool(
        controller_status.get(
            "active",
            False,
        )
    ):
        problems.append(
            "controller bridge is not active"
        )

    if problems:
        _write(
            result=(
                "C3_ACTUATOR_TRIGGER_BLOCKED"
            ),
            details=details,
            measurements=measurements,
            problems=problems,
            payload={
                "telemetry_before": (
                    telemetry_before
                ),
            },
        )
        return 2

    decoder_before_files = (
        _decoder_files()
    )
    trigger_unix_ns = (
        time.time_ns()
    )

    cycle = _request_json(
        "/plugins/games/"
        "c3-actuator-continuity-cycle",
        method="POST",
        timeout=12.0,
    )

    if (
        cycle.get("schema")
        != "privyhub_c3_actuator_cycle_probe_v1"
        or not bool(
            cycle.get(
                "ok",
                False,
            )
        )
    ):
        problems.append(
            "host cycle did not return the expected probe schema"
        )

    video_cycle = _dict(
        cycle.get("video")
    )
    fec_cycle = _dict(
        cycle.get("fec")
    )
    audio_cycle = _dict(
        cycle.get("audio")
    )
    controller_cycle = _dict(
        cycle.get("controller")
    )

    if bool(
        fec_cycle.get(
            "restarted",
            True,
        )
    ):
        problems.append(
            "FEC relay was restarted"
        )

    if not all(
        bool(
            fec_cycle.get(
                key,
                False,
            )
        )
        for key in (
            "running_before",
            "running_mid_cycle",
            "running_after",
        )
    ):
        problems.append(
            "FEC relay was not continuously active"
        )

    if not all(
        bool(
            audio_cycle.get(
                key,
                False,
            )
        )
        for key in (
            "active_before",
            "active_mid_cycle",
            "active_after",
        )
    ):
        problems.append(
            "process audio was not continuously active"
        )

    if not all(
        bool(
            controller_cycle.get(
                key,
                False,
            )
        )
        for key in (
            "active_before",
            "active_mid_cycle",
            "active_after",
        )
    ):
        problems.append(
            "controller bridge was not continuously active"
        )

    # Collect several health epochs after the cycle without adding a sampler.
    samples: list[
        dict[str, Any]
    ] = []
    seen_elapsed: set[int] = set()

    deadline = (
        time.monotonic()
        + 10.0
    )

    while time.monotonic() < deadline:
        telemetry = _request_json(
            "/diagnostics/stream-telemetry"
        )

        elapsed = int(
            telemetry.get(
                "session_elapsed_ms",
                0,
            )
            or 0
        )

        if (
            elapsed > 0
            and elapsed not in seen_elapsed
        ):
            seen_elapsed.add(elapsed)
            samples.append(telemetry)

        if len(samples) >= 4:
            break

        time.sleep(0.5)

    recovered = None

    for telemetry in samples:
        receiver = _dict(
            telemetry.get(
                "receiver"
            )
        )
        recent_fps = _number(
            receiver.get(
                "recent_fps"
            )
        )
        recent_mbps = _number(
            receiver.get(
                "recent_mbps"
            )
        )

        if (
            bool(
                telemetry.get(
                    "available",
                    False,
                )
            )
            and bool(
                telemetry.get(
                    "fresh",
                    False,
                )
            )
            and receiver.get(
                "waiting_for_idr"
            )
            is False
            and recent_fps is not None
            and recent_fps > 0.0
            and recent_mbps is not None
            and recent_mbps > 0.0
        ):
            recovered = telemetry
            break

    if recovered is None:
        problems.append(
            "no recovered fresh rendered-video telemetry was observed"
        )
    else:
        details.append(
            "fresh post-cycle video telemetry recovered"
        )

    measurements.update(
        {
            "pre_recent_mbps": (
                receiver_before.get(
                    "recent_mbps"
                )
            ),
            "pre_recent_fps": (
                receiver_before.get(
                    "recent_fps"
                )
            ),
            "pre_queue_depth": (
                decoder_before.get(
                    "queue_depth"
                )
            ),
            "host_ffmpeg_spawn_ms": (
                video_cycle.get(
                    "ffmpeg_spawn_ms"
                )
            ),
            "host_first_rtp_resume_ms": (
                video_cycle.get(
                    "first_rtp_resume_ms"
                )
            ),
            "host_verified_ms": (
                video_cycle.get(
                    "host_verified_ms"
                )
            ),
            "fec_rtp_packets_delta_during_cycle": (
                fec_cycle.get(
                    "rtp_packets_delta"
                )
            ),
            "fec_send_errors_delta_during_cycle": (
                fec_cycle.get(
                    "send_errors_delta"
                )
            ),
            "audio_packets_sent_delta_during_cycle": (
                audio_cycle.get(
                    "packets_sent_delta"
                )
            ),
            "audio_send_errors_delta_during_cycle": (
                audio_cycle.get(
                    "send_errors_delta"
                )
            ),
            "controller_packets_delta_during_cycle": (
                controller_cycle.get(
                    "packets_received_delta"
                )
            ),
            "controller_bad_packets_delta_during_cycle": (
                controller_cycle.get(
                    "bad_packets_delta"
                )
            ),
            "post_sample_count": len(
                samples
            ),
        }
    )

    if recovered is not None:
        recovered_receiver = _dict(
            recovered.get(
                "receiver"
            )
        )
        recovered_decoder = _dict(
            recovered.get(
                "decoder"
            )
        )
        measurements.update(
            {
                "recovered_recent_mbps": (
                    recovered_receiver.get(
                        "recent_mbps"
                    )
                ),
                "recovered_recent_fps": (
                    recovered_receiver.get(
                        "recent_fps"
                    )
                ),
                "recovered_waiting_for_idr": (
                    recovered_receiver.get(
                        "waiting_for_idr"
                    )
                ),
                "recovered_queue_depth": (
                    recovered_decoder.get(
                        "queue_depth"
                    )
                ),
                "recovered_output_gap_ms": (
                    _dict(
                        recovered.get(
                            "latency"
                        )
                    ).get(
                        "output_gap_ms"
                    )
                ),
            }
        )

    state = {
        "schema": STATE_SCHEMA,
        "trigger_unix_ns": (
            trigger_unix_ns
        ),
        "decoder_files_before": (
            decoder_before_files
        ),
        "cycle": cycle,
        "telemetry_before": (
            telemetry_before
        ),
        "telemetry_after": samples,
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
            "same-bitrate video-only cycle invoked",
            "FEC relay restart requested: NO",
            "process-audio restart requested: NO",
            "controller restart requested: NO",
            "session-end decoder report still required",
        ]
    )

    result = (
        "C3_ACTUATOR_CYCLE_TRIGGERED"
        if not problems
        else "C3_ACTUATOR_CYCLE_TRIGGERED_WITH_FINDINGS"
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
                "C3_ACTUATOR_FINALIZE_BLOCKED"
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
            "C3 actuator trigger state is invalid"
        )

    before = set(
        state.get(
            "decoder_files_before",
            [],
        )
    )

    candidates = [
        path
        for path in DECODER_ROOT.glob(
            "native_decoder_*.json"
        )
        if (
            path.is_file()
            and path.name not in before
        )
    ] if DECODER_ROOT.is_dir() else []

    if not candidates:
        _write(
            result=(
                "C3_ACTUATOR_FINALIZE_NEEDS_SESSION_END"
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
        _dict(document).get(
            "report"
        )
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
        "session_duration_ms": (
            report.get(
                "duration_ms"
            )
        ),
        "sequence_resyncs": (
            video.get(
                "sequence_resyncs"
            )
        ),
        "ssrc_changes": (
            video.get(
                "ssrc_changes"
            )
        ),
        "packets_dropped_waiting_for_idr": (
            video.get(
                "packets_dropped_waiting_for_idr"
            )
        ),
        "resync_to_idr_ms": (
            video.get(
                "resync_to_idr_ms"
            )
        ),
        "max_resync_to_idr_ms": (
            video.get(
                "max_resync_to_idr_ms"
            )
        ),
        "waiting_for_idr_at_end": (
            video.get(
                "waiting_for_idr"
            )
        ),
        "idr_frames": (
            video.get(
                "idr_frames"
            )
        ),
        "lost_packets": (
            video.get(
                "lost_packets"
            )
        ),
        "fec_recovered_packets": (
            video.get(
                "fec_recovered_packets"
            )
        ),
        "fec_unrecoverable_groups": (
            video.get(
                "fec_unrecoverable_groups"
            )
        ),
        "decoder_rendered_frames": (
            decoder.get(
                "rendered_frames"
            )
        ),
        "decoder_dropped_frames": (
            decoder.get(
                "dropped_frames"
            )
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
        "audio_packets": (
            audio.get(
                "packets"
            )
        ),
        "audio_lost_packets": (
            audio.get(
                "lost_packets"
            )
        ),
        "audio_write_errors": (
            audio.get(
                "write_errors"
            )
        ),
        "audio_underruns": (
            audio.get(
                "underruns"
            )
        ),
        "controller_packets_sent": (
            controller.get(
                "packets_sent"
            )
        ),
        "controller_send_errors": (
            controller.get(
                "send_errors"
            )
        ),
    }

    problems: list[str] = []

    if int(
        video.get(
            "sequence_resyncs",
            0,
        )
        or 0
    ) < 1:
        problems.append(
            "no receiver sequence resync was recorded"
        )

    if (
        video.get(
            "waiting_for_idr"
        )
        is not False
    ):
        problems.append(
            "receiver was still waiting for IDR at session end"
        )

    if int(
        video.get(
            "idr_frames",
            0,
        )
        or 0
    ) <= 0:
        problems.append(
            "no IDR frame was recorded"
        )

    if int(
        decoder.get(
            "rendered_frames",
            0,
        )
        or 0
    ) <= 0:
        problems.append(
            "decoder rendered no frames"
        )

    if int(
        audio.get(
            "write_errors",
            0,
        )
        or 0
    ) != 0:
        problems.append(
            "audio write errors were recorded"
        )

    if int(
        controller.get(
            "send_errors",
            0,
        )
        or 0
    ) != 0:
        problems.append(
            "controller send errors were recorded"
        )

    trigger_problems = (
        state.get(
            "trigger_problems",
            []
        )
    )
    if isinstance(
        trigger_problems,
        list,
    ):
        problems.extend(
            str(item)
            for item in trigger_problems
        )

    details = [
        "host same-bitrate video cycle evidence loaded",
        "normal Android decoder-session report loaded",
        "manual gameplay regression result must be supplied separately",
        "no interruption threshold is classified by this probe",
    ]

    result = (
        "C3_ACTUATOR_CONTINUITY_EVIDENCE_CAPTURED"
        if not problems
        else "C3_ACTUATOR_CONTINUITY_EVIDENCE_CAPTURED_WITH_FINDINGS"
    )

    final_payload = {
        "state": state,
        "decoder_session_log": (
            latest.as_posix()
        ),
        "decoder_session_report": (
            report
        ),
    }

    _write(
        result=result,
        details=details,
        measurements=measurements,
        problems=problems,
        payload=final_payload,
    )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "PrivyHub C3 same-bitrate actuator continuity probe"
        )
    )
    parser.add_argument(
        "--finalize",
        action="store_true",
        help=(
            "Consume the new decoder-session report after normal End."
        ),
    )
    args = parser.parse_args()

    if args.finalize:
        return _finalize()

    return _trigger()


if __name__ == "__main__":
    raise SystemExit(main())
