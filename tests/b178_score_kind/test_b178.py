#!/usr/bin/env python3
"""B178 (host): the `score` result kind — a title whose final screen shows each side's number, the winner the side
with more. Every picture made-up (`score_capture.py`); no title, nothing read from the hub's own folders but T88's /
T89's rules' sha256 (read only).

- `Learn`: made-up titles through the tool's label and learn (the session's readings given as the session would):
  four end saves whose numbers share their digits -> label PASS, learn PASS (every save read by a spec learnt
  without it), the sidecar `"result": "score"`, a version-4 spec; T90's shape (a digit only one save shows) -> label
  PASS, learn FAIL naming the digits, then one more save showing them -> PASS.
- `Reads`: that spec on a tie (both numbers), numbers with digits never learnt (unknown, never ended: no guess), the
  middle of a match with a score bug, the final screen's numbers moved, the loading screen, the begin.
- `LabelChecks`: each check failing on purpose and the line it gives; the second time -> the user; the user's numbers
  that do not fit; a systematic misread that gets through (the record's residual).
- `Hub`: B114's harness, its `b178` mode — the tool's whole path through the real routes (register -> label -> learn
  -> bench -> close) and the hub's endings (real numbers, the winner's seat, a tie -> null, unreadable -> no result).
- `SoloDraw`: solo's read for a score title's tie (`--winner draw`).
- `TodayUnchanged`: the flags absent, B114's `today` routes the same on HEAD's code and mine.
Temp dirs removed.

    python3 -m unittest discover -s tests/b178_score_kind -v
"""
from __future__ import annotations

