#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any


CONTROL_BASE = "http://127.0.0.1:8765"
PROFILE_ID = "native_game_720p60_reference"
REFERENCE_KBPS = 7000
TARGET_KBPS = 6000

TEXT_LOG = Path(
    "logs/streaming/c3_fixed_6000_characterization.txt"
)
JSON_LOG = Path(
    "logs/streaming/c3_fixed_6000_characterization.json"
)
STATE_PATH = Path(
    "logs/streaming/c3_fixed_6000_characterization_state.json"
)
DECODER_ROOT = Path(
    "logs/games/decoder_sessions"
)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _request_json(
    path: str,
    *,
    method: str = "GET",
    timeout: float = 8.0,
) -> dict[str, Any]:
    request = urllib.request.Request(
        CONTROL_BASE + path,
        data=b"" if method == "POST" else None,
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
            f"Companion request failed with HTTP {exc.code}: "
            + detail[:500]
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            "Companion request failed: "
            + type(exc).__name__
        ) from exc

    if not isinstance(payload, dict):
        raise RuntimeError(
            "Companion response was not an object"
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


def _series(
    samples: list[dict[str, Any]],
    section: str,
    key: str,
) -> list[float]:
    values: list[float] = []
    for sample in samples:
        value = _number(
            _dict(
                sample.get(section)
            ).get(key)
        )
        if value is not None:
            values.append(value)
    return values


def _summary(
    values: list[float],
) -> dict[str, float] | None:
    if not values:
        return None
    return {
        "min": round(min(values), 6),
        "median": round(
            statistics.median(values),
            6,
        ),
        "max": round(max(values), 6),
    }


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
        "PrivyHub C3 fixed 6000 kbps characterization",
        f"Result: {result}",
        "",
        "Privacy:",
        "- Network addresses printed: NO",
        "- Endpoint identity persisted: NO",
        "",
        "Details:",
        *(
            [f"- {x}" for x in details]
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
            [f"- {x}" for x in problems]
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


def _start() -> int:
    problems: list[str] = []
    details: list[str] = []
    measurements: dict[str, Any] = {}

    status_before = _request_json(
        "/plugins/games/native-stream-status"
    )
    telemetry_before = _request_json(
        "/diagnostics/stream-telemetry"
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

    if status_before.get(
        "profile_id"
    ) != PROFILE_ID:
        problems.append(
            "reference profile is not active"
        )

    if int(
        status_before.get(
            "bitrate_kbps",
            0,
        )
        or 0
    ) != REFERENCE_KBPS:
        problems.append(
            "characterization must begin at 7000 kbps"
        )

    profile = _dict(
        status_before.get("profile")
    )
    invariants = {
        "width": 1280,
        "height": 720,
        "fps": 60,
        "gop_frames": 15,
        "bframes": 0,
        "fec_group_size": 8,
    }
    for key, expected in invariants.items():
        source = (
            profile
            if key == "bframes"
            else status_before
        )
        if int(
            source.get(
                key,
                -1,
            )
            or 0
        ) != expected:
            problems.append(
                f"reference invariant mismatch: {key}"
            )

    if not bool(
        _dict(
            status_before.get("fec")
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
            status_before.get("audio")
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
            status_before.get("controller")
        ).get(
            "active",
            False,
        )
    ):
        problems.append(
            "controller bridge is not active"
        )

    if not bool(
        telemetry_before.get(
            "available",
            False,
        )
    ) or not bool(
        telemetry_before.get(
            "fresh",
            False,
        )
    ):
        problems.append(
            "C2 stream telemetry is not fresh before characterization"
        )

    pre_elapsed = int(
        telemetry_before.get(
            "session_elapsed_ms",
            0,
        )
        or 0
    )

    if problems:
        _write(
            result="C3_FIXED_6000_START_BLOCKED",
            details=details,
            measurements=measurements,
            problems=problems,
            payload={},
        )
        return 2

    decoder_before = _decoder_files()

    cycle = _request_json(
        "/plugins/games/c3-fixed-bitrate-6000-cycle",
        method="POST",
        timeout=12.0,
    )

    if (
        cycle.get("schema")
        != "privyhub_c3_fixed_bitrate_cycle_v1"
        or not bool(cycle.get("ok", False))
        or int(
            cycle.get(
                "target_bitrate_kbps",
                0,
            )
            or 0
        ) != TARGET_KBPS
    ):
        problems.append(
            "6000 kbps actuator cycle did not return expected schema"
        )

    status_after = _request_json(
        "/plugins/games/native-stream-status"
    )

    if int(
        status_after.get(
            "bitrate_kbps",
            0,
        )
        or 0
    ) != TARGET_KBPS:
        problems.append(
            "native status does not report 6000 kbps after cycle"
        )

    if int(
        status_after.get(
            "source_bitrate_kbps",
            0,
        )
        or 0
    ) != TARGET_KBPS:
        problems.append(
            "native source bitrate does not report 6000 kbps"
        )

    if int(
        status_after.get(
            "reference_bitrate_kbps",
            0,
        )
        or 0
    ) != REFERENCE_KBPS:
        problems.append(
            "reference bitrate was not preserved as 7000 kbps"
        )

    for key, expected in {
        "width": 1280,
        "height": 720,
        "fps": 60,
        "gop_frames": 15,
        "fec_group_size": 8,
    }.items():
        if int(
            status_after.get(
                key,
                -1,
            )
            or 0
        ) != expected:
            problems.append(
                f"post-cycle invariant mismatch: {key}"
            )

    samples: list[dict[str, Any]] = []
    seen: set[int] = set()
    deadline = time.monotonic() + 16.0

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
            elapsed > pre_elapsed
            and elapsed not in seen
        ):
            seen.add(elapsed)
            samples.append(telemetry)

        if len(samples) >= 6:
            break

        time.sleep(0.5)

    fresh_samples = [
        sample
        for sample in samples
        if bool(sample.get("available", False))
        and bool(sample.get("fresh", False))
    ]

    if len(fresh_samples) < 3:
        problems.append(
            "fewer than three fresh post-6000 telemetry intervals captured"
        )

    waiting_values = [
        _dict(sample.get("receiver")).get(
            "waiting_for_idr"
        )
        for sample in fresh_samples
    ]
    if not any(
        value is False
        for value in waiting_values
    ):
        problems.append(
            "receiver did not return to non-waiting-for-IDR state"
        )

    receiver_mbps = _series(
        fresh_samples,
        "receiver",
        "recent_mbps",
    )
    receiver_fps = _series(
        fresh_samples,
        "receiver",
        "recent_fps",
    )
    jitter = _series(
        fresh_samples,
        "receiver",
        "interarrival_jitter_ms",
    )
    queue = _series(
        fresh_samples,
        "decoder",
        "queue_depth",
    )
    rx_decode = _series(
        fresh_samples,
        "latency",
        "receive_to_decode_ms",
    )
    output_gap = _series(
        fresh_samples,
        "latency",
        "output_gap_ms",
    )

    cycle_video = _dict(
        cycle.get("video")
    )
    cycle_fec = _dict(
        cycle.get("fec")
    )
    cycle_audio = _dict(
        cycle.get("audio")
    )
    cycle_controller = _dict(
        cycle.get("controller")
    )

    measurements.update(
        {
            "target_bitrate_kbps": TARGET_KBPS,
            "post_status_bitrate_kbps": status_after.get(
                "bitrate_kbps"
            ),
            "post_status_reference_bitrate_kbps": status_after.get(
                "reference_bitrate_kbps"
            ),
            "host_first_rtp_resume_ms": cycle_video.get(
                "first_rtp_resume_ms"
            ),
            "fresh_sample_count": len(
                fresh_samples
            ),
            "receiver_recent_mbps": _summary(
                receiver_mbps
            ),
            "receiver_recent_fps": _summary(
                receiver_fps
            ),
            "interarrival_jitter_ms": _summary(
                jitter
            ),
            "decoder_queue_depth": _summary(
                queue
            ),
            "receive_to_decode_ms": _summary(
                rx_decode
            ),
            "output_gap_ms": _summary(
                output_gap
            ),
            "cycle_fec_send_errors_delta": cycle_fec.get(
                "send_errors_delta"
            ),
            "cycle_audio_send_errors_delta": cycle_audio.get(
                "send_errors_delta"
            ),
            "cycle_controller_bad_packets_delta": cycle_controller.get(
                "bad_packets_delta"
            ),
        }
    )

    state = {
        "schema": "privyhub_c3_fixed_6000_state_v1",
        "target_bitrate_kbps": TARGET_KBPS,
        "reference_bitrate_kbps": REFERENCE_KBPS,
        "decoder_files_before": decoder_before,
        "cycle": cycle,
        "status_after": status_after,
        "telemetry_samples": samples,
        "start_problems": problems,
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
            "6000 kbps diagnostic candidate activated",
            "resolution/fps/GOP/FEC invariants unchanged",
            "automatic adaptation remains disabled",
            "manual focused play and normal End are still required",
        ]
    )

    _write(
        result=(
            "C3_FIXED_6000_RUNTIME_SAMPLE_CAPTURED"
            if not problems
            else "C3_FIXED_6000_RUNTIME_SAMPLE_CAPTURED_WITH_FINDINGS"
        ),
        details=details,
        measurements=measurements,
        problems=problems,
        payload=state,
    )

    return 0


def _finalize() -> int:
    if not STATE_PATH.is_file():
        _write(
            result="C3_FIXED_6000_FINALIZE_BLOCKED",
            details=[],
            measurements={},
            problems=[
                "6000 characterization state is missing"
            ],
            payload={},
        )
        return 2

    state = json.loads(
        STATE_PATH.read_text(
            encoding="utf-8"
        )
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
            result="C3_FIXED_6000_FINALIZE_NEEDS_SESSION_END",
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
        key=lambda path: path.stat().st_mtime_ns,
    )

    document = json.loads(
        latest.read_text(
            encoding="utf-8"
        )
    )
    report = _dict(
        _dict(document).get("report")
    )
    video = _dict(report.get("video"))
    decoder = _dict(report.get("decoder"))
    audio = _dict(report.get("audio"))
    controller = _dict(
        report.get("controller")
    )

    measurements = {
        "target_bitrate_kbps": TARGET_KBPS,
        "session_duration_ms": report.get(
            "duration_ms"
        ),
        "sequence_resyncs": video.get(
            "sequence_resyncs"
        ),
        "ssrc_changes": video.get(
            "ssrc_changes"
        ),
        "packets_dropped_waiting_for_idr": video.get(
            "packets_dropped_waiting_for_idr"
        ),
        "resync_to_idr_ms": video.get(
            "resync_to_idr_ms"
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
        "decoder_queue_overflow_drops": decoder.get(
            "queue_overflow_drops"
        ),
        "decoder_max_output_gap_ms": decoder.get(
            "max_output_gap_ms"
        ),
        "decoder_max_rx_to_decode_ms": decoder.get(
            "max_rx_to_decode_ms"
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

    problems: list[str] = []

    if video.get(
        "waiting_for_idr"
    ) is not False:
        problems.append(
            "receiver was still waiting for IDR at session end"
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
        decoder.get(
            "dropped_frames",
            0,
        )
        or 0
    ) != 0:
        problems.append(
            "decoder dropped frames were recorded"
        )

    if int(
        decoder.get(
            "queue_overflow_drops",
            0,
        )
        or 0
    ) != 0:
        problems.append(
            "decoder queue-overflow drops were recorded"
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

    start_problems = state.get(
        "start_problems",
        [],
    )
    if isinstance(
        start_problems,
        list,
    ):
        problems.extend(
            str(x)
            for x in start_problems
        )

    details = [
        "6000 kbps post-cycle telemetry and decoder-session evidence captured",
        "whole-session loss/FEC/audio totals are preserved as raw measurements",
        "no visual-quality acceptance threshold is encoded by this probe",
        "manual focused-play quality observation is required separately",
    ]

    payload = {
        "state": state,
        "decoder_session_log": latest.as_posix(),
        "decoder_session_report": report,
    }

    _write(
        result=(
            "C3_FIXED_6000_EVIDENCE_CAPTURED"
            if not problems
            else "C3_FIXED_6000_EVIDENCE_CAPTURED_WITH_FINDINGS"
        ),
        details=details,
        measurements=measurements,
        problems=problems,
        payload=payload,
    )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "PrivyHub C3 fixed 6000 kbps characterization"
        )
    )
    parser.add_argument(
        "--finalize",
        action="store_true",
        help=(
            "Consume the decoder-session report after normal End."
        ),
    )
    args = parser.parse_args()

    if args.finalize:
        return _finalize()

    return _start()


if __name__ == "__main__":
    raise SystemExit(main())
