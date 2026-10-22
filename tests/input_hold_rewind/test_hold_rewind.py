#!/usr/bin/env python3
"""B4: rewind on the input hold's release (PRIVYHUB_INPUT_HOLD_REWIND=1).

    python3 -m unittest discover -s tests/input_hold_rewind -v

A fake core speaks RetroArch 1.22.2's command interface over loopback UDP at 60 fps, as measured on the host
(b4_2026-10-22/pause_confirm_lag.json): every pending datagram is read once per frame; a GET_STATUS is answered
with the state before that frame's hotkeys; PAUSE_TOGGLE / REWIND are hotkeys for that frame; playing, the frame
counter goes -1 (REWIND, with history) or +1. A fake emulator pauses / resumes it as EmulatorManager does (status,
toggle, a 50-ms poll). The recovery is the real LinkDropRecovery; the dispatcher is B2's, synchronous.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import hold_rewind as hr  # noqa: E402
import input_hold as ih  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402

FRAME = 1.0 / 60.0


class FakeCore(threading.Thread):
    def __init__(self, honour_rewind=True):
        super().__init__(daemon=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.setblocking(False)
        self.port = self.sock.getsockname()[1]
        self.honour_rewind = honour_rewind
        self.drop_status_after_rewind = 0     # GET_STATUS replies to swallow once a REWIND was seen
        self.counter = 0
        self.paused = False
        self.history = deque(maxlen=600)
        self.timeline = []                    # (monotonic, counter) per frame
        self.rewind_cmds = 0
        self.rewind_steps = 0
        self.last_rewind_counter = None
        self._stop = threading.Event()

    def run(self):
        nxt = time.monotonic()
        while not self._stop.is_set():
            pressed, replies = set(), []
            while True:
                try:
                    data, src = self.sock.recvfrom(256)
                except (BlockingIOError, OSError):
                    break
                cmd = data.decode().strip()
                if cmd == "GET_STATUS":
                    if self.drop_status_after_rewind and self.rewind_cmds:
                        self.drop_status_after_rewind -= 1
                    else:
                        replies.append(src)
                else:
                    pressed.add(cmd)
                    if cmd == "REWIND":
                        self.rewind_cmds += 1
            state = "PAUSED" if self.paused else "PLAYING"
            for src in replies:                                     # the state before this frame's hotkeys
                self.sock.sendto(f"GET_STATUS {state} snes,fake,crc32=0".encode(), src)
            if "PAUSE_TOGGLE" in pressed:
                self.paused = not self.paused
            if not self.paused:
                if "REWIND" in pressed and self.honour_rewind and self.history:
                    self.counter = self.history.pop()
                    self.rewind_steps += 1
                    self.last_rewind_counter = self.counter
                else:
                    self.history.append(self.counter)
                    self.counter += 1
            self.timeline.append((time.monotonic(), self.counter))
            nxt += FRAME
            time.sleep(max(0.0, nxt - time.monotonic()))

    def counter_at(self, t):
        best = None
        for at, c in list(self.timeline):
            if at <= t:
                best = c
        return best

    def stop(self):
        self._stop.set()
        self.join(1.0)
        self.sock.close()


class FakeEmulator:
    """EmulatorManager.pause() / resume() as written: GET_STATUS, PAUSE_TOGGLE, then poll every 50 ms."""

    def __init__(self, core):
        self.lock = threading.RLock()
        self._network_cmd_port = core.port
        self._paused = False
        self.calls = []

    def _req(self, cmd, expect):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(("127.0.0.1", 0))
            s.settimeout(0.45)
            s.sendto(cmd.encode(), ("127.0.0.1", self._network_cmd_port))
            if expect:
                return s.recvfrom(4096)[0].decode().strip()

    def _status(self):
        return self._req("GET_STATUS", True).split()[1]

    def _set(self, want, name):
        with self.lock:
            self.calls.append(name)
            if self._status() != want:
                self._req("PAUSE_TOGGLE", False)
                deadline = time.monotonic() + 1.5
                while self._status() != want:
                    if time.monotonic() > deadline:
                        raise RuntimeError(f"not {want}")
                    time.sleep(0.05)
            self._paused = want == "PAUSED"

    def pause(self):
        self._set("PAUSED", "pause")

    def resume(self):
        self._set("PLAYING", "resume")


class FakeController:
    _input_hold = object()                    # B2 wired its detector

    def __init__(self):
        self.neutralized = 0
        self.mask = None

    def _neutralize(self, player=None):
        self.neutralized += 1

    def set_input_mask(self, mask):
        self.mask = mask


def session_cfg(on=True):
    d = Path(tempfile.mkdtemp(prefix="b4_cfg_"))
    p = d / "privyhub-session.cfg"
    p.write_text('video_vsync = "true"\n' + ('rewind_enable = "true"\n' if on else ""))
    return p


class Rig:
    """A live fake core, the fake emulator, the real recovery, B2's dispatcher (synchronous), the rewinder."""

    def __init__(self, rewind=True, honour_rewind=True, cfg_on=True, cap=30, nci_factory=hr.Nci):
        self.core = FakeCore(honour_rewind)
        self.core.start()
        self.emu = FakeEmulator(self.core)
        self.ctrl = FakeController()
        self.root = Path(tempfile.mkdtemp(prefix="b4_rec_"))
        self.rec = ldr.LinkDropRecovery(
            self.root, pause_game=self.emu.pause, resume_game=self.emu.resume,
            save_recovery_state=lambda: {}, restart_encoder=lambda: {}, full_start_encoder=lambda: {},
            stream_active=lambda: True, end_session=lambda: None, client_packet_age_ms=lambda: 10.0,
            recovery_save_detail=lambda: {})
        self.rec._state = ldr.STATE_PLAYING
        self.rec._state_since = time.monotonic()
        self.rw = None
        if rewind:
            self.rw = hr.Rewinder(self.emu, self.ctrl, cap, session_config=session_cfg(cfg_on),
                                  nci_factory=nci_factory)
            self.rec._input_hold_rewind = self.rw
        self.d = ih.HoldDispatcher(self.rec, lambda: self.emu._paused, threaded=False)
        time.sleep(0.3)

    def hold(self, silence_s=0.25):
        """The player's last packet now; B2's detector fires `silence_s` later (put + handle)."""
        onset = time.monotonic()
        onset_counter = self.core.counter_at(onset)
        time.sleep(silence_s)
        ev = ("hold", round((time.monotonic() - onset) * 1000.0, 1))
        self.d.put(ev)
        self.d.handle(ev)
        return onset, onset_counter

    def release(self, held_ms=500.0):
        self.d.handle(("release", held_ms))

    def rows(self):
        p = self.rec.log_path()
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []

    def events(self):
        return [r["event"] for r in self.rows()]

    def close(self):
        self.core.stop()


