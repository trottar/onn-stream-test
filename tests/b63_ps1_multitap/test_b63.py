#!/usr/bin/env python3
"""B63 (host): the PS1 multitap only for a multitap-capable title -- the capability from the metadata, the plan's cap
(2 ports, the multitap off) for a join / pick on any other PS1 title, the echo the client reads, the relaunch refused,
the knob `PRIVYHUB_PS1_MULTITAP_CAPABILITY=0` = today. Fakes only; temp dirs removed at exit.

    python3 -m unittest discover -s tests/b63_ps1_multitap -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401
sys.path.insert(0, str(ROOT / "tests" / "n64_session"))

import players_session as ps  # noqa: E402
import relaunch_ports as rp  # noqa: E402
from games import emulator_manager as em  # noqa: E402
from test_n64_session import fake_project, run_launch, tree  # noqa: E402

CAPABLE = "game_ps1_aaaaaaaaaaaaaaaa"
OFF = "game_ps1_bbbbbbbbbbbbbbbb"
UNKNOWN = "game_ps1_cccccccccccccccc"
FLAGGED = "game_ps1_dddddddddddddddd"
OVERRIDES = {CAPABLE: {"ps1_multitap": "port1", "controller_profile": "dualshock"}, OFF: {"ps1_multitap": "off"},
             FLAGGED: {"ps1_multitap_capable": True}}


def write_overrides(proj: Path) -> None:
    p = proj / "data/games/retroarch/controller_overrides.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"version": 1, "games": OVERRIDES}))


class Plan(unittest.TestCase):
    def test_capable_and_not(self):
        p = ps.plan("ps1", 4, 1, capable=True)
        self.assertEqual((p["ports"], p["multitap"], p["ps1_mode"], p["capable"]), (4, True, "port1", True))
        self.assertNotIn("capped_from", p)
        p = ps.plan("ps1", 4, 1, source="join", capable=False)
        self.assertEqual((p["ports"], p["multitap"], p["multitap_available"], p["ps1_mode"], p["capped_from"]),
                         (2, False, False, "off", 4))
        self.assertEqual(p["device_args"], ["--device=1:1", "--device=2:1"])
        self.assertEqual(ps.plan("ps1", 1, 1, capable=False)["ports"], 1)

    def test_none_is_todays_plan_and_other_systems(self):
        self.assertEqual(ps.plan("ps1", 4, 1), {"players_chosen": 4, "ports": 4, "multitap": True,
                                                "multitap_available": True, "ps1_mode": "port1",
                                                "device_args": [f"--device={i}:1" for i in range(1, 5)],
                                                "source": "launch"})
        for system in ("snes", "ps2", "n64"):
            self.assertEqual(ps.plan(system, 4, None, capable=False), ps.plan(system, 4, None))


class Capability(unittest.TestCase):
    def setUp(self):
        self.proj = Path(tempfile.mkdtemp(prefix="b63_proj_"))
        write_overrides(self.proj)
        self.m = em.EmulatorManager(self.proj)

    def test_from_the_metadata(self):
        g = lambda gid, system="ps1": {"id": gid, "system": system}
        self.assertTrue(self.m.ps1_multitap_capable(g(CAPABLE)))
        self.assertTrue(self.m.ps1_multitap_capable(g(FLAGGED)))
        self.assertFalse(self.m.ps1_multitap_capable(g(OFF)))
        self.assertFalse(self.m.ps1_multitap_capable(g(UNKNOWN)))
        self.assertFalse(self.m.ps1_multitap_capable(g(CAPABLE, "snes")))
        self.assertFalse(self.m.ps1_multitap_capable({"id": "bad id!", "system": "ps1"}))

    def test_the_knob(self):
        self.assertTrue(ps.capability_rule_on({}))
        self.assertTrue(ps.capability_rule_on({ps.CAPABILITY_ENV: "1"}))
        self.assertFalse(ps.capability_rule_on({ps.CAPABILITY_ENV: "0"}))


class Echo(unittest.TestCase):
    def emu(self, session=None, capable=False, multitap_on=False):
        return types.SimpleNamespace(_players_session=session, active_game={"id": OFF, "system": "ps1"},
                                     ps1_multitap_capable=lambda game: capable,
                                     ps1_multitap=lambda game: {"enabled": multitap_on})

    def test_a_capped_join_says_two_and_no_multitap(self):
        got = ps.ports_set(self.emu(ps.plan("ps1", 4, 1, source="join", capable=False)), None)["ports_set"]
        self.assertEqual({k: got[k] for k in ("players", "multitap", "multitap_available", "capable", "capped_from")},
                         {"players": 2, "multitap": False, "multitap_available": False, "capable": False,
                          "capped_from": 4})

    def test_the_metadata_fallback(self):
        self.assertFalse(ps.ports_set(self.emu(), None)["ports_set"]["multitap_available"])
        self.assertTrue(ps.ports_set(self.emu(capable=True), None)["ports_set"]["multitap_available"])
        self.assertTrue(ps.ports_set(self.emu(multitap_on=True), None)["ports_set"]["multitap_available"])
        old = os.environ.get(ps.CAPABILITY_ENV)
        os.environ[ps.CAPABILITY_ENV] = "0"
        try:
            got = ps.ports_set(self.emu(), None)["ports_set"]
            self.assertTrue(got["multitap_available"])
            self.assertNotIn("capable", got)
        finally:
            os.environ.pop(ps.CAPABILITY_ENV) if old is None else os.environ.__setitem__(ps.CAPABILITY_ENV, old)


class Relaunch(unittest.TestCase):
    def plugin(self, capable):
        calls = []
        emu = types.SimpleNamespace(status=lambda: {"active": True, "paused": False},
                                    active_game={"id": OFF, "system": "ps1"}, ps1_multitap_capable=lambda g: capable,
                                    pause=lambda: calls.append("pause"), stop=lambda: calls.append("stop"))
        return types.SimpleNamespace(_emulator=emu, _native_stream=types.SimpleNamespace(stop=lambda: calls.append(
            "stream_stop")), _recovery_start_args={}), calls

    def test_incapable_refused_nothing_stopped(self):
        plugin, calls = self.plugin(False)
        with self.assertRaises(rp.RelaunchRefused) as cm:
            rp.run(plugin, 4, 3)
        self.assertEqual(str(cm.exception), "This game supports 2 players")
        self.assertEqual(calls, [])

    def test_capable_passes_the_rule(self):
        plugin, calls = self.plugin(True)
        with self.assertRaises(rp.RelaunchRefused) as cm:          # stops later, at the next check (no client)
            rp.run(plugin, 4, 3)
        self.assertNotEqual(str(cm.exception), "This game supports 2 players")


class Launch(unittest.TestCase):
    """A PS1 launch through B59's fake RetroArch tree: the join's 3 -> 4 asked, capped to 2 on an incapable title."""

    def setUp(self):
        self.proj = fake_project(tree({}), cores=("mednafen_psx_hw_libretro.so",))
        (self.proj / "games/ps1").mkdir(parents=True, exist_ok=True)
        (self.proj / "games/ps1/made-up.cue").write_text('FILE "made-up.bin" BINARY\n')
        (self.proj / "games/ps1/made-up.bin").write_bytes(b"\0" * 16)
        write_overrides(self.proj)
        self.xdg = Path(tempfile.mkdtemp(prefix="b63_xdg_"))
        base = self.xdg / "retroarch/config/Beetle PSX HW/Beetle PSX HW.opt"
        base.parent.mkdir(parents=True)
        base.write_text('beetle_psx_hw_enable_multitap_port1 = "enabled"\nbeetle_psx_hw_enable_multitap_port2 = '
                        '"disabled"\n')

    def launch(self, gid, extra=None):
        game = {"id": gid, "system": "ps1", "title": "made-up", "relative_path": "games/ps1/made-up.cue"}
        out = run_launch(None, self.proj, game, joined=3, xdg=self.xdg, extra=extra)
        opt = (self.xdg / "retroarch/config/Beetle PSX HW/made-up.opt").read_text()
        return out, opt

    def test_incapable_is_capped_to_two(self):
        out, opt = self.launch(OFF)
        dev = [a for a in out["calls"][0] if a.startswith("--device=")]
        self.assertEqual(len(dev), 2, dev)
        self.assertIn('beetle_psx_hw_enable_multitap_port1 = "disabled"', opt)
        self.assertIn("PS1 multitap: off", out["log"])
        self.assertIn("PS1 ports capped: 4 -> 2 (not multitap-capable)", out["log"])
        self.assertEqual((out["ports_set"]["players"], out["ports_set"]["multitap_available"]), (2, False))

    def test_capable_keeps_the_multitap(self):
        out, opt = self.launch(CAPABLE)
        self.assertEqual(len([a for a in out["calls"][0] if a.startswith("--device=")]), 4)
        self.assertIn('beetle_psx_hw_enable_multitap_port1 = "enabled"', opt)
        self.assertNotIn("PS1 ports capped", out["log"])

    def test_the_knob_zero_is_today(self):
        out, opt = self.launch(OFF, extra={ps.CAPABILITY_ENV: "0"})
        self.assertEqual(len([a for a in out["calls"][0] if a.startswith("--device=")]), 4)
        self.assertIn('beetle_psx_hw_enable_multitap_port1 = "enabled"', opt)
        self.assertNotIn("capable", out["ports_set"])


if __name__ == "__main__":
    unittest.main()
