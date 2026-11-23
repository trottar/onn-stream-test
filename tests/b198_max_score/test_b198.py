#!/usr/bin/env python3
"""B198 (host): `register --max-score N` for a `score` title whose scores stay low. Every picture made-up
(`low_capture.py`; B181's `line_capture.py` for `Limit`); no title, nothing read from the hub's own folders.

- `Low`: a made-up low-scoring title (`low_capture.py`: its finals only, large) — five end saves (B171: a third save of
  P1's ending), finals 0-4, each of 0-4 shown by two saves, none of 5-9:
  - `--max-score 4` -> label and learn PASS; the every-digit cell names 0-4; 5-9 recorded "not expected";
  - `--max-score 5` -> learn FAIL on the every-digit cell alone, its line naming only 5 (never 6-9); two more saves
    showing a 5 -> PASS, 6-9 never shown;
  - no flag -> today: FAIL on today's cell, naming 5-9.
  (The queue's "finals 0-4, --max-score 5, passes" cannot pass under its own rule: 5 can occur from 0 to 5 and no save
  shows it — disclosed in the record.)
- `Hub`: the spec learnt with N: a final of 7 (a digit never learnt) -> `unknown` with `end_unread`, never `end`,
  never any number; a final above N with every digit learnt -> the same (`above_max`); a final within N -> `end` with
  the numbers. Through B182's watch (`companion/h7_minigame.py`'s `_run`, its picture and its game stubbed): the final
  of 7 -> `unreadable`, one `final_unreadable` row, no scores.
- `Register`: `--max-score` only with `--result score`; its cell; kept in the binding; the inputs digest today's
  without it.
- `Limit` (B178's, disclosed — not B198's): a line score whose finals and cells are all single digits (B181's
  `line_capture`) -> label FAIL "the numbers at one place in every save": the final's place not told from a cell
  column's. Never a PASS, never a guess.
Temp dirs removed.

    python3 -m unittest discover -s tests/b198_max_score -v
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(HERE), str(ROOT / "tests" / "b181_every_digit"),
                str(ROOT / "tests" / "b178_score_kind")]
import low_capture as lo  # noqa: E402
import test_b181 as b181  # noqa: E402  (its Made: the tool, the made-up saves, the label stage as the session gives it)

_ = None
LOW = {"begin": {"kind": "begin"}, "other": {"kind": "other"},
       "end_P1": {"kind": "end_low", "s": [1, 0], "look": 1}, "end_P1_2": {"kind": "end_low", "s": [3, 2], "look": 2},
       "end_P1_3": {"kind": "end_low", "s": [4, 1], "look": 3}, "end_P2": {"kind": "end_low", "s": [0, 4], "look": 4},
       "end_P2_2": {"kind": "end_low", "s": [2, 3], "look": 5}}
FIVES = {"end_P1_4": {"kind": "end_low", "s": [5, 2], "look": 6}, "end_P2_3": {"kind": "end_low", "s": [3, 5], "look": 7}}
LINE_LOW = {"begin": {"kind": "begin"}, "other": {"kind": "other"},     # B178's limit: single digits everywhere
            "end_P1": {"kind": "end_line", "q": [[1, 0, 2, 1, _, _], [0, 1, 0, 0, _, _]], "s": [4, 1], "look": 1},
            "end_P1_2": {"kind": "end_line", "q": [[0, 3, 0, 0, _, _], [0, 0, 0, 0, _, _]], "s": [3, 0], "look": 2},
            "end_P2": {"kind": "end_line", "q": [[0, 0, 1, 0, _, _], [1, 1, 0, 1, _, _]], "s": [1, 3], "look": 3},
            "end_P2_2": {"kind": "end_line", "q": [[2, 0, 0, 0, _, _], [0, 4, 0, 0, _, _]], "s": [2, 4], "look": 4}}
TODAY_CELL = "every digit 0-9 read by a reader learnt without each save that shows it"


def cell(n: int, digits: str) -> str:
    return f"every digit that can occur up to {n} ({', '.join(digits)}) read by a reader learnt without each save that shows it"


class Made(b181.Made):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ["PARTY_ADD_GAME_CAPTURE"] = "low_capture:capture"     # restored by B181's tearDownClass

    def put_max(self, code: str, saves: dict, max_score: int | None) -> None:
        """B181's made-up saves; the binding as register writes it with --max-score N (and its inputs digest)."""
        self.put(code, saves)
        pag = self.pag
        bp = pag.binding_path(code)
        b = json.loads(bp.read_text())
        if max_score is None:
            b.pop("max_score", None)
        else:
            b["max_score"] = max_score
        b["register_inputs"] = pag.register_inputs(b, pag.kept_states(code))
        bp.write_text(json.dumps(b))
        pag.verdict_path(code, "register").write_text(json.dumps({"verdict": "PASS", "inputs": b["register_inputs"]}))

    def learnt(self, code: str, saves: dict, max_score: int | None) -> tuple[int, str, dict]:
        self.put_max(code, saves, max_score)
        rc, out = self.label_all(code, saves)
        self.assertEqual(rc, 0, out + json.dumps(self.verdict(code, "label")["bad"]))
        rc, out = self.tool("learn", code)
        return rc, out, self.verdict(code, "learn")


