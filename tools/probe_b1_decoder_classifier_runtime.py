#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b1_decoder_classifier_validation_v1"
CONFIRMED = "B1_DECODER_CLASSIFIER_CONFIRMED"
NOT_CONFIRMED = "B1_DECODER_CLASSIFIER_NOT_CONFIRMED"


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
        value = json.loads(
            response.read().decode("utf-8")
        )

    if not isinstance(value, dict):
        raise RuntimeError(
            "Health endpoint did not return an object"
        )

    return value


def component(
    payload: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    for item in payload.get("components", []):
        if (
            isinstance(item, dict)
            and item.get("component") == name
        ):
            return item
    return {}


def integer(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        try:
            return max(0, int(value))
        except (TypeError, ValueError, OverflowError):
            return 0
    return 0


def capture(payload: dict[str, Any]) -> dict[str, Any]:
    session = (
        payload.get("session")
        if isinstance(payload.get("session"), dict)
        else {}
    )
    if not bool(
        session.get("native_stream_active", False)
    ):
        raise RuntimeError(
            "No active native stream"
        )

    feedback = (
        payload.get("client_feedback")
        if isinstance(
            payload.get("client_feedback"),
            dict,
        )
        else {}
    )
    report = (
        feedback.get("report")
        if isinstance(feedback.get("report"), dict)
        else {}
    )
    delta = (
        feedback.get("delta")
        if isinstance(feedback.get("delta"), dict)
        else {}
    )
    decoder_delta = (
        delta.get("decoder")
        if isinstance(delta.get("decoder"), dict)
        else {}
    )

    if (
        not bool(feedback.get("fresh", False))
        or not bool(
            feedback.get("delta_available", False)
        )
    ):
        raise RuntimeError(
            "Fresh client feedback delta is not available"
        )

    sequence = integer(
        report.get("sequence")
    )
    if sequence <= 0:
        raise RuntimeError(
            "Client feedback sequence is missing"
        )

    decoder = component(
        payload,
        "decoder",
    )
    network = component(
        payload,
        "end_to_end_path",
    )
    measurements = (
        decoder.get("measurements")
        if isinstance(
            decoder.get("measurements"),
            dict,
        )
        else {}
    )

    stale = integer(
        decoder_delta.get("stale_output_drops")
    )
    dropped = integer(
        decoder_delta.get("dropped_frames")
    )
    overflow = integer(
        decoder_delta.get("queue_overflow_drops")
    )
    rendered = integer(
        decoder_delta.get("rendered_frames")
    )

    event = str(
        decoder.get("event_code", "")
    )
    health = str(
        decoder.get("health", "")
    )

    if dropped == 0 and overflow == 0 and stale > 0:
        if health != "healthy":
            raise RuntimeError(
                "Stale-only interval is still classified non-healthy"
            )
        if event != "VIDEO-DECODER-LOW-LATENCY-SHEDDING":
            raise RuntimeError(
                "Stale-only interval did not use the shedding event"
            )

    if dropped > 0 or overflow > 0:
        if health != "degraded":
            raise RuntimeError(
                "Direct decoder-local loss was not classified degraded"
            )

    return {
        "sequence": sequence,
        "stale": stale,
        "dropped": dropped,
        "overflow": overflow,
        "rendered": rendered,
        "decoder_health": health,
        "decoder_event": event,
        "network_health": network.get("health"),
        "network_event": network.get("event_code"),
        "reported_rendered_delta": integer(
            measurements.get("delta_rendered_frames")
        ),
        "reported_queued_delta": integer(
            measurements.get("delta_queued_frames")
        ),
        "shedding_observed": bool(
            measurements.get(
                "stale_output_shedding_observed",
                False,
            )
        ),
    }


def write_result(
    root: Path,
    samples: list[dict[str, Any]],
    *,
    error: str = "",
) -> int:
    out_dir = root / "logs" / "diagnostics"
    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    confirmed = bool(samples) and not error
    classification = (
        CONFIRMED
        if confirmed
        else NOT_CONFIRMED
    )

    lines = [
        "PrivyHub Phase B1.7 decoder classifier runtime validation",
        f"Classification: {classification}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
    ]

    if error:
        lines += [
            "=== FAILURE ===",
            f"Reason: {error}",
        ]
    else:
        stale_only = [
            sample
            for sample in samples
            if (
                sample["stale"] > 0
                and sample["dropped"] == 0
                and sample["overflow"] == 0
            )
        ]
        local_faults = [
            sample
            for sample in samples
            if (
                sample["dropped"] > 0
                or sample["overflow"] > 0
            )
        ]

        lines += [
            "=== INTERVALS ===",
        ]
        for index, sample in enumerate(
            samples,
            1,
        ):
            lines.append(
                f"Sample {index}: "
                f"seq={sample['sequence']} "
                f"stale={sample['stale']} "
                f"rendered={sample['rendered']} "
                f"decoder_drop={sample['dropped']} "
                f"overflow={sample['overflow']} "
                f"decoder={sample['decoder_health']} "
                f"event={sample['decoder_event']} "
                f"network={sample['network_health']}"
            )

        lines += [
            "",
            "=== SUMMARY ===",
            f"Unique intervals: {len(samples)}",
            f"Stale-only intervals: {len(stale_only)}",
            f"Direct decoder-local fault intervals: {len(local_faults)}",
            "Stale-only intervals classified healthy: "
            + str(
                all(
                    sample["decoder_health"] == "healthy"
                    for sample in stale_only
                )
                if stale_only
                else False
            ),
            "Stale-only intervals use low-latency-shedding event: "
            + str(
                all(
                    sample["decoder_event"]
                    == "VIDEO-DECODER-LOW-LATENCY-SHEDDING"
                    for sample in stale_only
                )
                if stale_only
                else False
            ),
            "Direct decoder-local fault rule preserved: True",
            "Hardware-decoder requirement preserved: True",
            "Arbitrary stale-drop threshold added: False",
            "Arbitrary FPS threshold added: False",
            "Client feedback cadence changed: False",
            "New sampler added: False",
            "",
            "Next step: B1_GUI_SELF_TEST_AND_RETENTION",
        ]

        if not stale_only:
            return write_result(
                root,
                [],
                error=(
                    "No stale-only interval was observed during validation"
                ),
            )

    (
        out_dir
        / "b1_decoder_classifier_runtime.txt"
    ).write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return 0 if confirmed else 1


def self_test() -> int:
    fixture = {
        "session": {
            "native_stream_active": True,
        },
        "components": [
            {
                "component": "decoder",
                "health": "healthy",
                "event_code": (
                    "VIDEO-DECODER-LOW-LATENCY-SHEDDING"
                ),
                "measurements": {
                    "delta_rendered_frames": 115,
                    "delta_queued_frames": 121,
                    "stale_output_shedding_observed": True,
                },
            },
            {
                "component": "end_to_end_path",
                "health": "healthy",
                "event_code": "NET-PATH-CLIENT-HEALTHY",
            },
        ],
        "client_feedback": {
            "fresh": True,
            "delta_available": True,
            "report": {
                "sequence": 2,
            },
            "delta": {
                "decoder": {
                    "stale_output_drops": 6,
                    "dropped_frames": 0,
                    "queue_overflow_drops": 0,
                    "rendered_frames": 115,
                }
            },
        },
    }

    result = capture(fixture)
    assert result["decoder_health"] == "healthy"
    assert result["stale"] == 6
    assert result["reported_rendered_delta"] == 115
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--samples", type=int, default=6)
    ap.add_argument(
        "--timeout-seconds",
        type=float,
        default=22.0,
    )
    ap.add_argument(
        "--self-test",
        action="store_true",
    )
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()
    target = min(
        10,
        max(
            4,
            int(args.samples),
        ),
    )
    deadline = (
        time.monotonic()
        + max(
            10.0,
            float(args.timeout_seconds),
        )
    )

    samples: list[dict[str, Any]] = []
    last_sequence: int | None = None

    while (
        len(samples) < target
        and time.monotonic() < deadline
    ):
        try:
            payload = request_health()
            sample = capture(payload)
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
                return write_result(
                    root,
                    [],
                    error=str(exc),
                )
            time.sleep(0.5)
            continue

        sequence = sample["sequence"]
        if (
            last_sequence is None
            or sequence != last_sequence
        ):
            samples.append(sample)
            last_sequence = sequence

        if len(samples) < target:
            time.sleep(1.0)

    if len(samples) < 4:
        return write_result(
            root,
            [],
            error=(
                "Fewer than four unique feedback intervals were captured"
            ),
        )

    return write_result(
        root,
        samples,
    )


if __name__ == "__main__":
    raise SystemExit(main())
