#!/usr/bin/env python3
"""B68 (tool): `tools/library_m3u.py` on fixture libraries -- the sets, the reported cases, apply (the .m3u, the discs
untouched, the real plugin's list one entry per set), the state / card migration, undo, the flag gate, the log.
Made-up names in temp dirs (removed at exit); no real library, title or file.

    python3 -m unittest discover -s tests/b68_library_m3u -v
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401
sys.path.insert(0, str(ROOT / "tools"))

import library_m3u as lm  # noqa: E402
import import_usb as iu  # noqa: E402

ON = {"PRIVYHUB_IMPORT": "1"}


def cue(name: str) -> str:
    return f'FILE "{name}.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n'


def library(sets: dict[str, list[int]], sub: str = "") -> Path:
    root = Path(tempfile.mkdtemp(prefix="b68_proj_"))
    lib = root / "games/ps1" / sub
    lib.mkdir(parents=True)
    for title, discs in sets.items():
        for n in discs:
            stem = f"{title} (Disc {n})"
            (lib / f"{stem}.cue").write_text(cue(stem))
            (lib / f"{stem}.bin").write_bytes(bytes([n]) * 64)
    (lib / "Single Game.cue").write_text(cue("Single Game"))
    (lib / "Single Game.bin").write_bytes(b"s" * 64)
    return root


def snap(root: Path) -> list:
    return sorted((str(p.relative_to(root)), p.stat().st_size, p.stat().st_mtime_ns)
                  for p in (root / "games").rglob("*") if p.is_file() and p.suffix != ".m3u")


def run(root: Path, *args, env=ON):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = lm.main(list(args), root=root, environ=env, game_active=lambda: False)
    return code, buf.getvalue()


SCAN = r'''
import json, os, sys, threading, importlib.util
from pathlib import Path
sys.path.insert(0, "companion")
spec = importlib.util.spec_from_file_location("g", "companion/plugins/games.py")
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
p = object.__new__(G.GamesPlugin)
proj = Path(os.environ["B68_PROJ"]); p.PROJECT_ROOT = proj; p.GAMES_ROOT = proj / "games"
p._lock = threading.RLock(); p._cached_at = 0.0; p._cached_games = []
print(json.dumps(sorted((g["title"], g["format"]) for g in p._scan() if g["system"] == "ps1")))
'''


def scan(root: Path) -> list:
    r = subprocess.run([sys.executable, "-c", SCAN], cwd=ROOT, env={"PATH": "/usr/bin:/bin", "B68_PROJ": str(root)},
                       capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(r.stderr[-1500:])
    return [tuple(x) for x in json.loads(r.stdout.strip().splitlines()[-1])]


class Plan(unittest.TestCase):
    def test_sets_and_lines(self):
        root = library({"Alpha Quest": [1, 2], "Beta Saga": [1, 2, 3, 4]})
        plan = lm.make_plan(root)
        got = {s["m3u"]: s["lines"] for s in plan["sets"]}
        self.assertEqual(got, {"games/ps1/Alpha Quest.m3u": ["Alpha Quest (Disc 1).cue", "Alpha Quest (Disc 2).cue"],
                               "games/ps1/Beta Saga.m3u": [f"Beta Saga (Disc {n}).cue" for n in range(1, 5)]})
        self.assertEqual(plan["reported"], [])

    def test_reported_cases(self):
        root = library({"Gap Game": [1, 3], "Lone Disc": [1], "Same Game": [1, 2], "Other Game": [1, 2],
                        "Named Game": [1, 2]})
        lib = root / "games/ps1"
        (lib / "Same Game.m3u").write_bytes(iu.m3u_bytes(["Same Game (Disc 1).cue", "Same Game (Disc 2).cue"]))
        (lib / "Other Game.m3u").write_bytes(iu.m3u_bytes(["Other Game (Disc 2).cue"]))
        (lib / "Elsewhere.m3u").write_bytes(iu.m3u_bytes(["Named Game (Disc 1).cue"]))
        plan = lm.make_plan(root)
        codes = sorted((r["code"], r["discs"]) for r in plan["reported"])
        self.assertEqual(codes, [("already", 2), ("covered", 2), ("disc_gap", 2), ("m3u_differs", 2)])
        self.assertEqual([s["m3u"] for s in plan["sets"] if not s["m3u_present"]], [])

    def test_a_subfolder_set(self):
        root = library({"Deep Game": [1, 2]}, sub="sub")
        self.assertEqual([s["m3u"] for s in lm.make_plan(root)["sets"]], ["games/ps1/sub/Deep Game.m3u"])


class Apply(unittest.TestCase):
    def test_apply_the_list_and_idempotent(self):
        root = library({"Alpha Quest": [1, 2], "Beta Saga": [1, 2, 3, 4]})
        before = snap(root)
        self.assertEqual(len(scan(root)), 7)                                # 6 disc entries + the single
        code, out = run(root, "apply")
        self.assertEqual(code, 0)
        self.assertIn("written 2", out)
        self.assertEqual((root / "games/ps1/Alpha Quest.m3u").read_text(),
                         "Alpha Quest (Disc 1).cue\nAlpha Quest (Disc 2).cue\n")
        self.assertEqual(before, snap(root))                               # every disc untouched
        self.assertEqual(scan(root), [("Alpha Quest", "m3u"), ("Beta Saga", "m3u"), ("Single Game", "cue")])
        code, out = run(root, "apply")
        self.assertIn("written 0, already 2", out)

    def test_the_flag_and_a_running_game(self):
        root = library({"Alpha Quest": [1, 2]})
        for env in ({}, {"PRIVYHUB_IMPORT": "0"}, {"PRIVYHUB_IMPORT": "yes"}):
            for cmd in ("plan", "apply", "undo"):
                self.assertEqual(run(root, cmd, env=env)[0], 9)
        self.assertFalse((root / "games/ps1/Alpha Quest.m3u").exists())
        self.assertFalse((root / "data").exists())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(lm.main(["apply"], root=root, environ=ON, game_active=lambda: True), 6)


class Migration(unittest.TestCase):
    def setUp(self):
        self.root = library({"Alpha Quest": [1, 2]})
        saves = self.root / lm.SAVES / "Beetle PSX HW"
        saves.mkdir(parents=True)
        (saves / "Alpha Quest (Disc 1).srm").write_bytes(b"1" * 128)
        time.sleep(0.02)
        (saves / "Alpha Quest (Disc 2).srm").write_bytes(b"2" * 128)        # newer: the set gets this one
        states = self.root / lm.STATES / "Beetle PSX HW"
        states.mkdir(parents=True)
        (states / "Alpha Quest (Disc 1).state1").write_bytes(b"S" * 64)
        (states / "Alpha Quest (Disc 1).state1.png").write_bytes(b"P")
        did = iu.stable_id("ps1", "games/ps1/Alpha Quest (Disc 1).cue")
        idx = self.root / lm.SLOT_INDEX
        idx.write_text(json.dumps({"schema": 1, "games": {did: {"slots": {"1": {
            "state_file": "data/games/retroarch/states/Beetle PSX HW/Alpha Quest (Disc 1).state1",
            "modified_unix_ms": 1, "size_bytes": 64}}}}}))

    def test_plan_says_it_and_apply_without_migrating(self):
        code, out = run(self.root, "plan")
        self.assertIn("would no longer show unless migrated", out)
        code, out = run(self.root, "apply")
        self.assertIn("run again with --migrate-states", out)
        self.assertFalse((self.root / lm.SAVES / "Beetle PSX HW/Alpha Quest.srm").exists())

    def test_migrate_newest_card_states_and_slots(self):
        run(self.root, "apply")
        code, out = run(self.root, "apply", "--migrate-states")             # after a plain apply: still migrates
        card = self.root / lm.SAVES / "Beetle PSX HW/Alpha Quest.srm"
        self.assertEqual(card.read_bytes(), b"2" * 128)
        self.assertTrue((self.root / lm.SAVES / "Beetle PSX HW/Alpha Quest (Disc 1).srm").exists())   # kept
        self.assertTrue((self.root / lm.STATES / "Beetle PSX HW/Alpha Quest.state1").is_file())
        self.assertTrue((self.root / lm.STATES / "Beetle PSX HW/Alpha Quest.state1.png").is_file())
        games = json.loads((self.root / lm.SLOT_INDEX).read_text())["games"]
        new = games[iu.stable_id("ps1", "games/ps1/Alpha Quest.m3u")]
        self.assertTrue(new["slots"]["1"]["state_file"].endswith("Beetle PSX HW/Alpha Quest.state1"))

    def test_a_present_target_is_never_overwritten(self):
        card = self.root / lm.SAVES / "Beetle PSX HW/Alpha Quest.srm"
        card.write_bytes(b"mine")
        run(self.root, "apply", "--migrate-states")
        self.assertEqual(card.read_bytes(), b"mine")

    def test_a_target_appearing_after_the_plan_is_not_overwritten(self):
        plan0 = lm.make_plan(self.root)                                      # the card's target absent then
        card = self.root / lm.SAVES / "Beetle PSX HW/Alpha Quest.srm"
        card.write_bytes(b"made meanwhile")
        orig = lm.make_plan
        lm.make_plan = lambda root: plan0                                    # apply's re-check sees the old plan
        try:
            lm.apply_plan(plan0, self.root, migrate=True)
        finally:
            lm.make_plan = orig
        self.assertEqual(card.read_bytes(), b"made meanwhile")

    def test_undo_only_its_own_and_unchanged(self):
        run(self.root, "apply", "--migrate-states")
        m3u = self.root / "games/ps1/Alpha Quest.m3u"
        card = self.root / lm.SAVES / "Beetle PSX HW/Alpha Quest.srm"
        card.write_bytes(b"played since")                                   # changed after the apply: kept
        before = snap(self.root)
        code, out = run(self.root, "undo")
        self.assertFalse(m3u.exists())
        self.assertTrue(card.exists())
        self.assertIn("left (changed since) 1", out)
        self.assertTrue((self.root / lm.SAVES / "Beetle PSX HW/Alpha Quest (Disc 2).srm").exists())
        self.assertNotIn(iu.stable_id("ps1", "games/ps1/Alpha Quest.m3u"),
                         json.loads((self.root / lm.SLOT_INDEX).read_text())["games"])
        self.assertEqual([x for x in before if "Disc" in x[0]], [x for x in snap(self.root) if "Disc" in x[0]])


class Log(unittest.TestCase):
    def test_no_name_path_or_id(self):
        root = library({"Alpha Quest": [1, 2]})
        run(root, "plan")
        run(root, "apply")
        text = "".join(p.read_text() for p in (root / "data/import/logs").glob("library_m3u_*.log"))
        for bad in ("Alpha", "Quest", "Disc", ".cue", ".m3u", "games/", "game_ps1_", str(root)):
            self.assertNotIn(bad, text)
        self.assertIn('"label": "S1"', text)


if __name__ == "__main__":
    unittest.main()