class Low(Made):
    def test_1_max_4_passes_without_5_to_9(self):
        rc, out, v = self.learnt("T81", LOW, 4)
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))
        self.assertEqual(v["cells"][cell(4, "01234")], {"shown by fewer than two saves": [],
                                                       "not expected (above the highest score)": list("56789")})
        d = v["recorded"]["digits"]
        self.assertEqual((d["expected"], d["not expected"], d["never"]), (list("01234"), list("56789"), list("56789")))
        spec = json.loads((Path(os.environ["PRIVYHUB_H7_RULES"]) / "madeupt81.endscreen.json").read_text())
        self.assertEqual(spec["score"]["max_score"], 4)
        self.assertNotIn(TODAY_CELL, v["cells"])

    def test_2_max_5_asks_only_for_5_then_passes(self):
        rc, out, v = self.learnt("T82", LOW, 5)
        self.assertEqual(rc, 1, out)
        self.assertEqual(v["bad"], [cell(5, "012345")])
        self.assertEqual(v["cells"][cell(5, "012345")]["shown by fewer than two saves"], ["5"])
        self.assertIn("whose final score shows 5 (either side's number)", out)
        for d in "6789":                                       # the line names only expected digits
            self.assertNotIn(d, out.split("whose final score shows ", 1)[1].split(";", 1)[0])
        self.assertIn("1 digit is still short (5)", out)
        self.put_max("T82", FIVES, 5)
        rc, out = self.tool("label", "T82", *[f"{r}={b181.text(st)},{b181.text(st)}" for r, st in sorted(FIVES.items())])
        if rc == 1 and "Look at label/digits.png" in out:
            rc, out = self.tool("label", "T82", "look=all")
        self.assertEqual(rc, 0, out)
        rc, out = self.tool("learn", "T82")
        v = self.verdict("T82", "learn")
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))
        self.assertEqual(v["recorded"]["digits"]["never"], list("6789"))

    def test_3_no_flag_is_today(self):
        rc, out, v = self.learnt("T83", LOW, None)
        self.assertEqual(rc, 1, out)
        self.assertEqual(v["bad"], [TODAY_CELL])
        self.assertEqual(v["cells"][TODAY_CELL], {"shown by fewer than two saves": list("56789")})
        self.assertNotIn("expected", v["recorded"]["digits"])
        self.assertIn("whose final score shows 5, 6, 7, 8 or 9", out)


