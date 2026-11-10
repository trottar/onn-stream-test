#!/usr/bin/env python3
"""B80 (host): PCSX2's bundled widescreen / no-interlacing / 60-fps patches per PS2 title, inside PRIVYHUB_PS2=1
(PRIVYHUB_PS2_PATCHES=0 = today). Fixtures only: made-up PCSX2 logs, a made-up patches.zip behind a fake `7z`,
B49's PCSX2 launch rig; nothing fetched, no emulator started; temp dirs removed at exit.

    python3 -m unittest discover -s tests/art_systems -p 'test_b80.py' -v
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

import ps2_patches as pp  # noqa: E402
import ps2_session as ps2  # noqa: E402

sys.path.insert(0, str(ROOT / "tests" / "ps2_session"))
import test_ps2_session as ps2rig  # noqa: E402

SERIAL, CRC = "SLUS-99901", "1234ABCD"      # made up
GAME = {"id": "game_ps2_x", "system": "ps2", "title": "made-up", "relative_path": "ps2/one.chd"}


def log_text(name: str, serial: str = SERIAL, crc: str = CRC) -> str:
    return (f"[    1.3284] GameDB: Has not been initialized yet, initializing...\n"
            f"[    1.3691] Disc changed to {name}.\n[    1.3691]   Name: x\n[    1.3691]   Serial: {serial}\n"
            f"[    1.3691]   Version: 1.00\n[    1.3691]   CRC: {crc}\n[    1.3691] Applying settings...\n")


def bundle(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n, txt in files.items():
            z.writestr(n, txt)
    return buf.getvalue()


ZIP = bundle({f"{SERIAL}_{CRC}.pnach": "gametitle=x\n[Widescreen 16:9]\npatch=1,EE,0,word,0\n[60 FPS]\npatch=1,EE,4,word,0\n",
              "SLUS-99902_AAAAAAAA.pnach": "[No-Interlacing]\npatch=1,EE,0,word,0\n"})


def fake_7z(cmd, **kw):
    assert cmd[:3] == ["7z", "x", "-so"] and cmd[-1] == pp.ZIP_MEMBER, cmd
    return types.SimpleNamespace(returncode=0, stdout=ZIP)


def project(logs: dict[str, str] | None = None) -> Path:
    root = Path(tempfile.mkdtemp(prefix="b80_"))
    d = root / "data/games/ps2/logs"
    d.mkdir(parents=True)
    for name, text in (logs or {}).items():
        (d / name).write_text(text)
    return root


class Ids(unittest.TestCase):
    def test_from_the_logs_last_launch_wins(self):
        root = project({"20261101T000000Z-pcsx2.log": log_text("one.chd", crc="00000000"),
                        "20261102T000000Z-pcsx2.log": log_text("one.chd"),
                        "20261103T000000Z-pcsx2.log": log_text("two.chd", serial="SLUS-99902", crc="AAAAAAAA")})
        ids = pp.ids_from_logs(root / "data/games/ps2/logs")
        self.assertEqual(ids["one.chd"], (SERIAL, CRC))
        self.assertEqual(ids["two.chd"], ("SLUS-99902", "AAAAAAAA"))

    def test_cached_by_game_id_and_unknown_is_none(self):
        root = project({"20261102T000000Z-pcsx2.log": log_text("one.chd")})
        logs = root / "data/games/ps2/logs"
        self.assertEqual(pp.title_ids(root, GAME, logs), (SERIAL, CRC))
        (logs / "20261102T000000Z-pcsx2.log").unlink()        # the logs pruned: the cache keeps it
        self.assertEqual(pp.title_ids(root, GAME, logs), (SERIAL, CRC))
        self.assertIsNone(pp.title_ids(root, {**GAME, "id": "game_ps2_y", "relative_path": "ps2/never.chd"}, logs))

    def test_a_malformed_serial_is_not_learned(self):
        root = project({"20261102T000000Z-pcsx2.log": log_text("one.chd", serial="../x")})
        self.assertIsNone(pp.title_ids(root, GAME, root / "data/games/ps2/logs"))


class Bundle(unittest.TestCase):
    def setUp(self):
        pp._zip_cache.clear()
        self.app = Path(tempfile.mkdtemp(prefix="b80_app_")) / "pcsx2.AppImage"
        self.app.write_bytes(b"x")

    def test_groups_and_available(self):
        g = pp.bundle_groups(self.app, SERIAL, CRC, run=fake_7z)
        self.assertEqual(g, {"Widescreen 16:9", "60 FPS"})
        self.assertEqual(pp.available(g), ["ws", "60"])
        self.assertEqual(pp.available(pp.bundle_groups(self.app, "SLUS-99902", "AAAAAAAA", run=fake_7z)), ["ni"])
        self.assertEqual(pp.bundle_groups(self.app, "SLUS-00000", "00000000", run=fake_7z), set())

    def test_read_once_per_appimage(self):
        calls = []
        run = lambda cmd, **kw: (calls.append(1), fake_7z(cmd))[1]
        pp.bundle_groups(self.app, SERIAL, CRC, run=run)
        pp.bundle_groups(self.app, SERIAL, CRC, run=run)
        self.assertEqual(len(calls), 1)


class Toggles(unittest.TestCase):
    def test_stored_and_an_unavailable_one_refused(self):
        root = project()
        self.assertIsNone(pp.get_toggles(root, "g"))
        self.assertEqual(pp.set_toggles(root, "g", {"ws": True, "60": False}, ["ws", "60"]),
                         {"ws": True, "ni": False, "60": False})
        self.assertEqual(pp.get_toggles(root, "g"), {"ws": True, "ni": False, "60": False})
        with self.assertRaises(ValueError):
            pp.set_toggles(root, "g", {"ni": True}, ["ws", "60"])

    def test_the_keys_from_the_toggles(self):
        self.assertEqual(pp.game_ini_text({"ws": True, "ni": False, "60": True}),
                         pp.MARKER + "\n[EmuCore]\nEnableWideScreenPatches = true\nEnableNoInterlacingPatches = false\n"
                         "\n[Patches]\nEnable = 60 FPS\n")
        self.assertNotIn("[Patches]", pp.game_ini_text({"ws": False, "ni": True, "60": False}))
        self.assertIn("EnableNoInterlacingPatches = true", pp.game_ini_text({"ni": True}))

    def test_both_file_names(self):
        d = Path(tempfile.mkdtemp(prefix="b80_gs_"))
        self.assertEqual(pp.write_game_ini(d, SERIAL, "1234abcd", "x\n"), [f"{CRC}.ini", f"{SERIAL}_{CRC}.ini"])
        self.assertEqual(sorted(p.name for p in d.iterdir()), sorted([f"{CRC}.ini", f"{SERIAL}_{CRC}.ini"]))

    def test_the_line(self):
        self.assertEqual(pp.log_line({"ws": True}), "PS2 patches: ws=on ni=off 60=off")


class Launch(unittest.TestCase):
    """B49's rig: the PCSX2 launch in a subprocess (PRIVYHUB_PS2=1), a fake Popen and Session."""

    def setUp(self):
        self.games = ps2rig.tree({"one.chd": b"1"})
        self.bios = ps2rig.tree({"image.bin": b"\0" * ps2.BIOS_IMAGE_BYTES, "image.nvm": b"n"})

    def launch(self, toggles=None, knob=None, learned=True):
        proj = ps2rig.tree({"runtime/emulators/pcsx2/pcsx2-fake.AppImage": b"x"})
        (proj / "runtime" / "h3_p1_paths.txt").write_text(f"BIOS_DIR={self.bios}\nGAMES_DIR={self.games}\n")
        if learned:
            (proj / "data/games/ps2/logs").mkdir(parents=True)
            (proj / "data/games/ps2/logs/20261101T000000Z-pcsx2.log").write_text(log_text("one.chd"))
        if toggles is not None:
            pp.set_toggles(proj, GAME["id"], toggles, ["ws", "ni", "60"])
        real_run = ps2rig.subprocess.run
        extra = {} if knob is None else {"PRIVYHUB_PS2_PATCHES": knob}

        def run(cmd, **kw):
            kw["env"] = {**kw.get("env", {}), **extra}
            return real_run(cmd, **kw)
        with mock.patch.object(ps2rig.subprocess, "run", run):
            out = ps2rig.run_launch("1", proj)
        self.assertEqual(out["launch"]["launch_kind"], "pcsx2", out)
        gs = proj / "data/games/ps2/config/PCSX2/gamesettings"
        log = next((proj / "logs/games").glob("*-ps2.log")).read_text()
        return gs, log

    def test_a_record_writes_the_game_ini_and_the_line(self):
        gs, log = self.launch({"ws": True, "ni": False, "60": True})
        text = (gs / f"{CRC}.ini").read_text()
        self.assertIn("EnableWideScreenPatches = true", text)
        self.assertIn("Enable = 60 FPS", text)
        self.assertEqual(text, (gs / f"{SERIAL}_{CRC}.ini").read_text())
        self.assertIn("PS2 patches: ws=on ni=off 60=on", log)
        self.assertNotIn(SERIAL, log)

    def test_all_off_still_written_so_an_earlier_on_is_undone(self):
        gs, log = self.launch({"ws": False, "ni": False, "60": False})
        self.assertIn("EnableWideScreenPatches = false", (gs / f"{CRC}.ini").read_text())
        self.assertIn("PS2 patches: ws=off ni=off 60=off", log)

    def test_no_record_or_knob_zero_or_unknown_ids_is_today(self):
        for kw in ({}, {"toggles": {"ws": True}, "knob": "0"}, {"toggles": {"ws": True}, "learned": False}):
            gs, log = self.launch(**kw)
            self.assertFalse(gs.exists(), kw)
            self.assertNotIn("PS2 patches", log)


