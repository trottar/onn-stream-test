"""B4: on the input hold's release, rewind the core by the frames it ran without the player before the pause landed.

`PRIVYHUB_INPUT_HOLD_REWIND=1`, read only when `PRIVYHUB_INPUT_HOLD` is set and valid (B2). **Absent = B2's hold
byte for byte**: nothing imports this module. `PRIVYHUB_INPUT_HOLD_REWIND_CAP` (5-120, default 30). Design:
`docs/memory/evidence/b4_2026-10-22/design_written_before_code.md` (hashed before this code).

RetroArch 1.22.2's command interface reads no frame counter, so the counter is the host's monotonic clock x 60 fps:
the onset (the receive loop's stamp of the last controller packet) and the confirmed pause (B2's dispatcher, when
EmulatorManager.pause() returned PAUSED). On release, before the resume: mask the player's input, `REWIND` +
`PAUSE_TOGGLE` in one instant, `REWIND` every half frame for N frames, one `GET_STATUS` within 2 frames' time
(PLAYING = confirmed), unmask; then B2's resume as today. Never raises: a failure is a `rewind_failed` row and the
resume proceeds. One owner: the recovery calls `rewind` from its own two resumes (the hold's release, and v2's
controller-return exit after a handover).
"""

from __future__ import annotations

import math
import socket
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable, Mapping

FLAG_ENV = "PRIVYHUB_INPUT_HOLD_REWIND"
CAP_ENV = "PRIVYHUB_INPUT_HOLD_REWIND_CAP"
HOLD_ENV = "PRIVYHUB_INPUT_HOLD"
DEFAULT_CAP = 30
MIN_CAP, MAX_CAP = 5, 120
FPS = 60.0                  # the cores' nominal rate (snes 60.10, psx 59.94: < 0.05 frame over 20)
CONFIRM_FRAMES = 2          # GET_STATUS must answer within this many frames' time
# pause()'s PAUSED read trails the pause itself: RetroArch answers a GET_STATUS read in the same poll as the toggle
# with the old state, so PAUSED is pause()'s next poll, 50 ms later. Measured on this host, 20 / 20 pauses: 61-67 ms
# = 3.66-4.01 frames after the poll that read the toggle (b4_2026-10-22/pause_confirm_lag.json); that poll's frame
# runs no core frame (the pause). floor(3.66 + 1) = 4 frames are subtracted: the rewind lands within 1 frame of the
# onset (0-1 before it if the toggle's frame does not run, 0-1 after if it does).
PAUSE_CONFIRM_LAG_FRAMES = 4
MASK_INPUT = True           # the task's "with input masked" (design §5: the trade-off)
MASK_MAX_S = 1.0            # the mask can never outlive this
METHOD = "unpaused_per_frame"
HOST = "127.0.0.1"
CONFIG_MARK = 'rewind_enable = "true"'

# Real savestates on disk, uncompressed (RZIP header), bytes: b4_2026-10-22/savestate_sizes.json.
STATE_BYTES = {
    "snes9x_libretro.so": 823_536,
    "bsnes_libretro.so": 284_304,
    "mednafen_psx_hw_libretro.so": 16_777_240,
}
DEFAULT_BUFFER_BYTES = 20 * 1024 * 1024     # RetroArch's own default (its saved config: "20971520")
KEYS = ("rewind_enable", "rewind_granularity", "rewind_buffer_size", "audio_rewind_mute")


def parse_cap(raw: Any) -> tuple[int, str | None]:
    if raw is None or str(raw).strip() == "":
        return DEFAULT_CAP, None
    v = str(raw).strip()
    if v.isdigit() and MIN_CAP <= int(v) <= MAX_CAP:
        return int(v), None
    return DEFAULT_CAP, f"cap ignored: {v[:32]!r} is not {MIN_CAP}-{MAX_CAP}; {DEFAULT_CAP}"


def parse(environ: Mapping[str, str]) -> tuple[bool, str | None]:
    """(on, None) / (False, why when set but ignored) / (False, None) when absent."""
    raw = (environ.get(FLAG_ENV) or "").strip()
    if not raw:
        return False, None
    if raw != "1":
        return False, f"ignored: {raw[:32]!r} is not 1"
    import input_hold
    hold_ms, _ = input_hold.parse(environ.get(HOLD_ENV))
    if hold_ms is None:
        return False, "ignored: the hold is not active (PRIVYHUB_INPUT_HOLD absent or invalid)"
    return True, None


def buffer_bytes(core_name: str, cap: int) -> int:
    raw = STATE_BYTES.get(str(core_name))
    if raw is None:
        return DEFAULT_BUFFER_BYTES
    mib = 1024 * 1024
    return int(math.ceil(raw * (cap + 2) / mib)) * mib


