#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
import time
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b1_decoder_stale_semantics_v1"
CLASSIFICATION = "B1_DECODER_STALE_SEMANTICS_CAPTURED"
NOT_CAPTURED = "B1_DECODER_STALE_SEMANTICS_NOT_CAPTURED"


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
            "Health endpoint did not return an object"
        )

    return payload


def object_value(
    value: Any,
) -> dict[str, Any]:
    return (
        value
        if isinstance(
            value,
            dict,
        )
        else {}
    )


def number(
    value: Any,
) -> float | None:
    if isinstance(
        value,
        bool,
    ):
        return None

    if isinstance(
        value,
        (int, float),
    ):
        result = float(
            value
        )
        if math.isfinite(
            result
        ):
            return result

    return None


def integer(
    value: Any,
) -> int | None:
    numeric = number(
        value
    )
    if numeric is None:
        return None
    return int(
        numeric
    )


def component(
    payload: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    for item in payload.get(
        "components",
        [],
    ):
        if (
            isinstance(
                item,
                dict,
            )
            and item.get(
                "component"
            )
            == name
        ):
            return item

    return {}


def capture_unique_sample(
    payload: dict[str, Any],
) -> dict[str, Any]:
    session = object_value(
        payload.get(
            "session"
        )
    )

    if not bool(
        session.get(
            "native_stream_active",
            False,
        )
    ):
        raise RuntimeError(
            "No active native stream"
        )

    feedback = object_value(
        payload.get(
            "client_feedback"
        )
    )
    report = object_value(
        feedback.get(
            "report"
        )
    )
    delta = object_value(
        feedback.get(
            "delta"
        )
    )

    if not bool(
        feedback.get(
            "available",
            False,
        )
    ):
        raise RuntimeError(
            "Client feedback unavailable"
        )

    if not bool(
        feedback.get(
            "fresh",
            False,
        )
    ):
        raise RuntimeError(
            "Client feedback stale"
        )

    if not bool(
        feedback.get(
            "delta_available",
            False,
        )
    ):
        raise RuntimeError(
            "Client feedback delta unavailable"
        )

    if (
        report.get(
            "schema"
        )
        != "privyhub_client_health_v1"
    ):
        raise RuntimeError(
            "Client health schema mismatch"
        )

    sequence = integer(
        report.get(
            "sequence"
        )
    )
    interval_ms = integer(
        report.get(
            "interval_ms"
        )
    )

    if sequence is None:
        raise RuntimeError(
            "Client feedback sequence missing"
        )

    if (
        interval_ms is None
        or interval_ms <= 0
    ):
        raise RuntimeError(
            "Client feedback interval missing"
        )

    video = object_value(
        report.get(
            "video"
        )
    )
    decoder = object_value(
        report.get(
            "decoder"
        )
    )
    video_delta = object_value(
        delta.get(
            "video"
        )
    )
    decoder_delta = object_value(
        delta.get(
            "decoder"
        )
    )

    native_stream = component(
        payload,
        "native_stream",
    )
    native_measurements = object_value(
        native_stream.get(
            "measurements"
        )
    )

    network = component(
        payload,
        "end_to_end_path",
    )
    decoder_health = component(
        payload,
        "decoder",
    )

    target_fps = number(
        native_measurements.get(
            "fps"
        )
    )
    receive_fps = number(
        video.get(
            "recent_fps"
        )
    )
    receive_mbps = number(
        video.get(
            "recent_mbps"
        )
    )

    rendered_delta = integer(
        decoder_delta.get(
            "rendered_frames"
        )
    )
    stale_delta = integer(
        decoder_delta.get(
            "stale_output_drops"
        )
    )
    decoder_drop_delta = integer(
        decoder_delta.get(
            "dropped_frames"
        )
    )
    overflow_delta = integer(
        decoder_delta.get(
            "queue_overflow_drops"
        )
    )
    queued_delta = integer(
        decoder_delta.get(
            "queued_frames"
        )
    )

    rendered_fps_estimate = None
    if (
        rendered_delta is not None
        and interval_ms > 0
    ):
        rendered_fps_estimate = (
            rendered_delta
            * 1000.0
            / interval_ms
        )

    stale_share_of_outputs = None
    if (
        rendered_delta is not None
        and stale_delta is not None
    ):
        outputs = (
            rendered_delta
            + stale_delta
        )
        if outputs > 0:
            stale_share_of_outputs = (
                stale_delta
                / outputs
            )

    receive_target_ratio = None
    if (
        receive_fps is not None
        and target_fps is not None
        and target_fps > 0.0
    ):
        receive_target_ratio = (
            receive_fps
            / target_fps
        )

    render_target_ratio = None
    if (
        rendered_fps_estimate is not None
        and target_fps is not None
        and target_fps > 0.0
    ):
        render_target_ratio = (
            rendered_fps_estimate
            / target_fps
        )

    return {
        "sequence": sequence,
        "interval_ms": interval_ms,
        "feedback_age_ms": integer(
            feedback.get(
                "age_ms"
            )
        ),
        "payload_bytes": integer(
            feedback.get(
                "payload_bytes"
            )
        ),
        "target_fps": target_fps,
        "receive_fps": receive_fps,
        "receive_mbps": receive_mbps,
        "receive_target_ratio": receive_target_ratio,
        "queued_delta": queued_delta,
        "rendered_delta": rendered_delta,
        "rendered_fps_estimate": (
            rendered_fps_estimate
        ),
        "render_target_ratio": (
            render_target_ratio
        ),
        "stale_delta": stale_delta,
        "stale_share_of_outputs": (
            stale_share_of_outputs
        ),
        "decoder_drop_delta": (
            decoder_drop_delta
        ),
        "overflow_delta": (
            overflow_delta
        ),
        "queue_depth": integer(
            decoder.get(
                "queue_depth"
            )
        ),
        "rx_to_decode_ms": integer(
            decoder.get(
                "latest_rx_to_decode_ms"
            )
        ),
        "output_gap_ms": integer(
            decoder.get(
                "latest_output_gap_ms"
            )
        ),
        "hardware_accelerated": (
            decoder.get(
                "hardware_accelerated"
            )
        ),
        "network_health": (
            network.get(
                "health"
            )
        ),
        "network_event": (
            network.get(
                "event_code"
            )
        ),
        "decoder_health": (
            decoder_health.get(
                "health"
            )
        ),
        "decoder_event": (
            decoder_health.get(
                "event_code"
            )
        ),
        "fec_recovered_delta": integer(
            video_delta.get(
                "fec_recovered_packets"
            )
        ),
        "fec_unrecoverable_delta": integer(
            video_delta.get(
                "fec_unrecoverable_groups"
            )
        ),
        "network_dropped_frame_delta": integer(
            video_delta.get(
                "dropped_frames"
            )
        ),
        "waiting_for_idr": (
            video.get(
                "waiting_for_idr"
            )
        ),
    }


def finite_values(
    samples: list[dict[str, Any]],
    key: str,
) -> list[float]:
    result = []

    for sample in samples:
        value = number(
            sample.get(
                key
            )
        )
        if value is not None:
            result.append(
                value
            )

    return result


def int_sum(
    samples: list[dict[str, Any]],
    key: str,
) -> int:
    total = 0

    for sample in samples:
        value = integer(
            sample.get(
                key
            )
        )
        if value is not None:
            total += value

    return total


def max_or_none(
    values: list[float],
) -> float | None:
    return (
        max(
            values
        )
        if values
        else None
    )


def min_or_none(
    values: list[float],
) -> float | None:
    return (
        min(
            values
        )
        if values
        else None
    )


def median_or_none(
    values: list[float],
) -> float | None:
    return (
        statistics.median(
            values
        )
        if values
        else None
    )


def summarize(
    samples: list[dict[str, Any]],
) -> dict[str, Any]:
    receive_fps = finite_values(
        samples,
        "receive_fps",
    )
    render_fps = finite_values(
        samples,
        "rendered_fps_estimate",
    )
    receive_ratio = finite_values(
        samples,
        "receive_target_ratio",
    )
    render_ratio = finite_values(
        samples,
        "render_target_ratio",
    )
    stale_share = finite_values(
        samples,
        "stale_share_of_outputs",
    )
    output_gap = finite_values(
        samples,
        "output_gap_ms",
    )
    rx_decode = finite_values(
        samples,
        "rx_to_decode_ms",
    )
    queue_depth = finite_values(
        samples,
        "queue_depth",
    )

    stale_intervals = sum(
        1
        for sample in samples
        if (
            integer(
                sample.get(
                    "stale_delta"
                )
            )
            or 0
        )
        > 0
    )

    degraded_intervals = sum(
        1
        for sample in samples
        if sample.get(
            "decoder_health"
        )
        == "degraded"
    )

    network_degraded_intervals = sum(
        1
        for sample in samples
        if sample.get(
            "network_health"
        )
        not in (
            "healthy",
            "idle",
        )
    )

    return {
        "sample_count": len(
            samples
        ),
        "stale_intervals": (
            stale_intervals
        ),
        "decoder_degraded_intervals": (
            degraded_intervals
        ),
        "network_nonhealthy_intervals": (
            network_degraded_intervals
        ),
        "stale_total": int_sum(
            samples,
            "stale_delta",
        ),
        "rendered_total": int_sum(
            samples,
            "rendered_delta",
        ),
        "decoder_drop_total": int_sum(
            samples,
            "decoder_drop_delta",
        ),
        "overflow_total": int_sum(
            samples,
            "overflow_delta",
        ),
        "fec_unrecoverable_total": int_sum(
            samples,
            "fec_unrecoverable_delta",
        ),
        "network_dropped_frame_total": int_sum(
            samples,
            "network_dropped_frame_delta",
        ),
        "receive_fps_min": min_or_none(
            receive_fps
        ),
        "receive_fps_median": median_or_none(
            receive_fps
        ),
        "receive_fps_max": max_or_none(
            receive_fps
        ),
        "rendered_fps_min": min_or_none(
            render_fps
        ),
        "rendered_fps_median": median_or_none(
            render_fps
        ),
        "rendered_fps_max": max_or_none(
            render_fps
        ),
        "receive_target_ratio_min": min_or_none(
            receive_ratio
        ),
        "render_target_ratio_min": min_or_none(
            render_ratio
        ),
        "stale_share_max": max_or_none(
            stale_share
        ),
        "output_gap_ms_max": max_or_none(
            output_gap
        ),
        "rx_to_decode_ms_max": max_or_none(
            rx_decode
        ),
        "queue_depth_max": max_or_none(
            queue_depth
        ),
        "waiting_for_idr_intervals": sum(
            1
            for sample in samples
            if sample.get(
                "waiting_for_idr"
            )
            is True
        ),
    }


def fmt(
    value: Any,
    digits: int = 3,
) -> str:
    if value is None:
        return "<unknown>"

    if isinstance(
        value,
        float,
    ):
        return f"{value:.{digits}f}"

    return str(
        value
    )


def format_text(
    samples: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    lines = [
        "PrivyHub Phase B1.6 decoder stale-output semantics audit",
        f"Classification: {CLASSIFICATION}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "Classifier changed by probe: NONE",
        "",
        "=== INTERVAL MEASUREMENTS ===",
    ]

    for index, sample in enumerate(
        samples,
        1,
    ):
        lines.append(
            "Sample "
            f"{index}: "
            f"seq={sample['sequence']} "
            f"age_ms={fmt(sample['feedback_age_ms'])} "
            f"rx_fps={fmt(sample['receive_fps'])} "
            f"render_fps_est={fmt(sample['rendered_fps_estimate'])} "
            f"stale={fmt(sample['stale_delta'])} "
            f"decoder_drop={fmt(sample['decoder_drop_delta'])} "
            f"overflow={fmt(sample['overflow_delta'])} "
            f"queue={fmt(sample['queue_depth'])} "
            f"rx_to_decode_ms={fmt(sample['rx_to_decode_ms'])} "
            f"output_gap_ms={fmt(sample['output_gap_ms'])} "
            f"fec_unrec={fmt(sample['fec_unrecoverable_delta'])} "
            f"net_drop={fmt(sample['network_dropped_frame_delta'])} "
            f"network={sample['network_health']} "
            f"decoder={sample['decoder_health']}"
        )

    lines += [
        "",
        "=== SUMMARY ===",
        f"Unique intervals captured: {summary['sample_count']}",
        f"Intervals with stale drops: {summary['stale_intervals']}",
        f"Intervals classifier marked decoder degraded: {summary['decoder_degraded_intervals']}",
        f"Network non-healthy intervals: {summary['network_nonhealthy_intervals']}",
        f"Stale drops total: {summary['stale_total']}",
        f"Rendered frames total: {summary['rendered_total']}",
        f"Ordinary decoder drops total: {summary['decoder_drop_total']}",
        f"Queue overflow drops total: {summary['overflow_total']}",
        f"FEC unrecoverable groups total: {summary['fec_unrecoverable_total']}",
        f"Network dropped frames total: {summary['network_dropped_frame_total']}",
        "Receive FPS min/median/max: "
        f"{fmt(summary['receive_fps_min'])}/"
        f"{fmt(summary['receive_fps_median'])}/"
        f"{fmt(summary['receive_fps_max'])}",
        "Rendered FPS estimate min/median/max: "
        f"{fmt(summary['rendered_fps_min'])}/"
        f"{fmt(summary['rendered_fps_median'])}/"
        f"{fmt(summary['rendered_fps_max'])}",
        f"Minimum receive/target FPS ratio: {fmt(summary['receive_target_ratio_min'])}",
        f"Minimum render/target FPS ratio: {fmt(summary['render_target_ratio_min'])}",
        f"Maximum stale share of decoder outputs: {fmt(summary['stale_share_max'])}",
        f"Maximum output gap ms: {fmt(summary['output_gap_ms_max'])}",
        f"Maximum RX-to-decode ms: {fmt(summary['rx_to_decode_ms_max'])}",
        f"Maximum decoder queue depth: {fmt(summary['queue_depth_max'])}",
        f"Waiting-for-IDR intervals: {summary['waiting_for_idr_intervals']}",
        "",
        "=== INTERPRETATION BOUNDARY ===",
        "No stale-drop threshold applied: True",
        "No FPS threshold applied: True",
        "No decoder classifier change applied: True",
        "Raw measurements are authoritative over the current classifier.",
        "",
        "Next step: INSPECT_STALE_DROP_PATTERN_THEN_DECIDE_CLASSIFIER_RULE",
    ]

    return "\n".join(
        lines
    ) + "\n"


def self_test() -> int:
    samples = [
        {
            "receive_fps": 60.0,
            "rendered_fps_estimate": 58.0,
            "receive_target_ratio": 1.0,
            "render_target_ratio": 58.0 / 60.0,
            "stale_share_of_outputs": 4.0 / 120.0,
            "output_gap_ms": 17,
            "rx_to_decode_ms": 3,
            "queue_depth": 1,
            "stale_delta": 4,
            "rendered_delta": 116,
            "decoder_drop_delta": 0,
            "overflow_delta": 0,
            "fec_unrecoverable_delta": 0,
            "network_dropped_frame_delta": 0,
            "decoder_health": "degraded",
            "network_health": "healthy",
            "waiting_for_idr": False,
        },
        {
            "receive_fps": 59.8,
            "rendered_fps_estimate": 59.0,
            "receive_target_ratio": 59.8 / 60.0,
            "render_target_ratio": 59.0 / 60.0,
            "stale_share_of_outputs": 2.0 / 120.0,
            "output_gap_ms": 17,
            "rx_to_decode_ms": 2,
            "queue_depth": 1,
            "stale_delta": 2,
            "rendered_delta": 118,
            "decoder_drop_delta": 0,
            "overflow_delta": 0,
            "fec_unrecoverable_delta": 0,
            "network_dropped_frame_delta": 0,
            "decoder_health": "degraded",
            "network_health": "healthy",
            "waiting_for_idr": False,
        },
    ]

    result = summarize(
        samples
    )

    assert result[
        "sample_count"
    ] == 2
    assert result[
        "stale_total"
    ] == 6
    assert result[
        "rendered_total"
    ] == 234
    assert result[
        "decoder_drop_total"
    ] == 0
    assert result[
        "overflow_total"
    ] == 0

    return 0


def write_failure(
    root: Path,
    reason: str,
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

    text = "\n".join(
        [
            "PrivyHub Phase B1.6 decoder stale-output semantics audit",
            f"Classification: {NOT_CAPTURED}",
            f"Schema: {SCHEMA}",
            "Production files modified by probe: NONE",
            "Network addresses collected/logged: NONE",
            "Classifier changed by probe: NONE",
            "",
            "=== FAILURE ===",
            f"Reason: {reason}",
            "",
        ]
    )

    (
        out_dir
        / "b1_decoder_stale_semantics.txt"
    ).write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )

    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        default=".",
    )
    ap.add_argument(
        "--samples",
        type=int,
        default=8,
    )
    ap.add_argument(
        "--timeout-seconds",
        type=float,
        default=28.0,
    )
    ap.add_argument(
        "--self-test",
        action="store_true",
    )
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    root = Path(
        args.root
    ).resolve()
    target_samples = min(
        12,
        max(
            4,
            int(
                args.samples
            ),
        ),
    )

    samples: list[
        dict[str, Any]
    ] = []
    last_sequence: int | None = None
    deadline = (
        time.monotonic()
        + max(
            10.0,
            float(
                args.timeout_seconds
            ),
        )
    )

    while (
        len(
            samples
        )
        < target_samples
        and time.monotonic()
        < deadline
    ):
        try:
            payload = request_health()
            sample = capture_unique_sample(
                payload
            )
        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
            OSError,
            ValueError,
            json.JSONDecodeError,
            RuntimeError,
        ) as exc:
            if not samples:
                return write_failure(
                    root,
                    str(
                        exc
                    ),
                )

            time.sleep(
                0.5
            )
            continue

        sequence = int(
            sample[
                "sequence"
            ]
        )

        if (
            last_sequence is None
            or sequence
            != last_sequence
        ):
            samples.append(
                sample
            )
            last_sequence = (
                sequence
            )

        if len(
            samples
        ) < target_samples:
            time.sleep(
                1.0
            )

    if len(
        samples
    ) < 4:
        return write_failure(
            root,
            "Fewer than four unique client-health intervals were captured",
        )

    summary = summarize(
        samples
    )

    output = {
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
        "classifier_changed_by_probe": (
            "NONE"
        ),
        "samples": samples,
        "summary": summary,
        "interpretation": {
            "stale_drop_threshold_applied": False,
            "fps_threshold_applied": False,
            "classifier_change_applied": False,
            "measurement_priority": (
                "raw_measurements_over_current_classifier"
            ),
        },
    }

    out_dir = (
        root
        / "logs"
        / "diagnostics"
    )
    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        out_dir
        / "b1_decoder_stale_semantics.json"
    ).write_text(
        json.dumps(
            output,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    (
        out_dir
        / "b1_decoder_stale_semantics.txt"
    ).write_text(
        format_text(
            samples,
            summary,
        ),
        encoding="utf-8",
        newline="\n",
    )

    print(
        CLASSIFICATION
    )
    print(
        "Text:",
        out_dir
        / "b1_decoder_stale_semantics.txt",
    )
    print(
        "JSON:",
        out_dir
        / "b1_decoder_stale_semantics.json",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
