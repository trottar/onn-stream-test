#!/usr/bin/env python3
"""B140 (host): the paused begin made sure of before it is read — through the real HTTP server on loopback, behind
PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1.

B114's scenario, its `nopress` mode (B137's fake title, taught to show its begin only N frames after a load): after
the paused load the hub advances frames in steps (0, 2, 4, 8, 16, 30) with a grab after each, until the window has moved
from its pre-load picture (or the read names the start), the cap 60 frames; presses from every pad every 0.2 s
throughout.

Checked: the begin after **0, 2 and 12** frames → `ready`, the row naming 0 / 2 / 14 frames in 1 / 2 / 4 steps,
`changed` true, the fake never resumed from the launch's answer to the go, every frame it ran saw neutral pads,
`playing` on the begin, scored; **never** → `given_up` "…the title did not show its starting point" within a few
seconds (60 frames, `changed` false), no route, no switch, never resumed, no frame with a button; the practices' ways
back with a 12-frame title the same; B137's cases with the new row; the flags absent → today (B137's `Today`).

    python3 -m unittest discover -s tests/b140_party_begin_shown -v
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
import test_b114 as b114  # noqa: E402
import test_b124 as b124  # noqa: E402

NO_BEGIN = "the title did not show its starting point"


class BeginShown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b114.b99.tree()
        b124.IDS.clear()
        b124.IDS.update(ids)
        cls.out = b114.run(root, b114.BOTH, ids, "nopress", extra=b124.extra)
        cls.s = cls.out["steps"]

    def _clean(self, seg, tag, advances):
        self.assertTrue(seg.get("paused_from"), (tag, seg))
        self.assertEqual(seg["resumes"], 0, (tag, seg))
        self.assertEqual(seg["frames_with_a_button"], 0, (tag, seg))
        self.assertEqual(seg["left_start"], 0, (tag, seg))
        self.assertEqual(seg["advances"], advances, (tag, seg))

    def test_0_the_begin_after_0_2_12_frames_ready_with_the_frames_the_row_names(self):
        s = self.s
        for tag, frames, steps in (("v0", 0, 1), ("v2", 2, 2), ("v12", 14, 4)):
            self.assertEqual(s[tag + "_ready"]["phase"], "ready", tag)
            row = [r for r in s[tag + "_row_fields"] if r["step"] == "minigame_frame_advance"]
            self.assertEqual(len(row), 1, tag)
            self.assertEqual((row[0]["frames"], row[0]["batches"], row[0]["changed"], row[0]["paused"]),
                             (frames, steps, True, True), tag)
            self.assertGreaterEqual(row[0]["moved"], 0.20, tag)
            self._clean(s[tag + "_segment"], tag, frames)
            for w in s[tag + "_mute"]:
                self.assertEqual(w["buttons_written"], 0, (tag, w))
            self.assertEqual(s[tag + "_on_the_begin"], {"left_start_at_first_frame": False, "loads_after_go": 0}, tag)
            self.assertEqual(s[tag]["state"], "ended", tag)

    def test_1_never_fails_plainly_at_the_cap(self):
        s = self.s
        self.assertEqual(s["vn"]["state"], "given_up")
        self.assertIn(NO_BEGIN, s["vn"]["why"])
        self.assertLess(s["vn_s"], 10.0)                         # not "not recognised" 15 s later
        self.assertEqual(s["vn_row"][0]["frames"], 60)
        self.assertEqual((s["vn_row"][0]["batches"], s["vn_row"][0]["changed"]), (6, False))
        self.assertEqual(s["vn_resumes"], 0)
        self.assertEqual(s["vn_frames_with_a_button"], 0)
        self.assertNotIn("minigame_route", s["vn_rows"])
        self.assertEqual(s["vn_switches"], [])
        self.assertTrue(s["vn_title_gone"])

    def test_2_the_ways_back_the_same(self):
        s = self.s
        for n in range(2):
            self.assertEqual(s[f"vp_back{n + 1}"], {"state": "starting", "phase": "ready", "practices": n + 1})
            self._clean(s["vp_way_back_segments"][n], f"way back {n + 1}", 14)
        self.assertEqual([(r["frames"], r["batches"], r["changed"]) for r in s["vp_fa_rows"]], [(14, 4, True)] * 3)
        self.assertEqual(s["vp_on_the_begin"], {"left_start_at_first_frame": False, "loads_after_go": 0})


if __name__ == "__main__":
    unittest.main()
