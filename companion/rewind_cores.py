"""B9: the hold's rewind per core -- RetroArch's rewind for an allow-list, a scratch savestate as the PS1 path.

`PRIVYHUB_INPUT_HOLD_REWIND` (B4's flag, read only with the hold active):
- `1` (B12): `state` for every core (BENCH-R3: the rewind method read PAUSED after on snes9x and PS1; `state` played);
- `rewind` (B9's `1`): RetroArch's rewind **only for the allow-list** (snes9x, bsnes). Another core gets no rewind keys
  in its launch config (Beetle PSX HW: no 1-GB buffer, no +16.6 points) and a `rewind_skipped` row at the release;
- `all`: B4's behaviour for every core (nothing here is wired);
- `state`: no rewind keys; a scratch `SAVE_STATE_SLOT 9` at a controller silence of 400 ms
  (`PRIVYHUB_INPUT_HOLD_STATE_AT_MS`), loaded at the release into a running core (D-BASE-R3C: a mid-FMV state loaded
  into a PAUSED Beetle PSX HW loops; into a RUNNING core it plays).
Absent: nothing imports this module. Design: `docs/memory/evidence/b9_2026-10-22/design_written_before_code.md`
(hashed before this code). Called only from B4's Rewinder (one owner: the recovery's resumes) and B2's detector.
"""

from __future__ import annotations

import queue
import socket
import threading
import time
from pathlib import Path
from typing import Any, Callable, Mapping

FLAG_ENV = "PRIVYHUB_INPUT_HOLD_REWIND"
STATE_AT_ENV = "PRIVYHUB_INPUT_HOLD_STATE_AT_MS"
ALLOW = frozenset({"snes9x_libretro.so", "bsnes_libretro.so"})
STATE_AT_DEFAULT_MS = 400
STATE_AT_MIN_MS = 100
SLOT = 9                    # not 0 (the recovery's staging slot), not 1-3 (the user's)
SAVE_ACK_S = 0.10
LOAD_CONFIRM_S = 0.15       # a 16-MB state; B4's 2-frame window is for REWIND
MATCH_S = 0.005             # the pending's onset and the saved silence's onset are the same packet time
STALL_MATCH_S = 0.10        # B12: a stall save and the stall pause estimate the same client frame (receive - age)
FILE_SLACK_S = 1.0
PAUSE_CONFIRM_LAG_FRAMES = 4   # B4's


def mode(environ: Mapping[str, str]) -> str | None:
    raw = (environ.get(FLAG_ENV) or "").strip()
    return {"1": "state", "rewind": "allow", "all": "all", "state": "state"}.get(raw)   # B12: `1` = state


def config_allowed(core_name: str, environ: Mapping[str, str]) -> bool:
    """The launch config's rewind keys: `1` only for the allow-list, `state` never, `all` always."""
    m = mode(environ)
    if m == "state":
        return False
    if m == "allow":
        return str(core_name) in ALLOW
    return True


def parse_state_at(environ: Mapping[str, str], hold_ms: int | None) -> tuple[int, str | None]:
    raw = (environ.get(STATE_AT_ENV) or "").strip()
    top = (hold_ms or 950) - 50
    if not raw:
        return min(STATE_AT_DEFAULT_MS, top), None
    if raw.isdigit() and STATE_AT_MIN_MS <= int(raw) <= top:
        return int(raw), None
    return min(STATE_AT_DEFAULT_MS, top), f"ignored: {raw[:32]!r} is not {STATE_AT_MIN_MS}-{top}"


def _read(nci: Any, timeout: float, prefix: str) -> str | None:
    """The first reply from the core's port that starts with `prefix`, within `timeout`; None when none."""
    sock = getattr(nci, "sock", None)
    if sock is None:
        return None
    deadline = time.monotonic() + timeout
    while True:
        left = deadline - time.monotonic()
        if left <= 0:
            return None
        sock.settimeout(left)
        try:
            data, src = sock.recvfrom(4096)
        except (socket.timeout, OSError):
            return None
        text = data.decode("utf-8", errors="replace").strip()
        if src[0] == "127.0.0.1" and int(src[1]) == int(nci.port) and text.upper().startswith(prefix):
            return text


