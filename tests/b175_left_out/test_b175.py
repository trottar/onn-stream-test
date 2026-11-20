#!/usr/bin/env python3
"""B175 + B176 (host): a cell for a match the spec did not learn from; two plain hints — the add-a-game tool's learn on
made-up titles (B171's near-alike screens, `tests/b171_more_saves/near_capture.py`), nothing of the hub's read.

Each row of the record's table, through learn (the kept saves written as register writes them, register's PASS beside
them, as rehearse's scratch does; one row through rehearse):
- **the weak pass** (one save per ending, other characters in each): today's cells all met, **the left-out cells not
  met** ("its ending's only match"), the line names the next save;
- **two per ending, other characters in every match:** a left-out save ends as the other ending → the line asks that
  ending a third save (no accusation: two saves cannot tell a wrong role from a thin ending); asked saves → PASS;
- **near-alike, two per ending** → asks; **three per ending** → PASS; **far apart on two** → PASS;
- **the same characters within an ending** (only the cursor moved) → "look like the same match saved twice";
- **a save in the wrong role:** with two per ending → a save is asked; with three → "A save may be in the wrong role",
  nothing asked;
- **only the margin cell fails** (a large mark the begin alone shows) → FAIL on `margin_needed` alone;
- the spec written to the rules folder is the one learnt from every save; rehearse carries the cell; nothing named;
  no bar changed. Temp dirs removed.

    python3 -m unittest discover -s tests/b175_left_out -v
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "b171_more_saves"))
sys.path.insert(0, str(ROOT / "tools"))
import near_capture as nc  # noqa: E402
import test_b171 as b171  # noqa: E402  (its made-up hub, its fixture, its rehearse title)

_tool = b171._tool


def st(kind, look=0, far=False, cur=None, mark=0):
    d = {"kind": kind, "look": look, "far": far, "mark": mark}
    if cur is not None:
        d["cur"] = cur
    return d


B, O = st("start"), st("other")


class Rows(b171.Base):
    def put(self, code: str, saves: dict) -> None:
        """The kept saves as register keeps them, and register's PASS for them (as rehearse's scratch writes it)."""
        pag = self.pag
        kf = self.tmp / "home" / code / "kept"
        kf.mkdir(parents=True, exist_ok=True)
        for role, s in saves.items():
            self.n += 1
            (kf / f"{role}.state").write_text(json.dumps({**s, "n": self.n}))
        b = {"code": code, "game": f"madeupnear{code.lower()}", "players": 2, "system": "ps1", "result": "winner",
             "cheat": None, "relative_path": "", "title": "", "content": ""}
        bp = self.tmp / "home" / code / "binding.json"
        if bp.is_file():
            b = json.loads(bp.read_text())
        b["register_inputs"] = pag.register_inputs(b, pag.kept_states(code))
        bp.write_text(json.dumps(b, indent=1, sort_keys=True) + "\n")
        ev = self.tmp / "ev" / code
        ev.mkdir(parents=True, exist_ok=True)
        (ev / "register.json").write_text(json.dumps({"verdict": "PASS", "inputs": b["register_inputs"]}) + "\n")

    def learn(self, code: str):
        rc, out = _tool("learn", code)
        v, c, page = self.verdict("learn", code)
        return rc, v, c, page, out

    def follow(self, code: str, looks, kinds=None, most: int = 6) -> tuple[list, int]:
        """learn; while its line names a save: that save (another look), learn again — the same bars."""
        asked, looks = [], iter(looks)
        rc, v, c, page, out = self.learn(code)
        while rc != 0 and len(asked) < most:
            role = (v.get("recorded") or {}).get("one more save")
            if not role:
                break
            asked.append(role)
            ending = self.pag._role_class(role)
            self.put(code, {role: st((kinds or {}).get(ending, ending), next(looks))})
            rc, v, c, page, out = self.learn(code)
        return asked, rc

    def bad(self, c: dict) -> list:
        return [k for k, x in c.items() if not x["met"]]

    # --- the rows --------------------------------------------------------------------------------------------------
    def test_1_the_weak_pass_now_not_met(self):
        self.put("T71", {"begin": B, "other": O, "end_P1": st("end_P1", 1), "end_P2": st("end_P2", 2)})
        rc, v, c, page, out = self.learn("T71")
        self.assertEqual(rc, 1, out)
        self.assertEqual(self.bad(c), ["left out: end_P1", "left out: end_P2"])     # every cell of today's met
        self.assertEqual(c["left out: end_P1"]["read"], "its ending's only match")
        self.assertEqual(c["left out: end_P1"]["bar"], "end_P1 within <= 2.0 s, never another")
        self.assertEqual(v["recorded"]["one more save"], "end_P1_2")
        self.assertIn("One more save: end_P1_2 — the screen after a match player 1 won", page)
        self.assertFalse(list((self.tmp / "rules").glob("*.endscreen.json")))   # only a pass reaches the rules

    def test_2_two_per_ending_other_characters_asks_a_third(self):
        self.put("T72", {"begin": B, "other": O, "end_P1": st("end_P1", 1), "end_P1_2": st("end_P1", 2),
                         "end_P2": st("end_P2", 3), "end_P2_2": st("end_P2", 4)})
        rc, v, c, page, out = self.learn("T72")
        self.assertEqual(rc, 1, out)
        self.assertFalse(c["left out: end_P2"]["met"])               # read as the other ending
        self.assertNotIn("wrong role", v["recorded"])                             # two saves: no accusation
        self.assertNotIn("A save may be in the wrong role", page)
        self.assertEqual(v["recorded"]["one more save"], ASKED["T72"][0])
        asked, rc = self.follow("T72", looks=[5, 6, 7, 8])
        self.assertEqual(rc, 0)
        self.assertEqual(asked, ASKED["T72"])

    def test_3_near_alike_two_asks_three_pass(self):
        """Near-alike, two per ending, P2's first match with P1's characters: asked to the cap; three per ending with
        other characters in each: PASS."""
        self.put("T73", {"begin": B, "other": O, "end_P1": st("end_P1", 1), "end_P1_2": st("end_P1", 2),
                         "end_P2": st("end_P2", 1), "end_P2_2": st("end_P2", 3)})
        asked, rc = self.follow("T73", looks=[5, 6, 7, 8])
        v, c, page = self.verdict("learn", "T73")
        self.assertEqual(asked, ASKED["T73"])
        self.assertEqual(rc, 1)                       # end_P2 shares end_P1's characters: left out, not read as its own
        self.assertEqual(v["recorded"]["cannot be told apart"], ["end_P2"])     # the cap, as today
        self.assertFalse(c["left out: end_P2"]["met"])
        self.put("T74", {"begin": B, "other": O, "end_P1": st("end_P1", 1), "end_P1_2": st("end_P1", 2),
                         "end_P1_3": st("end_P1", 4), "end_P2": st("end_P2", 1), "end_P2_2": st("end_P2", 3),
                         "end_P2_3": st("end_P2", 5)})
        rc, v, c, page, out = self.learn("T74")
        self.assertEqual(rc, 0, out + page)
        for r in ("end_P1", "end_P1_2", "end_P1_3", "end_P2", "end_P2_2", "end_P2_3"):
            self.assertEqual(c[f"left out: {r}"]["read"], [self.pag._role_class(r), 2.0])
        # the spec written is the one learnt from every save
        es = self.pag._endscreen()
        pics = self.tmp / "home/T74/pictures"
        spec, _arr, _rep = es.learn(pics, pics / "labels.json", "first", name="madeupneart74")
        written = json.loads((self.tmp / "rules/madeupneart74.endscreen.json").read_text())
        self.assertEqual(written["frames"], spec["frames"])
        self.assertEqual(written["margin_needed"], spec["margin_needed"])
        self.assertEqual(written["outcome_mask_px"], spec["outcome_mask_px"])

    def test_4_far_apart_two(self):
        self.put("T75", {"begin": B, "other": O, "end_P1": st("end_P1", 1, True), "end_P1_2": st("end_P1", 2, True),
                         "end_P2": st("end_P2", 3, True), "end_P2_2": st("end_P2", 4, True)})
        rc, v, c, page, out = self.learn("T75")
        self.assertEqual(rc, 0, out + page)

    def test_5_the_same_match_twice(self):
        """The same characters within an ending, only the cursor moved: leave-one-out alone would pass it."""
        self.put("T76", {"begin": B, "other": O, "end_P1": st("end_P1", 1, cur=0), "end_P1_2": st("end_P1", 1, cur=3),
                         "end_P2": st("end_P2", 2, cur=0), "end_P2_2": st("end_P2", 2, cur=3)})
        rc, v, c, page, out = self.learn("T76")
        self.assertEqual(rc, 1, out)
        pairs = c["no two saves of one ending the same picture"]["read"]
        self.assertEqual([p[:2] for p in pairs], [["end_P1", "end_P1_2"], ["end_P2", "end_P2_2"]])
        self.assertTrue(all(p[2] < 1.0 for p in pairs))
        self.assertEqual(c["left out: end_P1"]["read"], "its ending's only match")   # the pair counts as one
        line = "end_P1 and end_P1_2 look like the same match saved twice: save end_P1_2 again from another match."
        self.assertEqual(v["recorded"], {"same match twice": ["end_P1", "end_P1_2"], "line": line})
        self.assertIn(line, page)
        self.assertIn(line, out)
        self.put("T76", {"end_P1_2": st("end_P1", 3)})                     # saved again from another match
        rc, v, c, page, out = self.learn("T76")
        self.assertEqual(v["recorded"]["same match twice"], ["end_P2", "end_P2_2"])

    def test_6_a_save_in_the_wrong_role(self):
        """Two per ending, end_P2_2 holds a P1 win: two saves cannot tell it from a thin ending — saves are asked (the user
        gives each from another match, the right winner); once its ending has two other matches, the save in the wrong
        role is named and nothing more is asked."""
        self.put("T77", {"begin": B, "other": O, "end_P1": st("end_P1", 1), "end_P1_2": st("end_P1", 2),
                         "end_P2": st("end_P2", 3), "end_P2_2": st("end_P1", 4)})
        rc, v, c, page, out = self.learn("T77")
        self.assertEqual(rc, 1, out)
        self.assertNotIn("wrong role", v["recorded"])
        asked, looks = [], iter([5, 6, 7, 8])
        while (v.get("recorded") or {}).get("one more save") and len(asked) < 4:
            role = v["recorded"]["one more save"]
            asked.append(role)
            self.put("T77", {role: st(self.pag._role_class(role), next(looks))})
            rc, v, c, page, out = self.learn("T77")
        self.assertEqual(asked, ASKED["T77"])
        self.assertEqual(rc, 1, out)
        line = ("A save may be in the wrong role: end_P2_2 reads as end_P1. Check which player won that match; collect "
                "it again under the right role.")
        self.assertEqual(v["recorded"], {"wrong role": ["end_P2_2", "end_P1"], "line": line})
        self.assertIn(line, page)
        self.assertNotIn("One more save", page + out)

    def test_7_only_the_margin_fails(self):
        """A large mark the begin alone shows: the endings' tally a small share of the outcome mask — separable, nothing
        unknown, every replay and every left-out save its own, and the margin under its bar."""
        m = 16
        self.put("T78", {"begin": st("start", mark=m), "other": O,
                         **{r: st(self.pag._role_class(r), look, mark=m) for r, look in
                            (("end_P1", 1), ("end_P1_2", 2), ("end_P1_3", 4), ("end_P2", 1), ("end_P2_2", 3),
                             ("end_P2_3", 5))}})
        rc, v, c, page, out = self.learn("T78")
        self.assertEqual(rc, 1, out)
        self.assertEqual(self.bad(c), ["margin_needed"])
        self.assertLess(c["margin_needed"]["read"], 0.0796)

    def test_8_through_register(self):
        """A new title through register and learn (the made-up hub, the user's made-up slots): asks a third."""
        self.two_per_ending(1, 1)
        rc, out = _tool("learn", "T80")
        v, c, page = self.verdict("learn")
        self.assertEqual(rc, 1, out)
        self.assertTrue(any(k.startswith("left out: ") for k in c))
        self.names_absent(self.written() + out)


class RehearseCarries(b171.Rehearse):
    """rehearse runs learn's whole path in its scratch: the left-out cells come with it."""

    test_t88_shape_asks_then_passes = None
    test_a_kept_extra_that_is_an_end_screen_is_a_source = None

    def test_rehearse_carries_the_cell(self):
        self.save(2, "other")
        rc, out = _tool("rehearse", "T85", "--collect", "other=2")
        v, c, page = self.verdict("rehearse", "T85")
        self.assertEqual(rc, 1, out)
        self.assertEqual(c["learn: left out: end_P1"]["read"], "its ending's only match")
        self.assertEqual(v["recorded"]["one more save"], "end_P1_2")
        self.assertIn("then rehearse T85 --collect end_P1_2=<slot>.", page)
        self.assertTrue(c["the real rules folder: every file's sha256 before = after"]["met"])


ASKED = {"T72": ["end_P1_3", "end_P2_3", "end_P2_4"], "T73": ["end_P1_3", "end_P2_3", "end_P2_4"],
         "T77": ["end_P1_3", "end_P2_3", "end_P2_4"]}      # as the first run gave them (the learner decides)


if __name__ == "__main__":
    unittest.main()
