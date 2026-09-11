from __future__ import annotations

import copy
import re
import threading
import time

from collections import deque
from pathlib import Path
from typing import Any

EVENT_HISTORY_SCHEMA = "privyhub_diagnostic_event_history_v1"
EVENT_RECORD_SCHEMA = "privyhub_diagnostic_event_v1"
DEFAULT_EVENT_CAPACITY = 128

_ADDRESS_RE = re.compile(
    r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"
)
_MAC_RE = re.compile(
    r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
)

_PULSE_KEYS = {
    "delta_fec_recovered_packets",
    "delta_fec_unrecoverable_groups",
    "delta_dropped_frames",
    "delta_stale_output_drops",
    "delta_queue_overflow_drops",
}

_MAX_MEASUREMENT_KEYS = 32
_MAX_TEXT = 160


def _safe_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    text = value.strip()[:_MAX_TEXT]
    text = _ADDRESS_RE.sub(
        "<redacted-address>",
        text,
    )
    return _MAC_RE.sub(
        "<redacted-address>",
        text,
    )


def _safe_measurements(
    value: Any,
    *,
    depth: int = 0,
) -> Any:
    if depth > 2:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        return _safe_text(value)

    if isinstance(value, dict):
        result: dict[str, Any] = {}

        for index, key in enumerate(
            sorted(
                value,
                key=lambda item: str(item),
            )
        ):
            if index >= _MAX_MEASUREMENT_KEYS:
                break

            safe_key = _safe_text(str(key))
            if not safe_key:
                continue

            child = _safe_measurements(
                value[key],
                depth=depth + 1,
            )

            if child is not None:
                result[safe_key] = child

        return result

    if isinstance(value, list):
        return [
            child
            for child in (
                _safe_measurements(
                    item,
                    depth=depth + 1,
                )
                for item in value[:16]
            )
            if child is not None
        ]

    return None


def _positive_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    return value > 0


def _session_identifier(
    games_status: Any,
) -> str:
    if not isinstance(games_status, dict):
        return ""

    for key in (
        "session_id",
        "game_id",
        "active_game_id",
    ):
        value = games_status.get(key)
        if isinstance(value, str):
            safe = _safe_text(value)
            if safe:
                return safe

    return ""


def _client_sequence(
    snapshot: dict[str, Any],
) -> int | None:
    feedback = snapshot.get("client_feedback")

    if not isinstance(feedback, dict):
        return None

    report = feedback.get("report")

    if not isinstance(report, dict):
        return None

    value = report.get("sequence")

    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    return None


