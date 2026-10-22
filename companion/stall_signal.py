"""B7: the client's stall signal -- a picture-only drop pauses the game, and it resumes when the player can see again.

`PRIVYHUB_STALL_SIGNAL=1` (act at an output age of 150 ms) or `=<ms>` (150-2000). **Absent = today**: nothing imports
this module, and a stall datagram is a bad packet (it fails the 36-byte size check) exactly as any unknown datagram
is today. Design: `docs/memory/evidence/b7_2026-10-22/design_written_before_code.md` (hashed before this code).

The client (`debug.privyhub.stall_signal`) sends a 24-byte `PHS1` datagram on the controller socket every 50 ms while
its output is older than S or its recovery gate (the full-screen "Reconnecting" overlay) stands, then one
`stall_end` when gameplay is shown again. Here, one owner -- recovery v2's state machine:
- a stall (age >= T, or the gate bit) while PLAYING: `_enter_recovery(trigger="client_stall")`, B4's pending onset =
  the client's last displayed frame on this clock (receive time - age; the LAN's one-way delay taken as 0);
- a stall while a hold stands: B2's own handover (`input_hold_handover`, trigger client_stall); B4's onset stays;
- the hold's release waits <= 60 ms for a stall first (the first controller packet back beats the next stall);
- `stall_end`, or 300 ms with no stall: B4's rewind, then the resume (`resumed via stall_end` / `stall_quiet`);
- a client ready within 20 s of that resume ends the recovery, not a session.
The receive loop only parses and queues; one worker does the rest.
"""

from __future__ import annotations

import queue
import struct
import threading
import time
from typing import Any, Callable, Mapping

FLAG_ENV = "PRIVYHUB_STALL_SIGNAL"
DEFAULT_MS = 150
MIN_MS, MAX_MS = 150, 2000
MAGIC = b"PHS1"
PACKET = struct.Struct("<4sBBHIqI")         # 24 bytes
KIND_STALL, KIND_END = 1, 2
FLAG_IN_GATE = 1
REASON = "client_stall"
QUIET_S = 0.30              # no stall for this long while the stall owns the pause = stall_end lost
DEFER_S = 0.06              # the hold's release waits this long for a stall (> one 50-ms stall interval)
READY_AFTER_S = 20.0


def parse(raw: Any) -> tuple[int | None, str | None]:
    if raw is None or str(raw).strip() == "":
        return None, None
    v = str(raw).strip()
    if v == "1":
        return DEFAULT_MS, None
    if v.isdigit() and MIN_MS <= int(v) <= MAX_MS:
        return int(v), None
    return None, f"ignored: {v[:32]!r} is not 1 / {MIN_MS}-{MAX_MS}"


def decode(data: bytes) -> tuple[int, bool, int, int, int] | None:
    """(kind, in_gate, seq, client frame, output age ms) or None."""
    if len(data) != PACKET.size or data[:4] != MAGIC:
        return None
    _m, kind, flags, _r, seq, frames, age = PACKET.unpack(data)
    if kind not in (KIND_STALL, KIND_END):
        return None
    return kind, bool(flags & FLAG_IN_GATE), seq, frames, age


