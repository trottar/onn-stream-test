#!/usr/bin/env python3
"""B41 (host): the title's player count in the start response for a client with `player_prompt=1`, and the prompt's
claims (`claimed_by`) on the `pad_slots` rows; no key = today (nothing imported, the response and rows byte for byte).

    python3 -m unittest discover -s tests/player_prompt -v

`plugins/games.py` loaded alone (tests/pad_slots' way), a real LinkDropRecovery on a temp dir, a fake emulator.
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
import player_count  # noqa: E402
import pad_slots  # noqa: E402

spec = importlib.util.spec_from_file_location("b41_games_plugin", ROOT / "companion" / "plugins" / "games.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

TWO = "0:a1b2c3:sony,1:d4e5f6:sony"
HB = "sequence={}&interval_ms=2000&last_output_age_ms=16&rendered_frames=600&queued_frames=0&rx_packets=900&elapsed_ms=10000"


def plugin(system="ps1", player_mode="unknown", source="unknown", max_players=0, multitap=False, game=True):
    root = Path(tempfile.mkdtemp(prefix="b41_root_"))
    rec = ldr.LinkDropRecovery(
        root, pause_game=lambda: None, resume_game=lambda: None, save_recovery_state=lambda: {},
        restart_encoder=lambda: {}, full_start_encoder=lambda: {}, stream_active=lambda: True,
        end_session=lambda: None, client_packet_age_ms=lambda: 10.0, recovery_save_detail=lambda: {})

    class Emu:
        active_game = {"id": "g1", "system": system, "title": "t"} if game else None

        def status(self):
            return {"active": True, "paused": True, "pid": 1}

        def ps1_multitap(self, g):
            return {"enabled": multitap, "mode": "port1" if multitap else "off"}

    class Ctl:
        def status(self):
            return {"updates_by_player": [1, 0, 0, 0]}

    p = object.__new__(G.GamesPlugin)
    p.PROJECT_ROOT = root
    p._emulator = Emu()
    p._recovery = rec
    p._native_stream = types.SimpleNamespace(start=lambda **kw: {"active": True},
                                             _session_io=types.SimpleNamespace(controller=Ctl()))
    p._diagnostic_heartbeat_interval_ms = lambda: 2000
    p._adaptive_bitrate_session_ended = lambda: None
    p._read_library_state = lambda: {"games": {}}
    p._decorate_game = lambda g, lib, st, md: {**g, "player_mode": player_mode, "player_mode_source": source,
                                               "max_players": max_players}
    return p, root, rec


def rec_rows(rec):
    path = rec.log_path()
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def hb_rows(root):
    path = root / "logs" / "games" / "native_stream_heartbeat.log"
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


class Players(unittest.TestCase):
    def start(self, **kw):
        p, root, rec = plugin(**kw)
        return p.handle_post_request("native-stream-start", "port=48100&player_prompt=1", "127.0.0.1")

    def test_an_unknown_title_is_two(self):
        r = self.start()
        self.assertEqual((r["players"], r["players_source"]), (2, "default"))

    def test_single_is_one(self):
        self.assertEqual(self.start(player_mode="single", source="manual", max_players=4)["players"], 1)
        self.assertEqual(self.start(player_mode="single", source="metadata", max_players=1)["players_source"],
                         "metadata")

    def test_ps1_with_the_multitap_is_four_and_without_it_two(self):
        self.assertEqual(self.start(player_mode="multi", source="metadata", max_players=4, multitap=True)["players"], 4)
        self.assertEqual(self.start(player_mode="multi", source="metadata", max_players=4, multitap=False)["players"], 2)
        self.assertEqual(self.start(multitap=True)["players"], 4)                       # unknown + multitap: the ports
        self.assertEqual(self.start(player_mode="multi", max_players=3, multitap=True)["players"], 3)

    def test_a_four_player_snes_title_is_two(self):
        r = self.start(system="snes", player_mode="multi", source="metadata", max_players=4, multitap=True)
        self.assertEqual((r["players"], r["players_source"]), (2, "metadata"))

    def test_no_game_or_a_failing_read_is_two(self):
        self.assertEqual(self.start(game=False)["players"], 2)
        p, root, rec = plugin()
        p._decorate_game = lambda *a: (_ for _ in ()).throw(RuntimeError("x"))
        r = p.handle_post_request("native-stream-start", "port=48100&player_prompt=1", "127.0.0.1")
        self.assertEqual((r["players"], r["players_source"]), (2, "default"))

    def test_without_the_key_the_response_is_todays(self):
        p, root, rec = plugin(player_mode="single")
        r = p.handle_post_request("native-stream-start", "port=48100", "127.0.0.1")
        self.assertNotIn("players", r)
        self.assertNotIn("players_source", r)
        r2 = p.handle_post_request("native-stream-start", "port=48100&player_prompt=0", "127.0.0.1")
        self.assertNotIn("players", r2)


class Claims(unittest.TestCase):
    def test_the_claims_ride_the_start_and_heartbeat_rows(self):
        p, root, rec = plugin()
        p.handle_post_request("native-stream-start", "port=48100&player_prompt=1&pad_slots=" + TWO + "&pad_claims=0:p,1:s",
                              "127.0.0.1")
        p.handle_post_request("native-stream-heartbeat", HB.format(1) + "&pad_slots=" + TWO + "&pad_claims=0:p,1:s",
                              "127.0.0.1")
        p.handle_post_request("native-stream-heartbeat", HB.format(2) + "&pad_slots=" + TWO + "&pad_claims=0:p,1:p",
                              "127.0.0.1")
        rows = [r for r in rec_rows(rec) if r["event"] == "pad_slots"]
        self.assertEqual(rows[0]["when"], "start")
        self.assertEqual([e["claimed_by"] for e in rows[0]["slots"]], ["prompt", "stable"])
        self.assertEqual([r["when"] for r in rows], ["start", "change"])   # a re-claim is a change
        self.assertEqual([e["claimed_by"] for e in rows[1]["slots"]], ["prompt", "prompt"])
        self.assertEqual([e["claimed_by"] for e in hb_rows(root)[0]["pad_slots"]], ["prompt", "stable"])

    def test_without_claims_the_rows_are_b34s(self):
        log = pad_slots.SlotsLog()
        rows = []
        fake = types.SimpleNamespace(_log=lambda ev, **f: rows.append({"event": ev, **f}))
        log.start(fake, TWO)
        log2 = pad_slots.SlotsLog()
        rows2 = []
        log2.start(types.SimpleNamespace(_log=lambda ev, **f: rows2.append({"event": ev, **f})), TWO, claims=None)
        self.assertEqual(rows, rows2)
        self.assertNotIn("claimed_by", json.dumps(rows))

    def test_a_malformed_claims_value_adds_nothing(self):
        for bad in ("0:x", "9:p", "0:p;1:s", "0:prompt"):
            self.assertIsNone(pad_slots.parse_claims(bad))
            self.assertEqual(pad_slots.with_claims(pad_slots.parse(TWO), bad), pad_slots.parse(TWO))
        self.assertEqual(pad_slots.parse_claims(""), {})

    def test_the_rule_alone(self):
        self.assertEqual(player_count.rule("", "", 0, False), (2, "default"))
        self.assertEqual(player_count.rule("multi", "manual", 0, False), (2, "manual"))
        self.assertEqual(player_count.rule("multi", "metadata", 2, True), (2, "multitap"))


class Absent(unittest.TestCase):
    def test_a_fresh_process_without_the_key_imports_nothing(self):
        code = ("import sys, importlib.util; sys.path.insert(0, 'companion');"
                "s = importlib.util.spec_from_file_location('g', 'companion/plugins/games.py');"
                "m = importlib.util.module_from_spec(s); s.loader.exec_module(m);"
                "print('player_count' in sys.modules, 'pad_slots' in sys.modules)")
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                             env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(out.stdout.strip(), "False False", out.stderr[-500:])


if __name__ == "__main__":
    unittest.main()
