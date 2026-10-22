#!/usr/bin/env python3
"""B2: the fast input hold.

    python3 -m unittest discover -s tests/input_hold -v

The detector with a fake clock; the dispatcher synchronous; the recovery state machine (`LinkDropRecovery`) with fake
callbacks (no emulator, no stream): one owner, one pause row, the handover to v2, the rate limits, the user's pause;
the flag; the hooks' shape; and the real controller receive loop with B1's uplink blackout.
"""

from __future__ import annotations

import ast
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
sys.path.insert(0, str(ROOT / "tests" / "impairment"))

import impairment as imp  # noqa: E402
import input_hold as ih  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


def detector(ms=250):
    out, clock = [], Clock()
    return ih.InputHoldDetector(ms, out.append, clock), out, clock


class Flag(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(ih.parse(None), (None, None))
        self.assertEqual(ih.parse(""), (None, None))
        self.assertEqual(ih.parse("1"), (250, None))
        self.assertEqual(ih.parse("on"), (250, None))
        self.assertEqual(ih.parse("250"), (250, None))
        self.assertEqual(ih.parse(" 1000 "), (1000, None))
        for bad in ("0", "99", "4001", "fast", "-250", "250ms"):
            hold, why = ih.parse(bad)
            self.assertIsNone(hold, bad)
            self.assertTrue(why and why.startswith("ignored"), bad)


class Detector(unittest.TestCase):
    def test_short_silence_nothing(self):
        d, out, _ = detector()
        d.on_quiet(100.249, 100.0)
        self.assertEqual(out, [])

    def test_one_hold_then_one_release(self):
        d, out, _ = detector()
        d.on_quiet(100.25, 100.0)
        d.on_quiet(100.30, 100.0)
        d.on_quiet(103.00, 100.0)
        self.assertEqual(out, [("hold", 250.0)])
        d.on_packet(104.0)
        d.on_packet(104.01)
        self.assertEqual(out, [("hold", 250.0), ("release", 4000.0)])

    def test_never_before_a_first_packet(self):
        d, out, _ = detector()
        d.on_quiet(5.0, 0.0)
        self.assertEqual(out, [])

    def test_cap_six_in_sixty_seconds_logged_once(self):
        d, out, _ = detector()
        t = 100.0
        for _ in range(8):
            d.on_quiet(t + 0.3, t)
            d.on_packet(t + 0.4)
            t += 5.0
        kinds = [k for k, _ in out]
        self.assertEqual(kinds.count("hold"), 6)
        self.assertEqual(kinds.count("cap"), 1)
        self.assertEqual(d.capped, 2)
        # after the window rolls, holds again
        t = 100.0 + 61.0
        d.on_quiet(t + 0.3, t)
        self.assertEqual([k for k, _ in out].count("hold"), 7)


class FakeRecovery:
    """LinkDropRecovery's real state machine with fake callbacks and a temp log."""

    def __init__(self, resume_raises=False):
        self.calls = []
        self.root = Path(tempfile.mkdtemp(prefix="b2_rec_"))

        def resume():
            self.calls.append("resume")
            if resume_raises:
                raise RuntimeError("resume failed")

        self.rec = ldr.LinkDropRecovery(
            self.root, pause_game=lambda: self.calls.append("pause"), resume_game=resume,
            save_recovery_state=lambda: {}, restart_encoder=lambda: {}, full_start_encoder=lambda: {},
            stream_active=lambda: True, end_session=lambda: None, client_packet_age_ms=lambda: 10.0,
            recovery_save_detail=lambda: {})
        self.rec._state = ldr.STATE_PLAYING          # a live session, no monitor thread
        self.rec._state_since = time.monotonic()

    def rows(self):
        p = self.rec.log_path()
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []

    def events(self):
        return [(r["event"], r.get("trigger") or r.get("via")) for r in self.rows()]


class Recovery(unittest.TestCase):
    def test_hold_then_release(self):
        f = FakeRecovery()
        self.assertTrue(f.rec.note_input_hold(260.0))
        self.assertEqual(f.rec.current_state(), ldr.STATE_PAUSED_RECOVERING)
        self.assertTrue(f.rec.note_input_release(3900.0))
        self.assertEqual(f.rec.current_state(), ldr.STATE_PLAYING)
        self.assertEqual(f.calls, ["pause", "resume"])
        self.assertEqual(f.events(), [("desync_pause", "input_hold"), ("resumed", "input_release")])
        self.assertEqual(f.rows()[-1]["held_ms"], 3900.0)

    def test_v2_threshold_hands_over_one_pause_row(self):
        f = FakeRecovery()
        f.rec.note_input_hold(255.0)
        f.rec.note_client_silence(5350.0)                    # v2's controller_silence, while held
        self.assertEqual(f.calls, ["pause"])                 # no second pause
        self.assertFalse(f.rec.note_input_release(5600.0))   # the hold no longer owns it
        self.assertEqual(f.calls, ["pause"])
        ev = f.events()
        self.assertEqual([e for e in ev if e[0] == "desync_pause"], [("desync_pause", "input_hold")])
        self.assertIn(("input_hold_handover", "controller_silence"), ev)
        # v2's own controller-return exit resumes it, once
        f.rec.enable_controller_exit(True)
        now = time.monotonic()
        self.assertFalse(f.rec._maybe_exit_controller_pause(now, 20.0))
        self.assertFalse(f.rec._maybe_exit_controller_pause(now + 0.3, 20.0))
        f.rec._heartbeat_history = [(now + 0.4, 30)]
        self.assertTrue(f.rec._maybe_exit_controller_pause(now + 0.5, 20.0))
        self.assertEqual(f.calls, ["pause", "resume"])
        self.assertEqual(f.events()[-1], ("resumed", "controller_return"))

    def test_client_desync_hands_over(self):
        f = FakeRecovery()
        f.rec.note_input_hold(255.0)
        f.rec.note_client_desync("output_silence", 1300.0)
        self.assertEqual(f.calls, ["pause"])
        self.assertIn(("input_hold_handover", "client_output_silence"), f.events())
        self.assertFalse(f.rec.note_input_release(1500.0))

    def test_client_ready_gate_resumes_a_hold(self):
        f = FakeRecovery()
        f.rec.note_input_hold(255.0)
        self.assertTrue(f.rec.note_stream_ready())
        self.assertFalse(f.rec.note_input_release(900.0))    # already PLAYING: nothing
        self.assertEqual(f.calls, ["pause"])                 # the gate's resume is the plugin's, not this callback

    def test_resume_failure_hands_to_controller_silence(self):
        f = FakeRecovery(resume_raises=True)
        f.rec.note_input_hold(255.0)
        self.assertFalse(f.rec.note_input_release(800.0))
        self.assertEqual(f.rec.current_state(), ldr.STATE_PAUSED_RECOVERING)
        self.assertEqual(f.rec._last_desync_reason, "controller_silence")
        self.assertEqual(f.events()[-1][0], "input_release_failed")

    def test_no_hold_unless_playing(self):
        f = FakeRecovery()
        f.rec.note_client_silence(5350.0)                    # v2 paused first
        self.assertFalse(f.rec.note_input_hold(255.0))
        self.assertEqual(f.calls, ["pause"])
        self.assertNotIn("input_hold_handover", [e[0] for e in f.events()])

    def test_without_the_hold_today_unchanged(self):
        f = FakeRecovery()
        f.rec.note_client_silence(5350.0)
        f.rec.note_client_desync("output_silence", 1000.0)  # already paused: ignored, as today
        self.assertEqual(f.calls, ["pause"])
        self.assertEqual(f.events(), [("desync_pause", "controller_silence")])


class Dispatcher(unittest.TestCase):
    def _d(self, paused=False, resume_raises=False):
        f = FakeRecovery(resume_raises)
        clock, slept = Clock(50.0), []
        d = ih.HoldDispatcher(f.rec, lambda: paused, clock=clock,
                              sleep=lambda s: (slept.append(round(s, 3)), setattr(clock, "t", clock.t + s)),
                              threaded=False)
        return f, d, clock, slept

    def test_min_hold(self):
        f, d, clock, slept = self._d()
        d.handle(("hold", 255.0))
        clock.t += 0.01                                   # the packets came back 10 ms after the pause returned
        d.handle(("release", 265.0))
        self.assertEqual(slept, [0.04])
        self.assertEqual(f.calls, ["pause", "resume"])

    def test_the_users_pause_wins(self):
        f, d, _, _ = self._d(paused=True)
        d.handle(("hold", 255.0))
        d.handle(("release", 400.0))
        d.handle(("hold", 255.0))
        self.assertEqual(f.calls, [])
        self.assertEqual([e[0] for e in f.events()], ["input_hold_skipped_paused"])

    def test_cap_row(self):
        f, d, _, _ = self._d()
        d.handle(("cap", 300.0))
        self.assertEqual(f.events(), [("input_hold_cap", None)])


class Hooks(unittest.TestCase):
    def _hooks(self, rel, test_text):
        tree = ast.parse((ROOT / "companion" / rel).read_text())
        return [n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test) == test_text]

    def test_shapes(self):
        self.assertEqual(len(self._hooks("native_session_io.py", "self._input_hold is not None")), 2)
        self.assertEqual(len(self._hooks("plugins/games.py", "_input_hold is not None")), 1)
        tree = ast.parse((ROOT / "companion" / "plugins" / "games.py").read_text())
        guarded = [n for n in tree.body if isinstance(n, ast.If) and "import input_hold" in ast.unparse(n)]
        self.assertEqual(len(guarded), 1)
        self.assertIn("PRIVYHUB_INPUT_HOLD", ast.unparse(guarded[0].test))
        top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any("input_hold" in ast.unparse(n) for n in top))

    def test_flag_absent_not_imported(self):
        env = {k: v for k, v in os.environ.items() if k not in (ih.FLAG_ENV, imp.FLAG_ENV)}
        code = ("import sys; sys.path.insert(0, 'companion'); import native_session_io as n; "
                "print('input_hold' in sys.modules, n.NativeControllerBridge._input_hold)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True,
                             text=True, timeout=120)
        self.assertEqual(out.stdout.strip(), "False None", out.stderr[-500:])


