#!/usr/bin/env python3
"""B6: the hold's trigger (H = 950 for `1` / `on`), B4's rewind cap default, the cap rule (released holds only, a
10-s disarm), and the resume (R1 hold_return after a controller_silence handover, R2 a client handover left to the
client's gate, R3 a late client ready after a hold resume). B2's and B4's tests are untouched.

    python3 -m unittest discover -s tests/input_hold_b6 -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import hold_rewind as hr  # noqa: E402
import hold_tuning as ht  # noqa: E402
import input_hold as ih  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402

ON = {"PRIVYHUB_INPUT_HOLD": "1", "PRIVYHUB_INPUT_HOLD_B6": "1"}


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


class Rec:
    """The real LinkDropRecovery, fake callbacks, B6's tuning on it (a fake clock for the tuning)."""

    def __init__(self, b6=True, clock=None, rewind=None):
        self.calls = []
        self.root = Path(tempfile.mkdtemp(prefix="b6_rec_"))
        self.rec = ldr.LinkDropRecovery(
            self.root, pause_game=lambda: self.calls.append("pause"), resume_game=lambda: self.calls.append("resume"),
            save_recovery_state=lambda: {}, restart_encoder=lambda: {}, full_start_encoder=lambda: {},
            stream_active=lambda: True, end_session=lambda: None, client_packet_age_ms=lambda: 10.0,
            recovery_save_detail=lambda: {})
        self.rec._state = ldr.STATE_PLAYING
        self.rec._state_since = time.monotonic()
        self.clock = clock or Clock()
        self.t = ht.Tuning(950, clock=self.clock) if b6 else None
        if b6:
            self.rec._input_hold_b6 = self.t
        if rewind is not None:
            self.rec._input_hold_rewind = rewind

    def rows(self):
        p = self.rec.log_path()
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []

    def events(self):
        return [(r["event"], r.get("trigger") or r.get("via")) for r in self.rows()]


class FakeRewind:
    def __init__(self, calls):
        self.calls = calls
        self.cap = 30

    def rewind(self, rec, via):
        self.calls.append(f"rewind:{via}")


class TheFlag(unittest.TestCase):
    def test_enabled_and_h(self):
        self.assertEqual(ht.enabled({}), (False, None))
        self.assertEqual(ht.enabled(ON), (True, None))
        for env in ({"PRIVYHUB_INPUT_HOLD_B6": "1"}, {"PRIVYHUB_INPUT_HOLD": "0", "PRIVYHUB_INPUT_HOLD_B6": "1"},
                    {"PRIVYHUB_INPUT_HOLD": "1", "PRIVYHUB_INPUT_HOLD_B6": "yes"}):
            on, why = ht.enabled(env)
            self.assertFalse(on, env)
            self.assertTrue(why.startswith("ignored"), env)
        self.assertEqual(ht.hold_ms({"PRIVYHUB_INPUT_HOLD": "1"}), 950)
        self.assertEqual(ht.hold_ms({"PRIVYHUB_INPUT_HOLD": "on"}), 950)
        self.assertEqual(ht.hold_ms({"PRIVYHUB_INPUT_HOLD": "250"}), 250)
        self.assertEqual(ht.hold_ms({"PRIVYHUB_INPUT_HOLD": "1200"}), 1200)
        self.assertEqual(ih.parse("1"), (250, None))         # B2's grammar and meaning, untouched

    def test_wire_sets_h_cap_and_logs(self):
        r = Rec(b6=False, rewind=FakeRewind([]))
        det = ih.InputHoldDetector(250, lambda e: None)
        ctrl = type("C", (), {"_input_hold": det})()
        t = ht.wire(r.rec, ctrl, ON)
        self.assertIs(det.tuning, t)
        self.assertIs(r.rec._input_hold_b6, t)
        self.assertAlmostEqual(det.hold_s, 0.95)
        self.assertEqual(r.rec._input_hold_rewind.cap, 62)
        row = [x for x in r.rows() if x["event"] == "input_hold_b6_config"][-1]
        self.assertFalse(row["ignored"])
        self.assertEqual(row["hold_ms"], 950)
        r2 = Rec(b6=False)
        self.assertIsNone(ht.wire(r2.rec, ctrl, {"PRIVYHUB_INPUT_HOLD": "1", "PRIVYHUB_INPUT_HOLD_B6": "2"}))
        self.assertEqual([x["ignored"] for x in r2.rows()], [True])
        self.assertIsNone(ht.wire(r2.rec, ctrl, {"PRIVYHUB_INPUT_HOLD": "1"}))   # absent: nothing, no row
        self.assertEqual(len(r2.rows()), 1)


