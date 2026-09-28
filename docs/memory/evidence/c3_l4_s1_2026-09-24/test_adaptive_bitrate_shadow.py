#!/usr/bin/env python3
"""C3.L4-S1: unit tests for the shadow adaptive-bitrate policy.

    python3 -m unittest tools/test_adaptive_bitrate_shadow.py -v

Synthetic telemetry only; nothing touches the companion, the stream or the
network. Every test names the rule it checks (the constants and rules are
pre-registered in handoffs/C3-L4-S1_SHADOW_CONTROLLER_TASK.md and written
into architecture/ADAPTIVE_BITRATE.md §"C3.L4 shadow controller — S1").
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "companion"))

import adaptive_bitrate as ab  # noqa: E402

CLEAN = dict(fps=59.9, queue=0, gap=17)
FALLBACK = dict(fps=40.0, queue=3, gap=120)
FALLBACK_GAP = dict(fps=45.0, queue=0, gap=400)
ROUTINE = dict(fps=55.0, queue=1, gap=60)


def telemetry(elapsed_ms, fps, queue, gap, *, fresh=True, available=True, idr=False):
    return {
        "schema": "privyhub_stream_telemetry_v1",
        "available": available,
        "fresh": fresh,
        "session_elapsed_ms": elapsed_ms,
        "receiver": {"recent_fps": fps, "waiting_for_idr": idr, "lost_packets_delta": 0},
        "decoder": {"queue_depth": queue},
        "latency": {"output_gap_ms": gap},
        "fec": {"recovered_packets_delta": 0},
    }


class Feeder:
    """Feeds the pure policy one 2 s report at a time; collects events."""

    def __init__(self):
        self.p = ab.ShadowPolicy()
        self.t = 0
        self.events = []

    def feed(self, n=1, **kw):
        out = []
        for _ in range(n):
            self.t += ab.REPORT_INTERVAL_MS
            ev = self.p.feed(ab._sample(telemetry(self.t, kw["fps"], kw["queue"], kw["gap"],
                                                  fresh=kw.get("fresh", True),
                                                  available=kw.get("available", True),
                                                  idr=kw.get("idr", False))))
            out += ev
        self.events += out
        return out

    def acts(self, events=None):
        """Would-acts of the ACTING track (FALLBACK down, RECOVERY up)."""
        return [e for e in (self.events if events is None else events)
                if e["event"] == "would_act" and e.get("track") == "acting_path_shadow"]

    def routine(self, events=None):
        return [e for e in (self.events if events is None else events)
                if e["event"] == "would_act" and e["class"] == "ROUTINE"]


class ShadowPolicyTests(unittest.TestCase):

    def test_clean_stream_1000_reports_no_decision(self):
        """Rule: a healthy stream (fps 59.9, queue 0, gap <= 150) never draws a decision."""
        f = Feeder()
        f.feed(1000, **CLEAN)
        self.assertEqual(f.acts(), [])
        self.assertEqual(f.p.would_act, {"FALLBACK": 0, "ROUTINE": 0, "INCREASE": 0})
        self.assertEqual(f.p.level_kbps, 7000)
        self.assertEqual(f.p.state, ab.REFERENCE)

    def test_transport_gaps_100_200_ms_do_not_trigger(self):
        """Rule: output gaps of 100-200 ms (the transport's own) are not FALLBACK evidence."""
        f = Feeder()
        for i in range(500):
            f.feed(fps=59.9, queue=0, gap=100 + (i % 5) * 25)
        self.assertEqual(f.acts(), [])

    def test_fallback_one_decrease_then_blackout_then_hold_down(self):
        """Rules: FALLBACK (fps < 50 on 5/5 and queue >= 2 on >= 3/5) -> exactly one
        FALLBACK would-decrease, straight to the floor (a jump, never a ramp); the
        next 3 reports are blacked out; nothing further while held down / at the
        floor. On a queue-driven onset ROUTINE's 4-of-5 is met one report earlier:
        it is logged on its own track and does not move the level."""
        f = Feeder()
        f.feed(20, **CLEAN)
        ev = f.feed(5, **FALLBACK)
        acts = f.acts(ev)
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["class"], "FALLBACK")
        self.assertEqual((acts[0]["from_kbps"], acts[0]["to_kbps"]), (7000, 5000))
        self.assertFalse(acts[0]["acted"])
        self.assertLessEqual(len(f.routine(ev)), 1)
        self.assertEqual(f.p.level_kbps, 5000)
        # blackout: the next 3 reports are not evaluated at all
        before = f.p.suppressed["blackout"]
        f.feed(3, **FALLBACK)
        self.assertEqual(f.p.suppressed["blackout"] - before, 3)
        self.assertEqual(f.p.blackout_remaining, 0)
        # already at the floor and held down: nothing more
        f.feed(60, **FALLBACK)
        self.assertEqual(len(f.acts()), 1)
        self.assertEqual(f.p.would_act["FALLBACK"], 1)

    def test_fallback_by_output_gap(self):
        """Rule: FALLBACK also on fps < 50 on 5/5 with output_gap > 250 ms on >= 2/5
        (queue 0: ROUTINE is not met, so this is the only would-act)."""
        f = Feeder()
        f.feed(10, **CLEAN)
        ev = f.feed(5, **FALLBACK_GAP)
        self.assertEqual([a["class"] for a in f.acts(ev)], ["FALLBACK"])
        self.assertEqual(f.routine(), [])

    def test_reversal_hold_down_60_reports(self):
        """Rule: after an action, no action in the other direction for 60 reports."""
        f = Feeder()
        f.feed(10, **CLEAN)
        f.feed(5, **FALLBACK)                   # down at report 15
        f.feed(3 + 90, **CLEAN)                 # up at report 108 (5000 -> 5500)
        self.assertEqual([a["direction"] for a in f.acts()], ["down", "up"])
        f.feed(3 + 55, **FALLBACK)              # 58 reports since the up: held down
        self.assertEqual(len(f.acts()), 2)
        self.assertGreater(f.p.suppressed["hold_down"], 0)
        f.feed(2, **FALLBACK)                   # 60: the reversal is allowed
        self.assertEqual([a["direction"] for a in f.acts()], ["down", "up", "down"])

    def test_routine_logged_once_per_30_reports_never_moves_level(self):
        """Rule: ROUTINE (not authorized) is counted on its own 30-report hold-down
        while the evidence persists, and never moves the virtual level."""
        f = Feeder()
        f.feed(10, **CLEAN)
        f.feed(4, **ROUTINE)                    # 4 of 5 below 57 with queue >= 1: logged
        self.assertEqual(len(f.routine()), 1)
        f.feed(29, **ROUTINE)                   # 29 reports since: held
        self.assertEqual(len(f.routine()), 1)
        f.feed(1, **ROUTINE)                    # 30: logged again
        self.assertEqual(len(f.routine()), 2)
        self.assertEqual(f.p.level_kbps, 7000)
        self.assertEqual(f.acts(), [])

    def test_routine_one_decrease_logged_as_routine(self):
        """Rule: ROUTINE (fps < 57 on >= 4/5 with queue >= 1 on >= 3/5) -> one
        would-decrease, class ROUTINE, one rung (7000 -> 6000), not FALLBACK."""
        f = Feeder()
        f.feed(10, **CLEAN)
        ev = f.feed(5, **ROUTINE)
        r = f.routine(ev)
        self.assertEqual(len(r), 1)
        self.assertEqual((r[0]["from_kbps"], r[0]["to_kbps"]), (7000, 6000))
        self.assertEqual(f.p.would_act["ROUTINE"], 1)
        self.assertEqual(f.p.would_act["FALLBACK"], 0)
        self.assertEqual(f.acts(), [])

    def test_recovery_increase_after_exactly_90_clean(self):
        """Rule: below 7000, one would-increase (one rung) after exactly 90
        consecutive clean reports -- counted after the 3-report blackout -- not before."""
        f = Feeder()
        f.feed(10, **CLEAN)
        f.feed(5, **FALLBACK)                        # -> 5000
        f.feed(3, **CLEAN)                           # blackout
        f.feed(89, **CLEAN)
        self.assertEqual(len(f.acts()), 1)
        self.assertEqual(f.p.clean_count, 89)
        ev = f.feed(1, **CLEAN)                      # the 90th
        acts = f.acts(ev)
        self.assertEqual(len(acts), 1)
        self.assertEqual((acts[0]["direction"], acts[0]["from_kbps"], acts[0]["to_kbps"]),
                         ("up", 5000, 5500))

    def test_one_unclean_report_restarts_the_clean_count(self):
        """Rule: the 90 clean reports must be consecutive."""
        f = Feeder()
        f.feed(10, **CLEAN)
        f.feed(5, **FALLBACK)
        f.feed(3, **CLEAN)
        f.feed(80, **CLEAN)
        f.feed(1, fps=58.0, queue=0, gap=17)         # not clean (fps < 59)
        f.feed(89, **CLEAN)
        self.assertEqual(len(f.acts()), 1)
        f.feed(1, **CLEAN)
        self.assertEqual(len(f.acts()), 2)

    def test_alternating_pattern_oscillation_hold_on_third_reversal(self):
        """Rule: a third direction change within 10 minutes -> HOLD, reason
        `oscillation`, for the rest of the session; the third reversal is not acted."""
        f = Feeder()
        f.feed(10, **CLEAN)
        f.feed(5, **FALLBACK)                  # down (7000 -> 5000)
        f.feed(3 + 90, **CLEAN)                # up (change 1: 5000 -> 5500)
        f.feed(60, **FALLBACK)                 # reversal hold-down 60, then down (change 2)
        f.feed(3 + 90, **CLEAN)                # up would be change 3 -> HOLD
        acts = f.acts()
        self.assertEqual([a["direction"] for a in acts], ["down", "up", "down"])
        holds = [e for e in f.events if e["event"] == "hold"]
        self.assertEqual(len(holds), 1)
        self.assertEqual(holds[0]["reason"], "oscillation")
        self.assertLessEqual(f.t, ab.OSCILLATION_WINDOW_MS + 60_000)
        self.assertEqual(f.p.state, ab.HOLD)
        f.feed(200, **FALLBACK)                # nothing more this session
        f.feed(200, **CLEAN)
        self.assertEqual(len(f.acts()), 3)
        self.assertEqual(f.p.state, ab.HOLD)

    def test_stale_telemetry_no_decision(self):
        """Rule: telemetry not fresh / unavailable -> TELEMETRY_STALE, no decision,
        even when the numbers would be FALLBACK."""
        f = Feeder()
        f.feed(10, **CLEAN)
        f.feed(20, fresh=False, **FALLBACK)
        self.assertEqual(f.acts(), [])
        self.assertEqual(f.p.state, ab.TELEMETRY_STALE)
        f.feed(20, available=False, **FALLBACK)
        self.assertEqual(f.acts(), [])
        self.assertEqual(f.p.state, ab.TELEMETRY_STALE)

    def test_no_distinct_snapshot_for_3_reports_is_stale(self):
        """Rule: the same snapshot (session_elapsed_ms not advancing) 3 times -> TELEMETRY_STALE."""
        p = ab.ShadowPolicy()
        p.feed(ab._sample(telemetry(2000, **{"fps": 59.9, "queue": 0, "gap": 17})))
        for _ in range(3):
            p.feed(ab._sample(telemetry(2000, 40.0, 3, 120)))
        self.assertEqual(p.state, ab.TELEMETRY_STALE)
        self.assertEqual(p.reason, "no_distinct_snapshot")
        self.assertEqual(p.decision_seq, 0)

    def test_restart_settling_signature_no_decision(self):
        """Rule: a restart's own settling signature (one report at 45 fps, then clean)
        draws no decision (S1 soak: 40-54 fps for one to three reports)."""
        f = Feeder()
        for _ in range(50):
            f.feed(20, **CLEAN)
            f.feed(1, fps=45.0, queue=1, gap=190)
        f.feed(20, **CLEAN)
        for _ in range(20):
            f.feed(3, fps=48.0, queue=0, gap=200)   # three settling reports
            f.feed(30, **CLEAN)
        self.assertEqual(f.acts(), [])

    def test_resync_waiting_for_idr_never_evidence(self):
        """Rule (D-019): reports during a known resync (waiting_for_idr) never count."""
        f = Feeder()
        f.feed(10, **CLEAN)
        f.feed(20, idr=True, **FALLBACK)
        self.assertEqual(f.acts(), [])

    def test_loss_alone_never_evidence(self):
        """Rule: lost packets / recovered FEC alone never force a decrease."""
        p = ab.ShadowPolicy()
        for i in range(200):
            t = telemetry(2000 * (i + 1), 59.9, 0, 17)
            t["receiver"]["lost_packets_delta"] = 40
            t["fec"]["recovered_packets_delta"] = 40
            p.feed(ab._sample(t))
        self.assertEqual(p.decision_seq, 0)

    def test_new_session_resets(self):
        """Rule: session_elapsed_ms going backwards is a new session: back to REFERENCE at 7000."""
        f = Feeder()
        f.feed(10, **CLEAN)
        f.feed(5, **FALLBACK)
        self.assertEqual(f.p.level_kbps, 5000)
        ev = f.p.feed(ab._sample(telemetry(2000, 59.9, 0, 17)))
        self.assertEqual(ev[0]["event"], "session_reset")
        self.assertEqual(f.p.level_kbps, 7000)
        self.assertEqual(f.p.would_act["FALLBACK"], 0)


