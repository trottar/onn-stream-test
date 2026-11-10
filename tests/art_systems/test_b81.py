#!/usr/bin/env python3
"""B81 (host): the drop-in folders — the user's PS2 .pnach per game, and the user's own .cht on PS1 / SNES
(PRIVYHUB_CHEAT_DROPINS=0 = today). Fixture folders only, made-up names; B49's PCSX2 rig; nothing fetched, nothing
started; temp dirs removed at exit.

    python3 -m unittest discover -s tests/art_systems -p 'test_b81.py' -v
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

import cheat_dropins as cd  # noqa: E402
import ps2_patches as pp  # noqa: E402
import ps2_session as ps2  # noqa: E402
from games import emulator_manager as em  # noqa: E402

sys.path.insert(0, str(ROOT / "tests" / "ps2_session"))
import test_ps2_session as ps2rig  # noqa: E402
import test_b80 as b80  # noqa: E402

CONFIG = ROOT / "companion/games/config/emulators.json"
DB_CHT = b'cheats = 1\n\ncheat0_desc = "Database One"\ncheat0_code = "80000000 0001"\ncheat0_enable = false\n'
USER_CHT = b'cheats = 2\n\ncheat0_desc = "My Own A"\ncheat0_code = "80000004 0001"\ncheat0_enable = false\n\n' \
           b'cheat1_desc = "My Own B"\ncheat1_code = "80000008 0001"\ncheat1_enable = false\n'
PRE_ENABLED = b'cheats = 1\n\ncheat0_desc = "On Already"\ncheat0_code = "8000000C 0001"\ncheat0_enable = true\n'
PS1 = {"id": "game_ps1_0000000000000001", "system": "ps1", "title": "Made Up", "relative_path": "games/ps1/Made Up (USA).chd"}


def ps1_project(manifest: bool = True, user: dict[str, bytes] | None = None) -> Path:
    root = Path(tempfile.mkdtemp(prefix="b81_"))
    (root / "data/games").mkdir(parents=True)
    if manifest:
        rel = f"data/games/user_content/{PS1['id']}/cheats/libretro/Made Up (USA).cht"
        (root / rel).parent.mkdir(parents=True)
        (root / rel).write_bytes(DB_CHT)
        (root / "data/games/cheats.json").write_text(json.dumps({"games": {PS1["id"]: {
            "id": PS1["id"], "system": "ps1", "relative_path": PS1["relative_path"], "status": "cached",
            "provider": "libretro", "files": [{"local_path": rel, "local_filename": "Made Up (USA).cht",
                                               "local_sha256": hashlib.sha256(DB_CHT).hexdigest().upper(),
                                               "cheat_count": 1}]}}}))
    for name, data in (user or {}).items():
        d = root / "data/games/retroarch/cheats/ps1/Made Up (USA)"
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_bytes(data)
    return root


def manager(root: Path) -> em.EmulatorManager:
    return em.EmulatorManager(root, config_path=CONFIG)


class RetroArchDropIns(unittest.TestCase):
    def test_appended_after_the_database(self):
        root = ps1_project(user={"mine.cht": USER_CHT})
        cat = manager(root).cheat_catalog(PS1)
        self.assertEqual([s["provider"] for s in cat["sources"]], ["libretro", "user"])
        user = cat["sources"][1]
        self.assertEqual((user["source_index"], user["filename"], user["cheat_count"]), (1, "mine.cht", 2))
        self.assertEqual([e["description"] for e in user["entries"]], ["My Own A", "My Own B"])
        self.assertEqual(cat["user_files_skipped"], 0)

    def test_launched_as_a_database_file(self):
        root = ps1_project(user={"mine.cht": USER_CHT})
        m = manager(root)
        rt, session = m._prepare_cheat_runtime(PS1, Path("/nowhere/Made Up (USA).chd"), 1, [1])
        staged = rt / "Beetle PSX HW" / "Made Up (USA).cht"
        self.assertEqual(staged.read_bytes(), USER_CHT)
        self.assertEqual((session["source_filename"], session["enabled_cheat_indexes"]), ("mine.cht", [1]))

    def test_a_pre_enabled_file_is_skipped_and_counted(self):
        root = ps1_project(user={"a.cht": PRE_ENABLED, "b.cht": USER_CHT})
        cat = manager(root).cheat_catalog(PS1)
        self.assertEqual([s["filename"] for s in cat["sources"]], ["Made Up (USA).cht", "b.cht"])
        self.assertEqual(cat["user_files_skipped"], 1)

    def test_no_user_file_is_todays_dict(self):
        root = ps1_project()
        today = manager(root)._cheat_catalog_base_unlocked(PS1)
        self.assertEqual(manager(root).cheat_catalog(PS1), today)
        with mock.patch.dict(os.environ, {"PRIVYHUB_CHEAT_DROPINS": "0"}):
            root2 = ps1_project(user={"mine.cht": USER_CHT})
            self.assertEqual(manager(root2).cheat_catalog(PS1), manager(root2)._cheat_catalog_base_unlocked(PS1))

    def test_no_manifest_still_lists_the_users(self):
        root = ps1_project(manifest=False, user={"mine.cht": USER_CHT})
        cat = manager(root).cheat_catalog(PS1)
        self.assertEqual((cat["status"], [s["filename"] for s in cat["sources"]]), ("cached", ["mine.cht"]))
        with mock.patch.dict(os.environ, {"PRIVYHUB_CHEAT_DROPINS": "0"}):
            with self.assertRaises(em.EmulatorError):                     # today: no manifest is an error
                manager(root).cheat_catalog(PS1)

    def test_only_ps1_and_snes(self):
        self.assertIsNone(cd.retro_dir(Path("/p"), "n64", "x"))
        self.assertIsNone(cd.retro_dir(Path("/p"), "ps1", ".."))
        self.assertEqual(cd.retro_dir(Path("/p"), "snes", "A Game"), Path("/p/data/games/retroarch/cheats/snes/A Game"))


class Folders(unittest.TestCase):
    def test_created_empty_once_and_not_with_the_knob_off(self):
        root = ps1_project()
        manager(root).cheat_catalog(PS1)
        for rel in ("data/games/retroarch/cheats/ps1", "data/games/retroarch/cheats/snes"):
            self.assertTrue((root / rel).is_dir())
            self.assertEqual(list((root / rel).iterdir()), [])
        self.assertEqual(cd.ensure_folders(root, ps2=True), ["data/games/ps2/cheats"])
        root2 = ps1_project()
        with mock.patch.dict(os.environ, {"PRIVYHUB_CHEAT_DROPINS": "0"}):
            manager(root2).cheat_catalog(PS1)
        self.assertFalse((root2 / "data/games/retroarch/cheats").exists())


class Pnach(unittest.TestCase):
    def test_groups_and_staging(self):
        d = Path(tempfile.mkdtemp(prefix="b81_p_"))
        (d / "a.pnach").write_text("[Made Up Lives]\npatch=1,EE,0,word,1\n")
        (d / "b.pnach").write_text("patch=1,EE,4,word,1\n[Made Up Lives]\n[Made Up Money]\npatch=1,EE,8,word,1\n")
        target, groups = cd.stage_pnach(d / "cheats", b80.SERIAL, "1234abcd", [d / "a.pnach", d / "b.pnach"])
        self.assertEqual(target.name, f"{b80.SERIAL}_{b80.CRC}.pnach")
        self.assertEqual(groups, ["Made Up Lives", "Made Up Money"])
        text = target.read_text()
        self.assertIn("patch=1,EE,0,word,1", text)
        self.assertIn("patch=1,EE,8,word,1", text)
        self.assertNotIn("a.pnach", text)
        with self.assertRaises(ValueError):
            cd.stage_pnach(d / "cheats", "../x", b80.CRC, [])

    def test_the_users_own_folder_from_the_paths_file(self):
        root = Path(tempfile.mkdtemp(prefix="b81_r_"))
        mine = Path(tempfile.mkdtemp(prefix="b81_mine_"))
        (mine / b80.SERIAL).mkdir()
        (mine / b80.SERIAL / "x.pnach").write_text("patch=1\n")
        paths = root / "paths.txt"
        paths.write_text(f"PS2_CHEATS_DIR={mine}\n")
        env = {"PRIVYHUB_PS2_PATHS": str(paths)}
        self.assertEqual([p.name for p in cd.pnach_files(root, b80.SERIAL, env)], ["x.pnach"])
        self.assertEqual(cd.pnach_files(root, b80.SERIAL, {"PRIVYHUB_PS2_PATHS": str(root / "none")}), [])


class PS2Launch(unittest.TestCase):
    """B49's rig: the PCSX2 launch in a subprocess (PRIVYHUB_PS2=1) with cheat arguments."""

    CODE_TAIL = '''
import json as _j
'''

    def setUp(self):
        self.games = ps2rig.tree({"one.chd": b"1"})
        self.bios = ps2rig.tree({"image.bin": b"\0" * ps2.BIOS_IMAGE_BYTES, "image.nvm": b"n"})

    def project(self, files=True):
        proj = ps2rig.tree({"runtime/emulators/pcsx2/pcsx2-fake.AppImage": b"x"})
        (proj / "runtime" / "h3_p1_paths.txt").write_text(f"BIOS_DIR={self.bios}\nGAMES_DIR={self.games}\n")
        (proj / "data/games/ps2/logs").mkdir(parents=True)
        (proj / "data/games/ps2/logs/20261101T000000Z-pcsx2.log").write_text(b80.log_text("one.chd"))
        if files:
            d = proj / "data/games/ps2/cheats" / b80.SERIAL
            d.mkdir(parents=True)
            (d / "first.pnach").write_text("[Made Up Lives]\npatch=1,EE,0,word,1\n")
            (d / "second.pnach").write_text("patch=1,EE,4,word,1\n")
        return proj

    def launch(self, proj, cheats=None, knob=None):
        code = ps2rig.LAUNCH_CODE
        if cheats is not None:
            code = code.replace('r = m.launch(game, players_chosen=int(os.environ["B49_PICK"]) if os.environ.get("B49_PICK") else None)',
                                f'r = m.launch(game, cheat_source_index=0, cheat_enabled_indexes={cheats!r})')
            assert "cheat_source_index=0" in code
        env = {"PATH": "/usr/bin:/bin", "B49_PROJ": str(proj), "PRIVYHUB_PS2": "1"}
        if knob is not None:
            env["PRIVYHUB_CHEAT_DROPINS"] = knob
        r = ps2rig.subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True)
        if r.returncode:
            raise AssertionError(r.stderr[-2000:])
        out = json.loads(r.stdout.strip().splitlines()[-1])
        gs = proj / "data/games/ps2/config/PCSX2/gamesettings"
        cheats_dir = proj / "data/games/ps2/config/PCSX2/cheats"
        logs = sorted((proj / "logs/games").glob("*-ps2.log"))
        # two launches in the same second share one log file (opened for append): the last session's part only
        text = logs[-1].read_text() if logs else ""
        return out, gs, cheats_dir, "PrivyHub game session (PS2)" + text.split("PrivyHub game session (PS2)")[-1]

    def test_listed_by_name(self):
        proj = self.project()
        old = em._ps2
        em._ps2 = ps2
        self.addCleanup(lambda: setattr(em, "_ps2", old))
        cat = manager(proj).cheat_catalog(b80.GAME)
        self.assertEqual([e["description"] for e in cat["sources"][0]["entries"]], ["first.pnach", "second.pnach"])
        self.assertNotIn(b80.SERIAL, json.dumps(cat))
        unknown = manager(proj).cheat_catalog({**b80.GAME, "id": "game_ps2_q", "relative_path": "ps2/unseen.chd"})
        self.assertEqual((unknown["status"], unknown["sources"]), ("unavailable", []))

    def test_a_cheat_launch_stages_and_switches_on_then_a_plain_launch_switches_off(self):
        proj = self.project()
        out, gs, cheats_dir, log = self.launch(proj, cheats=[0, 1])
        self.assertEqual(out["launch"]["launch_kind"], "pcsx2", out)
        staged = (cheats_dir / f"{b80.SERIAL}_{b80.CRC}.pnach").read_text()
        self.assertIn("patch=1,EE,0,word,1", staged)
        self.assertIn("patch=1,EE,4,word,1", staged)
        ini = (gs / f"{b80.CRC}.ini").read_text()
        self.assertIn("EnableCheats = true", ini)
        self.assertIn("[Cheats]\nEnable = Made Up Lives", ini)
        self.assertIn("PS2 cheats: 2 files enabled", log)
        self.assertNotIn("first.pnach", log)
        out2, gs2, _c, log2 = self.launch(proj)
        self.assertIn("EnableCheats = false", (gs2 / f"{b80.CRC}.ini").read_text())
        self.assertNotIn("PS2 cheats", log2)

    def test_knob_zero_is_today(self):
        proj = self.project()
        out, gs, cheats_dir, log = self.launch(proj, cheats=[0], knob="0")
        self.assertEqual(out["launch"]["launch_kind"], "pcsx2", out)
        self.assertFalse(cheats_dir.exists())
        self.assertFalse(gs.exists())
        self.assertNotIn("PS2 cheats", log)

    def test_a_bad_pick_refuses_before_anything_is_written(self):
        proj = self.project()
        out, gs, cheats_dir, _log = self.launch(proj, cheats=[5])
        self.assertEqual(out.get("error"), "EmulatorError")
        self.assertEqual(out["calls"]["popen"], [])
        self.assertFalse(cheats_dir.exists())

    def test_a_plain_launch_without_a_written_file_is_today(self):
        proj = self.project()
        out, gs, cheats_dir, log = self.launch(proj)
        self.assertFalse(gs.exists())
        self.assertFalse(cheats_dir.exists())


class Docs(unittest.TestCase):
    def test_cheats_md_names_the_folders(self):
        text = (ROOT / "docs/CHEATS.md").read_text()
        for needle in ("data/games/retroarch/cheats/ps1/", "data/games/retroarch/cheats/snes/", "data/games/ps2/cheats/",
                       ".pnach", ".cht", "PS2_CHEATS_DIR"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