class Plugin(unittest.TestCase):
    def load(self):
        spec = importlib.util.spec_from_file_location("g_b80", ROOT / "companion/plugins/games.py")
        G = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(G)
        G._ps2_session = ps2
        return G

    def plugin(self, G, offer):
        p = object.__new__(G.GamesPlugin)
        p.details = lambda q: {"ok": True, "id": GAME["id"], "system": "ps2"}
        p._tile_session_fields = lambda gid: {}
        p._find_game_by_id = lambda gid: dict(GAME)
        stored = {}
        p._emulator = types.SimpleNamespace(
            ps2_patches=lambda g: offer,
            set_ps2_patches=lambda g, w: (stored.update(w), {"available": ["ws"], "on": ["ws"] if w["ws"] else []})[1])
        return p, stored

    def test_details_key_only_with_a_patch(self):
        G = self.load()
        p, _ = self.plugin(G, {"available": ["ws", "60"], "on": ["ws"]})
        self.assertEqual(p.handle("details", f"id={GAME['id']}")["ps2_patches"], {"available": ["ws", "60"], "on": ["ws"]})
        p2, _ = self.plugin(G, None)
        self.assertNotIn("ps2_patches", p2.handle("details", f"id={GAME['id']}"))
        G._ps2_session = None
        self.assertNotIn("ps2_patches", p.handle("details", f"id={GAME['id']}"))

    def test_the_action(self):
        G = self.load()
        p, stored = self.plugin(G, None)
        r = p.handle("ps2-patches", f"id={GAME['id']}&ws=1&ni=0&fps60=0")
        self.assertEqual(stored, {"ws": True, "ni": False, "60": False})
        self.assertEqual(r["ps2_patches"], {"available": ["ws"], "on": ["ws"]})


