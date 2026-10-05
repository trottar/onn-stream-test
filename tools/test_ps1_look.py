#!/usr/bin/env python3
"""C5-M5B section 4: the PS1 look behind PRIVYHUB_PS1_LOOK (companion/games/ps1_look.py and its
use in EmulatorManager). Pre-registered in evidence/c5_m5b_2026-10-03/c5_m5b_preregistration.txt."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "companion"))

from games import ps1_look  # noqa: E402

ADOPTED = (
    'beetle_psx_hw_dither_mode = "1x(native)"\n'
    'beetle_psx_hw_filter = "nearest"\n'
    'beetle_psx_hw_filter_exclude_2d_polygon = "disabled"\n'
    'beetle_psx_hw_internal_resolution = "4x"\n'
    'beetle_psx_hw_msaa = "1x"\n'
    'beetle_psx_hw_pgxp_mode = "disabled"\n'
    'beetle_psx_hw_pgxp_nclip = "disabled"\n'
    'beetle_psx_hw_pgxp_texture = "disabled"\n'
    'beetle_psx_hw_pgxp_vertex = "disabled"\n'
)


class PS1Look(unittest.TestCase):
    def test_unset_and_4x_change_nothing(self):
        for env in ({}, {ps1_look.LOOK_ENV: ""}, {ps1_look.LOOK_ENV: "  "}):
            self.assertEqual(ps1_look.look_from_env(env), (None, {}, False))
        self.assertEqual(ps1_look.look_from_env({ps1_look.LOOK_ENV: "4x"}), ("4x", {}, False))
        self.assertEqual(ps1_look.look_from_env({ps1_look.LOOK_ENV: " 4X "}), ("4x", {}, False))

    def test_unknown_is_ignored_and_flagged(self):
        self.assertEqual(ps1_look.look_from_env({ps1_look.LOOK_ENV: "ultra"}), (None, {}, True))

    def test_remaster_is_the_full_preset_and_not_offered_at_the_rung(self):
        self.assertEqual(ps1_look.PRESETS["remaster"], ps1_look.MEASURE["measure-full"])
        self.assertFalse(ps1_look.REMASTER_AT_RUNG_OFFERED)
        self.assertEqual(ps1_look.look_from_env({ps1_look.LOOK_ENV: "remaster"})[0], "remaster")

    def test_offered_presets(self):
        # "4x" always; "remaster" only if the full preset held 60 (filled from the cost table).
        self.assertIn("4x", ps1_look.PRESETS)
        self.assertTrue(set(ps1_look.PRESETS) <= {"4x", "remaster"})
        self.assertFalse(any(k.startswith("measure-") for k in ps1_look.PRESETS))

    def test_session_options_replace_only_the_named_keys(self):
        keys = {"beetle_psx_hw_filter": "SABR", "beetle_psx_hw_dither_mode": "disabled"}
        out = ps1_look.session_options_text(ADOPTED, keys)
        self.assertIn('beetle_psx_hw_filter = "SABR"\n', out)
        self.assertIn('beetle_psx_hw_dither_mode = "disabled"\n', out)
        self.assertIn('beetle_psx_hw_filter_exclude_2d_polygon = "disabled"\n', out)   # a prefix twin untouched
        a, b = ADOPTED.splitlines(), out.splitlines()
        self.assertEqual(len(a), len(b))
        self.assertEqual(sum(1 for x, y in zip(a, b) if x != y), 2)
        self.assertEqual(ps1_look.session_options_text(ADOPTED, {}), ADOPTED)

    def test_every_preset_and_lever_applies_to_the_adopted_keys(self):
        for table in (ps1_look.PRESETS, ps1_look.MEASURE):
            for name, keys in table.items():
                out = ps1_look.session_options_text(ADOPTED, keys)
                for k, v in keys.items():
                    self.assertIn(f'{k} = "{v}"\n', out, name)

    def test_missing_key_and_unsafe_values_fail_closed(self):
        with self.assertRaises(ValueError):
            ps1_look.session_options_text(ADOPTED, {"beetle_psx_hw_no_such_key": "x"})
        with self.assertRaises(ValueError):
            ps1_look.session_options_text(ADOPTED, {"beetle_psx_hw_filter": 'a"b'})
        with self.assertRaises(ValueError):
            ps1_look.session_cfg_text("x", '/tmp/a"b')

    def test_cfg_lines(self):
        t = ps1_look.session_cfg_text("remaster", "/p/privyhub-look-session.opt")
        self.assertIn('global_core_options = "true"\n', t)
        self.assertIn('core_options_path = "/p/privyhub-look-session.opt"\n', t)
        self.assertIn("PRIVYHUB_PS1_LOOK=remaster", t)


class EmulatorManagerLook(unittest.TestCase):
    """The look through EmulatorManager on a temporary project: unset -> the session cfg byte-identical,
    a preset -> the session file + the two cfg lines, the end -> removed and any rewrite recorded; the
    adopted options file is only read."""

    def setUp(self):
        import os
        import tempfile
        from games import emulator_manager as em
        self.em, self.os = em, os
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "proj"
        (self.root / "data/games/retroarch/config").mkdir(parents=True)
        (self.root / "data/games/retroarch/autoconfig").mkdir(parents=True)
        self.base_cfg = self.root / "data/games/retroarch/retroarch.cfg"
        self.base_cfg.write_text('joypad_autoconfig_dir = "data/games/retroarch/autoconfig"\nvideo_vsync = "true"\n')
        self.override = self.root / "data/games/retroarch/config/input.cfg"
        self.override.write_text('network_cmd_enable = "true"\nnetwork_cmd_port = "55355"\n')
        self.cfgdir = self.tmp / "xdg" / "retroarch" / "config"
        (self.cfgdir / "Beetle PSX HW").mkdir(parents=True)
        self.adopted = self.cfgdir / "Beetle PSX HW" / "Beetle PSX HW.opt"
        self.adopted.write_text(ADOPTED)
        self.m = em.EmulatorManager.__new__(em.EmulatorManager)
        self.m.project_root = self.root.resolve()
        self.m._retroarch_config_directory = lambda runtime: self.cfgdir
        self.saved = os.environ.get(ps1_look.LOOK_ENV)
        self.game = {"id": "game_ps1_x", "system": "ps1"}
        self.core = Path("mednafen_psx_hw_libretro.so")

    def tearDown(self):
        import shutil
        if self.saved is None:
            self.os.environ.pop(ps1_look.LOOK_ENV, None)
        else:
            self.os.environ[ps1_look.LOOK_ENV] = self.saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cfg(self, look):
        info = self.m._prepare_ps1_look(self.game, {}, self.core)
        p = self.m._prepare_retroarch_session_config(self.base_cfg, self.override, look_override=info["cfg_text"])
        return info, p.read_text()

    def test_unset_and_4x_are_byte_identical_and_write_nothing(self):
        self.os.environ.pop(ps1_look.LOOK_ENV, None)
        p = self.m._prepare_retroarch_session_config(self.base_cfg, self.override)
        ref = p.read_text()
        for value in (None, "4x", "nonsense"):
            if value is None:
                self.os.environ.pop(ps1_look.LOOK_ENV, None)
            else:
                self.os.environ[ps1_look.LOOK_ENV] = value
            info, text = self.cfg(value)
            self.assertEqual(text, ref, value)
            self.assertFalse(info["applied"])
            self.assertFalse(self.m._ps1_look_session_options_path().exists())
        self.assertEqual(self.adopted.read_text(), ADOPTED)

    def test_preset_writes_the_session_file_and_points_the_launch_at_it(self):
        self.os.environ[ps1_look.LOOK_ENV] = "measure-pgxp"
        info, text = self.cfg("measure-pgxp")
        target = self.m._ps1_look_session_options_path()
        self.assertTrue(info["applied"])
        self.assertTrue(text.endswith('global_core_options = "true"\n'
                                      f'core_options_path = "{target}"\n'))
        self.assertIn('beetle_psx_hw_pgxp_mode = "memory only"', target.read_text())
        self.assertEqual(self.adopted.read_text(), ADOPTED)          # read, never written
        self.assertEqual(target.parent, (self.root / "data/games/retroarch/config").resolve())

    def test_not_a_beetle_launch_is_not_applied(self):
        self.os.environ[ps1_look.LOOK_ENV] = "measure-pgxp"
        info = self.m._prepare_ps1_look({"id": "g", "system": "snes"}, {}, Path("bsnes_libretro.so"))
        self.assertFalse(info["applied"])
        self.assertEqual(info["cfg_text"], "")
        self.assertFalse(self.m._ps1_look_session_options_path().exists())

    def test_session_end_removes_the_file_and_records_a_rewrite(self):
        self.os.environ[ps1_look.LOOK_ENV] = "measure-filter-xbr"
        self.cfg("x")
        target = self.m._ps1_look_session_options_path()
        target.write_text(target.read_text().replace('"xBR"', '"nearest"'))   # RetroArch rejected it on exit
        rec = self.m._end_ps1_look_session()
        self.assertTrue(rec["removed"])
        self.assertFalse(target.exists())
        self.assertEqual(rec["rewritten_keys"], {"beetle_psx_hw_filter": {"written": "xBR", "after_exit": "nearest"}})
        self.assertIsNone(self.m._end_ps1_look_session())                 # nothing left to end
        log = self.root / "logs/games/ps1_look_sessions.jsonl"
        self.assertEqual(len(log.read_text().splitlines()), 1)

    def test_a_stale_file_never_carries_into_the_next_launch(self):
        target = self.m._ps1_look_session_options_path()
        target.write_text("stale")
        self.os.environ.pop(ps1_look.LOOK_ENV, None)
        self.cfg(None)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
