"""B2: the fast input hold -- a controller silence >= H ms pauses the core, the first packet back resumes it.

`PRIVYHUB_INPUT_HOLD=<H ms>` (100-4000; `1` / `on` = 250). **Absent = today**:
nothing imports this module. Design:
`docs/memory/evidence/b2_2026-10-22/design_written_before_code.md` (hashed
before this code).

The client sends its whole controller state ~430 times a second whether or not
the player moves (`NativeControllerSender.sendLoop`), so a silence is the link,
not a still player. One owner: recovery v2's `LinkDropRecovery` (a second,
faster trigger, reason `input_hold`, through its own pause / resume). This
module only detects (in the controller receive loop, never blocking it) and
hands the two events, in order, to one worker thread.
"""

from __future__ import annotations

import queue
import threading
import time
from collections import deque
from typing import Any, Callable, Mapping

FLAG_ENV = "PRIVYHUB_INPUT_HOLD"
DEFAULT_MS = 250
MIN_MS, MAX_MS = 100, 4000
MIN_HOLD_MS = 50            # a release waits until the pause has stood this long (>= 2 frames at 60 fps)
CAP_HOLDS = 6               # at most this many holds ...
CAP_WINDOW_S = 60.0         # ... in any rolling 60 s; past it v2's 5.35-s trigger still protects
REASON = "input_hold"


def parse(raw: Any) -> tuple[int | None, str | None]:
    """(H ms, None) when valid; (None, why) when set but ignored; (None, None) when absent."""
    if raw is None or str(raw).strip() == "":
        return None, None
    v = str(raw).strip().lower()
    if v in ("1", "on"):
        return DEFAULT_MS, None
    if v.isdigit() and MIN_MS <= int(v) <= MAX_MS:
        return int(v), None
    return None, f"ignored: {str(raw).strip()[:32]!r} is not 1 / on / {MIN_MS}-{MAX_MS}"


class InputHoldDetector:
    """Pure, driven by the controller receive loop. Emits ("hold", age_ms) / ("release", held_ms) to `emit`."""

    def __init__(self, hold_ms: int, emit: Callable[[tuple], None], clock: Callable[[], float] = time.monotonic):
        self.hold_s = hold_ms / 1000.0
        self._emit = emit
        self._clock = clock
        self.held = False
        self._silence_start = 0.0
        self._starts: deque[float] = deque()
        self._cap_reported_until = 0.0
        self.holds = 0
        self.releases = 0
        self.capped = 0

    # B6: the trigger's tuning (hold_tuning.Tuning; only PRIVYHUB_INPUT_HOLD_B6=1 sets it). None = B2.
    tuning: Any = None
    # B9: the scratch savestate's mark (rewind_cores.StateMark; only PRIVYHUB_INPUT_HOLD_REWIND=state). None = B2.
    state_mark: Any = None

    def on_quiet(self, now: float, last_any_packet_at: float) -> None:
        # B9: the scratch save inside the silence, before the hold (PRIVYHUB_INPUT_HOLD_REWIND=state only)
        if self.state_mark is not None:
            self.state_mark.on_quiet(now, last_any_packet_at)
        # B6: B2's logic with B6's cap rule (PRIVYHUB_INPUT_HOLD_B6 only)
        if self.tuning is not None:
            return self.tuning.on_quiet(self, now, last_any_packet_at)
        if self.held or last_any_packet_at <= 0.0 or now - last_any_packet_at < self.hold_s:
            return
        while self._starts and now - self._starts[0] >= CAP_WINDOW_S:
            self._starts.popleft()
        if last_any_packet_at <= self._silence_start:
            return                                    # this silence was already counted (capped)
        self._silence_start = last_any_packet_at
        if len(self._starts) >= CAP_HOLDS:
            self.capped += 1
            if now >= self._cap_reported_until:
                self._cap_reported_until = self._starts[0] + CAP_WINDOW_S
                self._emit(("cap", round((now - last_any_packet_at) * 1000.0, 1)))
            return
        self._starts.append(now)
        self.held = True
        self.holds += 1
        self._emit(("hold", round((now - last_any_packet_at) * 1000.0, 1)))

    def on_packet(self, now: float) -> None:
        if not self.held:
            return
        self.held = False
        self.releases += 1
        self._emit(("release", round((now - self._silence_start) * 1000.0, 1)))


