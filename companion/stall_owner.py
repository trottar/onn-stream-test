"""B12: the stall's resume, inside the one owner -- a picture-only drop resumes when the client can see, with the state
saved at the stall, and v2 does not restart the encoder under it.

`PRIVYHUB_STALL_RESUME=1`, active only with `PRIVYHUB_STALL_SIGNAL` wired (B7). **Absent = today**: nothing imports this
module. Design: `docs/memory/evidence/b12_2026-10-23/design_written_before_code.md` (hashed before this code).

BENCH-R3 B (`@down`): the stall paused at 420-484 ms; the client's gate `ready` then resumed it through recovery's
plain `note_stream_ready` (no load / rewind), v2's monitor restarted the encoder in 3 of 5 blackouts (it runs for any
paused recovery once the client has been present 2 s) and the ladder stepped 7000->5000; a gate-bit stall then paused
again. Here, for a pause the stall owns (reason `client_stall`, not B8's hold episode):
- with `PRIVYHUB_INPUT_HOLD_REWIND=state` (or `1`), the first stall datagram of an episode asks B9's worker for a
  scratch save (`kind` stall, onset = the client's last displayed frame), so the resume loads ~150 ms after it;
- the client's `ready` resumes it through the owner with that load (`resumed via client_ready_stall`), B7's ready window
  set; `stall_end` first is B7's own resume (unchanged); after either, gate-bit stalls over fresh output are ignored and
  the late `stall_end` is `stall_end_late`;
- v2's encoder restart is held off until the pause is 5,000 ms old (v2's own trigger); then v2 owns it, once
  (`stall_handover_v2`).

B16 (the same flag; design `docs/memory/evidence/b16_2026-10-24/design_written_before_code.md`, hashed before this
code). CL-B10 cell 3: the client's gate held the picture 1.3-3.2 s after the downlink's return (four 500-ms gate ticks),
v2's hold expired first in all 5, and blackout 5's restart acted on a heartbeat built before the return; cell 2 saved
state at four 150-ms client stalls. Here:
- the start response tells the client to send its ready as soon as it has a decodable frame (`client_hint`); the host
  resumes on it through the owners above (B12's `client_ready_stall`, B8's `client_ready_hold`);
- the stall's save comes only from the stall signal (age >= its threshold, 400 with `1`), synchronously before B7's
  pause (B9 skips a paused core): no save under the 400-ms signal;
- v2 takes a stall-owned pause past 5 s only while the newest stall datagram (<= 300 ms old) shows the client still
  stalled.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping

FLAG_ENV = "PRIVYHUB_STALL_RESUME"
V2_MS = 5_000               # E3-R1's controller-silence trigger: past it, v2 owns the pause
EPISODE_S = 20.0            # an episode's resumed phase never outlives this (the client's gate times out at 15 s)
REASON = "client_stall"
NEWEST_S = 0.30             # B16: the newest stall datagram describes the client now (B7's quiet rule: 300 ms)


def enabled(environ: Mapping[str, str]) -> tuple[bool, str | None]:
    raw = (environ.get(FLAG_ENV) or "").strip()
    if not raw:
        return False, None
    if raw != "1":
        return False, f"ignored: {raw[:32]!r} is not 1"
    import stall_signal
    if stall_signal.parse(environ.get(stall_signal.FLAG_ENV))[0] is None:
        return False, "ignored: the stall signal is not active (PRIVYHUB_STALL_SIGNAL absent or invalid)"
    return True, None


class StallOwner:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._saved_episode = False             # this stall episode asked for its save
        self._resumed_at: float | None = None   # the owner resumed this episode's pause (gate stalls ignored after)
        self._ignored = 0
        self._handed_key: float | None = None   # the pause v2 took over (once)
        self._last_rx = 0.0
        self._newest: tuple[float, int] = (0.0, 0)   # B16: the newest stall datagram (receive time, output age)
        self._threshold_ms = 400                 # B16: the stall signal's threshold (B7's, set per datagram)

    @staticmethod
    def _state(recovery: Any) -> tuple[str, str | None, float]:
        with recovery._lock:
            return recovery._state, recovery._last_desync_reason, recovery._state_since

    @staticmethod
    def _hold_episode(recovery: Any, key: float) -> bool:
        b8 = getattr(recovery, "_input_hold_b8", None)
        return b8 is not None and getattr(b8, "key", None) == key

    # --- B7's worker -------------------------------------------------------------------------------------------------

    def on_stall(self, recovery: Any, rx: float, age: int, gate: bool, threshold_ms: int, frame: int) -> bool:
        """At the top of B7's stall branch. True = ignore this stall (the client's gate over fresh output after the
        owner's resume)."""
        state, _reason, _key = self._state(recovery)
        if rx - self._last_rx > 0.3:
            self._saved_episode = False         # a new client episode (B7's quiet gap)
        self._last_rx = rx
        self._newest = (rx, int(age))           # B16: what the client says now (v2's rule)
        self._threshold_ms = int(threshold_ms)
        if self._resumed_at is not None:
            if self._clock() - self._resumed_at > EPISODE_S:
                self._end()
            elif state == "PLAYING" and gate and age < threshold_ms:
                self._ignored += 1
                if self._ignored == 1:
                    recovery._log("stall_gate_after_resume", client_frame=frame, age_ms=age)
                return True
        # B16: the save only from the stall signal (age >= its threshold), taken now, before B7's pause below
        if state == "PLAYING" and not self._saved_episode and not gate and age >= threshold_ms:
            rw = getattr(recovery, "_input_hold_rewind", None)
            cores = getattr(rw, "b9", None) if rw is not None else None
            if cores is not None and getattr(cores, "mode", None) == "state":
                self._saved_episode = True
                try:
                    cores.save(rx - float(age) / 1000.0, rx, "stall")
                except Exception:
                    pass                        # the pause must never wait on a failed save
        return False

    def late_stall_end(self, recovery: Any, state: str, frame: int) -> bool:
        """In B7's stall_end branch: True = a logged no-op on a core the owner already resumed."""
        resumed = self._resumed_at
        self._saved_episode = False             # the client's episode ended: the next stall is a new one
        if resumed is not None and state == "PLAYING":
            recovery._log("stall_end_late", client_frame=frame, ignored_gate_stalls=self._ignored,
                          since_resume_ms=int((self._clock() - resumed) * 1000.0))
            self._end()
            return True
        self._end()
        return False

    def _end(self) -> None:
        self._resumed_at = None
        self._ignored = 0

    # --- the owner's own methods -------------------------------------------------------------------------------------

    def ready_resume(self, recovery: Any) -> bool:
        """The plugin's ready action, before its own status read (the core still paused): a stall-owned pause resumes
        through the owner, with the stall's load."""
        state, reason, key = self._state(recovery)
        if state != "PAUSED_RECOVERING" or reason != REASON or self._hold_episode(recovery, key):
            return False
        rw = getattr(recovery, "_input_hold_rewind", None)
        if rw is not None:
            rw.rewind(recovery, "client_ready_stall")
        error = ""
        try:
            recovery._resume_game()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        with recovery._lock:
            if recovery._state != "PAUSED_RECOVERING" or recovery._last_desync_reason != REASON:
                return False
            if error:
                recovery._log("stall_ready_resume_failed", resume_error=error)
                return False                    # today's gate path still resumes it
            recovering_ms = int((time.monotonic() - recovery._state_since) * 1000.0)
            recovery._state = "PLAYING"
            recovery._state_since = time.monotonic()
            from games.link_drop_recovery import RESTART_BACKOFF_MS
            recovery._restart_backoff_ms = RESTART_BACKOFF_MS
            recovery._last_restart_at = None
            recovery._client_present_since = time.monotonic()
            self._resumed_at = self._clock()
            self._ignored = 0
            sig = getattr(recovery, "_client_stall", None)
            if sig is not None:
                from stall_signal import READY_AFTER_S
                sig._ready_until = sig._clock() + READY_AFTER_S      # the ready itself: client_ready_after_stall
            recovery._log("resumed", from_state="PAUSED_RECOVERING", recovering_ms=recovering_ms,
                          restarts=recovery._restarts, via="client_ready_stall")
            return True

    @staticmethod
    def client_hint() -> dict[str, Any]:
        """B16: the start response's `stall_resume`: the client's ready as soon as it has a decodable frame."""
        return {"fast_ready": True}

    def holds_v2(self, recovery: Any, now: float) -> bool:
        """From the monitor, before v2's encoder restart: True = skip v2 this tick (a young stall-owned pause)."""
        with recovery._lock:
            if recovery._state != "PAUSED_RECOVERING" or recovery._last_desync_reason != REASON:
                return False
            key = recovery._state_since
            age_ms = (now - key) * 1000.0
        if self._hold_episode(recovery, key) or self._handed_key == key:
            return False
        if age_ms < V2_MS:
            return True
        # B16: v2 takes it only while the newest stall datagram shows the client still stalled (never on a heartbeat
        # read before the return; a client with frames sends its ready within ~0.55 s)
        rx, last_age = self._newest
        if not (now - rx <= NEWEST_S and last_age >= self._threshold_ms):
            return True
        self._handed_key = key
        recovery._log("stall_handover_v2", held_ms=int(age_ms), v2_ms=V2_MS)
        return False


def wire(recovery: Any, controller: Any, environ: Mapping[str, str]) -> StallOwner | None:
    """The plugin's one call, after B7's (and B8's) wires."""
    on, why = enabled(environ)
    if on and getattr(recovery, "_client_stall", None) is None:
        on, why = False, "ignored: B7's signal is not wired"
    if not on:
        if why:
            recovery._log("stall_resume_config", ignored=True, reason=why)
        return None
    o = StallOwner()
    recovery._stall_owner = o
    rw = getattr(recovery, "_input_hold_rewind", None)
    recovery._log("stall_resume_config", ignored=False, v2_ms=V2_MS,
                  state_save=bool(getattr(getattr(rw, "b9", None), "mode", None) == "state"),
                  fast_ready=True, save_from_signal=True, v2_newest_s=NEWEST_S)
    return o