class TheCount(unittest.TestCase):
    def test_counter_from_the_two_stamps(self):
        rw = hr.Rewinder(object(), FakeController(), 30)
        p = {"onset": 100.0, "paused_at": 100.0 + 22 / 60.0}
        self.assertEqual(rw.counter_before(p), 22 - hr.PAUSE_CONFIRM_LAG_FRAMES)
        self.assertEqual(rw.counter_before({"onset": 100.0, "paused_at": 100.01}), 0)

    def test_fifo_stays_aligned_across_a_skipped_hold(self):
        rw = hr.Rewinder(object(), FakeController(), 30)
        rec = type("R", (), {"_state_since": 7.0})()
        rw.stamp(("hold", 250.0), 10.25)                # skipped (the user's pause): popped, no pending
        rw.stamp(("release", 400.0), 10.40)
        rw.stamp(("hold", 300.0), 20.30)
        rw.on_handle(("hold", 250.0))
        rw.note_paused(False, None, rec)
        self.assertIsNone(rw._pending)
        rw.on_handle(("release", 400.0))
        rw.on_handle(("hold", 300.0))
        rw.note_paused(True, 20.40, rec)
        self.assertAlmostEqual(rw._pending["onset"], 20.0)
        self.assertEqual(rw._pending["key"], 7.0)


