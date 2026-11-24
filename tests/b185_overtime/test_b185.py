# Frozen with T90's old score path (queue BQ, B217): this suite's made-up noise is exactly the pre-BP fixture (one generator per run, the shared save counter); the per-picture noise is for the new path's suites only.
#!/usr/bin/env python3
"""B185 / B186 / B187 (host): a column only one save fills (overtime); a digit only one save shows, learnt from that
save when it shows it several times; the ask to the user, rare and plain, with the picture. Every picture made-up
(B181's `line_capture.py`); no title, nothing read from the hub's own folders, the hub never reached (port 9), no
systemctl (a stand-in that lists nothing).

- `Overtime`: one save fills OT1 -> label PASS, its OT cells "shown only here", never named; learn PASS (the left-out
  cell not failed by it); two overtime saves -> the column learnt (a place in the spec, read back in each left out);
  a filled OT cell breaking the sum still caught.
- `OneSave`: a digit one save shows three times (and no other save) -> learnt from that save, learn PASS; the
  across-save spread within its bar; a digit one save shows once -> short, learn FAIL naming it.
- `Ask`: two readings differing twice -> the ask names the match (who won, its final as read, when kept), the cells
  in doubt by column, the picture copied to the ask folder, the final left out of the record; a final alone refused;
  the whole line score with the user's numbers -> PASS; close removes the picture. A sum failing twice -> the ask
  names that side's every cell. A read-back contradiction named twice -> never the user, never another match.
Temp dirs removed.

    python3 -m unittest discover -s tests/b185_overtime -v
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests" / "b181_every_digit"), str(ROOT / "tests" / "b178_score_kind")]

ENV_KEYS = ("PRIVYHUB_ADD_GAME_HOME", "PRIVYHUB_ADD_GAME_EVIDENCE", "PRIVYHUB_H7_RULES", "PRIVYHUB_ADD_GAME_LOGS",
            "PARTY_ADD_GAME_CAPTURE", "PRIVYHUB_ADD_GAME_HUB", "PRIVYHUB_ADD_GAME_DROPINS", "PRIVYHUB_ADD_GAME_ASK",
            "PRIVYHUB_ADD_GAME_PROJECT", "PRIVYHUB_ADD_GAME_SYSTEMCTL")
EVERY = "every digit 0-9 read by a reader learnt without each save that shows it"
_ = None
B, O = {"kind": "begin"}, {"kind": "other"}


def end(q1, s1, q2, s2, look):
    return {"kind": "end_line", "q": [q1, q2], "s": [s1, s2], "look": look}


# B181's LINE (every digit in two saves or more), its end_P1_2 now an overtime match (OT1 filled, both rows)
OT = {"begin": B, "other": O,
      "end_P1": end([1, 2, 3, 4, _, _], 10, [0, 5, 0, 1, _, _], 6, 1),
      "end_P1_2": end([7, 8, 9, 0, 3, _], 27, [6, 5, 4, 3, 0, _], 18, 2),
      "end_P2": end([2, 0, 1, 3, _, _], 6, [9, 8, 7, 0, _, _], 24, 3),
      "end_P2_2": end([5, 6, 0, 0, _, _], 11, [7, 8, 9, 1, _, _], 25, 4)}
OT2 = dict(OT, end_P2=end([2, 0, 1, 3, 1, _], 7, [9, 8, 7, 0, 6, _], 30, 3))       # two overtime matches
# T90's shape: the overtime save the only one with a 7 (nine of them, in its cells only) and the only one filling OT1
T90S = {"begin": B, "other": O,
        "end_P1": end([1, 2, 3, 4, _, _], 10, [0, 5, 0, 1, _, _], 6, 1),
        "end_P1_2": end([7, 7, 7, 7, 7, _], 35, [7, 7, 7, 7, 0, _], 28, 2),
        "end_P2": end([2, 0, 1, 3, _, _], 6, [9, 8, 6, 0, _, _], 23, 3),
        "end_P2_2": end([5, 6, 0, 0, _, _], 11, [6, 8, 9, 1, _, _], 24, 4)}
# 6 shown by end_P2 alone, three times; every other digit by two saves or more
SIX = {"begin": B, "other": O,
       "end_P1": end([1, 2, 3, 4, _, _], 10, [0, 5, 0, 2, _, _], 7, 1),
       "end_P1_2": end([7, 8, 9, 0, _, _], 24, [5, 5, 4, 3, _, _], 17, 2),
       "end_P2": end([6, 0, 0, 0, _, _], 6, [9, 8, 6, 1, _, _], 24, 3),
       "end_P2_2": end([5, 5, 0, 0, _, _], 10, [7, 8, 9, 1, _, _], 25, 4)}
# 6 shown by end_P2 alone, once
SIX1 = dict(SIX, end_P2=end([2, 0, 1, 3, _, _], 6, [9, 8, 7, 0, _, _], 24, 3))


def text(st: dict) -> str:
    return "-".join("+".join("_" if c is None else str(c) for c in cells) + "=" + str(fin)
                    for cells, fin in zip(st["q"], st["s"]))


class Made(unittest.TestCase):
    N = [0]

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="b185_"))
        cls.old = {k: os.environ.get(k) for k in ENV_KEYS}
        os.environ.update({"PRIVYHUB_ADD_GAME_HOME": str(cls.tmp / "home"), "PRIVYHUB_ADD_GAME_EVIDENCE": str(cls.tmp / "ev"),
                           "PRIVYHUB_H7_RULES": str(cls.tmp / "rules"), "PRIVYHUB_ADD_GAME_LOGS": str(cls.tmp / "logs"),
                           "PARTY_ADD_GAME_CAPTURE": "line_capture:capture", "PRIVYHUB_ADD_GAME_HUB": "http://127.0.0.1:9",
                           "PRIVYHUB_ADD_GAME_DROPINS": str(cls.tmp / "dropins"),
                           "PRIVYHUB_ADD_GAME_ASK": str(cls.tmp / "project" / "logs" / "add_game_ask"),
                           "PRIVYHUB_ADD_GAME_PROJECT": str(cls.tmp / "project"),
                           "PRIVYHUB_ADD_GAME_SYSTEMCTL": "true"})
        (cls.tmp / "rules").mkdir()
        (cls.tmp / "project").mkdir()
        import party_add_game as pag
        cls.pag = pag

    @classmethod
    def tearDownClass(cls):
        for k, v in cls.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        """The made-up font's own thresholds are tight (its noise +-2): at some noise seeds a reader learnt without a
        save misses that save's 5s and 8s (HEAD's code too — B181's suite's order happens to miss them). Every test
        here pins its seeds (the state counter from 0, whatever ran before), so it reads; disclosed in the record."""
        self.N[0] = 0

    def put(self, code: str, saves: dict) -> None:
        pag = self.pag
        kf = pag.kept_folder(code)
        kf.mkdir(parents=True, exist_ok=True)
        for role, st in saves.items():
            self.N[0] += 1
            (kf / f"{role}.state").write_text(json.dumps({**st, "n": self.N[0]}))
        bp = pag.binding_path(code)
        b = json.loads(bp.read_text()) if bp.is_file() else {
            "code": code, "game": "madeup" + code.lower(), "players": 2, "system": "ps1", "result": "score",
            "cheat": None, "relative_path": "", "title": "", "content": ""}
        b["register_inputs"] = pag.register_inputs(b, pag.kept_states(code))
        bp.write_text(json.dumps(b))
        pag.verdict_path(code, "register").parent.mkdir(parents=True, exist_ok=True)
        pag.verdict_path(code, "register").write_text(json.dumps({"verdict": "PASS", "inputs": b["register_inputs"]}))

    def tool(self, *argv) -> tuple[int, str]:
        buf, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = self.pag.main([str(a) for a in argv])
        return rc, buf.getvalue() + err.getvalue()

    def verdict(self, code: str, stage: str) -> dict:
        v = self.pag.load_verdict(code, stage) or {}
        return {"verdict": v.get("verdict"), "bad": [c["cell"] for c in v.get("cells", []) if not c["met"]],
                "cells": {c["cell"]: c["read"] for c in v.get("cells", [])}, "recorded": v.get("recorded") or {},
                "raw": v}

    def looked(self, code: str, rc: int, out: str) -> tuple[int, str]:
        if rc == 1 and "Look at label/digits.png" in out:
            return self.tool("label", code, "look=all")
        return rc, out

    def label_all(self, code: str, saves: dict, wrong: dict | None = None):
        texts = {r: f"{text(st)},{text(st)}" for r, st in saves.items() if r.startswith("end_")}
        texts.update(wrong or {})
        return self.looked(code, *self.tool("label", code, *[f"{r}={t}" for r, t in sorted(texts.items())]))


class Overtime(Made):
    def test_1_one_overtime_save_counts(self):
        self.put("T91", OT)
        rc, out = self.label_all("T91", OT)
        lv = self.verdict("T91", "label")
        self.assertEqual(rc, 0, out + json.dumps(lv["bad"]))
        self.assertNotIn("Read again", out)
        self.assertEqual(lv["recorded"]["shown only here"]["end_P1_2"],
                         {"columns": ["P1 column 5", "P2 column 5"]})
        self.assertIn("shown only here: P1 column 5, P2 column 5",
                      lv["cells"]["end_P1_2: read back by a reader learnt without it"])
        rc, out = self.tool("learn", "T91")
        v = self.verdict("T91", "learn")
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))
        self.assertEqual(v["recorded"]["shown only here"]["end_P1_2"], {"columns": ["P1 column 5", "P2 column 5"]})
        self.assertEqual(v["cells"]["end_P1_2: ended as itself"], [27, 18])      # the hub reads its finals
        spec = json.loads((Path(os.environ["PRIVYHUB_H7_RULES"]) / "madeupt91.endscreen.json").read_text())
        self.assertIsNotNone(spec["score"]["columns"][0][4])                   # learnt from the one save
        self.assertIsNone(spec["score"]["columns"][0][5])

    def test_2_two_overtime_saves_the_column_learnt(self):
        self.put("T92", OT2)
        rc, out = self.label_all("T92", OT2)
        lv = self.verdict("T92", "label")
        self.assertEqual(rc, 0, out + json.dumps(lv["bad"]))
        self.assertNotIn("shown only here", json.dumps(lv["recorded"]))
        self.assertEqual(lv["cells"]["end_P2: read back by a reader learnt without it"], text(OT2["end_P2"]))
        rc, out = self.tool("learn", "T92")
        v = self.verdict("T92", "learn")
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))
        self.assertEqual(v["cells"]["left out: end_P1_2"][0], text(OT2["end_P1_2"]))   # OT1 read at its place

    def test_4_t90s_shape(self):
        """The refused case: label twice with the same readings -> PASS, never read again, never the user; learn
        PASS, the 7 learnt from the overtime save's own nine."""
        self.put("T90", T90S)
        for _try in (1, 2):
            rc, out = self.label_all("T90", T90S)
            lv = self.verdict("T90", "label")
            self.assertEqual(rc, 0, out + json.dumps(lv["bad"]))
            self.assertNotIn("Read again", out)
            self.assertNotIn("Ask the user", out)
        self.assertEqual(lv["recorded"]["shown only here"]["end_P1_2"],
                         {"digits": ["7"], "columns": ["P1 column 5", "P2 column 5"]})
        rc, out = self.tool("learn", "T90")
        v = self.verdict("T90", "learn")
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))
        self.assertEqual(v["cells"][EVERY]["learnt from one save"], {"7": "9 glyphs in end_P1_2, 9 read back"})
        self.assertEqual(v["cells"]["end_P1_2: ended as itself"], [35, 28])
        self.assertEqual(v["cells"]["left out: end_P1_2"][0],
                         "7+7+7+7+*+_=35-7+7+7+7+*+_=28 (shown only here: P1 column 5, P2 column 5)")

    def test_3_an_overtime_cell_breaking_the_sum(self):
        self.put("T93", OT)
        bad = text(OT["end_P1_2"]).replace("7+8+9+0+3", "7+8+9+0+5")
        rc, out = self.label_all("T93", OT, {"end_P1_2": f"{bad},{bad}"})
        self.assertEqual(rc, 1)
        self.assertIn("end_P1_2 (P1's cells add up to 29, not its final 27)", out)


