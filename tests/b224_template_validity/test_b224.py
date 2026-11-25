#!/usr/bin/env python3
"""B224 (host): the score path's template stream keeps a synthetic glyph only when it is valid as a test variant is
(B214 / B221: one glyph cut, at least SYN_OWN of its cut ink pasted, its cut box the pasted glyph's own size within
VARIANT_SIZE_TOL) — one that is not is thrown away and the next drawn from the same stream, up to VARIANT_DRAWS; fewer
valid is recorded, never an error. A title with no draw thrown away is byte for byte the predecessor's (queue BU's
`c7750afc`, loaded from git); the letters path is not touched. Made-up pictures only (B178's font, B214's panel,
B191's letters); temp dirs removed (the suites' harnesses).

- `Stream`: B221's line joins the pasted 4 into one wider cut on some shifts — those draws thrown away and redrawn,
  eight made, none of them a joined cut; a background where every paste cuts as two glyphs — none made in 24 draws,
  recorded; no line — the templates byte for byte the predecessor's.
- `Score`: a made-up score title (B208's FULL) surveyed, labelled — score_gates' fit and refs the predecessor's, none
  thrown away; train's page records made / thrown away by symbol.
- `Letters`: a made-up letters title (B191's) surveyed, labelled, planned, trained — the spec the predecessor's.

    python3 -m unittest discover -s tests/b224_template_validity -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import types
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests" / "b214_variants"), str(ROOT / "tests" / "b208_survey"),
                str(ROOT / "tests" / "b178_score_kind"), str(ROOT / "tests" / "b191_letters")]
import test_b214 as b214  # noqa: E402  (its made-up picture)
import test_b208 as b208  # noqa: E402  (B178's harness with survey, and FULL)

PREDECESSOR = "c7750afc"
PREDECESSOR_SHA = "58ca125956fe92f97e9c5dbe6d7f8feba97a5029749cd87df5734da874881bb5"


def predecessor_steps():
    """The predecessor's party_steps, from git (no file written); its own functions call each other."""
    import hashlib
    src = subprocess.run(["git", "-C", str(ROOT), "show", f"{PREDECESSOR}:tools/party_steps.py"], capture_output=True,
                         check=True).stdout
    assert hashlib.sha256(src).hexdigest() == PREDECESSOR_SHA
    mod = types.ModuleType("party_steps_predecessor")
    mod.__file__ = str(ROOT / "tools" / "party_steps.py")
    exec(compile(src, "party_steps_predecessor", "exec"), mod.__dict__)
    return mod


class Stream(unittest.TestCase):
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
        self.lined[293, 111:119] = 235.0                  # B221's line: joins the 4's crossbar on a right shift

    def joined_cells(self, bg, seed: int, n: int) -> list:
        """Replays the stream's first n draws by hand: the cells of the draws cut as one glyph wider than the 4."""
        E, st = self.es, self.st
        t, l, b, r = self.g[0], self.g[1], self.g[2], self.g[3]
        ink = E._ink(self.a, self.place["pol"], int(self.place["r"]), E._contrast(self.a))[t:b + 1, l:r + 1]
        rng = np.random.default_rng(seed)
        out = []
        for _ in range(n):
            rng.integers(1)
            dx, dy = int(rng.integers(-st.SYN_DX, st.SYN_DX + 1)), int(rng.integers(-st.SYN_DY, st.SYN_DY + 1))
            pic = bg.copy()
            cx = (self.region[0] + self.region[2]) // 2 - (r - l + 1) // 2 + dx
            pic[t + dy:t + dy + b - t + 1, cx:cx + r - l + 1][ink] = self.a[t:b + 1, l:r + 1][ink]
            gl = E.place_glyphs(pic, self.place)
            if gl and len(gl) == 1 and (gl[0][3] - gl[0][1] + 1) - (r - l + 1) > st.VARIANT_SIZE_TOL:
                out.append(E.glyph_cell(pic, gl[0], self.place))
        return out

    def test_1_a_joined_wider_cut_is_thrown_away_and_redrawn(self):
        log: dict = {}
        cells = self.st.synthetic_glyphs([(self.a, self.g)], [self.lined], self.place, self.region,
                                         np.random.default_rng(224), self.st.SYN_PER_GLYPH, log=log)[0]
        self.assertEqual(len(cells), self.st.SYN_PER_GLYPH)
        self.assertGreater(log["thrown away"], 0, log)
        self.assertEqual(set(log["why"]), {"not its own size"}, log)
        self.assertEqual(log["draws"], self.st.SYN_PER_GLYPH + log["thrown away"])
        joined = self.joined_cells(self.lined, 224, log["draws"])
        self.assertEqual(len(joined), log["thrown away"])
        for c in cells:                                    # never a template
            self.assertFalse(any(np.array_equal(c, j) for j in joined))

    def test_2_fewer_than_eight_valid_is_recorded_not_an_error(self):
        bad = self.st.erase(b214.picture(None, blob=True), self.place, self.region)  # every paste cuts as two
        bad[276:304, 116:122] = 235.0                     # B214's bar, drawn back after the erase
        log: dict = {}
        cells = self.st.synthetic_glyphs([(self.a, self.g)], [bad], self.place, self.region,
                                         np.random.default_rng(224), self.st.SYN_PER_GLYPH, log=log)[0]
        self.assertEqual(cells, [])
        self.assertEqual((log["made"], log["draws"], log["thrown away"]), (0, self.st.VARIANT_DRAWS,
                                                                            self.st.VARIANT_DRAWS))
        self.assertEqual(log[f"glyphs short of {self.st.SYN_PER_GLYPH}"], 1)

    def test_3_none_thrown_away_is_the_predecessors_byte_for_byte(self):
        old = predecessor_steps()
        log: dict = {}
        mine = self.st.synthetic_glyphs([(self.a, self.g)], [self.good], self.place, self.region,
                                        np.random.default_rng(224), self.st.SYN_PER_GLYPH, log=log)[0]
        theirs = old.synthetic_glyphs([(self.a, self.g)], [self.good], self.place, self.region,
                                      np.random.default_rng(224), old.SYN_PER_GLYPH)[0]
        self.assertEqual(log["thrown away"], 0)
        self.assertEqual(len(mine), len(theirs))
        for x, y in zip(mine, theirs):
            self.assertEqual(np.asarray(x).tobytes(), np.asarray(y).tobytes())

    def test_4_the_test_variants_unchanged(self):
        old = predecessor_steps()
        for bg in (self.good, self.lined):
            v1, d1 = self.st.test_variants(self.a, self.g, [bg], self.place, self.region, np.random.default_rng(5))
            v2, d2 = old.test_variants(self.a, self.g, [bg], self.place, self.region, np.random.default_rng(5))
            self.assertEqual((d1, len(v1)), (d2, len(v2)))
            for x, y in zip(v1, v2):
                self.assertEqual(np.asarray(x).tobytes(), np.asarray(y).tobytes())