import contextlib
import hashlib
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
sys.path[:0] = [str(ROOT / "tools"), str(HERE)]
for sub in ("b114_party_minigame_hang", "b124_party_four_seats", "b123_h7_n64_start", "b157_add_game"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import score_capture as sc  # noqa: E402

BASELINE = "b243dd63"
A = {"begin": {"kind": "begin"}, "other": {"kind": "other"},
     "end_P1": {"kind": "end", "s": [21, 14], "look": 1}, "end_P1_2": {"kind": "end", "s": [42, 12], "look": 2},
     "end_P2": {"kind": "end", "s": [14, 24], "look": 3}, "end_P2_2": {"kind": "end", "s": [12, 41], "look": 4}}
T90_SHAPE = {"begin": {"kind": "begin"}, "other": {"kind": "other"},
             "end_P1": {"kind": "end", "s": [15, 2], "look": 1}, "end_P1_2": {"kind": "end", "s": [35, 28], "look": 2},
             "end_P2": {"kind": "end", "s": [0, 22], "look": 3}, "end_P2_2": {"kind": "end", "s": [0, 29], "look": 4}}
ENV_KEYS = ("PRIVYHUB_ADD_GAME_HOME", "PRIVYHUB_ADD_GAME_EVIDENCE", "PRIVYHUB_H7_RULES", "PRIVYHUB_ADD_GAME_LOGS",
            "PARTY_ADD_GAME_CAPTURE", "PRIVYHUB_ADD_GAME_HUB", "PRIVYHUB_ADD_GAME_DROPINS")


def rd(nums, again=None) -> str:
    a = "-".join(map(str, nums))
    return f"{a},{'-'.join(map(str, again)) if again is not None else a}"


class Made(unittest.TestCase):
    """A temp add_game home, evidence and rules folder; the made-up picture source."""
    N = [0]

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="b178_"))
        cls.old = {k: os.environ.get(k) for k in ENV_KEYS}
        os.environ.update({"PRIVYHUB_ADD_GAME_HOME": str(cls.tmp / "home"), "PRIVYHUB_ADD_GAME_EVIDENCE": str(cls.tmp / "ev"),
                           "PRIVYHUB_H7_RULES": str(cls.tmp / "rules"), "PRIVYHUB_ADD_GAME_LOGS": str(cls.tmp / "logs"),
                           "PARTY_ADD_GAME_CAPTURE": "score_capture:capture", "PRIVYHUB_ADD_GAME_HUB": "http://127.0.0.1:9",
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
        """The kept saves (made-up states) and register's PASS, as rehearse's scratch writes them."""
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

    def label_all(self, code: str, saves: dict, wrong: dict | None = None):
        args = [f"{r}={rd(st['s'])}" for r, st in sorted(saves.items()) if r.startswith("end_")]
        for r, val in (wrong or {}).items():
            args = [a for a in args if not a.startswith(r + "=")] + [f"{r}={val}"]
        return self.tool("label", code, *args)


class Learn(Made):
    def test_1_shared_digits_pass(self):
        self.put("T91", A)
        rc, out = self.tool("label", "T91")
        self.assertEqual(rc, 1, out)
        self.assertIn("Read the final score", out)
        pics = sorted(p.name for p in self.pag.label_folder("T91").iterdir())
        self.assertEqual(pics, sorted(f"{r}.{i}.png" for r in A if r.startswith("end_") for i in (1, 2)))
        rc, out = self.label_all("T91", A)
        self.assertEqual(rc, 0, out + json.dumps(self.verdict("T91", "label")))
        self.assertTrue(any(p.name.endswith(".P1.png") for p in self.pag.label_folder("T91").iterdir()))   # crops
        rc, out = self.tool("learn", "T91")
        v = self.verdict("T91", "learn")
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))
        for r in ("end_P1", "end_P1_2", "end_P2", "end_P2_2"):
            self.assertEqual(v["cells"][f"{r}: ended as itself"], A[r]["s"])
            self.assertEqual(v["cells"][f"left out: {r}"][0], A[r]["s"])
        rules = Path(os.environ["PRIVYHUB_H7_RULES"])
        self.assertEqual(json.loads((rules / "madeupt91.party.json").read_text()), {"players": 2, "result": "score"})
        self.assertEqual(json.loads((rules / "madeupt91.endscreen.json").read_text())["version"], 4)
        self.assertEqual(v["recorded"]["digits"]["never"], ["0", "3", "5", "6", "7", "8", "9"])

    def test_2_t90_shape_names_the_digits_then_passes(self):
        self.put("T92", T90_SHAPE)
        rc, out = self.label_all("T92", T90_SHAPE)
        lv = self.verdict("T92", "label")
        self.assertEqual(rc, 0, out + json.dumps(lv["bad"]))
        self.assertEqual(lv["cells"]["end_P1: read back by a reader learnt without it"], "not read (shown only here: 1)")
        self.assertEqual(lv["cells"]["end_P2: read back by a reader learnt without it"], [0, 22])
        rc, out = self.tool("learn", "T92")
        v = self.verdict("T92", "learn")
        self.assertEqual(rc, 1)
        self.assertEqual(sorted(v["bad"]), ["left out: end_P1", "left out: end_P1_2", "left out: end_P2_2"])
        self.assertIn("whose final score shows 1, 3, 8 or 9", out)
        self.assertIn("end_P1_3 if P1 won, end_P2_3 if P2 won", out)
        self.assertEqual(v["recorded"]["digits"]["in one save"], ["1", "3", "8", "9"])
        self.assertFalse((Path(os.environ["PRIVYHUB_H7_RULES"]) / "madeupt92.party.json").exists())
        more = {"end_P1_3": {"kind": "end", "s": [39, 18], "look": 7}}
        self.put("T92", more)
        rc, out = self.tool("label", "T92", f"end_P1_3={rd([39, 18])}")
        self.assertEqual(rc, 0, out)
        rc, out = self.tool("learn", "T92")
        self.assertEqual(rc, 0, out + json.dumps(self.verdict("T92", "learn")["bad"]))

    def test_3_learn_needs_label(self):
        self.put("T93", A)
        rc, out = self.tool("learn", "T93")
        self.assertEqual(rc, 2)
        self.assertIn("label has no PASS", out)