class TheReceiveLoop(unittest.TestCase):
    def test_a_one_second_uplink_blackout_holds_once_and_releases(self):
        import test_blackout as TB
        f = FakeRecovery()
        d = ih.HoldDispatcher(f.rec, lambda: False, threaded=False)
        det = ih.InputHoldDetector(250, d.handle)
        import native_session_io as nsio
        nsio.NativeControllerBridge._input_hold = det        # as set_input_hold, for every bridge the helper makes
        try:
            epoch = time.monotonic()
            gate = imp.UplinkGate(imp.Blackout(1.0, 10.0, 1.0, epoch=epoch))
            TB.run_bridge(3.0, gate, silence_ms=5000.0)
        finally:
            nsio.NativeControllerBridge._input_hold = None
        self.assertIn(det.holds, (1, 2))                      # the blackout (and maybe the sender's end at 3 s)
        rows = f.rows()
        first = [r for r in rows if r["event"] == "desync_pause"][0]
        self.assertEqual(first["trigger"], "input_hold")
        self.assertGreaterEqual(first["age_ms"], 250.0)
        self.assertLessEqual(first["age_ms"], 320.0)
        resumed = [r for r in rows if r["event"] == "resumed"][0]
        self.assertAlmostEqual(resumed["held_ms"], 1000.0, delta=80.0)


