#!/usr/bin/env python3
"""B65 (host): an N64 load (the onn's Continue, a LOAD) only into a core that answers PAUSED right now, within 1.5 s;
else refused, never sent, with a `continue_skipped` row; a done load logs `continue_load`. PS1 and the flag-absent
path as today. A real `load_state` on a temp project with a fake RetroArch command port; temp dirs removed at exit.

    python3 -m unittest discover -s tests/b65_n64_continue -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

from games import emulator_manager as em  # noqa: E402

N64 = "mupen64plus_next_libretro.so"


class FakeCore:
    """`status` is what GET_STATUS answers: a string, None (silent), or a callable of the elapsed seconds."""

    def __init__(self, status="PAUSED"):
        self.status = status
        self.log: list[str] = []
        self.t0 = time.monotonic()

    def request(self, cmd, expect_response=False, timeout=None, retries=None):
        self.log.append(cmd)
        if cmd == "GET_STATUS":
            s = self.status(time.monotonic() - self.t0) if callable(self.status) else self.status
            if s is None:
                time.sleep(0.05)
                raise em.EmulatorError("RetroArch network command did not respond: GET_STATUS (timed out)")
            return f"GET_STATUS {s} fake,game"
        if cmd.startswith("LOAD_STATE_SLOT"):
            return cmd
        return None


def manager(core: FakeCore, n64: bool):
    proj = Path(tempfile.mkdtemp(prefix="b65_proj_"))
    states = proj / "data/games/retroarch/states"
    states.mkdir(parents=True)
    (states / "stem.state1").write_bytes(b"S" * 4096)
    m = em.EmulatorManager(proj)
    m._n64_core = N64 if n64 else None
    m.process = types.SimpleNamespace(pid=1, poll=lambda: None)
    m._refresh_process = lambda: None
    m.active_game = {"id": "game_x_0123", "system": "n64" if n64 else "ps1", "relative_path": "x/stem.z64"}
    m._paused = True
    m._save_state_slot_detail = lambda slot: {"exists": True, "state_file": "data/games/retroarch/states/stem.state1",
                                              "size_bytes": 4096}
    m._retroarch_network_request = core.request
    m._retroarch_session_log_position = lambda: 0
    m._retroarch_session_log_since = lambda off: []
    m.record_save_state_probe_event = lambda *a, **k: None
    return m


def run_load(m):
    try:
        return m.load_state(1), None
    except em.EmulatorError as exc:
        return None, str(exc)


class N64Load(unittest.TestCase):
    def test_paused_then_the_load(self):
        core = FakeCore("PAUSED")
        m = manager(core, True)
        _, err = run_load(m)
        self.assertIsNone(err, err)
        i = core.log.index("LOAD_STATE_SLOT 0")
        self.assertEqual(core.log[i - 1], "GET_STATUS")                       # the check right before the load
        ev = m._n64_continue_event
        self.assertEqual((ev["event"], ev["slot"]), ("continue_load", 1))
        self.assertIn("load_ms", ev)

    def test_a_late_core_waits(self):
        core = FakeCore(lambda t: "PAUSED" if t >= 0.8 else None)
        m = manager(core, True)
        t0 = time.monotonic()
        _, err = run_load(m)
        self.assertIsNone(err, err)
        self.assertGreaterEqual(time.monotonic() - t0, 0.75)
        self.assertIn("LOAD_STATE_SLOT 0", core.log)
        self.assertGreaterEqual(m._n64_continue_event["status_ms"], 750)

    def test_a_silent_port_refuses_unsent(self):
        core = FakeCore(None)
        m = manager(core, True)
        t0 = time.monotonic()
        _, err = run_load(m)
        self.assertLess(time.monotonic() - t0, 2.5)
        self.assertIn("N64 load refused: n64: command port silent", err)
        self.assertNotIn("LOAD_STATE_SLOT 0", core.log)
        self.assertEqual(m._n64_continue_event["event"], "continue_skipped")

    def test_a_playing_core_refuses_unsent(self):
        core = FakeCore("PLAYING")
        m = manager(core, True)
        _, err = run_load(m)
        self.assertIn("n64: core not paused PLAYING", err)
        self.assertNotIn("LOAD_STATE_SLOT 0", core.log)


class Others(unittest.TestCase):
    def test_ps1_as_today(self):
        core = FakeCore("PAUSED")
        m = manager(core, False)
        run_load(m)
        i = core.log.index("LOAD_STATE_SLOT 0")
        self.assertNotIn("GET_STATUS", core.log[:i])                          # no check before the load
        self.assertIsNone(m._n64_continue_event)

    def test_a_fresh_manager(self):
        m = em.EmulatorManager(Path(tempfile.mkdtemp(prefix="b65_proj_")))
        self.assertIsNone(m._n64_continue_event)
        self.assertIsNone(m._n64_core)


class PluginRow(unittest.TestCase):
    def test_the_row_is_written_and_cleared(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("g65", str(ROOT / "companion/plugins/games.py"))
        G = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(G)
        rows = []
        p = object.__new__(G.GamesPlugin)
        p._recovery = types.SimpleNamespace(_log=lambda e, **k: rows.append({"event": e, **k}))

        def load(slot):
            p._emulator._n64_continue_event = {"event": "continue_skipped", "slot": slot, "reason": "r"}
            raise em.EmulatorError("N64 load refused: r")
        p._emulator = types.SimpleNamespace(load_state=load, record_save_state_probe_event=lambda *a, **k: None,
                                            _n64_continue_event=None)
        with self.assertRaises(Exception):
            p.handle_post("load-state", "slot=1")
        self.assertEqual(rows, [{"event": "continue_skipped", "slot": 1, "reason": "r"}])
        self.assertIsNone(p._emulator._n64_continue_event)


if __name__ == "__main__":
    unittest.main()
