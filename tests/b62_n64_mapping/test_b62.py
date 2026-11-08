#!/usr/bin/env python3
"""B62 (host): the N64 layout -- the core remap (o = C-right, triangle = C-up for players 1-4) written and verified
before every N64 launch, the per-title `n64_layout` override, the layout as the details' controller label, the
tool's read-only check -- and absent = today. Fakes only (B59's fake RetroArch tree); temp dirs removed at exit.

    python3 -m unittest discover -s tests/b62_n64_mapping -v
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401
sys.path.insert(0, str(ROOT / "tests" / "n64_session"))
sys.path.insert(0, str(ROOT / "tools"))

import n64_session as n64  # noqa: E402
import n64_core_check  # noqa: E402
from test_n64_session import N64_GAME, SNES_GAME, fake_project, run_launch, tree  # noqa: E402

RMP = "retroarch/config/remaps/Mupen64Plus-Next/Mupen64Plus-Next.rmp"
OTHER = {"id": "game_n64_fedcba9876543210", "system": "n64", "title": "made-up two", "relative_path": "n64/two.v64"}


def overrides(proj: Path, games: dict) -> None:
    p = proj / "data/games/retroarch/controller_overrides.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"version": 1, "games": games}))


class Remap(unittest.TestCase):
    def test_the_binds(self):
        b = n64.remap_binds("face_c")
        self.assertEqual(len(b), 8)
        for p in range(1, 5):
            self.assertEqual((b[f"input_player{p}_btn_a"], b[f"input_player{p}_btn_x"]), ("20", "23"))
        self.assertEqual(n64.remap_binds("core"), {})
        self.assertEqual(n64.parse_remap(n64.remap_text("face_c")), b)

    def test_written_verified_idempotent(self):
        cfg = Path(tempfile.mkdtemp())
        r1 = n64.write_remap(cfg, "mupen64plus_next_libretro.so", "face_c")
        text = (cfg / "remaps/Mupen64Plus-Next/Mupen64Plus-Next.rmp").read_text()
        r2 = n64.write_remap(cfg, "mupen64plus_next_libretro.so", "face_c")
        self.assertEqual((r1["verified"], r1["binds"], r1["shadowed"]), (True, 8, 0))
        self.assertEqual(r1, r2)
        self.assertEqual(text, (cfg / "remaps/Mupen64Plus-Next/Mupen64Plus-Next.rmp").read_text())

    def test_a_tampered_read_back_refuses(self):
        cfg = Path(tempfile.mkdtemp())
        orig = n64.parse_remap
        try:
            n64.parse_remap = lambda text: {}
            with self.assertRaises(n64.N64Error):
                n64.write_remap(cfg, "mupen64plus_next_libretro.so", "face_c")
        finally:
            n64.parse_remap = orig

    def test_other_core_no_remap_and_layout_values(self):
        cfg = Path(tempfile.mkdtemp())
        self.assertFalse(n64.write_remap(cfg, "parallel_n64_libretro.so", "face_c")["written"])
        self.assertEqual(list(cfg.iterdir()), [])
        self.assertEqual(n64.layout_of(None), ("face_c", None))
        self.assertEqual(n64.layout_of({"n64_layout": "CORE"}), ("core", None))
        self.assertEqual(n64.layout_of({"n64_layout": "sideways"}), ("face_c", "sideways"))


class Launch(unittest.TestCase):
    def setUp(self):
        self.drive = tree({"one.z64": b"N64", "two.v64": b"N64"})
        self.proj = fake_project(self.drive)

    def test_present_and_complete_for_every_title(self):
        for game in (N64_GAME, OTHER):
            out = run_launch("1", self.proj, game)
            self.assertTrue(out["calls"], game)
            self.assertEqual(n64.parse_remap(out["rmp"]), n64.remap_binds("face_c"))
            self.assertIn("N64 remap: face_c (players 1-4, 8 binds) verified\n", out["log"])
            for line in n64.INPUT_CFG_LINES:
                self.assertIn(line, out["privyhub-input.cfg"])
            self.assertEqual((out["n64_session"]["layout"], out["n64_session"]["remap_binds"]), ("face_c", 8))
            self.assertEqual(out["label"], n64.LABELS["face_c"])

    def test_the_override_and_a_bad_value(self):
        overrides(self.proj, {N64_GAME["id"]: {"n64_layout": "core"}, OTHER["id"]: {"n64_layout": "sideways"}})
        out = run_launch("1", self.proj, N64_GAME)
        self.assertEqual(n64.parse_remap(out["rmp"]), {})
        self.assertIn("N64 remap: core (no binds) verified\n", out["log"])
        self.assertEqual(out["label"], n64.LABELS["core"])
        out = run_launch("1", self.proj, OTHER)
        self.assertEqual(n64.parse_remap(out["rmp"]), n64.remap_binds("face_c"))
        self.assertIn("(n64_layout ignored: 'sideways')", out["log"])

    def test_a_shadowing_remap_is_counted(self):
        xdg = Path(tempfile.mkdtemp(prefix="b62_xdg_"))
        (xdg / RMP).parent.mkdir(parents=True)
        (xdg / RMP).parent.joinpath("made-up title.rmp").write_text("")
        out = run_launch("1", self.proj, N64_GAME, xdg=xdg)
        self.assertIn("verified + shadowed 1\n", out["log"])

    def test_another_core_writes_no_remap(self):
        proj = fake_project(self.drive, cores=("parallel_n64_libretro.so",))
        out = run_launch("1", proj, N64_GAME, extra={"PRIVYHUB_N64_CORE": "parallel_n64"})
        self.assertIsNone(out["rmp"])
        self.assertIn("N64 remap: none (no remap for this core)\n", out["log"])

    def test_absent_and_other_systems(self):
        out = run_launch(None, self.proj, N64_GAME)
        self.assertIsNone(out["rmp"])
        self.assertEqual(out["label"], "EmulatorError")                       # today: no n64 profile
        for flag in (None, "1"):
            out = run_launch(flag, self.proj, SNES_GAME)
            self.assertIsNone(out["rmp"])
            for line in n64.INPUT_CFG_LINES:
                self.assertNotIn(line, out["privyhub-input.cfg"])
            self.assertNotEqual(out["label"], n64.LABELS["face_c"])


class Tool(unittest.TestCase):
    def check(self, cfg: Path) -> tuple[int, dict]:
        proj = tree({"runtime/emulators/retroarch/cores-linux/mupen64plus_next_libretro.so": b"x"})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = n64_core_check.main(["--root", str(proj), "--remap", "--config-dir", str(cfg)])
        return code, json.loads(buf.getvalue())["remap"]

    def test_absent_matches_differs_shadowed(self):
        cfg = Path(tempfile.mkdtemp())
        code, r = self.check(cfg)
        self.assertEqual((code, r["state"].split()[0], r["writable"]), (0, "absent", True))
        n64.write_remap(cfg, "mupen64plus_next_libretro.so", "face_c")
        self.assertEqual(self.check(cfg)[1]["state"], "matches")
        n64.write_remap(cfg, "mupen64plus_next_libretro.so", "core")
        self.assertEqual(self.check(cfg)[1]["state"], "matches core")
        p = cfg / "remaps/Mupen64Plus-Next/Mupen64Plus-Next.rmp"
        p.write_text('input_player1_btn_a = "3"\n')
        code, r = self.check(cfg)
        self.assertEqual((code, r["state"]), (5, "differs"))
        p.with_name("x.rmp").write_text("")
        self.assertEqual(self.check(cfg)[1]["shadowed"], 1)


if __name__ == "__main__":
    unittest.main()
