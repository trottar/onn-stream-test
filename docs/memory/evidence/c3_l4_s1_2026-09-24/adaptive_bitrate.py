"""C3.L4-S1: the adaptive-bitrate policy engine, SHADOW ONLY.

Design: `docs/memory/architecture/ADAPTIVE_BITRATE.md` section "C3.L4 shadow
controller — S1". This module watches the 2 s client telemetry the stream
already produces (`diagnostics.stream_telemetry`) and writes down what a
controller WOULD do. **It never actuates**: it holds no reference to any
actuator, and no mode it accepts calls one. `acted` is False always.

Modes, from `PRIVYHUB_ADAPTIVE_BITRATE_MODE`:

  off     (default, and any unrecognised value) -- nothing is evaluated,
          nothing is logged; the status field reads `mode: off`;
  shadow  -- every fresh, distinct client report is evaluated; every
          decision or state change is one JSON line in
          `logs/games/adaptive_bitrate_shadow.jsonl` (rotated at 4 MiB,
          three kept, into `stream_log_archive/`).

There is deliberately no third mode in this module.

Two trigger classes (`C3-L2`: `video_only_restart` is authorized for
fallback and recovery, not for automatic adaptation during play):

  FALLBACK -- the stream is already failing by the close-out's own rows;
              the only class a later acting mode could ever use;
  ROUTINE  -- capacity/latency pressure short of failure; not authorized;
              logged so the night shows how often it would fire.

A decrease is ONE transition (never a ramp): FALLBACK to the ladder's
floor, ROUTINE one rung down. An increase is one rung per decision.
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # the companion's layout; the unit tests import the pure engine only
    from games.log_rotation import rotate_if_needed
except Exception:  # pragma: no cover - exercised only outside the companion
    rotate_if_needed = None  # type: ignore[assignment]


SCHEMA = "privyhub_adaptive_bitrate_v1"
MODE_ENV = "PRIVYHUB_ADAPTIVE_BITRATE_MODE"
MODES = ("off", "shadow")
LOG_NAME = "adaptive_bitrate_shadow.jsonl"
LOG_MAX_BYTES = 4 * 1024 * 1024
LOG_KEEP = 3

# --- pre-registered constants (C3-L4-S1 task; sources in the architecture) --
LADDER_KBPS = (5000, 5500, 6000, 7000)      # D-066 / C3.L3
REFERENCE_KBPS = 7000
REPORT_INTERVAL_MS = 2000                   # the client's report cadence
BLACKOUT_REPORTS = 3                        # S1 soak: settling 1-3 reports
HOLDDOWN_SAME_REPORTS = 30                  # 60 s before the same direction
HOLDDOWN_REVERSAL_REPORTS = 60              # 120 s before a reversal
WINDOW_REPORTS = 5                          # 10 s of evidence for a decrease
FALLBACK_FPS_BELOW = 50.0                   # on all 5
FALLBACK_QUEUE_AT_LEAST, FALLBACK_QUEUE_OF = 2, 3        # >= 2 on >= 3 of 5
FALLBACK_GAP_ABOVE_MS, FALLBACK_GAP_OF = 250, 2          # > 250 on >= 2 of 5
ROUTINE_FPS_BELOW, ROUTINE_FPS_OF = 57.0, 4              # < 57 on >= 4 of 5
ROUTINE_QUEUE_AT_LEAST, ROUTINE_QUEUE_OF = 1, 3          # >= 1 on >= 3 of 5
CLEAN_FPS_AT_LEAST = 59.0
CLEAN_QUEUE_EQ = 0
CLEAN_GAP_AT_MOST_MS = 150
CLEAN_REPORTS_FOR_INCREASE = 90             # 180 s
OSCILLATION_CHANGES = 3                     # the third direction change ...
OSCILLATION_WINDOW_MS = 10 * 60 * 1000      # ... within 10 minutes -> HOLD
STALE_NON_DISTINCT_REPORTS = 3              # no distinct snapshot for 3 reports

# States (ADAPTIVE_BITRATE.md §C3 safety state)
REFERENCE = "REFERENCE"
PRESSURE = "PRESSURE"
HOLD_DOWN = "HOLD_DOWN"
RECOVERY_PROBATION = "RECOVERY_PROBATION"
TELEMETRY_STALE = "TELEMETRY_STALE"
ACTUATOR_FAILED = "ACTUATOR_FAILED"
HOLD = "HOLD"


def mode_from_env(environ: dict[str, str] | None = None) -> tuple[str, bool]:
    """(mode, ignored): an unrecognised value is `off`, and says so."""
    raw = (environ if environ is not None else os.environ).get(MODE_ENV)
    if raw is None or raw.strip() == "":
        return "off", False
    value = raw.strip().lower()
    if value in MODES:
        return value, False
    return "off", True


def _sample(telemetry: dict[str, Any]) -> dict[str, Any]:
    """The fields the policy reads, from a `privyhub_stream_telemetry_v1`."""
    receiver = telemetry.get("receiver") or {}
    decoder = telemetry.get("decoder") or {}
    latency = telemetry.get("latency") or {}
    return {
        "available": bool(telemetry.get("available")),
        "fresh": bool(telemetry.get("fresh")),
        "elapsed_ms": telemetry.get("session_elapsed_ms"),
        "fps": receiver.get("recent_fps"),
        "queue_depth": decoder.get("queue_depth"),
        "output_gap_ms": latency.get("output_gap_ms"),
        "waiting_for_idr": bool(receiver.get("waiting_for_idr")),
        "lost_packets_delta": receiver.get("lost_packets_delta"),
        "recovered_packets_delta": (telemetry.get("fec") or {}).get("recovered_packets_delta"),
    }


class ShadowPolicy:
    """The pure policy engine: feed it samples, it returns decisions.

    No clock, no I/O, no actuator. Time is the client's own
    `session_elapsed_ms`. The level it tracks is VIRTUAL: where the stream
    would be had every decision been acted on.
    """

    def __init__(self) -> None:
        self.reset(None)

    # -- lifecycle ---------------------------------------------------------
    def reset(self, elapsed_ms: int | None) -> None:
        self.level_kbps = REFERENCE_KBPS
        self.state = REFERENCE
        self.reason = "session_start"
        self.measurements: dict[str, Any] = {}
        self.window: deque[dict[str, Any]] = deque(maxlen=WINDOW_REPORTS)
        self.clean_count = 0
        self.blackout_remaining = 0
        self.reports_since_action: int | None = None
        self.last_direction: str | None = None
        self.direction_changes: list[int] = []
        self.oscillation_hold = False
        self.last_elapsed_ms = elapsed_ms
        self.non_distinct = 0
        self.decision_seq = 0
        self.reports = 0
        self.would_act = {"FALLBACK": 0, "ROUTINE": 0, "INCREASE": 0}
        self.stale_events = 0
        self.suppressed = {"blackout": 0, "hold_down": 0, "floor": 0, "oscillation": 0,
                           "routine_hold_down": 0}
        # The ROUTINE track: counted and logged on its own 30-report hold-down;
        # it never moves the virtual level, the blackout or the hold-down of the
        # acting track (FALLBACK down / RECOVERY up), because C3-L2 does not
        # authorize it and a later acting mode would not act on it.
        self.routine_reports_since: int | None = None

    # -- the rules ---------------------------------------------------------
    @staticmethod
    def _num(v: Any) -> float | None:
        return None if v is None or isinstance(v, bool) else float(v)

    def _is_clean(self, s: dict[str, Any]) -> bool:
        fps, q, gap = self._num(s["fps"]), self._num(s["queue_depth"]), self._num(s["output_gap_ms"])
        return (fps is not None and fps >= CLEAN_FPS_AT_LEAST and q is not None and q == CLEAN_QUEUE_EQ
                and gap is not None and gap <= CLEAN_GAP_AT_MOST_MS)

    def _evidence(self) -> tuple[str | None, dict[str, Any]]:
        """FALLBACK / ROUTINE / None over the last 5 fresh reports."""
        if len(self.window) < WINDOW_REPORTS:
            return None, {}
        fps = [self._num(s["fps"]) for s in self.window]
        q = [self._num(s["queue_depth"]) for s in self.window]
        gap = [self._num(s["output_gap_ms"]) for s in self.window]
        m = {"fps": fps, "queue_depth": q, "output_gap_ms": gap,
             "elapsed_ms": [s["elapsed_ms"] for s in self.window]}
        if any(v is None for v in fps):
            return None, m
        q_ok = [v for v in q if v is not None]
        g_ok = [v for v in gap if v is not None]
        fallback = (all(v < FALLBACK_FPS_BELOW for v in fps)
                    and (sum(1 for v in q_ok if v >= FALLBACK_QUEUE_AT_LEAST) >= FALLBACK_QUEUE_OF
                         or sum(1 for v in g_ok if v > FALLBACK_GAP_ABOVE_MS) >= FALLBACK_GAP_OF))
        if fallback:
            return "FALLBACK", m
        routine = (sum(1 for v in fps if v < ROUTINE_FPS_BELOW) >= ROUTINE_FPS_OF
                   and sum(1 for v in q_ok if v >= ROUTINE_QUEUE_AT_LEAST) >= ROUTINE_QUEUE_OF)
        if routine:
            return "ROUTINE", m
        return None, m

    def _hold_down_left(self, direction: str) -> int:
        if self.reports_since_action is None:
            return 0
        need = HOLDDOWN_SAME_REPORTS if direction == self.last_direction else HOLDDOWN_REVERSAL_REPORTS
        return max(0, need - self.reports_since_action)

    def _set_state(self, state: str, reason: str, m: dict[str, Any] | None = None) -> dict[str, Any] | None:
        if state == self.state and reason == self.reason:
            return None
        prev = self.state
        self.state, self.reason = state, reason
        if m is not None:
            self.measurements = m
        return {"event": "state", "from": prev, "to": state, "reason": reason}

    def _act(self, direction: str, cls: str, target: int, m: dict[str, Any], elapsed: int) -> dict[str, Any]:
        if self.last_direction is not None and direction != self.last_direction:
            self.direction_changes = [t for t in self.direction_changes
                                      if elapsed - t <= OSCILLATION_WINDOW_MS] + [elapsed]
            if len(self.direction_changes) >= OSCILLATION_CHANGES:
                self.oscillation_hold = True
                self.suppressed["oscillation"] += 1
                self.window.clear()
                self.clean_count = 0
                self.state, self.reason, self.measurements = HOLD, "oscillation", m
                self.decision_seq += 1
                return {"event": "hold", "class": cls, "direction": direction, "reason": "oscillation",
                        "would_target_kbps": target, "level_kbps": self.level_kbps,
                        "direction_changes_ms": list(self.direction_changes), "measurements": m,
                        "acted": False}
        self.decision_seq += 1
        self.would_act["INCREASE" if direction == "up" else cls] += 1
        prev = self.level_kbps
        self.level_kbps = target
        self.last_direction = direction
        self.reports_since_action = 0
        self.blackout_remaining = BLACKOUT_REPORTS
        self.window.clear()
        self.clean_count = 0
        self.state = HOLD_DOWN
        self.reason = f"would_{'increase' if direction == 'up' else 'decrease'}_{cls.lower()}"
        self.measurements = m
        return {"event": "would_act", "class": cls, "direction": direction, "from_kbps": prev,
                "to_kbps": target, "reason": self.reason, "track": "acting_path_shadow",
                "measurements": m, "acted": False}

    # -- one report --------------------------------------------------------
    def feed(self, s: dict[str, Any]) -> list[dict[str, Any]]:
        """Evaluate one client report. Returns the log events it produced."""
        events: list[dict[str, Any]] = []
        elapsed = s.get("elapsed_ms")
        if isinstance(elapsed, (int, float)) and self.last_elapsed_ms is not None \
                and elapsed < self.last_elapsed_ms:
            self.reset(int(elapsed))
            events.append({"event": "session_reset"})
        if not s.get("available") or not s.get("fresh") or not isinstance(elapsed, (int, float)):
            self.stale_events += 1
            e = self._set_state(TELEMETRY_STALE, "telemetry_unavailable" if not s.get("available")
                                else "telemetry_not_fresh")
            return events + ([e] if e else [])
        if self.last_elapsed_ms is not None and elapsed == self.last_elapsed_ms:
            self.non_distinct += 1
            if self.non_distinct >= STALE_NON_DISTINCT_REPORTS:
                self.stale_events += 1
                e = self._set_state(TELEMETRY_STALE, "no_distinct_snapshot")
                return events + ([e] if e else [])
            return events
        self.non_distinct = 0
        self.last_elapsed_ms = int(elapsed)
        self.reports += 1
        if self.reports_since_action is not None:
            self.reports_since_action += 1
        if self.routine_reports_since is not None:
            self.routine_reports_since += 1

        if self.oscillation_hold:
            e = self._set_state(HOLD, "oscillation")
            return events + ([e] if e else [])
        if self.blackout_remaining > 0:
            self.blackout_remaining -= 1
            self.suppressed["blackout"] += 1
            e = self._set_state(HOLD_DOWN, "blackout")
            return events + ([e] if e else [])
        if s.get("waiting_for_idr"):
            # D-019 / ADAPTIVE_BITRATE.md: a known resync is never evidence,
            # and it is not clean either.
            self.clean_count = 0
            e = self._set_state(self.state if self.state != TELEMETRY_STALE else REFERENCE,
                                "resync_ignored")
            return events + ([e] if e else [])

        self.window.append(s)
        self.clean_count = self.clean_count + 1 if self._is_clean(s) else 0
        cls, m = self._evidence()

        if cls == "FALLBACK":
            if self.level_kbps <= LADDER_KBPS[0]:
                self.suppressed["floor"] += 1
                e = self._set_state(PRESSURE, "fallback_at_floor", m)
                return events + ([e] if e else [])
            if self._hold_down_left("down") > 0:
                self.suppressed["hold_down"] += 1
                e = self._set_state(HOLD_DOWN, "fallback_in_hold_down", m)
                return events + ([e] if e else [])
            return events + [self._act("down", cls, LADDER_KBPS[0], m, int(elapsed))]

        if cls == "ROUTINE":
            target = next((k for k in reversed(LADDER_KBPS) if k < self.level_kbps), None)
            if target is None:
                self.suppressed["floor"] += 1
                e = self._set_state(PRESSURE, "routine_at_floor", m)
                return events + ([e] if e else [])
            if self.routine_reports_since is not None \
                    and self.routine_reports_since < HOLDDOWN_SAME_REPORTS:
                self.suppressed["routine_hold_down"] += 1
                e = self._set_state(PRESSURE, "routine_in_hold_down", m)
                return events + ([e] if e else [])
            self.routine_reports_since = 0
            self.decision_seq += 1
            self.would_act["ROUTINE"] += 1
            self.state, self.reason, self.measurements = PRESSURE, "would_decrease_routine", m
            return events + [{"event": "would_act", "class": "ROUTINE", "direction": "down",
                              "from_kbps": self.level_kbps, "to_kbps": target,
                              "reason": "would_decrease_routine", "track": "routine_not_authorized",
                              "measurements": m, "acted": False}]

        if self.level_kbps < REFERENCE_KBPS:
            if self.clean_count >= CLEAN_REPORTS_FOR_INCREASE:
                left = self._hold_down_left("up")
                if left > 0:
                    self.suppressed["hold_down"] += 1
                    e = self._set_state(HOLD_DOWN, "increase_in_hold_down")
                    return events + ([e] if e else [])
                target = next(k for k in LADDER_KBPS if k > self.level_kbps)
                return events + [self._act("up", "RECOVERY", target,
                                           {"clean_reports": self.clean_count}, int(elapsed))]
            e = self._set_state(RECOVERY_PROBATION, "counting_clean_reports")
            return events + ([e] if e else [])

        pressure_like = (self._num(s["fps"]) is not None and self._num(s["fps"]) < ROUTINE_FPS_BELOW)
        if pressure_like:
            e = self._set_state(PRESSURE, "pressure_sample", m)
        else:
            e = self._set_state(REFERENCE, "clean" if self._is_clean(s) else "no_evidence")
        return events + ([e] if e else [])

    def status(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "reason": self.reason,
            "reason_measurements": self.measurements,
            "shadow_level_kbps": self.level_kbps,
            "decision_sequence": self.decision_seq,
            "reports_evaluated": self.reports,
            "blackout_remaining_reports": self.blackout_remaining,
            "hold_down_remaining_reports": {
                "down": self._hold_down_left("down"),
                "up": self._hold_down_left("up"),
            },
            "clean_sample_count": self.clean_count,
            "would_act": dict(self.would_act),
            "suppressed": dict(self.suppressed),
            "telemetry_stale_events": self.stale_events,
            "oscillation_hold": self.oscillation_hold,
        }


class AdaptiveBitrateShadow:
    """The companion wrapper: mode, the decision log, the status field."""

    def __init__(self, project_root: Path, environ: dict[str, str] | None = None) -> None:
        self.mode, self.mode_env_ignored = mode_from_env(environ)
        self.log_path = Path(project_root) / "logs" / "games" / LOG_NAME
        self._lock = threading.Lock()
        self._policy = ShadowPolicy()
        self._last_observed_unix_ms: int | None = None
        self._stream_kbps: int | None = None
        self._log_errors = 0

    def observe(self, telemetry: dict[str, Any], stream_bitrate_kbps: int | None = None) -> None:
        """Called once per accepted client report. Never raises, never acts."""
        if self.mode != "shadow":
            return
        try:
            s = _sample(telemetry)
            with self._lock:
                self._last_observed_unix_ms = int(time.time() * 1000)
                if stream_bitrate_kbps:
                    self._stream_kbps = int(stream_bitrate_kbps)
                events = self._policy.feed(s)
                if events:
                    base = {"schema": SCHEMA, "mode": self.mode, "acted": False,
                            "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                            "session_elapsed_ms": s.get("elapsed_ms"),
                            "stream_kbps": self._stream_kbps,
                            "shadow_level_kbps": self._policy.level_kbps,
                            "state": self._policy.state,
                            "sample": {k: s.get(k) for k in ("fps", "queue_depth", "output_gap_ms",
                                                             "waiting_for_idr", "lost_packets_delta")}}
                    for e in events:
                        self._write({**base, **e})
        except Exception:
            # The shadow must never disturb the stream or the health path.
            pass

    def _write(self, row: dict[str, Any]) -> None:
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            if rotate_if_needed is not None:
                rotate_if_needed(self.log_path, max_bytes=LOG_MAX_BYTES, keep=LOG_KEEP)
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, separators=(",", ":")) + "\n")
        except OSError:
            self._log_errors += 1

    def status(self) -> dict[str, Any]:
        out: dict[str, Any] = {"schema": SCHEMA, "mode": self.mode, "acted": False}
        if self.mode_env_ignored:
            out["mode_env_ignored"] = True
        if self.mode != "shadow":
            return out
        with self._lock:
            age = (None if self._last_observed_unix_ms is None
                   else max(0, int(time.time() * 1000) - self._last_observed_unix_ms))
            out.update({
                "trigger_classes": ["FALLBACK", "ROUTINE"],
                "current_kbps": self._stream_kbps,
                "validated_ladder_kbps": list(LADDER_KBPS),
                "reference_kbps": REFERENCE_KBPS,
                "telemetry_age_ms": age,
                "telemetry_stale_now": age is not None and age > STALE_NON_DISTINCT_REPORTS * REPORT_INTERVAL_MS,
                "log_errors": self._log_errors,
                **self._policy.status(),
            })
        return out


_INSTANCE: AdaptiveBitrateShadow | None = None
_INSTANCE_LOCK = threading.Lock()


def get_shadow(project_root: Path) -> AdaptiveBitrateShadow:
    """One per companion process; the mode is read once, at first use."""
    global _INSTANCE
    with _INSTANCE_LOCK:
        if _INSTANCE is None:
            _INSTANCE = AdaptiveBitrateShadow(project_root)
        return _INSTANCE