class TheCap(unittest.TestCase):
    def test_parse_cap(self):
        self.assertEqual(hr.parse_cap(None), (30, None))
        self.assertEqual(hr.parse_cap("10"), (10, None))
        self.assertEqual(hr.parse_cap("5"), (5, None))
        self.assertEqual(hr.parse_cap("120"), (120, None))
        for bad in ("4", "121", "x", "-3"):
            cap, why = hr.parse_cap(bad)
            self.assertEqual(cap, 30, bad)
            self.assertTrue(why and "ignored" in why, bad)

    def test_requested_is_capped(self):
        rig = Rig(cap=10)
        try:
            rig.hold(silence_s=0.6)                       # ~36 + frames: capped at 10
            rig.release()
            row = [r for r in rig.rows() if r["event"] == "input_release"][0]
            self.assertGreater(row["counter_before"], 10)
            self.assertEqual(row["requested_frames"], 10)
            self.assertLessEqual(abs(row["rewound_frames"] - 10), 1)
        finally:
            rig.close()


class TheRewind(unittest.TestCase):
    def test_requested_on_release_confirmed_back_to_the_onset(self):
        rig = Rig()
        try:
            onset, onset_counter = rig.hold()
            self.assertEqual(rig.emu.calls, ["pause"])
            time.sleep(0.5)                               # the blackout
            seen = []

            class Spy(hr.Nci):
                def send(self, cmd):
                    seen.append(rig.rw.mask.masked())
                    super().send(cmd)

            rig.rw._nci_factory = Spy
            rig.release()
            self.assertTrue(seen and all(seen))           # masked on every datagram of the rewind
            self.assertFalse(rig.rw.mask.masked())        # and not after
            self.assertGreaterEqual(rig.ctrl.neutralized, 1)
            self.assertEqual(rig.events(), ["desync_pause", "input_release", "resumed"])
            row = [r for r in rig.rows() if r["event"] == "input_release"][0]
            for k in ("requested_frames", "rewound_frames", "counter_before", "counter_after", "onset_to_pause_ms",
                      "rewind_ms", "via", "method", "cap", "pause_confirm_lag_frames"):
                self.assertIn(k, row)
            self.assertEqual(row["via"], "input_release")
            self.assertGreaterEqual(row["requested_frames"], 15)
            self.assertLessEqual(abs(row["counter_after"]), 1)
            self.assertLessEqual(abs(row["rewound_frames"] - row["requested_frames"]), 1)
            # the fake core's own counter: back at the onset's, +-1
            self.assertIsNotNone(rig.core.last_rewind_counter)
            self.assertLessEqual(abs(rig.core.last_rewind_counter - onset_counter), 1,
                                 (rig.core.last_rewind_counter, onset_counter, row))
            self.assertEqual(rig.emu.calls, ["pause", "resume"])
            self.assertEqual(rig.rec.current_state(), ldr.STATE_PLAYING)
            self.assertFalse(rig.core.paused)
        finally:
            rig.close()


class RewindFailed(unittest.TestCase):
    def _assert_resumed(self, rig, reason_part):
        ev = rig.events()
        self.assertEqual(ev, ["desync_pause", "rewind_failed", "resumed"], rig.rows())
        row = [r for r in rig.rows() if r["event"] == "rewind_failed"][0]
        self.assertIn(reason_part, row["reason"])
        self.assertEqual(rig.emu.calls, ["pause", "resume"])
        self.assertEqual(rig.rec.current_state(), ldr.STATE_PLAYING)
        self.assertFalse(rig.core.paused)
        self.assertFalse(rig.rw.mask.masked())
        return row

    def test_status_not_answered_within_two_frames(self):
        rig = Rig()
        try:
            rig.hold()
            rig.core.drop_status_after_rewind = 1
            rig.release()
            self._assert_resumed(rig, "not answered within 2 frames")
        finally:
            rig.close()

    def test_session_config_without_rewind(self):
        rig = Rig(cfg_on=False)
        try:
            rig.hold()
            rig.release()
            self._assert_resumed(rig, "no rewind_enable")
            self.assertEqual(rig.core.rewind_cmds, 0)
        finally:
            rig.close()

    def test_no_port(self):
        rig = Rig()
        try:
            rig.hold()
            port, rig.emu._network_cmd_port = rig.emu._network_cmd_port, None
            orig_set = rig.emu._set
            rig.emu._set = lambda w, n: (setattr(rig.emu, "_network_cmd_port", port), orig_set(w, n))[1]
            rig.release()
            self._assert_resumed(rig, "no RetroArch command port")
        finally:
            rig.close()

    def test_the_transport_raises(self):
        def broken(port):
            raise OSError("socket refused")
        rig = Rig(nci_factory=broken)
        try:
            rig.hold()
            rig.release()
            self._assert_resumed(rig, "socket refused")
        finally:
            rig.close()