class StallSignal:
    def __init__(self, recovery: Any, threshold_ms: int, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep, threaded: bool = True):
        self.recovery = recovery
        self.threshold_ms = int(threshold_ms)
        self._clock = clock
        self._sleep = sleep
        self._q: "queue.SimpleQueue[tuple]" = queue.SimpleQueue()
        self.last_stall_rx = 0.0
        self.stalls = 0
        self.ends = 0
        self._ready_until = 0.0
        self._acted = False                       # this stall episode paused the game or took a hold over
        if threaded:
            threading.Thread(target=self._run, name="PrivyHub-Stall-Signal", daemon=True).start()

    # --- the receive loop (never blocks) -------------------------------------------------------------------------

    def on_datagram(self, data: bytes, now: float) -> bool:
        ev = decode(data)
        if ev is None:
            return False
        if ev[0] == KIND_STALL:
            self.last_stall_rx = now
        self._q.put((ev, now))
        return True

    # --- the worker -----------------------------------------------------------------------------------------------

    def _run(self) -> None:
        while True:
            try:
                item = self._q.get(timeout=0.05)
            except queue.Empty:
                item = None
            try:
                if item is not None:
                    self.handle(*item)
                self.check_quiet(self._clock())
            except Exception:
                pass                                  # the signal must never take the worker down

    def _state(self) -> tuple[str, str | None, float]:
        r = self.recovery
        with r._lock:
            return r._state, r._last_desync_reason, r._state_since

    def handle(self, ev: tuple, rx: float) -> None:
        kind, gate, seq, frame, age = ev
        state, reason, _key = self._state()
        if kind == KIND_STALL:
            self.stalls += 1
            if age < self.threshold_ms and not gate:
                return
            if state == "PLAYING":
                self.recovery._enter_recovery(trigger=REASON, age_ms=float(age))
                st, rs, key = self._state()
                if st == "PAUSED_RECOVERING" and rs == REASON:
                    self._acted = True
                    paused_at = self._clock()
                    self.recovery._log("client_stall", client_frame=frame, age_ms=age, in_gate=gate, seq=seq)
                    rw = getattr(self.recovery, "_input_hold_rewind", None)
                    if rw is not None:
                        rw.set_pending(rx - age / 1000.0, paused_at, self.recovery)
            elif state == "PAUSED_RECOVERING" and reason == "input_hold":
                self.recovery._enter_recovery(trigger=REASON, age_ms=float(age))   # B2's own handover
                self._acted = True
            return
        self.ends += 1
        acted, self._acted = self._acted, False
        if state == "PAUSED_RECOVERING" and reason == REASON:
            self.resume("stall_end", frame)
        elif acted and state == "PLAYING":
            self.recovery._log("stall_end_after_gate", client_frame=frame)     # the client's gate resumed it first

    def check_quiet(self, now: float) -> None:
        state, reason, _key = self._state()
        if state == "PAUSED_RECOVERING" and reason == REASON and now - self.last_stall_rx >= QUIET_S:
            self.resume("stall_quiet", None)

    def resume(self, via: str, frame: int | None) -> bool:
        r = self.recovery
        rw = getattr(r, "_input_hold_rewind", None)
        if rw is not None:
            rw.rewind(r, via)
        error = ""
        try:
            r._resume_game()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        from games.link_drop_recovery import RESTART_BACKOFF_MS
        with r._lock:
            if r._state != "PAUSED_RECOVERING" or r._last_desync_reason != REASON:
                return False
            if error:
                r._log("stall_resume_failed", resume_error=error, via=via)
                return False                          # the client's gate or the give-up still apply
            recovering_ms = int((time.monotonic() - r._state_since) * 1000.0)
            r._state = "PLAYING"
            r._state_since = time.monotonic()
            r._restart_backoff_ms = RESTART_BACKOFF_MS
            r._last_restart_at = None
            r._client_present_since = time.monotonic()
            self._ready_until = self._clock() + READY_AFTER_S
            r._log("resumed", from_state="PAUSED_RECOVERING", recovering_ms=recovering_ms, restarts=r._restarts,
                   via=via, client_frame=frame)
            return True

    # --- the recovery's own methods --------------------------------------------------------------------------------

    def defer_release(self, recovery: Any) -> bool:
        """At note_input_release's top: wait <= 60 ms for a stall; True = the hold was handed to the stall."""
        state, reason, _key = self._state()
        if state != "PAUSED_RECOVERING" or reason != "input_hold":
            return False
        t0 = self._clock()
        while True:
            if self.last_stall_rx >= t0 - DEFER_S:
                recovery._enter_recovery(trigger=REASON, age_ms=0.0)     # B2's own handover
                st, rs, _k = self._state()
                self._acted = self._acted or rs == REASON
                return rs == REASON
            if self._clock() - t0 >= DEFER_S:
                return False
            self._sleep(0.005)

    def ready_after_stall(self, recovery: Any) -> bool:
        now = self._clock()
        with recovery._lock:
            if recovery._state != "PLAYING" or now >= self._ready_until:
                return False
            self._ready_until = 0.0
            recovery._log("client_ready_after_stall", within_s=READY_AFTER_S)
            return True


def wire(recovery: Any, controller: Any, environ: Mapping[str, str]) -> StallSignal | None:
    """The plugin's one call (after B2 / B4 / B6's): parse, one config row, the signal on the bridge and the recovery."""
    t, why = parse(environ.get(FLAG_ENV))
    if t is None:
        if why:
            recovery._log("stall_signal_config", ignored=True, reason=why)
        return None
    s = StallSignal(recovery, t)
    recovery._client_stall = s
    controller.set_stall_signal(s)
    recovery._log("stall_signal_config", ignored=False, threshold_ms=t, quiet_s=QUIET_S, defer_s=DEFER_S,
                  ready_after_s=READY_AFTER_S)
    return s
