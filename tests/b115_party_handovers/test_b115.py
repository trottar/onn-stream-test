#!/usr/bin/env python3
"""B115 (host): the mini game's hand-overs made planned — through the real HTTP server on loopback.

B114's harness (its stream stub with its own lock and a capture that follows one process, the onn's client thread
with client-health, heartbeats and stall datagrams through the real stall worker, status / result /
native-stream-status every 0.1 s) with the hub's adopted lines on: **three mini games back to back** (Home / RESUME in
the first; a real stall — the client's video stopping while the title plays, outside the switch windows — in the
third). Checked: **the way back switches the stream to the board before the title stops** (switched true, the stream
never down, the title's stop row after the switch's), **the way in the same**; across every hand-over **no**
client_stall / desync_pause / stall_handover_v2 / encoder_restart / resumed row, **no** escalation or bitrate step,
**no key to the board**, while the client did stall during each restart (the stalls sent and not taken, counted in
the window's row); the real stall handled as today (the title paused, no key to the board, resumed); every route
< 2 s while a mini game is on. Each flag absent → today: B114's flag test (the real routes against HEAD's code), and
the stall worker with no window attribute is today's (its suites). Temp dirs removed.

    python3 -m unittest discover -s tests/b115_party_handovers -v
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "b114_party_minigame_hang"))
import test_b114 as b114  # noqa: E402  (its harness; its tests are not collected here)

RECOVERY_ACTS = ("client_stall", "desync_pause", "stall_handover_v2", "encoder_restart", "resumed", "gave_up_saved",
                 "input_hold_handover", "stall_resume_failed")


class Handovers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, cls.ids = b114.b99.tree()
        cls.out = b114.run(root, b114.BOTH, cls.ids, "three")
        cls.s = cls.out["steps"]

    def test_0_three_back_to_back(self):
        self.assertIsNone(self.out["hung"], self.out.get("mg_thread"))
        for tag, cls_, scores in (("m1", "end_P2", [0, 1]), ("m2", "end_P1", [1, 0]), ("m3", "end_P1", [1, 0])):
            r = self.s[tag]
            self.assertEqual((r["state"], r["class"], r["scores"]), ("ended", cls_, scores), (tag, r))
            self.assertTrue(self.s[tag + "_closed"] and self.s[tag + "_title_gone"], tag)
            self.assertIsNone(self.s[tag + "_route_after"], tag)
            self.assertEqual(self.s[tag + "_status_kind"], "godot", tag)

    def test_1_the_way_back_switches_before_the_title_stops(self):
        board = self.out["board_pid"]
        for tag in ("m1", "m2", "m3"):
            sw = self.s[tag + "_switches"]
            self.assertEqual([(x["window"], x["switched"], x.get("planned")) for x in sw],
                             [("minigame", True, True), ("board", True, True)], (tag, sw))
            rows = self.s[tag + "_rows"]
            back = max(i for i, x in enumerate(rows) if x == "minigame_stream")
            self.assertLess(back, rows.index("minigame_title_stopped"), (tag, rows))   # the switch, then the title
            ev = self.s[tag + "_stream_events"]
            self.assertNotIn("down", [e[0] for e in ev], (tag, ev))                     # the stream never went down
            starts = [e for e in ev if e[0] == "start"]
            self.assertEqual(starts[-1][1], board, (tag, ev))                            # the board's own window
            self.assertTrue(self.s[tag + "_board_picture_back"], tag)
            self.assertLess(self.s[tag + "_board_picture_s"], 1.0, tag)                  # already back at the end

    def test_2_the_recovery_stays_out_of_both_hand_overs(self):
        for tag in ("m1", "m2"):
            acts = [x for x in self.s[tag + "_rec"] if x in RECOVERY_ACTS]
            # m1's Home / RESUME end and start the recovery's session (session_ended / session_started): not acts
            self.assertEqual(acts, [], (tag, self.s[tag + "_rec"]))
        stall_rows = [x[0] for x in self.s["m3_stall_rec"]]
        m3_acts = [x for x in self.s["m3_rec"] if x in RECOVERY_ACTS]
        self.assertEqual(sorted(m3_acts), sorted(x for x in stall_rows if x in RECOVERY_ACTS))   # only the real stall's
        for tag in ("m1", "m2", "m3"):
            self.assertEqual(self.s[tag + "_keys_all"], [], tag)                         # no key to the board at all
            wins = self.s[tag + "_windows"]
            self.assertEqual([w["window"] for w in wins], ["minigame", "board"], (tag, wins))
            self.assertGreater(sum(w["stalls_not_taken"] for w in wins), 0, (tag, wins))  # the client did stall

    def test_3_no_escalation_no_bitrate_step(self):
        events = [e[0] for e in self.s["abr_all"]]
        self.assertNotIn("escalation_armed", events, self.s["abr_all"])
        self.assertNotIn("transition", events, self.s["abr_all"])
        sources = [e[1] for e in self.s["abr_all"] if e[0] == "ssrc_change"]
        self.assertEqual(sources.count("minigame_switch"), 6, self.s["abr_all"])       # two per mini game, planned
        self.assertNotIn("recovery_full_start", sources)

    def test_4_a_real_stall_during_a_mini_game_is_handled_as_today(self):
        self.assertTrue(self.s["m3_paused_by_stall"])                                    # the title paused
        self.assertTrue(self.s["m3_resumed_after_stall"])
        rows = self.s["m3_stall_rec"]
        self.assertIn(["desync_pause", "client_stall"], rows, rows)
        self.assertIn("resumed", [x[0] for x in rows], rows)
        self.assertEqual(self.s["m3_stall_keys"], [])                                    # the title's, not the board's

    def test_5_every_route_within_2_s_and_home_resume_in_order(self):
        lat = self.out["lat"]
        for kind in ("status", "result", "ns_status", "home", "board_end", "start"):
            self.assertLess(lat[kind]["max"], b114.WITHIN_S, (kind, lat[kind]))
        self.assertEqual(self.s["m1_home"], {"code": 200, "taken": "home"})
        self.assertIs(self.s["m1_title_paused_after_home"], True)
        self.assertEqual(self.s["m1_resume"], {"start": 200, "start_active": True, "ready": 200, "released": True})


if __name__ == "__main__":
    unittest.main()
