#!/usr/bin/env python3
"""B205 (host): synthetic training for the score kind — templates only; every gate measured on the real glyphs. Fast
tests on made-up glyph cells and a made-up picture (no title; no temp dir made).

- `Gates`: `_digit_stats` with training cells — the templates move toward them, but each digit's own spread is the
  real glyphs' farthest from its template (a far synthetic outlier never widens it), and with no training cells it is
  B178's, unchanged.
- `Make`: `synthetic_digits` is deterministic for one seed, makes only keys some real glyph has, at the asked count.

    python3 -m unittest discover -s tests/b205_synthetic_digits -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests" / "b204_every_number")]
import h7_endscreen as es  # noqa: E402
import test_b204 as b204  # noqa: E402  (its made-up glyph cells and font)


def real_cells() -> dict:
    rng = np.random.default_rng(205)
    return {d: [b204.glyph(b204.FONT[d], 4, rng) for _ in range(3)] for d in "038"}


class Gates(unittest.TestCase):
    def test_1_no_training_is_today(self):
        cells = real_cells()
        a = es._digit_stats(cells, {k: 2 for k in cells})
        b = es._digit_stats(cells, {k: 2 for k in cells}, {})
        self.assertTrue(np.array_equal(a[1], b[1]))
        self.assertEqual((a[2], a[3]), (b[2], b[3]))

    def test_2_a_far_synthetic_glyph_never_widens_a_digits_own_spread(self):
        cells = real_cells()
        far = np.ones_like(cells["3"][0])                     # a synthetic "3" unlike any real 3
        keys, refs, gaps, need, noise, small = es._digit_stats(cells, {k: 2 for k in cells}, {"3": [far]})
        i = keys.index("3")
        own = max(float(es.cell_dists(c, refs[i:i + 1])[0]) for c in cells["3"])   # the real 3s only
        self.assertGreater(float(es.cell_dists(far, refs[i:i + 1])[0]), own)        # the outlier is farther ...
        real_noise = max(max(float(es.cell_dists(c, refs[j:j + 1])[0]) for c in cells[k]) for j, k in enumerate(keys))
        self.assertAlmostEqual(noise, real_noise, places=6)                           # ... and not counted, in the
        self.assertAlmostEqual(gaps["3"]["worst_own"], round(max(own, real_noise), 4), places=4)   # noise or the spread
        self.assertFalse(np.array_equal(refs[i], np.mean(cells["3"], axis=0)))       # the template did move


class Make(unittest.TestCase):
    def real(self):
        rng = np.random.default_rng(7)
        a = np.clip(rng.normal(90, 20, (120, 160)), 0, 255).astype(np.float32)
        out = []
        for d in "03":
            crop = np.full((32, 24), 40, np.float32)
            ink = np.zeros((32, 24), bool)
            for r, row in enumerate(b204.FONT[d]):
                for c, bit in enumerate(row):
                    if bit == "1":
                        crop[2 + 4 * r:6 + 4 * r, 2 + 4 * c:6 + 4 * c] = 230
                        ink[2 + 4 * r:6 + 4 * r, 2 + 4 * c:6 + 4 * c] = True
            out.append(("" + d, crop, ink, 1))
        return out, [a]

    def test_1_deterministic_and_only_real_keys(self):
        real, frames = self.real()
        x = es.synthetic_digits(real, frames, {"": {28, 12}}, np.random.default_rng(1), 5)
        y = es.synthetic_digits(real, frames, {"": {28, 12}}, np.random.default_rng(1), 5)
        self.assertEqual(sorted(x), ["0", "3"])
        self.assertEqual([len(v) for v in x.values()], [5, 5])
        self.assertTrue(all(np.array_equal(p, q) for k in x for p, q in zip(x[k], y[k])))
        self.assertEqual(x["0"][0].shape, (es.SCORE_CELL[0] + 2, es.SCORE_CELL[1] + 2))


if __name__ == "__main__":
    unittest.main()
