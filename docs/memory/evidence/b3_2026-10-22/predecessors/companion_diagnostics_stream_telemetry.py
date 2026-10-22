from __future__ import annotations

import copy
import math
import threading
import time

from typing import Any


STREAM_TELEMETRY_SCHEMA = "privyhub_stream_telemetry_v1"
DEFAULT_MAX_AGE_MS = 6_000


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def _int_or_none(value: Any) -> int | None:
    number = _number(value)
    return None if number is None else int(number)


def _float_or_none(value: Any) -> float | None:
    number = _number(value)
    return None if number is None else float(number)


class StreamTelemetryStore:
    """Latest-only adaptation-facing stream measurements."""

    def __init__(self, *, max_age_ms: int = DEFAULT_MAX_AGE_MS) -> None:
        self._lock = threading.Lock()
        self._max_age_ms = max(1_000, int(max_age_ms))
        self._snapshot: dict[str, Any] | None = None
        self._received_unix_ms = 0
        self._sender_baseline: dict[str, float] | None = None

    @staticmethod
    def _sender_values(
        native_stream_status: dict[str, Any],
    ) -> dict[str, float] | None:
        fec = _dict(native_stream_status.get("fec"))
        values = {
            "sent_bytes": _number(fec.get("sent_bytes")),
            "send_calls": _number(fec.get("send_calls")),
            "send_errors": _number(fec.get("send_errors")),
            "send_call_total_us": _number(fec.get("send_call_total_us")),
        }
        if any(value is None for value in values.values()):
            return None
        return {
            key: float(value)
            for key, value in values.items()
            if value is not None
        }

    @staticmethod
    def _sender_delta(
        current: dict[str, float] | None,
        previous: dict[str, float] | None,
    ) -> tuple[bool, dict[str, Any]]:
        if current is None or previous is None:
            return False, {}

        keys = (
            "sent_bytes",
            "send_calls",
            "send_errors",
            "send_call_total_us",
        )
        if any(current[key] < previous[key] for key in keys):
            return False, {}

        calls_delta = int(current["send_calls"] - previous["send_calls"])
        duration_delta_us = (
            current["send_call_total_us"] - previous["send_call_total_us"]
        )

        return True, {
            "sent_bytes_delta": int(
                current["sent_bytes"] - previous["sent_bytes"]
            ),
            "send_calls_delta": calls_delta,
            "send_errors_delta": int(
                current["send_errors"] - previous["send_errors"]
            ),
            "send_call_avg_us": (
                duration_delta_us / calls_delta
                if calls_delta > 0
                else 0.0
            ),
        }

    def accept(
        self,
        *,
        client_health_feedback: dict[str, Any],
        native_stream_status: dict[str, Any],
    ) -> dict[str, Any]:
        feedback = _dict(client_health_feedback)
        report = _dict(feedback.get("report"))
        delta = _dict(feedback.get("delta"))
        video = _dict(report.get("video"))
        decoder = _dict(report.get("decoder"))
        video_delta = _dict(delta.get("video"))
        decoder_delta = _dict(delta.get("decoder"))
        fec = _dict(native_stream_status.get("fec"))

        sender_current = self._sender_values(native_stream_status)

        with self._lock:
            sender_delta_available, sender_delta = self._sender_delta(
                sender_current,
                self._sender_baseline,
            )
            if sender_current is not None:
                self._sender_baseline = sender_current

        available = bool(feedback.get("available")) and bool(report)
        delta_available = bool(feedback.get("delta_available"))

        payload: dict[str, Any] = {
            "schema": STREAM_TELEMETRY_SCHEMA,
            "available": available,
            "fresh": bool(feedback.get("fresh")) if available else False,
            "profile_id": (
                str(native_stream_status.get("profile_id", "")).strip()
                or None
            ),
            "sample_interval_ms": _int_or_none(report.get("interval_ms")),
            "session_elapsed_ms": _int_or_none(report.get("session_elapsed_ms")),
            "delta_available": delta_available,
            "receiver": {
                "recent_mbps": _float_or_none(video.get("recent_mbps")),
                "recent_fps": _float_or_none(video.get("recent_fps")),
                "packets_delta": (
                    _int_or_none(video_delta.get("packets"))
                    if delta_available
                    else None
                ),
                "lost_packets_delta": (
                    _int_or_none(video_delta.get("lost_packets"))
                    if delta_available
                    else None
                ),
                "late_or_reordered_packets_delta": (
                    _int_or_none(video_delta.get("late_or_reordered_packets"))
                    if delta_available
                    else None
                ),
                "forward_gap_events_delta": (
                    _int_or_none(video_delta.get("forward_gap_events"))
                    if delta_available
                    else None
                ),
                "interarrival_jitter_ms": _float_or_none(
                    video.get("interarrival_jitter_ms")
                ),
                "waiting_for_idr": (
                    bool(video.get("waiting_for_idr"))
                    if "waiting_for_idr" in video
                    else None
                ),
            },
            "fec": {
                "recovered_packets_delta": (
                    _int_or_none(video_delta.get("fec_recovered_packets"))
                    if delta_available
                    else None
                ),
                "unrecoverable_groups_delta": (
                    _int_or_none(video_delta.get("fec_unrecoverable_groups"))
                    if delta_available
                    else None
                ),
                "group_size": _int_or_none(fec.get("group_size")),
            },
            "sender": {
                "delta_available": sender_delta_available,
                "sent_bytes_delta": sender_delta.get("sent_bytes_delta"),
                "send_calls_delta": sender_delta.get("send_calls_delta"),
                "send_errors_delta": sender_delta.get("send_errors_delta"),
                "send_call_avg_us": sender_delta.get("send_call_avg_us"),
                "send_call_max_us": _float_or_none(fec.get("send_call_max_us")),
            },
            "latency": {
                "control_round_trip_ms": _int_or_none(
                    report.get("control_round_trip_ms")
                ),
                "receive_to_decode_ms": _int_or_none(
                    decoder.get("latest_rx_to_decode_ms")
                ),
                "output_gap_ms": _int_or_none(
                    decoder.get("latest_output_gap_ms")
                ),
            },
            "decoder": {
                "queue_depth": _int_or_none(decoder.get("queue_depth")),
                "queue_depth_delta": (
                    _int_or_none(decoder_delta.get("queue_depth_delta"))
                    if delta_available
                    else None
                ),
                "queued_frames_delta": (
                    _int_or_none(decoder_delta.get("queued_frames"))
                    if delta_available
                    else None
                ),
                "rendered_frames_delta": (
                    _int_or_none(decoder_delta.get("rendered_frames"))
                    if delta_available
                    else None
                ),
                "dropped_frames_delta": (
                    _int_or_none(decoder_delta.get("dropped_frames"))
                    if delta_available
                    else None
                ),
                "queue_overflow_drops_delta": (
                    _int_or_none(decoder_delta.get("queue_overflow_drops"))
                    if delta_available
                    else None
                ),
                "stale_output_drops_delta": (
                    _int_or_none(decoder_delta.get("stale_output_drops"))
                    if delta_available
                    else None
                ),
                "hardware_accelerated": (
                    bool(decoder.get("hardware_accelerated"))
                    if "hardware_accelerated" in decoder
                    else None
                ),
                "vendor_codec": (
                    bool(decoder.get("vendor_codec"))
                    if "vendor_codec" in decoder
                    else None
                ),
                "low_latency_enabled": (
                    bool(decoder.get("low_latency_enabled"))
                    if "low_latency_enabled" in decoder
                    else None
                ),
            },
        }

        now_ms = int(time.time() * 1000.0)
        with self._lock:
            self._snapshot = payload
            self._received_unix_ms = now_ms

        return copy.deepcopy(payload)

    def snapshot(self) -> dict[str, Any]:
        now_ms = int(time.time() * 1000.0)

        with self._lock:
            payload = copy.deepcopy(self._snapshot)
            received = int(self._received_unix_ms)

        if payload is None:
            return {
                "schema": STREAM_TELEMETRY_SCHEMA,
                "available": False,
                "fresh": False,
                "age_ms": None,
                "profile_id": None,
                "sample_interval_ms": None,
                "session_elapsed_ms": None,
                "delta_available": False,
                "receiver": {},
                "fec": {},
                "sender": {"delta_available": False},
                "latency": {},
                "decoder": {},
            }

        age_ms = max(0, now_ms - received)
        payload["age_ms"] = age_ms
        payload["fresh"] = (
            bool(payload.get("available"))
            and age_ms <= self._max_age_ms
        )
        return payload
