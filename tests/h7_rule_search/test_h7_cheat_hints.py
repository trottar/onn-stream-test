#!/usr/bin/env python3
"""B97 (host, no emulator): hints from a cheat list in the hub's stored form, and the search's --hints / (b2) on
made-up memories. The fixtures' cheat lists are made up (`fixtures.cht`); no real list is read. Temp dirs removed.

    python3 -m unittest discover -s tests/h7_rule_search -p 'test_h7_cheat_hints.py' -v
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))
import fixtures as F  # noqa: E402
import h7_cheat_hints as ch  # noqa: E402
import h7_rule_search as search  # noqa: E402

HINTS = ROOT / "tools" / "h7_cheat_hints.py"
VOCABULARY = {"player", "players"}          # the tool's own words (keys, reasons) — not taken from a description


def descriptions(text: str) -> list[str]:
    return re.findall(r'cheat\d+_desc\s*=\s*"(.*?)"', text)


class Hints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="h7_hints_test_"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def write(self, name: str, data: str | bytes) -> Path:
        p = self.tmp / name
        (p.write_bytes if isinstance(data, bytes) else p.write_text)(data)
        return p

    def test_ps1_hints_every_readable_form(self):
        res = ch.read_hints(self.write("ps1.cht", F.cht("ps1")), "ps1")
        got = {(h["player"], h["address"], h["bytes"], h["kind"], h["value"]) for h in res["hints"]}
        p = F.PS1
        r = [hex(p["block"] + k * p["stride"] + p["rounds"]) for k in range(2)]
        lv = [hex(p["block"] + k * p["stride"] + p["level"]) for k in range(2)]
        self.assertIn(("P1", lv[0], 2, "level", 120), got)                 # '+' form
        self.assertIn(("P2", lv[1], 2, "level", 120), got)                 # ':' form, "Player 2"
        self.assertIn(("P1", r[0], 2, "tally", 2), got)                    # 4-hex chunks
        self.assertIn(("P2", r[1], 2, "tally", 2), got)                    # "2P"
        self.assertIn(("P1", "0xf9000", 1, "other", 3), got)               # type 30: 1 byte; a third thing
        self.assertIn(("P1", lv[0], 2, "level", None), got)                # a value to choose
        self.assertEqual(res["skipped"], {"no player": 2, "several players": 1, "a form this tool does not read": 1})
        cond = [h for h in res["hints"] if h["line"] == 1]                 # the write after a condition
        self.assertEqual([(h["player"], h["address"]) for h in cond], [("P1", lv[0])])
        groups = {h["code"]: h["pair_group"] for h in res["hints"]}
        self.assertEqual(groups[3], groups[4])                             # "P1 Rounds Won" / "2P Rounds Won"
        self.assertNotEqual(groups[1], groups[3])

    def test_snes_hints(self):
        res = ch.read_hints(self.write("snes.cht", F.cht("snes")), "snes")
        p = F.SNES
        got = {(h["player"], h["address"], h["bytes"], h["kind"]) for h in res["hints"]}
        for k in range(2):
            self.assertIn((f"P{k + 1}", hex(p["block"] + k * p["stride"] + p["level"]), 1, "level"), got)
            self.assertIn((f"P{k + 1}", hex(p["block"] + k * p["stride"] + p["rounds"]), 1, "tally"), got)
        self.assertEqual(res["skipped"]["no constant RAM write"], 1)       # the Game Genie code

    def test_no_description_text_in_any_output(self):
        for system in ("ps1", "snes"):
            text = F.cht(system)
            path = self.write(f"{system}_d.cht", text)
            words = {w.casefold() for d in descriptions(text) for w in re.findall(r"[A-Za-z]{4,}", d)} - VOCABULARY
            self.assertTrue(words)
            for args in ([], ["--counts"]):
                r = subprocess.run([sys.executable, "-I", "-B", str(HINTS), "--system", system, "--cheats", str(path),
                                    *args], capture_output=True, text=True, timeout=60)
                out = r.stdout.casefold()
                self.assertEqual(r.returncode, 0)
                for d in descriptions(text):
                    self.assertNotIn(d.casefold(), out)
                for w in words:
                    self.assertNotIn(w, out, (system, args))
                if args:
                    self.assertNotIn("0x", out)                             # counts only: no address

    def test_unreadable_or_empty_files_give_no_hints(self):
        cases = {"empty.cht": "", "garbage.cht": bytes(range(256)) * 8, "not_a_list.cht": "hello\nworld\n"}
        for name, data in cases.items():
            res = ch.read_hints(self.write(name, data), "ps1")
            self.assertEqual(res["hints"], [], name)
            self.assertTrue(res["unreadable"], name)
        res = ch.read_hints(self.tmp / "missing.cht", "ps1")
        self.assertEqual(res["hints"], [])
        self.assertTrue(res["unreadable"])


def st(label, winner, pairs, size=4096):
    m = bytearray(size)
    for a, v in pairs.items():
        m[a] = v
    return {"label": label, "winner": winner, "mem": bytes(m), "stable": np.ones(size, dtype=bool)}


class SearchWithHints(unittest.TestCase):
    """Made-up memories: a planted counter (0x100 / 0x110), a smaller-stride counter that ranks first by the order
    (0x200 / 0x208), a level whose loser is above 0 in one end (0x300 / 0x310), a score pair no template finds (0x400 /
    0x410) and a hinted pair that fails P2's state (0x500 / 0x510)."""
    FACTS = {"begin": {0x100: (0, 0), 0x200: (0, 0), 0x300: (120, 120), 0x400: (0, 0), 0x500: (3, 3)},
             "P1": {0x100: (2, 1), 0x200: (3, 1), 0x300: (40, 0), 0x400: (200, 100), 0x500: (7, 2)},
             "P2": {0x100: (1, 2), 0x200: (1, 3), 0x300: (0, 70), 0x400: (90, 150), 0x500: (6, 4)},
             "P1b": {0x100: (2, 0), 0x200: (2, 1), 0x300: (90, 30), 0x400: (180, 60), 0x500: (8, 1)},
             "P2b": {0x100: (0, 2), 0x200: (0, 1), 0x300: (10, 50), 0x400: (40, 250), 0x500: (2, 1)}}
    STRIDE = {0x100: 0x10, 0x200: 0x8, 0x300: 0x10, 0x400: 0x10, 0x500: 0x10}

    def states(self, *names):
        out = []
        for n in names:
            pairs = {}
            for base, (x, y) in self.FACTS[n].items():
                pairs[base], pairs[base + self.STRIDE[base]] = x, y
            out.append(st(*(("begin", None) if n == "begin" else ("end", n[:2])), pairs))
        return out

    HINTS = [{"player": "P1", "address": "0x100", "bytes": 1, "value": 2, "kind": "tally", "code": 0, "pair_group": 0},
             {"player": "P2", "address": "0x110", "bytes": 1, "value": 2, "kind": "tally", "code": 1, "pair_group": 0},
             {"player": "P1", "address": "0x400", "bytes": 1, "value": 255, "kind": "tally", "code": 2, "pair_group": 1},
             {"player": "P2", "address": "0x410", "bytes": 1, "value": 255, "kind": "tally", "code": 3, "pair_group": 1},
             {"player": "P1", "address": "0x500", "bytes": 1, "value": 9, "kind": "tally", "code": 4, "pair_group": 2},
             {"player": "P2", "address": "0x510", "bytes": 1, "value": 9, "kind": "tally", "code": 5, "pair_group": 2},
             {"player": "P1", "address": "0x300", "bytes": 1, "value": 120, "kind": "level", "code": 6, "pair_group": 3},
             {"player": "P2", "address": "0x310", "bytes": 1, "value": 120, "kind": "level", "code": 7, "pair_group": 3}]

    def first(self, out, t):
        return [p["address"] for p in out["templates"][t]["passing"][0]["rule"]["players"]]

    def test_the_hinted_family_is_ranked_first_with_three_states(self):
        three = self.states("begin", "P1", "P2")
        self.assertEqual(self.first(search.search(three, 2), "a"), ["0x200", "0x208"])     # by the order alone
        out = search.search(three, 2, self.HINTS)
        self.assertEqual(self.first(out, "a"), ["0x100", "0x110"])                          # the hinted one first
        self.assertTrue(out["templates"]["a"]["passing"][0]["hinted"])
        self.assertEqual({h["code"] for h in out["templates"]["a"]["passing"][0]["hinted_by"]}, {0, 1})
        self.assertFalse(out["decided"])                                                     # still weak: a hint is
        self.assertEqual(out["evidence"], "weak")                                           # evidence, not a verdict

    def test_a_hinted_pair_no_template_found_is_tested_directly(self):
        out = search.search(self.states("begin", "P1", "P2", "P1b", "P2b"), 2, self.HINTS)
        score = [s for s in out["hinted_sets"]["sets"] if [p["address"] for p in s["rule"]["players"]] == ["0x400", "0x410"]]
        self.assertEqual(len(score), 1)
        self.assertTrue(score[0]["holds"])
        self.assertEqual(score[0]["found_by"], [])
        self.assertEqual(score[0]["values_per_state"], [[0, 0], [200, 100], [90, 150], [180, 60], [40, 250]])
        for t in ("a", "b", "b2"):
            self.assertNotIn(["0x400", "0x410"], [[p["address"] for p in f["rule"]["players"]]
                                                  for f in out["templates"][t]["families"]])
        self.assertIn(["0x400", "0x410"], [[p["address"] for p in f["rule"]["players"]]
                                           for f in out["templates"]["h"]["passing"]])
        self.assertEqual(out["templates"]["h"]["evidence"]["level"], "strong")
        self.assertEqual((out["template"], [p["address"] for p in out["rule"]["players"]]), ("a", ["0x100", "0x110"]))

    def test_the_decoy_hint_fails_a_state_and_is_not_chosen(self):
        out = search.search(self.states("begin", "P1", "P2"), 2, self.HINTS)
        decoy = [s for s in out["hinted_sets"]["sets"] if [p["address"] for p in s["rule"]["players"]] == ["0x500", "0x510"]]
        self.assertEqual(len(decoy), 1)
        self.assertFalse(decoy[0]["holds"])
        self.assertEqual(decoy[0]["failing_states"], [2])                                    # P2's end
        for t in out["templates"].values():
            self.assertNotIn(["0x500", "0x510"], [[p["address"] for p in f["rule"]["players"]] for f in t["passing"]])

    def test_b2_holds_where_the_loser_is_above_0(self):
        out = search.search(self.states("begin", "P1", "P2", "P1b", "P2b"), 2)
        b2 = [[p["address"] for p in f["rule"]["players"]] for f in out["templates"]["b2"]["passing"]]
        b = [[p["address"] for p in f["rule"]["players"]] for f in out["templates"]["b"]["families"]]
        self.assertIn(["0x300", "0x310"], b2)
        self.assertNotIn(["0x300", "0x310"], b)                                              # (b) needs the loser at 0
        self.assertEqual(out["templates"]["b2"]["evidence"]["level"], "strong")
        self.assertEqual(out["template"], "a")                                               # b2 answers after a, b, c
        out3 = search.search(self.states("begin", "P1", "P2"), 2)
        self.assertIn(["0x300", "0x310"], [[p["address"] for p in f["rule"]["players"]]
                                           for f in out3["templates"]["b"]["families"]])     # every b also fits b2
        self.assertIn(["0x300", "0x310"], [[p["address"] for p in f["rule"]["players"]]
                                           for f in out3["templates"]["b2"]["families"]])

    def test_the_hinted_b2_family_is_the_answer_when_a_and_b_have_none(self):
        facts = {n: {0x300: v[0x300]} for n, v in self.FACTS.items()}
        old = self.FACTS
        try:
            self.FACTS = facts
            out = search.search(self.states("begin", "P1", "P2", "P1b", "P2b"), 2, self.HINTS)
        finally:
            self.FACTS = old
        self.assertTrue(out["decided"])
        self.assertEqual(out["template"], "b2")
        self.assertTrue(out["templates"]["b2"]["passing"][0]["hinted"])

    def test_b2_pairs_equal_the_stride_loop(self):                    # addendum 1
        rng = np.random.default_rng(5)
        for players, labels in ((2, (("begin", None), ("end", "P1"), ("end", "P2"), ("end", "P1"))),
                                (4, (("begin", None), ("end", "P1"), ("end", "P3")))):
            states = []
            for n, (lab, w) in enumerate(labels):
                m = rng.integers(0, 256, 0x8000, dtype=np.uint8)
                lv = [120] * players if lab == "begin" else [0] * players
                if w:
                    lv[int(w[1]) - 1] = 50
                    lv[(int(w[1])) % players] = 20 + n                  # a loser above 0
                for k in range(players):
                    m[0x4000 + k * 0x30] = lv[k]
                states.append({"label": lab, "winner": w, "mem": m.tobytes(), "stable": np.ones(0x8000, dtype=bool)})
            ctx = search._Ctx(states, players)
            ctx.sets = []
            idx = list(range(len(states)))
            begins = [i for i in idx if ctx.label[i] == "begin"]
            ends = [(i, ctx.win[i]) for i in idx if ctx.label[i] == "end"]
            got = {}
            old = search.B2_PAIRS
            try:
                for flag in (True, False):
                    search.B2_PAIRS = flag
                    got[flag] = sorted((c["size"], c["base"], c["stride"]) for c in
                                       search._block(ctx, idx, begins, ends, "b2"))
            finally:
                search.B2_PAIRS = old
            self.assertEqual(got[True], got[False], players)
            self.assertIn((1, 0x4000, 0x30), got[True])

    def test_b2_over_its_cap_is_not_testable_and_the_rest_unchanged(self):     # addendum 2
        states = self.states("begin", "P1", "P2", "P1b", "P2b")
        plain = search.search(states, 2)
        self.assertGreater(plain["templates"]["b2"]["count"], 0)
        old = search.B2_CAP
        try:
            search.B2_CAP = 0
            out = search.search(states, 2)
        finally:
            search.B2_CAP = old
        b2 = out["templates"]["b2"]
        self.assertIn("too many (b2) candidates", b2["not_testable"])
        self.assertEqual((b2["count"], b2["evidence"]["level"]), (None, "none"))
        self.assertTrue(all(r["skipped"] for r in b2["folds"]))
        for k in ("a", "b", "c"):
            self.assertEqual(json.dumps(out["templates"][k], sort_keys=True),
                             json.dumps(plain["templates"][k], sort_keys=True))
        self.assertEqual((out["decided"], out["template"]), (True, "a"))

    def test_no_hints_from_an_unreadable_or_empty_file_and_the_search_as_without(self):
        tmp = Path(tempfile.mkdtemp(prefix="h7_hints_search_"))
        try:
            states = self.states("begin", "P1", "P2", "P1b", "P2b")
            plain = search.search(states, 2)
            for name, data in (("empty.cht", b""), ("garbage.cht", bytes(range(256)) * 4)):
                (tmp / name).write_bytes(data)
                hints, info = search.load_hints(tmp / name, "ps1")
                self.assertEqual(hints, [])
                self.assertEqual(info["read"], 0)
                self.assertTrue(info["why"])
                out = search.search(states, 2, hints)
                self.assertEqual(json.dumps(out, sort_keys=True), json.dumps(plain, sort_keys=True))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