def config_block(core_name: str, environ: Mapping[str, str]) -> str:
    cap, _ = parse_cap(environ.get(CAP_ENV))
    # B6: the buffer for B6's cap default (PRIVYHUB_INPUT_HOLD_B6=1, no _CAP given)
    if (environ.get("PRIVYHUB_INPUT_HOLD_B6") or "").strip():
        import hold_tuning
        cap = hold_tuning.rewind_cap_default(environ) or cap
    return ("\n\n# PrivyHub B4 input-hold rewind (PRIVYHUB_INPUT_HOLD_REWIND=1)\n"
            'rewind_enable = "true"\n'
            'rewind_granularity = "1"\n'
            f'rewind_buffer_size = "{buffer_bytes(core_name, cap)}"\n'
            'audio_rewind_mute = "true"\n')


def apply_session_config(session_text: str, core_name: str, environ: Mapping[str, str]) -> str:
    """The generator's one call: the block appended, flag on only. A base that already sets a key is refused
    (RetroArch ignored a duplicate assignment appended after the persistent one, A7.3), so nothing is appended."""
    on, _ = parse(environ)
    if not on:
        return session_text
    for line in session_text.splitlines():
        if line.strip().split("=", 1)[0].strip() in KEYS:
            return session_text
    return session_text + config_block(core_name, environ)


