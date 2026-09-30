"""C3-L4-L1: the adaptive-bitrate LIVE mode -- the controller acts.

Authorized by `docs/memory/decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`:
one `video_only_restart` per adaptation event, straight to the target (the
ladder chooses the target, it is never stepped through), the existing
hold-downs as the minimum spacing, the blackout kept. Design and mapping
table: `docs/memory/evidence/c3_l4_l1_2026-09-28/c3_l4_l1_design.txt`;
architecture: `ADAPTIVE_BITRATE.md` section "C3.L4 live mode -- as built".

`adaptive_bitrate.py` (the shadow) is not changed: it still accepts only
`off` and `shadow`, holds no actuator, and its test suite is unchanged. This
module owns the third value of `PRIVYHUB_ADAPTIVE_BITRATE_MODE`:

  off / shadow / unrecognised -- exactly the shadow module's behaviour;
  live -- every fresh, distinct client report is evaluated by `LivePolicy`
          (the shadow's evidence rules, the live mapping table below) and a
          transition it names is carried out through the SAME actuator the
          loopback `c3-validated-bitrate-transition` route calls
          (`NativeStreamManager.diagnostic_c3_validated_bitrate_transition`).

Kill switches: unset the flag + restart the unit = off; at runtime
`POST /plugins/games/adaptive-bitrate/disable` switches the controller to
shadow behaviour for the rest of the session (idempotent; there is no enable
route). Test-only: `PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1` with live enables
`POST /plugins/games/adaptive-bitrate/inject?class=FALLBACK|ROUTINE`.

Serialization with link-drop recovery: the actuator runs on one worker
thread while holding `NativeStreamManager._lock` -- the lock recovery's own
restart (`recovery_restart_encoder`, C3-F1) and full start take -- and the
recovery state is re-read under that lock immediately before the restart;
anything but PLAYING aborts the transition. So a controller transition and a
recovery restart never overlap, and a recovery restart that follows one runs
at the new level (C3-F1 is level-preserving).
"""

from __future__ import annotations

import contextlib
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import adaptive_bitrate as ab

try:  # the reference profile's id; a pure module, safe for the unit tests
    from native_stream_profiles import NATIVE_GAME_720P60_REFERENCE as _REFERENCE_PROFILE
    REFERENCE_PROFILE_ID = _REFERENCE_PROFILE.id
except Exception:  # pragma: no cover
    REFERENCE_PROFILE_ID = "native_game_720p60_reference"


MODE_ENV = ab.MODE_ENV
INJECT_ENV = "PRIVYHUB_ADAPTIVE_BITRATE_INJECT"
LIVE = "live"
MODES = ("off", "shadow", LIVE)
SCHEMA = ab.SCHEMA                       # the same log, the same schema; rows say mode live

LADDER_KBPS = ab.LADDER_KBPS             # 5000 / 5500 / 6000 / 7000
REFERENCE_KBPS = ab.REFERENCE_KBPS
REPORT_INTERVAL_MS = ab.REPORT_INTERVAL_MS

# --- THE mapping table (design note §2; one table, nowhere else) -----------
# A decrease names its target from the trigger's severity and reaches it in
# ONE transition; an increase is one rung per event.
TARGET_KBPS = {"FALLBACK": 5000, "ROUTINE": 6000}

# Hold-downs: reports since the last transition before the next one of this
# kind may fire, by the direction of that last transition. At the 2 s cadence:
# 30 = 60 s, 60 = 120 s. An increase needs, in addition, 90 consecutive clean
# reports counted after the blackout (>= 93 reports = 186 s since the last).
HOLDDOWN_REPORTS = {
    ("FALLBACK", "down"): 30, ("FALLBACK", "up"): 60,
    ("ROUTINE", "down"): 60, ("ROUTINE", "up"): 60,
    ("INCREASE", "up"): 30, ("INCREASE", "down"): 60,
}
BLACKOUT_REPORTS = ab.BLACKOUT_REPORTS                    # 3 reports, after ANY SSRC change
CLEAN_REPORTS_FOR_INCREASE = ab.CLEAN_REPORTS_FOR_INCREASE  # 90
MIN_SESSION_AGE_MS = 60_000
RATE_LIMIT_TRANSITIONS = 4
RATE_LIMIT_WINDOW_MS = 10 * 60 * 1000
# On a queue-driven onset ROUTINE's 4-of-5 is met one report before
# FALLBACK's 5-of-5 (S1). While the newest report is itself below FALLBACK's
# fps line, ROUTINE waits up to this many reports for FALLBACK to decide, so
# one failure is one transition (to 5000), not 6000 and then 5000.
ROUTINE_ESCALATION_DEFER_REPORTS = 4