class DiagnosticEventHistory:
    def __init__(
        self,
        *,
        capacity: int = DEFAULT_EVENT_CAPACITY,
    ) -> None:
        self._capacity = max(
            16,
            int(capacity),
        )
        self._lock = threading.Lock()
        self._events: deque[dict[str, Any]] = deque(
            maxlen=self._capacity
        )
        self._last_component_signature: dict[
            str,
            tuple[str, str, str],
        ] = {}
        self._last_pulse_sequence: dict[
            str,
            int,
        ] = {}
        self._last_event_id_by_component: dict[
            str,
            int,
        ] = {}
        self._next_event_id = 1

    @property
    def capacity(self) -> int:
        return self._capacity

    def _append(
        self,
        *,
        timestamp_unix_ms: int,
        session_id: str,
        component: dict[str, Any],
        event_kind: str,
        pulse_measurements: dict[str, Any] | None = None,
    ) -> None:
        component_name = _safe_text(
            component.get(
                "component",
                "unknown",
            )
        ) or "unknown"

        predecessor = self._last_event_id_by_component.get(
            component_name
        )

        severity = _safe_text(
            component.get(
                "severity",
                "info",
            )
        ) or "info"

        remediation = ""

        if severity == "error":
            remediation = (
                "Run Self-Test and collect a sanitized diagnostics bundle."
            )
        elif severity == "warning":
            remediation = (
                "Review raw measurements; collect diagnostics if the condition persists."
            )

        event_id = self._next_event_id
        self._next_event_id += 1

        measurements = (
            pulse_measurements
            if pulse_measurements is not None
            else component.get(
                "measurements",
                {},
            )
        )

        record = {
            "schema": EVENT_RECORD_SCHEMA,
            "event_id": event_id,
            "timestamp_unix_ms": int(
                timestamp_unix_ms
            ),
            "session_id": _safe_text(
                session_id
            ),
            "subsystem": _safe_text(
                component.get(
                    "subsystem",
                    "unknown",
                )
            ) or "unknown",
            "component": component_name,
            "severity": severity,
            "event_code": _safe_text(
                component.get(
                    "event_code",
                    "UNKNOWN",
                )
            ) or "UNKNOWN",
            "summary": _safe_text(
                component.get(
                    "summary",
                    "",
                )
            ),
            "raw_measurements": _safe_measurements(
                measurements
            ),
            "classification_result": _safe_text(
                component.get(
                    "health",
                    "unknown",
                )
            ) or "unknown",
            "classifier": _safe_measurements(
                component.get(
                    "classification",
                    {},
                )
            ),
            "causal_predecessor_event_id": predecessor,
            "remediation_hint": remediation,
            "privacy_classification": (
                "ordinary-diagnostics-no-network-identifiers"
            ),
            "event_kind": event_kind,
        }

        self._events.append(
            record
        )

        self._last_event_id_by_component[
            component_name
        ] = event_id

    def observe_snapshot(
        self,
        snapshot: dict[str, Any],
        *,
        games_status: Any = None,
    ) -> None:
        generated = snapshot.get(
            "generated_unix_ms"
        )

        if not isinstance(
            generated,
            int,
        ):
            generated = int(
                time.time()
                * 1000.0
            )

        components = snapshot.get(
            "components"
        )

        if not isinstance(
            components,
            list,
        ):
            return

        session_id = _session_identifier(
            games_status
        )

        sequence = _client_sequence(
            snapshot
        )

        with self._lock:
            for raw_component in components:
                if not isinstance(
                    raw_component,
                    dict,
                ):
                    continue

                component = raw_component
                component_name = _safe_text(
                    component.get(
                        "component",
                        "unknown",
                    )
                ) or "unknown"

                signature = (
                    _safe_text(
                        component.get(
                            "health",
                            "unknown",
                        )
                    ),
                    _safe_text(
                        component.get(
                            "severity",
                            "info",
                        )
                    ),
                    _safe_text(
                        component.get(
                            "event_code",
                            "UNKNOWN",
                        )
                    ),
                )

                previous = (
                    self._last_component_signature.get(
                        component_name
                    )
                )

                if previous != signature:
                    self._append(
                        timestamp_unix_ms=generated,
                        session_id=session_id,
                        component=component,
                        event_kind=(
                            "initial"
                            if previous is None
                            else "transition"
                        ),
                    )
                    self._last_component_signature[
                        component_name
                    ] = signature

                measurements = component.get(
                    "measurements"
                )

                if not isinstance(
                    measurements,
                    dict,
                ):
                    continue

                pulse = {
                    key: measurements.get(key)
                    for key in sorted(
                        _PULSE_KEYS
                    )
                    if (
                        key in measurements
                        and _positive_number(
                            measurements.get(
                                key
                            )
                        )
                    )
                }

                if not pulse:
                    continue

                if sequence is None:
                    continue

                pulse_key = (
                    component_name
                )

                if (
                    self._last_pulse_sequence.get(
                        pulse_key
                    )
                    == sequence
                ):
                    continue

                self._append(
                    timestamp_unix_ms=generated,
                    session_id=session_id,
                    component=component,
                    event_kind="measurement_pulse",
                    pulse_measurements=pulse,
                )

                self._last_pulse_sequence[
                    pulse_key
                ] = sequence

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            events = copy.deepcopy(
                list(
                    self._events
                )
            )

        return {
            "schema": EVENT_HISTORY_SCHEMA,
            "capacity": self._capacity,
            "count": len(events),
            "bounded": True,
            "events": events,
        }