class Hub(Made):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls("run")
        try:
            rc, out, v = t.learnt("T84", {**LOW, **FIVES}, 5)
            assert rc == 0, out + json.dumps(v["bad"])
        except BaseException:
            cls.tearDownClass()                              # its temp dir removed even when the set-up fails
            raise
        import h7_endscreen as es
        cls.es = es
        cls.spec, cls.arrays = es.load_spec(Path(os.environ["PRIVYHUB_H7_RULES"]) / "madeupt84.endscreen.json")

    def reads(self, s, spec=None, n: int = 6) -> list[dict]:
        import numpy as np
        rng = np.random.default_rng(198)
        reader = self.es.Reader(spec or self.spec, self.arrays, clock=lambda: 0.0)
        return [reader.read(lo.low_screen(s, 9, rng), now=float(k)) for k in range(n)]

    def ended(self, reads: list[dict], spec=None):
        e = self.es.Ended(spec or self.spec)
        e.start_loaded()
        for r in reads:
            e.feed(r["class"], r.get("scores"))
        return e

    def test_1_a_final_of_7_never_read(self):
        self.assertEqual(self.spec["score"]["max_score"], 5)
        rs = self.reads([7, 1])
        self.assertEqual({r["class"] for r in rs}, {"unknown"}, rs)
        self.assertTrue(all(r.get("end_unread") for r in rs))
        self.assertEqual({r.get("scores") for r in rs}, {None})
        e = self.ended(rs)
        self.assertEqual((e.ended, e.scores), (None, None))

    def test_2_within_n_read(self):
        rs = self.reads([5, 1])
        e = self.ended(rs)
        self.assertEqual((e.ended, e.scores), ("end", [5, 1]))

    def test_3_above_n_with_every_digit_learnt_given_up(self):
        spec4 = json.loads(json.dumps(self.spec))
        spec4["score"]["max_score"] = 4                        # the same spec, its N one lower: 5 is above it
        rs = self.reads([5, 1], spec4)
        self.assertEqual({r["class"] for r in rs}, {"unknown"}, rs)
        self.assertTrue(all(r.get("end_unread") and r.get("above_max") for r in rs))
        self.assertEqual(self.ended(rs, spec4).ended, None)
        rs = self.reads([10, 0])                                 # a two-digit final above 5
        self.assertEqual({r["class"] for r in rs}, {"unknown"}, rs)
        self.assertTrue(all(r.get("end_unread") for r in rs))

    def test_4_the_watch_gives_up(self):
        """B182's watch on the reads of a final of 7: `unreadable`, one `final_unreadable` row, no scores."""
        sys.path.insert(0, str(ROOT / "companion"))
        import numpy as np
        import h7_minigame as hm
        log = self.tmp / "watch" / "h7.jsonl"
        mg = hm.MiniGame(None, None, lambda rel: log, environ={}, clock=time.monotonic)
        mg.read_every = 0.01
        rng = np.random.default_rng(7)

        class Live:
            def _running(self):
                return "madeupt84", "ps1", "x"

        class Pic:
            def grab(self):
                return lo.low_screen([7, 1], 9, rng).convert("RGB")

        mg._live, mg.picture = Live(), Pic()
        token = object()
        reader, ended = self.es.Reader(self.spec, self.arrays), self.es.Ended(self.spec)
        ended.start_loaded()
        mg._watch = {"state": "watching", "game": "madeupt84", "class": None, "seen_start": True, "recognised": True,
                     "reads": 0, "last": None, "loaded": True, "picture_failures": 0, "keep": None,
                     "t0": time.monotonic(), "token": token, "_keep_dir": None, "_recognise_s": 30.0}
        th = threading.Thread(target=mg._run, args=(token, "madeupt84", reader, ended, self.spec), daemon=True)
        th.start()
        th.join(60)
        self.assertFalse(th.is_alive())
        w = mg._watch
        self.assertEqual(w["state"], "unreadable", w)
        self.assertNotIn("scores", w)
        rows = [json.loads(x) for x in log.read_text().splitlines()]
        self.assertEqual([r["step"] for r in rows if r["step"] in ("final_unreadable", "ended")], ["final_unreadable"])


class Register(Made):
    def setUp(self):
        r = Path(os.environ["PRIVYHUB_H7_RULES"])
        (r / "madeupreg.party.json").write_text(json.dumps({"players": 2, "result": "score"}))
        Path(os.environ["PRIVYHUB_ADD_GAME_DROPINS"]).mkdir(parents=True, exist_ok=True)

    def reg(self, code: str, *more) -> tuple[int, str]:
        return self.tool("register", code, "--players", 2, "--system", "ps1", "--rules-players", 2, *more)

    def test_1_only_with_score(self):
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()):
            rc, _out = self.reg("T85", "--result", "winner", "--max-score", 5)
        self.assertEqual(rc, 2)

    def test_2_kept_in_the_binding_and_the_inputs(self):
        self.reg("T86", "--result", "score", "--max-score", 5)
        b = json.loads(self.pag.binding_path("T86").read_text())
        v = self.verdict("T86", "register")
        self.assertEqual(v["cells"]["the highest score one side reaches (--max-score)"], "5")
        self.assertEqual(b["max_score"], 5)
        self.reg("T86", "--result", "score")                  # again without it: dropped, the digest today's
        b2 = json.loads(self.pag.binding_path("T86").read_text())
        self.assertNotIn("max_score", b2)
        self.assertNotEqual(b["register_inputs"], b2["register_inputs"])
        self.assertNotIn("the highest score one side reaches (--max-score)", self.verdict("T86", "register")["cells"])
        today = self.pag.digest({"code": b2["code"], "players": b2["players"], "system": b2["system"],
                                 "result": b2["result"], "setup": bool(b2.get("cheat")), "kept": {},
                                 "game": __import__("hashlib").sha256(b2["game"].encode()).hexdigest()})
        self.assertEqual(b2["register_inputs"], today)

    def test_3_not_a_whole_number(self):
        self.reg("T87", "--result", "score", "--max-score", "five")
        v = self.verdict("T87", "register")
        self.assertIn("the highest score one side reaches (--max-score)", v["bad"])
        self.assertNotIn("max_score", json.loads(self.pag.binding_path("T87").read_text()))


class Limit(b181.Made):
    def test_single_digits_in_a_line_score_not_placed(self):
        """B178's place choice (disclosed, not changed here): finals and cells all single digits -> the final's place
        not told from a cell column's; label FAIL on the place cell, never a PASS."""
        self.put("T79", LINE_LOW)
        rc, out = self.label_all("T79", LINE_LOW)
        self.assertEqual(rc, 1, out)
        self.assertIn("the numbers at one place in every save", self.verdict("T79", "label")["bad"])


if __name__ == "__main__":
    unittest.main()
