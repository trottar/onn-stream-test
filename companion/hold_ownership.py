"""B8: the hold / stall ownership at the link's return -- what the one owner remembers.

`PRIVYHUB_INPUT_HOLD_B8=1`, active only with the hold (`PRIVYHUB_INPUT_HOLD`), B6 (`PRIVYHUB_INPUT_HOLD_B6=1`) and the
stall signal (`PRIVYHUB_STALL_SIGNAL`) wired. **Absent = BENCH-R2's code byte for byte**: nothing imports this module.
Design: `docs/memory/evidence/b8_2026-10-22/design_written_before_code.md` (hashed before this code).

BENCH-R2 b1: on a `@both` blackout the hold paused at ~950 ms; at the link's return the client's stall took the pause
over (B2's handover); the client's gate `ready` then resumed it without B4's rewind, and a gate-bit stall paused it
again, so only that second pause's 1-4 frames were rewound and the resume came 2-4 s after the return. Here:
- the episode: a hold's pause (its key = the owner's `_state_since`);
- the handover carries the hold's pending rewind: its onset moves to the client's last displayed frame when that is
  earlier, so the rewind requests the pre-hold frames + the stall's own (`input_hold_carry`);
- the return (the first controller packet back) arms the resume at the first heartbeat after it that shows the
  client's output fresh (`resumed via hold_return_stall`), without waiting for a second stall or the client's gate;
  a client ready that lands first resumes with the same rewind (`via client_ready_hold`, in the plugin's ready
  action before its own resume: B4's method needs the core paused);
- after the resume, gate-bit stalls over fresh output are the client's overlay, not a drop (ignored); the late
  `stall_end` is a logged no-op (`stall_end_late`); a stall with a stale output still acts as B7.
One owner: recovery v2's state machine; B8 is called from its own methods and B7's worker.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping

FLAG_ENV = "PRIVYHUB_INPUT_HOLD_B8"
REWIND_CAP_ENV = "PRIVYHUB_INPUT_HOLD_REWIND_CAP"
CAP_EXTRA = 10              # the client's frames before the silence's onset (b1: ~70 ms = 4) + margin
EPISODE_S = 20.0            # an episode never outlives this after its return (the client's gate times out at 15 s)
OUTPUT_FRESH_MS = 300       # B6's R1 test (v2's EXIT_OUTPUT_AGE_MS)
STALL_REASON = "client_stall"
HOLD_REASON = "input_hold"


def enabled(environ: Mapping[str, str]) -> tuple[bool, str | None]:
    raw = (environ.get(FLAG_ENV) or "").strip()
    if not raw:
        return False, None
    if raw != "1":
        return False, f"ignored: {raw[:32]!r} is not 1"
    import hold_tuning
    import stall_signal
    if not hold_tuning.enabled(environ)[0]:
        return False, "ignored: the hold with B6 is not active (PRIVYHUB_INPUT_HOLD + PRIVYHUB_INPUT_HOLD_B6=1)"
    if stall_signal.parse(environ.get(stall_signal.FLAG_ENV))[0] is None:
        return False, "ignored: the stall signal is not active (PRIVYHUB_STALL_SIGNAL absent or invalid)"
    return True, None


def rewind_cap(environ: Mapping[str, str], cap: int) -> int:
    """B4's cap with B8 on and no `_CAP` given: B6's default + CAP_EXTRA (72 at H 950), <= 120."""
    if not enabled(environ)[0] or (environ.get(REWIND_CAP_ENV) or "").strip():
        return cap
    return min(120, int(cap) + CAP_EXTRA)


class Ownership:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._end()

    def _end(self) -> None:
        self.key: float | None = None           # the hold's pause (`_state_since`), None = no episode
        self.carried = False
        self.return_at: float | None = None     # the first controller packet back
        self.resumed_at: float | None = None
        self.ignored = 0

    @staticmethod
    def _state(recovery: Any) -> tuple[str, str | None, float]:
        with recovery._lock:
            return recovery._state, recovery._last_desync_reason, recovery._state_since

    # --- the owner's own methods ----------------------------------------------------------------------------------

    def note_hold(self, recovery: Any) -> None:
        """In note_input_hold, after the pause: a new episode when the pause stands as the hold's."""
        state, reason, key = self._state(recovery)
        if state == "PAUSED_RECOVERING" and reason == HOLD_REASON:
            self._end()
            self.key = key

    def note_return(self, recovery: Any) -> None:
        """At note_input_release's top (the first controller packet back, before B7's 60-ms wait)."""
        state, reason, key = self._state(recovery)
        if (self.key is not None and key == self.key and state == "PAUSED_RECOVERING"
                and reason in (HOLD_REASON, STALL_REASON) and self.return_at is None):
            self.return_at = self._clock()

    def maybe_resume(self, recovery: Any, now: float) -> bool:
        """From the monitor (after B6's R1): the first fresh heartbeat after the return resumes a stall-owned hold."""
        with recovery._lock:
            if (recovery._state != "PAUSED_RECOVERING" or recovery._last_desync_reason != STALL_REASON
                    or self.key is None or recovery._state_since != self.key or self.return_at is None):
                return False
            if not recovery._heartbeat_history:
                return False
            hb_at, hb_age = recovery._heartbeat_history[-1]
            if hb_at <= self.return_at or not 0 <= hb_age <= OUTPUT_FRESH_MS:
                return False
            back = self.return_at
        return self._resume(recovery, "hold_return_stall", output_age_ms=hb_age,
                            packets_back_to_resume_ms=int((self._clock() - back) * 1000.0))

    def ready_resume(self, recovery: Any) -> bool:
        """The plugin's ready action, before its own status read and resume (the core still paused, so B4's method
        applies): the client's ready while the hold's stall-owned pause stands. The ready that follows is then B6's
        `client_ready_after_hold` (not a session)."""
        state, reason, key = self._state(recovery)
        if state != "PAUSED_RECOVERING" or reason != STALL_REASON or self.key is None or key != self.key:
            return False
        return self._resume(recovery, "client_ready_hold")

    def _resume(self, recovery: Any, via: str, **fields: Any) -> bool:
        rw = getattr(recovery, "_input_hold_rewind", None)
        if rw is not None:
            rw.rewind(recovery, via)
        error = ""
        try:
            recovery._resume_game()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        with recovery._lock:
            if recovery._state != "PAUSED_RECOVERING" or recovery._last_desync_reason != STALL_REASON:
                return False                            # B7's stall_end resumed it meanwhile
            if error:
                recovery._log("hold_return_stall_failed", resume_error=error, via=via)
                return False                            # B7's stall_end / quiet, the gate or the give-up still apply
            recovering_ms = int((time.monotonic() - recovery._state_since) * 1000.0)
            recovery._state = "PLAYING"
            recovery._state_since = time.monotonic()
            from games.link_drop_recovery import RESTART_BACKOFF_MS
            recovery._restart_backoff_ms = RESTART_BACKOFF_MS
            recovery._last_restart_at = None
            recovery._client_present_since = time.monotonic()
            recovery._exit_ok_since = None
            recovery._exit_packets_back_at = None
            self.resumed_at = self._clock()
            if self.return_at is None:
                self.return_at = self.resumed_at
            b6 = getattr(recovery, "_input_hold_b6", None)
            if b6 is not None:
                from hold_tuning import READY_AFTER_HOLD_S
                b6._ready_window_until = b6._clock() + READY_AFTER_HOLD_S   # B6's R3, as B6's own resume sets it
            recovery._log("resumed", from_state="PAUSED_RECOVERING", recovering_ms=recovering_ms,
                          restarts=recovery._restarts, via=via, **fields)
            return True

    # --- B7's worker -------------------------------------------------------------------------------------------------

    def _returned(self, now: float) -> bool:
        """The episode is past its return (and not expired)."""
        if self.key is None or self.return_at is None:
            return False
        if now - (self.resumed_at or self.return_at) > EPISODE_S:
            self._end()
            return False
        return True

    def ignore_stall(self, recovery: Any, gate: bool, age: int, threshold_ms: int, frame: int) -> bool:
        """A stall at the top of B7's branch: True = the client's gate over fresh output after the episode's resume."""
        if not self._returned(self._clock()):
            return False
        state, _reason, _key = self._state(recovery)
        if state != "PLAYING" or not gate or age >= threshold_ms:
            return False
        self.ignored += 1
        if self.ignored == 1:
            recovery._log("stall_gate_after_return", client_frame=frame, age_ms=age)
        return True

    def note_stall(self, recovery: Any, rx: float, age: int, frame: int) -> None:
        """At the end of B7's stall branch: the handover carries the hold's pending rewind (onset = the earlier)."""
        state, reason, key = self._state(recovery)
        if state != "PAUSED_RECOVERING" or reason != STALL_REASON or self.key is None or key != self.key:
            return
        pre = extra = None
        rw = getattr(recovery, "_input_hold_rewind", None)
        if rw is not None and hasattr(rw, "counter_before"):
            client_onset = rx - float(age) / 1000.0
            with rw._lock:
                pending = rw._pending
                if pending is not None and pending.get("key") == key:
                    b8 = pending.get("b8")
                    if b8 is None:
                        pending["b8_hold_onset"] = pending["onset"]
                        b8 = pending["b8"] = {"pre_hold_frames": rw.counter_before(pending), "stall_frames": 0}
                    if client_onset < pending["onset"]:
                        pending["onset"] = client_onset
                        b8["stall_frames"] = max(0, int(round((pending["b8_hold_onset"] - client_onset) * rw.fps)))
                    pre, extra = b8["pre_hold_frames"], b8["stall_frames"]
        if not self.carried:
            self.carried = True
            recovery._log("input_hold_carry", pre_hold_frames=pre, stall_frames=extra, client_frame=frame, age_ms=age)

    def late_stall_end(self, recovery: Any, state: str, reason: str | None, frame: int) -> bool:
        """In B7's stall_end branch: True = a logged no-op on a core this episode already resumed."""
        if self.key is None:
            return False
        if state == "PLAYING" and self._returned(self._clock()):
            since = None if self.resumed_at is None else int((self._clock() - self.resumed_at) * 1000.0)
            recovery._log("stall_end_late", client_frame=frame, ignored_gate_stalls=self.ignored,
                          since_resume_ms=since)
            self._end()
            return True
        if state == "PAUSED_RECOVERING" and reason == STALL_REASON:
            self._end()                                 # B7's own stall_end resume ends the episode (the rewind carried)
        return False


def wire(recovery: Any, controller: Any, environ: Mapping[str, str]) -> Ownership | None:
    """The plugin's one call, after B2's, B4's, B6's and B7's wires."""
    on, why = enabled(environ)
    if on and (getattr(recovery, "_input_hold_b6", None) is None or getattr(recovery, "_client_stall", None) is None):
        on, why = False, "ignored: B6's tuning or B7's signal is not wired"
    if not on:
        if why:
            recovery._log("input_hold_b8_config", ignored=True, reason=why)
        return None
    o = Ownership()
    recovery._input_hold_b8 = o
    rw = getattr(recovery, "_input_hold_rewind", None)
    if rw is not None:
        rw.cap = rewind_cap(environ, rw.cap)
    recovery._log("input_hold_b8_config", ignored=False, rewind_cap=(rw.cap if rw is not None else None),
                  output_fresh_ms=OUTPUT_FRESH_MS, episode_s=EPISODE_S)
    return o
