#!/usr/bin/env python3
"""B79 (host): GameCube cheats from Dolphin's bundled codes, inside PRIVYHUB_GAMECUBE=1 (PRIVYHUB_GC_CHEATS=0 =
today). Fixtures only: made-up disc headers, a fake bundled reader (no 7z run, no AppImage read), B69's fake Dolphin;
nothing fetched, no emulator started; temp dirs removed at exit.

    python3 -m unittest discover -s tests/art_systems -p 'test_b79.py' -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

import gamecube_session as gc  # noqa: E402
import gc_cheats  # noqa: E402

sys.path.insert(0, str(ROOT / "tests" / "gamecube_session"))
import test_gamecube_session as gcrig  # noqa: E402

GID = "GZZE01"          # made up
ID3_INI = """[Core]
CPUThread = False
[ActionReplay]
# a comment
$Made Up Infinite Health
04000000 00000000
$Made Up Moon Jump
04000004 00000000
[Gecko]
$Made Up Speed [someone]
C2000000 00000000
"""
ID6_INI = """[ActionReplay]
$Made Up Infinite Health
04000000 00000000
$Made Up All Items
04000008 00000000
[Gecko]
$Made Up Debug Menu [another] [x]
C2000004 00000000
[Video_Settings]
SafeTextureCacheColorSamples = 0
"""
BUNDLED = {GID[:3] + ".ini": ID3_INI, GID + ".ini": ID6_INI}


def header(kind: str, gid: str = GID, magic: bytes = gc_cheats.GC_MAGIC) -> bytes:
    disc = gid.encode() + b"\0" * (0x1C - 6) + magic + b"\0" * 0x60
    if kind == "rvz":
        return b"RVZ\x01" + b"\0" * (0x58 - 4) + disc + b"\0" * 0x100
    if kind == "ciso":
        return b"CISO" + b"\0" * (gc_cheats.CISO_OFFSET - 4) + disc
    return disc + b"\0" * 0x100


def fake_reader(name: str):
    return BUNDLED.get(name)


class DiscId(unittest.TestCase):
    def write(self, name, data):
        d = Path(tempfile.mkdtemp(prefix="b79_"))
        (d / name).write_bytes(data)
        return d / name

    def test_offsets(self):
        self.assertEqual(gc_cheats.disc_id(self.write("a.rvz", header("rvz"))), GID)
        self.assertEqual(gc_cheats.disc_id(self.write("a.iso", header("iso"))), GID)
        self.assertEqual(gc_cheats.disc_id(self.write("a.ciso", header("ciso"))), GID)

    def test_not_a_gamecube_disc(self):
        self.assertIsNone(gc_cheats.disc_id(self.write("a.rvz", header("rvz", magic=b"\0\0\0\0"))))
        self.assertIsNone(gc_cheats.disc_id(self.write("a.iso", header("iso", gid="gz e01"))))
        self.assertIsNone(gc_cheats.disc_id(self.write("a.iso", b"short")))
        self.assertIsNone(gc_cheats.disc_id(Path("/nowhere/x.rvz")))


class Codes(unittest.TestCase):
    def test_names_listed_author_stripped_merged_once(self):
        codes = gc_cheats.codes_for(GID, fake_reader)
        self.assertEqual([(c["kind"], c["description"]) for c in codes], [
            ("ar", "Made Up Infinite Health"), ("ar", "Made Up Moon Jump"), ("gecko", "Made Up Speed"),
            ("ar", "Made Up All Items"), ("gecko", "Made Up Debug Menu")])
        self.assertEqual([c["index"] for c in codes], [0, 1, 2, 3, 4])

    def test_nothing_bundled_is_empty(self):
        self.assertEqual(gc_cheats.codes_for("GQQE01", fake_reader), [])

    def test_the_7z_command_reads_only_the_bundled_path(self):
        calls = []

        def run(cmd, **kw):
            calls.append(cmd)
            return types.SimpleNamespace(returncode=0, stdout=b"[Gecko]\n")
        self.assertEqual(gc_cheats.read_bundled(Path("/x/dolphin.AppImage"), "GZZ.ini", run=run), "[Gecko]\n")
        self.assertEqual(calls, [["7z", "x", "-so", "/x/dolphin.AppImage", "usr/share/dolphin-emu/Sys/GameSettings/GZZ.ini"]])
        self.assertIsNone(gc_cheats.read_bundled(Path("/x/a"), "../../etc/passwd", run=run))
        self.assertEqual(len(calls), 1)
        self.assertIsNone(gc_cheats.read_bundled(Path("/x/a"), "GZZ.ini",
                                                 run=lambda *a, **k: types.SimpleNamespace(returncode=2, stdout=b"")))


class Enabled(unittest.TestCase):
    def test_written_and_other_sections_kept(self):
        user = Path(tempfile.mkdtemp(prefix="b79_user_"))
        (user / "GameSettings").mkdir()
        (user / "GameSettings" / f"{GID}.ini").write_text(
            "[Core]\nCPUThread = False\n[ActionReplay_Enabled]\n$Old One\n[Video_Settings]\nX = 1\n")
        p = gc_cheats.write_enabled(user, GID, ["Made Up Moon Jump"], ["Made Up Speed"])
        self.assertEqual(p.read_text(), "[Core]\nCPUThread = False\n[Video_Settings]\nX = 1\n\n"
                                        "[ActionReplay_Enabled]\n$Made Up Moon Jump\n[Gecko_Enabled]\n$Made Up Speed\n")

    def test_none_enabled_no_file(self):
        user = Path(tempfile.mkdtemp(prefix="b79_user_"))
        self.assertIsNone(gc_cheats.write_enabled(user, GID, [], []))
        self.assertFalse((user / "GameSettings").exists())

    def test_dolphin_ini_default_is_todays_bytes(self):
        self.assertEqual(gc.dolphin_ini(), gc.dolphin_ini(False))
        self.assertIn("EnableCheats = False", gc.dolphin_ini())
        self.assertIn("EnableCheats = True", gc.dolphin_ini(True))
        self.assertEqual(gc.dolphin_ini(True).replace("EnableCheats = True", "EnableCheats = False"), gc.dolphin_ini())


class Manager(gcrig.Rig):
    def setUp(self):
        super().setUp()
        (self.games / "one.rvz").write_bytes(header("rvz") + b"\0" * gcrig.MIB)
        self.reader = mock.patch.object(gc_cheats, "read_bundled", lambda appimage, name, run=None: BUNDLED.get(name))
        self.reader.start()
        self.addCleanup(self.reader.stop)
        self.game = {"id": "game_gc_fake", "system": "gamecube", "title": "made-up", "relative_path": "gamecube/one.rvz"}

    def manager(self):
        from games import emulator_manager as em
        return em.EmulatorManager(self.proj, config_path=ROOT / "companion/games/config/emulators.json")

    def cheat_launch(self, indexes):
        from games import emulator_manager as em
        rig = self
        f = gcrig.FakeDolphin(self.proj, user_dir=self.user)
        self.fake = f
        em.subprocess.Popen = lambda cmd, **kw: (rig.popen.append({"cmd": cmd}), gcrig.FakeProc(f.pid))[1]

        class S(rig.old_session):
            def __init__(self, pid, log, **kw):
                super().__init__(pid, log, run=f.run, kill=f.kill, sleep=f.sleep, clock=f.clock, proc_root=f.proc,
                                 grab=f.grab, **kw)
        gc.Session = S
        gc.wait_helpers = lambda sid, *a, **k: "gone 1.0s"
        m = self.manager()
        self.addCleanup(lambda: m._close_quietly(m.log_handle))
        return m, m.launch(self.game, cheat_source_index=0, cheat_enabled_indexes=indexes)

    def test_the_onns_shape(self):
        cat = self.manager().cheat_catalog(self.game)
        self.assertEqual(cat["status"], "cached")
        src = cat["sources"][0]
        self.assertEqual((src["source_index"], src["filename"], src["cheat_count"]), (0, "Dolphin's built-in codes", 5))
        self.assertEqual(src["entries"][2], {"index": 2, "description": "Made Up Speed", "kind": "gecko"})
        self.assertNotIn("_gid", cat)
        self.assertNotIn(GID, repr(cat))
        prof = self.manager().cheat_profiles(self.game)
        self.assertEqual((prof["profiles"], prof["status"]), ([], "cached"))

    def test_a_cheat_launch_writes_the_user_file_and_the_switch(self):
        m, r = self.cheat_launch([1, 2])
        self.assertEqual(r["gc_cheats"], 2)
        ini = (self.user / "GameSettings" / f"{GID}.ini").read_text()
        self.assertEqual(ini, "[ActionReplay_Enabled]\n$Made Up Moon Jump\n[Gecko_Enabled]\n$Made Up Speed\n")
        self.assertEqual((self.user / "Config" / "Dolphin.ini").read_text(), gc.dolphin_ini(True))
        log = self.log_text()
        self.assertIn("GC cheats: 2 enabled", log)
        self.assertNotIn("Made Up", log)
        self.assertNotIn(GID, log)

    def test_a_plain_launch_is_today(self):
        m, r = self.launch()
        self.assertNotIn("gc_cheats", r)
        self.assertEqual((self.user / "Config" / "Dolphin.ini").read_text(), gc.dolphin_ini())
        self.assertFalse((self.user / "GameSettings").exists())
        self.assertNotIn("GC cheats", self.log_text())

    def test_bad_picks_refuse_before_anything_is_written(self):
        for idx in ([], [9], [-1]):
            with self.assertRaises(Exception):
                self.cheat_launch(idx)
        self.assertFalse((self.user / "GameSettings").exists())

    def test_knob_zero_is_today(self):
        with mock.patch.dict(os.environ, {"PRIVYHUB_GC_CHEATS": "0"}):
            m = self.manager()
            self.assertIsNone(m._ext_cheat_catalog(self.game))
            m2, r = self.cheat_launch([1])
        self.assertNotIn("gc_cheats", r)
        self.assertFalse((self.user / "GameSettings").exists())
        self.assertEqual((self.user / "Config" / "Dolphin.ini").read_text(), gc.dolphin_ini())

    def test_an_unknown_disc_lists_nothing(self):
        (self.games / "one.rvz").write_bytes(b"\0" * gcrig.MIB)
        cat = self.manager().cheat_catalog(self.game)
        self.assertEqual((cat["status"], cat["sources"], cat["game_id_known"]), ("no_codes", [], False))


if __name__ == "__main__":
    unittest.main()
