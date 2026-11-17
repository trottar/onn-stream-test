#!/usr/bin/env python3
"""B131 (host): the onn's SAVE / LOAD while a hub mini game is starting or playing — through the real HTTP server on
loopback, behind PRIVYHUB_PARTY=1 (and PRIVYHUB_H7=1 for the mini games).

B127's run of B114's scenario (B108's stand-in board, B101 / B103's fake RetroArch reading the session config's states
folder, the two titles under fake cheat setups made by the onn's Extras launch, the onn's thread and the calls every
0.1 s), with a SAVE (slot 1, and `replace=true`) and a LOAD (slot 1) sent during each mini game — the two-player one
under the PS1 setup and the four-player one under the N64 setup: each **400 "not during a mini game: nothing was
saved" / "… loaded"**, one `minigame_state_refused` row each, **nothing sent to the title** (the fake's command log),
the mini game still playing and ended as without them, **every setup file byte-equal**. After the mini games, with the
board the session, today's path (the board's own refusal) — the same answers as HEAD's companion; the flags absent (and
with them on, no mini game) → HEAD's answers through the real routes. Temp dirs removed.

    python3 -m unittest discover -s tests/b131_party_save_load -v
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("b114_party_minigame_hang", "b124_party_four_seats", "b127_party_cheat_setups", "b115_party_handovers"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import test_b114 as b114  # noqa: E402  (harnesses; their tests are not collected here)
import test_b124 as b124  # noqa: E402
import test_b127 as b127  # noqa: E402

HEAD = "1fc0ced0"
SAVED = "not during a mini game: nothing was saved"
LOADED = "not during a mini game: nothing was loaded"
BOARD = "Saving and loading are not offered for the board game; nothing was sent."


def extra_saveload(work, frames):
    return {**b124.extra(work, frames), "saveload": True}


def extra_board(work, frames):
    return {"board_saveload": True}


class DuringAMiniGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b114.b99.tree()
        b124.IDS.clear()
        b124.IDS.update(ids)
        cls.out = b114.run(root, b114.BOTH, ids, "cheat", extra=extra_saveload)
        cls.s = cls.out["steps"]

    def test_0_refused_plainly_with_a_row_nothing_sent(self):
        self.assertIsNone(self.out["hung"])
        for tag, state in (("ca2", "playing"), ("cb4", "playing")):
            sl = self.s[tag + "_saveload"]
            for k, line in (("save", SAVED), ("save_replace", SAVED), ("load", LOADED)):
                self.assertEqual((sl[k]["code"], sl[k]["body"].get("error")), (400, line), (tag, k))
            self.assertEqual(self.s[tag + "_saveload_sent"], [], tag)
            self.assertEqual(self.s[tag + "_saveload_rows"],
                             [{"step": "minigame_state_refused", "what": w, "state": state}
                              for w in ("save", "save", "load")], tag)
            self.assertEqual(self.s[tag + "_state_after_saveload"], "playing", tag)

    def test_1_the_mini_games_end_as_without_them(self):
        a, b = self.s["ca2"], self.s["cb4"]
        self.assertEqual((a["state"], a["class"], a["scores"]), ("ended", "end_P2", [0, 1]))
        self.assertEqual((b["state"], b["places"], b["scores"]), ("ended", [2, 1, 4, 3], [3, 4, 1, 2]))

    def test_2_every_setup_file_byte_equal(self):
        self.assertTrue(self.s["c_files_same"], self.s["c_files_diff"])
        self.assertEqual(self.s["c_scratch_end"], [])

    def test_3_after_the_mini_games_the_boards_own_refusal(self):
        for k in ("save", "load"):
            r = self.s["c_board_saveload"][k]
            self.assertEqual((r["code"], r["body"].get("error")), (503, BOARD), k)


def masked(step):
    return step["code"], b127.MASK.sub("<n>", b114.CLOCK.sub("<ms>", step["raw"]))


class Today(unittest.TestCase):
    def test_flags_absent_and_no_mini_game_are_heads(self):
        code = b114.code_of(HEAD)
        if code is None:
            self.skipTest("git is absent")
        envs = ({**b114.b85.FLAGS, **b114.ADOPTED}, {**b114.b85.FLAGS, **b114.ADOPTED, "PRIVYHUB_H7": "1"},
                {**b114.b85.FLAGS, **b114.ADOPTED, "PRIVYHUB_PARTY": "1"}, b114.BOTH)
        for env in envs:
            root, ids = b114.b99.tree(code)
            base = b114.run(root, env, ids, "cheat_today", extra=extra_board)["steps"]
            root2, ids2 = b114.b99.tree()
            mine = b114.run(root2, env, ids2, "cheat_today", extra=extra_board)["steps"]
            routes = [k for k in base if isinstance(base[k], dict) and "code" in base[k]]
            self.assertEqual(sorted(routes), sorted(k for k in mine if isinstance(mine[k], dict) and "code" in mine[k]))
            for k in routes:
                self.assertEqual(masked(mine[k]), masked(base[k]), (sorted(env), k))
            if env.get("PRIVYHUB_PARTY") == "1":
                self.assertEqual((base["board_save"]["code"], base["board_save"]["body"].get("error")), (503, BOARD))
                self.assertEqual((base["board_load"]["code"], base["board_load"]["body"].get("error")), (503, BOARD))


if __name__ == "__main__":
    unittest.main()
