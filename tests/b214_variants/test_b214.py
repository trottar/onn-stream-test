#!/usr/bin/env python3
"""B214 / B215 / B216 (host): the once rule's test variants (each the glyph that was pasted: cut as one glyph, at least
SYN_OWN of its ink pasted ink; redrawn up to 24 draws; eight needed; never in the templates), plan's last line the
whole ask (= train's), register on three saves on the new path. Made-up pictures only (B178's font); temp dirs removed
(B178's harness).

- `Variants`: a background that merges every paste into two glyphs is thrown away and the next draw taken — eight
  valid from a mix; none valid in 24 draws from bad backgrounds only -> not counted, "variants could not be made";
  valid variants read as another symbol -> refused, and the record says what they read as.
- `Ask`: plan's last line = train's on three made-up titles (all counted; a digit never seen; once-seen digits not
  counted for want of a rigidity); the templates' synthetic glyphs are exactly SYN_PER_GLYPH a real glyph (no test
  variant among them).
- `Register`: three saves of a made-up score title -> "kept states present" met (the new path); a title the old
  learn wrote -> the old two-per-ending minimum; a second register keeps the survey.

    python3 -m unittest discover -s tests/b214_variants -v
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests" / "b208_survey"), str(ROOT / "tests" / "b178_score_kind")]
import test_b208 as b208  # noqa: E402  (B178's harness with --max-score, and its made-up titles)
import score_capture as sc  # noqa: E402

FULL, NO_3 = b208.FULL, b208.NO_3
B, O = b208.B, b208.O
NO_RIGIDITY = {"begin": B, "other": O, "end_P1": {"kind": "end", "s": [1, 0], "look": 1},
               "end_P2": {"kind": "end", "s": [0, 2], "look": 3}}


def picture(text: str | None, blob: bool = False) -> np.ndarray:
    """A flat grey 640 x 480 with a dark panel; `text` centred at (100, 276) in B178's font; `blob`: a bright bar of a
    glyph's height inside the panel beside the number's place (every paste then cuts as two glyphs)."""
    im = Image.new("L", (640, 480), 120)
    d = ImageDraw.Draw(im)
    d.rectangle((40, 250, 160, 330), fill=35)
    if text:
        sc.number(d, 100, 276, text)
    if blob:
        d.rectangle((116, 276, 121, 303), fill=235)
    return np.asarray(im, dtype=np.float32)


class Variants(unittest.TestCase):
    def setUp(self):
        import party_steps as st
        import h7_endscreen as es
        self.st, self.es = st, es
        self.a = picture("4")
        self.region = [60, 266, 140, 314]
        self.place = st.region_place(self.a, self.region)
        self.g = st.region_glyphs(self.a, self.place)[0]
        self.good = st.erase(self.a, self.place, self.region)
        self.bad = st.erase(picture(None, blob=True), self.place, self.region)
        self.bad[276:304, 116:122] = 235.0                         # the bar survives the erase (drawn back)

    def test_0_the_share_is_b192s(self):
        self.assertEqual((self.st.SYN_OWN, self.st.VARIANTS_NEEDED, self.st.VARIANT_DRAWS),
                         (self.es.SYN_OWN, 8, 24))

    def test_1_a_bad_cut_is_redrawn_not_counted_against(self):
        rng = np.random.default_rng(214)
        v, draws = self.st.test_variants(self.a, self.g, [self.good, self.bad], self.place, self.region, rng)
        self.assertEqual(len(v), 8)
        self.assertGreater(draws, 8)                               # some draws were thrown away
        self.assertLessEqual(draws, 24)

    def test_2_fewer_than_eight_not_counted_and_said(self):
        rng = np.random.default_rng(214)
        v, draws = self.st.test_variants(self.a, self.g, [self.bad], self.place, self.region, rng)
        self.assertEqual((len(v), draws), (0, 24))
        ok, row = self.st._once_rule("score", "4", {"rigidity": 0.9}, v, [], lambda c: "4")
        self.assertFalse(ok)
        self.assertIn("variants could not be made", row["variants"])
        ok, row = self.st._once_rule("score", "4", {"rigidity": 0.9}, ["x"] * 7, [], lambda c: "4")
        self.assertFalse(ok)                                       # seven read right are not eight

    def test_4_one_cut_with_foreign_ink_is_not_the_pasted_glyph(self):
        """A bar of the line's height in the glyph's columns: every paste cuts as exactly one glyph; where the bar is not
        under the pasted glyph's own ink, less than SYN_OWN of the cut is pasted ink -> thrown away (only the share says
        so): 24 draws, fewer than eight valid."""
        merged = self.good.copy()
        merged[276:304, 98:102] = 235.0
        rng = np.random.default_rng(214)
        v, draws = self.st.test_variants(self.a, self.g, [merged], self.place, self.region, rng)
        self.assertEqual(draws, 24)
        self.assertLess(len(v), 8)
        pic = merged.copy()
        self.assertEqual(len(self.es.place_glyphs(pic, self.place) or []), 1)     # the bar alone: one glyph

    def test_3_valid_variants_misread_still_refused(self):
        ok, row = self.st._once_rule("score", "4", {"rigidity": 0.9}, ["x"] * 8, [], lambda c: "9")
        self.assertFalse(ok)
        self.assertEqual(row["variants read as"], {"9": 8})
        ok, _row = self.st._once_rule("score", "4", {"rigidity": 0.9}, ["x"] * 8, [], lambda c: "4")
        self.assertTrue(ok)


class Ask(b208.Made):
    def ask_of(self, code: str, saves: dict) -> tuple[str, str]:
        self.put(code, saves)
        self.surveyed(code)
        self.labelled(code, saves)
        rc, plan = self.tool("plan", code)
        self.assertEqual(rc, 0, plan)
        _rc, train = self.tool("train", code)
        return plan.strip().splitlines()[-1], train.strip().splitlines()[-1]

    def test_1_plan_equals_train_on_every_made_up_title(self):
        got = {code: self.ask_of(code, saves) for code, saves in (("T71", FULL), ("T72", NO_3), ("T73", NO_RIGIDITY))}
        for code, (plan, train) in got.items():
            self.assertEqual(plan, train, code)
        self.assertEqual(got["T71"][0], "Nothing more is needed.")
        self.assertEqual(got["T72"][0], "Still needed: a final score with a 3 in it (either player).")
        self.assertIn("a final score with a 1 in it", got["T73"][0])     # seen once, no rigidity: asked by plan
        self.assertIn("a final score with a 2 in it", got["T73"][0])
        rec = self.verdict("T73", "plan")["recorded"]
        self.assertEqual(sorted(rec["train's gates"]["not counted"]), ["1", "2"])

    def test_2_no_test_variant_in_the_templates(self):
        import party_steps as st
        self.ask_of("T74", FULL)
        syn = self.verdict("T74", "train")["recorded"]["synthetic"]
        first = sum(len(str(x)) for r, s_ in FULL.items() if r.startswith("end_") for x in s_["s"])
        self.assertEqual(syn["made"] + syn["not cut"], st.SYN_PER_GLYPH * first)
        self.assertTrue(all(v["valid"] == st.VARIANTS_NEEDED for v in syn["variants"].values()), syn["variants"])


class Register(b208.Made):
    def setUp(self):
        drop = self.tmp / "dropins"
        drop.mkdir(exist_ok=True)
        for i in range(18):
            (drop / f"line{i:02d}.conf").write_text(f"[Service]\nEnvironment=PRIVYHUB_LINE{i:02d}=1\n")
        self.saved = self.pag._find_title
        self.pag._find_title = lambda system, words: {"game": "madeup" + self.code.lower(), "title": "",
                                                      "content": "", "relative_path": ""}

    def tearDown(self):
        self.pag._find_title = self.saved

    def register(self, code: str, check: bool = True) -> dict:
        self.code = code
        a = {"players": 2, "system": "ps1", "result": "score", "find": "x", "check": check, "collect": [],
             "readings": []}
        cells, b, _inputs = self.pag._register(code, a)
        return {r["cell"]: r for r in cells.rows}

    def test_1_three_saves_pass_on_the_new_path(self):
        self.put("T75", {k: FULL[k] for k in ("begin", "other", "end_P1")})
        rows = self.register("T75")
        self.assertTrue(rows["kept states present"]["met"], rows["kept states present"])
        self.assertNotIn("missing", rows)
        self.assertTrue(all(r["met"] for r in rows.values()), [r for r in rows.values() if not r["met"]])

    def test_2_a_title_the_old_learn_wrote_keeps_the_old_minimum(self):
        self.put("T76", {k: FULL[k] for k in ("begin", "other", "end_P1")})
        (self.pag.rules_folder() / "madeupt76.party.json").write_text(json.dumps({"players": 2, "result": "score"}))
        rows = self.register("T76")
        self.assertFalse(rows["kept states present"]["met"])
        self.assertEqual(rows["missing"]["read"], ["end_P1_2", "end_P2", "end_P2_2"])

    def test_3_a_second_register_keeps_the_survey(self):
        self.put("T77", FULL)
        self.surveyed("T77")
        self.register("T77", check=False)
        self.assertEqual(self.pag.load_binding("T77")["survey"]["kind"], "score")


if __name__ == "__main__":
    unittest.main()