class Manager(unittest.TestCase):
    def test_offer_and_set_through_the_manager(self):
        from games import emulator_manager as em
        old = em._ps2
        em._ps2 = ps2
        self.addCleanup(lambda: setattr(em, "_ps2", old))
        pp._zip_cache.clear()
        root = project({"20261102T000000Z-pcsx2.log": log_text("one.chd")})
        (root / "runtime/emulators/pcsx2").mkdir(parents=True)
        (root / "runtime/emulators/pcsx2/pcsx2-fake.AppImage").write_bytes(b"x")
        m = em.EmulatorManager(root, config_path=ROOT / "companion/games/config/emulators.json")
        with mock.patch.object(pp.subprocess, "run", fake_7z):
            self.assertEqual(m.ps2_patches(GAME), {"available": ["ws", "60"], "on": []})
            self.assertEqual(m.set_ps2_patches(GAME, {"ws": True}), {"available": ["ws", "60"], "on": ["ws"]})
            with self.assertRaises(em.EmulatorError):
                m.set_ps2_patches(GAME, {"ni": True})
            with mock.patch.dict(os.environ, {"PRIVYHUB_PS2_PATCHES": "0"}):
                self.assertIsNone(m.ps2_patches(GAME))
            self.assertIsNone(m.ps2_patches({**GAME, "id": "game_ps2_z", "relative_path": "ps2/unseen.chd"}))
        self.assertNotIn(SERIAL, json.dumps(m.ps2_patches(GAME) or {}))


if __name__ == "__main__":
    unittest.main()