class InputMask:
    """The bridge's mask (`masked()` read by the receive loop). Expires by itself after MASK_MAX_S."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._until = 0.0

    def on(self) -> None:
        self._until = self._clock() + MASK_MAX_S

    def off(self) -> None:
        self._until = 0.0

    def masked(self) -> bool:
        return self._until > 0.0 and self._clock() < self._until


class Nci:
    """Raw loopback UDP to RetroArch's command port (no per-datagram logging, a timeout below 50 ms)."""

    def __init__(self, port: int):
        self.port = int(port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((HOST, 0))

    def send(self, cmd: str) -> None:
        self.sock.sendto(cmd.encode("utf-8"), (HOST, self.port))

    def status(self, timeout: float) -> str:
        self.sock.settimeout(timeout)
        deadline = time.monotonic() + timeout
        self.send("GET_STATUS")
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise socket.timeout("GET_STATUS")
            self.sock.settimeout(left)
            data, src = self.sock.recvfrom(4096)
            if src[0] == HOST and int(src[1]) == self.port:
                return data.decode("utf-8", errors="replace").strip()

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


class Rewinder:
    """Stamps (loop thread), the pending hold (worker), the rewind (the recovery's resumes)."""

    def __init__(self, emulator: Any, controller: Any, cap: int, *, fps: float = FPS,
                 clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep,
                 session_config: Path | None = None, nci_factory: Callable[[int], Any] = Nci,
                 mask: InputMask | None = None):
        self.emulator = emulator
        self.controller = controller
        self.cap = int(cap)
        self.fps = float(fps)
        self._clock = clock
        self._sleep = sleep
        self.session_config = session_config
        self._nci_factory = nci_factory
        self.mask = mask or InputMask(clock)
        self._puts: deque[float] = deque()
        self._onset: float | None = None
        self._pending: dict[str, Any] | None = None
        self._lock = threading.Lock()

    # --- B2's dispatcher (input_hold.HoldDispatcher) -----------------------------------------------------------

    def stamp(self, event: tuple, now: float) -> None:
        """put(), in the receive loop at detection time: a hold's put time, in order."""
        if event and event[0] == "hold":
            self._puts.append(now)

    def on_handle(self, event: tuple) -> None:
        """handle()'s first statement: one stamp popped per hold event, on every path."""
        if event and event[0] == "hold":
            put_at = self._puts.popleft() if self._puts else None
            self._onset = None if put_at is None else put_at - float(event[1]) / 1000.0

    def note_paused(self, ours: bool, paused_at: float | None, recovery: Any) -> None:
        """After B2's `_paused_at`: the pending hold of this pause episode (or none)."""
        with self._lock:
            if ours and paused_at is not None and self._onset is not None:
                self._pending = {"onset": self._onset, "paused_at": paused_at,
                                 "key": getattr(recovery, "_state_since", None)}
            else:
                self._pending = None
            self._onset = None

    # --- the recovery's two resumes ----------------------------------------------------------------------------

    def counter_before(self, pending: Mapping[str, float]) -> int:
        """Frames the core ran since the onset (0 at the onset), at the confirmed pause less its measured lag."""
        raw = int(round((pending["paused_at"] - pending["onset"]) * self.fps))
        return max(0, raw - PAUSE_CONFIRM_LAG_FRAMES)

    def rewind(self, recovery: Any, via: str) -> dict[str, Any] | None:
        """Before the resume. None when there is no pending hold for this pause; else the row written. Never raises."""
        with self._lock:
            pending, self._pending = self._pending, None
            if pending is None or pending.get("key") != getattr(recovery, "_state_since", None):
                return None                                       # none, or a stale one from another pause: dropped
        fields: dict[str, Any] = {"via": via, "method": METHOD, "cap": self.cap}
        try:
            before = self.counter_before(pending)
            requested = min(before, self.cap)
            fields.update(counter_before=before, requested_frames=requested, rewound_frames=0,
                          counter_after=before,
                          onset_to_pause_ms=round((pending["paused_at"] - pending["onset"]) * 1000.0, 1),
                          pause_confirm_lag_frames=PAUSE_CONFIRM_LAG_FRAMES)
            if requested <= 0:
                return self._row(recovery, "input_release", fields, rewind_ms=0.0)
            why = self._precondition()
            if why:
                return self._row(recovery, "rewind_failed", fields, reason=why)
            ok, rewound, ms, why = self._run(requested)
            fields.update(rewound_frames=rewound, counter_after=before - rewound)
            if not ok:
                return self._row(recovery, "rewind_failed", fields, rewind_ms=ms, reason=why)
            return self._row(recovery, "input_release", fields, rewind_ms=ms)
        except Exception as exc:                                  # the hold never fails because the rewind did
            try:
                return self._row(recovery, "rewind_failed", fields, reason=f"{type(exc).__name__}: {exc}")
            except Exception:
                return None

    def _precondition(self) -> str | None:
        port = getattr(self.emulator, "_network_cmd_port", None)
        if port is None:
            return "no RetroArch command port"
        if self.session_config is not None:
            try:
                text = Path(self.session_config).read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                return f"session config unreadable: {exc}"
            if CONFIG_MARK not in text:
                return "the session config carries no rewind_enable (the running RetroArch was not launched with it)"
        return None

    def _run(self, requested: int) -> tuple[bool, int, float, str | None]:
        frame = 1.0 / self.fps
        lock = getattr(self.emulator, "lock", None) or threading.RLock()
        with lock:
            nci = self._nci_factory(int(self.emulator._network_cmd_port))
            try:
                if MASK_INPUT:
                    self.mask.on()
                    try:
                        self.controller._neutralize()
                    except Exception:
                        pass
                t0 = self._clock()
                nci.send("REWIND")
                nci.send("PAUSE_TOGGLE")
                last = t0
                end = t0 + (requested - 0.5) * frame
                while True:
                    self._sleep(frame / 2.0)
                    now = self._clock()
                    if now >= end:
                        break
                    nci.send("REWIND")
                    last = now
                rewound = min(requested, int(math.floor((last - t0) * self.fps + 1e-9)) + 1)   # polls that saw one
                ms = round((last - t0) * 1000.0, 1)
                try:
                    status = nci.status(CONFIRM_FRAMES * frame)
                except (OSError, socket.timeout) as exc:
                    return False, rewound, ms, f"GET_STATUS not answered within {CONFIRM_FRAMES} frames: {exc}"
                if not status.upper().startswith("GET_STATUS PLAYING"):
                    return False, rewound, ms, f"not playing after the rewind: {status[:40]}"
                return True, rewound, ms, None
            finally:
                if MASK_INPUT:
                    self.mask.off()
                nci.close()

    def _row(self, recovery: Any, event: str, fields: dict[str, Any], **extra: Any) -> dict[str, Any]:
        row = dict(fields, **extra)
        recovery._log(event, **row)
        return row


def wire(recovery: Any, controller: Any, emulator: Any, environ: Mapping[str, str],
         project_root: Path | None = None) -> Rewinder | None:
    """The plugin's one call (after B2's wire): parse, one config row, the rewinder on the recovery, the mask on the
    bridge. Acts only when B2 wired its detector (the hold is active)."""
    on, why = parse(environ)
    if on and getattr(controller, "_input_hold", None) is None:
        on, why = False, "ignored: the hold is not active (no detector)"
    cap, cap_why = parse_cap(environ.get(CAP_ENV))
    if not on:
        if why:
            recovery._log("input_hold_rewind_config", ignored=True, reason=why)
        return None
    cfg = None if project_root is None else Path(project_root) / "data/games/retroarch/config/privyhub-session.cfg"
    rw = Rewinder(emulator, controller, cap, session_config=cfg)
    recovery._input_hold_rewind = rw
    controller.set_input_mask(rw.mask)
    recovery._log("input_hold_rewind_config", ignored=False, cap=cap, cap_note=cap_why, fps=FPS, method=METHOD,
                  mask_input=MASK_INPUT, confirm_frames=CONFIRM_FRAMES)
    return rw
