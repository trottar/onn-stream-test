#!/usr/bin/env python3
"""B34 (host): the client's stable slot map -- a `pad_slots` recovery row at each start, the map and the per-slot
counters on the heartbeat row, a change row when it moves; no key = today (nothing imported, rows byte for byte).

    python3 -m unittest discover -s tests/pad_slots -v

`plugins/games.py` loaded alone (tests/guard_end's way), a real LinkDropRecovery on a temp dir, a fake controller.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

from games import link_drop_recovery as ldr  # noqa: E402

spec = importlib.util.spec_from_file_location("b34_games_plugin", ROOT / "companion" / "plugins" / "games.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

TWO = "0:a1b2c3:sony,1:d4e5f6:sony"


def plugin():
    root = Path(tempfile.mkdtemp(prefix="b34_root_"))
    rec = ldr.LinkDropRecovery(
        root, pause_game=lambda: None, resume_game=lambda: None, save_recovery_state=lambda: {},
        restart_encoder=lambda: {}, full_start_encoder=lambda: {}, stream_active=lambda: True,
        end_session=lambda: None, client_packet_age_ms=lambda: 10.0, recovery_save_detail=lambda: {})

    class Emu:
        def status(self):
            return {"active": True, "paused": True, "pid": 1}

    class Ctl:
        def status(self):
            return {"updates_by_player": [120, 80, 0, 0]}

    p = object.__new__(G.GamesPlugin)
    p.PROJECT_ROOT = root
    p._emulator = Emu()
    p._recovery = rec
    p._native_stream = types.SimpleNamespace(start=lambda **kw: {"active": True},
                                             _session_io=types.SimpleNamespace(controller=Ctl()))
    p._diagnostic_heartbeat_interval_ms = lambda: 2000
    p._adaptive_bitrate_session_ended = lambda: None
    return p, root, rec


def rec_rows(rec):
    path = rec.log_path()
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def hb_rows(root):
    path = root / "logs" / "games" / "native_stream_heartbeat.log"
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


HB = "sequence={}&interval_ms=2000&last_output_age_ms=16&rendered_frames=600&queued_frames=0&rx_packets=900&elapsed_ms=10000"


class PadSlotsHost(unittest.TestCase):
    def test_the_start_key_writes_one_row(self):
        p, root, rec = plugin()
        p.handle_post_request("native-stream-start", "port=48100&pad_slots=" + TWO, "127.0.0.1")
        rows = [r for r in rec_rows(rec) if r["event"] == "pad_slots"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["when"], "start")
        self.assertEqual(rows[0]["count"], 2)
        self.assertEqual(rows[0]["slots"], [{"slot": 0, "pad": "a1b2c3", "class": "sony"},
                                            {"slot": 1, "pad": "d4e5f6", "class": "sony"}])

    def test_the_heartbeat_key_goes_on_the_row_and_a_change_row_only_on_change(self):
        p, root, rec = plugin()
        p.handle_post_request("native-stream-start", "port=48100&pad_slots=0:a1b2c3:sony", "127.0.0.1")
        p.handle_post_request("native-stream-heartbeat", HB.format(1) + "&pad_slots=0:a1b2c3:sony", "127.0.0.1")
        p.handle_post_request("native-stream-heartbeat", HB.format(2) + "&pad_slots=" + TWO, "127.0.0.1")
        p.handle_post_request("native-stream-heartbeat", HB.format(3) + "&pad_slots=" + TWO, "127.0.0.1")
        hb = hb_rows(root)
        self.assertEqual([len(r["pad_slots"]) for r in hb], [1, 2, 2])
        self.assertEqual(hb[0]["updates_by_player"], [120, 80, 0, 0])
        rows = [r for r in rec_rows(rec) if r["event"] == "pad_slots"]
        self.assertEqual([r["when"] for r in rows], ["start", "change"])
        self.assertEqual(rows[1]["heartbeat_sequence"], 2)

    def test_a_bad_value_is_dropped_never_written(self):
        p, root, rec = plugin()
        bad = "0:SECRETNAME:sony"
        p.handle_post_request("native-stream-heartbeat", HB.format(1) + "&pad_slots=" + bad, "127.0.0.1")
        p.handle_post_request("native-stream-start", "port=48100&pad_slots=" + bad, "127.0.0.1")
        for r in hb_rows(root) + rec_rows(rec):
            self.assertNotIn("SECRETNAME", json.dumps(r))
        self.assertTrue(hb_rows(root)[0]["pad_slots_bad"])
        self.assertNotIn("pad_slots", hb_rows(root)[0])
        for bad2 in ("0:a1b2c3:sony,0:d4e5f6:sony", "4:a1b2c3:sony", ",".join(["0:a1b2c3:x1"] * 5)):
            self.assertIsNone(__import__("pad_slots").parse(bad2))
        self.assertEqual(__import__("pad_slots").parse(""), [])

    def test_no_key_is_today(self):
        p, root, rec = plugin()
        p.handle_post_request("native-stream-start", "port=48100", "127.0.0.1")
        p.handle_post_request("native-stream-heartbeat", HB.format(1), "127.0.0.1")
        self.assertEqual([r for r in rec_rows(rec) if r["event"] == "pad_slots"], [])
        row = hb_rows(root)[0]
        for k in ("pad_slots", "updates_by_player", "pad_slots_bad"):
            self.assertNotIn(k, row)
        self.assertIsNone(getattr(p, "_pad_slots_log", None))

    def test_a_fresh_process_without_the_key_imports_nothing(self):
        code = ("import sys, importlib.util; sys.path.insert(0, 'companion');"
                "s = importlib.util.spec_from_file_location('g', 'companion/plugins/games.py');"
                "m = importlib.util.module_from_spec(s); s.loader.exec_module(m);"
                "print('pad_slots' in sys.modules)")
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                             env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(out.stdout.strip(), "False", out.stderr[-500:])


if __name__ == "__main__":
    unittest.main()
