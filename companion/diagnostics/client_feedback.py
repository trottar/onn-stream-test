from __future__ import annotations

import copy
import math
import threading
import time

from typing import Any

CLIENT_HEALTH_SCHEMA = "privyhub_client_health_v1"
CLIENT_HEALTH_STORE_SCHEMA = "privyhub_client_health_store_v1"

DEFAULT_MAX_AGE_MS = 6_000

_VIDEO_COUNTERS = (
    "packets",
    "lost_packets",
    "dropped_frames",
    "fec_recovered_packets",
    "fec_unrecoverable_groups",
    "late_or_reordered_packets",
    "forward_gap_events",
)

_DECODER_COUNTERS = (
    "queued_frames",
    "rendered_frames",
    "dropped_frames",
    "queue_overflow_drops",
    "stale_output_drops",
)


def _int(value: Any, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    number = int(value)
    if number < 0:
        raise ValueError(f"{name} must be non-negative")
    return number


def _float(value: Any, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return number


def _bool(value: Any, *, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def _object(value: Any, *, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def normalize_client_health(payload: Any) -> dict[str, Any]:
    root = _object(payload, name="payload")
    if root.get("schema") != CLIENT_HEALTH_SCHEMA:
        raise ValueError("Unsupported client health schema")

    sequence = _int(root.get("sequence"), name="sequence")
    if sequence <= 0:
        raise ValueError("sequence must be positive")

    interval_ms = _int(root.get("interval_ms"), name="interval_ms")
    if interval_ms < 250 or interval_ms > 60_000:
        raise ValueError("interval_ms is outside the supported range")

    session_elapsed_ms = _int(
        root.get("session_elapsed_ms"),
        name="session_elapsed_ms",
    )

    video = _object(root.get("video"), name="video")
    decoder = _object(root.get("decoder"), name="decoder")

    normalized_video = {
        key: _int(video.get(key), name=f"video.{key}")
        for key in _VIDEO_COUNTERS
    }
    normalized_video["recent_fps"] = _float(
        video.get("recent_fps"),
        name="video.recent_fps",
    )
    normalized_video["recent_mbps"] = _float(
        video.get("recent_mbps"),
        name="video.recent_mbps",
    )
    normalized_video["waiting_for_idr"] = _bool(
        video.get("waiting_for_idr"),
        name="video.waiting_for_idr",
    )

    normalized_decoder = {
        key: _int(decoder.get(key), name=f"decoder.{key}")
        for key in _DECODER_COUNTERS
    }
    for key in (
        "queue_depth",
        "latest_rx_to_decode_ms",
        "latest_output_gap_ms",
    ):
        normalized_decoder[key] = _int(
            decoder.get(key),
            name=f"decoder.{key}",
        )

    for key in (
        "hardware_accelerated",
        "vendor_codec",
        "low_latency_enabled",
    ):
        normalized_decoder[key] = _bool(
            decoder.get(key),
            name=f"decoder.{key}",
        )

    return {
        "schema": CLIENT_HEALTH_SCHEMA,
        "sequence": sequence,
        "interval_ms": interval_ms,
        "session_elapsed_ms": session_elapsed_ms,
        "video": normalized_video,
        "decoder": normalized_decoder,
    }


def _counter_delta(
    current: dict[str, Any],
    previous: dict[str, Any],
    keys: tuple[str, ...],
) -> dict[str, int]:
    return {
        key: max(0, int(current.get(key, 0)) - int(previous.get(key, 0)))
        for key in keys
    }


def _deltas(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
) -> tuple[bool, dict[str, Any]]:
    if not isinstance(previous, dict):
        return False, {}

    if (
        int(current.get("sequence", 0))
        <= int(previous.get("sequence", 0))
        or int(current.get("session_elapsed_ms", 0))
        <= int(previous.get("session_elapsed_ms", 0))
    ):
        return False, {}

    return True, {
        "video": _counter_delta(
            _object(current.get("video"), name="video"),
            _object(previous.get("video"), name="previous.video"),
            _VIDEO_COUNTERS,
        ),
        "decoder": _counter_delta(
            _object(current.get("decoder"), name="decoder"),
            _object(previous.get("decoder"), name="previous.decoder"),
            _DECODER_COUNTERS,
        ),
    }


class ClientHealthStore:
    def __init__(self, *, max_age_ms: int = DEFAULT_MAX_AGE_MS) -> None:
        self._lock = threading.Lock()
        self._max_age_ms = max(1_000, int(max_age_ms))
        self._report: dict[str, Any] | None = None
        self._received_unix_ms = 0
        self._payload_bytes = 0
        self._delta_available = False
        self._delta: dict[str, Any] = {}

    def accept(
        self,
        payload: Any,
        *,
        payload_bytes: int,
    ) -> dict[str, Any]:
        normalized = normalize_client_health(payload)
        body_bytes = max(0, int(payload_bytes))
        now_ms = int(time.time() * 1000.0)

        with self._lock:
            delta_available, delta = _deltas(normalized, self._report)
            self._report = normalized
            self._received_unix_ms = now_ms
            self._payload_bytes = body_bytes
            self._delta_available = delta_available
            self._delta = delta

        return {
            "ok": True,
            "accepted": True,
            "schema": CLIENT_HEALTH_SCHEMA,
            "sequence": normalized["sequence"],
        }

    def snapshot(self) -> dict[str, Any]:
        now_ms = int(time.time() * 1000.0)

        with self._lock:
            report = copy.deepcopy(self._report)
            received = int(self._received_unix_ms)
            payload_bytes = int(self._payload_bytes)
            delta_available = bool(self._delta_available)
            delta = copy.deepcopy(self._delta)

        if report is None:
            return {
                "schema": CLIENT_HEALTH_STORE_SCHEMA,
                "available": False,
                "fresh": False,
                "age_ms": None,
                "payload_bytes": 0,
                "delta_available": False,
                "report": {},
                "delta": {},
            }

        age_ms = max(0, now_ms - received)
        return {
            "schema": CLIENT_HEALTH_STORE_SCHEMA,
            "available": True,
            "fresh": age_ms <= self._max_age_ms,
            "age_ms": age_ms,
            "payload_bytes": payload_bytes,
            "delta_available": delta_available,
            "report": report,
            "delta": delta,
        }