class UnattendedFramesReader(unittest.TestCase):
    """tools/unattended_frames.py on synthetic logs: the raw count and the core-running count."""

    def test_counts(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import unattended_frames as uf
        d = Path(tempfile.mkdtemp(prefix="b2_uf_"))
        (d / "native_frame_sizes.jsonl").write_text("".join(
            json.dumps({"at_utc": f"2026-10-22T00:00:{s:02d}.000Z", "frames": 60}) + "\n" for s in range(0, 40)))
        (d / "native_stream_ctrl_gaps.log").write_text("".join(json.dumps(r) + "\n" for r in (
            {"start_utc": "2026-10-22T00:00:10.000Z", "end_utc": "2026-10-22T00:00:14.000Z", "gap_ms": 4000},
            {"start_utc": "2026-10-22T00:00:14.300Z", "end_utc": "2026-10-22T00:00:14.600Z", "gap_ms": 300},
            {"start_utc": "2026-10-22T00:00:30.000Z", "end_utc": "2026-10-22T00:00:31.000Z", "gap_ms": 1000})))
        (d / "native_stream_recovery.log").write_text("".join(json.dumps(r) + "\n" for r in (
            {"at_utc": "2026-10-22T00:00:10.300Z", "event": "desync_pause", "trigger": "input_hold"},
            {"at_utc": "2026-10-22T00:00:14.000Z", "event": "resumed", "via": "input_release"})))
        r = uf.measure(d, uf.ts("2026-10-22T00:00:00"), uf.ts("2026-10-22T00:00:40"))
        self.assertEqual(r["episodes"], 2)                         # 10-14.6 s joined (< 500 ms apart), and 30-31 s
        self.assertAlmostEqual(r["unattended_frames"], (3.75 + 0.05 + 0.75) * 60, delta=0.5)
        self.assertAlmostEqual(r["unattended_frames_core_running"], (0.05 + 0.05 + 0.75) * 60, delta=0.5)
        self.assertEqual(r["held_episodes"], {"250": 2, "500": 2, "1000": 2})


if __name__ == "__main__":
    unittest.main()
