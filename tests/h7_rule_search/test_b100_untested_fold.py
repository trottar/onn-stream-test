#!/usr/bin/env python3
"""B100 (host, no emulator): a fold whose training search was "not testable" (over a cap) is not a fold passed — the
template reads at most "weak", the words say why; a fold skipped for want of another example of its winner is as
before. H7-P3's shape on made-up memory (B98's) plus a block of fixed pseudo-random bytes, so (b2) finds more on four
states than on five. Temp dirs: none.

    python3 -m unittest discover -s tests/h7_rule_search -p 'test_b100_untested_fold.py' -v
"""
from __future__ import annotations

import json
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))
import h7_rule_search as search  # noqa: E402
import test_b98_acceptance as b98  # noqa: E402  (a module: its tests are not collected twice)


def shape_with_noise() -> list[dict]:
    states = b98.states()
    rnd = random.Random(100)
    for s in states:
        m = bytearray(s["mem"])
        m[0x800:0x1000] = bytes(rnd.randrange(256) for _ in range(0x800))
        s["mem"] = bytes(m)
    return states


def testable(states, idx, cap) -> bool:
    """Whether (b2)'s search on the states `idx` stays under `cap` (the cap counts candidates before merging)."""
    old = search.B2_CAP
    try:
        search.B2_CAP = cap
        ctx = search._Ctx(states, 2)
        begins = [i for i in idx if ctx.label[i] == "begin"]
        ends = [(i, ctx.win[i]) for i in idx if ctx.label[i] == "end"]
        return isinstance(search._block(ctx, idx, begins, ends, "b2"), list)
    finally:
        search.B2_CAP = old


def b2_caps(states) -> tuple[int, list[int]]:
    """The smallest cap at which (b2) is testable on all five states, and on each four-state training set."""
    def least(idx):
        lo, hi = 0, 1
        while not testable(states, idx, hi):
            hi *= 2
        while lo < hi:
            mid = (lo + hi) // 2
            lo, hi = (mid + 1, hi) if not testable(states, idx, mid) else (lo, mid)
        return lo
    every = list(range(len(states)))
    ends = [i for i in every if states[i]["label"] == "end"]
    return least(every), [least([j for j in every if j != e]) for e in ends]


class UntestedFold(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states = shape_with_noise()
        cls.full, cls.train = b2_caps(cls.states)

    def search(self, cap, loose=False):
        old, old_loose = search.B2_CAP, search.ACCEPT_LOOSE
        try:
            search.B2_CAP, search.ACCEPT_LOOSE = cap, loose
            return search.search(self.states, 2, b98.HINTS)
        finally:
            search.B2_CAP, search.ACCEPT_LOOSE = old, old_loose

    def cap_between(self) -> int:
        """H7-P3's case: the cap at the smallest four-state need — that fold runs, the others are not tested."""
        cap = min(self.train)
        self.assertGreaterEqual(cap, self.full)
        self.assertGreater(max(self.train), cap, self.train)
        return cap

    def test_the_counts_make_the_case(self):
        print(f"\nB100 (b2) least cap: five states {self.full}, four-state training sets {self.train}", file=sys.stderr)
        self.assertGreater(max(self.train), min(self.train))
        self.assertGreaterEqual(min(self.train), self.full)

    def test_a_template_with_a_fold_not_tested_is_weak(self):
        out = self.search(self.cap_between())
        b2 = out["templates"]["b2"]
        ev = b2["evidence"]
        untested = [r for r in b2["folds"] if r.get("not_tested")]
        self.assertTrue(untested)
        self.assertGreaterEqual(ev["folds_run"], 1)                                     # H7-P3's: some ran, some not
        self.assertEqual(ev["folds_not_tested"], len(untested))
        self.assertTrue(all(r["skipped"] for r in untested))
        self.assertEqual(ev["level"], "weak")
        self.assertIn("could not be tested", ev["words"])
        self.assertIn("a fold not tested is not a fold passed", ev["words"])
        self.assertIn("over its cap", ev["would_make_strong"])
        self.assertGreater(b2["passing_count"], 0)

    def test_with_the_cap_out_of_reach_b2_is_strong(self):
        out = self.search(10 ** 9)
        self.assertEqual(out["templates"]["b2"]["evidence"]["level"], "strong")
        self.assertNotIn("folds_not_tested", out["templates"]["b2"]["evidence"])

    def test_the_hinted_pairs_answer_is_unchanged(self):
        capped, free = self.search(self.cap_between()), self.search(10 ** 9)
        for out in (capped, free):
            self.assertTrue(out["decided"])
            self.assertEqual(out["template"], "h")
            self.assertEqual([p["address"] for p in out["rule"]["players"]], ["0x500", "0x510"])
        self.assertNotIn("b2", [x["template"] for x in capped["not_accepted"]])          # weak: not an answer at all
        self.assertIn("b2", [x["template"] for x in free["not_accepted"]])               # strong, loose: not accepted

    def test_accept_loose_against_b97_differs_only_where_a_fold_is_not_tested(self):
        old = b98.b97_search()
        if old is None:
            self.skipTest("git or B97's commit is absent")
        cap = self.cap_between()
        prev = old.B2_CAP
        try:
            old.B2_CAP = cap
            theirs = old.search(self.states, 2, b98.HINTS)
        finally:
            old.B2_CAP = prev
        mine = self.search(cap, loose=True)
        self.assertEqual(theirs["templates"]["b2"]["evidence"]["level"], "strong")       # B97: strong on 1 of 4
        self.assertEqual(mine["templates"]["b2"]["evidence"]["level"], "weak")           # B100: weak
        for k in ("a", "b", "c", "h"):                                                  # every other template equal
            self.assertEqual(json.dumps(theirs["templates"][k]), json.dumps(mine["templates"][k]), k)
        strip = lambda o: {k: v for k, v in o.items() if k not in ("templates", "also_fits")}
        self.assertEqual(json.dumps(strip(theirs)), json.dumps(strip(mine)))                # the answer: h in both

    def test_no_other_example_is_as_before(self):
        out = search.search(b98.states()[:3], 2, b98.HINTS)                             # begin + P1 + P2
        for k in ("a", "b", "b2", "h"):
            ev = out["templates"][k]["evidence"]
            self.assertNotIn("folds_not_tested", ev)
            if ev["level"] == "weak":
                self.assertIn("no other example of that winner", ev["words"])


if __name__ == "__main__":
    unittest.main()