class HoldDispatcher:
    """One worker: the recovery calls, in order, off the receive loop. `run_sync` for tests (no thread)."""

    def __init__(self, recovery: Any, game_paused: Callable[[], bool],
                 clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep,
                 threaded: bool = True) -> None:
        self.recovery = recovery
        self.game_paused = game_paused
        self._clock = clock
        self._sleep = sleep
        self._q: "queue.SimpleQueue[tuple]" = queue.SimpleQueue()
        self._paused_at: float | None = None      # when OUR hold's pause returned
        self._ours = False
        self._skipped_reported = False
        if threaded:
            threading.Thread(target=self._run, name="PrivyHub-Input-Hold", daemon=True).start()

    def put(self, event: tuple) -> None:
        # B4: a hold's detection time, for the rewind's onset (PRIVYHUB_INPUT_HOLD_REWIND only)
        if getattr(self.recovery, "_input_hold_rewind", None) is not None:
            self.recovery._input_hold_rewind.stamp(event, self._clock())
        self._q.put(event)

    def _run(self) -> None:
        while True:
            event = self._q.get()
            try:
                self.handle(event)
            except Exception:
                pass                                  # the hold must never take the worker down

    def handle(self, event: tuple) -> None:
        # B4: one stamp popped per hold event, on every path (PRIVYHUB_INPUT_HOLD_REWIND only)
        if getattr(self.recovery, "_input_hold_rewind", None) is not None:
            self.recovery._input_hold_rewind.on_handle(event)
        kind, ms = event
        if kind == "hold":
            try:
                paused = bool(self.game_paused())
            except Exception:
                paused = False
            if paused:
                self._ours = False
                if not self._skipped_reported:
                    self._skipped_reported = True
                    self.recovery._log("input_hold_skipped_paused", age_ms=ms)
                return
            self._skipped_reported = False
            self._ours = bool(self.recovery.note_input_hold(ms))
            self._paused_at = self._clock() if self._ours else None
            # B4: the pending hold: onset and confirmed pause (PRIVYHUB_INPUT_HOLD_REWIND only)
            if getattr(self.recovery, "_input_hold_rewind", None) is not None:
                self.recovery._input_hold_rewind.note_paused(self._ours, self._paused_at, self.recovery)
        elif kind == "release":
            if not self._ours:
                return
            self._ours = False
            if self._paused_at is not None:
                wait = MIN_HOLD_MS / 1000.0 - (self._clock() - self._paused_at)
                if wait > 0:
                    self._sleep(wait)
            self.recovery.note_input_release(ms)
        elif kind == "cap":
            self.recovery._log("input_hold_cap", age_ms=ms, cap_holds=CAP_HOLDS, cap_window_s=CAP_WINDOW_S)


def wire(recovery: Any, controller: Any, game_paused: Callable[[], bool],
         environ: Mapping[str, str]) -> InputHoldDetector | None:
    """The plugin's one call: parse, log an ignored value once, build and hand the detector to the bridge."""
    hold_ms, why = parse(environ.get(FLAG_ENV))
    if hold_ms is None:
        if why:
            recovery._log("input_hold_config", ignored=True, reason=why)
        return None
    dispatcher = HoldDispatcher(recovery, game_paused)
    detector = InputHoldDetector(hold_ms, dispatcher.put)
    controller.set_input_hold(detector)
    recovery._log("input_hold_config", ignored=False, hold_ms=hold_ms, min_hold_ms=MIN_HOLD_MS,
                  cap_holds=CAP_HOLDS, cap_window_s=CAP_WINDOW_S)
    return detector
