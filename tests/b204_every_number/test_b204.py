#!/usr/bin/env python3
"""B204 (host): every number on a score title's final screen, and another size of the score's font counted only when
the title's own numbers say so. Fast tests (no pictures but made-up glyph cells); no title.

- `Reading`: a side's stats rows after ':' parsed and written back as given; a reading without ':' is today's text;
  the learner's class carries every stats row as one more column; the sum is over the period cells only.
- `Sizes`: `_one_font` — one font drawn at two sizes (each digit's two cells near, two digits far) -> counted; two
  faces (one size's 3 drawn like another's 8) -> not counted; no digit in both -> not counted.
Temp dirs: none made.

    python3 -m unittest discover -s tests/b204_every_number -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools")]
import h7_endscreen as es  # noqa: E402
import party_add_game as pag  # noqa: E402

T92_LIKE = "02+_+_+_+_=02:13.00.00.00.01.00-00+_+_+_+_=00:00.00.00.00.00.00"


class Reading(unittest.TestCase):
    def test_1_stats_round_trip(self):
        self.assertTrue(pag.READING.match(T92_LIKE))
        self.assertEqual(pag._text(pag._sides(T92_LIKE)), T92_LIKE)
        for t in ("9+2+2+2+_+_=15-0+0+2+0+_+_=2", "21-14", "03+_=03-00+_=00", "5:1.2-3:0.0"):
            self.assertEqual(pag._text(pag._sides(t)), t)

    def test_2_the_learners_class(self):
        self.assertEqual(pag._score_class(T92_LIKE),
                         "end_s02+_+_+_+_+13+00+00+00+01+00=02-00+_+_+_+_+00+00+00+00+00+00=00")
        self.assertEqual(pag._score_class("21-14"), "end_s21-14")
        self.assertTrue(es.SCORE_LABEL.match(pag._score_class(T92_LIKE)))

    def test_3_the_sum_over_the_periods_only(self):
        cells, fin = pag._sides(T92_LIKE)[0]
        self.assertEqual([str(c) if c is not None else None for c in pag._periods(cells)], ["02", None, None, None, None])
        self.assertEqual(sum(x for x in pag._periods(cells) if x is not None), fin)
        self.assertEqual(len(cells), 11)                       # every stats row one more column
        self.assertEqual(pag._digits_of(T92_LIKE), {"0", "1", "2", "3"})


def glyph(pattern: list[str], scale: int, rng) -> np.ndarray:
    """A made-up glyph cell: a 5 x 7 pattern drawn at `scale`, then brought to the cell's size (as `glyph_cell` does)."""
    from PIL import Image
    a = np.kron(np.array([[1.0 if c == "1" else 0.0 for c in row] for row in pattern], np.float32),
                np.ones((scale, scale), np.float32))
    a = np.clip(a + rng.normal(0, 0.03, a.shape), 0, 1)
    ch, cw = es.SCORE_CELL
    w = min(cw, max(1, int(round(a.shape[1] * ch / a.shape[0]))))
    arr = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((w, ch), Image.BOX), np.float32) / 255.0
    cell = np.zeros((ch + 2, cw + 2), np.float32)
    off = (cw + 2 - w) // 2
    cell[1:ch + 1, off:off + w] = arr
    return cell


FONT = {"0": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
        "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
        "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"]}


class Sizes(unittest.TestCase):
    def cells(self, small_font: dict) -> dict:
        rng = np.random.default_rng(204)
        out = {}
        for d in "038":
            out[d] = [glyph(FONT[d], 8, rng) for _ in range(3)]
            out["c:" + d] = [glyph(small_font[d], 2, rng) for _ in range(3)]
        return out

    def test_1_one_font_counted(self):
        one, same, two = es._one_font(self.cells(FONT), "", "c:")
        self.assertTrue(one, (same, two))
        self.assertLess(same, two)

    def test_2_two_faces_not_counted(self):
        other = {**FONT, "3": FONT["8"], "8": FONT["3"]}         # the small face's 3 and 8 swapped shapes
        one, same, two = es._one_font(self.cells(other), "", "c:")
        self.assertFalse(one, (same, two))

    def test_3_no_digit_in_both(self):
        cells = {"0": self.cells(FONT)["0"], "c:3": self.cells(FONT)["c:3"]}
        self.assertEqual(es._one_font(cells, "", "c:"), (False, None, None))


if __name__ == "__main__":
    unittest.main()