class ModeAndWrapperTests(unittest.TestCase):

    def test_mode_default_off(self):
        """Rule: the flag defaults to off."""
        self.assertEqual(ab.mode_from_env({}), ("off", False))
        self.assertEqual(ab.mode_from_env({ab.MODE_ENV: ""}), ("off", False))

    def test_only_off_and_shadow_are_accepted(self):
        """Rule: `shadow` is the only non-off mode; anything else reads off, flagged."""
        self.assertEqual(ab.mode_from_env({ab.MODE_ENV: "shadow"}), ("shadow", False))
        self.assertEqual(ab.mode_from_env({ab.MODE_ENV: " SHADOW "}), ("shadow", False))
        for other in ("on", "act", "enabled", "1", "true", "l" + "ive"):
            self.assertEqual(ab.mode_from_env({ab.MODE_ENV: other}), ("off", True), other)
        self.assertEqual(ab.MODES, ("off", "shadow"))

    def test_off_writes_nothing_and_status_says_off(self):
        """Rule: mode off evaluates nothing, logs nothing, and the field reads mode: off."""
        with tempfile.TemporaryDirectory() as d:
            s = ab.AdaptiveBitrateShadow(Path(d), environ={})
            for i in range(20):
                s.observe(telemetry(2000 * (i + 1), **{"fps": 40.0, "queue": 3, "gap": 400}))
            self.assertEqual(s.status(), {"schema": ab.SCHEMA, "mode": "off", "acted": False})
            self.assertFalse((Path(d) / "logs" / "games" / ab.LOG_NAME).exists())

    def test_shadow_logs_decisions_never_acts(self):
        """Rule: shadow logs one line per decision or state change, never per report,
        and every line and the status carry acted: false."""
        with tempfile.TemporaryDirectory() as d:
            s = ab.AdaptiveBitrateShadow(Path(d), environ={ab.MODE_ENV: "shadow"})
            n = 0
            for _ in range(200):
                n += 1
                s.observe(telemetry(2000 * n, 59.9, 0, 17), stream_bitrate_kbps=7000)
            for _ in range(5):
                n += 1
                s.observe(telemetry(2000 * n, 40.0, 3, 120), stream_bitrate_kbps=7000)
            log = Path(d) / "logs" / "games" / ab.LOG_NAME
            rows = [json.loads(l) for l in log.read_text().splitlines()]
            self.assertLess(len(rows), 20)            # not one per report
            self.assertTrue(all(r["acted"] is False for r in rows))
            self.assertEqual(sum(1 for r in rows if r["event"] == "would_act"
                                 and r["class"] == "FALLBACK"), 1)
            st = s.status()
            self.assertEqual(st["mode"], "shadow")
            self.assertIs(st["acted"], False)
            self.assertEqual(st["would_act"]["FALLBACK"], 1)
            self.assertEqual(st["current_kbps"], 7000)
            self.assertEqual(st["shadow_level_kbps"], 5000)
            for key in ("state", "validated_ladder_kbps", "telemetry_age_ms", "decision_sequence",
                        "reason", "reason_measurements", "hold_down_remaining_reports",
                        "clean_sample_count", "blackout_remaining_reports"):
                self.assertIn(key, st)

    def test_no_actuator_reference(self):
        """Rule: the module holds no actuator: it imports nothing from the stream path."""
        src = Path(ab.__file__).read_text()
        for name in ("native_stream", "set_bitrate", "transition", "restart_encoder", "subprocess"):
            self.assertNotIn("import " + name, src)
            self.assertNotIn(name + "(", src)


if __name__ == "__main__":
    unittest.main()
