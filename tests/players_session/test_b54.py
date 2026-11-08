#!/usr/bin/env python3
"""B54 (host): hold-to-join's `players_joined` sets the launch's ports (1 / 2 -> two, 3 / 4 -> the multitap, `source`
`join`); B46's `players_chosen` is still accepted as B46; the start / heartbeat rows carry `join: hold`,
`players_joined` and the labels; without the key, B46's rows byte for byte.

    python3 -m unittest discover -s tests/players_session -v
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

import pad_slots  # noqa: E402
import players_session as ps  # noqa: E402
from test_players_session import HB, TWO, plugin  # noqa: E402

BASE = {"cheat_source_index": None, "cheat_enabled_indexes": None, "mod_index": None}


class Joined(unittest.TestCase):
    def test_parse_and_the_ports(self):
        self.assertEqual([ps.parse_joined(x) for x in ("0", "1", "4", "5", "-1", "x", None)], [0, 1, 4, None, None, None, None])
        self.assertEqual([ps.ports_for_joined(n) for n in (1, 2, 3, 4)], [2, 2, 4, 4])
        self.assertEqual(ps.plan("ps1", 4, 1, source="join")["source"], "join")
        self.assertEqual(ps.plan("ps1", 4, 1)["source"], "launch")   # B46's default kept

    def test_players_joined_sets_the_launch_ports_with_source_join(self):
        p, _, _, calls = plugin()
        p._emulator.launch = lambda game, **kw: (calls.append(kw), setattr(p._emulator, "_players_session",
                                                 ps.plan("ps1", kw["players_chosen"], 1)) if "players_chosen" in kw
                                                 else None, {"active": True})[-1]
        p.handle_post("launch", "id=g1&players_joined=1")
        self.assertEqual(calls[-1], {**BASE, "players_chosen": 2})
        self.assertEqual(p._emulator._players_session["source"], "join")
        p.handle_post("launch", "id=g1&players_joined=3")
        self.assertEqual(calls[-1], {**BASE, "players_chosen": 4})
        r = p.handle_post_request("native-stream-start", "port=48100&player_prompt=1", "127.0.0.1")
        self.assertEqual(r["ports_set"], {"players_chosen": 4, "ports": 4, "players": 4, "multitap": True,
                                          "multitap_available": True, "source": "join"})
        p.handle_post("launch", "id=g1&players_joined=0")          # nobody joined last time: today's call
        self.assertEqual(calls[-1], BASE)
        p.handle_post("launch", "id=g1&players_joined=x")          # malformed: today's call
        self.assertEqual(calls[-1], BASE)

    def test_players_chosen_is_still_b46s(self):
        p, _, _, calls = plugin()
        p.handle_post("launch", "id=g1&players_chosen=1")
        self.assertEqual(calls[-1], {**BASE, "players_chosen": 1})   # B46's 1 (port 2 off), unchanged
        p.handle_post("launch", "id=g1&players_chosen=4")
        self.assertEqual(calls[-1], {**BASE, "players_chosen": 4})

    def test_the_rows_carry_join_hold_the_count_and_the_labels(self):
        p, root, rec, _ = plugin()
        p.handle_post_request("native-stream-start",
                              "port=48100&player_prompt=1&pad_slots=0:a1b2c3:sony&pad_claims=0:p&players_joined=0",
                              "127.0.0.1")   # the start carries the old map (the client clears it at the answer)
        p.handle_post_request("native-stream-heartbeat",
                              HB.format(1) + "&pad_slots=" + TWO + "&pad_claims=0:p,1:p&players_joined=2", "127.0.0.1")
        p.handle_post_request("native-stream-heartbeat",
                              HB.format(2) + "&pad_slots=" + TWO + "&pad_claims=0:p,1:p&players_joined=2", "127.0.0.1")
        rows = [json.loads(x) for x in rec.log_path().read_text().splitlines()]
        rows = [r for r in rows if r["event"] == "pad_slots"]
        self.assertEqual([r["when"] for r in rows], ["start", "change"])
        self.assertEqual((rows[0]["join"], rows[0]["players_joined"], rows[0]["count"]), ("hold", 0, 1))
        self.assertEqual((rows[1]["join"], rows[1]["players_joined"]), ("hold", 2))
        self.assertEqual([(e["label"], e["claimed_by"]) for e in rows[1]["slots"]], [("P1", "prompt"), ("P2", "prompt")])
        hb = [json.loads(x) for x in (root / "logs" / "games" / "native_stream_heartbeat.log").read_text().splitlines()]
        self.assertEqual((hb[-1]["join"], hb[-1]["players_joined"]), ("hold", 2))
        self.assertNotIn("players_chosen", hb[-1])

    def test_a_changed_count_alone_is_a_change_row(self):
        rows = []
        log = pad_slots.SlotsLog()
        rec = types.SimpleNamespace(_log=lambda ev, **f: rows.append({"event": ev, **f}))
        log.start(rec, TWO, claims="0:p,1:p", players_joined=2)
        log.heartbeat(rec, TWO, {"sequence": 1}, claims="0:p,1:p", players_joined=2)
        log.heartbeat(rec, TWO, {"sequence": 2}, claims="0:p,1:p", players_joined=3)
        self.assertEqual([r["when"] for r in rows], ["start", "change"])
        self.assertEqual(rows[1]["players_joined"], 3)

    def test_without_the_key_the_rows_are_b46s(self):
        rows_a, rows_b = [], []
        a, b = pad_slots.SlotsLog(), pad_slots.SlotsLog()
        fa = types.SimpleNamespace(_log=lambda ev, **f: rows_a.append({"event": ev, **f}))
        fb = types.SimpleNamespace(_log=lambda ev, **f: rows_b.append({"event": ev, **f}))
        a.start(fa, TWO, claims="0:p,1:s", players_chosen=2)
        b.start(fb, TWO, claims="0:p,1:s", players_chosen=2, players_joined=None)
        va, vb = {"sequence": 1}, {"sequence": 1}
        a.heartbeat(fa, TWO, va, claims="0:p,1:p", players_chosen=4)
        b.heartbeat(fb, TWO, vb, claims="0:p,1:p", players_chosen=4, players_joined=None)
        self.assertEqual(rows_a, rows_b); self.assertEqual(va, vb)
        self.assertNotIn("players_joined", json.dumps(rows_a)); self.assertNotIn('"join"', json.dumps(rows_a))
        self.assertIsNone(pad_slots.parse_joined("5")); self.assertEqual(pad_slots.parse_joined("0"), 0)


if __name__ == "__main__":
    unittest.main()
