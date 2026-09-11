#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any

CONFIRMED = "B1_CLIENT_FEEDBACK_CONFIRMED"
NOT_CONFIRMED = "B1_CLIENT_FEEDBACK_NOT_CONFIRMED"

FORBIDDEN_KEYS = {
    "pid", "port", "local_port", "target_pid", "client_ip",
    "project_root", "media_root", "path", "capture_target", "title", "window",
}
IPV4 = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
MAC = re.compile(
    r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
)


def request_health() -> dict[str, Any]:
    request = urllib.request.Request(
        "http://127.0.0.1:8765/diagnostics/health",
        headers={"Cache-Control": "no-cache"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=3.0) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Health endpoint did not return an object")
    return payload


def component(payload: dict[str, Any], name: str) -> dict[str, Any]:
    for item in payload.get("components", []):
        if isinstance(item, dict) and item.get("component") == name:
            return item
    return {}


def walk(value: Any, *, keys: set[str], strings: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key))
            walk(child, keys=keys, strings=strings)
    elif isinstance(value, list):
        for child in value:
            walk(child, keys=keys, strings=strings)
    elif isinstance(value, str):
        strings.append(value)


def validate(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != "privyhub_diagnostics_health_v1":
        raise RuntimeError("Health schema mismatch")

    session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
    if not bool(session.get("native_stream_active", False)):
        raise RuntimeError("No active native stream; launch a game and rerun")

    feedback = (
        payload.get("client_feedback")
        if isinstance(payload.get("client_feedback"), dict)
        else {}
    )
    report = feedback.get("report") if isinstance(feedback.get("report"), dict) else {}
    delta = feedback.get("delta") if isinstance(feedback.get("delta"), dict) else {}

    if feedback.get("schema") != "privyhub_client_health_store_v1":
        raise RuntimeError("Client feedback store schema mismatch")
    if not bool(feedback.get("available", False)):
        raise RuntimeError("Client feedback is unavailable")
    if not bool(feedback.get("fresh", False)):
        raise RuntimeError("Client feedback is stale")
    if not bool(feedback.get("delta_available", False)):
        raise RuntimeError("Client feedback delta is not available yet")
    if report.get("schema") != "privyhub_client_health_v1":
        raise RuntimeError("Client report schema mismatch")

    sequence = report.get("sequence")
    interval_ms = report.get("interval_ms")
    age_ms = feedback.get("age_ms")
    payload_bytes = feedback.get("payload_bytes")

    if not isinstance(sequence, int) or sequence < 2:
        raise RuntimeError("Client feedback sequence has not advanced")
    if interval_ms != 2_000:
        raise RuntimeError("Unexpected client feedback interval")
    if not isinstance(age_ms, int) or age_ms < 0 or age_ms > 6_000:
        raise RuntimeError("Client feedback age is outside the freshness window")
    if (
        not isinstance(payload_bytes, int)
        or payload_bytes <= 0
        or payload_bytes > 8_192
    ):
        raise RuntimeError("Client feedback payload size is invalid")

    video = report.get("video") if isinstance(report.get("video"), dict) else {}
    decoder = report.get("decoder") if isinstance(report.get("decoder"), dict) else {}
    if (
        not isinstance(video.get("recent_fps"), (int, float))
        or video.get("recent_fps", 0.0) <= 0.0
    ):
        raise RuntimeError("Client recent FPS is not positive")
    if not bool(decoder.get("hardware_accelerated", False)):
        raise RuntimeError("Client decoder is not reporting hardware acceleration")

    network = component(payload, "end_to_end_path")
    decoder_component = component(payload, "decoder")
    if network.get("health") == "unknown":
        raise RuntimeError("Network path remained unknown after fresh deltas")
    if decoder_component.get("health") == "unknown":
        raise RuntimeError("Decoder remained unknown after fresh deltas")

    collection = payload.get("collection") if isinstance(payload.get("collection"), dict) else {}
    if collection.get("new_resource_sampler_started") is not False:
        raise RuntimeError("Unexpected new resource sampler")

    keys: set[str] = set()
    strings: list[str] = []
    walk(payload, keys=keys, strings=strings)
    if keys & FORBIDDEN_KEYS:
        raise RuntimeError("Privacy-forbidden key present")
    for text in strings:
        if IPV4.search(text) or MAC.search(text):
            raise RuntimeError("Network identifier value detected")

    video_delta = delta.get("video") if isinstance(delta.get("video"), dict) else {}
    decoder_delta = delta.get("decoder") if isinstance(delta.get("decoder"), dict) else {}

    return {
        "sequence": sequence,
        "interval_ms": interval_ms,
        "age_ms": age_ms,
        "payload_bytes": payload_bytes,
        "recent_fps": video.get("recent_fps"),
        "recent_mbps": video.get("recent_mbps"),
        "fec_recovered_delta": video_delta.get("fec_recovered_packets"),
        "fec_unrecoverable_delta": video_delta.get("fec_unrecoverable_groups"),
        "decoder_stale_delta": decoder_delta.get("stale_output_drops"),
        "decoder_overflow_delta": decoder_delta.get("queue_overflow_drops"),
        "network_health": network.get("health"),
        "network_event": network.get("event_code"),
        "decoder_health": decoder_component.get("health"),
        "decoder_event": decoder_component.get("event_code"),
    }


def write_result(
    root: Path,
    *,
    result: dict[str, Any] | None,
    error: str = "",
) -> int:
    out_dir = root / "logs" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    classification = CONFIRMED if result is not None else NOT_CONFIRMED

    lines = [
        "PrivyHub Phase B1.5 Android client health feedback runtime probe",
        f"Classification: {classification}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
    ]

    if result is None:
        lines += ["=== FAILURE ===", "Reason: " + (error or "<unknown>")]
    else:
        lines += [
            "=== CLIENT FEEDBACK ===",
            f"Sequence: {result['sequence']}",
            f"Interval ms: {result['interval_ms']}",
            f"Age ms: {result['age_ms']}",
            f"Payload bytes: {result['payload_bytes']}",
            f"Recent video FPS: {result['recent_fps']}",
            f"Recent video Mbps: {result['recent_mbps']}",
            "FEC recovered packets delta: " + str(result["fec_recovered_delta"]),
            "FEC unrecoverable groups delta: " + str(result["fec_unrecoverable_delta"]),
            "Decoder stale drops delta: " + str(result["decoder_stale_delta"]),
            "Decoder overflow drops delta: " + str(result["decoder_overflow_delta"]),
            "",
            "=== NORMALIZED HEALTH ===",
            "Network path health: " + str(result["network_health"]),
            "Network path event: " + str(result["network_event"]),
            "Decoder health: " + str(result["decoder_health"]),
            "Decoder event: " + str(result["decoder_event"]),
            "",
            "New Android metrics timer added: False",
            "New resource sampler started: False",
            "Persistent client-health log added: False",
            "Benchmark thresholds applied: False",
            "Privacy-forbidden keys present: False",
            "Network identifier values present: False",
        ]

    (out_dir / "b1_client_feedback_runtime.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0 if result is not None else 1


def self_test() -> int:
    fixture = {
        "schema": "privyhub_diagnostics_health_v1",
        "session": {"native_stream_active": True},
        "components": [
            {
                "component": "end_to_end_path",
                "health": "healthy",
                "event_code": "NET-PATH-CLIENT-HEALTHY",
            },
            {
                "component": "decoder",
                "health": "healthy",
                "event_code": "VIDEO-DECODER-CLIENT-HEALTHY",
            },
        ],
        "client_feedback": {
            "schema": "privyhub_client_health_store_v1",
            "available": True,
            "fresh": True,
            "age_ms": 100,
            "payload_bytes": 600,
            "delta_available": True,
            "report": {
                "schema": "privyhub_client_health_v1",
                "sequence": 2,
                "interval_ms": 2000,
                "session_elapsed_ms": 4000,
                "video": {"recent_fps": 60.0, "recent_mbps": 7.5},
                "decoder": {"hardware_accelerated": True},
            },
            "delta": {
                "video": {
                    "fec_recovered_packets": 0,
                    "fec_unrecoverable_groups": 0,
                },
                "decoder": {
                    "stale_output_drops": 0,
                    "queue_overflow_drops": 0,
                },
            },
        },
        "collection": {"new_resource_sampler_started": False},
    }
    result = validate(fixture)
    assert result["sequence"] == 2
    assert result["network_health"] == "healthy"
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()
    try:
        payload = request_health()
        result = validate(payload)
    except (
        urllib.error.URLError,
        TimeoutError,
        ConnectionError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        RuntimeError,
    ) as exc:
        return write_result(root, result=None, error=str(exc))

    return write_result(root, result=result)


if __name__ == "__main__":
    raise SystemExit(main())