class FlagAbsent(unittest.TestCase):
    def test_no_rewinder_b2_exactly(self):
        rig = Rig(rewind=False)
        try:
            rig.hold()
            rig.release()
            self.assertEqual(rig.events(), ["desync_pause", "resumed"])
            self.assertEqual(rig.rows()[-1]["via"], "input_release")
            self.assertEqual(rig.core.rewind_cmds, 0)
            self.assertEqual(rig.emu.calls, ["pause", "resume"])
            self.assertIsNone(ldr.LinkDropRecovery._input_hold_rewind)
        finally:
            rig.close()

    def test_parse_and_wire(self):
        self.assertEqual(hr.parse({}), (False, None))
        self.assertEqual(hr.parse({"PRIVYHUB_INPUT_HOLD_REWIND": "1", "PRIVYHUB_INPUT_HOLD": "250"}), (True, None))
        for env in ({"PRIVYHUB_INPUT_HOLD_REWIND": "0", "PRIVYHUB_INPUT_HOLD": "250"},
                    {"PRIVYHUB_INPUT_HOLD_REWIND": "yes", "PRIVYHUB_INPUT_HOLD": "250"},
                    {"PRIVYHUB_INPUT_HOLD_REWIND": "1"},
                    {"PRIVYHUB_INPUT_HOLD_REWIND": "1", "PRIVYHUB_INPUT_HOLD": "0"}):
            on, why = hr.parse(env)
            self.assertFalse(on, env)
            self.assertTrue(why.startswith("ignored"), env)
        logged = []
        rec = type("R", (), {"_log": lambda self, e, **k: logged.append((e, k))})()
        self.assertIsNone(hr.wire(rec, FakeController(), object(), {"PRIVYHUB_INPUT_HOLD_REWIND": "yes",
                                                                   "PRIVYHUB_INPUT_HOLD": "250"}))
        self.assertEqual([(e, k["ignored"]) for e, k in logged], [("input_hold_rewind_config", True)])
        logged.clear()
        self.assertIsNone(hr.wire(rec, FakeController(), object(), {}))
        self.assertEqual(logged, [])
        ctrl = FakeController()
        rw = hr.wire(rec, ctrl, object(), {"PRIVYHUB_INPUT_HOLD_REWIND": "1", "PRIVYHUB_INPUT_HOLD": "250",
                                           "PRIVYHUB_INPUT_HOLD_REWIND_CAP": "500"})
        self.assertIs(rec._input_hold_rewind, rw)
        self.assertIs(ctrl.mask, rw.mask)
        self.assertEqual(rw.cap, 30)
        self.assertEqual(logged[-1][1]["ignored"], False)
        self.assertIn("cap ignored", logged[-1][1]["cap_note"])
        self.assertIsNone(hr.wire(rec, type("C", (), {"_input_hold": None})(), object(),
                                  {"PRIVYHUB_INPUT_HOLD_REWIND": "1", "PRIVYHUB_INPUT_HOLD": "250"}))

    def _imports(self, env_extra):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        env.update(env_extra)
        code = ("import sys; sys.path.insert(0, 'companion'); import native_session_io as n; "
                "from games import emulator_manager as em; "
                "print('hold_rewind' in sys.modules, em._hold_rewind is None, n.NativeControllerBridge._input_mask)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=120)
        return out.stdout.strip(), out.stderr[-500:]

    def test_fresh_process_hold_only_imports_nothing(self):
        out, err = self._imports({"PRIVYHUB_INPUT_HOLD": "250"})
        self.assertEqual(out, "False True None", err)
        out, err = self._imports({})
        self.assertEqual(out, "False True None", err)

    def test_fresh_process_both_flags_imports_it(self):
        out, err = self._imports({"PRIVYHUB_INPUT_HOLD": "250", "PRIVYHUB_INPUT_HOLD_REWIND": "1"})
        self.assertEqual(out, "True False None", err)


GEN = r"""
import hashlib, importlib.util, json, re, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
spec = importlib.util.spec_from_file_location("emx", sys.argv[2])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
root = Path(sys.argv[3]); em = object.__new__(m.EmulatorManager); em.project_root = root.resolve()
if len(sys.argv) > 4:
    em._hold_rewind_core = sys.argv[4]
out = em._prepare_retroarch_session_config(root / "retroarch.cfg", root / "privyhub-input.cfg")
text = out.read_text()
masked = re.sub(r'network_cmd_port = "\d+"', 'network_cmd_port = "<port>"', text)
print(json.dumps({"sha256": hashlib.sha256(masked.encode()).hexdigest(), "text": masked}))
"""


def gen_root():
    root = Path(tempfile.mkdtemp(prefix="b4_gen_"))
    (root / "autoconfig").mkdir()
    (root / "retroarch.cfg").write_text('# PrivyHub-managed RetroArch configuration\nvideo_vsync = "true"\n'
                                        'joypad_autoconfig_dir = "autoconfig"\nstate_slot = "0"\n')
    (root / "privyhub-input.cfg").write_text('# PrivyHub Phase A controller profile\n'
                                             'network_cmd_enable = "true"\nnetwork_cmd_port = "54321"\n')
    return root


_GEN_ROOT = []


def generate(module_path, env_extra, core=None):
    """One project root for every generation (its autoconfig path is in the config text)."""
    if not _GEN_ROOT:
        _GEN_ROOT.append(gen_root())
    env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    env.update(env_extra)
    args = [sys.executable, "-B", "-c", GEN, str(ROOT / "companion"), str(module_path), str(_GEN_ROOT[0])]
    if core:
        args.append(core)
    out = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    if out.returncode:
        raise AssertionError(out.stderr[-800:])
    return json.loads(out.stdout)


PREDECESSOR = Path(os.environ.get("B4_PREDECESSOR_EM", ""))


class TheConfig(unittest.TestCase):
    ON = {"PRIVYHUB_INPUT_HOLD": "250", "PRIVYHUB_INPUT_HOLD_REWIND": "1"}

    @unittest.skipUnless(PREDECESSOR.is_file(), "B4_PREDECESSOR_EM (the predecessor emulator_manager.py) not given")
    def test_masked_hash_flag_absent_is_the_predecessor(self):
        new = ROOT / "companion" / "games" / "emulator_manager.py"
        a = generate(PREDECESSOR, {})
        self.assertEqual(generate(new, {})["sha256"], a["sha256"])
        self.assertEqual(generate(new, {"PRIVYHUB_INPUT_HOLD": "250"})["sha256"], a["sha256"])
        self.assertEqual(generate(new, {"PRIVYHUB_INPUT_HOLD": "250", "PRIVYHUB_INPUT_HOLD_REWIND": "yes"})["sha256"],
                         a["sha256"])
        on = generate(new, self.ON, "snes9x_libretro.so")
        self.assertTrue(on["text"].startswith(a["text"]))
        self.assertEqual(on["text"][len(a["text"]):], hr.config_block("snes9x_libretro.so", self.ON))

    def test_the_keys_once_and_the_bytes_per_core(self):
        new = ROOT / "companion" / "games" / "emulator_manager.py"
        want = {"snes9x_libretro.so": 27_262_976, "bsnes_libretro.so": 9_437_184,
                "mednafen_psx_hw_libretro.so": 537_919_488, "fceumm_libretro.so": 20_971_520}
        for core, size in want.items():
            text = generate(new, self.ON, core)["text"]
            for key in hr.KEYS:
                self.assertEqual(len(re.findall(rf"(?m)^{key} = ", text)), 1, (core, key))
            self.assertIn(f'rewind_buffer_size = "{size}"', text, core)
            self.assertIn('rewind_enable = "true"', text)
            self.assertIn('rewind_granularity = "1"', text)
            self.assertIn('audio_rewind_mute = "true"', text)
        self.assertEqual(hr.buffer_bytes("snes9x_libretro.so", 10), 10 * 1024 * 1024)   # 823,536 x 12 = 9.42 MiB -> 10
        text = generate(new, dict(self.ON, PRIVYHUB_INPUT_HOLD_REWIND_CAP="10"), "mednafen_psx_hw_libretro.so")["text"]
        self.assertIn(f'rewind_buffer_size = "{hr.buffer_bytes("mednafen_psx_hw_libretro.so", 10)}"', text)

    def test_a_base_with_a_rewind_key_is_left_alone(self):
        base = 'video_vsync = "true"\nrewind_enable = "false"\n'
        self.assertEqual(hr.apply_session_config(base, "snes9x_libretro.so", self.ON), base)
        self.assertEqual(hr.apply_session_config("x = 1\n", "snes9x_libretro.so", {}), "x = 1\n")


class TheHandover(unittest.TestCase):
    def _exit(self, rig):
        rig.rec.enable_controller_exit(True)
        now = time.monotonic()
        self.assertFalse(rig.rec._maybe_exit_controller_pause(now, 20.0))
        self.assertFalse(rig.rec._maybe_exit_controller_pause(now + 0.3, 20.0))
        rig.rec._heartbeat_history = [(now + 0.4, 30)]
        self.assertTrue(rig.rec._maybe_exit_controller_pause(now + 0.5, 20.0))

    def test_v2_takes_the_hold_over_and_its_exit_rewinds_once(self):
        rig = Rig()
        try:
            onset, onset_counter = rig.hold()
            rig.rec.note_client_silence(5350.0)                 # v2's controller_silence while held
            rig.release(5600.0)                                  # the hold no longer owns it: no rewind here
            self.assertNotIn("input_release", rig.events())
            self._exit(rig)
            ev = rig.events()
            self.assertEqual(ev, ["desync_pause", "input_hold_handover", "input_release", "resumed"])
            row = [r for r in rig.rows() if r["event"] == "input_release"][0]
            self.assertEqual(row["via"], "controller_return")
            self.assertLessEqual(abs(rig.core.last_rewind_counter - onset_counter), 1)
            self.assertEqual(rig.rows()[-1]["via"], "controller_return")
            self.assertEqual(rig.emu.calls, ["pause", "resume"])
        finally:
            rig.close()

    def test_a_v2_pause_without_a_hold_is_not_rewound(self):
        rig = Rig()
        try:
            rig.rec.note_client_silence(5350.0)
            self._exit(rig)
            self.assertEqual(rig.events(), ["desync_pause", "resumed"])
            self.assertEqual(rig.core.rewind_cmds, 0)
        finally:
            rig.close()

    def test_a_stale_pending_hold_is_not_used_by_a_later_pause(self):
        rig = Rig()
        try:
            rig.hold()
            rig.rec.note_client_desync("output_silence", 1300.0)   # the client's desync takes the hold over
            self.assertTrue(rig.rec.note_stream_ready())           # the client's gate resumes it (no rewind there)
            rig.emu.resume()
            time.sleep(0.05)
            rig.rec.note_client_silence(5350.0)                    # a later v2 pause of its own
            self._exit(rig)
            self.assertNotIn("input_release", rig.events())
            self.assertEqual(rig.core.rewind_cmds, 0)
        finally:
            rig.close()


class TheHooks(unittest.TestCase):
    def _ifs(self, rel, test_text):
        tree = ast.parse((ROOT / "companion" / rel).read_text())
        return [n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test) == test_text]

    def test_shapes(self):
        self.assertEqual(len(self._ifs("native_session_io.py",
                                       "self._input_mask is not None and self._input_mask.masked()")), 1)
        self.assertEqual(len(self._ifs("input_hold.py",
                                       "getattr(self.recovery, '_input_hold_rewind', None) is not None")), 3)
        self.assertEqual(len(self._ifs("games/link_drop_recovery.py", "self._input_hold_rewind is not None")), 2)
        self.assertEqual(len(self._ifs("plugins/games.py", "_hold_rewind is not None")), 1)
        self.assertEqual(len(self._ifs("games/emulator_manager.py", "_hold_rewind is not None")), 2)
        for rel in ("plugins/games.py", "games/emulator_manager.py"):
            tree = ast.parse((ROOT / "companion" / rel).read_text())
            guarded = [n for n in tree.body if isinstance(n, ast.If) and "import hold_rewind" in ast.unparse(n)]
            self.assertEqual(len(guarded), 1, rel)
            self.assertIn("PRIVYHUB_INPUT_HOLD_REWIND", ast.unparse(guarded[0].test))
            top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
            self.assertFalse(any("hold_rewind" in ast.unparse(n) for n in top), rel)


