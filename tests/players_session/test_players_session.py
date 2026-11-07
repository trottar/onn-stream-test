#!/usr/bin/env python3
"""B46 (host): the chooser's pick (`players_chosen`) sets the session's ports at the launch -- the PS1 multitap `.opt`
and the `--device` arguments -- read back from what was written; the start response's `ports_set`; the `pad_slots`
rows' `players_chosen` / `label`. Without the key: today (the launch call, the `.opt` path, the arguments, the rows).

    python3 -m unittest discover -s tests/players_session -v
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

from games import emulator_manager as em  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402
import pad_slots  # noqa: E402
import players_session as ps  # noqa: E402

spec = importlib.util.spec_from_file_location("b46_games_plugin", ROOT / "companion" / "plugins" / "games.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

BASE_OPT = 'beetle_psx_hw_renderer = "hardware"\nbeetle_psx_hw_enable_multitap_port1 = "disabled"\n'
TWO = "0:a1b2c3:sony,1:d4e5f6:sony"
HB = "sequence={}&interval_ms=2000&last_output_age_ms=16&rendered_frames=600&queued_frames=0&rx_packets=900&elapsed_ms=10000"


def manager(overrides=None):
    """A bare EmulatorManager on a temp project and a temp RetroArch config tree (no RetroArch, no launch)."""
    root = Path(tempfile.mkdtemp(prefix="b46_root_"))
    cfg = root / "ra_config"
    (cfg / "Beetle PSX HW").mkdir(parents=True)
    (cfg / "Beetle PSX HW" / "Beetle PSX HW.opt").write_text(BASE_OPT)
    m = object.__new__(em.EmulatorManager)
    m.project_root = root.resolve()
    m._players_session = None
    m._load_controller_overrides = lambda: {"games": dict(overrides or {})}
    m._retroarch_config_directory = lambda runtime: cfg.resolve()
    m._retroarch_options_metadata_path = lambda target, config_directory, platform: target.name
    return m, root, cfg


GAME = {"id": "ps1-title-1", "system": "ps1"}
CONTENT = Path("/nowhere/content-one.chd")
RUNTIME = {"runtime_platform": "linux"}


def opt_text(cfg):
    p = cfg / "Beetle PSX HW" / "content-one.opt"
    return p.read_text() if p.exists() else None


class Plan(unittest.TestCase):
    def test_parse(self):
        self.assertEqual([ps.parse(x) for x in ("1", "2", "4", " 4 ")], [1, 2, 4, 4])
        for bad in ("3", "0", "", "x", None, "5"):
            self.assertIsNone(ps.parse(bad))

    def test_ps1(self):
        self.assertEqual(ps.plan("ps1", 1, 1)["device_args"], ["--device=1:1", "--device=2:0"])
        self.assertEqual(ps.plan("ps1", 2, 517)["device_args"], ["--device=1:517", "--device=2:517"])
        p4 = ps.plan("ps1", 4, 1)
        self.assertEqual(p4["device_args"], ["--device=%d:1" % i for i in range(1, 5)])
        self.assertEqual((p4["ps1_mode"], p4["ports"], p4["multitap"]), ("port1", 4, True))
        self.assertEqual(ps.plan("ps1", 2, 1)["ps1_mode"], "off")

    def test_snes_and_others(self):
        self.assertEqual(ps.plan("snes", 4, None)["device_args"], ["--device=2:257"])
        self.assertEqual(ps.plan("snes", 2, None)["device_args"], [])
        self.assertEqual(ps.plan("snes", 1, None)["device_args"], ["--device=2:0"])
        n4 = ps.plan("nes", 4, None)
        self.assertEqual((n4["device_args"], n4["ports"], n4["multitap"], n4["multitap_available"]), ([], 2, False, False))
        self.assertEqual(ps.plan("genesis", 1, None)["device_args"], ["--device=2:0"])


class DeviceArgs(unittest.TestCase):
    def test_no_pick_is_todays_list(self):
        m, _, _ = manager()
        m.INPUT_PROFILE_PLAYERS = em.EmulatorManager.INPUT_PROFILE_PLAYERS
        self.assertEqual(m._device_args({"libretro_device": 1}, {"enabled": False}), ["--device=1:1", "--device=2:1"])
        self.assertEqual(m._device_args({"libretro_device": 517}, {"enabled": True}),
                         ["--device=%d:517" % i for i in range(1, 5)])
        self.assertEqual(m._device_args({"libretro_device": None}, {"enabled": False}), [])

    def test_a_pick_replaces_the_list(self):
        m, _, _ = manager()
        self.assertEqual(m._device_args({"libretro_device": 1}, {"enabled": False}, ps.plan("ps1", 1, 1)),
                         ["--device=1:1", "--device=2:0"])
        self.assertEqual(m._device_args({"libretro_device": None}, {"enabled": False}, ps.plan("snes", 4, None)),
                         ["--device=2:257"])


class Opt(unittest.TestCase):
    def test_no_pick_and_no_metadata_writes_nothing(self):
        m, root, cfg = manager()
        r = m._prepare_ps1_multitap_options(GAME, RUNTIME, CONTENT)
        self.assertFalse(r["managed"])
        self.assertIsNone(opt_text(cfg))
        self.assertFalse((root / ps_opts()).exists())

    def test_a_pick_of_multitap_writes_port1_and_reads_back(self):
        m, root, cfg = manager()
        r = m._prepare_ps1_multitap_options(GAME, RUNTIME, CONTENT, session_mode="port1")
        self.assertTrue(r["managed"] and r["enabled"] and r["port1"])
        self.assertIn('beetle_psx_hw_enable_multitap_port1 = "enabled"', opt_text(cfg))
        self.assertIn('beetle_psx_hw_enable_multitap_port2 = "disabled"', opt_text(cfg))
        self.assertEqual(len(json.loads((root / ps_opts()).read_text())["stems"]), 1)   # listed, by hash
        self.assertNotIn("content-one", (root / ps_opts()).read_text())

    def test_a_pick_of_two_overrides_a_metadata_multitap_without_writing_it(self):
        over = {"ps1-title-1": {"ps1_multitap": "port1"}}
        m, root, cfg = manager(over)
        r = m._prepare_ps1_multitap_options(GAME, RUNTIME, CONTENT, session_mode="off")
        self.assertFalse(r["enabled"])
        self.assertIn('beetle_psx_hw_enable_multitap_port1 = "disabled"', opt_text(cfg))
        self.assertEqual(over, {"ps1-title-1": {"ps1_multitap": "port1"}})        # the metadata untouched

    def test_the_stale_guard(self):
        m, root, cfg = manager()
        m._prepare_ps1_multitap_options(GAME, RUNTIME, CONTENT, session_mode="port1")
        # the same title launched later with no pick and no metadata value: rewritten off, unlisted
        r = m._prepare_ps1_multitap_options(GAME, RUNTIME, CONTENT)
        self.assertTrue(r["managed"]); self.assertFalse(r["enabled"])
        self.assertIn('beetle_psx_hw_enable_multitap_port1 = "disabled"', opt_text(cfg))
        self.assertEqual(json.loads((root / ps_opts()).read_text())["stems"], [])
        # and then today's path: nothing managed
        self.assertFalse(m._prepare_ps1_multitap_options(GAME, RUNTIME, CONTENT)["managed"])
        # a title never picked is untouched even with the list present
        other = Path("/nowhere/content-two.chd")
        self.assertFalse(m._prepare_ps1_multitap_options({"id": "ps1-title-2", "system": "ps1"}, RUNTIME, other)["managed"])
        # a non-PS1 title is never guarded
        m._prepare_ps1_multitap_options(GAME, RUNTIME, CONTENT, session_mode="port1")
        self.assertFalse(m._prepare_ps1_multitap_options({"id": "snes-1", "system": "snes"}, RUNTIME, CONTENT)["managed"])


def ps_opts():
    return em.EmulatorManager.PLAYERS_SESSION_OPTS


def plugin(launched=None, system="ps1", multitap=False):
    root = Path(tempfile.mkdtemp(prefix="b46_plug_"))
    rec = ldr.LinkDropRecovery(
        root, pause_game=lambda: None, resume_game=lambda: None, save_recovery_state=lambda: {},
        restart_encoder=lambda: {}, full_start_encoder=lambda: {}, stream_active=lambda: True,
        end_session=lambda: None, client_packet_age_ms=lambda: 10.0, recovery_save_detail=lambda: {})
    calls = []

    class Emu:
        active_game = {"id": "g1", "system": system, "title": "t"}
        _players_session = launched

        def status(self):
            return {"active": True, "paused": True, "pid": 1}

        def ps1_multitap(self, g):
            return {"enabled": multitap}

        def launch(self, game, **kw):
            calls.append(kw)
            return {"active": True}

    class Ctl:
        def status(self):
            return {"updates_by_player": [1, 0, 0, 0]}

    p = object.__new__(G.GamesPlugin)
    p.PROJECT_ROOT = root
    p._emulator = Emu()
    p._recovery = rec
    p._native_stream = types.SimpleNamespace(start=lambda **kw: {"active": True},
                                             _session_io=types.SimpleNamespace(controller=Ctl()))
    p._diagnostic_heartbeat_interval_ms = lambda: 2000
    p._adaptive_bitrate_session_ended = lambda: None
    p._read_library_state = lambda: {"games": {}}
    p._decorate_game = lambda g, lib, st, md: {**g, "player_mode": "", "player_mode_source": "", "max_players": 0}
    p._find_game_by_id = lambda gid: {"id": gid, "system": system}
    p._parse_cheat_launch_request = lambda q: (None, None)
    return p, root, rec, calls


class Handler(unittest.TestCase):
    def test_the_launch_passes_the_pick_only_when_present(self):
        p, _, _, calls = plugin()
        p.handle_post("launch", "id=g1")
        p.handle_post("launch", "id=g1&players_chosen=4")
        p.handle_post("launch", "id=g1&players_chosen=3")          # malformed: today's call
        self.assertEqual(calls, [{"cheat_source_index": None, "cheat_enabled_indexes": None, "mod_index": None},
                                 {"cheat_source_index": None, "cheat_enabled_indexes": None, "mod_index": None,
                                  "players_chosen": 4},
                                 {"cheat_source_index": None, "cheat_enabled_indexes": None, "mod_index": None}])

    def test_ports_set_echoes_the_launch_else_the_metadata(self):
        p, _, _, _ = plugin(launched=ps.plan("ps1", 4, 1))
        r = p.handle_post_request("native-stream-start", "port=48100&player_prompt=1", "127.0.0.1")
        self.assertEqual(r["ports_set"], {"players_chosen": 4, "ports": 4, "players": 4, "multitap": True,
                                          "multitap_available": True, "source": "launch"})
        p2, _, _, _ = plugin(multitap=True)
        self.assertEqual(p2.handle_post_request("native-stream-start", "port=48100&player_prompt=1",
                                                "127.0.0.1")["ports_set"]["source"], "metadata")
        self.assertEqual(p2.handle_post_request("native-stream-start", "port=48100&player_prompt=1",
                                                "127.0.0.1")["ports_set"]["players"], 4)
        p3, _, _, _ = plugin(system="nes")
        self.assertFalse(p3.handle_post_request("native-stream-start", "port=48100&player_prompt=1",
                                                "127.0.0.1")["ports_set"]["multitap_available"])
        # no prompt key: no ports_set (today)
        self.assertNotIn("ports_set", p.handle_post_request("native-stream-start", "port=48100", "127.0.0.1"))

    def test_the_rows_carry_the_pick_and_the_labels(self):
        p, root, rec, _ = plugin()
        p.handle_post_request("native-stream-start", "port=48100&player_prompt=1&pad_slots=" + TWO + "&pad_claims=0:s,1:s", "127.0.0.1")
        p.handle_post_request("native-stream-heartbeat",
                              HB.format(1) + "&pad_slots=" + TWO + "&pad_claims=0:p,1:p&players_chosen=2", "127.0.0.1")
        p.handle_post_request("native-stream-heartbeat",
                              HB.format(2) + "&pad_slots=" + TWO + "&pad_claims=0:p,1:p&players_chosen=2", "127.0.0.1")
        rows = [json.loads(x) for x in rec.log_path().read_text().splitlines()]
        rows = [r for r in rows if r["event"] == "pad_slots"]
        self.assertEqual([r["when"] for r in rows], ["start", "change"])
        self.assertNotIn("players_chosen", rows[0])
        self.assertEqual(rows[1]["players_chosen"], 2)
        self.assertEqual([(e["label"], e["claimed_by"]) for e in rows[1]["slots"]], [("P1", "prompt"), ("P2", "prompt")])
        hb = [json.loads(x) for x in (root / "logs" / "games" / "native_stream_heartbeat.log").read_text().splitlines()]
        self.assertEqual(hb[-1]["players_chosen"], 2)

    def test_without_the_pick_the_rows_are_b41s(self):
        rows_a, rows_b = [], []
        a, b = pad_slots.SlotsLog(), pad_slots.SlotsLog()
        fa = types.SimpleNamespace(_log=lambda ev, **f: rows_a.append({"event": ev, **f}))
        fb = types.SimpleNamespace(_log=lambda ev, **f: rows_b.append({"event": ev, **f}))
        a.start(fa, TWO, claims="0:p,1:s"); b.start(fb, TWO, claims="0:p,1:s", players_chosen=None)
        va, vb = {"sequence": 1}, {"sequence": 1}
        a.heartbeat(fa, TWO, va, claims="0:p,1:p"); b.heartbeat(fb, TWO, vb, claims="0:p,1:p", players_chosen=None)
        self.assertEqual(rows_a, rows_b); self.assertEqual(va, vb)
        self.assertNotIn("label", json.dumps(rows_a)); self.assertNotIn("players_chosen", json.dumps(rows_a))
        self.assertIsNone(pad_slots.parse_chosen("3")); self.assertEqual(pad_slots.parse_chosen("4"), 4)


if __name__ == "__main__":
    unittest.main()
