#!/usr/bin/env python3
"""G6-SCREEN1b (host): a handheld PS2 launch (`display=handheld` on the launch request) runs without the widescreen
patch, for that launch only. Fixtures only (B49's PCSX2 launch rig in a subprocess, a fake Popen and Session, made-up
logs); nothing fetched, no emulator started; temp dirs removed at exit.

    python3 -m unittest discover -s tests/g6_screen1b -v
"""

from __future__ import annotations

import ast
import base64
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tests" / "art_systems"))
import _tmp_cleanup  # noqa: E402,F401

import ps2_patches as pp  # noqa: E402

sys.path.insert(0, str(ROOT / "tests" / "ps2_session"))
import test_ps2_session as ps2rig  # noqa: E402

SERIAL, CRC = "SLUS-99901", "1234ABCD"      # made up
GAME_ID = "game_ps2_x"


def log_text(name: str) -> str:
    return (f"[    1.3691] Disc changed to {name}.\n[    1.3691]   Serial: {SERIAL}\n[    1.3691]   CRC: {CRC}\n")


def must_replace(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, old[:80]        # a missed anchor fails loudly
    return text.replace(old, new)


# B49's rig with: the request's display, the game settings files as PCSX2 would read them at its spawn, the
# session's `widescreen` field, and a second launch without the field (the next launch)
CODE = ps2rig.LAUNCH_CODE
CODE = must_replace(CODE, """        calls["popen"].append({""", """        gs = proj / "data/games/ps2/config/PCSX2/gamesettings"
        calls.setdefault("gs_at_spawn", []).append({p.name: p.read_text() for p in sorted(gs.glob("*.ini"))} if gs.is_dir() else {})
        calls["popen"].append({""")
CODE = must_replace(CODE, """    r = m.launch(game, players_chosen=int(os.environ["B49_PICK"]) if os.environ.get("B49_PICK") else None)""",
                    """    kw = {"display": os.environ["G6_DISPLAY"]} if os.environ.get("G6_DISPLAY") else {}
    if os.environ.get("G6_SYSTEM"):
        game["system"] = os.environ["G6_SYSTEM"]
    r = m.launch(game, players_chosen=int(os.environ["B49_PICK"]) if os.environ.get("B49_PICK") else None, **kw)
    out["status_widescreen"] = m.status().get("widescreen", "absent")
    out["launch_widescreen"] = r.get("widescreen", "absent")""")
CODE = must_replace(CODE, """    out["stop"] = m.stop().get("ps2_exit"); out["kind_after"] = m._launch_kind""",
                    """    out["stop"] = m.stop().get("ps2_exit"); out["kind_after"] = m._launch_kind
    if os.environ.get("G6_NEXT"):
        r2 = m.launch(game)
        out["next_widescreen"] = m.status().get("widescreen", "absent")
        m.stop()""")


def tree_hashes(folder: Path) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.glob("*.ini"))} \
        if folder.is_dir() else {}


class Pure(unittest.TestCase):
    def test_handheld_toggles_turn_only_ws_off(self):
        self.assertEqual(pp.handheld_toggles({"ws": True, "ni": True, "60": True}), {"ws": False, "ni": True, "60": True})
        self.assertEqual(pp.handheld_toggles({"ws": True}), {"ws": False, "ni": False, "60": False})

    def test_the_line_has_no_title_or_serial(self):
        self.assertEqual(pp.handheld_line(True),
                         "PS2 handheld: widescreen patch off for this launch only (the title's setting: on)")
        self.assertIn("setting: off", pp.handheld_line(False))

    def test_the_journal_puts_back_bytes_and_absence(self):
        root = ps2rig.tree({"data/games/ps2/x": b""})
        gs = root / "gs"
        gs.mkdir()
        (gs / f"{CRC}.ini").write_bytes(b"; earlier\r\nEnableWideScreenPatches = true\n\xff")
        pp.journal_game_ini(root, gs, SERIAL, CRC)                   # the second name absent
        (gs / f"{CRC}.ini").write_text("changed")
        (gs / f"{SERIAL}_{CRC}.ini").write_text("new")
        self.assertEqual(sorted(pp.restore_journal(root)), sorted([f"{CRC}.ini", f"{SERIAL}_{CRC}.ini"]))
        self.assertEqual((gs / f"{CRC}.ini").read_bytes(), b"; earlier\r\nEnableWideScreenPatches = true\n\xff")
        self.assertFalse((gs / f"{SERIAL}_{CRC}.ini").exists())
        self.assertFalse((root / pp.JOURNAL_FILE).exists())
        self.assertEqual(pp.restore_journal(root), [])                 # no journal: nothing

    def test_pcsx2s_settings_lines(self):
        self.assertTrue(pp.settings_read_in_log("[ 0.98] Loading game settings from '/x/gamesettings/A.ini'...\n"))
        self.assertTrue(pp.settings_read_in_log("[ 1.56] No game settings found (tried '/x/A.ini')\n"))
        self.assertFalse(pp.settings_read_in_log("[ 0.04] Game Settings Directory: /x/gamesettings\n"))


