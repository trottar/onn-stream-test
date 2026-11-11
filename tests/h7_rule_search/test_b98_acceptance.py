#!/usr/bin/env python3
"""B98 (host, no emulator): the acceptance rule in the search — a strong answer decides only when its template is a or
b, its family is hinted, or it is a hinted set (h); (b2) and (c) answers are listed as not accepted, with the reason.
`--accept-loose` gives B97's output byte for byte (B97's search read from its commit with `git show`; skipped without
git). Made-up memories only; temp dirs removed.

    python3 -m unittest discover -s tests/h7_rule_search -p 'test_b98_acceptance.py' -v
"""
from __future__ import annotations

import importlib.util
import json
import os
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
import h7_rule_search as search  # noqa: E402
import test_h7_cheat_hints as hint_tests  # noqa: E402  (a module, so its tests are not collected twice)

B97_COMMIT = "a5383e3b"          # queue AJ: B96 + B97's search, the version --accept-loose must equal


def b97_search():
    """B97's tools/h7_rule_search.py as a module, read from its commit; None without git or the commit."""
    try:
        repo = os.environ.get("H7_GIT_REPO") or str(ROOT)       # a test work copy is not a git repo: its runner says where
        text = subprocess.run(["git", "-C", repo, "show", f"{B97_COMMIT}:tools/h7_rule_search.py"],
                              capture_output=True, text=True, timeout=60, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    tmp = Path(tempfile.mkdtemp(prefix="b98_b97_"))
    try:
        path = tmp / "h7_rule_search_b97.py"
        path.write_text(text)
        spec = importlib.util.spec_from_file_location("h7_rule_search_b97", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def loose_equal(test: unittest.TestCase, old, cases):
    """Each case (states, players, hints): B97's output and this search's with ACCEPT_LOOSE, as JSON, equal."""
    prev = search.ACCEPT_LOOSE
    try:
        search.ACCEPT_LOOSE = True
        for n, (states, players, hints) in enumerate(cases):
            a = json.dumps(old.search(states, players, hints))
            b = json.dumps(search.search(states, players, hints))
            test.assertEqual(a, b, n)
    finally:
        search.ACCEPT_LOOSE = prev


def st(label, winner, pairs, size=4096):
    m = bytearray(size)
    for a, v in pairs.items():
        m[a] = v
    return {"label": label, "winner": winner, "mem": bytes(m), "stable": np.ones(size, dtype=bool)}


NAMES = ("begin", "P1", "P2", "P1b", "P2b")
# H7-P3's shape: a counter (a), a level that empties (b), a single field (c), a level whose loser stays above 0 (b2),
# a pair no template finds that the cheat list names (h)
SHAPE = {0x100: [(0, 0), (2, 1), (1, 2), (2, 0), (0, 2)],
         0x200: [(120, 120), (40, 0), (0, 70), (90, 0), (0, 50)],
         0x300: [255, 0, 1, 0, 1],
         0x400: [(100, 100), (60, 30), (20, 80), (90, 10), (40, 70)],
         0x500: [(0, 0), (140, 70), (133, 140), (140, 100), (110, 140)]}
HINTS = [{"player": "P1", "address": "0x500", "bytes": 1, "value": 140, "kind": "level", "code": 0, "pair_group": 0},
         {"player": "P2", "address": "0x510", "bytes": 1, "value": 140, "kind": "level", "code": 1, "pair_group": 0}]


def states(keep=tuple(SHAPE)):
    out = []
    for i, n in enumerate(NAMES):
        pairs = {}
        for base in keep:
            v = SHAPE[base][i]
            if isinstance(v, tuple):
                pairs[base], pairs[base + 0x10] = v
            else:
                pairs[base] = v
        out.append(st(*(("begin", None) if n == "begin" else ("end", n[:2])), pairs))
    return out


def addrs(rule):
    return [p["address"] for p in rule["players"]] if rule.get("players") else [rule["address"]]


class Acceptance(unittest.TestCase):
    def test_h7_p3s_shape_answers_the_hinted_set(self):
        out = search.search(states(), 2, HINTS)
        levels = {k: out["templates"][k]["evidence"]["level"] for k in ("a", "b", "c", "b2", "h")}
        self.assertEqual(set(levels.values()), {"strong"}, levels)
        self.assertTrue(out["decided"])
        self.assertTrue(out["accepted"])
        self.assertEqual(out["template"], "h")
        self.assertEqual(addrs(out["rule"]), ["0x500", "0x510"])
        self.assertFalse(out["ranking_pick"])
        self.assertEqual(out["ranking_pick_count"], 1)
        self.assertEqual([x["template"] for x in out["also_fits"]], ["a", "b"])
        na = {x["template"]: x for x in out["not_accepted"]}
        self.assertEqual(set(na), {"c", "b2"})
        for k in ("c", "b2"):
            self.assertEqual((na[k]["level"], na[k]["accepted"]), ("strong", False))
            self.assertIn(f"({k})", na[k]["why_not"])

    def test_only_b2_strong_without_hints_is_not_decided(self):
        out = search.search(states((0x400,)), 2)
        self.assertEqual(out["templates"]["b2"]["evidence"]["level"], "strong")
        self.assertFalse(out["decided"])
        self.assertFalse(out["accepted"])
        self.assertNotIn("rule", out)
        self.assertEqual([x["template"] for x in out["not_decided"]["not_accepted"]], ["b2"])
        self.assertIn("loosest", out["not_decided"]["why"])

    def test_c_alone_strong_is_not_accepted(self):
        out = search.search(states((0x300,)), 2)
        self.assertEqual(out["templates"]["c"]["evidence"]["level"], "strong")
        self.assertFalse(out["decided"])
        self.assertEqual([x["template"] for x in out["not_decided"]["not_accepted"]], ["c"])
        self.assertIn("single field", out["not_decided"]["why"])

    def test_a_hinted_b2_family_still_decides(self):
        hints = [dict(h, address=a) for h, a in zip(HINTS, ("0x400", "0x410"))]
        out = search.search(states((0x400,)), 2, hints)
        self.assertTrue(out["decided"])
        self.assertEqual(out["template"], "b2")                    # hinted: accepted, and first by the order
        self.assertEqual(addrs(out["rule"]), ["0x400", "0x410"])

    def test_a_ranking_pick_is_said(self):
        two = {0x100: SHAPE[0x100], 0x600: [(0, 0), (3, 1), (1, 3), (3, 0), (0, 3)]}   # two counters pass
        out = search.search([st(*(("begin", None) if n == "begin" else ("end", n[:2])),
                                {**{b: v[i][0] for b, v in two.items()},
                                 **{b + 0x10: v[i][1] for b, v in two.items()}}) for i, n in enumerate(NAMES)], 2)
        self.assertEqual(out["template"], "a")
        self.assertGreater(out["templates"]["a"]["passing_count"], 1)
        self.assertTrue(out["ranking_pick"])
        self.assertEqual(out["ranking_pick_count"], out["templates"]["a"]["passing_count"])
        self.assertIn("not a unique fit", out["ranking_pick_words"])

    def test_accept_loose_restores_b97s_answer(self):
        prev = search.ACCEPT_LOOSE
        try:
            search.ACCEPT_LOOSE = True
            out = search.search(states((0x400,)), 2)
        finally:
            search.ACCEPT_LOOSE = prev
        self.assertTrue(out["decided"])
        self.assertEqual(out["template"], "b2")
        self.assertNotIn("accepted", out)

    def test_the_cli_flag(self):
        r = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tools/h7_rule_search.py"), "--help"],
                           capture_output=True, text=True, timeout=60)
        self.assertIn("--accept-loose", r.stdout)


@unittest.skipUnless(b97_search() is not None, "git or B97's commit is absent")
class LooseIsB97ByteForByte(unittest.TestCase):
    def test_on_b97s_made_up_memories(self):
        old = b97_search()
        f = hint_tests.SearchWithHints()
        cases = []
        for names in (("begin", "P1", "P2"), ("begin", "P1", "P2", "P1b", "P2b")):
            for hints in (None, hint_tests.SearchWithHints.HINTS):
                cases.append((f.states(*names), 2, hints))
        cases += [(states(), 2, HINTS), (states(), 2, None), (states((0x400,)), 2, None), (states((0x300,)), 2, None)]
        loose_equal(self, old, cases)


if __name__ == "__main__":
    unittest.main()
