#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any


SCHEMA = "privyhub_stream_telemetry_v1"
PROFILE = "native_game_720p60_reference"
URL = "http://127.0.0.1:8765/diagnostics/stream-telemetry"


def get_json() -> dict[str, Any]:
    request = urllib.request.Request(
        URL,
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=2.0) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Telemetry endpoint did not return an object")
    return payload


def number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = root / "logs/streaming/c2_stream_telemetry_runtime.txt"
    jout = root / "logs/streaming/c2_stream_telemetry_runtime.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    samples: list[dict[str, Any]] = []
    error = ""

    deadline = time.monotonic() + 12.0
    while time.monotonic() < deadline:
        try:
            payload = get_json()
            samples.append(payload)

            receiver = payload.get("receiver", {})
            sender = payload.get("sender", {})
            latency = payload.get("latency", {})
            decoder = payload.get("decoder", {})

            ready = (
                payload.get("schema") == SCHEMA
                and payload.get("available") is True
                and payload.get("fresh") is True
                and payload.get("profile_id") == PROFILE
                and payload.get("delta_available") is True
                and number(receiver.get("interarrival_jitter_ms"))
                and number(latency.get("control_round_trip_ms"))
                and sender.get("delta_available") is True
                and number(sender.get("sent_bytes_delta"))
                and number(sender.get("send_calls_delta"))
                and number(sender.get("send_errors_delta"))
                and number(sender.get("send_call_avg_us"))
                and number(sender.get("send_call_max_us"))
                and number(decoder.get("queue_depth"))
                and number(decoder.get("queue_depth_delta"))
            )
            if ready:
                break
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            RuntimeError,
        ) as exc:
            error = f"{type(exc).__name__}: {exc}"

        time.sleep(1.0)

    payload = samples[-1] if samples else {}
    receiver = payload.get("receiver", {}) if isinstance(payload, dict) else {}
    fec = payload.get("fec", {}) if isinstance(payload, dict) else {}
    sender = payload.get("sender", {}) if isinstance(payload, dict) else {}
    latency = payload.get("latency", {}) if isinstance(payload, dict) else {}
    decoder = payload.get("decoder", {}) if isinstance(payload, dict) else {}

    checks = {
        "schema": payload.get("schema") == SCHEMA,
        "available": payload.get("available") is True,
        "fresh": payload.get("fresh") is True,
        "reference_profile": payload.get("profile_id") == PROFILE,
        "client_delta": payload.get("delta_available") is True,
        "jitter_numeric": number(receiver.get("interarrival_jitter_ms")),
        "control_round_trip_numeric": number(
            latency.get("control_round_trip_ms")
        ),
        "sender_delta": sender.get("delta_available") is True,
        "sender_bytes_numeric": number(sender.get("sent_bytes_delta")),
        "sender_calls_numeric": number(sender.get("send_calls_delta")),
        "sender_errors_numeric": number(sender.get("send_errors_delta")),
        "sender_avg_numeric": number(sender.get("send_call_avg_us")),
        "sender_max_numeric": number(sender.get("send_call_max_us")),
        "queue_depth_numeric": number(decoder.get("queue_depth")),
        "queue_depth_delta_numeric": number(
            decoder.get("queue_depth_delta")
        ),
        "no_adaptation_fields": not any(
            key in payload
            for key in (
                "target_bitrate_kbps",
                "selected_bitrate_kbps",
                "adaptation_action",
                "congestion_class",
            )
        ),
    }

    passed = all(checks.values())
    result = (
        "C2_STREAM_TELEMETRY_RUNTIME_PASS"
        if passed
        else "C2_STREAM_TELEMETRY_RUNTIME_INCOMPLETE"
    )

    lines = [
        "PrivyHub C2 stream telemetry runtime validation",
        f"Result: {result}",
        "",
        "Privacy:",
        "- Network addresses printed: NO",
        "- Source/request address identity field expected: NO",
        "",
        "Checks:",
        *[
            f"- {name}: {'PASS' if value else 'FAIL'}"
            for name, value in checks.items()
        ],
        "",
        "Measurements:",
        f"- sample_count: {len(samples)}",
        f"- age_ms: {payload.get('age_ms')}",
        f"- sample_interval_ms: {payload.get('sample_interval_ms')}",
        f"- receiver_recent_mbps: {receiver.get('recent_mbps')}",
        f"- receiver_recent_fps: {receiver.get('recent_fps')}",
        f"- interarrival_jitter_ms: {receiver.get('interarrival_jitter_ms')}",
        f"- lost_packets_delta: {receiver.get('lost_packets_delta')}",
        f"- fec_recovered_packets_delta: {fec.get('recovered_packets_delta')}",
        f"- fec_unrecoverable_groups_delta: {fec.get('unrecoverable_groups_delta')}",
        f"- control_round_trip_ms: {latency.get('control_round_trip_ms')}",
        f"- receive_to_decode_ms: {latency.get('receive_to_decode_ms')}",
        f"- output_gap_ms: {latency.get('output_gap_ms')}",
        f"- queue_depth: {decoder.get('queue_depth')}",
        f"- queue_depth_delta: {decoder.get('queue_depth_delta')}",
        f"- sender_sent_bytes_delta: {sender.get('sent_bytes_delta')}",
        f"- sender_send_calls_delta: {sender.get('send_calls_delta')}",
        f"- sender_send_errors_delta: {sender.get('send_errors_delta')}",
        f"- sender_send_call_avg_us: {sender.get('send_call_avg_us')}",
        f"- sender_send_call_max_us: {sender.get('send_call_max_us')}",
        "",
        "Endpoint/read error:",
        error or "<none>",
        "",
        "Manual regression still required:",
        "- picture",
        "- process audio",
        "- controller input",
        "- Pause/Resume",
        "- Save/Load",
        "- End/teardown",
    ]

    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    jout.write_text(
        json.dumps(
            {
                "result": result,
                "checks": checks,
                "measurements": {
                    "age_ms": payload.get("age_ms"),
                    "sample_interval_ms": payload.get("sample_interval_ms"),
                    "receiver_recent_mbps": receiver.get("recent_mbps"),
                    "receiver_recent_fps": receiver.get("recent_fps"),
                    "interarrival_jitter_ms": receiver.get(
                        "interarrival_jitter_ms"
                    ),
                    "lost_packets_delta": receiver.get("lost_packets_delta"),
                    "fec_recovered_packets_delta": fec.get(
                        "recovered_packets_delta"
                    ),
                    "fec_unrecoverable_groups_delta": fec.get(
                        "unrecoverable_groups_delta"
                    ),
                    "control_round_trip_ms": latency.get(
                        "control_round_trip_ms"
                    ),
                    "receive_to_decode_ms": latency.get(
                        "receive_to_decode_ms"
                    ),
                    "output_gap_ms": latency.get("output_gap_ms"),
                    "queue_depth": decoder.get("queue_depth"),
                    "queue_depth_delta": decoder.get("queue_depth_delta"),
                    "sender_sent_bytes_delta": sender.get("sent_bytes_delta"),
                    "sender_send_calls_delta": sender.get("send_calls_delta"),
                    "sender_send_errors_delta": sender.get("send_errors_delta"),
                    "sender_send_call_avg_us": sender.get(
                        "send_call_avg_us"
                    ),
                    "sender_send_call_max_us": sender.get(
                        "send_call_max_us"
                    ),
                },
                "privacy": (
                    "No network addresses collected or printed; telemetry "
                    "contract must contain no source/request identity field."
                ),
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print("\n".join(lines))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