class Launch(unittest.TestCase):
    """B49's rig in a subprocess (PRIVYHUB_PS2=1): what PCSX2 would read at its spawn, and the files after."""

    def setUp(self):
        self.games = ps2rig.tree({"one.chd": b"1"})
        self.bios = ps2rig.tree({"image.bin": b"\0" * ps2rig.ps2.BIOS_IMAGE_BYTES, "image.nvm": b"n"})

    def project(self, toggles=None, earlier: bytes | None = None):
        proj = ps2rig.tree({"runtime/emulators/pcsx2/pcsx2-fake.AppImage": b"x"})
        (proj / "runtime" / "h3_p1_paths.txt").write_text(f"BIOS_DIR={self.bios}\nGAMES_DIR={self.games}\n")
        (proj / "data/games/ps2/logs").mkdir(parents=True)
        (proj / "data/games/ps2/logs/20261101T000000Z-pcsx2.log").write_text(log_text("one.chd"))
        if toggles is not None:
            pp.set_toggles(proj, GAME_ID, toggles, ["ws", "ni", "60"])
        if earlier is not None:       # the files as an earlier (normal) launch left them
            gs = proj / "data/games/ps2/config/PCSX2/gamesettings"
            gs.mkdir(parents=True)
            for n in (f"{CRC}.ini", f"{SERIAL}_{CRC}.ini"):
                (gs / n).write_bytes(earlier)
        return proj

    def run_rig(self, proj, display=None, system=None, nxt=False):
        env = {"PATH": "/usr/bin:/bin", "B49_PROJ": str(proj), "PRIVYHUB_PS2": "1"}
        if display:
            env["G6_DISPLAY"] = display
        if system:
            env["G6_SYSTEM"] = system
        if nxt:
            env["G6_NEXT"] = "1"
        r = subprocess.run([sys.executable, "-c", CODE], cwd=ROOT, env=env, capture_output=True, text=True)
        if r.returncode:
            raise AssertionError(r.stderr[-2000:])
        out = json.loads(r.stdout.strip().splitlines()[-1])
        logs = sorted((proj / "logs/games").glob("*-ps2.log"))
        return out, "\n".join(p.read_text() for p in logs)

    def test_handheld_ws_on_is_off_at_the_spawn_and_the_files_come_back(self):
        earlier = pp.game_ini_text({"ws": True, "ni": False, "60": True}).encode()
        proj = self.project({"ws": True, "ni": False, "60": True}, earlier=earlier)
        gs = proj / "data/games/ps2/config/PCSX2/gamesettings"
        toggles_file = proj / pp.TOGGLES_FILE
        before, toggles_before = tree_hashes(gs), toggles_file.read_bytes()
        out, log = self.run_rig(proj, display="handheld")
        spawn = out["calls"]["gs_at_spawn"][0]
        for n in (f"{CRC}.ini", f"{SERIAL}_{CRC}.ini"):
            self.assertIn("EnableWideScreenPatches = false", spawn[n])     # what PCSX2 reads
            self.assertIn("Enable = 60 FPS", spawn[n])                       # the other toggles as they are
        self.assertEqual(tree_hashes(gs), before)                            # put back, byte for byte
        self.assertEqual(toggles_file.read_bytes(), toggles_before)           # the record never touched
        self.assertFalse((proj / pp.JOURNAL_FILE).exists())
        self.assertIs(out["status_widescreen"], False)
        self.assertIs(out["launch_widescreen"], False)
        self.assertIn("PS2 handheld: widescreen patch off for this launch only (the title's setting: on)", log)
        self.assertIn("PS2 handheld: game settings put back", log)
        self.assertNotIn(SERIAL, log)

    def test_the_next_launch_without_the_field_has_it_on_again(self):
        earlier = pp.game_ini_text({"ws": True, "ni": False, "60": False}).encode()
        proj = self.project({"ws": True, "ni": False, "60": False}, earlier=earlier)
        out, _ = self.run_rig(proj, display="handheld", nxt=True)
        self.assertIn("EnableWideScreenPatches = false", out["calls"]["gs_at_spawn"][0][f"{CRC}.ini"])
        self.assertIn("EnableWideScreenPatches = true", out["calls"]["gs_at_spawn"][1][f"{CRC}.ini"])
        self.assertEqual(out["calls"]["gs_at_spawn"][1][f"{CRC}.ini"], earlier.decode())
        self.assertEqual(out["next_widescreen"], "absent")

    def test_without_the_field_today(self):
        proj = self.project({"ws": True, "ni": False, "60": False})
        out, log = self.run_rig(proj)
        self.assertIn("EnableWideScreenPatches = true", out["calls"]["gs_at_spawn"][0][f"{CRC}.ini"])
        self.assertEqual(out["status_widescreen"], "absent")
        self.assertNotIn("PS2 handheld", log)

    def test_handheld_with_ws_already_off_writes_nothing_new(self):
        for toggles in (None, {"ws": False, "ni": True, "60": False}):
            proj = self.project(toggles)
            gs = proj / "data/games/ps2/config/PCSX2/gamesettings"
            out_today, _ = self.run_rig(self.project(toggles))
            out, log = self.run_rig(proj, display="handheld")
            self.assertEqual(out["calls"]["gs_at_spawn"], out_today["calls"]["gs_at_spawn"], toggles)
            self.assertIs(out["status_widescreen"], False)
            self.assertIn("(the title's setting: off)", log)
            self.assertNotIn("put back", log)
            self.assertFalse((proj / pp.JOURNAL_FILE).exists())

    def test_a_crash_left_journal_is_put_back_by_the_next_launch(self):
        earlier = b"; an earlier launch's bytes\nEnableWideScreenPatches = true\n"
        proj = self.project(None, earlier=earlier)
        gs = proj / "data/games/ps2/config/PCSX2/gamesettings"
        pp.journal_game_ini(proj, gs, SERIAL, CRC)
        for n in (f"{CRC}.ini", f"{SERIAL}_{CRC}.ini"):
            (gs / n).write_text(pp.game_ini_text({"ws": False}))           # as a crash after the handheld write
        out, _ = self.run_rig(proj)                                           # the next launch, no field, no record
        self.assertEqual(out["calls"]["gs_at_spawn"][0][f"{CRC}.ini"], earlier.decode())
        self.assertFalse((proj / pp.JOURNAL_FILE).exists())