class UnattendedNet(unittest.TestCase):
    def _logs(self):
        d = Path(tempfile.mkdtemp(prefix="b4_uf_"))
        (d / "native_frame_sizes.jsonl").write_text("".join(
            json.dumps({"at_utc": f"2026-10-22T00:00:{s:02d}.000Z", "frames": 60}) + "\n" for s in range(0, 40)))
        (d / "native_stream_ctrl_gaps.log").write_text("".join(json.dumps(r) + "\n" for r in (
            {"start_utc": "2026-10-22T00:00:10.000Z", "end_utc": "2026-10-22T00:00:14.000Z", "gap_ms": 4000},
            {"start_utc": "2026-10-22T00:00:30.000Z", "end_utc": "2026-10-22T00:00:31.000Z", "gap_ms": 1000})))
        (d / "native_stream_recovery.log").write_text("".join(json.dumps(r) + "\n" for r in (
            {"at_utc": "2026-10-22T00:00:10.330Z", "event": "desync_pause", "trigger": "input_hold"},
            {"at_utc": "2026-10-22T00:00:14.330Z", "event": "input_release", "rewound_frames": 19},
            {"at_utc": "2026-10-22T00:00:14.340Z", "event": "resumed", "via": "input_release"})))
        return d

    def test_net(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import unattended_frames as uf
        d = self._logs()
        a, b = uf.ts("2026-10-22T00:00:00"), uf.ts("2026-10-22T00:00:40")
        plain = uf.measure(d, a, b)
        self.assertNotIn("net", plain)
        r = uf.measure(d, a, b, net=True)
        eps = {e["start"]: e for e in r["net"]["episodes"]}
        first = eps["2026-10-22T00:00:10.000Z"]
        self.assertAlmostEqual(first["unattended_frames_core_running"], 0.08 * 60, delta=0.5)   # 250 -> 330 ms
        self.assertEqual(first["rewound_frames"], 19.0)
        self.assertEqual(first["unattended_frames_core_running_net"], 0.0)
        self.assertAlmostEqual(first["rewound_beyond_threshold"], 19 - 4.8, delta=0.5)
        second = eps["2026-10-22T00:00:30.000Z"]
        self.assertEqual(second["rewound_frames"], 0.0)
        self.assertAlmostEqual(second["unattended_frames_core_running_net"], 45.0, delta=0.5)
        self.assertAlmostEqual(r["net"]["unattended_frames_core_running_net"], 45.0, delta=0.5)
        self.assertEqual(r["net"]["rewinds"], 1)
        self.assertEqual(r["net"]["rewound_unassigned"], 0.0)

    def test_without_net_the_cli_output_is_the_predecessors(self):
        pred = Path(os.environ.get("B4_PREDECESSOR_UF", ""))
        if not pred.is_file():
            self.skipTest("B4_PREDECESSOR_UF not given")
        d = self._logs()
        args = ["--logs", str(d), "--span", "2026-10-22T00:00:00", "2026-10-22T00:00:40"]
        new = subprocess.run([sys.executable, "-B", str(ROOT / "tools" / "unattended_frames.py"), *args],
                             capture_output=True, text=True, timeout=60).stdout
        old = subprocess.run([sys.executable, "-B", str(pred), *args], capture_output=True, text=True,
                             timeout=60).stdout
        self.assertEqual(new, old)
        self.assertTrue(new)


if __name__ == "__main__":
    unittest.main()
