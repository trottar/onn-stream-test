#!/usr/bin/env python3
"""B134 (host): the listing's names and practice from the load screen — through the real HTTP server on loopback,
behind PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1.

B114's scenario, its `practice` mode (B133's harness): the list with the fixture's made-up names; a held start, then
**three practices** — `party-minigame-go?practice=1` → `playing` with `"practice": true`, an end screen shown in it
changing nothing, the pads routed and the stream on the title; **the second pad's Start** (a controller report through
the bridge) leaves the first two, **the practice time** (scaled) the third → back to `"starting"`, `"ready"`,
`"practices": n`, the route cleared, the stream on the board, no scores — then **a real go**, Start in it doing nothing
on the hub, scored as today; **no name in any row**; the board's end and the onn's Home / END during a practice and
during its way back → given up, nothing scored, the title gone, the Start hook cleared. The flags absent → HEAD's
answers (B133's test). Temp dirs removed.

    python3 -m unittest discover -s tests/b134_party_practice -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("b114_party_minigame_hang", "b124_party_four_seats", "b115_party_handovers", "b123_h7_n64_start"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import test_b114 as b114  # noqa: E402  (harnesses; their tests are not collected here)
import test_b124 as b124  # noqa: E402

MADE_UP = {2: "Juliet Run (USA)", 4: "Alpha Racer (USA)"}        # B85's made-up fixture titles, as the library has them


class Practice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b114.b99.tree()
        b124.IDS.clear()
        b124.IDS.update(ids)
        cls.out = b114.run(root, b114.BOTH, ids, "practice", extra=b124.extra)
        cls.s = cls.out["steps"]

    def test_0_the_list_names_each_game_no_name_in_any_row(self):
        self.assertIsNone(self.out["hung"])
        self.assertEqual({e["players"]: e["title"] for e in self.s["h_list"]}, MADE_UP)
        self.assertEqual(self.s["p_names_in_rows"], [])

    def test_1_three_practices(self):
        for n in (1, 2, 3):
            tag = f"p{n}"
            self.assertEqual(self.s[tag + "_go"], {"ok": True, "go": "taken", "phase": "ready", "practice": True}, tag)
            self.assertEqual(self.s[tag + "_playing"], {"state": "playing", "practice": True, "practices": n - 1}, tag)
            self.assertEqual(self.s[tag + "_still"],                       # an end screen in a practice: nothing
                             {"state": "playing", "practice": True, "scores": None, "class": None}, tag)
            self.assertEqual(self.s[tag + "_route_in"], {"0": 0, "1": 1}, tag)
            self.assertTrue(self.s[tag + "_stream_on_title"], tag)
            self.assertEqual(self.s[tag + "_back"], {"state": "starting", "phase": "ready", "practices": n,
                                                    "scores": None}, tag)
            self.assertIsNone(self.s[tag + "_route_back"], tag)
            self.assertTrue(self.s[tag + "_stream_on_board"], tag)
        ends = [r.get("by") for r in self.s["p_end_rows"] if r["step"] == "minigame_practice_end"]
        self.assertEqual(ends, ["start_button", "start_button", "time"])

    def test_2_then_a_real_go_start_does_nothing_scored_as_today(self):
        self.assertEqual(self.s["p_real_go"]["practice"], False)
        self.assertEqual(self.s["p_real_after_start"], {"state": "playing", "practice": None})
        self.assertEqual(self.s["p_real"], {"state": "ended", "class": "end_P2", "scores": [0, 1], "practices": 3})
        self.assertEqual(self.s["p_practice_end_rows_total"], 3)
        self.assertTrue(self.s["p_title_gone"] and self.s["p_closed"])

    def test_3_ends_during_a_practice_and_its_way_back(self):
        for tag in ("q1", "q2", "q3", "q4"):
            r = self.s[tag]
            self.assertEqual((r["state"], r["closed"], r["scores"]), ("given_up", True, None), (tag, r))
            self.assertTrue(self.s[tag + "_title_gone"], tag)
            self.assertTrue(self.s[tag + "_hook_cleared"], tag)
        self.assertEqual(self.s["q2"]["why"], "the onn's Home during the preparation")
        self.assertEqual(self.s["q4"]["why"], "ended from the onn")

    def test_4_routes_within_2_s_nothing_left(self):
        for kind in ("status", "result", "ns_status", "start", "go", "board_end"):
            self.assertLess(self.out["lat"][kind]["max"], b114.WITHIN_S, kind)
        self.assertEqual(self.s["h_running_at_end"], [False])


if __name__ == "__main__":
    unittest.main()
