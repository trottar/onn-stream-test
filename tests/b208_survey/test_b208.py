#!/usr/bin/env python3
"""B208 / B209 (host): the front of the add-a-game path rebuilt — survey, label on the regions, plan, train. Made-up
score titles (B178's picture source, `score_capture.py`: each side's number centred in its panel); no title; temp
dirs removed (B178's harness).

- `Survey`: the boxes picture and its numbers; the kind checked against register's; box numbers -> regions (the box
  and a 6-px margin); `again P2` asks for P2 alone; `ok` -> PASS; a region of the session's (a rectangle) on an empty
  part of the screen gives no place; the place's window is the region.
- `Path`: survey -> label -> plan -> train on four made-up end saves: plan's list and its last line; train PASS with
  the digits one save shows counted "seen once"; the sidecar carries the code; the spec's places are the regions;
  nothing searched for a place (the place finder and the old learner made to raise); learn refused for a surveyed
  title. A digit no save shows: plan's last line asks for it, and train does not learn it.
- `Gates`: rigidity, the once rule's three conditions, the bar as set (B211), plan's symbols, the ask's words.

    python3 -m unittest discover -s tests/b208_survey -v
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests" / "b178_score_kind")]
for sub in ("b114_party_minigame_hang", "b124_party_four_seats", "b123_h7_n64_start", "b157_add_game",
            "b181_every_digit"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import test_b178 as b178  # noqa: E402  (its harness: temp home, evidence, rules; the made-up picture source)

B, O = {"kind": "begin"}, {"kind": "other"}
FULL = {"begin": B, "other": O, "end_P1": {"kind": "end", "s": [4, 1], "look": 1},
        "end_P1_2": {"kind": "end", "s": [3, 0], "look": 2}, "end_P2": {"kind": "end", "s": [1, 2], "look": 3},
        "end_P2_2": {"kind": "end", "s": [0, 4], "look": 4}}
NO_3 = {**FULL, "end_P1_2": {"kind": "end", "s": [4, 0], "look": 2}}


class Made(b178.Made):
    def put(self, code: str, saves: dict, top: int = 4) -> None:
        super().put(code, saves)
        bp = self.pag.binding_path(code)
        b = json.loads(bp.read_text())
        b["max_score"] = top
        b["register_inputs"] = self.pag.register_inputs(b, self.pag.kept_states(code))
        bp.write_text(json.dumps(b))
        self.pag.verdict_path(code, "register").write_text(json.dumps({"verdict": "PASS",
                                                                        "inputs": b["register_inputs"]}))

    def boxes_at(self, code: str) -> tuple[int, int]:
        bx = json.loads((self.pag.home(code) / "survey" / "boxes.json").read_text())["boxes"]
        def at(x, y):
            return next(i for i, q in enumerate(bx, 1) if q[0] <= x <= q[2] and q[1] <= y <= q[3])
        return at(100, 290), at(540, 290)

    def surveyed(self, code: str) -> None:
        """As a session answers when the box holding a number is its whole panel: a rectangle off the grid."""
        self.assertEqual(self.tool("survey", code)[0], 3)
        self.assertEqual(self.tool("survey", code, "score", "60,266,140,314", "500,266,580,314")[0], 3)
        self.assertEqual(self.tool("survey", code, "ok")[0], 0)

    def labelled(self, code: str, saves: dict) -> None:
        args = [f"{r}={'-'.join(map(str, st['s']))},{'-'.join(map(str, st['s']))}" for r, st in sorted(saves.items())
                if r.startswith("end_")]
        rc, out = self.tool("label", code, *args)
        self.assertEqual(rc, 1, out)                      # the last look not yet given
        self.assertIn("look=all", out)
        rc, out = self.tool("label", code, "look=all")
        self.assertEqual(rc, 0, out)


class Survey(Made):
    def test_1_the_answer_flow(self):
        self.put("T81", FULL)
        rc, out = self.tool("survey", "T81")
        self.assertEqual(rc, 3, out)
        self.assertTrue((self.pag.home("T81") / "survey" / "boxes.png").is_file())
        p1, p2 = self.boxes_at("T81")
        rc, out = self.tool("survey", "T81", "letters", "AB", p1, p2)
        self.assertEqual(rc, 2, out)                      # the kind is register's
        self.assertIn("REFUSED", out)
        self.assertEqual(self.tool("survey", "T81", "score", p1, p2)[0], 3)
        b = json.loads(self.pag.binding_path("T81").read_text())
        bx = json.loads((self.pag.home("T81") / "survey" / "boxes.json").read_text())["boxes"]
        self.assertEqual(b["survey"]["regions"][0], [bx[p1 - 1][0] - 6, bx[p1 - 1][1] - 6, bx[p1 - 1][2] + 6,
                                                     bx[p1 - 1][3] + 6])
        self.assertFalse(b["survey"]["confirmed"])
        rc, out = self.tool("survey", "T81", "again", "P2")
        self.assertEqual(rc, 3)
        self.assertIn("P2", out)
        self.assertEqual(self.tool("survey", "T81", "P2", p2)[0], 3)
        self.assertTrue((self.pag.home("T81") / "survey" / "regions.png").is_file())
        self.assertEqual(self.tool("survey", "T81", "ok")[0], 0)
        self.assertEqual(self.verdict("T81", "survey")["verdict"], "PASS")

    def test_3_after_register_holds_three_saves(self):
        """register (today's) FAILs with three saves (it names a second save of each ending); survey runs on them."""
        three = {k: FULL[k] for k in ("begin", "other", "end_P1")}
        self.put("T85", three)
        v = json.loads(self.pag.verdict_path("T85", "register").read_text())
        self.pag.verdict_path("T85", "register").write_text(json.dumps({**v, "verdict": "FAIL"}))
        self.assertEqual(self.tool("survey", "T85")[0], 3)
        self.put("T86", {k: FULL[k] for k in ("begin", "end_P1")})
        rc, out = self.tool("survey", "T86")
        self.assertEqual(rc, 2)
        self.assertIn("begin, other and one ending", out)

    def test_2_a_region_holds_only_what_is_in_it(self):
        import party_steps as st
        self.put("T82", FULL)
        b = self.pag.load_binding("T82")
        kept = self.pag.kept_states("T82")
        a = st.grey(st.final_pictures("T82", b, kept, "end_P1")[0])
        self.assertIsNone(st.region_place(a, [8, 440, 60, 470]))        # nothing there: no place (no search)
        pl = st.region_place(a, [60, 266, 140, 314])
        pad = int(round((pl["bot"] - pl["top"] + 1) * 20 / 24)) + 2
        self.assertEqual((pl["x0"] - pad, pl["x1"] + pad), (60, 140))   # its window is the region
        self.assertEqual(len(st.region_glyphs(a, pl)), 1)               # "4"
        self.assertEqual(len(st.region_glyphs(a, st.region_place(a, [500, 266, 580, 314]))), 1)


class Path_(Made):
    def test_1_the_whole_path(self):
        import h7_endscreen as es
        self.put("T83", FULL)
        self.surveyed("T83")
        self.labelled("T83", FULL)
        rc, out = self.tool("plan", "T83")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "Nothing more is needed.")
        rec = self.verdict("T83", "plan")["recorded"]
        self.assertEqual(rec["symbols"], {"0": "twice or more", "1": "twice or more",       # B215 (queue BQ): plan
                                          "2": "once (counted: seen once)",                  # runs train's gates
                                          "3": "once (counted: seen once)", "4": "twice or more"})
        saved = (es._find_place, es.learn_scores, es._find_columns)

        def no(*a, **k):
            raise AssertionError("a place was searched for")
        es._find_place = es.learn_scores = es._find_columns = no
        try:
            rc, out = self.tool("train", "T83")
        finally:
            es._find_place, es.learn_scores, es._find_columns = saved
        v = self.verdict("T83", "train")
        self.assertEqual(v["verdict"], "PASS", v["bad"])
        self.assertEqual(sorted(v["recorded"]["seen once"]), ["2", "3"])
        self.assertEqual(out.strip().splitlines()[-1], "Nothing more is needed.")
        b = self.pag.load_binding("T83")
        side = json.loads((self.pag.rules_folder() / f"{b['game']}.party.json").read_text())
        self.assertEqual(side, {"code": "T83", "players": 2, "result": "score"})
        spec, _arr = es.load_spec(self.pag.rules_folder() / f"{b['game']}.endscreen.json")
        self.assertEqual((spec["version"], spec["score"]["region_source"]), (4, "survey"))
        self.assertEqual(spec["score"]["regions"], b["survey"]["regions"])
        self.assertEqual(self.tool("learn", "T83")[0], 2)                # its learning is train

    def test_2_a_digit_no_save_shows_is_asked_and_not_learnt(self):
        self.put("T84", NO_3)
        self.surveyed("T84")
        self.labelled("T84", NO_3)
        rc, out = self.tool("plan", "T84")
        self.assertEqual(out.strip().splitlines()[-1], "Still needed: a final score with a 3 in it (either player).")
        rc, out = self.tool("train", "T84")
        v = self.verdict("T84", "train")
        self.assertEqual(v["verdict"], "FAIL")
        self.assertIn("gate 3: every symbol the result can show learnt (none never seen)", v["bad"])
        self.assertIn("3", v["cells"]["gate 3: every symbol the result can show learnt (none never seen)"])
        self.assertFalse((self.pag.rules_folder() / "madeupt84.party.json").exists())


