#!/usr/bin/env python3
"""B200 (host): a `score` title whose numbers are drawn with a leading 0 (T92's final screen, made up), read as drawn;
a place whose glyphs are the same shape in saves labelled with different digits never taken. Every picture made-up
(`pad_capture.py`; B178's `score_capture.py` for `Panel`); no title, nothing read from the hub's own folders.

- `Drawn`: the made-up padded screen (big padded finals beside a box of small padded period cells, only the first
  filled; digit-like headings; a stats table of "00"; every final's leading 0 hollow), four end saves, finals 0-3,
  `--max-score 3`, read as drawn ("03+_+_+_+_=03-01+_+_+_+_=01") -> label PASS (the finals' places on the finals, the
  first cells found off the finals' line, in their own group "c:"), learn PASS, the spec's places the numbers.
- `Single`: the same saves read as single numbers ("3+_+_+_+_=3-1+_+_+_+_=1") -> label FAIL, never a PASS; never a
  place on the hollow of a final's leading 0 (the trap T92's first run fell into); learn refused.
- `Counted`: two periods filled (the cells 01 + 02 = the final 03): the cells' 2 is never in a final; B204 (queue BN):
  the cells are the finals' font at another size, so their 2 counts and learn passes (B200 had it
  short; a small font of another face teaches nothing: `tests/b204_every_number`, `Sizes`).
- `Panel` (B198's disclosed case): B178's own made-up final screen (a dark panel under each number) with single-digit
  finals -> the places found are the numbers (never the panel), or the place cell is not met; never a panel taken.
- `Value`: `Drawn` — its value for checks, its glyphs for counts; a reading without a leading 0 is today's text.
Temp dirs removed.

    python3 -m unittest discover -s tests/b200_drawn_places -v
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(HERE), str(ROOT / "tests" / "b198_max_score"),
                str(ROOT / "tests" / "b181_every_digit"), str(ROOT / "tests" / "b178_score_kind")]
import pad_capture as pc  # noqa: E402
import test_b198 as b198  # noqa: E402  (its Made: the tool, the made-up saves, --max-score in the binding)

_ = None
BLANKS = [_, _, _, _]
PAD = {"begin": {"kind": "begin"}, "other": {"kind": "other"},
       "end_P1": {"kind": "end_pad", "s": [2, 0], "q": [[2, *BLANKS], [0, *BLANKS]], "look": 1},
       "end_P1_2": {"kind": "end_pad", "s": [3, 1], "q": [[3, *BLANKS], [1, *BLANKS]], "look": 2},
       "end_P2": {"kind": "end_pad", "s": [1, 3], "q": [[1, *BLANKS], [3, *BLANKS]], "look": 3},
       "end_P2_2": {"kind": "end_pad", "s": [0, 2], "q": [[0, *BLANKS], [2, *BLANKS]], "look": 4}}
TWO = [_, _, _]
COUNTED = {"begin": {"kind": "begin"}, "other": {"kind": "other"},     # the cells show 2; no final does
           "end_P1": {"kind": "end_pad", "s": [3, 0], "q": [[1, 2, *TWO], [0, 0, *TWO]], "look": 1},
           "end_P1_2": {"kind": "end_pad", "s": [3, 1], "q": [[2, 1, *TWO], [1, 0, *TWO]], "look": 2},
           "end_P2": {"kind": "end_pad", "s": [0, 3], "q": [[0, 0, *TWO], [2, 1, *TWO]], "look": 3},
           "end_P2_2": {"kind": "end_pad", "s": [1, 3], "q": [[1, 0, *TWO], [1, 2, *TWO]], "look": 4}}
PANEL = {"begin": {"kind": "begin"}, "other": {"kind": "other"},       # B178's screen, single-digit finals
         "end_P1": {"kind": "end", "s": [4, 1], "look": 1}, "end_P1_2": {"kind": "end", "s": [3, 0], "look": 2},
         "end_P2": {"kind": "end", "s": [1, 3], "look": 3}, "end_P2_2": {"kind": "end", "s": [0, 4], "look": 4}}
PLACE = "the numbers at one place in every save"


def drawn(st: dict) -> str:
    """The reading as the screen draws it: every number padded to two digits."""
    return "-".join("+".join("_" if c is None else pc.pad(c) for c in cells) + "=" + pc.pad(fin)
                    for cells, fin in zip(st["q"], st["s"]))


def single(st: dict) -> str:
    return "-".join("+".join("_" if c is None else str(c) for c in cells) + "=" + str(fin)
                    for cells, fin in zip(st["q"], st["s"]))


def inside(pl: dict, box: tuple) -> bool:
    """A place within a drawn box (x0, top, x1, bot) at the score picture's size (the game's area, 640 x 480)."""
    return box[0] - 4 <= pl["x0"] and pl["x1"] <= box[2] + 4 and box[1] - 4 <= pl["top"] and pl["bot"] <= box[3] + 4


def final_box(k: int) -> tuple:
    cx = pc.FINAL_X[k]
    w = 2 * 30 + 6
    return (cx - w // 2, pc.FINAL_TOP, cx + w // 2, pc.FINAL_TOP + 42)


def lead_zero(k: int) -> tuple:
    """A final's leading 0 (its hollow inside): the left glyph of the padded final."""
    cx = pc.FINAL_X[k]
    return (cx - 33, pc.FINAL_TOP, cx - 3, pc.FINAL_TOP + 42)


def cell_box(k: int) -> tuple:
    cx = pc.CELL_X[k]
    return (cx - 11, pc.BOX[1] + 6, cx + 11, pc.BOX[1] + 6 + 14)


