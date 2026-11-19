#!/usr/bin/env python3
"""B155 (host): the `minigame_launch` row carries "keys_written" — through the real HTTP server on loopback, behind
PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1.

PP-H4's C cell read the session config's two keys at three of seven launches (each launch rewrites the file). B155: the
party layer reads the session config back after each of its launches — written by that launch, each of
PARTY_SESSION_SETTINGS's keys there once with its value → `"keys_written": true`.

B114's harness, its `b155` mode: a held party launch (true; the file's two lines); a second with the emulator's write
made keyless after the fact (false: the read is real, not the arm); a users' launch of the same title (no minigame row,
no field; its config without the keys). The flags absent: the routes as HEAD's (B114's `today` mode, the same answers
on HEAD's code and mine). Temp dirs removed.

    python3 -m unittest discover -s tests/b155_party_keys_written -v
"""
from __future__ import annotations

import json
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

BASELINE = "d7a99b62"
LINES = ['video_font_enable = "false"', 'menu_show_load_content_animation = "false"']


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


class KeysWritten(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = run_mode("b155", b114.BOTH)

    def test_party_launch_true(self):
        rows = self.s["b155a_launch_rows"]
        self.assertEqual(len(rows), 1, rows)
        self.assertIs(rows[0].get("keys_written"), True, rows)
        self.assertTrue(rows[0].get("pid_owned"), rows)
        self.assertEqual(sorted(self.s["b155a_lines"]), sorted(LINES))

    def test_a_keyless_write_reads_false(self):
        rows = self.s["b155b_launch_rows"]
        self.assertEqual(len(rows), 1, rows)
        self.assertIs(rows[0].get("keys_written"), False, rows)
        self.assertEqual(self.s["b155b_lines"], [])

    def test_users_launch_no_field(self):
        self.assertEqual(self.s["b155_users_launch"], 200)
        self.assertEqual(self.s["b155_users_rows"], [])
        self.assertEqual(self.s["b155_users_lines"], [])


class FlagsAbsent(unittest.TestCase):
    """B114's `today` mode with the flags absent: every answer the same on HEAD's code and mine."""

    def test_today_the_same(self):
        env = {**b114.b85.FLAGS, **b114.ADOPTED}                      # the hub's adopted flags, the party's absent
        mine = run_mode("today", env)
        head = run_mode("today", env, BASELINE)
        for k in ("list", "start", "result", "end", "go", "status_idle", "home_idle", "stop_idle"):
            self.assertEqual((mine[k]["code"], b114.CLOCK.sub("<ms>", mine[k]["raw"])),
                             (head[k]["code"], b114.CLOCK.sub("<ms>", head[k]["raw"])), k)
        self.assertEqual(mine["ports_today"], head["ports_today"])
        self.assertEqual(mine["b139_users_cfg"], head["b139_users_cfg"])      # the users' launch's config
        self.assertEqual(mine["b139_users_cfg"]["keys"], {})


if __name__ == "__main__":
    unittest.main()