class Reads(Made):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls("run")
        t.put("T94", A)
        t.label_all("T94", A)
        rc, out = t.tool("learn", "T94")
        assert rc == 0, out
        import h7_endscreen as es
        cls.es = es
        cls.spec, cls.arrays = es.load_spec(Path(os.environ["PRIVYHUB_H7_RULES"]) / "madeupt94.endscreen.json")

    def run_of(self, st: dict, seconds: float = 20.0):
        import numpy as np
        rng = np.random.default_rng(31)
        reader = self.es.Reader(self.spec, self.arrays, clock=lambda: 0.0)
        ended = self.es.Ended(self.spec)
        ended.start_loaded()
        reads = []
        for k in range(0, int(seconds)):
            r = reader.read(sc.picture({"look": 9, **st}, float(k), k, rng), now=float(k))
            reads.append((r["class"], r.get("scores")))
            ended.feed(r["class"], r.get("scores"))
        return reads, ended

    def test_tie_read_as_both_numbers(self):
        reads, ended = self.run_of({"kind": "end", "s": [14, 14]}, 6)
        self.assertEqual((ended.ended, ended.scores), ("end", [14, 14]))

    def test_a_number_never_learnt_is_not_read(self):
        reads, ended = self.run_of({"kind": "end", "s": [17, 3]}, 6)
        self.assertIsNone(ended.ended)
        self.assertEqual({c for c, _s in reads}, {"unknown"})

    def test_not_the_final_screen(self):
        for st in ({"kind": "mid_score", "s": [21, 14]}, {"kind": "other"}, {"kind": "end_offset", "s": [21, 14]}):
            reads, ended = self.run_of(st, 6)
            self.assertIsNone(ended.ended, (st, reads))
        reads, ended = self.run_of({"kind": "end", "s": [21, 14]}, 14)          # held 9 s, then the loading screen
        self.assertEqual(ended.scores, [21, 14])
        self.assertEqual({c for c, _s in reads[10:]}, {"other"})
        reads, ended = self.run_of({"kind": "begin"}, 4)
        self.assertEqual({c for c, _s in reads}, {"start"})


class LabelChecks(Made):
    def test_two_readings_differ_then_the_user(self):
        self.put("T95", A)
        rc, out = self.label_all("T95", A, {"end_P1": rd([21, 14], [21, 11])})
        self.assertEqual(rc, 1)
        self.assertIn("Read again: end_P1 (its two readings differ)", out)
        rc, out = self.tool("label", "T95", f"end_P1={rd([21, 14], [21, 11])}")
        self.assertIn("Ask the user for end_P1's numbers", out)
        rc, out = self.tool("label", "T95", "end_P1=21-14,user")
        self.assertEqual(rc, 0, out)

    def test_role_and_swapped_sides(self):
        self.put("T96", A)
        rc, out = self.label_all("T96", A, {"end_P2": rd([21, 14]), "end_P1": rd([14, 21])})
        self.assertEqual(rc, 1)
        v = self.verdict("T96", "label")
        self.assertIn("end_P2: the role's player ahead", v["bad"])
        self.assertIn("end_P1: the role's player ahead", v["bad"])
        self.assertIn("end_P1 (P1 is not ahead in it)", out)

    def test_a_digit_misread_as_another_seen_digit(self):
        self.put("T97", A)
        rc, out = self.label_all("T97", A, {"end_P1": rd([24, 14])})
        self.assertEqual(rc, 1)
        self.assertIn("end_P1 (a reader learnt from the other saves reads it as 21-14)", out)
        for right in ("end_P1_2 (", "end_P2 (", "end_P2_2 ("):                  # the saves it spoiled: not named
            self.assertNotIn(right, out)

    def test_a_misread_digit_only_this_save_shows(self):
        """T90's shape: 16-2 for 15-2 (no other save shows a 1 or a 6) passes the label stage; learn cannot pass with
        it; once one more save shows a 1, the label stage names that save alone."""
        self.put("T88", T90_SHAPE)
        rc, out = self.label_all("T88", T90_SHAPE, {"end_P1": rd([16, 2])})
        self.assertEqual(rc, 0, out)
        rc, out = self.tool("learn", "T88")
        self.assertEqual(rc, 1, out)
        self.put("T88", {"end_P1_3": {"kind": "end", "s": [39, 18], "look": 7}})
        rc, out = self.tool("label", "T88", f"end_P1_3={rd([39, 18])}")
        self.assertEqual(rc, 1, out)
        self.assertIn("Read again: end_P1 (a reader learnt from the other saves reads it as 15-2)", out)
        self.assertNotIn("end_P1_2 (", out)

    def test_a_dropped_digit(self):
        self.put("T98", A)
        rc, out = self.label_all("T98", A, {"end_P1_2": rd([42, 2])})
        self.assertEqual(rc, 1)
        self.assertIn("end_P1_2 (P2's number does not fit where the other saves have it)", out)

    def test_the_users_numbers_that_do_not_fit(self):
        self.put("T99", A)
        rc, out = self.label_all("T99", A, {"end_P1": "24-14,user"})
        self.assertEqual(rc, 1)
        self.assertIn("end_P1 cannot be read as the user says", out)

    def test_a_systematic_misread_gets_through(self):
        """The residual, said in the record: one glyph misread the same way in every save that shows it."""
        self.put("T89", A)
        nine = {r: rd([int(str(x).replace("4", "9")) for x in st["s"]]) for r, st in A.items() if r.startswith("end_")}
        rc, out = self.label_all("T89", A, nine)
        self.assertEqual(rc, 0, out)
        rc, out = self.tool("learn", "T89")
        self.assertEqual(rc, 0, out)