class Made(b198.Made):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ["PARTY_ADD_GAME_CAPTURE"] = "pad_capture:capture"     # restored by B181's tearDownClass

    def label_with(self, code: str, saves: dict, read, look: bool = True) -> tuple[int, str]:
        texts = {r: read(st) for r, st in saves.items() if r.startswith("end_")}
        rc, out = self.tool("label", code, *[f"{r}={t},{t}" for r, t in sorted(texts.items())])
        if rc == 1 and look and "Look at label/digits.png" in out:
            rc, out = self.tool("label", code, "look=all")
        return rc, out

    def places(self, code: str) -> list:
        return json.loads(self.pag.label_path(code).read_text()).get("places") or []


class Drawn(Made):
    def test_1_read_as_drawn_label_and_learn_pass(self):
        self.put_max("T71", PAD, 3)
        rc, out = self.label_with("T71", PAD, drawn)
        v = self.verdict("T71", "label")
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))
        self.assertEqual(v["cells"][PLACE], "found")
        pls = self.places("T71")
        self.assertTrue(inside(pls[0], final_box(0)) and inside(pls[1], final_box(1)), pls)
        rc, out = self.tool("learn", "T71")
        v = self.verdict("T71", "learn")
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))
        spec = json.loads((Path(os.environ["PRIVYHUB_H7_RULES"]) / "madeupt71.endscreen.json").read_text())
        cols = spec["score"]["columns"]
        for k in range(2):                                     # the first period's cell, off the finals' line
            self.assertTrue(cols[k][0] and inside(cols[k][0], cell_box(k)), cols)
            self.assertTrue(cols[k][0]["offline"])
            self.assertEqual(cols[k][0]["group"], "")            # B204 (queue BN): one font at another size, counted
            self.assertEqual(cols[k][1:], [None] * 4)
        self.assertEqual(sorted({k[:-1] for k in spec["score"]["keys"]}), [""])
        self.assertTrue(spec["score"]["sizes"]["c:"]["counted"])
        self.assertEqual(v["recorded"]["digits"]["expected"], list("0123"))


class Single(Made):
    def test_1_single_numbers_never_take_a_same_shape_place(self):
        self.put_max("T72", PAD, 3)
        rc, out = self.label_with("T72", PAD, single)
        v = self.verdict("T72", "label")
        self.assertEqual(rc, 1, out)                           # never a PASS
        self.assertNotEqual(v["verdict"], "PASS")
        for pl in self.places("T72"):                          # never the hollow of a final's leading 0
            for k in range(2):
                self.assertFalse(inside(pl, lead_zero(k)), pl)
        if PLACE in v["bad"]:
            self.assertIn("as drawn, leading zeros included", out)
        rc, out = self.tool("learn", "T72")
        self.assertEqual(rc, 2, out)                           # refused: label has no PASS


class Counted(Made):
    def test_1_small_cells_of_the_score_font_count(self):
        self.put_max("T73", COUNTED, 3)
        rc, out = self.label_with("T73", COUNTED, drawn)
        v = self.verdict("T73", "label")
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))
        rc, out = self.tool("learn", "T73")
        v = self.verdict("T73", "learn")
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))     # B204 (queue BN): the cells are the finals' font at
        cell = b198.cell(3, "0123")                             # another size, so their 2 counts and learn passes
        self.assertEqual(v["cells"][cell]["shown by fewer than two saves"], [])   # (B200 had 2 short; another face
        #                                                                           teaches nothing: test_b204.Sizes)


class Panel(Made):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ["PARTY_ADD_GAME_CAPTURE"] = "score_capture:capture"

    def test_1_a_panel_never_taken(self):
        self.put_max("T74", PANEL, 4)
        texts = {r: "-".join(str(x) for x in st["s"]) for r, st in PANEL.items() if r.startswith("end_")}
        rc, out = self.tool("label", "T74", *[f"{r}={t},{t}" for r, t in sorted(texts.items())])
        v = self.verdict("T74", "label")
        pls = self.places("T74")
        if v["cells"].get(PLACE) == "found":                  # the numbers themselves, never the panel under them
            for cx, pl in zip((100, 540), pls):               # score_capture: each number at cx, rows 276-303
                self.assertTrue(inside(pl, (cx - 14, 272, cx + 14, 308)), pls)
        else:
            self.assertIn(PLACE, v["bad"], out)
            self.assertEqual(pls, [])


class Value(unittest.TestCase):
    def test_1_drawn(self):
        import h7_endscreen as es
        x = es.Drawn("03")
        self.assertEqual((x, str(x), f"{x}", json.dumps(x), x + 1, x > 2), (3, "03", "03", "3", 4, True))
        self.assertEqual([str(v) for v in es.score_numbers("end_s03+_=03-01+_=01")], ["03", "01"])
        self.assertEqual([[str(c) if c is not None else None for c in r] for r in es.score_cells("end_s03+_=03-01+_=01")],
                         [["03", None], ["01", None]])

    def test_2_a_reading_without_a_leading_zero_is_today(self):
        import party_add_game as pag
        for t in ("9+2+2+2+_+_=15-0+0+2+0+_+_=2", "21-14", "0-2"):
            self.assertEqual(pag._text(pag._sides(t)), t)
        self.assertEqual(pag._text(pag._sides("03+_=03-00+_=00")), "03+_=03-00+_=00")
        self.assertEqual(pag._digits_of("03-01"), {"0", "1", "3"})
        self.assertEqual(pag._finals("05-04"), [5, 4])


if __name__ == "__main__":
    unittest.main()
