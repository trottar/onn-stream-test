#!/usr/bin/env python3
"""B54 (host): `native-stream-relaunch-ports` -- the same title relaunched mid-session with the multitap, play resuming
where it was. Fakes record the call order: pause / save / stream stop / stop / launch(4) / resume / settle /
load(the relaunch save) / pause / stream start on PS1; the recorded `restarted` path on PS2 (no save, no load); the
refusals touch nothing; the new launch failing -> the previous ports; the load failing -> `restarted`; the rows.
`load_recovery_state_running()` with no source = today's path.

    python3 -m unittest discover -s tests/relaunch_ports -v
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

from games import emulator_manager as em  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402
import players_session as ps  # noqa: E402
import relaunch_ports as rp  # noqa: E402

spec = importlib.util.spec_from_file_location("b54_games_plugin", ROOT / "companion" / "plugins" / "games.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def rig(kind="retroarch", system="ps1", multitap=False, cheat=False, fail_launch=0, fail_load=False,
        args=True, fail_save=False):
    root = Path(tempfile.mkdtemp(prefix="b54_relaunch_"))
    rec = ldr.LinkDropRecovery(
        root, pause_game=lambda: None, resume_game=lambda: None, save_recovery_state=lambda: {},
        restart_encoder=lambda: {}, full_start_encoder=lambda: {}, stream_active=lambda: True,
        end_session=lambda: None, client_packet_age_ms=lambda: 10.0, recovery_save_detail=lambda: {})
    calls = []
    clock = Clock()
    state = Path(root / "content-one.state.relaunch")

    class Emu:
        active_game = {"id": "g1", "system": system, "title": "t"}
        _launch_kind = "pcsx2" if kind == "pcsx2" else None
        _active_cheat_session = {"session_kind": "cheat"} if cheat else None
        _players_session = ps.plan(system, 4, 1) if multitap else None
        pid = 10
        paused = False
        launches = 0

        def status(self):
            return {"active": True, "paused": self.paused, "pid": self.pid}

        def ps1_multitap(self, g):
            return {"enabled": False}

        def pause(self):
            calls.append("pause"); clock.t += 0.1; self.paused = True; return self.status()

        def resume(self):
            calls.append("resume"); self.paused = False; return self.status()

        def save_relaunch_state(self):
            calls.append("save"); clock.t += 1.2
            if fail_save:
                raise em.EmulatorError("no state")
            return {"ok": True, "state_path": state}

        def stop(self):
            calls.append("stop"); clock.t += 1.5; return {"stopped": True}

        def launch(self, game, **kw):
            calls.append(("launch", kw.get("players_chosen"))); clock.t += 2.5
            Emu.launches += 1
            if Emu.launches <= fail_launch:
                raise em.EmulatorError("RetroArch exited during startup")
            self.pid += 1
            self.paused = False
            self._players_session = ps.plan(system, kw["players_chosen"], 1)
            return {"active": True}

        def load_recovery_state_running(self, source=None):
            calls.append(("load", source)); clock.t += 0.4
            if fail_load:
                raise em.EmulatorError("RetroArch reported Failed to load state")
            return {"accepted": True}

    class Stream:
        DEFAULT_PORT = 48100

        def stop(self):
            calls.append("stream_stop"); return {}

        def start(self, **kw):
            calls.append(("stream_start", kw["managed_process_id"], kw["port"])); clock.t += 0.8; return {"active": True}

        def end_game_session(self):
            calls.append("end_game_session"); return {}

    p = object.__new__(G.GamesPlugin)
    p.PROJECT_ROOT = root
    p._emulator = Emu()
    p._recovery = rec
    p._native_stream = Stream()
    p._recovery_start_args = {"client_ip": "127.0.0.1", "port": 48100} if args else None
    return p, rec, calls, clock, state


def rows(rec, event):
    return [r for r in (json.loads(x) for x in rec.log_path().read_text().splitlines()) if r["event"] == event] \
        if rec.log_path().exists() else []


class Sequence(unittest.TestCase):
    def test_ps1_the_state_round_trip_in_order(self):
        p, rec, calls, clock, state = rig()
        r = rp.run(p, 4, 3, clock=clock, sleep=clock.sleep)
        self.assertEqual(calls, ["pause", "save", "stream_stop", "stop", ("launch", 4), "resume",
                                 ("load", state), "pause", ("stream_start", 11, 48100)])
        self.assertTrue(r["ok"])
        self.assertEqual(r["relaunch"]["state"], "loaded")
        self.assertEqual(r["relaunch"]["steps_ms"]["settle"], 1000)          # the 1.0-s settle before the load
        self.assertEqual(r["relaunch"]["total_ms"], 7600)          # 0.1+1.2+1.5+2.5+1.0+0.4+0.1+0.8 s
        self.assertEqual(r["ports_set"], {"players_chosen": 4, "ports": 4, "players": 4, "multitap": True,
                                          "multitap_available": True, "source": "relaunch"})
        row = rows(rec, "relaunch_ports")[-1]
        self.assertEqual((row["ok"], row["state"], row["players"], row["players_joined"], row["within_budget"]),
                         (True, "loaded", 4, 3, True))
        self.assertEqual(rows(rec, "ports_set")[-1]["source"], "relaunch")

    def test_ps2_restarts_the_title_recorded(self):
        p, rec, calls, clock, _ = rig(kind="pcsx2", system="ps2")
        r = rp.run(p, 4, 3, clock=clock, sleep=clock.sleep)
        self.assertEqual(calls, ["pause", "stream_stop", "stop", ("launch", 4), "pause", ("stream_start", 11, 48100)])
        self.assertEqual(r["relaunch"]["state"], "restarted")
        self.assertEqual(rows(rec, "relaunch_ports")[-1]["reason"], "ps2_no_relaunch_state")

    def test_the_launch_failing_brings_the_previous_ports_back(self):
        p, rec, calls, clock, state = rig(fail_launch=1)
        r = rp.run(p, 4, 3, clock=clock, sleep=clock.sleep)
        self.assertIn(("launch", 4), calls); self.assertIn(("launch", 2), calls)
        self.assertIn(("load", state), calls)
        self.assertFalse(r["ok"])
        self.assertEqual(r["relaunch"]["fallback"], "previous_ports")
        self.assertEqual(r["ports_set"]["players"], 2)

    def test_both_launches_failing_end_the_session(self):
        p, rec, calls, clock, _ = rig(fail_launch=2)
        with self.assertRaises(RuntimeError):
            rp.run(p, 4, 3, clock=clock, sleep=clock.sleep)
        self.assertEqual(calls[-1], "end_game_session")
        self.assertTrue(rows(rec, "relaunch_ports")[-1]["ended"])

    def test_the_load_failing_is_a_restart(self):
        p, rec, calls, clock, _ = rig(fail_load=True)
        r = rp.run(p, 4, 3, clock=clock, sleep=clock.sleep)
        self.assertTrue(r["ok"])
        self.assertEqual(r["relaunch"]["state"], "restarted")
        self.assertIn("load_error", rows(rec, "relaunch_ports")[-1])
        self.assertEqual(calls[-1][0], "stream_start")

    def test_refusals_touch_nothing(self):
        for kw, n in (({"system": "nes"}, 4), ({"cheat": True}, 4), ({"args": False}, 4), ({"multitap": True}, 4),
                      ({}, 3)):
            p, rec, calls, clock, _ = rig(**kw)
            with self.assertRaises(rp.RelaunchRefused):
                rp.run(p, n, 3, clock=clock, sleep=clock.sleep)
            self.assertEqual(calls, [], kw)
        p, rec, calls, clock, _ = rig(fail_save=True)        # the save fails: only the pause happened
        with self.assertRaises(rp.RelaunchRefused):
            rp.run(p, 4, 3, clock=clock, sleep=clock.sleep)
        self.assertEqual(calls, ["pause", "save"])

    def test_the_endpoint(self):
        p, rec, calls, clock, state = rig()
        orig = rp.run
        rp.run = lambda plugin, players, joined: orig(plugin, players, joined, clock=clock, sleep=clock.sleep)
        try:
            r = p.handle_post_request("native-stream-relaunch-ports", "players=4&players_joined=3", "127.0.0.1")
            self.assertTrue(r["ok"]); self.assertEqual(r["ports_set"]["source"], "relaunch")
            r2 = p.handle_post_request("native-stream-relaunch-ports", "players=4&players_joined=3", "127.0.0.1")
            self.assertFalse(r2["ok"]); self.assertIn("already", r2["refused"])   # four ports already
            self.assertEqual(r2["ports_set"]["players"], 4)
            self.assertEqual(rows(rec, "relaunch_ports")[-1]["refused"], "The session already has these ports")
        finally:
            rp.run = orig


class Manager(unittest.TestCase):
    def bare(self):
        m = object.__new__(em.EmulatorManager)
        m._launch_kind = None
        m.lock = threading.RLock()
        m._refresh_process = lambda: None
        m.process = types.SimpleNamespace(poll=lambda: None)
        m.active_game = {"id": "g1"}
        m._paused = False
        m._retroarch_network_status = lambda: "PLAYING"
        root = Path(tempfile.mkdtemp(prefix="b54_mgr_"))
        rec_path = root / "content-one.state.recovery"
        rec_path.write_bytes(b"R" * 64)
        rel_path = root / "content-one.state.relaunch"
        rel_path.write_bytes(b"L" * 64)
        m._recovery_state_path_for_active = lambda: rec_path
        m._active_state_stem = lambda: "content-one"
        staged = []
        m._copy_state_file = lambda a, b: (staged.append(a), b.write_bytes(a.read_bytes()))
        import hashlib
        m._state_file_diagnostic = lambda p: {"size_bytes": p.stat().st_size,
                                              "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        m._retroarch_session_log_position = lambda: 0
        m.record_save_state_probe_event = lambda *a, **k: None
        m._retroarch_network_request = lambda *a, **k: "LOAD_STATE_SLOT 0"
        m._retroarch_session_log_since = lambda off: ["[State] Loading state slot 0"]
        m.status = lambda: {"active": True}
        return m, staged, rec_path, rel_path

    def test_no_source_is_todays_recovery_path(self):
        m, staged, rec_path, rel_path = self.bare()
        m.load_recovery_state_running()
        self.assertEqual(staged, [rec_path])

    def test_the_relaunch_source_is_staged(self):
        m, staged, rec_path, rel_path = self.bare()
        m.load_recovery_state_running(source=rel_path)
        self.assertEqual(staged, [rel_path])

    def test_save_relaunch_state_copies_and_verifies(self):
        m, staged, rec_path, rel_path = self.bare()
        src = rel_path.with_name("content-one.state")
        src.write_bytes(b"S" * 80)
        m._capture_slot0_state = lambda **k: {"source": src, "source_diag": m._state_file_diagnostic(src)}
        r = m.save_relaunch_state()
        self.assertEqual(r["state_path"], src.with_name("content-one.state.relaunch"))
        self.assertEqual(r["state_path"].read_bytes(), b"S" * 80)
        m._launch_kind = "pcsx2"
        with self.assertRaises(em.EmulatorError):
            m.save_relaunch_state()


if __name__ == "__main__":
    unittest.main()
