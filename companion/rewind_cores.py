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
N64_SKIP = "n64: no save into a running core"          # B61 (only an N64 session, PRIVYHUB_N64=1)
N64_RELEASE = "n64: plain resume (no state)"           # B61
RELEASE_SETTLE_GC_S = 0.2    # B69: F9 then this, so Dolphin's hotkey thread has run the load before the resume key


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


BYE_S = 30.0                # B18: a client's bye holds for this long (the same PLAYING period only)
PRODUCED_MS = 250           # B18: the stream is produced if its sender's packet count moved this recently


class SessionEnd:
    """B18: the session's end as the owner knows it -- no save and no hold once it is known.

    CL-B11 cells 2 / 3: at each window's end the client's sender stopped at `surfaceDestroyed`, B9's silence save fired at
    400 ms, and the client's report (+154-181 ms) and stop (+205-207 ms) came after it. Here the end is known from:
    - the client's `bye` (PHS1 kind 3, sent by a finishing activity before its sender stops; B7's worker hands it over),
      for the same PLAYING period (keyed to `_state_since`) and <= BYE_S;
    - any state but PLAYING (the stop request, `native-stream-stop`, B17's `guard_end`: ENDED);
    - the stream no longer produced: its sender's packet count (session_io's, one packet per 10 ms) has not moved for
      PRODUCED_MS (the game's exit, the stream stopped).
    """

    def __init__(self, recovery: Any, clock: Callable[[], float] = time.monotonic):
        self.recovery = recovery
        self._clock = clock
        self._bye: tuple[float, float] | None = None     # (receive time, the PLAYING period's key)
        self.packets: Callable[[], int] | None = None     # the plugin's: the stream sender's packets sent
        self._last_count: int | None = None
        self._moved_at = 0.0
        self.saves_skipped = 0
        self.holds_skipped = 0

    def sample(self, now: float) -> None:
        f = self.packets
        if f is None:
            return
        try:
            c = int(f())
        except Exception:
            return
        if self._last_count is None or c != self._last_count:
            self._last_count = c
            self._moved_at = now

    def note_bye(self, rx: float, frame: int) -> None:
        r = self.recovery
        with r._lock:
            key = r._state_since
        first = self._bye is None or self._bye[1] != key
        self._bye = (rx, key)
        if first:
            r._log("session_end_bye", client_frame=frame)

    def ending(self, now: float) -> str | None:
        r = self.recovery
        with r._lock:
            state, key = r._state, r._state_since
        if state != "PLAYING":
            return f"state_{str(state).lower()}"
        b = self._bye
        if b is not None and b[1] == key and now - b[0] <= BYE_S:
            return "client_bye"
        if self.packets is not None and self._last_count is not None and (now - self._moved_at) * 1000.0 > PRODUCED_MS:
            return "stream_stopped"
        return None

    def blocks_hold(self, recovery: Any) -> bool:
        """The recovery's `note_input_hold`, first: True = no hold (the client's bye)."""
        if self.ending(self._clock()) != "client_bye":
            return False
        self.holds_skipped += 1
        recovery._log("input_hold_skipped_ending", reason="client_bye")
        return True


class StateMark:
    """On B2's detector: once per silence, at STATE_AT ms, asks for the scratch save. Never blocks the loop."""

    def __init__(self, cores: "Cores", at_ms: int):
        self.cores = cores
        self.at_s = at_ms / 1000.0
        self._marked = 0.0

    # B18: the session's end (SessionEnd); None = B9
    end: Any = None

    def on_quiet(self, now: float, last_any_packet_at: float) -> None:
        if self.end is not None:
            self.end.sample(now)
        if last_any_packet_at <= 0.0 or now - last_any_packet_at < self.at_s or last_any_packet_at == self._marked:
            return
        self._marked = last_any_packet_at
        # B18: no save once the session's end is known
        if self.end is not None:
            why = self.end.ending(now)
            if why:
                self.end.saves_skipped += 1
                self.cores.recovery._log("state_save_skipped", reason=why,
                                         silence_ms=round((now - last_any_packet_at) * 1000.0, 1))
                return
        self.cores.request_save(last_any_packet_at, now)


