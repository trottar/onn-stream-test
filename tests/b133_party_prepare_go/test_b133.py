#!/usr/bin/env python3
"""B133 (host): the hub prepares the title behind the board and hands over on the board's go — through the real HTTP
server on loopback, behind PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1.

B114's scenario, its `hold` mode: B108's stand-in board, B101's fake RetroArch, B103's scripted pictures, the stream stub
following one window, the onn's thread and status / result / native-stream-status every 0.1 s; the PS1 title (two
players) and the N64 one (four, B122's version-3 spec). Checked: `party-minigame-start?…&hold=1` → `"preparing"` →
`"ready"` with **no route and no switch** (the stream still on the board, the title paused); a hold with the board
asking → still `ready`; the go → the begin loaded again, the route, the planned switch, `playing`, ended as today; the
rows in that order with `prepare_s` / `held_s` / `handover_s`; a go before `ready` remembered (T89-shaped, back to
back); a second go; never the start → `given_up`, no route, no switch, the title gone, the board's session back; the
board no longer asking → `given_up`; the board's end and a second start during the preparation and the hold; the onn's
Home (the mini game given up, then Home / RESUME on the board) and END (everything ends); every route < 2 s; nothing
left running. The flags absent → HEAD's answers; no `hold` → today (B114 / B124 / B127's suites). Temp dirs removed.

    python3 -m unittest discover -s tests/b133_party_prepare_go -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("b114_party_minigame_hang", "b124_party_four_seats", "b127_party_cheat_setups", "b115_party_handovers",
            "b123_h7_n64_start"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import test_b114 as b114  # noqa: E402  (harnesses; their tests are not collected here)
import test_b124 as b124  # noqa: E402
import test_b127 as b127  # noqa: E402

HEAD = "73284310"                       # queue AU's baseline: the companion before B133 / B134
NO_GO = "no mini game is waiting for the go"


class PrepareAndGo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b114.b99.tree()
        b124.IDS.clear()
        b124.IDS.update(ids)
        cls.out = b114.run(root, b114.BOTH, ids, "hold", extra=b124.extra)
        cls.s = cls.out["steps"]

    def test_0_prepared_behind_the_board_then_ready_nothing_routed(self):
        s = self.s
        self.assertIsNone(self.out["hung"])
        self.assertEqual(s["h1_preparing"]["phase"], "preparing")
        self.assertEqual(s["h1_ready"], {"state": "starting", "phase": "ready", "recognised": True, "practices": 0})
        self.assertEqual(s["h1_rows_at_ready"], ["minigame_start", "minigame_launch", "minigame_watch", "minigame_ready"])
        self.assertIsNone(s["h1_route_ready"])
        self.assertTrue(s["h1_stream_on_board"])
        self.assertTrue(s["h1_title_paused_ready"])
        self.assertEqual(s["h1_still"], {"state": "starting", "phase": "ready"})      # a hold, the board asking

    def test_1_the_go_hands_over_and_the_match_ends_as_today(self):
        s = self.s
        self.assertEqual(s["h1_go"], {"ok": True, "go": "taken", "phase": "ready", "practice": False})
        self.assertEqual(s["h1_route_playing"], {"0": 0, "1": 1})
        self.assertTrue(s["h1_stream_on_title"])
        self.assertEqual(s["h1"], {"state": "ended", "class": "end_P1", "scores": [1, 0], "why": None})
        self.assertEqual(s["h1_rows"][:9], ["minigame_start", "minigame_launch", "minigame_watch", "minigame_ready",
                                            "minigame_go", "minigame_reloaded", "minigame_route", "minigame_stream",
                                            "minigame_playing"])
        f = s["h1_row_fields"]
        self.assertEqual(f["minigame_start"], {"hold": True})
        self.assertGreater(f["minigame_ready"]["prepare_s"], 0.5)
        self.assertGreaterEqual(f["minigame_go"]["held_s"], 3.0)
        self.assertFalse(f["minigame_go"]["remembered"])
        self.assertLess(f["minigame_playing"]["handover_s"], 2.0)
        self.assertEqual(s["h1_switches"], [["minigame", True], ["board", True]])
        self.assertTrue(s["h1_title_gone"] and s["h1_closed"] and s["h1_board_picture_back"])
        self.assertIsNone(s["h1_route_after"])

    def test_2_a_go_before_ready_is_remembered_a_second_go_already_t89_shaped(self):
        s = self.s
        self.assertEqual((s["h2_go_early"]["go"], s["h2_go_early"]["phase"]), ("remembered", "preparing"))
        self.assertEqual(s["h2_go_second"]["go"], "already")
        self.assertEqual(s["h2"]["state"], "ended")
        self.assertEqual((s["h2"]["places"], s["h2"]["scores"], s["h2"]["seats"]), ([2, 1, 4, 3], [3, 4, 1, 2], [3, 1, 4, 2]))
        self.assertEqual(s["h2_go_row"], [{"remembered": True}])
        self.assertEqual(s["h2_switches"], [["minigame", True], ["board", True]])

    def test_3_never_the_start_nothing_routed_nothing_switched(self):
        s = self.s
        self.assertEqual(s["h3"]["state"], "given_up")
        self.assertIn("start screen was not recognised", s["h3"]["why"])
        self.assertNotIn("minigame_route", s["h3_rows"])
        self.assertEqual(s["h3_switches"], [])
        self.assertTrue(s["h3_title_gone"])
        self.assertEqual(s["h3_status_kind"], "godot")

    def test_4_the_board_no_longer_asking(self):
        self.assertEqual(self.s["h4"], {"state": "given_up", "why": "the board stopped asking", "closed": True})
        self.assertTrue(self.s["h4_title_gone"])
        self.assertNotIn("minigame_route", self.s["h4_rows"])

    def test_5_the_boards_end_and_a_second_start_during_the_preparation_and_the_hold(self):
        for tag in ("h5p", "h5h"):
            self.assertEqual(self.s[tag + "_state"], "given_up", tag)
            self.assertEqual(self.s[tag + "_second_start"]["code"], 400, tag)
            self.assertTrue(self.s[tag + "_title_gone"] and self.s[tag + "_closed"], tag)
            self.assertNotIn("minigame_route", self.s[tag + "_rows"], tag)
            self.assertEqual(self.s[tag + "_switches"], [], tag)

    def test_6_the_onns_home_and_end_during_the_preparation_and_the_hold(self):
        s = self.s
        self.assertEqual(s["h6"], {"state": "given_up", "why": "the onn's Home during the preparation", "closed": True})
        self.assertTrue(s["h6_title_gone"])
        self.assertEqual(s["h6_resume"], {"start": 200, "ready": 200, "kind": "godot"})
        self.assertEqual(s["h6_route_ever"], [])
        self.assertEqual(s["h7"], {"state": "given_up", "why": "ended from the onn", "closed": True})
        self.assertTrue(s["h7_title_gone"] and s["h7_board_gone"])

    def test_7_refusals_routes_within_2_s_nothing_left(self):
        s = self.s
        self.assertEqual((s["h_go_none"]["code"], s["h_go_none"]["body"]["error"]), (400, NO_GO))
        self.assertEqual((s["h_go_bad"]["code"], s["h_go_bad"]["body"]["error"]), (400, "practice is 1"))
        self.assertEqual((s["h_hold_bad"]["code"], s["h_hold_bad"]["body"]["error"]), (400, "hold is 1"))
        for kind in ("status", "result", "ns_status", "start", "go", "board_end", "home"):
            self.assertLess(self.out["lat"][kind]["max"], b114.WITHIN_S, kind)
        self.assertEqual(s["h_running_at_end"], [False])
        self.assertIsNone(s["h_board_at_end"])


class Today(unittest.TestCase):
    def test_flags_absent_and_no_mini_game_are_heads(self):
        code = b114.code_of(HEAD)
        if code is None:
            self.skipTest("git is absent")
        for env in ({**b114.b85.FLAGS, **b114.ADOPTED}, {**b114.b85.FLAGS, **b114.ADOPTED, "PRIVYHUB_PARTY": "1"},
                    {**b114.b85.FLAGS, **b114.ADOPTED, "PRIVYHUB_H7": "1"}):
            root, ids = b114.b99.tree(code)
            base = b114.run(root, env, ids, "today")["steps"]
            root2, ids2 = b114.b99.tree()
            mine = b114.run(root2, env, ids2, "today")["steps"]
            for k in ("list", "start", "result", "end", "go", "status_idle", "home_idle", "stop_idle"):
                self.assertEqual((mine[k]["code"], b114.CLOCK.sub("<ms>", mine[k]["raw"])),
                                 (base[k]["code"], b114.CLOCK.sub("<ms>", base[k]["raw"])), (sorted(env), k))


if __name__ == "__main__":
    unittest.main()
