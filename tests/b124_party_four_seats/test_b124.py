#!/usr/bin/env python3
"""B124 (host): four seats on the board and who plays what — through the real HTTP server on loopback, behind
PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1.

B114's harness (B108's stand-in board, B101's fake RetroArch, B103's fake pictures, the stream stub with its own lock,
the onn's client thread and status / result / native-stream-status every 0.1 s) with the hub's adopted lines on, and
**two mini games in the rules folder**: the fixture's PS1 title with B103's two-player spec and sidecar, and the
fixture's **N64 title with a real version-3 spec** (B122, learnt here from B122's synthetic pictures) **and the places
sidecar** (`{"players": 4}`: 4, 3, 2, 1). Checked: the board's start answers **four players and four ports**; the
board's launch environment carries `PRIVYPARTY_ON_HUB=1`; a four-player title with two seats and a two-player one with
four refused; **four back to back — two-player (1,2), four-player (3,1,4,2) with Home / RESUME, two-player (2,1),
four-player (1,2,3,4)** — the route seat → port in the order given, the four-player end read as places and turned
into scores in the seats' order, a RESUME during a four-player game still answering four ports, every hand-over
planned (B115: two switches, no recovery act, no key to the board), no escalation, every route < 2 s while a mini game
is on. Each flag absent → today (B114's and B123's flag tests). Temp dirs removed.

    python3 -m unittest discover -s tests/b124_party_four_seats -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("b114_party_minigame_hang", "b123_h7_n64_start", "b115_party_handovers"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import test_b114 as b114  # noqa: E402  (harnesses; their tests are not collected here)
import test_b123 as b123  # noqa: E402
import test_b115 as b115  # noqa: E402


def extra(work: Path, frames: Path) -> dict:
    import numpy as np
    rng = np.random.default_rng(124)
    for i in range(6):
        b123.b122.start(i, rng).save(frames / f"s4start_{i}.png")
        b123.b122.other(i, rng).save(frames / f"s4other_{i}.png")
        b123.b122.results(i, "2143", 40, rng).save(frames / f"s4r2143_{i}.png")
    return {"n64_id": IDS[b114.b85.N64_TITLE], "v3": str(b123.v3_spec(work))}


IDS: dict = {}


class FourSeats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b114.b99.tree()
        IDS.update(ids)
        cls.out = b114.run(root, b114.BOTH, ids, "four", extra=extra)
        cls.s = cls.out["steps"]

    def test_0_the_board_takes_four_pads(self):
        self.assertIsNone(self.out["hung"], self.out.get("mg_thread"))
        bp = self.s["board_ports"]
        self.assertEqual((bp["players"], bp["players_source"]), (4, "party"))
        self.assertEqual((bp["ports_set"]["players"], bp["ports_set"]["ports"], bp["ports_set"]["source"]),
                         (4, 4, "party"))
        self.assertEqual(self.s["on_hub_word"], "1")
        self.assertEqual(self.s["four_list"], [2, 4])

    def test_1_seats_must_fit_the_title(self):
        for k in ("refuse_4p_two_seats", "refuse_2p_four_seats"):
            r = self.s[k]
            self.assertEqual(r["code"], 400, (k, r))
            self.assertIn("different seats, 1-4", r["body"]["error"])
        self.assertIn("takes 4", self.s["refuse_4p_two_seats"]["body"]["error"])
        self.assertIn("takes 2", self.s["refuse_2p_four_seats"]["body"]["error"])

    def test_2_the_route_seat_to_port_in_the_order_given(self):
        self.assertEqual(self.s["a2_route_during"], {"0": 0, "1": 1})
        self.assertEqual(self.s["b4_route_during"], {"2": 0, "0": 1, "3": 2, "1": 3})   # seat 3 -> port 1 ...
        self.assertEqual(self.s["c2_route_during"], {"1": 0, "0": 1})
        self.assertEqual(self.s["d4_route_during"], {"0": 0, "1": 1, "2": 2, "3": 3})
        for tag in ("a2", "b4", "c2", "d4"):
            self.assertIsNone(self.s[tag + "_route_after"], tag)

    def test_3_places_to_scores_in_the_seats_order(self):
        # the pictures' Place row: port 1 2nd, port 2 1st, port 3 4th, port 4 3rd; seat k plays port k
        for tag, seats in (("b4", [3, 1, 4, 2]), ("d4", [1, 2, 3, 4])):
            r = self.s[tag]
            self.assertEqual((r["state"], r["class"], r["places"], r["scores"], r["seats"]),
                             ("ended", "end", [2, 1, 4, 3], [3, 4, 1, 2], seats), (tag, r))
        for tag, cls_, scores in (("a2", "end_P1", [1, 0]), ("c2", "end_P2", [0, 1])):
            r = self.s[tag]
            self.assertEqual((r["state"], r["class"], r["scores"]), ("ended", cls_, scores), (tag, r))
            self.assertNotIn("places", r)                                 # the two-player answer as before

    def test_4_every_hand_over_planned_and_the_recovery_out(self):
        for tag in ("a2", "b4", "c2", "d4"):
            sw = [(x["window"], x["switched"], x.get("planned")) for x in self.s[tag + "_switches"]]
            self.assertEqual(sw, [("minigame", True, True), ("board", True, True)], tag)
            acts = [x for x in self.s[tag + "_rec"] if x in b115.RECOVERY_ACTS]
            self.assertEqual(acts, [], (tag, self.s[tag + "_rec"]))
            self.assertEqual(self.s[tag + "_keys_all"], [], tag)
            self.assertTrue(self.s[tag + "_board_picture_back"], tag)
            self.assertTrue(self.s[tag + "_title_gone"], tag)
        events = [e[0] for e in self.s["abr_all"]]
        self.assertNotIn("escalation_armed", events)
        self.assertNotIn("transition", events)

    def test_5_resume_during_a_four_player_game_and_the_two_second_rule(self):
        self.assertEqual(self.s["b4_resume_ports"], {"players": 4, "ports": 4})
        lat = self.out["lat"]
        for kind in ("status", "result", "ns_status", "home", "board_end", "start"):
            self.assertLess(lat[kind]["max"], b114.WITHIN_S, (kind, lat[kind]))


if __name__ == "__main__":
    unittest.main()