class Gates(unittest.TestCase):
    def cells(self):
        import test_b204 as b204
        rng = np.random.default_rng(208)
        return {d: [b204.glyph(b204.FONT[d], 4, rng) for _ in range(3)] for d in "038"}

    def setUp(self):
        sys.path.insert(0, str(ROOT / "tests" / "b204_every_number"))
        import party_add_game as pag
        import party_steps as st
        self.pag, self.st = pag, st

    def test_1_rigidity(self):
        c = self.cells()
        r = self.st.rigidity("score", c, {k: 2 for k in c})
        self.assertGreater(r["rigidity"], 0.0)
        same = {k: [v[0]] * 2 for k, v in c.items()}
        self.assertEqual(self.st.rigidity("score", same, {k: 2 for k in c})["rigidity"], 1.0)
        self.assertIsNone(self.st.rigidity("score", c, {"0": 2, "3": 1, "8": 1})["rigidity"])

    def test_2_the_once_rule(self):
        st = self.st
        bar = self.pag.BARS["rigid_min"][0]
        read = {"a": "5", "b": "5", "x": "3"}.get
        eight = ["a", "b"] * 4                                          # B214 (queue BQ): eight valid variants
        ok, _ = st._once_rule("score", "5", {"rigidity": bar}, eight, [("3", "x")], read)
        self.assertTrue(ok)
        ok, _ = st._once_rule("score", "5", {"rigidity": bar - 0.0001}, eight, [("3", "x")], read)
        self.assertFalse(ok)                                             # not rigid
        ok, _ = st._once_rule("score", "5", {"rigidity": 0.9}, ["a"] * 7 + ["x"], [], read)
        self.assertFalse(ok)                                             # a variant not read as itself
        ok, _ = st._once_rule("score", "5", {"rigidity": 0.9}, eight, [("3", "b")], read)
        self.assertFalse(ok)                                             # another symbol's glyph read as it
        ok, _ = st._once_rule("score", "5", {"rigidity": 0.9}, [], [], read)
        self.assertFalse(ok)                                             # no variant: not counted

    def test_3_the_bar_as_set(self):
        v, src = self.pag.BARS["rigid_min"]
        self.assertEqual(v, 0.0995)
        self.assertIn("T90 0.5693", src)
        self.assertIn("T91 0.1990", src)

    def test_4_plan_symbols_and_ask(self):
        st = self.st
        b = {"survey": {"kind": "score"}, "max_score": 5}
        self.assertEqual(st.plan_symbols(b, {"end_P2": "05-06"}), list("0123456"))
        self.assertEqual(st.plan_symbols({"survey": {"kind": "score"}}, {"end_P1": "3-1"}), list("0123456789"))
        self.assertEqual(st.plan_symbols({"survey": {"kind": "letters"}, "word": "WOW"}, {"e": "---/WOW"}),
                         ["O", "W", "-"])
        self.assertEqual(st.ask_line("score", []), "Nothing more is needed.")
        self.assertEqual(st.ask_line("score", ["1"]), "Still needed: a final score with a 1 in it (either player).")
        self.assertEqual(st.shown_counts("score", {"a": "05-04", "b": "02-00"}, list("0245")),
                         {"0": 2, "2": 1, "4": 1, "5": 1})


if __name__ == "__main__":
    unittest.main()
