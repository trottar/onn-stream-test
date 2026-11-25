#!/usr/bin/env python3
"""B221 (host): a valid test variant is the glyph's own size — besides B214's two conditions (one glyph cut; at least
SYN_OWN of its ink pasted), its cut box within VARIANT_SIZE_TOL (2) px of the pasted glyph's width and height. Made-up
picture (B178's font, B214's panel); no title; no temp dir.

- `Size`: a thin line beside the 4's crossbar joins the pasted 4 into one wider cut on some shifts (its ink share still
  above SYN_OWN, so only the size says so) — those draws thrown away and redrawn, eight valid made, the symbol not
  refused for them; with no line, every draw is valid; a variant of the glyph's own size that is misread still
  refuses the symbol.

    python3 -m unittest discover -s tests/b221_variant_size -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests" / "b214_variants"), str(ROOT / "tests" / "b208_survey"),
                str(ROOT / "tests" / "b178_score_kind")]
import test_b214 as b214  # noqa: E402  (its made-up picture)


class Size(unittest.TestCase):
    def setUp(self):
        import party_steps as st
        import h7_endscreen as es
        self.st, self.es = st, es
        self.a = b214.picture("4")
        self.region = [60, 266, 140, 314]
        self.place = st.region_place(self.a, self.region)
        self.g = st.region_glyphs(self.a, self.place)[0]
        self.good = st.erase(self.a, self.place, self.region)
        self.lined = self.good.copy()
        self.lined[293, 111:119] = 235.0                  # touches the crossbar when the 4 is shifted right

    def test_0_the_tolerance(self):
        self.assertEqual(self.st.VARIANT_SIZE_TOL, 2)

    def test_1_a_joined_wider_cut_is_redrawn_not_counted_against(self):
        rng = np.random.default_rng(221)
        v, draws = self.st.test_variants(self.a, self.g, [self.lined], self.place, self.region, rng)
        self.assertEqual(len(v), 8)                        # the symbol still gets its eight
        self.assertGreater(draws, 8)                       # some joined cuts were thrown away

    def test_2_the_joined_cut_is_wider_and_passes_the_share(self):
        """The line really makes a wider single cut whose ink share is above SYN_OWN (so only B221 throws it away)."""
        E, st = self.es, self.st
        t, l, b, r = self.g[0], self.g[1], self.g[2], self.g[3]
        ink = E._ink(self.a, self.place["pol"], int(self.place["r"]), E._contrast(self.a))[t:b + 1, l:r + 1]
        pic = self.lined.copy()
        cx = (self.region[0] + self.region[2]) // 2 - (r - l + 1) // 2 + 3      # dx = +3
        pic[t:b + 1, cx:cx + r - l + 1][ink] = self.a[t:b + 1, l:r + 1][ink]
        gl = E.place_glyphs(pic, self.place)
        self.assertEqual(len(gl), 1)
        c = gl[0]
        self.assertGreater((c[3] - c[1] + 1) - (r - l + 1), st.VARIANT_SIZE_TOL)
        pasted = np.zeros(pic.shape, bool)
        pasted[t:b + 1, cx:cx + r - l + 1] = ink
        cut = E._ink(pic, self.place["pol"], int(self.place["r"]), E._contrast(pic))[c[0]:c[2] + 1, c[1]:c[3] + 1]
        share = float((cut & pasted[c[0]:c[2] + 1, c[1]:c[3] + 1]).sum()) / float(cut.sum())
        self.assertGreaterEqual(share, st.SYN_OWN)

    def test_3_no_line_every_draw_valid(self):
        rng = np.random.default_rng(221)
        v, draws = self.st.test_variants(self.a, self.g, [self.good], self.place, self.region, rng)
        self.assertEqual((len(v), draws), (8, 8))

    def test_4_a_right_sized_misread_variant_still_refuses(self):
        rng = np.random.default_rng(221)
        v, _draws = self.st.test_variants(self.a, self.g, [self.good], self.place, self.region, rng)
        ok, row = self.st._once_rule("score", "4", {"rigidity": 0.9}, v, [], lambda c: "?")
        self.assertFalse(ok)
        self.assertEqual(row["variants read as"], {"?": 8})


if __name__ == "__main__":
    unittest.main()
