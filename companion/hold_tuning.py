"""B6: the input hold's trigger, cap rule and resume, from BENCH-R1's data.

`PRIVYHUB_INPUT_HOLD_B6=1`, read only when `PRIVYHUB_INPUT_HOLD` is set and valid (B2). **Absent = B2 + B4 byte for
byte**: nothing imports this module. Design: `docs/memory/evidence/b6_2026-10-22/design_written_before_code.md`
(hashed before this code); the data: `gap_distribution.md`.

- `1` / `on` mean H = 950 ms (the smallest H with <= 1 gap >= H per 10 min on each clean session on file); numbers
  stay numbers.
- B4's rewind cap default (no `_CAP` given): max(30, round(H / 16.7) + 5), <= 120 (62 at 950).
- The cap counts only holds released by input; 6 in 60 s disarm the hold for 10 s.
- The resume: a hold that v2's `controller_silence` took over resumes at the first heartbeat after the link's
  return that shows the client's output fresh (`hold_return`); a hold a client trigger took over is left to the
  client's gate (its full-screen black overlay); a client `ready` within 20 s of a hold-originated resume ends that
  recovery instead of starting a session. One owner: the recovery calls these from its own methods.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Callable, Mapping

FLAG_ENV = "PRIVYHUB_INPUT_HOLD_B6"
HOLD_ENV = "PRIVYHUB_INPUT_HOLD"
REWIND_CAP_ENV = "PRIVYHUB_INPUT_HOLD_REWIND_CAP"
H_DEFAULT_MS = 950
CAP_RELEASED = 6            # released holds ...
CAP_WINDOW_S = 60.0         # ... in a rolling 60 s ...
DISARM_S = 10.0             # ... disarm the hold this long
READY_AFTER_HOLD_S = 20.0   # the client's gate times out at 15 s
OUTPUT_FRESH_MS = 300       # v2's EXIT_OUTPUT_AGE_MS
FRAME_MS = 16.7


def enabled(environ: Mapping[str, str]) -> tuple[bool, str | None]:
    raw = (environ.get(FLAG_ENV) or "").strip()
    if not raw:
        return False, None
    if raw != "1":
        return False, f"ignored: {raw[:32]!r} is not 1"
    import input_hold
    if input_hold.parse(environ.get(HOLD_ENV))[0] is None:
        return False, "ignored: the hold is not active (PRIVYHUB_INPUT_HOLD absent or invalid)"
    return True, None


def hold_ms(environ: Mapping[str, str]) -> int | None:
    """The H in effect with B6 on: `1` / `on` = 950, a number = itself."""
    import input_hold
    raw = (environ.get(HOLD_ENV) or "").strip().lower()
    ms, _ = input_hold.parse(raw)
    if ms is None:
        return None
    return H_DEFAULT_MS if raw in ("1", "on") else ms


def rewind_cap_default(environ: Mapping[str, str]) -> int | None:
    """B4's cap when B6 is on and no `_CAP` is given; None = leave B4's own."""
    if not enabled(environ)[0] or (environ.get(REWIND_CAP_ENV) or "").strip():
        return None
    h = hold_ms(environ) or H_DEFAULT_MS
    return min(120, max(30, int(round(h / FRAME_MS)) + 5))


class Tuning:
    def __init__(self, hold_ms_value: int, clock: Callable[[], float] = time.monotonic):
        self.hold_ms = hold_ms_value
        self._clock = clock
        self._released: deque[float] = deque()
        self._disarmed_until = 0.0
        self._hold_key: float | None = None
        self._return_at: float | None = None
        self._ready_window_until = 0.0
        self.disarms = 0

    # --- the detector (InputHoldDetector.on_quiet, B2's logic with B6's cap) -----------------------------------

    def on_quiet(self, det: Any, now: float, last_any_packet_at: float) -> None:
        if det.held or last_any_packet_at <= 0.0 or now - last_any_packet_at < det.hold_s:
            return
        if last_any_packet_at <= det._silence_start:
            return                                    # this silence was already counted (held or disarmed)
        det._silence_start = last_any_packet_at
        if now < self._disarmed_until:
            det.capped += 1
            return
        det.held = True
        det.holds += 1
        det._emit(("hold", round((now - last_any_packet_at) * 1000.0, 1)))

    def _count_release(self, recovery: Any, now: float) -> None:
        while self._released and now - self._released[0] >= CAP_WINDOW_S:
            self._released.popleft()
        self._released.append(now)
        if len(self._released) >= CAP_RELEASED:
            self._disarmed_until = now + DISARM_S
            self._released.clear()
            self.disarms += 1
            recovery._log("input_hold_cap", rule="b6", released_holds=CAP_RELEASED, cap_window_s=CAP_WINDOW_S,
                          disarm_s=DISARM_S)

    # --- the recovery's own methods -------------------------------------------------------------------------------

    def note_hold(self, recovery: Any) -> None:
        """After note_input_hold's pause: the episode key, when the pause stands as the hold's."""
        with recovery._lock:
            if recovery._state == "PAUSED_RECOVERING" and recovery._last_desync_reason == "input_hold":
                self._hold_key = recovery._state_since
                self._return_at = None

    def note_release(self, recovery: Any) -> None:
        """At note_input_release's top (the first controller packet back after a hold)."""
        now = self._clock()
        with recovery._lock:
            state, reason, key = recovery._state, recovery._last_desync_reason, recovery._state_since
        if state != "PAUSED_RECOVERING" or key != self._hold_key:
            return
        if reason == "input_hold":
            self._count_release(recovery, now)          # a true hold, released by input
            self._ready_window_until = now + READY_AFTER_HOLD_S
        elif reason == "controller_silence":
            self._return_at = now                       # R1 armed: resume at the first fresh heartbeat after this
            recovery._log("hold_return_armed", via="input_release")

    def maybe_resume(self, recovery: Any, now: float) -> bool:
        """R1, from the recovery's monitor: True when this resumed the game."""
        with recovery._lock:
            if (recovery._state != "PAUSED_RECOVERING" or recovery._last_desync_reason != "controller_silence"
                    or self._return_at is None or recovery._state_since != self._hold_key):
                return False
            back = self._return_at
            if not recovery._heartbeat_history:
                return False
            hb_at, hb_age = recovery._heartbeat_history[-1]
            if hb_at <= back or not 0 <= hb_age <= OUTPUT_FRESH_MS:
                return False
            self._return_at = None
        rw = getattr(recovery, "_input_hold_rewind", None)
        if rw is not None:
            rw.rewind(recovery, "hold_return")
        error = ""
        try:
            recovery._resume_game()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        with recovery._lock:
            if recovery._state != "PAUSED_RECOVERING":
                return False
            if error:
                recovery._log("hold_return_failed", resume_error=error)
                return False                            # v2's exit (or the give-up) still applies
            recovering_ms = int((now - recovery._state_since) * 1000.0)
            recovery._state = "PLAYING"
            recovery._state_since = time.monotonic()
            from games.link_drop_recovery import RESTART_BACKOFF_MS
            recovery._restart_backoff_ms = RESTART_BACKOFF_MS
            recovery._last_restart_at = None
            recovery._client_present_since = time.monotonic()
            recovery._exit_ok_since = None
            recovery._exit_packets_back_at = None
            self._ready_window_until = self._clock() + READY_AFTER_HOLD_S
            recovery._log("resumed", from_state="PAUSED_RECOVERING", recovering_ms=recovering_ms,
                          restarts=recovery._restarts, via="hold_return", output_age_ms=hb_age,
                          packets_back_to_resume_ms=int((now - back) * 1000.0))
            return True

    def ready_after_hold(self, recovery: Any) -> bool:
        """R3, at note_gameplay_released's top: a late client ready after a hold-originated resume."""
        now = self._clock()
        with recovery._lock:
            if recovery._state != "PLAYING" or now >= self._ready_window_until:
                return False
            self._ready_window_until = 0.0
            recovery._log("client_ready_after_hold", within_s=READY_AFTER_HOLD_S)
            return True


def wire(recovery: Any, controller: Any, environ: Mapping[str, str]) -> Tuning | None:
    """The plugin's one call, after B2's and B4's wires: H, the detector's cap, the recovery's hooks, B4's cap."""
    on, why = enabled(environ)
    if not on:
        if why:
            recovery._log("input_hold_b6_config", ignored=True, reason=why)
        return None
    det = getattr(controller, "_input_hold", None)
    if det is None:
        recovery._log("input_hold_b6_config", ignored=True, reason="ignored: no hold detector")
        return None
    h = hold_ms(environ) or H_DEFAULT_MS
    det.hold_s = h / 1000.0
    t = Tuning(h)
    det.tuning = t
    recovery._input_hold_b6 = t
    rcap = rewind_cap_default(environ)
    rw = getattr(recovery, "_input_hold_rewind", None)
    if rw is not None and rcap is not None:
        rw.cap = rcap
    recovery._log("input_hold_b6_config", ignored=False, hold_ms=h, cap_released=CAP_RELEASED,
                  cap_window_s=CAP_WINDOW_S, disarm_s=DISARM_S, rewind_cap=(rw.cap if rw is not None else None),
                  ready_after_hold_s=READY_AFTER_HOLD_S)
    return t
