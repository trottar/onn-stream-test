#!/usr/bin/env python3
"""B158 (host): winner-only results — through the real HTTP server on loopback, behind PRIVYHUB_PARTY=1 and
PRIVYHUB_H7=1.

A sidecar's `"result": "winner"`: the scores one-hot for the winner (a version-2 spec: end_Pk = port k won; a
version-3 spec: the port that read place 1), the ended row and the result carry `"winner"` — that port's seat, from
the seats given. Without the key: today.

B114's harness, its `winner158` mode: the made-up two-player title (end P1 with seats 1,2; end P2 with seats 2,1) and
B124's made-up four-player title (the row 2143 with seats 3,1,4,2), both with `"result": "winner"`; then sidecars that
must not be listed (`result` with `scores` / `places_to_scores`; `result` another word). T88's and T89's own files are
never touched (their sha256 read before and after, read only). The flags absent: B114's `today` routes the same on
HEAD's code and mine. Temp dirs removed.

    python3 -m unittest discover -s tests/b158_winner_only -v
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "b114_party_minigame_hang"))
sys.path.insert(0, str(ROOT / "tests" / "b124_party_four_seats"))
import test_b114 as b114  # noqa: E402  (its harness; its tests are not collected here)
import test_b124 as b124  # noqa: E402

BASELINE = "3a9de095"


def run_mode(mode: str, env: dict, code_rev: str | None = None) -> dict:
    code = b114.code_of(code_rev) if code_rev else None
    if code_rev and code is None:
        raise unittest.SkipTest("git is absent")
    root, ids = b114.b99.tree(code)
    try:
        b124.IDS.clear()
        b124.IDS.update(ids)
        return b114.run(root, env, ids, mode, extra=b124.extra)["steps"]
    finally:
        shutil.rmtree(root, ignore_errors=True)
        if code is not None:
            shutil.rmtree(code, ignore_errors=True)


def kept_rules_digest() -> list:
    """The hub's own rules folder, read only: every sidecar's and spec's sha256 (no name kept, only the digests)."""
    folder = Path(os.environ.get("B158_KEPT_RULES", str(Path.home() / "privyhub_h7" / "rules")))
    if not folder.is_dir():
        return []
    return sorted(hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()
                  if p.name.endswith((".party.json", ".endscreen.json")))


class WinnerOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kept_before = kept_rules_digest()
        cls.s = run_mode("winner158", b114.BOTH)
        cls.kept_after = kept_rules_digest()

    def test_0_both_listed(self):
        self.assertEqual(self.s["w_list"], [2, 4])

    def test_1_two_players(self):
        a, b = self.s["w2a"], self.s["w2b"]
        self.assertEqual((a["state"], a["class"], a["scores"], a.get("winner")), ("ended", "end_P1", [1, 0], 1), a)
        self.assertEqual((b["state"], b["class"], b["scores"], b.get("winner")), ("ended", "end_P2", [0, 1], 1), b)
        self.assertEqual([(r["scores"], r.get("winner")) for r in self.s["w2a_ended_rows"]], [([1, 0], 1)])
        self.assertEqual([(r["scores"], r.get("winner")) for r in self.s["w2b_ended_rows"]], [([0, 1], 1)])

    def test_2_four_players_place_one_wins(self):
        r = self.s["w4"]
        # the row 2143 by port; seats 3,1,4,2 -> port 2 read place 1 -> seat 1 won; scores in the seats' order
        self.assertEqual((r["state"], r.get("places"), r["scores"], r.get("winner")),
                         ("ended", [2, 1, 4, 3], [0, 1, 0, 0], 1), r)
        rows = self.s["w4_ended_rows"]
        self.assertEqual([(x["places"], x["scores"], x.get("winner")) for x in rows], [([2, 1, 4, 3], [0, 1, 0, 0], 1)])

    def test_3_malformed_not_listed(self):
        self.assertEqual(self.s["w_list_both"], [])
        self.assertEqual(self.s["w_list_word"], [])

    def test_4_the_kept_rules_untouched(self):
        self.assertEqual(self.kept_before, self.kept_after)


class TodayUnchanged(unittest.TestCase):
    """The flags absent (the hub's adopted flags only): B114's `today` routes the same on HEAD's code and mine."""

    def test_today_the_same(self):
        env = {**b114.b85.FLAGS, **b114.ADOPTED}
        mine = run_mode("today", env)
        head = run_mode("today", env, BASELINE)
        for k in ("list", "start", "result", "end", "go", "status_idle", "home_idle", "stop_idle"):
            self.assertEqual((mine[k]["code"], b114.CLOCK.sub("<ms>", mine[k]["raw"])),
                             (head[k]["code"], b114.CLOCK.sub("<ms>", head[k]["raw"])), k)


if __name__ == "__main__":
    unittest.main()