class Hub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import test_b114 as b114
        import test_b124 as b124
        cls.kept_before = kept_rules_digest()
        root, ids = b114.b99.tree()
        try:
            b124.IDS.clear()
            b124.IDS.update(ids)

            def extra(work, frames):
                sc.frames(frames)
                return {"tools": str(ROOT / "tools"), "b178_dir": str(HERE)}
            cls.s = b114.run(root, b114.BOTH, ids, "b178", extra=extra, timeout=1200)["steps"]
        finally:
            shutil.rmtree(root, ignore_errors=True)
        cls.kept_after = kept_rules_digest()

    def test_0_no_error(self):
        self.assertNotIn("b178_error", self.s, self.s.get("b178_error"))

    def test_1_the_tools_whole_path(self):
        s = self.s
        self.assertEqual(s["s_reg_v"]["verdict"], "PASS", s["s_reg"])
        self.assertEqual(s["s_learn_before_label"]["rc"], 2)
        self.assertEqual(s["s_label_first"]["rc"], 1)
        self.assertEqual(len(s["s_label_pictures"]), 8)
        self.assertEqual(s["s_label_v"]["verdict"], "PASS", s["s_label"])
        self.assertEqual(s["s_learn_v"]["verdict"], "PASS", s["s_learn_v"]["bad"])
        self.assertEqual((s["s_sidecar"], s["s_spec_version"]), ({"players": 2, "result": "score"}, 4))
        self.assertEqual(s["s_bench_v"]["verdict"], "PASS", s["s_bench_v"]["bad"])
        for role, code in (("end_P1", 310), ("end_P1_2", 311), ("end_P2", 312), ("end_P2_2", 313)):
            self.assertEqual(s["s_bench_v"]["cells"][f"{role}: scores"], sc.SCORES[code])
            self.assertEqual(s["s_bench_v"]["cells"][f"{role}: ended with its class"], ["ended", "end"])
        self.assertEqual(s["s_close_v"]["verdict"], "PASS", s["s_close_v"]["bad"])

    def test_2_no_run_time_name(self):
        low = self.s["texts"].casefold()
        for n in self.s["names"]:
            self.assertNotIn(str(n).casefold(), low)

    def test_3_the_hubs_endings(self):
        s = self.s
        self.assertEqual(s["h_list"], [2])
        a, b, tie = s["h_a"], s["h_b"], s["h_tie"]
        self.assertEqual((a["state"], a["scores"], a.get("winner")), ("ended", [21, 14], 1), a)
        self.assertEqual((b["state"], b["scores"], b.get("winner")), ("ended", [21, 14], 2), b)    # port 1 = seat 2
        self.assertEqual((tie["state"], tie["scores"], tie.get("winner")), ("ended", [14, 14], None), tie)
        self.assertEqual(s["h_a_ended_rows"], [{"class": "end", "scores": [21, 14], "winner": 1}])
        self.assertEqual(s["h_tie_ended_rows"], [{"class": "end", "scores": [14, 14], "winner": None}])

    def test_4_unreadable_is_no_result(self):
        u = self.s["h_unread"]
        self.assertEqual(u["state"], "given_up", u)
        self.assertIn("unknown screen", u["why"])
        self.assertEqual(self.s["h_unread_rows"], ["minigame_given_up"])

    def test_5_not_listed(self):
        self.assertEqual((self.s["h_list_with_scores"], self.s["h_list_four"]), ([], []))

    def test_6_the_kept_rules_untouched(self):
        self.assertEqual(self.kept_before, self.kept_after)