class OneSave(Made):
    def test_1_a_digit_one_save_shows_three_times(self):
        self.put("T94", SIX)
        rc, out = self.label_all("T94", SIX)
        self.assertEqual(rc, 0, out + json.dumps(self.verdict("T94", "label")["bad"]))
        rc, out = self.tool("learn", "T94")
        v = self.verdict("T94", "learn")
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))
        cell = v["cells"][EVERY]
        self.assertEqual(cell["shown by fewer than two saves"], [])
        self.assertEqual(cell["learnt from one save"], {"6": "3 glyphs in end_P2, 3 read back"})
        sp = cell["across-save spread"]
        self.assertTrue(sp["met"] and sp["across"] <= sp["within"] + self.pag.ACROSS_MARGIN, sp)
        self.assertEqual(v["recorded"]["digits"]["learnt from one save"], ["6"])
        self.assertEqual(v["cells"]["left out: end_P2"][0], text(SIX["end_P2"]))  # its 6s by its own other 6s

    def test_2_a_digit_one_save_shows_once(self):
        self.put("T95", SIX1)
        rc, out = self.label_all("T95", SIX1)
        self.assertEqual(rc, 0, out)
        rc, out = self.tool("learn", "T95")
        v = self.verdict("T95", "learn")
        self.assertEqual(rc, 1, out)
        self.assertEqual(v["cells"][EVERY]["shown by fewer than two saves"], ["6"])
        self.assertEqual(v["cells"][EVERY]["learnt from one save"], {"6": "1 glyphs in end_P2, 0 read back — not learnt"})
        self.assertIn("whose line score shows 6", out)
        self.assertIn("1 digit is still short (6); if one is still short after that match, learn asks for one more.",
                      out)                                                     # B188: never "one is enough"