class Manager(unittest.TestCase):
    def test_display_is_read_only_in_the_ps2_branch(self):
        """Any other system: `display` is never read (the launch as today)."""
        src = (ROOT / "companion/games/emulator_manager.py").read_text()
        tree = ast.parse(src)
        launch = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "launch")
        uses = [n for n in ast.walk(launch) if isinstance(n, ast.Name) and n.id == "display"]
        self.assertEqual(len(uses), 1)
        ps2_if = next(n for n in ast.walk(launch) if isinstance(n, ast.If) and "_ps2.SYSTEM_ID" in ast.unparse(n.test))
        self.assertIn(uses[0], list(ast.walk(ps2_if)))


class Plugin(unittest.TestCase):
    def plugin(self):
        spec = importlib.util.spec_from_file_location("g_g6s1b", ROOT / "companion/plugins/games.py")
        G = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(G)
        p = object.__new__(G.GamesPlugin)
        seen = []
        p._find_game_by_id = lambda gid: {"id": gid, "system": "ps2", "relative_path": "ps2/one.chd"}
        p._parse_cheat_launch_request = lambda q: (None, None)
        p._game_discs = lambda g: 1
        p._log_launch_ports = lambda g, pl, q: None
        p._emulator = types.SimpleNamespace(launch=lambda g, **kw: (seen.append(kw), {"ok": True})[1])
        return p, seen

    def test_the_field_reaches_the_launch_only_when_sent(self):
        p, seen = self.plugin()
        p.handle_post("launch", "id=game_ps2_x")
        p.handle_post("launch", "id=game_ps2_x&display=handheld")
        p.handle_post("launch", "id=game_ps2_x&display=tv")
        self.assertNotIn("display", seen[0])
        self.assertEqual(seen[1].get("display"), "handheld")
        self.assertNotIn("display", seen[2])
        self.assertEqual({k: v for k, v in seen[1].items() if k != "display"}, seen[0])


class Relaunch(unittest.TestCase):
    def test_a_handheld_session_relaunches_as_one(self):
        sys.path.insert(0, str(ROOT / "tests" / "relaunch_ports"))
        import test_relaunch_ports as rr
        import relaunch_ports as rp
        for handheld in (True, False):
            p, rec, calls, clock, _ = rr.rig(kind="pcsx2", system="ps2", fail_save=True)
            kws = []
            emu = p._emulator
            orig = emu.launch
            emu._ps2_handheld = handheld
            emu.launch = lambda game, **kw: (kws.append(kw), orig(game, **kw))[1]
            rp.run(p, 4, 3, clock=clock, sleep=clock.sleep)
            self.assertEqual(kws[0].get("display"), "handheld" if handheld else None, handheld)
            if not handheld:
                self.assertEqual(kws[0], {"players_chosen": 4})          # today's call


if __name__ == "__main__":
    unittest.main()