class TheRewindCap(unittest.TestCase):
    def test_default(self):
        self.assertEqual(ht.rewind_cap_default(ON), 62)                          # round(950 / 16.7) + 5
        self.assertEqual(ht.rewind_cap_default(dict(ON, PRIVYHUB_INPUT_HOLD="250")), 30)
        self.assertEqual(ht.rewind_cap_default(dict(ON, PRIVYHUB_INPUT_HOLD="4000")), 120)
        self.assertIsNone(ht.rewind_cap_default(dict(ON, PRIVYHUB_INPUT_HOLD_REWIND_CAP="40")))  # explicit wins
        self.assertIsNone(ht.rewind_cap_default({"PRIVYHUB_INPUT_HOLD": "1"}))  # B6 absent

    def test_config_block_buffer(self):
        env = dict(ON, PRIVYHUB_INPUT_HOLD_REWIND="1")
        self.assertIn(f'rewind_buffer_size = "{51 * 1024 * 1024}"', hr.config_block("snes9x_libretro.so", env))
        self.assertIn(f'rewind_buffer_size = "{1025 * 1024 * 1024}"',
                      hr.config_block("mednafen_psx_hw_libretro.so", env))
        b4 = {"PRIVYHUB_INPUT_HOLD": "1", "PRIVYHUB_INPUT_HOLD_REWIND": "1"}
        self.assertIn('rewind_buffer_size = "27262976"', hr.config_block("snes9x_libretro.so", b4))   # B4's bytes


class TheDetector(unittest.TestCase):
    def test_950_threshold(self):
        out, clock = [], Clock()
        d = ih.InputHoldDetector(950, out.append, clock)
        d.tuning = ht.Tuning(950, clock)
        d.on_quiet(100.90, 100.0)
        self.assertEqual(out, [])
        d.on_quiet(100.96, 100.0)
        self.assertEqual(out, [("hold", 960.0)])
        d.on_packet(101.5)
        self.assertEqual(out[-1], ("release", 1500.0))


class TheCap(unittest.TestCase):
    def test_six_released_disarm_ten_seconds(self):
        clock = Clock(50.0)
        r = Rec(clock=clock)
        out = []
        d = ih.InputHoldDetector(950, out.append, clock)
        d.tuning = r.t
        t = 100.0
        for i in range(6):                                  # six true holds, each released by input
            d.on_quiet(t + 1.0, t)
            r.rec._state = ldr.STATE_PLAYING
            self.assertTrue(r.rec.note_input_hold(1000.0))
            clock.t = t + 1.5
            d.on_packet(t + 1.5)
            r.rec.note_input_release(500.0)
            t += 5.0
        self.assertEqual(r.t.disarms, 1)
        caps = [x for x in r.rows() if x["event"] == "input_hold_cap"]
        self.assertEqual(len(caps), 1)
        self.assertEqual(caps[0]["rule"], "b6")
        holds = d.holds
        clock.t = t                                         # within 10 s of the sixth release: disarmed
        d.on_quiet(t + 1.0, t)
        self.assertEqual(d.holds, holds)
        self.assertEqual(d.capped, 1)
        clock.t = t + 11.0                                  # after 10 s: armed again
        d.on_quiet(t + 12.0, t + 11.0)
        self.assertEqual(d.holds, holds + 1)

    def test_handed_over_holds_never_count(self):
        clock = Clock(50.0)
        r = Rec(clock=clock)
        for i in range(8):
            r.rec._state = ldr.STATE_PLAYING
            r.rec.note_input_hold(1000.0)
            r.rec.note_client_desync("output_silence", 1200.0)     # the client took it over
            r.rec.note_input_release(4000.0)
            clock.t += 3.0
        self.assertEqual(r.t.disarms, 0)
        self.assertEqual(len(r.t._released), 0)