class Score(b208.Made):
    def test_1_a_title_with_nothing_thrown_away_is_the_predecessors(self):
        import party_steps as st
        old = predecessor_steps()
        self.put("T71", b208.FULL)
        self.surveyed("T71")
        self.labelled("T71", b208.FULL)
        b, kept = self.pag.load_binding("T71"), self.pag.kept_states("T71")
        mine = st.score_gates("T71", b, kept, self.pag.Cells())
        theirs = old.score_gates("T71", b, kept, self.pag.Cells())
        self.assertEqual(mine["synthetic"]["thrown away"], 0, mine["synthetic"])
        keys = ("keys", "thresholds", "separable", "margin_needed")
        self.assertEqual(json.dumps({k: mine["full"][k] for k in keys}, sort_keys=True),
                         json.dumps({k: theirs["full"][k] for k in keys}, sort_keys=True))
        self.assertEqual(np.asarray(mine["refs"]).tobytes(), np.asarray(theirs["refs"]).tobytes())
        self.assertEqual(mine["synthetic"]["made"], theirs["synthetic"]["made"])

    def test_2_trains_page_records_made_and_thrown_away_by_symbol(self):
        self.put("T72", b208.FULL)
        self.surveyed("T72")
        self.labelled("T72", b208.FULL)
        self.assertEqual(self.tool("plan", "T72")[0], 0)
        rc, out = self.tool("train", "T72")
        v = self.verdict("T72", "train")
        self.assertEqual(v["verdict"], "PASS", v["bad"])
        syn = v["recorded"]["synthetic"]
        self.assertEqual(sorted(syn["by symbol"]), ["0", "1", "2", "3", "4"])
        for sym, row in syn["by symbol"].items():
            self.assertEqual(set(row) >= {"made", "thrown away", "draws"}, True, row)
        self.assertEqual(syn["made"], sum(r["made"] for r in syn["by symbol"].values()))
        self.assertEqual(syn["not cut"], 0)                # B224: a template cell is never empty now


class Letters(unittest.TestCase):
    """B191's made-up letters title through survey, label, plan and train: the spec the predecessor's."""

    def test_1_the_letters_spec_is_the_predecessors(self):
        import test_b191 as b191
        case = b191.Tool("test_1_register_options")
        b191.Tool.setUpClass()
        try:
            case.setUp()
            pag = case.pag
            import party_steps as st
            old = predecessor_steps()
            case.put("T73", b191.TITLE)
            self.assertEqual(case.tool("survey", "T73")[0], 3)
            rc, out = case.tool("survey", "T73", "letters", "WOW", "60,80,155,118", "485,80,580,118")
            self.assertEqual(rc, 3, out)
            self.assertEqual(case.tool("survey", "T73", "ok")[0], 0)
            reads = [f"{r}={t},{t}" for r, t in sorted(b191.READ.items())]
            rc, out = case.tool("label", "T73", *reads)
            if rc == 1 and "look=all" in out:
                rc, out = case.tool("label", "T73", "look=all")
            self.assertEqual(rc, 0, out)
            self.assertEqual(case.tool("plan", "T73")[0], 0)
            b, kept = pag.load_binding("T73"), pag.kept_states("T73")
            rules = pag.rules_folder()
            game = b["game"]
            specs = []
            for mod in (old, st):
                rc = mod.cmd_train("T73", {})
                self.assertEqual(rc, 0, case.verdict("T73", "train")["bad"])
                spec_json = (rules / f"{game}.endscreen.json").read_bytes()
                spec, arrays = case.es.load_spec(rules / f"{game}.endscreen.json")
                specs.append((spec_json, {k: np.asarray(v).tobytes() for k, v in sorted(arrays.items())}))
                b = pag.load_binding("T73")
            self.assertEqual(specs[0][0], specs[1][0])
            self.assertEqual(specs[0][1], specs[1][1])
        finally:
            b191.Tool.tearDownClass()


if __name__ == "__main__":
    unittest.main()