class Cores:
    """B4's Rewinder's B9 object (`1` and `state` only)."""

    # B33: no rewind without loss (rewind_needs_loss.Rule; the umbrella or PRIVYHUB_REWIND_NEEDS_LOSS=1). None = B9.
    no_loss: Any = None

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
        self.saves_skipped_n64 = 0             # B61
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
        # B61: an N64 session sends no state save into its running core (C23: the core never came back)
        if getattr(self.emulator, "_n64_core", None):
            self.saves_skipped_n64 += 1
            self.recovery._log("state_save_skipped", reason=N64_SKIP, core=self.core(), kind=kind,
                               silence_ms=round((mark_at - silence_start) * 1000.0, 1))
            return
        # B55: a PS2 session's slot-9 save goes through PINE (B49 skipped it)
        if getattr(self.emulator, "_launch_kind", None) == "pcsx2":
            return self._save_ps2(silence_start, mark_at, kind)
        # B69: a GameCube session's slot-9 save is Dolphin's Shift+F9 into the running game
        if getattr(self.emulator, "_launch_kind", None) == "dolphin":
            return self._save_gc(silence_start, mark_at, kind)
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
        # B61: an N64 session's release is a plain resume (no state was saved; the recovery's resume follows)
        if getattr(self.emulator, "_n64_core", None):
            fields.pop("slot", None)
            return rw._row(recovery, "rewind_skipped", fields, reason=N64_RELEASE)
        onset = pending.get("b8_hold_onset", pending["onset"])
        # B33: under 1 s with no loss behind it: resume, no load (the save stays); else today's load, with its why
        if self.no_loss is not None:
            resume, why, terms = self.no_loss.decide(onset)
            if resume:
                with self._lock:
                    self.last_save = None                         # one release per save
                self.no_loss.resumes += 1
                fields.update(method="resume", why=why, **terms)
                fields.pop("slot", None)
                return rw._row(recovery, "input_release", fields)
            self.no_loss.loads += 1
            fields.update(why=why, **terms)
        with self._lock:
            s = self.last_save
        # B12: a save taken at the client's stall matches the stall pause's own onset within 100 ms
        if s is not None and s.get("kind") == "stall" and abs(s["onset"] - onset) <= STALL_MATCH_S:
            onset = s["onset"]
        if s is None or not s.get("ok") or abs(s["onset"] - onset) > MATCH_S:
            return rw._row(recovery, "rewind_skipped", fields, reason="no scratch state for this pause")
        # B55: a PS2 session loads its slot-9 save through PINE (the picture checked after the recovery's resume)
        if getattr(self.emulator, "_launch_kind", None) == "pcsx2":
            return self._release_ps2(rw, recovery, fields, pending, s, onset)
        # B69: a GameCube session loads its slot-9 save by F9 (the picture checked after the recovery's resume)
        if getattr(self.emulator, "_launch_kind", None) == "dolphin":
            return self._release_gc(rw, recovery, fields, pending, s, onset)
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

    # --- B55: the PS2 branches (reached only in a PCSX2 session, i.e. with PRIVYHUB_PS2=1) ---------------------------

    def _spawn(self, fn: Callable[[], None]) -> None:
        """The verifier's thread (a test runs it in place, after its resume)."""
        threading.Thread(target=fn, name="PrivyHub-PS2-State-Verify", daemon=True).start()

    def _ps2_folder(self, ps2: Any) -> Path:
        return Path(self.emulator._project_path(ps2.DATA_DIR)) / "sstates"

    def _save_ps2(self, silence_start: float, mark_at: float, kind: str) -> None:
        import ps2_session as _ps2
        sess = getattr(self.emulator, "_ps2", None)
        if sess is None:
            return
        folder = self._ps2_folder(_ps2)
        lock = getattr(self.emulator, "lock", None) or threading.RLock()
        wall = self._wall()
        with lock:
            folder.mkdir(parents=True, exist_ok=True)
            before = _ps2.state_files(folder)
            t0 = self._clock()
            result = sess.state_message(_ps2.MSG_SAVE_STATE, _ps2.SCRATCH_SLOT)
            sent_at = t0
        ok = result == _ps2.PINE_OK
        ack = "pine ok" if ok else ("pine no answer" if result is None else "pine fail")
        with self._lock:
            self.last_save = {"onset": silence_start, "sent_at": sent_at, "wall": wall, "ack": ack, "ok": ok,
                              "kind": kind, "p2s_before": before}
            self.saves += 1
        self.recovery._log("state_saved" if ok else "state_save_failed", slot=_ps2.SCRATCH_SLOT, core="pcsx2",
                           kind=kind, silence_ms=round((mark_at - silence_start) * 1000.0, 1),
                           save_after_onset_ms=round((sent_at - silence_start) * 1000.0, 1), ack=ack,
                           ps2_states="pine")
        try:
            sess.log(f"PS2 state save: slot {_ps2.SCRATCH_SLOT} pine 0x09 {ack[5:]} ({kind})")
        except Exception:
            pass

    def _release_ps2(self, rw: Any, recovery: Any, fields: dict[str, Any], pending: Mapping[str, Any],
                     s: Mapping[str, Any], onset: float) -> dict[str, Any]:
        import ps2_session as _ps2
        sess = getattr(self.emulator, "_ps2", None)
        slot = _ps2.SCRATCH_SLOT
        fields.update(slot=slot, core="pcsx2", ps2_states="pine",
                      save_after_onset_ms=round((s["sent_at"] - onset) * 1000.0, 1))
        if sess is None:
            return rw._row(recovery, "rewind_failed", fields, reason="no PCSX2 session")
        got = sess.wait_state_file(self._ps2_folder(_ps2), slot, dict(s.get("p2s_before") or {}),
                                   bound=_ps2.RELEASE_SHARE_S)
        if got is None:
            with self._lock:
                self.last_save = None
            return rw._row(recovery, "rewind_skipped", fields, reason="the PS2 state file is not complete")
        lock = getattr(self.emulator, "lock", None) or threading.RLock()
        with lock:
            t0 = self._clock()
            try:
                sess.ensure_pine_pause()
            except Exception as exc:
                with self._lock:
                    self.last_save = None
                return rw._row(recovery, "rewind_failed", fields, reason=f"PCSX2 not paused for the load: {exc}")
            pre = sess.picture()
            offset = sess.log_size()
            result = sess.state_message(_ps2.MSG_LOAD_STATE, slot)
            line = result == _ps2.PINE_OK and sess.wait_log_line(
                sess.log_path, offset, f"Loaded state from slot {slot}.", bound=_ps2.RELEASE_SHARE_S)
            ms = round((self._clock() - t0) * 1000.0, 1)
        with self._lock:
            self.last_save = None                                 # one load per save
        fields.update(rewind_ms=ms, load_ms=ms)
        if result != _ps2.PINE_OK:
            return rw._row(recovery, "rewind_failed", fields, reason="PINE load not acknowledged")
        fields.update(line=bool(line), verification="picture_after_resume")
        try:
            sess.log(f"PS2 state load: slot {slot} pine 0x0a ok; {ms:.0f} ms")
        except Exception:
            pass
        row = rw._row(recovery, "input_release", fields)
        verify_fields = dict(fields)
        self._spawn(lambda: self._verify_ps2(rw, recovery, sess, pre, offset, verify_fields))
        return row

    def _verify_ps2(self, rw: Any, recovery: Any, sess: Any, pre: Any, offset: int, fields: dict[str, Any]) -> None:
        """After the recovery's resume: B52's picture check; static / fault -> the PS1-shaped `rewind_failed` row."""
        import ps2_session as _ps2
        try:
            t0 = sess.clock()
            while sess.status() != _ps2.PINE_RUNNING and sess.clock() - t0 < _ps2.VERIFY_RUNNING_S:
                sess.sleep(_ps2.STATE_POLL_S)
            verdict, seconds = sess.check_picture(pre[0] if pre else None, offset)
        except Exception:
            verdict, seconds = "static", 0.0
        recovery._log("ps2_states", check="picture", verdict=verdict, s=round(float(seconds), 1),
                      slot=fields.get("slot"), via=fields.get("via"))
        try:
            sess.log(f"PS2 state load: slot {fields.get('slot')} picture {verdict} {seconds:.1f}s")
        except Exception:
            pass
        if verdict != "ok":
            rw._row(recovery, "rewind_failed", fields,
                    reason=f"the game did not resume from the save (picture {verdict})")

    # --- B69: the GameCube branches (reached only in a Dolphin session, i.e. with PRIVYHUB_GAMECUBE=1) ----------------

    def _save_gc(self, silence_start: float, mark_at: float, kind: str) -> None:
        import gamecube_session as _gc
        sess = getattr(self.emulator, "_gc", None)
        if sess is None:
            return
        lock = getattr(self.emulator, "lock", None) or threading.RLock()
        wall = self._wall()
        with lock:
            folder = sess.state_dir()
            folder.mkdir(parents=True, exist_ok=True)
            before = _gc.state_files(folder)
            t0 = self._clock()
            ok = bool(sess.press_save(_gc.SCRATCH_SLOT))
            sent_at = t0
        ack = "hotkey sent" if ok else "hotkey not sent"
        with self._lock:
            self.last_save = {"onset": silence_start, "sent_at": sent_at, "wall": wall, "ack": ack, "ok": ok,
                              "kind": kind, "gc_before": before}
            self.saves += 1
        self.recovery._log("state_saved" if ok else "state_save_failed", slot=_gc.SCRATCH_SLOT, core="dolphin",
                           kind=kind, silence_ms=round((mark_at - silence_start) * 1000.0, 1),
                           save_after_onset_ms=round((sent_at - silence_start) * 1000.0, 1), ack=ack,
                           gc_states="hotkey")
        try:
            sess.log(f"GC state save: slot {_gc.SCRATCH_SLOT} {ack} ({kind})")
        except Exception:
            pass

    def _release_gc(self, rw: Any, recovery: Any, fields: dict[str, Any], pending: Mapping[str, Any],
                    s: Mapping[str, Any], onset: float) -> dict[str, Any]:
        import gamecube_session as _gc
        sess = getattr(self.emulator, "_gc", None)
        slot = _gc.SCRATCH_SLOT
        fields.update(slot=slot, core="dolphin", gc_states="hotkey",
                      save_after_onset_ms=round((s["sent_at"] - onset) * 1000.0, 1))
        if sess is None:
            return rw._row(recovery, "rewind_failed", fields, reason="no Dolphin session")
        got = sess.wait_state_file(sess.state_dir(), slot, dict(s.get("gc_before") or {}), bound=_gc.RELEASE_SHARE_S)
        if got is None:
            with self._lock:
                self.last_save = None
            return rw._row(recovery, "rewind_skipped", fields, reason="the GameCube state file is not stable")
        lock = getattr(self.emulator, "lock", None) or threading.RLock()
        with lock:
            t0 = self._clock()
            try:
                sess.ensure_hotkey_pause()
            except Exception as exc:
                with self._lock:
                    self.last_save = None
                return rw._row(recovery, "rewind_failed", fields, reason=f"Dolphin not paused for the load: {exc}")
            pre = sess.picture()
            sent = sess.press_load(slot)
            if sent:
                sess.sleep(RELEASE_SETTLE_GC_S)          # Dolphin's hotkey thread runs the load before the resume key
            ms = round((self._clock() - t0) * 1000.0, 1)
        with self._lock:
            self.last_save = None                                 # one load per save
        fields.update(rewind_ms=ms, load_ms=ms)
        if not sent:
            return rw._row(recovery, "rewind_failed", fields, reason="the load key was not sent (no window)")
        fields.update(verification="picture_after_resume")
        try:
            sess.log(f"GC state load: slot {slot} hotkey; {ms:.0f} ms")
        except Exception:
            pass
        row = rw._row(recovery, "input_release", fields)
        verify_fields = dict(fields)
        self._spawn(lambda: self._verify_gc(rw, recovery, sess, pre, verify_fields))
        return row

    def _verify_gc(self, rw: Any, recovery: Any, sess: Any, pre: Any, fields: dict[str, Any]) -> None:
        """After the recovery's resume: B52's picture check; static -> the PS1-shaped `rewind_failed` row."""
        import gamecube_session as _gc
        try:
            t0 = sess.clock()
            while sess.paused_by is not None and sess.clock() - t0 < _gc.VERIFY_RUNNING_S:
                sess.sleep(_gc.POLL_S)
            verdict, seconds = sess.check_picture(pre[0] if pre else None)
        except Exception:
            verdict, seconds = "static", 0.0
        recovery._log("gc_states", check="picture", verdict=verdict, s=round(float(seconds), 1),
                      slot=fields.get("slot"), via=fields.get("via"))
        try:
            sess.log(f"GC state load: slot {fields.get('slot')} picture {verdict} {seconds:.1f}s")
        except Exception:
            pass
        if verdict != "ok":
            rw._row(recovery, "rewind_failed", fields,
                    reason=f"the game did not resume from the save (picture {verdict})")

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
            # B18: the session's end, on the mark and the recovery (no save, no hold once it is known)
            se = SessionEnd(recovery)
            det.state_mark.end = se
            recovery._session_end = se
    recovery._log("input_hold_rewind_cores_config", mode=m, allow=sorted(ALLOW), slot=(SLOT if m == "state" else None),
                  state_at_ms=at_ms, state_at_note=why)
    # B33: no rewind without loss, inside the umbrella (or PRIVYHUB_REWIND_NEEDS_LOSS=1); absent = nothing imported
    if m == "state" and ((environ.get("PRIVYHUB_REWIND_NEEDS_LOSS") or "").strip() == "1"
                         or ((environ.get("PRIVYHUB_LINK_RECOVERY") or "").strip() == "1"
                             and (environ.get("PRIVYHUB_REWIND_NEEDS_LOSS") or "").strip() != "0")):
        import rewind_needs_loss
        rewind_needs_loss.wire(c, recovery, controller, environ)
    return c