class StateMark:
    """On B2's detector: once per silence, at STATE_AT ms, asks for the scratch save. Never blocks the loop."""

    def __init__(self, cores: "Cores", at_ms: int):
        self.cores = cores
        self.at_s = at_ms / 1000.0
        self._marked = 0.0

    def on_quiet(self, now: float, last_any_packet_at: float) -> None:
        if last_any_packet_at <= 0.0 or now - last_any_packet_at < self.at_s or last_any_packet_at == self._marked:
            return
        self._marked = last_any_packet_at
        self.cores.request_save(last_any_packet_at, now)


class Cores:
    """B4's Rewinder's B9 object (`1` and `state` only)."""

    def __init__(self, mode_value: str, emulator: Any, recovery: Any, *, clock: Callable[[], float] = time.monotonic,
                 wall: Callable[[], float] = time.time, threaded: bool = True):
        self.mode = mode_value
        self.emulator = emulator
        self.recovery = recovery
        self._clock = clock
        self._wall = wall
        self._q: "queue.SimpleQueue[tuple]" = queue.SimpleQueue()
        self._lock = threading.Lock()
        self.last_save: dict[str, Any] | None = None
        self.saves = 0
        self.saves_skipped_paused = 0
        self.nci_factory: Callable[[int], Any] | None = None
        if threaded and mode_value == "state":
            threading.Thread(target=self._run, name="PrivyHub-Rewind-State", daemon=True).start()

    def core(self) -> str:
        return str(getattr(self.emulator, "_hold_rewind_core", "") or "")

    # --- the scratch save (B2's detector -> this worker) -----------------------------------------------------------

    def request_save(self, silence_start: float, now: float, kind: str = "silence") -> None:
        self._q.put((silence_start, now, kind))

    def _run(self) -> None:
        while True:
            item = self._q.get()
            try:
                self.save(*item)
            except Exception:
                pass                                   # the save must never take the worker down

    def save(self, silence_start: float, mark_at: float, kind: str = "silence") -> None:
        if getattr(self.emulator, "_paused", False):
            self.saves_skipped_paused += 1
            return
        port = getattr(self.emulator, "_network_cmd_port", None)
        if port is None or self.nci_factory is None:
            return
        lock = getattr(self.emulator, "lock", None) or threading.RLock()
        wall = self._wall()
        with lock:
            nci = self.nci_factory(int(port))
            try:
                t0 = self._clock()
                nci.send(f"SAVE_STATE_SLOT {SLOT}")
                ack = _read(nci, SAVE_ACK_S, "SAVE_STATE_SLOT")
                sent_at = t0
            finally:
                nci.close()
        ok = bool(ack) and ack.upper().startswith(f"SAVE_STATE_SLOT {SLOT}")
        with self._lock:
            self.last_save = {"onset": silence_start, "sent_at": sent_at, "wall": wall, "ack": ack, "ok": ok,
                              "kind": kind}
            self.saves += 1
        self.recovery._log("state_saved" if ok else "state_save_failed", slot=SLOT, core=self.core(), kind=kind,
                           silence_ms=round((mark_at - silence_start) * 1000.0, 1),
                           save_after_onset_ms=round((sent_at - silence_start) * 1000.0, 1),
                           ack=(ack or "")[:40] or None)

    # --- the release (B4's Rewinder.rewind, one owner) ------------------------------------------------------------

    def handles(self, pending: Mapping[str, Any]) -> bool:
        """True = B9 writes this release's row: `state` always; `1` when the core is off the allow-list."""
        return self.mode == "state" or self.core() not in ALLOW

    def release(self, rw: Any, recovery: Any, fields: dict[str, Any], pending: Mapping[str, Any]) -> dict[str, Any]:
        if self.mode != "state":
            return rw._row(recovery, "rewind_skipped", fields, core=self.core(),
                           reason="the core is not on the rewind allow-list (PRIVYHUB_INPUT_HOLD_REWIND=1)")
        fields.update(method="state", slot=SLOT, core=self.core())
        onset = pending.get("b8_hold_onset", pending["onset"])
        with self._lock:
            s = self.last_save
        # B12: a save taken at the client's stall matches the stall pause's own onset within 100 ms
        if s is not None and s.get("kind") == "stall" and abs(s["onset"] - onset) <= STALL_MATCH_S:
            onset = s["onset"]
        if s is None or not s.get("ok") or abs(s["onset"] - onset) > MATCH_S:
            return rw._row(recovery, "rewind_skipped", fields, reason="no scratch state for this pause")
        why = self._file_problem(s)
        if why:
            return rw._row(recovery, "rewind_skipped", fields, reason=why)
        fps = float(rw.fps)
        fields.update(save_after_onset_ms=round((s["sent_at"] - onset) * 1000.0, 1),
                      frames_restored=max(0, int(round((pending["paused_at"] - s["sent_at"]) * fps))
                                          - PAUSE_CONFIRM_LAG_FRAMES),
                      net_unattended_frames=max(0, int(round((s["sent_at"] - onset) * fps))))
        port = getattr(self.emulator, "_network_cmd_port", None)
        if port is None:
            return rw._row(recovery, "rewind_failed", fields, reason="no RetroArch command port")
        lock = getattr(self.emulator, "lock", None) or threading.RLock()
        with lock:
            nci = rw._nci_factory(int(port))
            try:
                rw.mask.on()
                try:
                    rw.controller._neutralize()
                except Exception:
                    pass
                t0 = self._clock()
                nci.send("PAUSE_TOGGLE")                          # into a running core (D-BASE-R3C) ...
                nci.send(f"LOAD_STATE_SLOT {SLOT}")               # ... in the same instant
                ack = _read(nci, LOAD_CONFIRM_S, "LOAD_STATE_SLOT")
                nci.send("GET_STATUS")
                status = _read(nci, LOAD_CONFIRM_S, "GET_STATUS")
                ms = round((self._clock() - t0) * 1000.0, 1)
            finally:
                rw.mask.off()
                nci.close()
        with self._lock:
            self.last_save = None                                 # one load per save
        fields.update(rewind_ms=ms, load_ack=(ack or "")[:40] or None)
        if not ack or not ack.upper().startswith(f"LOAD_STATE_SLOT {SLOT}"):
            return rw._row(recovery, "rewind_failed", fields, reason="LOAD_STATE_SLOT not acknowledged",
                           status=(status or "")[:40] or None)
        if not status or not status.upper().startswith("GET_STATUS PLAYING"):
            return rw._row(recovery, "rewind_failed", fields, reason=f"not playing after the load: {(status or '')[:40]}")
        return rw._row(recovery, "input_release", fields)

    def _file_problem(self, s: Mapping[str, Any]) -> str | None:
        try:
            root = Path(self.emulator._state_root())
            stem = str(self.emulator._active_state_stem())
        except Exception as exc:
            return f"the state root is unknown: {type(exc).__name__}"
        name = f"{stem}.state{SLOT}"
        best = None
        try:
            for p in root.rglob(name):
                st = p.stat()
                if best is None or st.st_mtime > best[0]:
                    best = (st.st_mtime, st.st_size)
        except OSError as exc:
            return f"the state root is unreadable: {type(exc).__name__}"
        if best is None:
            return "no scratch state file"
        if best[1] <= 0 or best[0] < s["wall"] - FILE_SLACK_S:
            return "the scratch state file is older than this save"
        return None


def wire(rw: Any, recovery: Any, controller: Any, emulator: Any, environ: Mapping[str, str]) -> Cores | None:
    """hold_rewind.wire's one call (`1` / `state`): the B9 object on the Rewinder, the mark on B2's detector."""
    m = mode(environ)
    if m not in ("allow", "state"):
        return None
    c = Cores(m, emulator, recovery)
    c.nci_factory = rw._nci_factory
    rw.b9 = c
    at_ms = why = None
    if m == "state":
        det = getattr(controller, "_input_hold", None)
        import input_hold
        hold_ms, _ = input_hold.parse(environ.get(input_hold.FLAG_ENV))
        if (environ.get("PRIVYHUB_INPUT_HOLD_B6") or "").strip() == "1":       # B6 sets H after this wire runs
            import hold_tuning
            hold_ms = hold_tuning.hold_ms(environ) or hold_ms
        at_ms, why = parse_state_at(environ, hold_ms)
        if det is not None and hasattr(det, "on_quiet"):
            det.state_mark = StateMark(c, at_ms)
    recovery._log("input_hold_rewind_cores_config", mode=m, allow=sorted(ALLOW), slot=(SLOT if m == "state" else None),
                  state_at_ms=at_ms, state_at_note=why)
    return c