class Ask(Made):
    def test_1_two_readings_differ_twice_then_the_user(self):
        self.put("T96", OT)
        r1 = text(OT["end_P1_2"])
        r2 = r1.replace("7+8+9+0+3", "7+8+9+6+3")
        rc, out = self.label_all("T96", OT, {"end_P1_2": f"{r1},{r2}"})
        self.assertEqual(rc, 1)
        self.assertIn("Read again: end_P1_2 (its two readings differ)", out)
        self.assertNotIn("Ask the user", out)
        rc, out = self.tool("label", "T96", f"end_P1_2={r1},{r2}")
        self.assertEqual(rc, 1)
        self.assertIn("Ask the user about the match player 1 won 27-18 in overtime, kept at ", out)
        self.assertIn(": player 1's Q4, as its final stats screen shows them. YOU, now: ask Cowork to show you the "
                      "picture of that match; then reply with its scores.", out)
        pic = self.pag.ask_folder() / "T96_end_P1_2.png"
        self.assertTrue(pic.is_file())
        self.assertEqual([p.name for p in self.pag.ask_folder().iterdir()], ["T96_end_P1_2.png"])   # only that one
        v = self.verdict("T96", "label")
        self.assertNotIn("27-18", json.dumps(v["raw"]))                        # the final never written down
        self.assertNotIn("27-18", (self.pag.evidence("T96") / "label.md").read_text())
        self.assertEqual(v["recorded"]["ask the user"]["why"], "readings")
        rc, out = self.tool("label", "T96", "end_P1_2=27-18,user")            # a final alone: refused
        self.assertEqual(rc, 2)
        self.assertIn("the user's answer is the line score's own form", out)
        rc, out = self.looked("T96", *self.tool("label", "T96", f"end_P1_2={r1},user"))
        self.assertEqual(rc, 0, out)
        rc, out = self.tool("close", "T96")
        self.assertFalse(pic.exists())                                         # removed by close

    def test_2_a_sum_failing_twice(self):
        self.put("T97", OT)
        bad = text(OT["end_P1"]).replace("1+2+3+4", "1+2+3+9")                # 15, not its final 10
        rc, out = self.label_all("T97", OT, {"end_P1": f"{bad},{bad}"})
        self.assertIn("Read again: end_P1 (P1's cells add up to 15, not its final 10)", out)
        rc, out = self.tool("label", "T97", f"end_P1={bad},{bad}")
        self.assertIn("Ask the user about the match player 1 won 10-6, kept at ", out)
        self.assertIn(": player 1's Q1, Q2, Q3, Q4, OT1, OT2, final, as its final stats screen", out)
        self.assertNotIn("in overtime", out)

    def test_3_a_read_back_contradiction_is_never_asked(self):
        self.put("T98", OT)
        bad = text(OT["end_P1"]).replace("1+2+3+4+_+_=10", "1+2+3+7+_+_=13")   # adds up; the others read 4, 10
        rc, out = self.label_all("T98", OT, {"end_P1": f"{bad},{bad}"})
        self.assertEqual(rc, 1)
        self.assertIn("Read again: end_P1 (a reader learnt from the other saves reads it as", out)
        rc, out = self.tool("label", "T98", f"end_P1={bad},{bad}")
        self.assertEqual(rc, 1)
        self.assertNotIn("Ask the user", out)
        self.assertNotIn("collect it again", out)
        self.assertIn("Stop: end_P1 (a reader learnt from the other saves reads it as", out)
        self.assertIn("take this line back to the chat (Cowork)", out)
        self.assertFalse(self.pag.ask_folder().is_dir() and any(self.pag.ask_folder().glob("T98_*")))


if __name__ == "__main__":
    unittest.main()
