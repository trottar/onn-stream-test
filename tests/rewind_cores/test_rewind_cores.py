#!/usr/bin/env python3
"""B9: the stall signal's `1` = 400 ms; the hold's rewind per core (`1` allow-list, `all` = B4, `state` = a scratch
savestate loaded into a running core). B2 / B4 / B6 / B7 / B8's tests keep their own files.

    python3 -m unittest discover -s tests/rewind_cores -v

A fake core speaks RetroArch's command interface on loopback UDP: GET_STATUS, PAUSE_TOGGLE, REWIND, SAVE_STATE_SLOT n
(writes `<stem>.state<n>` under a temporary state root and acknowledges), LOAD_STATE_SLOT n (acknowledges when the
file exists; records whether the core was running at the load). The real recovery, B4's real Rewinder and Nci.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import hold_rewind as hr  # noqa: E402
import input_hold as ih  # noqa: E402
import rewind_cores as rc  # noqa: E402
import stall_signal as ss  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402

PSX = "mednafen_psx_hw_libretro.so"
SNES = "snes9x_libretro.so"


class FakeCore(threading.Thread):
    def __init__(self, root: Path, stem: str, ack_load=True):
        super().__init__(daemon=True)
        self.root, self.stem, self.ack_load = root, stem, ack_load
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.settimeout(0.05)
        self.port = self.sock.getsockname()[1]
        self.playing = True
        self.log: list[str] = []
        self.loads: list[bool] = []          # was the core running at each load
        self._stop = threading.Event()

    def run(self):
        while not self._stop.is_set():
            try:
                data, src = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            cmd = data.decode().strip()
            self.log.append(cmd)
            reply = None
            if cmd == "GET_STATUS":
                reply = f"GET_STATUS {'PLAYING' if self.playing else 'PAUSED'} fake,game,crc32=0"
            elif cmd == "PAUSE_TOGGLE":
                self.playing = not self.playing
            elif cmd.startswith("SAVE_STATE_SLOT "):
                n = cmd.split()[1]
                (self.root / f"{self.stem}.state{n}").write_bytes(b"S" * 1024)
                reply = cmd
            elif cmd.startswith("LOAD_STATE_SLOT "):
                n = cmd.split()[1]
                self.loads.append(self.playing)
                if self.ack_load and (self.root / f"{self.stem}.state{n}").is_file():
                    reply = cmd
            if reply is not None:
                self.sock.sendto(reply.encode(), src)

    def stop(self):
        self._stop.set()
        self.join(1.0)
        self.sock.close()


class FakeEmulator:
    def __init__(self, core: FakeCore, core_name: str):
        self.lock = threading.RLock()
        self._network_cmd_port = core.port
        self._paused = False
        self._hold_rewind_core = core_name
        self._core = core

    def _state_root(self):
        return self._core.root

    def _active_state_stem(self):
        return self._core.stem


class FakeController:
    def __init__(self, det=None):
        self._input_hold = det if det is not None else object()
        self.mask = None

    def _neutralize(self, player=None):
        pass

    def set_input_mask(self, mask):
        self.mask = mask


def recovery():
    root = Path(tempfile.mkdtemp(prefix="b9_rec_"))
    calls = []
    rec = ldr.LinkDropRecovery(
        root, pause_game=lambda: calls.append("pause"), resume_game=lambda: calls.append("resume"),
        save_recovery_state=lambda: {}, restart_encoder=lambda: {}, full_start_encoder=lambda: {},
        stream_active=lambda: True, end_session=lambda: None, client_packet_age_ms=lambda: 10.0,
        recovery_save_detail=lambda: {})
    rec._state = ldr.STATE_PLAYING
    rec._state_since = time.monotonic()
    rec.calls = calls
    return rec


def rows(rec):
    p = rec.log_path()
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


class Rig:
    def __init__(self, mode, core_name, ack_load=True, hold="1", b6=True):
        self.state_root = Path(tempfile.mkdtemp(prefix="b9_states_"))
        self.core = FakeCore(self.state_root, "Game (USA)", ack_load=ack_load)
        self.core.start()
        self.emu = FakeEmulator(self.core, core_name)
        self.det = ih.InputHoldDetector(250, lambda ev: None)
        self.ctrl = FakeController(self.det)
        self.rec = recovery()
        env = {"PRIVYHUB_INPUT_HOLD": hold, "PRIVYHUB_INPUT_HOLD_REWIND": mode}
        if b6:
            env["PRIVYHUB_INPUT_HOLD_B6"] = "1"
        self.env = env
        self.rw = hr.wire(self.rec, self.ctrl, self.emu, env)

    def pause_for_hold(self, onset, paused_at):
        """The hold's pause as B2 / B4 leave it: the core paused, the pending on this pause's key."""
        self.core.playing = False
        self.emu._paused = True
        self.rec._state = ldr.STATE_PAUSED_RECOVERING
        self.rec._state_since = time.monotonic()
        self.rw._pending = {"onset": onset, "paused_at": paused_at, "key": self.rec._state_since}

    def wait_saves(self, n, timeout=2.0):
        end = time.monotonic() + timeout
        while self.rw.b9.saves < n and time.monotonic() < end:
            time.sleep(0.01)
        return self.rw.b9.saves

    def stop(self):
        self.core.stop()


class StallThreshold(unittest.TestCase):
    def test_one_is_400_and_150_by_number(self):
        self.assertEqual(ss.parse("1"), (400, None))
        self.assertEqual(ss.parse("150"), (150, None))
        self.assertEqual(ss.parse("400"), (400, None))
        self.assertIsNone(ss.parse("149")[0])

    def test_the_host_acts_at_400_with_one(self):
        rec = recovery()
        sig = ss.StallSignal(rec, ss.parse("1")[0], threaded=False)
        rec._client_stall = sig
        now = time.monotonic()
        for i, age in enumerate((160, 210, 300, 390)):
            sig.handle((ss.KIND_STALL, False, i, 100, age), now)
        self.assertEqual(rec.calls, [])
        sig.handle((ss.KIND_STALL, False, 9, 100, 450), now)
        self.assertEqual(rec.calls, ["pause"])
        self.assertEqual([r["event"] for r in rows(rec)], ["desync_pause", "client_stall"])


class TheConfig(unittest.TestCase):
    BASE = 'video_vsync = "true"\n'

    def test_allow_list_all_and_state(self):
        one = {"PRIVYHUB_INPUT_HOLD": "1", "PRIVYHUB_INPUT_HOLD_REWIND": "rewind"}   # B12: B9's `1` is now `rewind`
        for core in (SNES, "bsnes_libretro.so"):
            self.assertEqual(hr.apply_session_config(self.BASE, core, one), self.BASE + hr.config_block(core, one))
        self.assertEqual(hr.apply_session_config(self.BASE, PSX, one), self.BASE)            # no 1-GB buffer
        self.assertEqual(hr.apply_session_config(self.BASE, "fceumm_libretro.so", one), self.BASE)
        al = dict(one, PRIVYHUB_INPUT_HOLD_REWIND="all")
        self.assertEqual(hr.apply_session_config(self.BASE, PSX, al), self.BASE + hr.config_block(PSX, one))  # B4's
        st = dict(one, PRIVYHUB_INPUT_HOLD_REWIND="state")
        for core in (SNES, PSX):
            self.assertEqual(hr.apply_session_config(self.BASE, core, st), self.BASE)
        self.assertEqual(hr.parse(st), (True, None))
        self.assertEqual(hr.parse(al), (True, None))
        self.assertFalse(hr.parse(dict(one, PRIVYHUB_INPUT_HOLD_REWIND="yes"))[0])

    def test_state_at(self):
        self.assertEqual(rc.parse_state_at({}, 950), (400, None))
        self.assertEqual(rc.parse_state_at({rc.STATE_AT_ENV: "300"}, 950), (300, None))
        self.assertEqual(rc.parse_state_at({}, 250)[0], 200)                                  # B2's H: below it
        self.assertEqual(rc.parse_state_at({rc.STATE_AT_ENV: "960"}, 950)[0], 400)
        self.assertIsNotNone(rc.parse_state_at({rc.STATE_AT_ENV: "960"}, 950)[1])


class AllowList(unittest.TestCase):
    def test_psx_under_one_is_skipped_with_nothing_sent(self):
        rig = Rig("rewind", PSX)                                 # B12: B9's `1` is now `rewind`
        try:
            now = time.monotonic()
            rig.pause_for_hold(now - 1.05, now)
            row = rig.rw.rewind(rig.rec, "input_release")
            self.assertEqual(row["core"], PSX)
            self.assertEqual([r["event"] for r in rows(rig.rec)][-1], "rewind_skipped")
            time.sleep(0.1)
            self.assertEqual(rig.core.log, [])
            self.assertEqual(rig.det.state_mark, None)                                       # no save under `1`
        finally:
            rig.stop()

    def test_snes_under_one_is_b4s_rewind(self):
        rig = Rig("rewind", SNES)                                # B12: B9's `1` is now `rewind`
        try:
            now = time.monotonic()
            rig.pause_for_hold(now - 0.5, now)
            row = rig.rw.rewind(rig.rec, "input_release")
            self.assertEqual(rows(rig.rec)[-1]["event"], "input_release")
            self.assertEqual(row["method"], hr.METHOD)
            self.assertGreater(row["rewound_frames"], 0)
            self.assertIn("REWIND", rig.core.log)
        finally:
            rig.stop()

    def test_all_wires_nothing_and_psx_is_b4s(self):
        rig = Rig("all", PSX)
        try:
            self.assertIsNone(rig.rw.b9)
            now = time.monotonic()
            rig.pause_for_hold(now - 0.5, now)
            rig.rw.rewind(rig.rec, "input_release")
            self.assertIn("REWIND", rig.core.log)
        finally:
            rig.stop()


class StatePath(unittest.TestCase):
    def test_the_mark_saves_once_per_silence_at_400(self):
        rig = Rig("state", PSX)
        try:
            self.assertIsNotNone(rig.det.state_mark)
            self.assertEqual(rig.det.state_mark.at_s, 0.4)
            last = time.monotonic()
            rig.det.on_quiet(last + 0.30, last)
            rig.det.on_quiet(last + 0.39, last)
            self.assertEqual(rig.wait_saves(1, 0.3), 0)
            rig.det.on_quiet(last + 0.41, last)
            rig.det.on_quiet(last + 0.46, last)
            rig.det.on_quiet(last + 0.96, last)
            self.assertEqual(rig.wait_saves(1), 1)
            time.sleep(0.2)
            self.assertEqual(rig.rw.b9.saves, 1)
            self.assertEqual(rig.core.log, [f"SAVE_STATE_SLOT {rc.SLOT}"])
            self.assertTrue((rig.state_root / f"Game (USA).state{rc.SLOT}").is_file())
            saved = [r for r in rows(rig.rec) if r["event"] == "state_saved"]
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]["core"], PSX)
            last2 = last + 2.0
            rig.det.on_quiet(last2 + 0.45, last2)                                            # a new silence
            self.assertEqual(rig.wait_saves(2), 2)
            rig.emu._paused = True                                                            # paused: no save
            last3 = last + 4.0
            rig.det.on_quiet(last3 + 0.45, last3)
            time.sleep(0.2)
            self.assertEqual(rig.rw.b9.saves, 2)
            self.assertEqual(rig.rw.b9.saves_skipped_paused, 1)
        finally:
            rig.stop()

    def test_the_release_loads_into_a_running_core(self):
        rig = Rig("state", PSX)
        try:
            last = time.monotonic() - 0.41                         # the save is sent now: ~410 ms after the onset
            rig.det.on_quiet(last + 0.41, last)
            self.assertEqual(rig.wait_saves(1), 1)
            rig.pause_for_hold(last, last + 1.05)
            row = rig.rw.rewind(rig.rec, "input_release")
            self.assertEqual(rows(rig.rec)[-1]["event"], "input_release", row)
            self.assertEqual(row["method"], "state")
            self.assertEqual(rig.core.log[1:4], ["PAUSE_TOGGLE", f"LOAD_STATE_SLOT {rc.SLOT}", "GET_STATUS"])
            self.assertEqual(rig.core.loads, [True])                                          # a running core
            self.assertTrue(rig.core.playing)
            sa = row["save_after_onset_ms"]
            self.assertGreaterEqual(sa, 400.0)
            self.assertLess(sa, 600.0)
            self.assertEqual(row["net_unattended_frames"], int(round(sa * 60 / 1000.0)))
            self.assertEqual(row["frames_restored"], int(round((1050.0 - sa) * 60 / 1000.0)) - 4)
            self.assertIsNone(rig.rw.b9.last_save)                                            # one load per save
            self.assertEqual(rig.rw.mask.masked(), False)
        finally:
            rig.stop()

    def test_b8s_moved_onset_still_matches(self):
        rig = Rig("state", PSX)
        try:
            last = time.monotonic() - 1.2
            rig.det.on_quiet(last + 0.41, last)
            rig.wait_saves(1)
            rig.pause_for_hold(last, last + 1.05)
            rig.rw._pending.update(onset=last - 0.07, b8_hold_onset=last)
            rig.rw.rewind(rig.rec, "hold_return_stall")
            self.assertEqual(rows(rig.rec)[-1]["event"], "input_release")
        finally:
            rig.stop()

    def test_no_state_for_this_pause_is_skipped_nothing_sent(self):
        for case in ("other_silence", "missing_file", "stale_file", "stall_only"):
            rig = Rig("state", PSX)
            try:
                last = time.monotonic() - 1.2
                if case != "stall_only":
                    rig.det.on_quiet(last + 0.41, last)
                    rig.wait_saves(1)
                n = len(rig.core.log)
                f = rig.state_root / f"Game (USA).state{rc.SLOT}"
                if case == "missing_file":
                    f.rename(f.with_suffix(".moved"))
                if case == "stale_file":
                    os.utime(f, (time.time() - 60, time.time() - 60))
                onset = last + 0.5 if case == "other_silence" else last
                rig.pause_for_hold(onset, last + 1.05)
                rig.rw.rewind(rig.rec, "input_release")
                self.assertEqual(rows(rig.rec)[-1]["event"], "rewind_skipped", case)
                time.sleep(0.05)
                self.assertEqual(len(rig.core.log), n, case)
            finally:
                rig.stop()

    def test_a_refused_load_fails_and_the_resume_proceeds(self):
        rig = Rig("state", PSX, ack_load=False)
        try:
            last = time.monotonic() - 1.2
            rig.det.on_quiet(last + 0.41, last)
            rig.wait_saves(1)
            rig.pause_for_hold(last, last + 1.05)
            rig.rec._last_desync_reason = "input_hold"
            rig.rec.note_input_release(1100.0)
            ev = [r["event"] for r in rows(rig.rec)]
            self.assertEqual(ev[-2:], ["rewind_failed", "resumed"])
            self.assertEqual(rig.rec.calls[-1], "resume")
        finally:
            rig.stop()


class FlagAbsent(unittest.TestCase):
    def _imports(self, env_extra):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        env.update(env_extra)
        code = ("import sys; sys.path.insert(0, 'companion'); import hold_rewind as h, input_hold, stall_signal; "
                "import os; e = dict(os.environ); "
                "print(h.apply_session_config('x = 1\\n', 'mednafen_psx_hw_libretro.so', e) == 'x = 1\\n', "
                "'rewind_cores' in sys.modules, input_hold.InputHoldDetector.state_mark, h.Rewinder.b9)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=120)
        return out.stdout.strip(), out.stderr[-400:]

    def test_absent_and_all_import_nothing(self):
        self.assertEqual(self._imports({})[0], "True False None None")
        self.assertEqual(self._imports({"PRIVYHUB_INPUT_HOLD": "1", "PRIVYHUB_INPUT_HOLD_REWIND": "all"})[0],
                         "False False None None")                                            # B4's block, no B9
        self.assertEqual(self._imports({"PRIVYHUB_INPUT_HOLD": "1", "PRIVYHUB_INPUT_HOLD_REWIND": "1"})[0],
                         "True True None None")


if __name__ == "__main__":
    unittest.main()