class TheResume(unittest.TestCase):
    def _handover_to_v2(self, rewind=False):
        clock = Clock(500.0)
        r = Rec(clock=clock)
        if rewind:
            r.rec._input_hold_rewind = FakeRewind(r.calls)
        r.rec.note_input_hold(960.0)
        r.rec.note_client_silence(5350.0)                   # v2's controller_silence takes the hold over
        return r, clock

    def test_r1_resume_at_the_first_fresh_heartbeat_after_the_return(self):
        r, clock = self._handover_to_v2(rewind=True)
        self.assertFalse(r.rec.note_input_release(6000.0))  # B2: not the hold's any more ...
        self.assertIn(("hold_return_armed", "input_release"), r.events())   # ... but B6 armed R1
        back = r.t._return_at
        now = time.monotonic()
        self.assertFalse(r.t.maybe_resume(r.rec, now))      # no heartbeat after the return yet
        r.rec._heartbeat_history = [(back - 1.0, 20)]       # a stale one (before the return)
        self.assertFalse(r.t.maybe_resume(r.rec, now))
        r.rec._heartbeat_history = [(back + 0.5, 900)]      # after, but the output not fresh
        self.assertFalse(r.t.maybe_resume(r.rec, now))
        r.rec._heartbeat_history = [(back + 0.9, 40)]       # after, fresh
        r.rec._tick()                                       # the monitor's own path
        self.assertEqual(r.rec.current_state(), ldr.STATE_PLAYING)
        self.assertEqual(r.calls, ["pause", "rewind:hold_return", "resume"])
        last = r.rows()[-1]
        self.assertEqual((last["event"], last["via"]), ("resumed", "hold_return"))
        self.assertEqual(last["output_age_ms"], 40)

    def test_v2_exit_still_works_first(self):
        r, clock = self._handover_to_v2()
        r.rec.enable_controller_exit(True)
        now = time.monotonic()
        self.assertFalse(r.rec._maybe_exit_controller_pause(now, 20.0))
        self.assertFalse(r.rec._maybe_exit_controller_pause(now + 0.3, 20.0))
        r.rec._heartbeat_history = [(now + 0.4, 30)]
        self.assertTrue(r.rec._maybe_exit_controller_pause(now + 0.5, 20.0))
        self.assertFalse(r.t.maybe_resume(r.rec, now + 0.6))   # already playing: nothing
        self.assertEqual(r.calls, ["pause", "resume"])

    def test_a_v2_pause_never_a_hold_is_not_resumed_by_b6(self):
        r = Rec()
        r.rec.note_client_silence(5350.0)
        r.rec.note_input_release(6000.0)
        r.rec._heartbeat_history = [(time.monotonic() + 5.0, 10)]
        self.assertFalse(r.t.maybe_resume(r.rec, time.monotonic()))
        self.assertEqual(r.calls, ["pause"])

    def test_r2_client_handover_left_to_the_clients_gate(self):
        r = Rec()
        r.rec.note_input_hold(960.0)
        r.rec.note_client_desync("output_silence", 1200.0)
        self.assertFalse(r.rec.note_input_release(4000.0))
        self.assertIsNone(r.t._return_at)
        r.rec._heartbeat_history = [(time.monotonic() + 5.0, 10)]
        self.assertFalse(r.t.maybe_resume(r.rec, time.monotonic()))
        self.assertEqual(r.rec.note_gameplay_released(), {"recovered": True, "from_state": "PAUSED_RECOVERING"})

    def test_r3_a_late_ready_after_a_hold_release_is_not_a_new_session(self):
        clock = Clock(800.0)
        r = Rec(clock=clock)
        r.rec.note_input_hold(960.0)
        self.assertTrue(r.rec.note_input_release(3000.0))   # resumed via input_release
        clock.t += 2.5                                      # the client's gate passes later
        self.assertEqual(r.rec.note_gameplay_released(), {"recovered": True, "from_state": "hold_resumed"})
        ev = [e for e, _ in r.events()]
        self.assertIn("client_ready_after_hold", ev)
        self.assertNotIn("session_started", ev)
        self.assertEqual(r.rec.note_gameplay_released()["recovered"], False)   # once only: the next is today's

    def test_r3_window_expires(self):
        clock = Clock(800.0)
        r = Rec(clock=clock)
        r.rec.note_input_hold(960.0)
        r.rec.note_input_release(3000.0)
        clock.t += 21.0
        self.assertEqual(r.rec.note_gameplay_released()["recovered"], False)
        self.assertIn("session_started", [e for e, _ in r.events()])

    def test_without_b6_b2_exactly(self):
        r = Rec(b6=False)
        r.rec.note_input_hold(960.0)
        self.assertTrue(r.rec.note_input_release(3000.0))
        self.assertEqual(r.rec.note_gameplay_released()["recovered"], False)   # today: a session start
        self.assertEqual([e for e, _ in r.events()], ["desync_pause", "resumed", "session_started"])


class FlagAbsent(unittest.TestCase):
    def _imports(self, extra):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        env.update(extra)
        code = ("import sys; sys.path.insert(0, 'companion'); import input_hold, hold_rewind; "
                "from games import link_drop_recovery as l; "
                "print('hold_tuning' in sys.modules, l.LinkDropRecovery._input_hold_b6, input_hold.InputHoldDetector.tuning)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=120)
        return out.stdout.strip(), out.stderr[-400:]

    def test_not_imported(self):
        for extra in ({}, {"PRIVYHUB_INPUT_HOLD": "1"}, {"PRIVYHUB_INPUT_HOLD": "1", "PRIVYHUB_INPUT_HOLD_REWIND": "1"}):
            out, err = self._imports(extra)
            self.assertEqual(out, "False None None", (extra, err))

    def test_hooks_shape(self):
        import ast

        def ifs(rel, text):
            tree = ast.parse((ROOT / "companion" / rel).read_text())
            return [n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test).startswith(text)]
        self.assertEqual(len(ifs("input_hold.py", "self.tuning is not None")), 1)
        self.assertEqual(len(ifs("games/link_drop_recovery.py", "self._input_hold_b6 is not None")), 4)
        self.assertEqual(len(ifs("plugins/games.py", "_hold_tuning is not None")), 1)
        self.assertEqual(len(ifs("hold_rewind.py", "(environ.get('PRIVYHUB_INPUT_HOLD_B6')")), 1)


if __name__ == "__main__":
    unittest.main()
