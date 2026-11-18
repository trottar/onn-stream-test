#!/usr/bin/env python3
"""B141 (host): Select is not passed to a held title — through the real HTTP server on loopback, behind
PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1.

RetroArch's hotkeys on the hub are pairs with Select (`input_enable_hotkey_btn` 6): + L1 load state, + R1 save state,
+ Start quit, + R3 pause toggle — and a paused core still takes them. B114's scenario, its `nopress` mode: the fake
RetroArch logs a hotkey whenever a virtual pad shows Select with one of those (paused or running). Select with each
paired button from every pad through the bridge, every 0.2 s, during the preparation and the hold, and on a practice's
way back.

Checked: no virtual pad's Select written down and the fake's hotkey log empty in both; the fake's state folder
byte-equal; after the go Select passes (written) and the hold is off; after the end the hold is off; the flags absent →
today (B137's `Today`, and the bridge's own default).

    python3 -m unittest discover -s tests/b141_party_select_held -v
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
sys.path.insert(0, str(ROOT / "companion"))
import test_b114 as b114  # noqa: E402
import test_b124 as b124  # noqa: E402


class SelectHeld(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b114.b99.tree()
        b124.IDS.clear()
        b124.IDS.update(ids)
        cls.s = b114.run(root, b114.BOTH, ids, "nopress", extra=b124.extra)["steps"]

    def test_0_no_select_and_no_hotkey_during_the_preparation_and_the_hold(self):
        s = self.s
        self.assertTrue(s["sl_hold_seen"])
        self.assertEqual(s["sl_ready"], "ready")
        self.assertEqual(s["sl_select_written_before_practice"], 0)
        self.assertEqual(s["sl_hotkeys_before_practice"], 0)

    def test_1_nor_on_a_practices_way_back(self):
        s = self.s
        self.assertEqual(s["sl_back"], "ready")
        self.assertEqual(s["sl_select_written_way_back"], 0)
        self.assertEqual(s["sl_hotkeys_way_back"], 0)
        self.assertTrue(s["sl_states_same"])

    def test_2_after_the_go_select_passes_and_the_hold_is_off_after_the_end(self):
        s = self.s
        self.assertEqual(s["sl_go"], "taken")
        self.assertGreaterEqual(s["sl_select_written_after_go"], 1)
        self.assertFalse(s["sl_held_flag_after_go"])
        self.assertFalse(s["sl_held_flag_after_end"])


class BridgeDefault(unittest.TestCase):
    def test_the_bridge_passes_select_unless_held(self):
        import native_session_io as nsio
        b = nsio.NativeControllerBridge(Path(HERE / "_unused"))
        b._gamepads = ["P1", "P2", "P3", "P4"]
        b._controller_backend = "linux_uinput"
        seen = []
        b._write_linux_report_locked = lambda index, report, *a, **k: seen.append((index, report["buttons"]))
        self.assertFalse(b._party_hold_select)                       # today
        b._apply_report(0, 0x0020 | 0x0100, 0, 0, 0, 0, 0, 0)
        self.assertEqual(seen[-1], (0, 0x0120))
        b.party_hold_select(True)                                    # the pad holding Select is written without it
        self.assertEqual(seen[-1], (0, 0x0100))
        b._apply_report(1, 0x0020 | 0x0010, 0, 0, 0, 0, 0, 0)
        self.assertEqual(seen[-1], (1, 0x0010))
        b.party_hold_select(False)
        b._apply_report(1, 0x0020, 0, 0, 0, 0, 0, 0)
        self.assertEqual(seen[-1], (1, 0x0020))


if __name__ == "__main__":
    unittest.main()
