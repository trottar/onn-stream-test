# Frozen with T90's old score path (queue BQ, B217): this suite's made-up noise is exactly the pre-BP fixture (one generator per run, the shared save counter); the per-picture noise is for the new path's suites only.
#!/usr/bin/env python3
"""B181 / B183 / B184 (host): every digit learnt from the whole line score; the last look; the held anchor. Every
picture made-up (`line_capture.py`, `score_capture.py`); no title, nothing read from the hub's own folders.

- `LineScore`: four end saves whose line scores show every digit 0-9 in two saves or more -> label (the session's
  readings as the session gives them, the last look `look=all`) and learn PASS; the columns found where they are
  drawn, the separator between them refused; a misread breaking a sum named; one digit in one save only -> learn FAIL,
  the every-digit cell and the line naming it, then one more save -> PASS.
- `FinalsOnly`: B178's made-up title (finals alone, digits 1, 2, 4) -> left out all met, learn FAIL on the every-digit
  cell alone, its line naming the seven digits.
- `LastLook`: the systematic misread of BG's table (every 4 read as 9) -> every other check met, the last look names
  the saves; `look=all` -> PASS (the session's answer is the test's: it knows what it drew).
- `Anchor`: a final screen held 4 s, then a still screen for the rest of the run -> the final screen's pictures are
  the labelled range (B167's anchor would take the later screen).
Temp dirs removed.

    python3 -m unittest discover -s tests/b181_every_digit -v
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
sys.path[:0] = [str(ROOT / "tools"), str(HERE), str(ROOT / "tests" / "b178_score_kind")]
import line_capture as lc  # noqa: E402

ENV_KEYS = ("PRIVYHUB_ADD_GAME_HOME", "PRIVYHUB_ADD_GAME_EVIDENCE", "PRIVYHUB_H7_RULES", "PRIVYHUB_ADD_GAME_LOGS",
            "PARTY_ADD_GAME_CAPTURE", "PRIVYHUB_ADD_GAME_HUB", "PRIVYHUB_ADD_GAME_DROPINS")
_ = None
# every digit in two saves or more (role check: the first two P1 ahead, the last two P2)
LINE = {"begin": {"kind": "begin"}, "other": {"kind": "other"},
        "end_P1": {"kind": "end_line", "q": [[1, 2, 3, 4, _, _], [0, 5, 0, 1, _, _]], "s": [10, 6], "look": 1},
        "end_P1_2": {"kind": "end_line", "q": [[7, 8, 9, 0, _, _], [6, 5, 4, 3, _, _]], "s": [24, 18], "look": 2},
        "end_P2": {"kind": "end_line", "q": [[2, 0, 1, 3, _, _], [9, 8, 7, 0, _, _]], "s": [6, 24], "look": 3},
        "end_P2_2": {"kind": "end_line", "q": [[5, 6, 0, 0, _, _], [7, 8, 9, 1, _, _]], "s": [11, 25], "look": 4}}
FINALS = {"begin": {"kind": "begin"}, "other": {"kind": "other"},
          "end_P1": {"kind": "end", "s": [21, 14], "look": 1}, "end_P1_2": {"kind": "end", "s": [42, 12], "look": 2},
          "end_P2": {"kind": "end", "s": [14, 24], "look": 3}, "end_P2_2": {"kind": "end", "s": [12, 41], "look": 4}}


def text(st: dict) -> str:
    if "q" not in st:
        return "-".join(str(x) for x in st["s"])
    return "-".join("+".join("_" if c is None else str(c) for c in cells) + "=" + str(fin)
                    for cells, fin in zip(st["q"], st["s"]))


class Made(unittest.TestCase):
    N = [0]

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="b181_"))
        cls.old = {k: os.environ.get(k) for k in ENV_KEYS}
        os.environ.update({"PRIVYHUB_ADD_GAME_HOME": str(cls.tmp / "home"), "PRIVYHUB_ADD_GAME_EVIDENCE": str(cls.tmp / "ev"),
                           "PRIVYHUB_H7_RULES": str(cls.tmp / "rules"), "PRIVYHUB_ADD_GAME_LOGS": str(cls.tmp / "logs"),
                           "PARTY_ADD_GAME_CAPTURE": "line_capture:capture", "PRIVYHUB_ADD_GAME_HUB": "http://127.0.0.1:9",
                           "PRIVYHUB_ADD_GAME_DROPINS": str(cls.tmp / "dropins")})
        (cls.tmp / "rules").mkdir()
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
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = self.pag.main([str(a) for a in argv])
        return rc, buf.getvalue()

    def verdict(self, code: str, stage: str) -> dict:
        v = self.pag.load_verdict(code, stage) or {}
        return {"verdict": v.get("verdict"), "bad": [c["cell"] for c in v.get("cells", []) if not c["met"]],
                "cells": {c["cell"]: c["read"] for c in v.get("cells", [])}, "recorded": v.get("recorded") or {}}

    def label_all(self, code: str, saves: dict, wrong: dict | None = None, look: bool = True):
        texts = {r: text(st) for r, st in saves.items() if r.startswith("end_")}
        texts.update(wrong or {})
        rc, out = self.tool("label", code, *[f"{r}={t},{t}" for r, t in sorted(texts.items())])
        if rc == 1 and look and "Look at label/digits.png" in out:
            rc, out = self.tool("label", code, "look=all")
        return rc, out


class LineScore(Made):
    def test_1_every_digit_from_the_line_score_pass(self):
        self.put("T91", LINE)
        rc, out = self.label_all("T91", LINE)
        self.assertEqual(rc, 0, out + json.dumps(self.verdict("T91", "label")["bad"]))
        self.assertTrue((self.pag.label_folder("T91") / "digits.png").is_file())
        rc, out = self.tool("learn", "T91")
        v = self.verdict("T91", "learn")
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))
        self.assertEqual(v["cells"]["every digit 0-9 read by a reader learnt without each save that shows it"],
                         {"shown by fewer than two saves": []})
        spec = json.loads((Path(os.environ["PRIVYHUB_H7_RULES"]) / "madeupt91.endscreen.json").read_text())
        for cols in spec["score"]["columns"]:                 # the columns where they are drawn, the separators refused
            got = [None if c is None else (c["x0"] + c["x1"]) / 2 for c in cols]
            self.assertEqual([None if g is None else round(g / 2) * 2 for g in got[:4]], [c for c in lc.COLS[:4]], got)
            self.assertEqual(got[4:], [None, None])

    def test_2_a_misread_breaking_a_sum(self):
        self.put("T92", LINE)
        rc, out = self.label_all("T92", LINE, {"end_P1": "1+2+3+9+_+_=10-0+5+0+1+_+_=6"})
        self.assertEqual(rc, 1)
        self.assertIn("end_P1 (P1's cells add up to 15, not its final 10)", out)

    def test_3_one_digit_in_one_save_then_one_more(self):
        saves = {"begin": {"kind": "begin"}, "other": {"kind": "other"},           # 6 shown by end_P2 alone
                 "end_P1": {"kind": "end_line", "q": [[1, 2, 3, 4, _, _], [0, 5, 0, 2, _, _]], "s": [10, 7], "look": 1},
                 "end_P1_2": {"kind": "end_line", "q": [[7, 8, 9, 0, _, _], [5, 5, 4, 3, _, _]], "s": [24, 17],
                              "look": 2},
                 "end_P2": {"kind": "end_line", "q": [[2, 0, 1, 3, _, _], [9, 8, 7, 0, _, _]], "s": [6, 24], "look": 3},
                 "end_P2_2": {"kind": "end_line", "q": [[5, 5, 0, 0, _, _], [7, 8, 9, 1, _, _]], "s": [10, 25],
                              "look": 4}}
        self.put("T93", saves)
        rc, out = self.label_all("T93", saves)
        self.assertEqual(rc, 0, out)
        rc, out = self.tool("learn", "T93")
        v = self.verdict("T93", "learn")
        self.assertEqual(rc, 1, out)
        self.assertIn("every digit 0-9 read by a reader learnt without each save that shows it", v["bad"])
        self.assertEqual(v["cells"]["every digit 0-9 read by a reader learnt without each save that shows it"]
                         ["shown by fewer than two saves"], ["6"])            # B186: the cell also says what one save showed
        self.assertIn("whose line score shows 6", out)
        more = {"end_P1_3": {"kind": "end_line", "q": [[6, 6, 1, 0, _, _], [3, 2, 0, 0, _, _]], "s": [13, 5], "look": 5}}
        self.put("T93", more)
        rc, out = self.tool("label", "T93", f"end_P1_3={text(more['end_P1_3'])},{text(more['end_P1_3'])}")
        if rc == 1 and "Look at label/digits.png" in out:
            rc, out = self.tool("label", "T93", "look=all")
        self.assertEqual(rc, 0, out)
        rc, out = self.tool("learn", "T93")
        self.assertEqual(rc, 0, out + json.dumps(self.verdict("T93", "learn")["bad"]))


class FinalsOnly(Made):
    def test_finals_only_needs_every_digit(self):
        self.put("T94", FINALS)
        rc, out = self.label_all("T94", FINALS)
        self.assertEqual(rc, 0, out)
        rc, out = self.tool("learn", "T94")
        v = self.verdict("T94", "learn")
        self.assertEqual(rc, 1, out)
        self.assertEqual(v["bad"], ["every digit 0-9 read by a reader learnt without each save that shows it"])
        self.assertIn("whose final score shows 0, 3, 5, 6, 7, 8 or 9", out)


class LastLook(Made):
    def test_the_systematic_misread_caught(self):
        self.put("T95", FINALS)
        nine = {r: "-".join(str(x).replace("4", "9") for x in st["s"]) for r, st in FINALS.items() if r.startswith("end_")}
        rc, out = self.label_all("T95", FINALS, nine, look=False)
        self.assertEqual(rc, 1)
        self.assertIn("Look at label/digits.png", out)
        self.assertEqual(self.verdict("T95", "label")["bad"], ["the last look: every glyph is the digit it was read as"])
        rows = self.pag.label_record("T95")["tiles"]["rows"]
        self.assertNotIn("4", rows)                            # every 4 in the row of 9
        rc, out = self.tool("label", "T95", "look=9:" + ".".join(str(i + 1) for i in range(len(rows["9"]))))
        self.assertEqual(rc, 1)
        for role in ("end_P1", "end_P1_2", "end_P2", "end_P2_2"):
            self.assertIn(f"{role} (a glyph read as 9 is not one, at the last look)", out)

    def test_look_all_passes(self):
        self.put("T96", FINALS)
        rc, out = self.label_all("T96", FINALS, look=False)
        self.assertEqual(rc, 1)
        self.assertIn("Look at label/digits.png", out)
        rc, out = self.tool("label", "T96", "look=all")
        self.assertEqual(rc, 0, out)


class Anchor(Made):
    def test_a_final_screen_held_four_seconds(self):
        st = dict(LINE["end_P1"], kind="end_short")
        self.put("T97", {"begin": {"kind": "begin"}, "other": {"kind": "other"}, "end_P1": st})
        pag = self.pag
        kept = pag.kept_states("T97")
        b = json.loads(pag.binding_path("T97").read_text())
        pics = pag._pictures("T97", b, kept)
        labels = pag._labels(pics, kept, pag._endscreen())
        held = [x for x in labels["runs"]["end_P1"] if x["label"] != "ignore"]
        self.assertEqual((held[0]["from"], held[0]["to"]), (0.0, 3.0), labels["runs"]["end_P1"])
        import csv
        rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader((pics / "end_P1" / "index.csv").open())]
        small = [pag._small(pics / "end_P1" / f) for _t, f in rows]
        self.assertGreater(pag._anchor(small), 3)              # B167's anchor: the later, longer screen


if __name__ == "__main__":
    unittest.main()
