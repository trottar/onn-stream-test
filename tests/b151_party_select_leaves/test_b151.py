#!/usr/bin/env python3
"""B151 (host): a practice is left by Select, not Start — through the real HTTP server on loopback, behind
PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1.

T89 goes on from its character screen only with Start, which B134 took as "leave the practice": a T89 practice would
end the moment anyone tried to start the fight. The user's choice: the pad's Select (Share) leaves a practice in every
game; Start goes to the game as in a real one.

B114's scenario, its `select151` mode (B137's fake title and virtual pads; T89-shaped: four seats 3,1,4,2, its start
screen left only by a press): a held start; **practice 1: Start from each of the four pads → still playing, the
title's four pads written with Start, the title off its start screen; then pad 1's Select → back, ready**; practices
2-4 left by the Select of pads 2, 3, 4; **practice 5: pad 3's Select already down at the hand-over (its reports
repeated) → the practice goes on; let go → on; pressed again → it ends**; practice 6: Select + Start together → left
by Select, Start written alone, no hotkey; practice 7: the time (scaled) → `"by": "time"`; **from the hold to the real
go no virtual pad written with Select, the hotkey log empty, the state folder byte-equal**; a real go: Select and Start
pass, nothing on the hub, scored as today; every end clears the hook, the hold and the bridge's record.
The bridge's own record (`_party_select_down`): untouched with the hold off; seeded at off → on; not re-seeded on → on.
The band's words. The flags absent: B114's / B133's tests (run with the suites). Temp dirs removed.

    python3 -m unittest discover -s tests/b151_party_select_leaves -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("b114_party_minigame_hang", "b124_party_four_seats"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
sys.path.insert(0, str(ROOT / "companion"))
import test_b114 as b114  # noqa: E402  (its harness; its tests are not collected here)
import test_b124 as b124  # noqa: E402

PLAYING = {"state": "playing", "practice": True}


class SelectLeaves(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b114.b99.tree()
        b124.IDS.clear()
        b124.IDS.update(ids)
        cls.s = b114.run(root, b114.BOTH, ids, "select151", extra=b124.extra)["steps"]

    def test_0_held_and_ready(self):
        self.assertTrue(self.s["s1_hold_seen"])
        self.assertEqual(self.s["s1_ready"]["phase"], "ready")

    def test_1_start_in_a_practice_reaches_the_title_and_the_practice_goes_on(self):
        s = self.s
        self.assertEqual(s["s1_p1_go"], ["taken", PLAYING])
        self.assertEqual(s["s1_after_starts"], PLAYING)
        self.assertEqual(s["s1_start_written_to"], [0, 1, 2, 3])          # every seated pad's Start, routed
        self.assertTrue(s["s1_title_left_start_in_practice"])             # T89-shaped: Start begins the fight
        self.assertEqual(s["s1_route_in"], {"2": 0, "0": 1, "3": 2, "1": 3})

    def test_2_a_select_press_on_each_pad_leaves_a_practice(self):
        s = self.s
        for n in (1, 2, 3, 4):
            self.assertEqual(s[f"s1_p{n}_back"], {"state": "starting", "phase": "ready", "practices": n}, n)
        for n in (2, 3, 4):
            self.assertEqual(s[f"s1_p{n}_before"], PLAYING, n)
        self.assertEqual(s["s1_end_by"][:4], ["select_button"] * 4)

    def test_3_a_select_held_across_the_hand_over_counts_only_when_pressed_again(self):
        s = self.s
        self.assertEqual(s["s1_p5_go"], ["taken", PLAYING])
        self.assertEqual(s["s1_p5_held"], PLAYING)
        self.assertEqual(s["s1_p5_let_go"], PLAYING)
        self.assertEqual(s["s1_p5_back"]["practices"], 5)
        self.assertEqual(s["s1_end_by"][4], "select_button")

    def test_4_select_with_start_leaves_by_select_start_passes_alone(self):
        s = self.s
        self.assertEqual(s["s1_p6_back"]["practices"], 6)
        self.assertEqual(s["s1_end_by"][5], "select_button")
        self.assertTrue(s["s1_p6_start_written"])
        self.assertTrue(s["s1_title_alive"])

    def test_5_the_time_bound_still_ends_one(self):
        self.assertEqual(self.s["s1_p7_back"]["practices"], 7)
        self.assertEqual(self.s["s1_end_by"], ["select_button"] * 6 + ["time"])

    def test_6_select_in_no_report_the_title_gets_before_a_real_go(self):
        s = self.s
        self.assertGreater(s["s1_writes_before_real_go"], 20)
        self.assertEqual(s["s1_select_written_before_real_go"], 0)
        self.assertEqual(s["s1_hotkeys_before_real_go"], 0)
        self.assertTrue(s["s1_states_same"])

    def test_7_a_real_go_as_today(self):
        s = self.s
        self.assertEqual(s["s1_real_go"], "taken")
        self.assertEqual(s["s1_real_after"], {"state": "playing", "practice": None})
        self.assertGreaterEqual(s["s1_real_select_written"], 1)            # Select passes from the real go on
        self.assertGreaterEqual(s["s1_real_start_written"], 1)
        self.assertFalse(s["s1_hook_in_real"])
        self.assertEqual(s["s1_real"], {"state": "ended", "class": "end", "places": [2, 1, 4, 3],
                                        "scores": [3, 4, 1, 2], "seats": [3, 1, 4, 2], "practices": 7})

    def test_8_every_end_clears_the_hook_the_hold_and_the_record(self):
        self.assertTrue(self.s["s1_hook_after_end"])
        self.assertFalse(self.s["s1_held_after_end"])
        self.assertIsNone(self.s["s1_seen_after_end"])


class BridgeRecord(unittest.TestCase):
    def test_the_raw_select_kept_only_while_held(self):
        import native_session_io as nsio
        b = nsio.NativeControllerBridge(Path(HERE / "_unused"))
        b._gamepads = ["P1", "P2", "P3", "P4"]
        b._controller_backend = "linux_uinput"
        seen = []
        b._write_linux_report_locked = lambda index, report, *a, **k: seen.append((index, report["buttons"]))
        self.assertIsNone(b._party_select_down)                           # today
        b._apply_report(2, 0x0020, 0, 0, 0, 0, 0, 0)
        self.assertIsNone(b._party_select_down)                           # the hold off: nothing kept
        self.assertEqual(seen[-1], (2, 0x0020))
        b.party_hold_select(True)                                         # off -> on: seeded from the last reports
        self.assertEqual(b._party_select_down, {0: False, 1: False, 2: True, 3: False})
        self.assertTrue(b.party_select_down(2))
        self.assertEqual(seen[-1], (2, 0))                                # B141: written once without it
        b._apply_report(2, 0, 0, 0, 0, 0, 0, 0)
        self.assertFalse(b.party_select_down(2))
        b._apply_report(1, 0x0020 | 0x0010, 0, 0, 0, 0, 0, 0)
        self.assertTrue(b.party_select_down(1))
        self.assertEqual(seen[-1], (1, 0x0010))                           # Select cleared, Start written
        b.set_party_route({0: 3})
        b.party_hold_select(True)                                         # on -> on: not seeded again
        self.assertTrue(b.party_select_down(1))
        b.set_party_route(None)
        b.party_hold_select(False)
        self.assertIsNone(b._party_select_down)
        self.assertFalse(b.party_select_down(1))
        b._apply_report(1, 0x0020, 0, 0, 0, 0, 0, 0)
        self.assertEqual(seen[-1], (1, 0x0020))                           # today again


class Band(unittest.TestCase):
    def test_the_words(self):
        import native_stream as ns
        self.assertEqual(ns.PARTY_BANNER_TEXT, "PRACTICE — press Select (Share) to go back")
        self.assertIn("text='PRACTICE — press Select (Share) to go back'", ns.PARTY_BANNER_FILTER)
        self.assertIn("y=h*5/100+10:box=1:boxcolor=black@0.72:boxborderw=10|16|10|16", ns.PARTY_BANNER_FILTER)


if __name__ == "__main__":
    unittest.main()
