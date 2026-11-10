#!/usr/bin/env python3
"""B77 (host): the onn's Input Profiles applied at PS2 (PCSX2 PAD bindings) and GameCube (Dolphin GCPadNew.ini)
launches; the Default profile = today's files byte for byte; PRIVYHUB_PROFILES_EXT=0 = today; N64's path checked.

Fakes only: B49's PCSX2 launch rig (a subprocess with a fake Popen / Session) and B69's Dolphin rig (a fake Dolphin);
no emulator is started, nothing is fetched; temp dirs removed at exit.

    python3 -m unittest discover -s tests/art_systems -p 'test_b77.py' -v
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

import gamecube_session as gc  # noqa: E402
import profile_layouts as pl  # noqa: E402
import ps2_session as ps2  # noqa: E402
from games import emulator_manager as em  # noqa: E402

sys.path.insert(0, str(ROOT / "tests" / "ps2_session"))
sys.path.insert(0, str(ROOT / "tests" / "gamecube_session"))
import test_ps2_session as ps2rig  # noqa: E402
import test_gamecube_session as gcrig  # noqa: E402

IDENTITY = dict(em.EmulatorManager.INPUT_PROFILE_EDITOR_DEFAULT_MAPPING)
SWAP = {"b": "b", "a": "a"}          # the bottom and right face buttons swapped (RetroPad target <- physical source)
CONFIG = ROOT / "companion/games/config/emulators.json"


def setup_profile(proj: Path, game_id: str, mapping: dict | None) -> None:
    """The fixture project's input_profiles.json through the manager's own API (as the onn's editor writes it)."""
    m = em.EmulatorManager(proj, config_path=CONFIG)
    if mapping is None:
        return
    if not set(mapping) <= set(pl.PLAYERS):
        mapping = {"player1": mapping}       # a single player's mapping is player 1's
    created = m.create_input_profile("Made Up", mapping)
    pid = created.get("profile", created).get("id")
    m.assign_input_profile({"id": game_id, "system": "x"}, pid)


class Translation(unittest.TestCase):
    def test_default_and_identity_are_todays_tables(self):
        for mapping in (None, {}, IDENTITY):
            self.assertEqual(pl.ds2_bindings(mapping, ps2.DS2_BINDINGS), ps2.DS2_BINDINGS)
            self.assertEqual(pl.gc_layout(mapping, gc.PAD_LAYOUT), gc.PAD_LAYOUT)
        self.assertTrue(pl.is_default({"player1": IDENTITY, "player3": {}}))

    def test_a_swap_on_both(self):
        ds2 = dict(pl.ds2_bindings(SWAP, ps2.DS2_BINDINGS))
        self.assertEqual((ds2["Cross"], ds2["Circle"]), ("FaceEast", "FaceSouth"))
        today = dict(ps2.DS2_BINDINGS)
        self.assertEqual({k: v for k, v in ds2.items() if k not in ("Cross", "Circle")},
                         {k: v for k, v in today.items() if k not in ("Cross", "Circle")})
        gcl = dict(pl.gc_layout(SWAP, gc.PAD_LAYOUT))
        self.assertEqual((gcl["Buttons/A"], gcl["Buttons/X"]), ("EAST", "SOUTH"))
        base = dict(gc.PAD_LAYOUT)
        self.assertEqual({k: v for k, v in gcl.items() if k not in ("Buttons/A", "Buttons/X")},
                         {k: v for k, v in base.items() if k not in ("Buttons/A", "Buttons/X")})

    def test_the_sticks(self):
        legacy = dict(pl.ds2_bindings({"left_x": "right_x"}, ps2.DS2_BINDINGS))
        self.assertEqual((legacy["LLeft"], legacy["LRight"], legacy["LUp"]), ("-RightX", "+RightX", "-LeftY"))
        direct = dict(pl.gc_layout({"left_stick_up": "right_stick_up"}, gc.PAD_LAYOUT))
        self.assertEqual((direct["Main Stick/Up"], direct["Main Stick/Down"]), ("Axis 4-", "Axis 1+"))
        legacy_gc = dict(pl.gc_layout({"right_y": "left_y"}, gc.PAD_LAYOUT))
        self.assertEqual((legacy_gc["C-Stick/Up"], legacy_gc["C-Stick/Down"]), ("Axis 1-", "Axis 1+"))

    def test_legacy_axis_applied_after_directional(self):
        d = dict(pl.ds2_bindings({"left_stick_left": "a", "left_x": "right_x"}, ps2.DS2_BINDINGS))
        self.assertEqual(d["LLeft"], "-RightX")

    def test_a_trigger_onto_a_button(self):
        g = dict(pl.gc_layout({"l2": "a"}, gc.PAD_LAYOUT))
        self.assertEqual((g["Triggers/L"], g["Triggers/L-Analog"]), ("SOUTH", "SOUTH"))
        d = dict(pl.ds2_bindings({"l2": "a"}, ps2.DS2_BINDINGS))
        self.assertEqual(d["L2"], "FaceSouth")

    def test_per_player(self):
        tables = pl.per_player({"player2": SWAP}, "ps2", ps2.DS2_BINDINGS)
        self.assertEqual(tables[0], ps2.DS2_BINDINGS)
        self.assertEqual(dict(tables[1])["Cross"], "FaceEast")
        self.assertEqual(pl.overridden_players({"player2": SWAP}), 1)
        secs = ps2.pad_sections(2, False, tables)
        self.assertEqual((secs["Pad1"]["Cross"], secs["Pad2"]["Cross"]), ("SDL-0/FaceSouth", "SDL-1/FaceEast"))
        ini = gc.gcpad_ini(pl.per_player({"player2": SWAP}, "gamecube", gc.PAD_LAYOUT))
        self.assertIn("[GCPad2]\nDevice = evdev/0/PrivyHub Virtual Gamepad P2\nButtons/A = `EAST`", ini)
        self.assertIn("[GCPad1]\nDevice = evdev/0/PrivyHub Virtual Gamepad P1\nButtons/A = `SOUTH`", ini)

    def test_the_default_text_is_todays_bytes(self):
        tables = pl.per_player({}, "ps2", ps2.DS2_BINDINGS)
        for players, tap in ((1, False), (2, False), (4, True)):
            self.assertEqual(ps2.pad_sections(players, tap, tables), ps2.pad_sections(players, tap))
        self.assertEqual(gc.gcpad_ini(pl.per_player({}, "gamecube", gc.PAD_LAYOUT)), gc.gcpad_ini())
        self.assertEqual(gc.config_files(), gc.config_files(None))

    def test_the_knob(self):
        self.assertTrue(pl.enabled({}))
        self.assertTrue(pl.enabled({"PRIVYHUB_PROFILES_EXT": "1"}))
        self.assertFalse(pl.enabled({"PRIVYHUB_PROFILES_EXT": "0"}))


class PS2Launch(unittest.TestCase):
    """B49's rig: the launch in a subprocess with PRIVYHUB_PS2=1, a fake Popen and a fake Session."""

    def setUp(self):
        self.games = ps2rig.tree({"one.chd": b"1"})
        self.bios = ps2rig.tree({"image.bin": b"\0" * ps2.BIOS_IMAGE_BYTES, "image.nvm": b"n"})
        self.ini = None

    def launch(self, mapping, knob=None):
        proj = ps2rig.tree({"runtime/emulators/pcsx2/pcsx2-fake.AppImage": b"x"})
        (proj / "runtime" / "h3_p1_paths.txt").write_text(f"BIOS_DIR={self.bios}\nGAMES_DIR={self.games}\n")
        setup_profile(proj, "game_ps2_x", mapping)
        env_extra = {} if knob is None else {"PRIVYHUB_PROFILES_EXT": knob}
        with mock.patch.dict(os.environ, env_extra):
            real_run = ps2rig.subprocess.run

            def run(cmd, **kw):
                kw["env"] = {**kw.get("env", {}), **env_extra}
                return real_run(cmd, **kw)
            with mock.patch.object(ps2rig.subprocess, "run", run):
                out = ps2rig.run_launch("1", proj)
        self.assertEqual(out["launch"]["launch_kind"], "pcsx2", out)
        ini = proj / "data/games/ps2/config/PCSX2/inis/PCSX2.ini"
        log = next((proj / "logs/games").glob("*-ps2.log")).read_text()
        # each launch has its own fixture project: its path is the only difference to take out
        return ini.read_text().replace(str(proj.resolve()), "<proj>").replace(str(proj), "<proj>"), log

    def test_a_swap_reaches_pad_ini(self):
        text, log = self.launch(SWAP)
        self.assertEqual(ps2.ini_get(text, "Pad1", "Cross"), "SDL-0/FaceEast")
        self.assertEqual(ps2.ini_get(text, "Pad1", "Circle"), "SDL-0/FaceSouth")
        self.assertEqual(ps2.ini_get(text, "Pad2", "Cross"), "SDL-1/FaceSouth")   # player 2: no override
        self.assertIn("PS2 input profile: assigned overrides=1", log)
        self.assertNotIn("Made Up", log)

    def test_default_profile_is_todays_bytes(self):
        today, log_today = self.launch(None, knob="0")
        default, log_default = self.launch(None)
        identity, _ = self.launch({p: IDENTITY for p in pl.PLAYERS})
        self.assertEqual(default, today)
        self.assertEqual(identity, today)
        self.assertNotIn("input profile", log_today)
        self.assertIn("PS2 input profile: default overrides=0", log_default)

    def test_knob_zero_ignores_the_swap(self):
        today, _ = self.launch(None, knob="0")
        off, log = self.launch(SWAP, knob="0")
        self.assertEqual(off, today)
        self.assertNotIn("input profile", log)


class GCLaunch(gcrig.Rig):
    """B69's rig: the manager in process with a fake Dolphin."""

    def launch_with(self, mapping, knob=None):
        setup_profile(self.proj, "game_gc_fake", mapping)
        env = {} if knob is None else {"PRIVYHUB_PROFILES_EXT": knob}
        with mock.patch.dict(os.environ, env):
            m, r = self.launch()
        text = (self.user / "Config" / "GCPadNew.ini").read_text()
        log = self.log_text()
        m.stop()
        for p in (self.proj / "logs/games").glob("*-gamecube.log"):
            p.unlink()
        return text, log

    def test_a_swap_reaches_gcpadnew(self):
        text, log = self.launch_with(SWAP)
        self.assertIn("[GCPad1]\nDevice = evdev/0/PrivyHub Virtual Gamepad P1\nButtons/A = `EAST`\nButtons/B = `WEST`\n"
                      "Buttons/X = `SOUTH`", text)
        self.assertIn("[GCPad2]\nDevice = evdev/0/PrivyHub Virtual Gamepad P2\nButtons/A = `SOUTH`", text)
        self.assertIn("GC input profile: assigned overrides=1", log)

    def test_default_is_todays_bytes_and_knob_zero(self):
        self.assertEqual(self.launch_with(None)[0], gc.gcpad_ini())
        self.assertEqual(self.launch_with(SWAP, knob="0")[0], gc.gcpad_ini())

    def test_other_config_files_unchanged_by_a_profile(self):
        self.launch_with(SWAP)
        for name in ("Dolphin.ini", "GFX.ini", "Hotkeys.ini", "Logger.ini"):
            self.assertEqual((self.user / "Config" / name).read_text(), gc.config_files()[name])

    def test_an_unusable_profile_is_todays_layout_and_logged(self):
        setup_profile(self.proj, "game_gc_fake", SWAP)
        path = self.proj / "data/games/input_profiles.json"
        data = json.loads(path.read_text())
        data["profiles"][0]["mapping"]["player1"]["a"] = "not_a_button"
        path.write_text(json.dumps(data))
        m, r = self.launch()
        self.assertEqual((self.user / "Config" / "GCPadNew.ini").read_text(), gc.gcpad_ini())
        self.assertIn("GC input profile: unusable", self.log_text())


class N64(unittest.TestCase):
    def test_the_profile_reaches_retroarchs_lines(self):
        effective = {"source": "game_assignment",
                     "profile": {"mapping": {"player1": SWAP, "player2": {}, "player3": {}, "player4": {}}}}
        lines = em.EmulatorManager._a8_retroarch_profile_lines(effective, runtime_platform="linux")
        self.assertIn('input_player1_b_btn = "1"', lines)   # RetroPad B (bottom) <- the physical right button
        self.assertIn('input_player1_a_btn = "0"', lines)

    def test_the_n64_launch_takes_the_input_override(self):
        src = (ROOT / "companion/games/emulator_manager.py").read_text()
        body = src[src.index("    def launch(\n"):]
        body = body[:body.index("\n    def ", 10)]
        self.assertIn("n64_launch = _n64 is not None", body)
        n64_at = body.index("if n64_launch:")
        override_at = body.index("self._prepare_input_override(")
        self.assertLess(n64_at, override_at)
        # no early return for N64 between the branch and the input override (only PS2 / GameCube return early)
        self.assertNotIn("return self._launch", body[n64_at:override_at])


if __name__ == "__main__":
    unittest.main()
