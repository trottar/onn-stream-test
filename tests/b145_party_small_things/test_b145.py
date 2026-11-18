#!/usr/bin/env python3
"""B145 (host): Select held through a practice too, until a real go — through the real HTTP server on loopback.

B141 held the pads' Select (RetroArch's hotkey button: + L1 load state, + R1 save state, + Start quit, + R3 pause
toggle) from a held title's launch to the go, but let it through at a practice's go: in a practice Select + L1 / R1
still loaded / saved over a slot of the users' cheat setup. B145: Select is held until a real go, practices included.

B114's scenario, its `nopress` mode (B137's fake title reads the virtual pads and logs every poll that sees Select with
a paired button; B141's cases first): a held start, a practice; **while it plays, Select + L1 / R1 / R3 from all four
pads every 0.2 s → the virtual pads written, none with Select; the fake's hotkey log empty; its state folder
byte-equal** — B151: the first of those pairs leaves the practice (`select_button`: Select is the way out now), the
pairs going on through its way back; a Select press after it changes nothing (was: Select + Start left it,
`start_button`); the title not quit; a real go → Select alone written; the hold off after it and after the end. HEAD's code (the mutation, run by the record): the same
presses in a practice reach the fake. Temp dirs removed.

    python3 -m unittest discover -s tests/b145_party_small_things -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "b114_party_minigame_hang"))
sys.path.insert(0, str(ROOT / "tests" / "b124_party_four_seats"))
import test_b114 as b114  # noqa: E402  (its harness; its tests are not collected here)
import test_b124 as b124  # noqa: E402


class SelectThroughPractice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b114.b99.tree()
        b124.IDS.clear()
        b124.IDS.update(ids)
        cls.s = b114.run(root, b114.BOTH, ids, "nopress", extra=b124.extra)["steps"]

    def test_0_a_practice_plays(self):
        s = self.s
        self.assertEqual(s["sp_ready"], "ready")
        self.assertEqual(s["sp_go"], "taken")
        self.assertEqual(s["sp_playing"], {"state": "playing", "practice": True})
        self.assertTrue(s["sp_title_running"])

    def test_1_no_select_and_no_hotkey_in_the_practice(self):
        s = self.s
        self.assertTrue(s["sp_held_in_practice"])
        self.assertGreater(s["sp_writes_in_practice"], 20)             # the pads did reach the title
        self.assertEqual(s["sp_select_written_in_practice"], 0)
        self.assertEqual(s["sp_hotkeys_in_practice"], 0)
        self.assertTrue(s["sp_states_same"])

    def test_2_select_start_leaves_the_practice_without_quitting(self):
        s = self.s
        self.assertEqual(s["sp_back"], "ready")
        self.assertEqual(s["sp_end_by"], ["select_button"])          # B151
        self.assertTrue(s["sp_title_alive"])
        self.assertEqual(s["sp_hotkeys_total"], 0)

    def test_3_a_real_go_lets_select_through(self):
        s = self.s
        self.assertEqual(s["sp_real_go"], "taken")
        self.assertGreaterEqual(s["sp_select_written_after_real_go"], 1)
        self.assertFalse(s["sp_held_after_real_go"])
        self.assertFalse(s["sp_held_after_end"])


if __name__ == "__main__":
    unittest.main()
