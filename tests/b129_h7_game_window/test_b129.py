#!/usr/bin/env python3
"""B129 (host): the watcher reads the game's own window — through the real HTTP server on loopback, behind
PRIVYHUB_H7=1.

B103's harness (B101's fake RetroArch, the made-up titles, B103's spec and pictures) with the watcher's own
`WindowPicture` against **a fake window table** (the `xdotool` calls answered from it) and **a fake screen** (Pillow's
grab returns a 1920 x 1080 desktop picture with the game's picture pasted at its window's place). Checked: a full-screen
game → (0, 0, 1920, 1080) as today, `recognised` true; **then a windowed game in the same companion (H7-V5's order) →
its own rectangle (960, 384, 960, 720)**, `recognised` true (today: the first game's rectangle — the desktop — never
the start); a larger window listed for the process but owned by another → the game's own window; no window owned by
the process (none, or only another's) → `picture_failed` rows, 0 reads, `recognised` false — never a read of the
desktop. The flag absent → HEAD's answers through the real routes. Temp dirs removed.

    python3 -m unittest discover -s tests/b129_h7_game_window -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("art_systems", "b99_h7_live_read", "b102_h7_endscreen", "b103_h7_minigame", "b114_party_minigame_hang"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import _tmp_cleanup  # noqa: E402,F401
import test_b85 as b85  # noqa: E402
import test_b99 as b99  # noqa: E402
import test_b103 as b103  # noqa: E402
import test_b114 as b114  # noqa: E402

HEAD = "1fc0ced0"                      # queue AT's baseline (H7-D1 committed): the companion before B129-B131
SCENARIO = (HERE / "b129_scenario.py").read_text()
ON = {**b85.FLAGS, "PRIVYHUB_H7": "1"}
OFF = dict(b85.FLAGS)


def run(root: Path, env: dict, gid: str, mode: str) -> dict:
    """B103's run with this scenario appended to B103's harness head (`today`: B103's own child)."""
    child = b103.CHILD if mode == "today" else b103.CHILD.split('out = {"steps": {}}')[0] + SCENARIO
    child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    child_env.update(env)
    xdg = root / "xdg"
    xdg.mkdir(exist_ok=True)
    child_env.update({"XDG_CONFIG_HOME": str(xdg), "HOME": str(xdg), "PRIVYHUB_H7_RULES": str(root / "h7rules")})
    (root / "tools").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "tools" / "h7_endscreen.py", root / "tools" / "h7_endscreen.py")
    work = Path(tempfile.mkdtemp(prefix="b129_fx_"))
    try:
        frames, spec_dir, js = b103.fixtures(work)
        js["arrays"] = f"{gid}.endscreen.npz"
        (spec_dir / "GAME.endscreen.json").write_text(json.dumps(js))
        r = subprocess.run([sys.executable, "-I", "-B", "-c", child, str(root),
                            json.dumps({"id": gid, "mode": mode, "p1": b99.P1, "p2": b99.P2, "frames": str(frames),
                                        "spec_dir": str(spec_dir)})],
                           cwd=root, env=child_env, capture_output=True, text=True, timeout=900)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


class GameWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b99.tree()
        cls.s = run(root, ON, ids[b85.PS1_TITLE], "window")["steps"]

    def test_0_a_full_screen_game_as_today(self):
        self.assertEqual(self.s["full_grabs"], [[0, 0, 1920, 1080]])
        self.assertEqual(self.s["full"]["recognised"], True)

    def test_1_then_a_windowed_game_its_own_rectangle(self):
        self.assertEqual(self.s["windowed_grabs"], [[960, 384, 1920, 1104]])     # (960, 384, 960, 720)
        self.assertEqual((self.s["windowed"]["recognised"], self.s["windowed"]["picture_failures"]), (True, 0))

    def test_2_a_window_listed_but_owned_by_another_is_not_taken(self):
        self.assertEqual(self.s["foreign_listed_grabs"], [[300, 200, 1260, 920]])
        self.assertEqual(self.s["foreign_listed"]["recognised"], True)

    def test_3_no_window_of_the_process_a_picture_failure_never_a_read(self):
        for tag in ("no_window", "only_foreign"):
            r = self.s[tag]
            self.assertEqual(self.s[tag + "_grabs"], [], tag)                  # nothing grabbed at all
            self.assertEqual((r["reads"], r["recognised"]), (0, False), (tag, r))
            self.assertGreaterEqual(r["picture_failures"], 3, tag)
            self.assertIn("picture_failed", self.s[tag + "_rows"], tag)
            self.assertEqual(self.s[tag + "_failures_why"],
                             ["the picture was not read: the game's window was not found"], tag)


class FlagAbsentIsHeads(unittest.TestCase):
    def test_flag_absent(self):
        code = b114.code_of(HEAD)
        if code is None:
            self.skipTest("git is absent")
        root, ids = b99.tree(code)
        base = run(root, OFF, ids[b85.PS1_TITLE], "today")["steps"]
        root2, ids2 = b99.tree()
        mine = run(root2, OFF, ids2[b85.PS1_TITLE], "today")["steps"]
        for k in ("get_before_launch", "start_before_launch", "get_after", "start_after", "start_after_load0"):
            self.assertEqual((mine[k]["code"], mine[k]["raw"]), (base[k]["code"], base[k]["raw"]), k)
        self.assertIn("Unknown Games plugin", base["start_after"]["body"]["error"])
        shutil.rmtree(code, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