ACTUATING = "ACTUATING"
DISABLED = "DISABLED"


def mode_from_env(environ: dict[str, str] | None = None) -> tuple[str, bool]:
    """(mode, ignored) over off / shadow / live; anything else is off, flagged."""
    raw = (environ if environ is not None else os.environ).get(MODE_ENV)
    if raw is None or raw.strip() == "":
        return "off", False
    value = raw.strip().lower()
    if value in MODES:
        return value, False
    return "off", True


def inject_from_env(environ: dict[str, str] | None = None) -> bool:
    return ((environ if environ is not None else os.environ).get(INJECT_ENV) or "").strip() == "1"


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class LivePolicy(ab.ShadowPolicy):
    """The live decision path: the shadow's evidence, the live mapping, the
    constraints of the C3-L4-L1 task. Pure: no clock, no I/O, no actuator.

    `feed(sample, ctx)` returns events; a `transition` event with `acted`
    true is a request the wrapper must carry out and confirm with
    `actuation_done()`. `ctx` carries the stream's real level
    (`stream_kbps`), the guard inputs (`guards`: name -> ok) and a clock
    (`clock_ms`, the client's elapsed when absent, as in the replays).
    """

    def __init__(self) -> None:
        # Companion-session scope (survives a client-side elapsed reset;
        # cleared by end_session()).
        self.transition_times_ms: list[int] = []
        self.transitions = 0
        self.acting = True
        self.actuator_failed = False
        self.rate_limited_events = 0
        self.last_action: dict[str, Any] | None = None
        super().__init__()

    # -- lifecycle ---------------------------------------------------------
    def reset(self, elapsed_ms: int | None, *, level_kbps: int | None = None) -> None:
        super().reset(elapsed_ms)
        if level_kbps in LADDER_KBPS:
            self.level_kbps = int(level_kbps)
        self.pending: dict[str, Any] | None = None
        self.routine_defer = 0
        self.refused: dict[str, int] = {}
        self.last_refusal_key: tuple[str, str] | None = None
        self.rate_limited_now = False

    def end_session(self) -> None:
        """`session_ended`: back to the reference, every timer cleared (C1)."""
        self.transition_times_ms = []
        self.transitions = 0
        self.acting = True
        self.actuator_failed = False
        self.rate_limited_events = 0
        self.last_action = None
        self.reset(None)

    # -- helpers -----------------------------------------------------------
    def hold_left(self, kind: str) -> int:
        if self.reports_since_action is None or self.last_direction is None:
            return 0
        need = HOLDDOWN_REPORTS[(kind, self.last_direction)]
        return max(0, need - self.reports_since_action)

    def holds_in_force(self) -> dict[str, Any]:
        return {"blackout_reports": self.blackout_remaining,
                "fallback_reports": self.hold_left("FALLBACK"),
                "routine_reports": self.hold_left("ROUTINE"),
                "increase_reports": self.hold_left("INCREASE"),
                "clean_reports": self.clean_count,
                "clean_needed": CLEAN_REPORTS_FOR_INCREASE,
                "last_direction": self.last_direction,
                "reports_since_transition": self.reports_since_action}

    def _recent_transitions(self, clock: int) -> list[int]:
        return [t for t in self.transition_times_ms if clock - t < RATE_LIMIT_WINDOW_MS]

    def _refuse(self, kind: str, reason: str, target: int | None, m: dict[str, Any],
                *, injected: bool, state: str, **extra: Any) -> list[dict[str, Any]]:
        self.refused[reason] = self.refused.get(reason, 0) + 1
        prev_state = self.state
        self.state, self.reason, self.measurements = state, reason, m
        key = (kind, reason)
        if key == self.last_refusal_key and not injected:
            return []                      # logged once per (class, reason) run
        self.last_refusal_key = key
        return [{"event": "refused", "class": kind, "reason": reason, "from_kbps": self.level_kbps,
                 "to_kbps": target, "injected": injected, "state_before": prev_state,
                 "holds_in_force": self.holds_in_force(), "measurements": m, "acted": False, **extra}]

    # -- the decision ------------------------------------------------------
    def _decide(self, kind: str, m: dict[str, Any], elapsed: int, ctx: dict[str, Any],
                *, injected: bool = False) -> list[dict[str, Any]]:
        direction = "up" if kind == "INCREASE" else "down"
        if kind == "INCREASE":
            target = next((k for k in LADDER_KBPS if k > self.level_kbps), None)
            if target is None:
                return self._refuse(kind, "at_reference", None, m, injected=injected, state=ab.REFERENCE)
        else:
            target = TARGET_KBPS[kind]

        left = self.hold_left(kind)
        if left > 0:
            return self._refuse(kind, "hold_down", target, m, injected=injected, state=ab.HOLD_DOWN,
                                hold_down_left_reports=left)
        if direction == "down" and target >= self.level_kbps:
            reason = "at_floor" if self.level_kbps <= LADDER_KBPS[0] else "at_or_below_target"
            return self._refuse(kind, reason, target, m, injected=injected, state=ab.PRESSURE)

        guards = dict(ctx.get("guards") or {})
        guards["session_age_60s"] = elapsed >= MIN_SESSION_AGE_MS
        failing = sorted(name for name, ok in guards.items() if not ok)
        if failing:
            return self._refuse(kind, "guard", target, m, injected=injected, state=self.state
                                if self.state != ab.REFERENCE else ab.PRESSURE, guards_failing=failing)

        clock = int(ctx.get("clock_ms", elapsed))
        if self.acting:
            recent = self._recent_transitions(clock)
            if len(recent) >= RATE_LIMIT_TRANSITIONS:
                self.rate_limited_now = True
                self.rate_limited_events += 1
                return self._refuse(kind, "RATE_LIMITED", target, m, injected=injected, state=ab.HOLD_DOWN,
                                    transitions_in_window=len(recent))
        self.rate_limited_now = False

        changes = self.direction_changes
        if self.last_direction is not None and direction != self.last_direction:
            changes = [t for t in self.direction_changes if elapsed - t <= ab.OSCILLATION_WINDOW_MS] + [elapsed]
            if len(changes) >= ab.OSCILLATION_CHANGES:
                self.direction_changes = changes
                self.oscillation_hold = True
                self.suppressed["oscillation"] += 1
                self.window.clear()
                self.clean_count = 0
                self.state, self.reason, self.measurements = ab.HOLD, "oscillation", m
                self.decision_seq += 1
                return [{"event": "hold", "class": kind, "direction": direction, "reason": "oscillation",
                         "would_target_kbps": target, "level_kbps": self.level_kbps,
                         "direction_changes_ms": list(changes), "measurements": m, "acted": False}]
        return self._transition(kind, direction, target, m, changes, clock, injected=injected)

    def _transition(self, kind: str, direction: str, target: int, m: dict[str, Any], changes: list[int],
                    clock: int, *, injected: bool) -> list[dict[str, Any]]:
        holds_before = self.holds_in_force()
        self.decision_seq += 1
        self.would_act["INCREASE" if direction == "up" else kind] += 1
        prev = self.level_kbps
        self.direction_changes = changes
        self.level_kbps = target
        self.last_direction = direction
        self.reports_since_action = 0
        self.blackout_remaining = BLACKOUT_REPORTS
        self.window.clear()
        self.clean_count = 0
        self.routine_defer = 0
        self.last_refusal_key = None
        self.state = ab.HOLD_DOWN
        self.reason = f"{'increase' if direction == 'up' else 'decrease'}_{kind.lower()}"
        self.measurements = m
        row = {"event": "transition" if self.acting else "would_act", "class": kind, "direction": direction,
               "from_kbps": prev, "to_kbps": target, "reason": self.reason, "injected": injected,
               "holds_in_force_before": holds_before, "measurements": m, "acted": self.acting,
               "decision_sequence": self.decision_seq}
        if self.acting:
            self.transitions += 1
            self.transition_times_ms.append(clock)
            self.pending = {"class": kind, "from_kbps": prev, "to_kbps": target,
                            "decision_sequence": self.decision_seq, "injected": injected}
            row["transitions_this_session"] = self.transitions
            row["transitions_in_window"] = len(self._recent_transitions(clock))
        self.last_action = {"class": kind, "direction": direction, "from_kbps": prev, "to_kbps": target,
                            "acted": self.acting, "injected": injected, "decision_sequence": self.decision_seq,
                            "result": "requested" if self.acting else "shadow"}
        return [row]

    # -- one report --------------------------------------------------------
    def feed(self, s: dict[str, Any], ctx: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        ctx = ctx or {}
        events: list[dict[str, Any]] = []
        elapsed = s.get("elapsed_ms")
        if isinstance(elapsed, (int, float)) and self.last_elapsed_ms is not None \
                and elapsed < self.last_elapsed_ms:
            self.reset(int(elapsed), level_kbps=ctx.get("stream_kbps") if self.acting else None)
            events.append({"event": "session_reset", "level_kbps": self.level_kbps})
        stream_kbps = ctx.get("stream_kbps")
        if self.acting and self.pending is None and stream_kbps in LADDER_KBPS \
                and stream_kbps != self.level_kbps:
            # The stream is the truth (a full start resets to 7000, C1).
            events.append({"event": "level_sync", "from_kbps": self.level_kbps, "to_kbps": int(stream_kbps)})
            self.level_kbps = int(stream_kbps)

        if not s.get("available") or not s.get("fresh") or not isinstance(elapsed, (int, float)):
            self.stale_events += 1
            e = self._set_state(ab.TELEMETRY_STALE, "telemetry_unavailable" if not s.get("available")
                                else "telemetry_not_fresh")
            return events + ([e] if e else [])
        if self.last_elapsed_ms is not None and elapsed == self.last_elapsed_ms:
            self.non_distinct += 1
            if self.non_distinct >= ab.STALE_NON_DISTINCT_REPORTS:
                self.stale_events += 1
                e = self._set_state(ab.TELEMETRY_STALE, "no_distinct_snapshot")
                return events + ([e] if e else [])
            return events
        self.non_distinct = 0
        self.last_elapsed_ms = int(elapsed)
        self.reports += 1
        if self.reports_since_action is not None:
            self.reports_since_action += 1

        if self.actuator_failed:
            e = self._set_state(ab.ACTUATOR_FAILED, "actuator_failed")
            return events + ([e] if e else [])
        if self.oscillation_hold:
            e = self._set_state(ab.HOLD, "oscillation")
            return events + ([e] if e else [])
        if self.blackout_remaining > 0:
            self.blackout_remaining -= 1
            self.suppressed["blackout"] += 1
            e = self._set_state(ab.HOLD_DOWN, "blackout")
            return events + ([e] if e else [])
        if s.get("waiting_for_idr"):
            self.clean_count = 0
            e = self._set_state(self.state if self.state != ab.TELEMETRY_STALE else ab.REFERENCE,
                                "resync_ignored")
            return events + ([e] if e else [])

        self.window.append(s)
        self.clean_count = self.clean_count + 1 if self._is_clean(s) else 0
        cls, m = self._evidence()

        if cls == "ROUTINE":
            newest = self._num(s["fps"])
            if newest is not None and newest < ab.FALLBACK_FPS_BELOW \
                    and self.routine_defer < ROUTINE_ESCALATION_DEFER_REPORTS:
                self.routine_defer += 1
                e = self._set_state(ab.PRESSURE, "routine_deferred_escalating", m)
                return events + ([e] if e else [])
        else:
            self.routine_defer = 0

        if cls in ("FALLBACK", "ROUTINE"):
            return events + self._decide(cls, m, int(elapsed), ctx)
        self.last_refusal_key = None

        if self.level_kbps < REFERENCE_KBPS:
            if self.clean_count >= CLEAN_REPORTS_FOR_INCREASE:
                return events + self._decide("INCREASE", {"clean_reports": self.clean_count}, int(elapsed), ctx)
            e = self._set_state(ab.RECOVERY_PROBATION, "counting_clean_reports")
            return events + ([e] if e else [])

        pressure_like = (self._num(s["fps"]) is not None and self._num(s["fps"]) < ab.ROUTINE_FPS_BELOW)
        if pressure_like:
            e = self._set_state(ab.PRESSURE, "pressure_sample", m)
        else:
            e = self._set_state(ab.REFERENCE, "clean" if self._is_clean(s) else "no_evidence")
        return events + ([e] if e else [])

    # -- inputs from outside the report stream -------------------------------
    def inject(self, kind: str, ctx: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Test-only: one synthetic degraded report of `kind`, decided as the
        evidence window would decide it -- every gate applies unchanged."""
        ctx = ctx or {}
        m = {"injected": True, "class": kind}
        elapsed = int(self.last_elapsed_ms or 0)
        if self.pending is not None:
            return self._refuse(kind, "actuating", TARGET_KBPS[kind], m, injected=True, state=self.state)
        if self.actuator_failed:
            return self._refuse(kind, "actuator_failed", TARGET_KBPS[kind], m, injected=True,
                                state=ab.ACTUATOR_FAILED)
        if self.oscillation_hold:
            return self._refuse(kind, "oscillation", TARGET_KBPS[kind], m, injected=True, state=ab.HOLD)
        if self.blackout_remaining > 0:
            return self._refuse(kind, "blackout", TARGET_KBPS[kind], m, injected=True, state=ab.HOLD_DOWN)
        return self._decide(kind, m, elapsed, ctx, injected=True)

    def actuation_done(self, ok: bool, *, actual_kbps: int | None, aborted: bool = False) -> list[dict[str, Any]]:
        pend, self.pending = self.pending, None
        if pend is None:
            return []
        if ok:
            # The SSRC changed now: the blackout counts from here.
            self.blackout_remaining = BLACKOUT_REPORTS
            self.window.clear()
            self.clean_count = 0
            if self.last_action is not None:
                self.last_action["result"] = "applied"
            return []
        if self.last_action is not None:
            self.last_action["result"] = "aborted" if aborted else "failed"
        if actual_kbps in LADDER_KBPS:
            self.level_kbps = int(actual_kbps)
        if aborted:
            # Recovery took the stream between the decision and the restart:
            # not an actuator failure; no transition happened.
            self.transitions = max(0, self.transitions - 1)
            if self.transition_times_ms:
                self.transition_times_ms.pop()
            return []
        self.actuator_failed = True
        self.state, self.reason = ab.ACTUATOR_FAILED, "actuator_failed"
        return []

    def note_ssrc_change(self, source: str) -> list[dict[str, Any]]:
        """Recovery restarted the encoder (or a full start ran): blackout."""
        self.blackout_remaining = BLACKOUT_REPORTS
        self.window.clear()
        self.clean_count = 0
        self.routine_defer = 0
        return [{"event": "ssrc_change", "source": source, "blackout_reports": BLACKOUT_REPORTS}]

    def status(self) -> dict[str, Any]:
        out = super().status()
        out.pop("shadow_level_kbps", None)
        out.update({
            "level_kbps": self.level_kbps,
            "transitions_this_session": self.transitions,
            "rate_limited": self.rate_limited_now,
            "rate_limited_events": self.rate_limited_events,
            "last_action": dict(self.last_action) if self.last_action else None,
            "hold_down_remaining_reports": {
                "fallback": self.hold_left("FALLBACK"),
                "routine": self.hold_left("ROUTINE"),
                "increase": self.hold_left("INCREASE"),
            },
            "refused": dict(self.refused),
            "actuator_failed": self.actuator_failed,
            "pending": dict(self.pending) if self.pending else None,
        })
        return out


class LiveController:
    """The companion wrapper for live mode: guards, the actuator worker, the
    decision log, the status field, the disable and inject routes."""

    def __init__(self, project_root: Path, environ: dict[str, str] | None = None) -> None:
        self.configured_mode = LIVE
        self.inject_enabled = inject_from_env(environ)
        self.log_path = Path(project_root) / "logs" / "games" / ab.LOG_NAME
        self._lock = threading.RLock()
        self._policy = LivePolicy()
        self._actuator: Callable[[int], dict[str, Any]] | None = None
        self._context: Callable[[], dict[str, Any]] | None = None
        self._serial_lock: Any = None
        self._recovery_state: Callable[[], str | None] | None = None
        self._inflight: dict[str, Any] | None = None
        self._stream_kbps: int | None = None
        self._last_observed_unix_ms: int | None = None
        self._last_sample: dict[str, Any] | None = None
        self._last_native_status: dict[str, Any] | None = None
        self._dropped_while_actuating = 0
        self.disabled = False
        self.disabled_at_utc: str | None = None
        self._log_errors = 0
        self._write({"event": "controller_start", "configured_mode": LIVE,
                     "inject_enabled": self.inject_enabled})

    # -- wiring (the games plugin, once) -----------------------------------
    def bind(self, *, actuator: Callable[[int], dict[str, Any]], context: Callable[[], dict[str, Any]],
             serial_lock: Any, recovery_state: Callable[[], str | None]) -> None:
        with self._lock:
            self._actuator = actuator
            self._context = context
            self._serial_lock = serial_lock
            self._recovery_state = recovery_state

    @property
    def effective_mode(self) -> str:
        return "shadow" if self.disabled else LIVE

    # -- the report path ---------------------------------------------------
    def _ctx(self, native_status: dict[str, Any] | None) -> dict[str, Any]:
        ns = native_status or {}
        extra: dict[str, Any] = {}
        if self._context is not None:
            try:
                extra = self._context() or {}
            except Exception:
                extra = {}
        profile = ns.get("profile") or {}
        overrides = ns.get("encoder_overrides") or {}
        guards = {
            "stream_active": bool(ns.get("active")),
            "game_active": bool(extra.get("game_active")),
            "game_not_paused": extra.get("game_paused") is False,
            "recovery_playing": extra.get("recovery_state") == "PLAYING",
            "reference_profile": (ns.get("profile_id") == REFERENCE_PROFILE_ID
                                  and profile.get("bitrate_kbps") == REFERENCE_KBPS),
            "no_override": overrides.get("any_override") is False,
            "actuator_bound": self._actuator is not None,
        }
        return {"stream_kbps": ns.get("bitrate_kbps"), "guards": guards,
                "clock_ms": int(time.monotonic() * 1000)}

    def observe(self, telemetry: dict[str, Any], stream_bitrate_kbps: int | None = None,
                native_status: dict[str, Any] | None = None) -> None:
        """Called once per accepted client report. Never raises."""
        try:
            s = ab._sample(telemetry)
            with self._lock:
                self._last_observed_unix_ms = int(time.time() * 1000)
                if stream_bitrate_kbps:
                    self._stream_kbps = int(stream_bitrate_kbps)
                self._last_native_status = native_status
                if self._inflight is not None:
                    # The restart is being measured, not the network.
                    self._dropped_while_actuating += 1
                    return
                self._last_sample = s
                ctx = self._ctx(native_status)
                events = self._policy.feed(s, ctx)
                self._emit(events, s, ctx)
                self._maybe_actuate()
        except Exception:
            pass

    def _emit(self, events: list[dict[str, Any]], s: dict[str, Any] | None,
              ctx: dict[str, Any] | None = None) -> None:
        for e in events:
            if e.get("event") == "state" and e.get("from") == e.get("to"):
                continue                   # S1 finding 1: state changes and decisions only
            row = {"session_elapsed_ms": (s or {}).get("elapsed_ms"),
                   "stream_kbps": self._stream_kbps,
                   "level_kbps": self._policy.level_kbps,
                   "state": self._policy.state,
                   "effective_mode": self.effective_mode}
            if s is not None:
                row["sample"] = {k: s.get(k) for k in ("fps", "queue_depth", "output_gap_ms",
                                                       "waiting_for_idr", "lost_packets_delta")}
            if ctx is not None and e.get("event") in ("transition", "refused", "would_act", "hold"):
                row["guards"] = ctx.get("guards")
            row.update(e)
            self._write(row)

    # -- the actuator --------------------------------------------------------
    def _maybe_actuate(self) -> None:
        pend = self._policy.pending
        if pend is None or self._inflight is not None:
            return
        self._inflight = dict(pend)
        threading.Thread(target=self._actuate, args=(dict(pend),),
                         name="PrivyHub-AdaptiveBitrate-Live", daemon=True).start()

    def _actuate(self, pend: dict[str, Any]) -> None:
        started = time.monotonic()
        ok, aborted, err, result = False, False, None, None
        recovery_state = None
        try:
            lock = self._serial_lock if self._serial_lock is not None else contextlib.nullcontext()
            with lock:
                # The recovery interlock, re-read under the stream lock.
                recovery_state = self._recovery_state() if self._recovery_state else None
                if recovery_state != "PLAYING":
                    aborted, err = True, f"recovery_state_{recovery_state}"
                elif self._actuator is None:
                    aborted, err = True, "actuator_not_bound"
                else:
                    result = self._actuator(int(pend["to_kbps"]))
                    ok = bool(isinstance(result, dict) and result.get("ok", True))
                    if not ok:
                        err = "actuator_returned_not_ok"
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
        took_ms = round((time.monotonic() - started) * 1000.0, 1)
        video = (result or {}).get("video") if isinstance(result, dict) else None
        with self._lock:
            actual = None
            if isinstance(result, dict) and ok:
                actual = result.get("target_bitrate_kbps", pend["to_kbps"])
            elif isinstance(result, dict):
                actual = result.get("from_bitrate_kbps")
            if actual is None and not ok:
                actual = pend["from_kbps"] if aborted else None
            self._policy.actuation_done(ok, actual_kbps=actual, aborted=aborted)
            if ok:
                self._stream_kbps = int(actual) if actual else self._stream_kbps
            self._inflight = None
            self._write({"event": "transition_done" if ok else ("transition_aborted" if aborted
                                                                 else "actuator_failed"),
                         "acted": ok, "class": pend.get("class"), "from_kbps": pend.get("from_kbps"),
                         "to_kbps": pend.get("to_kbps"), "injected": pend.get("injected"),
                         "decision_sequence": pend.get("decision_sequence"),
                         "actuation_ms": took_ms, "recovery_state_at_restart": recovery_state,
                         "error": err, "level_kbps": self._policy.level_kbps,
                         "state": self._policy.state, "effective_mode": self.effective_mode,
                         "cycle": ({k: video.get(k) for k in ("first_rtp_resume_ms", "ffmpeg_spawn_ms",
                                                               "rtp_silence_after_spawn_ms", "host_verified_ms")}
                                   if isinstance(video, dict) else None),
                         "blackout_reports": self._policy.blackout_remaining})
            if self._policy.last_action is not None:
                self._policy.last_action.update({"actuation_ms": took_ms, "at_utc": _now_utc(),
                                                 "error": err})

    # -- lifecycle hooks (the games plugin) --------------------------------
    def note_recovery_restart(self, source: str) -> None:
        """Recovery's restart (C3-F1) or full start changed the SSRC."""
        try:
            with self._lock:
                self._emit(self._policy.note_ssrc_change(source), None)
        except Exception:
            pass

    def session_ended(self) -> None:
        try:
            with self._lock:
                was = {"transitions_this_session": self._policy.transitions,
                       "level_kbps": self._policy.level_kbps, "disabled": self.disabled}
                self._policy.end_session()
                self.disabled = False
                self.disabled_at_utc = None
                self._write({"event": "session_ended_reset", "before": was,
                             "level_kbps": self._policy.level_kbps})
        except Exception:
            pass

    # -- routes --------------------------------------------------------------
    def disable(self) -> dict[str, Any]:
        """Switch to shadow behaviour for the rest of the session. Idempotent."""
        with self._lock:
            already = self.disabled
            if not already:
                self.disabled = True
                self.disabled_at_utc = _now_utc()
                self._policy.acting = False
                self._write({"event": "disabled", "effective_mode": "shadow",
                             "level_kbps": self._policy.level_kbps,
                             "inflight": dict(self._inflight) if self._inflight else None})
            return {"ok": True, "already_disabled": already, "effective_mode": "shadow",
                    "disabled_at_utc": self.disabled_at_utc,
                    "note": "live resumes only with a new session; unset the flag and restart the unit for off"}

    def inject(self, kind: str) -> tuple[int, dict[str, Any]]:
        if not self.inject_enabled:
            return 403, {"ok": False, "error": f"{INJECT_ENV}=1 is not set"}
        if kind not in TARGET_KBPS:
            return 400, {"ok": False, "error": "class must be FALLBACK or ROUTINE"}
        with self._lock:
            if self.disabled:
                return 403, {"ok": False, "error": "live mode is disabled for this session"}
            ctx = self._ctx(self._last_native_status)
            events = self._policy.inject(kind, ctx)
            self._write({"event": "inject", "class": kind, "at_elapsed_ms": self._policy.last_elapsed_ms})
            self._emit(events, self._last_sample, ctx)
            self._maybe_actuate()
            return 200, {"ok": True, "class": kind, "events": events,
                         "level_kbps": self._policy.level_kbps, "state": self._policy.state}

    # -- log / status ----------------------------------------------------------
    def _write(self, row: dict[str, Any]) -> None:
        base = {"schema": SCHEMA, "mode": LIVE, "at_utc": _now_utc(), "acted": False}
        base.update(row)
        try:
            import json
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            if ab.rotate_if_needed is not None:
                ab.rotate_if_needed(self.log_path, max_bytes=ab.LOG_MAX_BYTES, keep=ab.LOG_KEEP)
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(base, separators=(",", ":")) + "\n")
        except OSError:
            self._log_errors += 1

    def status(self) -> dict[str, Any]:
        with self._lock:
            age = (None if self._last_observed_unix_ms is None
                   else max(0, int(time.time() * 1000) - self._last_observed_unix_ms))
            p = self._policy.status()
            out: dict[str, Any] = {
                "schema": SCHEMA,
                "mode": self.effective_mode,
                "configured_mode": LIVE,
                "acts": not self.disabled,
                "acted": bool(self._policy.transitions),
                "disabled": self.disabled,
                "disabled_at_utc": self.disabled_at_utc,
                "state": ACTUATING if self._inflight else p["state"],
                "level": self._stream_kbps if self._stream_kbps else p["level_kbps"],
                "last_action": p["last_action"],
                "transitions_this_session": p["transitions_this_session"],
                "rate_limited": p["rate_limited"],
                "current_kbps": self._stream_kbps,
                "validated_ladder_kbps": list(LADDER_KBPS),
                "reference_kbps": REFERENCE_KBPS,
                "target_kbps_by_class": dict(TARGET_KBPS),
                "telemetry_age_ms": age,
                "reports_dropped_while_actuating": self._dropped_while_actuating,
                "log_errors": self._log_errors,
                "policy": p,
            }
            if self.inject_enabled:
                out["inject_enabled"] = True
            return out


_INSTANCE: Any = None
_INSTANCE_LOCK = threading.Lock()


def get_controller(project_root: Path) -> Any:
    """One per companion process; the mode is read once, at first use.

    `live` -> the LiveController; anything else -> the shadow module's own
    instance, exactly as before this module existed.
    """
    global _INSTANCE
    with _INSTANCE_LOCK:
        if _INSTANCE is None:
            mode, _ = mode_from_env()
            _INSTANCE = LiveController(project_root) if mode == LIVE else ab.get_shadow(project_root)
        return _INSTANCE


def is_live(controller: Any) -> bool:
    return isinstance(controller, LiveController)


LOOPBACK = {"127.0.0.1", "::1"}


def handle_route(project_root: Path, verb: str, query: str, client_ip: str) -> tuple[int, dict[str, Any]]:
    """POST /plugins/games/adaptive-bitrate/<verb> -> (HTTP status, payload).

    disable -- any caller; idempotent; live -> shadow for the rest of the
               session. In off / shadow there is nothing to disable (200).
    inject  -- test-only; 403 unless the caller is loopback, the inject flag
               is set and the mode is live (and not disabled).
    """
    from urllib.parse import parse_qs

    controller = get_controller(project_root)
    if verb == "disable":
        if not is_live(controller):
            return 200, {"ok": True, "already_disabled": True, "effective_mode": controller.mode,
                         "note": "the controller is not in live mode"}
        return 200, controller.disable()
    if verb == "inject":
        if client_ip not in LOOPBACK:
            return 403, {"ok": False, "error": "inject is loopback-only"}
        if not is_live(controller):
            return 403, {"ok": False, "error": f"{MODE_ENV}=live is not set"}
        kind = (parse_qs(query or "").get("class", [""])[0] or "").strip().upper()
        return controller.inject(kind)
    return 404, {"ok": False, "error": "unknown adaptive-bitrate route (disable, inject)"}