def kept_rules_digest() -> list:
    folder = Path.home() / "privyhub_h7" / "rules"
    if not folder.is_dir():
        return []
    return sorted(hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file())


class SoloDraw(unittest.TestCase):
    """solo's read for a score title: `--winner draw` (the hub's winner null on a tie); a seat where it was a tie fails."""

    def setUp(self):
        import test_b157
        self.case = test_b157.SoloReads("test_pass")
        self.case.setUp()
        b = json.loads((self.case.tmp / "home/T93/binding.json").read_text())
        b["result"] = "score"
        (self.case.tmp / "home/T93/binding.json").write_text(json.dumps(b))
        ev = self.case.tmp / "ev/T93"
        (ev / "bench.json").write_text(json.dumps({"verdict": "PASS", "inputs": self.case.pag.bench_inputs("T93", b)}))

    def tearDown(self):
        self.case.tearDown()

    def read(self, winner):
        (self.case.tmp / "home/T93/solo_mark.json").write_text(json.dumps(
            {"party": 0, "heartbeat": 0, "video": 0, "video_bytes": 0, "board_log": None, "board_lines": 0}))
        self.case.logs()
        p = self.case.tmp / "proj/logs/games/party.jsonl"
        rows = [json.loads(x) for x in p.read_text().splitlines()]
        rows[-1] = {**rows[-1], "class": "end", "scores": [14, 14], "winner": None}
        p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        import test_b157
        return test_b157._tool("solo", "T93", "--read", "--winner", winner)

    def test_draw(self):
        rc, out = self.read("draw")
        self.assertEqual(rc, 0, out + (self.case.tmp / "ev/T93/solo.md").read_text())

    def test_a_seat_on_a_tie_fails(self):
        rc, out = self.read(1)
        self.assertEqual(rc, 1, out)


class TodayUnchanged(unittest.TestCase):
    """The flags absent (the hub's adopted flags only): B114's `today` routes the same on HEAD's code and mine."""

    def test_today_the_same(self):
        import test_b114 as b114
        import test_b158 as b158
        env = {**b114.b85.FLAGS, **b114.ADOPTED}
        mine = b158.run_mode("today", env)
        head = b158.run_mode("today", env, BASELINE)
        for k in ("list", "start", "result", "end", "go", "status_idle", "home_idle", "stop_idle"):
            self.assertEqual((mine[k]["code"], b114.CLOCK.sub("<ms>", mine[k]["raw"])),
                             (head[k]["code"], b114.CLOCK.sub("<ms>", head[k]["raw"])), k)


sys.path.insert(0, str(ROOT / "tests" / "b158_winner_only"))

if __name__ == "__main__":
    unittest.main()
