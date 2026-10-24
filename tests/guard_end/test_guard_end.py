#!/usr/bin/env python3
"""B17: `native-stream-start?…&guard_end=1` -- a guarded client restart ends the old session in the start request
itself (the stop action's bookkeeping, at the action's entry), then today's start; the response acknowledges it.
Without the parameter the action is today's (the AST proof in evidence/b17_2026-10-24/).

    python3 -m unittest discover -s tests/guard_end -v

`plugins/games.py` loaded alone (tests/remote_ladder's way: constructs nothing), a fake emulator, recovery, stream.
"""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))


def load_games_plugin():
    spec = importlib.util.spec_from_file_location("b17_games_plugin", ROOT / "companion" / "plugins" / "games.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = load_games_plugin()


def plugin(calls):
    class Emu:
        def status(self):
            calls.append("emulator_status")
            return {"active": True, "paused": True, "pid": 1}

    p = object.__new__(G.GamesPlugin)
    p._emulator = Emu()
    p._recovery = types.SimpleNamespace(note_stream_start=lambda: calls.append("note_stream_start"),
                                        session_ended=lambda: calls.append("session_ended"), _stall_owner=None)
    p._native_stream = types.SimpleNamespace(start=lambda **kw: calls.append("stream_start") or {"active": True})
    p._diagnostic_heartbeat_interval_ms = lambda: 2000
    p._adaptive_bitrate_session_ended = lambda: calls.append("ladder_session_end")
    return p


class GuardEnd(unittest.TestCase):
    def test_guard_end_ends_the_old_session_first_in_the_same_request(self):
        calls = []
        out = plugin(calls).handle_post_request("native-stream-start", "port=48100&guard_end=1", "127.0.0.1")
        self.assertEqual(calls, ["session_ended", "ladder_session_end", "emulator_status", "note_stream_start",
                                 "stream_start"])
        self.assertIs(out.get("guard_end"), True)

    def test_without_it_today(self):
        calls = []
        out = plugin(calls).handle_post_request("native-stream-start", "port=48100", "127.0.0.1")
        self.assertEqual(calls, ["emulator_status", "note_stream_start", "stream_start"])
        self.assertNotIn("guard_end", out)
        calls = []
        out = plugin(calls).handle_post_request("native-stream-start", "port=48100&guard_end=0", "127.0.0.1")
        self.assertEqual(calls, ["emulator_status", "note_stream_start", "stream_start"])
        self.assertNotIn("guard_end", out)


if __name__ == "__main__":
    unittest.main()
