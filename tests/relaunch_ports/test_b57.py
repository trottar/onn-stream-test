#!/usr/bin/env python3
"""B57 (host): the PS2 multitap relaunch through PINE's reserved slot 7 -- the save with B52's file-complete check,
SIGTERM, the launch with `MultitapPort1` per the count, the hold until the game's ELF, the load, B52's picture check,
`state: loaded`; a failed step -> the title restarts without the state (`state: restarted` and the reason), never a
dead session. B51's PINE socket double and B52's fake window / log on the real EmulatorManager; the launch is faked as
a new PCSX2 whose log gains `ELF Loading:` once it has run ~6 s. No PCSX2, no BIOS, no title, no real folder.

    python3 -m unittest discover -s tests/relaunch_ports -v
"""

from __future__ import annotations

import importlib.util
import json
import signal
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tests" / "ps2_session"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401  (this run's temp dirs removed at exit)

import players_session as ps  # noqa: E402
import ps2_session as ps2  # noqa: E402
import relaunch_ports as rp  # noqa: E402
from games import emulator_manager as em  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402
import test_b51 as b51  # noqa: E402

spec = importlib.util.spec_from_file_location("b57_games_plugin", ROOT / "companion" / "plugins" / "games.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

STEM = b51.FAKE_STEM
BOOT_S = 6.0          # the fake PCSX2's boot to the ELF, in its running time (H3-P2: ~6-9 s)
SAVE = lambda slot: struct.pack("<IBB", 6, 0x09, slot)          # noqa: E731
LOAD = lambda slot: struct.pack("<IBB", 6, 0x0A, slot)          # noqa: E731


class Proc(b51.FakeProc):
    def __init__(self, pid):
        self.pid = pid
        self.waited = 0

    def wait(self, timeout=None):
        self.waited += 1
        return 0


class Rig:
    """One PS2 session on the real manager; `launch` / the clock / the window are the fakes."""

    def __init__(self, root: Path, picture="moving", tlb=False, elf=True, **pine):
        self.root = root
        self.d = b51.PineDouble(root, **pine)
        self.m, self.lines, self.kills = b51.session_manager(self.d)
        self.picture, self.tlb, self.elf = picture, tlb, elf
        self.t = [100.0]
        self.calls: list = []
        self.launches: list[dict] = []
        self.pid = 4242
        self.m.process = Proc(self.pid)
        self.m._players_session = ps.plan("ps2", 2, None, source="join")
        self.m._paused = False
        self.fake = self.m._fake
        self.fake.paused = False
        self.m._ps2.paused_by = None
        self.wire(self.m._ps2, self.fake, booted=True)
        m = self.m
        orig_stop = m.stop

        def stop():
            self.calls.append("stop")
            return orig_stop()

        def launch(game, **kw):
            n = kw.get("players_chosen")
            self.calls.append(("launch", n))
            plan = ps.plan("ps2", n, None)
            pads = ps2.pad_sections(int(plan["ports"]), bool(plan["multitap"]))      # the PS2 launch's own call
            self.launches.append({"players": n, "pad": pads["Pad"]})
            self.pid += 1
            m.process = Proc(self.pid)
            m.active_game = dict(game)
            m._launch_kind = "pcsx2"
            m._players_session = plan
            m._paused = False
            fake = b51.FakePcsx2(ps2.PINE_RUNNING)
            # a new PCSX2: a fresh per-launch log (no ELF yet), running from its boot
            self.d.emulog.write_text("[    0.1] PCSX2 log start\n")
            m._ps2 = ps2.Session(self.pid, self.lines.append, run=None, status=fake.status,
                                 kill=lambda pid, sig: self.kills.append(int(sig)), pine_path=self.d.path,
                                 log_path=self.d.emulog)
            self.fake = fake
            self.wire(m._ps2, fake, booted=False)
            self.t[0] += 2.0                                   # the window and the sink-input
            return {"active": True}

        m.stop, m.launch = stop, launch
        for name in ("pause", "resume", "save_relaunch_state"):
            orig = getattr(m, name)
            setattr(m, name, self.recorded(name, orig))
        orig_load = m.load_recovery_state_running
        m.load_recovery_state_running = lambda source=None: (self.calls.append(("load", source)),
                                                             orig_load(source=source))[1]

    def recorded(self, name, fn):
        def call(*a, **k):
            self.calls.append(name)
            return fn(*a, **k)
        return call

    def wire(self, sess, fake, booted):
        """The session's clock / sleep / window on this rig: running time boots the game (the ELF line) after BOOT_S;
        a TLB Miss after a load when asked; a static picture when asked."""
        run_s = [BOOT_S if booted else 0.0]
        orig_run, orig_grab = fake.run, fake.grab
        emulog = self.d.emulog

        def sleep(s):
            self.t[0] += s
            if not fake.paused:
                before = run_s[0]
                run_s[0] += s
                if self.elf and before < BOOT_S <= run_s[0]:
                    with open(emulog, "a") as fh:
                        fh.write("[    4.7] ELF Loading: <elf>, Game CRC = 00000000, EntryPoint = 0x00100008\n")

        def run(cmd, **kw):
            return orig_run(cmd, **kw)

        def grab(w):
            # the loaded state faults as the game runs from it (the running load sends no hotkey, so the frame is it)
            text = emulog.read_text()
            if self.tlb and not fake.paused and "Loaded state" in text and ps2.TLB_MISS not in text:
                with open(emulog, "a") as fh:
                    fh.write("[   15.3] TLB Miss, pc=0x0 addr=0x0 [store]\n")
            if self.picture == "moving":
                return orig_grab(w)
            return bytes([90] * (ps2.GRAB_W * ps2.GRAB_H))

        sess.sleep, sess.clock, sess.run, sess.grab = sleep, (lambda: self.t[0]), run, grab

    def clock(self):
        return self.t[0]

    def plugin(self):
        rec = ldr.LinkDropRecovery(
            self.root, pause_game=lambda: None, resume_game=lambda: None, save_recovery_state=lambda: {},
            restart_encoder=lambda: {}, full_start_encoder=lambda: {}, stream_active=lambda: True,
            end_session=lambda: None, client_packet_age_ms=lambda: 10.0, recovery_save_detail=lambda: {})
        calls, t = self.calls, self.t

        class Stream:
            DEFAULT_PORT = 48100

            def stop(self):
                calls.append("stream_stop"); return {}

            def start(self, **kw):
                calls.append(("stream_start", kw["managed_process_id"])); t[0] += 0.8; return {"active": True}

            def end_game_session(self):
                calls.append("end_game_session"); return {}

        p = object.__new__(G.GamesPlugin)
        p.PROJECT_ROOT = self.root
        p._emulator = self.m
        p._recovery = rec
        p._native_stream = Stream()
        p._recovery_start_args = {"client_ip": "127.0.0.1", "port": 48100}
        return p, rec

    def run(self):
        p, rec = self.plugin()
        r = rp.run(p, 4, 3, clock=self.clock, sleep=lambda s: self.t.__setitem__(0, self.t[0] + s))
        return r, rec


def rows(rec, event):
    path = rec.log_path()
    return [r for r in (json.loads(x) for x in path.read_text().splitlines()) if r["event"] == event] \
        if path.exists() else []


class Base(unittest.TestCase):
    def setUp(self):
        self.old = em._ps2
        em._ps2 = ps2                         # what PRIVYHUB_PS2=1 sets at import
        self.root = Path(tempfile.mkdtemp(prefix="b57_"))

    def tearDown(self):
        em._ps2 = self.old

    def rig(self, **kw):
        r = Rig(self.root, **kw)
        self.addCleanup(r.d.close)
        return r


class FullSequence(Base):
    def test_save_sigterm_launch_four_elf_load_picture_ready(self):
        g = self.rig()
        r, rec = g.run()
        self.assertEqual(g.calls, ["pause", "save_relaunch_state", "stream_stop", "stop", ("launch", 4), "resume",
                                   ("load", g.d.sstates / f"{STEM}.07.p2s"), "pause", ("stream_start", 4243)])
        # PINE: the save to slot 7, then the load of slot 7 -- nothing else (slots 8 / 9 untouched)
        self.assertEqual(g.d.requests, [SAVE(7), LOAD(7)])
        self.assertEqual(sorted(p.name for p in g.d.sstates.iterdir()), [f"{STEM}.07.p2s"])
        self.assertIn(signal.SIGTERM, g.kills)                                   # B49's stop: SIGTERM
        self.assertEqual(g.launches, [{"players": 4, "pad": {"MultitapPort1": "true", "MultitapPort2": "false"}}])
        self.assertTrue(r["ok"])
        self.assertEqual((r["relaunch"]["state"], r["relaunch"]["kind"], r["relaunch"]["landed_ports"]),
                         ("loaded", "pcsx2", 4))
        self.assertNotIn("reason", r["relaunch"])
        steps = r["relaunch"]["steps_ms"]
        self.assertNotIn("settle", steps)                                        # the ELF hold is the settle
        self.assertGreaterEqual(steps["load"], int((BOOT_S - 0.5) * 1000))       # the load held for the boot
        self.assertEqual(r["ports_set"], {"players_chosen": 4, "ports": 4, "players": 4, "multitap": True,
                                          "multitap_available": True, "source": "relaunch"})
        row = rows(rec, "relaunch_ports")[-1]
        self.assertEqual((row["ok"], row["state"], row["slot"], row["ps2_states"], row["players_joined"]),
                         (True, "loaded", 7, "pine", 3))
        self.assertTrue(row["within_budget"])
        self.assertLessEqual(row["total_ms"], rp.BUDGET_S * 1000)
        self.assertEqual(rows(rec, "ports_set")[-1]["source"], "relaunch")
        self.assertTrue(any(l.startswith("PS2 relaunch save: slot 7 pine 0x09 ok; file complete") for l in g.lines))
        self.assertTrue(any(l.startswith("PS2 relaunch load: slot 7 pine 0x0a ok; picture ok") for l in g.lines))
        self.assertTrue(g.fake.paused)                                           # paused for the client's gate
        # no slot index: the Game State list shows nothing new
        self.assertFalse(any(x["exists"] for x in g.m.status()["save_state_slot_details"]))

    def test_the_slot_numbers(self):
        self.assertEqual((ps2.RELAUNCH_SLOT, ps2.RECOVERY_SLOT, ps2.SCRATCH_SLOT), (7, 8, 9))


class Failures(Base):
    def assert_restarted(self, g, r, rec, reason):
        self.assertEqual(r["relaunch"]["state"], "restarted")
        self.assertEqual(r["relaunch"]["reason"], reason)
        row = rows(rec, "relaunch_ports")[-1]
        self.assertEqual((row["state"], row["reason"], row.get("ended")), ("restarted", reason, None))
        self.assertTrue(g.m.status()["active"])                                  # never a dead session
        self.assertEqual(r["ports_set"]["ports"], 4)
        self.assertEqual(g.calls[-1][0], "stream_start")

    def test_a_save_failure_restarts_the_title_not_a_refusal(self):
        for kw in ({"result": ps2.PINE_FAIL}, {"write_file": False}, {"answer": False}):
            with self.subTest(**kw):
                self.root = Path(tempfile.mkdtemp(prefix="b57_"))
                g = self.rig(**kw)
                r, rec = g.run()
                self.assert_restarted(g, r, rec, "ps2_relaunch_save_failed")
                self.assertNotIn(LOAD(7), g.d.requests)
                self.assertNotIn("resume", g.calls)
                self.assertIn("save_error", rows(rec, "relaunch_ports")[-1])

    def test_a_static_picture_restarts_the_title_clean(self):
        g = self.rig(picture="static")
        r, rec = g.run()
        self.assert_restarted(g, r, rec, "ps2_relaunch_picture_static")
        self.assertEqual([c for c in g.calls if c in ("stop",) or (isinstance(c, tuple) and c[0] == "launch")],
                         ["stop", ("launch", 4), "stop", ("launch", 4)])
        self.assertIn("stop_clean", r["relaunch"]["steps_ms"])
        self.assertIn("launch_clean", r["relaunch"]["steps_ms"])
        self.assertTrue(r["ok"])
        self.assertTrue(any(l.startswith("PS2 relaunch load: slot 7 pine 0x0a ok; picture static") for l in g.lines))

    def test_a_tlb_miss_restarts_the_title_clean(self):
        g = self.rig(tlb=True)
        r, rec = g.run()
        self.assert_restarted(g, r, rec, "ps2_relaunch_picture_fault")
        self.assertEqual(sum(1 for c in g.calls if isinstance(c, tuple) and c[0] == "launch"), 2)

    def test_the_elf_never_up_is_a_restart_without_a_second_launch(self):
        g = self.rig(elf=False)
        r, rec = g.run()
        self.assert_restarted(g, r, rec, "ps2_relaunch_load_failed")
        self.assertNotIn(LOAD(7), g.d.requests)
        self.assertEqual(sum(1 for c in g.calls if isinstance(c, tuple) and c[0] == "launch"), 1)
        self.assertFalse(r["relaunch"]["steps_ms"].get("launch_clean"))
        self.assertFalse(rows(rec, "relaunch_ports")[-1]["within_budget"])      # the 30-s ELF bound, recorded


class Unchanged(Base):
    def test_the_source_less_running_load_is_b55s_slot_8(self):
        g = self.rig()
        g.m._paused = True
        g.m.save_recovery_state()                                               # slot 8 + the index (B55)
        g.m._ps2.resume(); g.m._paused = False
        g.m.load_recovery_state_running()
        self.assertEqual(g.d.requests[-1], LOAD(8))
        self.assertTrue(any(l.startswith("PS2 recovery load: slot 8 pine 0x0a ok; picture ok") for l in g.lines))

    def test_a_foreign_source_is_refused_before_pine(self):
        g = self.rig()
        other = g.d.sstates / f"{STEM}.08.p2s"
        other.write_bytes(b51.zip_bytes())
        with self.assertRaises(em.EmulatorError):
            g.m.load_recovery_state_running(source=other)
        self.assertEqual(g.d.requests, [])

    def test_absent_no_ps2_session_exists(self):
        # without PRIVYHUB_PS2=1 the plugin never imports ps2_session (B49); a RetroArch manager's relaunch save is
        # B54's own path (its capture), never PINE
        em._ps2 = None
        m = em.EmulatorManager(self.root, config_path=(ROOT / "companion/games/config/emulators.json"))
        self.assertIsNone(m._launch_kind)
        with self.assertRaises(em.EmulatorError) as cm:
            m.save_relaunch_state()
        self.assertEqual(str(cm.exception), "No PrivyHub game session is running")


if __name__ == "__main__":
    unittest.main()
