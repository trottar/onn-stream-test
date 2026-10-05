#!/usr/bin/env python3
"""C3-L4-L1: unit tests for the LIVE adaptive-bitrate mode (C3-L4-L2 blend,
C3-L4-N1 capacity trigger and recovery-escalation backstop, C3-L4-N2 mild capacity).

    python3 -m unittest tools/test_adaptive_bitrate_live.py -v

Synthetic telemetry and a fake actuator only; nothing touches the companion,
the stream or the network. Every test names the constraint of
handoffs/C3-L4-L1_LIVE_CONTROLLER_TASK.md it checks (1-7) or the design
note's rule. The shadow suite (test_adaptive_bitrate_shadow.py) is separate
and unchanged.
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "companion"))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402

CLEAN = dict(fps=59.9, queue=0, gap=17)
FALLBACK = dict(fps=40.0, queue=3, gap=120)
FALLBACK_GAP = dict(fps=45.0, queue=0, gap=400)
ROUTINE = dict(fps=55.0, queue=1, gap=60)
SLOW_NO_QUEUE2 = dict(fps=45.0, queue=1, gap=100)   # ROUTINE met, FALLBACK never
UNCLEAN_GAP = dict(fps=59.9, queue=0, gap=200)       # not clean (gap > 150), no evidence
WANDER = dict(fps=57.5, queue=1, gap=120)            # clean by the blend, not by L1's rule

GOOD_GUARDS = {"stream_active": True, "game_active": True, "game_not_paused": True,
               "recovery_playing": True, "reference_profile": True, "no_override": True,
               "actuator_bound": True}


def telemetry(elapsed_ms, fps, queue, gap, *, fresh=True, available=True, idr=False, lost=0):
    return {
        "schema": "privyhub_stream_telemetry_v1",
        "available": available,
        "fresh": fresh,
        "session_elapsed_ms": elapsed_ms,
        "receiver": {"recent_fps": fps, "waiting_for_idr": idr, "lost_packets_delta": lost},
        "decoder": {"queue_depth": queue},
        "latency": {"output_gap_ms": gap},
        "fec": {"recovered_packets_delta": 0},
    }


class Feeder:
    """Feeds the pure LivePolicy one 2 s report at a time; the actuator is
    'instant and successful' unless told otherwise (as in the replays)."""

    def __init__(self, start_ms=60_000, guards=None, auto_confirm=True):
        self.p = live.LivePolicy()
        self.t = start_ms
        self.events = []
        self.guards = dict(GOOD_GUARDS if guards is None else guards)
        self.auto_confirm = auto_confirm
        self.transition_times = []

    def ctx(self):
        return {"guards": dict(self.guards), "clock_ms": self.t}

    def _after(self, ev):
        for e in ev:
            if e["event"] == "transition":
                self.transition_times.append((self.t, e["from_kbps"], e["to_kbps"], e["class"]))
        if self.auto_confirm and self.p.pending is not None:
            self.p.actuation_done(True, actual_kbps=self.p.pending["to_kbps"])

    def feed(self, n=1, **kw):
        out = []
        for _ in range(n):
            self.t += ab.REPORT_INTERVAL_MS
            ev = self.p.feed(ab._sample(telemetry(self.t, kw["fps"], kw["queue"], kw["gap"],
                                                  fresh=kw.get("fresh", True),
                                                  available=kw.get("available", True),
                                                  idr=kw.get("idr", False),
                                                  lost=kw.get("lost", 0))), self.ctx())
            self._after(ev)
            out += ev
        self.events += out
        return out

    def inject(self, kind):
        ev = self.p.inject(kind, self.ctx())
        self._after(ev)
        self.events += ev
        return ev

    def transitions(self, events=None):
        return [e for e in (self.events if events is None else events) if e["event"] == "transition"]

    def refused(self, reason=None, events=None):
        return [e for e in (self.events if events is None else events)
                if e["event"] == "refused" and (reason is None or e["reason"] == reason)]


class OneTransitionPerEvent(unittest.TestCase):
    """Constraint 1: one transition per event, to the mapped target."""

    def test_fallback_is_one_transition_straight_to_5000(self):
        f = Feeder()
        f.feed(20, **CLEAN)
        ev = f.feed(5, **FALLBACK_GAP)
        tr = f.transitions(ev)
        self.assertEqual(len(tr), 1)
        self.assertEqual((tr[0]["class"], tr[0]["from_kbps"], tr[0]["to_kbps"]), ("FALLBACK", 7000, 5000))
        self.assertTrue(tr[0]["acted"])
        f.feed(200, **FALLBACK_GAP)                 # persists: never a second rung
        self.assertEqual(len(f.transitions()), 1)
        self.assertEqual(f.p.level_kbps, 5000)

    def test_routine_is_one_transition_to_6000_then_nothing_while_routine(self):
        f = Feeder()
        f.feed(20, **CLEAN)
        ev = f.feed(5, **ROUTINE)
        tr = f.transitions(ev)
        self.assertEqual([(t["class"], t["from_kbps"], t["to_kbps"]) for t in tr], [("ROUTINE", 7000, 6000)])
        f.feed(300, **ROUTINE)                      # at 6000, ROUTINE names 6000: no step to 5500
        self.assertEqual(len(f.transitions()), 1)
        self.assertTrue(f.refused("at_or_below_target"))

    def test_queue_driven_failure_onset_is_one_transition_to_5000(self):
        """Design rule: ROUTINE defers while the newest report is below 50 fps,
        so a failure onset is ONE transition to 5000, not 6000 then 5000."""
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(8, **FALLBACK)
        self.assertEqual([(t["class"], t["to_kbps"]) for t in f.transitions()], [("FALLBACK", 5000)])

    def test_routine_deferral_is_bounded(self):
        """Design rule: slow (45 fps) with queue 1 meets ROUTINE but never FALLBACK;
        ROUTINE acts after at most 4 deferred reports."""
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(4, **SLOW_NO_QUEUE2)                 # ROUTINE met from the 4th
        self.assertEqual(f.transitions(), [])
        f.feed(4, **SLOW_NO_QUEUE2)
        tr = f.transitions()
        self.assertEqual([(t["class"], t["to_kbps"]) for t in tr], [("ROUTINE", 6000)])

    def test_mapping_table_is_the_only_target_source(self):
        self.assertEqual(live.TARGET_KBPS, {"FALLBACK": 5000, "ROUTINE": 6000})
        for kbps in live.TARGET_KBPS.values():
            self.assertIn(kbps, live.LADDER_KBPS)


class Blackout(unittest.TestCase):
    """Constraint 2: 3 reports after any SSRC change, own or recovery's."""

    def test_three_reports_after_own_transition_are_not_evaluated(self):
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(5, **FALLBACK_GAP)
        before = f.p.suppressed["blackout"]
        ev = f.feed(3, **FALLBACK_GAP)
        self.assertEqual(f.p.suppressed["blackout"] - before, 3)
        self.assertEqual([e for e in ev if e["event"] in ("transition", "refused")], [])
        self.assertEqual(f.p.blackout_remaining, 0)

    def test_injection_inside_blackout_is_refused(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.inject("ROUTINE")
        ev = f.inject("FALLBACK")
        self.assertEqual(ev[0]["reason"], "blackout")
        self.assertEqual(len(f.transitions()), 1)

    def test_recovery_restart_blacks_out_and_clears_evidence(self):
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(4, **FALLBACK_GAP)                  # 4 of 5: nothing yet
        ev = f.p.note_ssrc_change("recovery_restart")
        self.assertEqual(ev[0]["event"], "ssrc_change")
        f.feed(3, **FALLBACK_GAP)                  # blacked out
        self.assertEqual(f.transitions(), [])
        f.feed(4, **FALLBACK_GAP)                  # the window refills from zero
        self.assertEqual(f.transitions(), [])
        f.feed(1, **FALLBACK_GAP)
        self.assertEqual(len(f.transitions()), 1)

    def test_blackout_covers_s1_settling_p95(self):
        """S1: settling one to three reports (<= ~4 s, pooled max 5.0 s): 3 x 2 s = 6 s."""
        self.assertGreaterEqual(live.BLACKOUT_REPORTS * live.REPORT_INTERVAL_MS, 5000)


class HoldDowns(unittest.TestCase):
    """Constraint 1: no two transitions closer than the hold-down that applies."""

    def test_fallback_after_a_down_waits_30_reports(self):
        f = Feeder()
        f.feed(20, **CLEAN)
        while not f.transitions():
            f.feed(1, **ROUTINE)                   # 7000 -> 6000 (on the 4th: 4 of 5)
        f.feed(3, **CLEAN)                         # blackout
        f.feed(26, **FALLBACK_GAP)                 # 29 reports since the transition
        self.assertEqual(f.p.reports_since_action, 29)
        self.assertEqual(len(f.transitions()), 1)
        self.assertTrue(f.refused("hold_down"))
        f.feed(1, **FALLBACK_GAP)                  # 30: allowed
        self.assertEqual([(t["class"], t["to_kbps"]) for t in f.transitions()],
                         [("ROUTINE", 6000), ("FALLBACK", 5000)])

    def test_down_after_an_up_waits_60_reports(self):
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(5, **FALLBACK_GAP)                  # down
        f.feed(3 + 90, **CLEAN)                    # up to 5500
        self.assertEqual([t["to_kbps"] for t in f.transitions()], [5000, 5500])
        f.feed(3 + 55, **FALLBACK_GAP)             # 58 since the up
        self.assertEqual(len(f.transitions()), 2)
        f.feed(2, **FALLBACK_GAP)                  # 60
        self.assertEqual([t["to_kbps"] for t in f.transitions()], [5000, 5500, 5000])

    def test_routine_waits_60_reports_after_any_transition(self):
        f = Feeder()
        f.feed(20, **CLEAN)
        f.inject("ROUTINE")                        # 7000 -> 6000 (level 6000)
        f.p.level_kbps = 7000                      # pretend the stream went back (e.g. a full start)
        f.feed(3, **CLEAN)
        f.feed(55, **ROUTINE)                      # 58 since
        self.assertEqual(len(f.transitions()), 1)
        self.assertTrue(f.refused("hold_down"))
        f.feed(2, **ROUTINE)                       # 60
        self.assertEqual(len(f.transitions()), 2)

    def test_hold_down_seconds_at_the_2s_cadence(self):
        secs = {k: v * live.REPORT_INTERVAL_MS / 1000 for k, v in live.HOLDDOWN_REPORTS.items()}
        self.assertEqual(secs[("FALLBACK", "down")], 60)
        self.assertEqual(secs[("FALLBACK", "up")], 120)
        self.assertEqual(secs[("ROUTINE", "down")], 120)
        # C3-L4-L2: the increase window is 90 reports (180 s), 85 of them clean
        self.assertEqual(live.INCREASE_WINDOW_REPORTS * live.REPORT_INTERVAL_MS / 1000, 180)
        self.assertEqual(live.INCREASE_CLEAN_NEEDED, 85)


class IncreaseCadence(unittest.TestCase):
    """Constraint 1: an increase is one rung per event, >= 90 clean after the blackout."""

    def test_back_to_7000_one_rung_per_event(self):
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(5, **FALLBACK_GAP)
        f.feed(3 + 89, **CLEAN)
        self.assertEqual(len(f.transitions()), 1)
        f.feed(1, **CLEAN)
        f.feed(93, **CLEAN)
        f.feed(93, **CLEAN)
        tr = f.transition_times
        self.assertEqual([(a, b) for _, a, b, _ in tr], [(7000, 5000), (5000, 5500), (5500, 6000), (6000, 7000)])
        gaps = [tr[i + 1][0] - tr[i][0] for i in range(len(tr) - 1)]
        self.assertEqual(gaps, [93 * 2000] * 3)
        self.assertEqual(f.p.rate_limited_events, 0)
        f.feed(500, **CLEAN)
        self.assertEqual(len(f.transitions()), 4)
        self.assertEqual(f.p.state, ab.REFERENCE)

    def test_a_few_unclean_reports_do_not_restart_the_count(self):
        """C3-L4-L2 (replaces L1's consecutive rule): the window is 85 of 90,
        so one unclean report among 90 still steps up at the 90th."""
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(5, **FALLBACK_GAP)
        f.feed(3 + 80, **CLEAN)
        f.feed(1, **UNCLEAN_GAP)
        f.feed(8, **CLEAN)
        self.assertEqual(len(f.transitions()), 1)
        f.feed(1, **CLEAN)                           # the 90th after the blackout
        self.assertEqual([t["to_kbps"] for t in f.transitions()], [5000, 5500])


class BlendIncreaseRule(unittest.TestCase):
    """C3-L4-L2: the user's blend. clean = fps >= 57, queue <= 1, gap <= 150;
    one rung up when >= 85 of the last 90 evaluated reports since the last
    SSRC change (and its blackout) are clean."""

    def _down(self, f):
        f.feed(20, **CLEAN)
        f.feed(5, **FALLBACK_GAP)
        f.feed(3, **CLEAN)                           # the blackout
        self.assertEqual(len(f.p.inc_window), 0)

    def test_clean_boundary(self):
        p = live.LivePolicy()
        smp = lambda fps, q, g: ab._sample(telemetry(1, fps, q, g))
        self.assertTrue(p.increase_clean(smp(57.0, 1, 150)))
        self.assertFalse(p.increase_clean(smp(56.99, 0, 17)))
        self.assertFalse(p.increase_clean(smp(59.9, 2, 17)))
        self.assertFalse(p.increase_clean(smp(59.9, 0, 151)))
        self.assertFalse(p.increase_clean(smp(None, 0, 17)))

    def test_fires_at_exactly_85_of_90(self):
        f = Feeder()
        self._down(f)
        f.feed(5, **UNCLEAN_GAP)
        f.feed(84, **CLEAN)
        self.assertEqual(len(f.transitions()), 1)
        self.assertEqual((len(f.p.inc_window), f.p.clean_count), (89, 84))
        ev = f.feed(1, **CLEAN)                      # 90 reports, 85 clean
        tr = f.transitions(ev)
        self.assertEqual([(t["class"], t["from_kbps"], t["to_kbps"]) for t in tr], [("INCREASE", 5000, 5500)])
        self.assertEqual(tr[0]["measurements"], {"window_reports": 90, "clean_reports": 85})

    def test_84_of_90_does_not_fire_until_the_window_rolls(self):
        f = Feeder()
        self._down(f)
        f.feed(6, **UNCLEAN_GAP)
        f.feed(84, **CLEAN)                          # full window, 84 clean
        self.assertEqual(len(f.transitions()), 1)
        self.assertEqual((len(f.p.inc_window), f.p.clean_count), (90, 84))
        f.feed(1, **CLEAN)                           # the oldest unclean rolls out: 85 of 90
        self.assertEqual([t["to_kbps"] for t in f.transitions()], [5000, 5500])

    def test_the_blend_accepts_the_wander_l1_rejected(self):
        """fps 57-59 with queue 1 (L1 section 5: why the old rule never fired)."""
        f = Feeder()
        self._down(f)
        for _ in range(45):
            f.feed(1, **WANDER)
            f.feed(1, **CLEAN)
        self.assertEqual([t["to_kbps"] for t in f.transitions()], [5000, 5500])

    def test_stale_reports_are_skipped(self):
        f = Feeder()
        self._down(f)
        f.feed(45, **CLEAN)
        f.feed(10, fresh=False, **CLEAN)
        self.assertEqual(len(f.p.inc_window), 45)
        f.feed(44, **CLEAN)
        self.assertEqual(len(f.transitions()), 1)
        f.feed(1, **CLEAN)                           # the 90th EVALUATED report
        self.assertEqual(len(f.transitions()), 2)

    def test_window_empties_after_every_ssrc_change(self):
        f = Feeder()
        self._down(f)
        f.feed(80, **CLEAN)
        f.p.note_ssrc_change("recovery_restart")
        self.assertEqual(len(f.p.inc_window), 0)
        f.feed(3, **CLEAN)                           # recovery's blackout
        f.feed(89, **CLEAN)
        self.assertEqual(len(f.transitions()), 1)
        f.feed(1, **CLEAN)
        self.assertEqual(len(f.transitions()), 2)
        self.assertEqual(len(f.p.inc_window), 0)     # and after the increase's own change

    def test_a_hold_down_in_force_blocks_a_full_window(self):
        f = Feeder()
        self._down(f)
        f.feed(89, **CLEAN)
        f.p.reports_since_action = 10                # white-box: a hold-down still in force
        f.feed(1, **CLEAN)
        self.assertEqual(len(f.transitions()), 1)
        self.assertTrue(f.refused("hold_down"))
        f.p.reports_since_action = 60
        f.feed(1, **CLEAN)
        self.assertEqual(len(f.transitions()), 2)

    def test_resync_reports_enter_the_window_as_not_clean(self):
        f = Feeder()
        self._down(f)
        f.feed(6, idr=True, **CLEAN)
        f.feed(84, **CLEAN)
        self.assertEqual((len(f.p.inc_window), f.p.clean_count), (90, 84))
        self.assertEqual(len(f.transitions()), 1)

    def test_one_rung_per_event_never_two(self):
        f = Feeder()
        self._down(f)
        f.feed(400, **CLEAN)
        tr = f.transition_times
        self.assertEqual([(a, b) for _, a, b, _ in tr], [(7000, 5000), (5000, 5500), (5500, 6000), (6000, 7000)])
        self.assertTrue(all(tr[i + 1][0] - tr[i][0] >= 93 * 2000 for i in range(len(tr) - 1)))

    def test_parity_holds_at_reference(self):
        """An increase needs a prior decrease: a clean or wandering stream at 7000 never acts."""
        f = Feeder()
        for _ in range(500):
            f.feed(1, **WANDER)
            f.feed(1, **CLEAN)
        self.assertEqual(f.transitions(), [])


class Guards(unittest.TestCase):
    """Constraint 3: PLAYING, game active, reference profile, no override, age >= 60 s,
    recovery idle."""

    def _blocked_by(self, guard):
        g = dict(GOOD_GUARDS)
        g[guard] = False
        f = Feeder(guards=g)
        f.feed(20, **CLEAN)
        f.feed(30, **FALLBACK_GAP)
        self.assertEqual(f.transitions(), [])
        r = f.refused("guard")
        self.assertEqual(len(r), 1)                # logged once per run, not per report
        self.assertIn(guard, r[0]["guards_failing"])
        self.assertEqual(f.p.level_kbps, 7000)
        return f

    def test_any_override_blocks(self):
        self._blocked_by("no_override")

    def test_recovery_not_idle_blocks(self):
        self._blocked_by("recovery_playing")

    def test_game_inactive_or_paused_blocks(self):
        self._blocked_by("game_active")
        self._blocked_by("game_not_paused")

    def test_non_reference_profile_blocks(self):
        self._blocked_by("reference_profile")

    def test_stream_inactive_blocks(self):
        self._blocked_by("stream_active")

    def test_session_younger_than_60s_blocks(self):
        f = Feeder(start_ms=0)
        f.feed(10, **CLEAN)                        # to 20 s
        f.feed(10, **FALLBACK_GAP)                 # to 40 s: evidence, but too young
        self.assertEqual(f.transitions(), [])
        self.assertIn("session_age_60s", f.refused("guard")[0]["guards_failing"])
        f.feed(10, **FALLBACK_GAP)                 # past 60 s
        self.assertEqual(len(f.transitions()), 1)

    def test_guard_recovers_then_acts(self):
        f = self._blocked_by("recovery_playing")
        f.guards["recovery_playing"] = True
        f.feed(1, **FALLBACK_GAP)
        self.assertEqual(len(f.transitions()), 1)


class RateLimit(unittest.TestCase):
    """Constraint 4: at most 4 transitions in any 10-minute window."""

    def test_fifth_in_window_is_rate_limited_and_logged(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.p.transition_times_ms = [f.t - 500_000, f.t - 400_000, f.t - 300_000, f.t - 200_000]
        ev = f.feed(5, **FALLBACK_GAP)
        self.assertEqual(f.transitions(ev), [])
        r = f.refused("RATE_LIMITED")
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["transitions_in_window"], 4)
        self.assertTrue(f.p.status()["rate_limited"])
        self.assertEqual(f.p.level_kbps, 7000)
        f.feed(60, **FALLBACK_GAP)                 # 120 s later the oldest has left the window
        self.assertEqual(len(f.transitions()), 1)
        self.assertFalse(f.p.status()["rate_limited"])

    def test_hold_downs_alone_cannot_reach_the_limit_on_the_increase_path(self):
        """Down + three ups (the fastest legal return) is 4 in 558 s: never limited."""
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(5, **FALLBACK_GAP)
        f.feed(3 * 93 + 10, **CLEAN)
        self.assertEqual(len(f.transitions()), 4)
        self.assertEqual(f.p.rate_limited_events, 0)


class OscillationAndFailure(unittest.TestCase):

    def test_third_direction_change_in_10_min_holds_for_the_session(self):
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(5, **FALLBACK_GAP)                  # down
        f.feed(3 + 90, **CLEAN)                    # up (change 1)
        f.feed(60, **FALLBACK_GAP)                 # down (change 2)
        f.feed(3 + 90, **CLEAN)                    # up would be change 3 -> HOLD
        self.assertEqual([t["direction"] for t in f.transitions()], ["down", "up", "down"])
        self.assertEqual(f.p.state, ab.HOLD)
        f.feed(200, **FALLBACK_GAP)
        self.assertEqual(len(f.transitions()), 3)

    def test_actuator_failure_freezes_the_session(self):
        f = Feeder(auto_confirm=False)
        f.feed(20, **CLEAN)
        f.feed(5, **FALLBACK_GAP)
        f.p.actuation_done(False, actual_kbps=7000)
        self.assertTrue(f.p.actuator_failed)
        self.assertEqual(f.p.level_kbps, 7000)
        f.feed(300, **FALLBACK_GAP)
        self.assertEqual(len(f.transitions()), 1)
        self.assertEqual(f.p.state, ab.ACTUATOR_FAILED)

    def test_stale_telemetry_never_decides(self):
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(30, fresh=False, **FALLBACK_GAP)
        f.feed(30, available=False, **FALLBACK_GAP)
        self.assertEqual(f.transitions(), [])


class SessionReset(unittest.TestCase):
    """Constraint 5: every session ends at 7000; a new session starts clean."""

    def test_end_session_resets_to_reference_and_clears_history(self):
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(5, **FALLBACK_GAP)
        f.p.end_session()
        self.assertEqual(f.p.level_kbps, 7000)
        self.assertEqual(f.p.transitions, 0)
        self.assertEqual(f.p.transition_times_ms, [])
        self.assertIsNone(f.p.last_direction)

    def test_client_elapsed_reset_takes_the_stream_level(self):
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(5, **FALLBACK_GAP)
        ev = f.p.feed(ab._sample(telemetry(2000, **{"fps": 59.9, "queue": 0, "gap": 17})),
                      {"stream_kbps": 5000, "guards": GOOD_GUARDS})
        self.assertEqual(ev[0]["event"], "session_reset")
        self.assertEqual(f.p.level_kbps, 5000)
        self.assertEqual(f.p.transitions, 1)       # the companion session's count survives

    def test_level_follows_the_stream(self):
        """A recovery full start resets the encoder to 7000 (C1): the controller follows."""
        f = Feeder()
        f.feed(20, **CLEAN)
        f.feed(5, **FALLBACK_GAP)
        f.t += 2000
        ev = f.p.feed(ab._sample(telemetry(f.t, 59.9, 0, 17)), {"stream_kbps": 7000, "guards": GOOD_GUARDS})
        self.assertEqual(ev[0]["event"], "level_sync")
        self.assertEqual(f.p.level_kbps, 7000)


class InjectedSessionShape(unittest.TestCase):
    """Session B's pre-registration, offline."""

    def test_session_b_offline(self):
        f = Feeder(start_ms=0)
        f.feed(60, **CLEAN)                        # 120 s of PLAYING
        ev = f.inject("FALLBACK")
        tr = f.transitions(ev)
        self.assertEqual([(t["from_kbps"], t["to_kbps"]) for t in tr], [(7000, 5000)])
        self.assertTrue(tr[0]["injected"])
        f.feed(15, **CLEAN)                        # 30 s later
        ev2 = f.inject("FALLBACK")
        self.assertEqual(ev2[0]["event"], "refused")
        self.assertEqual(ev2[0]["reason"], "hold_down")
        f.feed(3 * 93, **CLEAN)
        self.assertEqual([(a, b) for _, a, b, _ in f.transition_times],
                         [(7000, 5000), (5000, 5500), (5500, 6000), (6000, 7000)])


# --------------------------------------------------------------------------
# The wrapper: actuator worker, interlock, serialization, routes, log, status
# --------------------------------------------------------------------------

# --- C3-L4-N1: the capacity trigger and the recovery-escalation backstop -------
# handoffs/C3-L4-N1_NFT_NIGHT1_SCORE_AND_CAPACITY_TRIGGER_TASK.md section 3.
CAP = dict(fps=35.0, queue=0, gap=20, lost=250)       # night 1 under the cap: no queue, heavy loss
CAP_LIGHT = dict(fps=35.0, queue=0, gap=20, lost=10)  # the same fps, loss under the bar
LOSS_ONLY = dict(fps=55.0, queue=0, gap=20, lost=400)  # heavy loss, fps above 50


def strict(f):
    """C3-L4-N2: the strict capacity FALLBACK's own transitions / refusals (the
    mild ROUTINE may act on the same shapes since N2; it is tested below)."""
    return [e for e in f.events if e["event"] in ("transition", "refused") and e.get("trigger") == "capacity"]


class CapacityTrigger(unittest.TestCase):
    """(a) FALLBACK `capacity`: fps < 50 on all 5 and lost >= 50 on >= 3 of 5."""

    def test_fires_at_exactly_5_of_5_fps_and_3_of_5_loss(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.feed(2, **CAP_LIGHT)
        f.feed(2, **CAP)
        self.assertEqual(f.transitions(), [])        # 4 reports: the window is not full of low fps
        ev = f.feed(1, **CAP)                        # 5/5 fps < 50, loss >= 50 on 3/5
        t = f.transitions(ev)
        self.assertEqual(len(t), 1)
        self.assertEqual((t[0]["class"], t[0]["from_kbps"], t[0]["to_kbps"]), ("FALLBACK", 7000, 5000))
        self.assertEqual(t[0]["reason"], "capacity")
        self.assertEqual(t[0]["trigger"], "capacity")
        self.assertEqual(t[0]["measurements"]["lost_packets_delta"], [10.0, 10.0, 250.0, 250.0, 250.0])
        self.assertEqual(f.p.last_action["reason"], "capacity")

    def test_boundaries_are_strict_and_inclusive_as_written(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.feed(5, fps=49.99, queue=0, gap=20, lost=50)   # < 50 and >= 50
        self.assertEqual(len(f.transitions()), 1)
        g = Feeder()
        g.feed(40, **CLEAN)
        g.feed(30, fps=50.0, queue=0, gap=20, lost=500)  # fps 50 is not < 50
        g.feed(30, fps=40.0, queue=0, gap=20, lost=49)   # 49 is not >= 50
        self.assertEqual(strict(g), [])                   # (fps 50 + 500 lost meets capacity_mild since N2)

    def test_not_at_4_of_5_fps(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        for _ in range(30):                          # every window holds one report at fps >= 50
            f.feed(4, **CAP)
            f.feed(1, fps=52.0, queue=0, gap=20, lost=250)
        self.assertEqual(strict(f), [])                   # (capacity_mild acts here since N2)

    def test_not_at_2_of_5_loss(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        for _ in range(30):                          # every window: 2 heavy, 3 light
            f.feed(2, **CAP)
            f.feed(3, **CAP_LIGHT)
        self.assertEqual(f.transitions(), [])
        self.assertEqual(f.refused(), [])

    def test_not_on_loss_alone(self):
        """F2's shape and worse: fps >= 50 with any loss is never capacity."""
        f = Feeder()
        f.feed(40, **CLEAN)
        f.feed(150, **LOSS_ONLY)
        f.feed(150, fps=59.7, queue=0, gap=15, lost=4)
        self.assertEqual(strict(f), [])                   # (fps 55 + 400 lost meets capacity_mild since N2)
        g = Feeder()
        g.feed(40, **CLEAN)
        g.feed(150, fps=58.0, queue=0, gap=15, lost=400)  # loss with fps >= 57: nothing at all
        self.assertEqual(g.transitions(), [])
        self.assertEqual(g.refused(), [])

    def test_stale_reports_never_count(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.feed(4, **CAP)
        f.feed(10, **dict(CAP, fresh=False))         # stale: skipped, the window keeps its 4
        f.feed(10, **dict(CAP, available=False))
        self.assertEqual(f.transitions(), [])
        ev = f.feed(1, **CAP)                         # the 5th evaluated report
        self.assertEqual(len(f.transitions(ev)), 1)

    def test_a_missing_loss_delta_does_not_count(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.feed(3, **dict(CAP, lost=None))
        f.feed(2, **CAP)                              # 5/5 fps, only 2 known deltas >= 50
        self.assertEqual(f.transitions(), [])
        ev = f.feed(1, **CAP)                         # now 3 of the last 5
        self.assertEqual(len(f.transitions(ev)), 1)

    def test_resync_reports_are_not_evidence(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.feed(4, **CAP)
        f.feed(5, **dict(CAP, idr=True))              # waiting_for_idr: never evidence
        self.assertEqual(f.transitions(), [])

    def test_not_while_recovery_is_not_playing(self):
        f = Feeder(guards=dict(GOOD_GUARDS, recovery_playing=False, game_not_paused=False))
        f.feed(40, **CLEAN)
        f.feed(10, **CAP)
        self.assertEqual(f.transitions(), [])
        r = f.refused("guard")
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["trigger"], "capacity")
        self.assertIn("recovery_playing", r[0]["guards_failing"])

    def test_not_during_the_blackout(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.p.note_ssrc_change("recovery_restart")
        ev = f.feed(3, **CAP)
        self.assertEqual({e.get("to") for e in ev if e["event"] == "state"}, {ab.HOLD_DOWN})
        f.feed(4, **CAP)
        self.assertEqual(f.transitions(), [])         # 4 evaluated after the blackout
        f.feed(1, **CAP)
        self.assertEqual(len(f.transitions()), 1)

    def test_not_during_a_hold_down(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.feed(5, **CAP)                              # capacity down to 5000
        f.feed(3 + 90, **CLEAN)                       # the blend climbs to 5500
        self.assertEqual([t["to_kbps"] for t in f.transitions()], [5000, 5500])
        f.feed(3 + 50, **CAP)                         # 53 reports after the up: hold-down 60
        self.assertEqual(len(f.transitions()), 2)
        self.assertEqual(f.refused("hold_down")[0]["trigger"], "capacity")
        f.feed(7, **CAP)
        self.assertEqual([t["to_kbps"] for t in f.transitions()], [5000, 5500, 5000])

    def test_at_5000_it_is_at_floor(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.feed(5, **CAP)
        f.feed(100, **CAP)
        self.assertEqual(len(f.transitions()), 1)
        self.assertEqual(len(f.refused("at_floor")), 1)   # logged once per run of the same refusal

    def test_the_rate_limit_still_binds(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.p.transition_times_ms = [f.t - 500_000, f.t - 400_000, f.t - 300_000, f.t - 200_000]
        f.feed(5, **CAP)
        self.assertEqual(f.transitions(), [])
        r = f.refused("RATE_LIMITED")
        self.assertEqual((len(r), r[0]["trigger"]), (1, "capacity"))

    def test_queue_gap_fallback_keeps_its_own_trigger(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.feed(5, **dict(FALLBACK_GAP, lost=300))    # both bars met: the queue/gap FALLBACK first
        t = f.transitions()
        self.assertEqual((t[0]["reason"], t[0]["trigger"]), ("decrease_fallback", "fps_queue_gap"))

    def test_the_shadow_is_unchanged(self):
        sp = ab.ShadowPolicy()
        t = 60_000
        for _ in range(40):
            t += 2000
            sp.feed(ab._sample(telemetry(t, **{k: CLEAN[k] for k in ("fps", "queue", "gap")})))
        ev = []
        for _ in range(20):
            t += 2000
            ev += sp.feed(ab._sample(telemetry(t, CAP["fps"], CAP["queue"], CAP["gap"], lost=CAP["lost"])))
        self.assertEqual([e for e in ev if e["event"] == "would_act"], [])


class RecoveryEscalation(unittest.TestCase):
    """(b) FALLBACK `recovery_escalation`: two recovery encoder restarts at one
    level within 180 s -> one FALLBACK after PLAYING and the blackout."""

    def restart(self, f, *, playing_after=True, gap_reports=0):
        """One recovery cycle: not PLAYING, the restart (note), PLAYING again."""
        f.guards["recovery_playing"] = False
        f.guards["game_not_paused"] = False
        ev = f.p.note_ssrc_change("recovery_restart", clock_ms=f.t)
        f.events += ev
        if gap_reports:
            f.feed(gap_reports, **CLEAN)
        if playing_after:
            f.guards["recovery_playing"] = True
            f.guards["game_not_paused"] = True
        return ev

    def test_fires_once_after_the_second_restart_within_180s(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        self.restart(f)
        f.feed(5, **CLEAN)                            # 10 s later
        ev = self.restart(f)
        self.assertEqual([e["event"] for e in ev], ["ssrc_change", "escalation_armed"])
        self.assertEqual(ev[1]["restart_gaps_ms"], [10_000])
        blk = f.feed(3, **CLEAN)                      # the blackout
        self.assertEqual(f.transitions(blk), [])
        ev = f.feed(1, **CLEAN)                       # first evaluated report, recovery PLAYING
        t = f.transitions(ev)
        self.assertEqual(len(t), 1)
        self.assertEqual((t[0]["class"], t[0]["from_kbps"], t[0]["to_kbps"], t[0]["reason"]),
                         ("FALLBACK", 7000, 5000, "recovery_escalation"))
        f.feed(200, **CLEAN)                          # ... and never again (the climb is the blend's)
        self.assertEqual([x["reason"] for x in f.transitions()],
                         ["recovery_escalation", "increase_increase", "increase_increase"])

    def test_not_after_two_restarts_181s_apart(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        self.restart(f)
        f.feed(90, **CLEAN)                           # 180 s
        f.t += 1000                                   # 181 s
        ev = self.restart(f)
        self.assertEqual([e["event"] for e in ev], ["ssrc_change"])
        f.feed(20, **CLEAN)
        self.assertEqual(f.transitions(), [])
        self.assertIsNone(f.p.escalation)

    def test_180s_exactly_is_within(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        self.restart(f)
        f.feed(90, **CLEAN)                           # exactly 180 s
        ev = self.restart(f)
        self.assertEqual(ev[-1]["event"], "escalation_armed")

    def test_not_at_different_levels(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        self.restart(f)                               # at 7000
        f.feed(3, **CLEAN)
        f.feed(5, **FALLBACK_GAP)                     # the controller takes the stream to 5000
        self.assertEqual(f.p.level_kbps, 5000)
        ev = self.restart(f)                          # at 5000, 16 s after the first
        self.assertEqual([e["event"] for e in ev], ["ssrc_change"])
        self.assertEqual(ev[0]["restart_level_kbps"], 5000)
        f.feed(20, **CLEAN)
        self.assertEqual(len(f.transitions()), 1)

    def test_a_full_start_counts_at_7000(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        self.restart(f)
        f.guards["recovery_playing"] = False
        ev = f.p.note_ssrc_change("recovery_full_start", clock_ms=f.t + 5000)
        self.assertEqual((ev[0]["restart_level_kbps"], ev[-1]["event"]), (7000, "escalation_armed"))

    def test_a_note_without_a_clock_is_not_a_restart(self):
        """Only the recovery restart path (with its clock) counts; a desync
        pause alone never reaches the controller at all."""
        f = Feeder()
        f.feed(40, **CLEAN)
        for _ in range(3):
            f.p.note_ssrc_change("recovery_restart")
            f.feed(4, **CLEAN)
        self.assertEqual(f.p.recovery_restarts, [])
        self.assertIsNone(f.p.escalation)

    def test_waits_while_recovery_is_not_playing(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        self.restart(f)
        self.restart(f, playing_after=False)
        f.feed(3 + 10, **CLEAN)                       # past the blackout, still PAUSED_RECOVERING
        self.assertEqual(f.transitions(), [])
        self.assertEqual(f.refused(), [])             # it waits; it does not spend itself on the guard
        self.assertIsNotNone(f.p.escalation)
        f.guards["recovery_playing"] = True
        f.guards["game_not_paused"] = True
        ev = f.feed(1, **CLEAN)
        self.assertEqual(f.transitions(ev)[0]["reason"], "recovery_escalation")

    def test_not_during_a_hold_down_and_consumed(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.feed(5, **FALLBACK_GAP)                     # down to 5000
        f.feed(3 + 90, **CLEAN)                       # up to 5500
        self.restart(f)
        f.feed(4, **CLEAN)
        self.restart(f)                               # two at 5500, 8 s apart
        f.feed(4, **CLEAN)                            # blackout, then one evaluated report
        r = f.refused("hold_down")
        self.assertEqual((len(r), r[0]["trigger"]), (1, "recovery_escalation"))
        self.assertIsNone(f.p.escalation)
        f.feed(100, **CLEAN)                          # no later retry from the same pair
        self.assertEqual([t["to_kbps"] for t in f.transitions()], [5000, 5500, 6000])

    def test_at_5000_it_is_at_floor_and_logged(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.feed(5, **FALLBACK_GAP)                     # 5000
        f.feed(40, **CLEAN)                           # past the FALLBACK hold-down
        self.restart(f)
        f.feed(2, **CLEAN)
        self.restart(f)
        f.feed(4, **CLEAN)
        r = f.refused("at_floor")
        self.assertEqual((len(r), r[0]["trigger"]), (1, "recovery_escalation"))
        self.assertEqual(len(f.transitions()), 1)

    def test_its_at_floor_is_logged_after_a_capacity_at_floor(self):
        """Night 1's replay: the capacity bar kept refusing at_floor at 5000; the
        backstop's own at_floor must still be written (not folded into that run)."""
        f = Feeder()
        f.feed(40, **CLEAN)
        f.feed(5, **CAP)                              # capacity -> 5000
        f.feed(40, **CAP)                             # capacity at_floor, logged once
        self.assertEqual(len(f.refused("at_floor")), 1)
        for _ in range(2):
            self.restart(f)
            f.feed(2, **CAP)
            self.restart(f)
            f.feed(4, **CAP)
        esc = [r for r in f.refused("at_floor") if r.get("trigger") == "recovery_escalation"]
        self.assertEqual(len(esc), 2)                 # both escalations, each logged

    def test_the_rate_limit_still_binds(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.p.transition_times_ms = [f.t - 500_000, f.t - 400_000, f.t - 300_000, f.t - 200_000]
        self.restart(f)
        self.restart(f)
        f.feed(4, **CLEAN)
        r = f.refused("RATE_LIMITED")
        self.assertEqual((len(r), r[0]["trigger"]), (1, "recovery_escalation"))
        self.assertEqual(f.transitions(), [])

    def test_disabled_it_would_act_only(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        f.p.acting = False
        self.restart(f)
        self.restart(f)
        ev = f.feed(4, **CLEAN)
        self.assertEqual([e["reason"] for e in ev if e["event"] == "would_act"], ["recovery_escalation"])
        self.assertEqual(f.transitions(), [])

    def test_end_session_clears_it(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        self.restart(f)
        self.restart(f)
        f.p.end_session()
        self.assertIsNone(f.p.escalation)
        self.assertEqual(f.p.recovery_restarts, [])


class NightOneShape(unittest.TestCase):
    """Night 1's F1 as the rules now see it: the cap at 7000 -> ONE capacity
    FALLBACK; the backstop does not fire because capacity acted first."""

    def test_cap_at_7000_is_one_capacity_fallback(self):
        f = Feeder()
        f.feed(90, **CLEAN)                           # the 120 s baseline (part)
        f.feed(2, fps=58.0, queue=0, gap=17, lost=0)
        f.feed(1, fps=35.9, queue=0, gap=4, lost=103)
        f.feed(4, fps=20.0, queue=0, gap=16, lost=250)
        t = f.transitions()
        self.assertEqual([(x["reason"], x["to_kbps"]) for x in t], [("capacity", 5000)])
        f.feed(300, fps=35.0, queue=0, gap=17, lost=250)   # the cap stays, the stream is at the floor
        self.assertEqual(len(f.transitions()), 1)
        self.assertEqual(f.p.rate_limited_events, 0)


# --- C3-L4-N2: the mild capacity trigger (the user's "Go", 2026-09-29) -------------
# handoffs/C3-L4-N2_NFT_NIGHT2_SCORE_AND_MILD_CAPACITY_TASK.md section 3.
MILD = dict(fps=55.0, queue=0, gap=20, lost=60)       # night 2 at 6000 under the cap
MILD_LIGHT = dict(fps=55.0, queue=0, gap=20, lost=10)
MILD_OK_FPS = dict(fps=58.0, queue=0, gap=20, lost=60)


def at_level(kbps):
    """A feeder whose stream sits at <kbps> (as after an earlier transition)."""
    f = Feeder()
    f.feed(40, **CLEAN)
    f.p.level_kbps = kbps
    return f


class MildCapacityTrigger(unittest.TestCase):
    """ROUTINE `capacity_mild`: fps < 57 on >= 4 of 5 and lost >= 50 on >= 3 of 5 -> one rung down."""

    def test_fires_at_4_of_5_fps_and_3_of_5_loss_one_rung(self):
        for start, want in ((7000, 6000), (6000, 5500), (5500, 5000)):
            f = at_level(start)
            f.feed(1, **MILD_OK_FPS)                     # 1 of 5 at fps >= 57
            f.feed(1, **MILD_LIGHT)
            f.feed(1, **MILD_LIGHT)
            f.feed(1, **MILD)
            self.assertEqual(f.transitions(), [])        # 4 reports: 3 under 57
            ev = f.feed(1, **MILD)                       # fps < 57 on 4/5, lost >= 50 on 3/5 (incl. the OK one)
            t = f.transitions(ev)
            self.assertEqual(len(t), 1, start)
            self.assertEqual((t[0]["class"], t[0]["from_kbps"], t[0]["to_kbps"], t[0]["reason"], t[0]["trigger"]),
                             ("ROUTINE", start, want, "capacity_mild", "capacity_mild"))

    def test_boundaries(self):
        f = at_level(6000)
        f.feed(30, fps=56.99, queue=0, gap=20, lost=50)   # < 57 and >= 50: fires
        self.assertEqual([t["to_kbps"] for t in f.transitions()], [5500])
        for fps, lost in ((57.0, 500), (40.0 + 16.0, 49), (56.0, 45)):
            g = at_level(6000)
            g.feed(30, fps=fps, queue=0, gap=20, lost=lost)   # 57.0 is not < 57; 49 / 45 are not >= 50
            self.assertEqual([t for t in g.transitions() if t["direction"] == "down"], [], (fps, lost))

    def test_not_at_3_of_5_fps(self):
        f = at_level(6000)
        for _ in range(30):
            f.feed(3, **MILD)
            f.feed(2, **MILD_OK_FPS)
        self.assertEqual(f.transitions(), [])
        self.assertEqual(f.refused(), [])

    def test_not_at_2_of_5_loss(self):
        f = at_level(6000)
        for _ in range(30):
            f.feed(2, **MILD)
            f.feed(3, **MILD_LIGHT)
        self.assertEqual(f.transitions(), [])
        self.assertEqual(f.refused(), [])

    def test_not_on_loss_alone(self):
        f = at_level(6000)
        f.feed(150, **MILD_OK_FPS)                       # heavy loss, fps >= 57 (clean by the blend)
        self.assertEqual([t for t in f.transitions() if t["direction"] == "down"], [])

    def test_not_on_fps_alone_and_the_queue_routine_is_unchanged(self):
        f = at_level(6000)
        f.feed(150, fps=55.0, queue=0, gap=20, lost=0)  # slow, no loss, no queue: nothing
        self.assertEqual(f.transitions(), [])
        g = Feeder()
        g.feed(40, **CLEAN)
        g.feed(5, **ROUTINE)                             # the old ROUTINE (queue >= 1), no loss
        t = g.transitions()
        self.assertEqual((t[0]["to_kbps"], t[0]["reason"], t[0]["trigger"]), (6000, "decrease_routine", "fps_queue_gap"))

    def test_strict_wins_when_both_hold(self):
        f = Feeder()
        f.feed(40, **CLEAN)
        ev = f.feed(5, fps=40.0, queue=0, gap=20, lost=250)
        t = f.transitions(ev)
        self.assertEqual((len(t), t[0]["reason"], t[0]["to_kbps"]), (1, "capacity", 5000))

    def test_one_rung_never_two_and_the_routine_hold_down(self):
        f = at_level(6000)
        f.feed(4, **MILD)                                 # the 4th meets the bar (the 1st in the window was clean)
        self.assertEqual([t["to_kbps"] for t in f.transitions()], [5500])
        f.feed(3 + 56, **MILD)                            # 59 reports after the down: ROUTINE hold-down 60
        self.assertEqual(len(f.transitions()), 1)
        self.assertEqual(f.refused("hold_down")[0]["trigger"], "capacity_mild")
        f.feed(1, **MILD)                                 # 60
        self.assertEqual([t["to_kbps"] for t in f.transitions()], [5500, 5000])

    def test_at_5000_it_is_at_floor_logged(self):
        f = at_level(5000)
        f.feed(40, **MILD)
        self.assertEqual(f.transitions(), [])
        r = f.refused("at_floor")
        self.assertEqual((len(r), r[0]["trigger"], r[0]["class"]), (1, "capacity_mild", "ROUTINE"))

    def test_not_during_the_blackout(self):
        f = at_level(6000)
        f.p.note_ssrc_change("recovery_restart")
        f.feed(3 + 4, **MILD)                            # 3 blackout + 4 evaluated
        self.assertEqual(f.transitions(), [])
        f.feed(1, **MILD)
        self.assertEqual(len(f.transitions()), 1)

    def test_the_rate_limit_binds(self):
        f = at_level(6000)
        f.p.transition_times_ms = [f.t - 500_000, f.t - 400_000, f.t - 300_000, f.t - 200_000]
        f.feed(5, **MILD)
        r = f.refused("RATE_LIMITED")
        self.assertEqual((len(r), r[0]["trigger"]), (1, "capacity_mild"))
        self.assertEqual(f.transitions(), [])

    def test_the_recovery_guard_binds(self):
        f = at_level(6000)
        f.guards.update(recovery_playing=False, game_not_paused=False)
        f.feed(10, **MILD)
        self.assertEqual(f.transitions(), [])
        self.assertIn("recovery_playing", f.refused("guard")[0]["guards_failing"])

    def test_missing_or_stale_reports_do_not_count(self):
        f = at_level(6000)
        f.feed(4, **dict(MILD, lost=None))
        f.feed(1, **MILD)                                 # only 1 known delta >= 50
        f.feed(10, **dict(MILD, fresh=False))             # stale: skipped
        self.assertEqual(f.transitions(), [])
        f.feed(2, **MILD)                                 # now 3 of the last 5
        self.assertEqual(len(f.transitions()), 1)

    def test_oscillation_guard_holds_the_third_change(self):
        """Night 3's pre-registered shape: 6000 -> 5500 (mild), up to 6000, mild back,
        then the next increase is the 3rd direction change inside 10 min -> HOLD."""
        f = at_level(6000)
        f.feed(5, **MILD)                                 # down 1 (no change yet)
        f.feed(3 + 90, **CLEAN)                           # up: change 1
        f.feed(60, **MILD)                                # down after the reversal hold-down: change 2
        f.feed(3 + 90, **CLEAN)                           # the next up would be change 3
        self.assertEqual([t["to_kbps"] for t in f.transitions()], [5500, 6000, 5500])
        self.assertEqual([e["reason"] for e in f.events if e["event"] == "hold"], ["oscillation"])
        self.assertEqual(f.p.level_kbps, 5500)

    def test_the_shadow_is_unchanged(self):
        sp = ab.ShadowPolicy()
        t = 60_000
        ev = []
        for _ in range(60):
            t += 2000
            ev += sp.feed(ab._sample(telemetry(t, MILD["fps"], MILD["queue"], MILD["gap"], lost=MILD["lost"])))
        self.assertEqual([e for e in ev if e["event"] == "would_act"], [])


class NightTwoShape(unittest.TestCase):
    def test_6000_under_the_cap_steps_to_5500_once(self):
        f = at_level(6000)
        for fps, lost in ((57.8, 12), (55.8, 60), (47.9, 70), (55.8, 58), (53.8, 64), (55.8, 61)):
            f.feed(1, fps=fps, queue=0, gap=16, lost=lost)
        self.assertEqual([(t["to_kbps"], t["reason"]) for t in f.transitions()], [(5500, "capacity_mild")])


def native_status(kbps=7000, *, override=False, profile_id=live.REFERENCE_PROFILE_ID, active=True):
    return {"active": active, "bitrate_kbps": kbps, "profile_id": profile_id,
            "profile": {"bitrate_kbps": 7000}, "encoder_overrides": {"any_override": override}}


class FakeStream:
    def __init__(self):
        self.lock = threading.RLock()
        self.kbps = 7000
        self.calls = []
        self.recovery = "PLAYING"
        self.fail = False
        self.owned_during_call = []

    def actuator(self, target):
        self.owned_during_call.append(self.lock._is_owned())
        self.calls.append(target)
        time.sleep(0.05)
        if self.fail:
            raise RuntimeError("replacement_ffmpeg_unstable")
        prev, self.kbps = self.kbps, target
        return {"ok": True, "from_bitrate_kbps": prev, "target_bitrate_kbps": target,
                "video": {"first_rtp_resume_ms": 90.0, "host_verified_ms": 900.0}}

    def context(self):
        return {"game_active": True, "game_paused": False, "recovery_state": self.recovery}


class WrapperTests(unittest.TestCase):

    def make(self, environ=None):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        c = live.LiveController(Path(d.name), environ=environ or {live.MODE_ENV: "live"})
        fs = FakeStream()
        c.bind(actuator=fs.actuator, context=fs.context, serial_lock=fs.lock,
               recovery_state=lambda: fs.recovery)
        return c, fs, Path(d.name) / "logs" / "games" / ab.LOG_NAME

    def drive(self, c, fs, n, start, **kw):
        t = start
        for _ in range(n):
            t += 2000
            c.observe(telemetry(t, kw["fps"], kw["queue"], kw["gap"], lost=kw.get("lost", 0)),
                      fs.kbps, native_status(fs.kbps))
            for _ in range(200):
                if c._inflight is None:
                    break
                time.sleep(0.005)
        return t

    def test_mode_parsing(self):
        """Constraint 6 / the flag: live is a value of the same flag; off stays the default."""
        self.assertEqual(live.mode_from_env({}), ("off", False))
        self.assertEqual(live.mode_from_env({live.MODE_ENV: "live"}), ("live", False))
        self.assertEqual(live.mode_from_env({live.MODE_ENV: "shadow"}), ("shadow", False))
        self.assertEqual(live.mode_from_env({live.MODE_ENV: "on"}), ("off", True))
        # the shadow module itself is unchanged: it still reads live as off
        self.assertEqual(ab.mode_from_env({ab.MODE_ENV: "live"}), ("off", True))

    def test_transition_goes_through_the_actuator_under_the_stream_lock(self):
        c, fs, log = self.make()
        t = self.drive(c, fs, 40, 0, **CLEAN)
        self.drive(c, fs, 5, t, **FALLBACK_GAP)
        self.assertEqual(fs.calls, [5000])
        self.assertEqual(fs.owned_during_call, [True])
        st = c.status()
        self.assertEqual((st["mode"], st["level"], st["transitions_this_session"]), ("live", 5000, 1))
        self.assertEqual(st["last_action"]["result"], "applied")
        for key in ("mode", "state", "level", "last_action", "transitions_this_session", "rate_limited"):
            self.assertIn(key, st)
        rows = [json.loads(x) for x in log.read_text().splitlines()]
        done = [r for r in rows if r["event"] == "transition_done"]
        self.assertEqual(len(done), 1)
        self.assertTrue(done[0]["acted"])
        req = [r for r in rows if r["event"] == "transition"][0]
        for key in ("class", "to_kbps", "holds_in_force_before", "measurements", "guards", "sample"):
            self.assertIn(key, req)
        self.assertTrue(all(r["mode"] == "live" for r in rows))
        self.assertFalse(any(r["event"] == "state" and r["from"] == r["to"] for r in rows))

    def test_recovery_interlock_under_the_lock_aborts(self):
        """Constraint 3: recovery entering between decision and restart aborts it."""
        c, fs, log = self.make()
        t = self.drive(c, fs, 40, 0, **CLEAN)
        fs.recovery = "PAUSED_RECOVERING"          # context said PLAYING at decision time? force it:
        c._context = lambda: {"game_active": True, "game_paused": False, "recovery_state": "PLAYING"}
        self.drive(c, fs, 5, t, **FALLBACK_GAP)
        self.assertEqual(fs.calls, [])
        st = c.status()
        self.assertEqual(st["transitions_this_session"], 0)
        self.assertEqual(st["level"], 7000)
        self.assertEqual(st["last_action"]["result"], "aborted")
        rows = [json.loads(x) for x in log.read_text().splitlines()]
        self.assertTrue(any(r["event"] == "transition_aborted" for r in rows))

    def test_reports_during_actuation_are_dropped(self):
        c, fs, _ = self.make()
        t = self.drive(c, fs, 40, 0, **CLEAN)
        gate = threading.Event()
        orig = fs.actuator
        c._actuator = lambda target: (gate.wait(2), orig(target))[1]
        for _ in range(5):
            t += 2000
            c.observe(telemetry(t, **FALLBACK_GAP), fs.kbps, native_status(fs.kbps))
        self.assertIsNotNone(c._inflight)
        self.assertEqual(c.status()["state"], live.ACTUATING)
        c.observe(telemetry(t + 2000, **FALLBACK_GAP), fs.kbps, native_status(fs.kbps))
        self.assertEqual(c.status()["reports_dropped_while_actuating"], 1)
        gate.set()
        for _ in range(200):
            if c._inflight is None:
                break
            time.sleep(0.005)
        self.assertEqual(c.status()["policy"]["blackout_remaining_reports"], 3)

    def test_actuator_exception_is_actuator_failed(self):
        c, fs, _ = self.make()
        fs.fail = True
        t = self.drive(c, fs, 40, 0, **CLEAN)
        self.drive(c, fs, 5, t, **FALLBACK_GAP)
        st = c.status()
        self.assertEqual(st["state"], ab.ACTUATOR_FAILED)
        self.assertTrue(st["policy"]["actuator_failed"])

    def test_any_override_from_native_status_blocks(self):
        c, fs, _ = self.make()
        t = 0
        for _ in range(45):
            t += 2000
            kw = CLEAN if t <= 80_000 else FALLBACK_GAP
            c.observe(telemetry(t, **kw), fs.kbps, native_status(fs.kbps, override=True))
        self.assertEqual(fs.calls, [])
        self.assertGreater(c.status()["policy"]["refused"].get("guard", 0), 0)
        rows = [json.loads(x) for x in c.log_path.read_text().splitlines()]
        refused = [r for r in rows if r["event"] == "refused"]
        self.assertEqual(len(refused), 1)
        self.assertIn("no_override", refused[0]["guards_failing"])

    def test_disable_is_idempotent_and_switches_to_shadow(self):
        """Constraint 6: disable -> shadow for the rest of the session; no enable route."""
        c, fs, log = self.make()
        t = self.drive(c, fs, 40, 0, **CLEAN)
        r1 = c.disable()
        r2 = c.disable()
        self.assertFalse(r1["already_disabled"])
        self.assertTrue(r2["already_disabled"])
        self.drive(c, fs, 5, t, **FALLBACK_GAP)
        self.assertEqual(fs.calls, [])
        st = c.status()
        self.assertEqual((st["mode"], st["configured_mode"], st["acts"]), ("shadow", "live", False))
        self.assertEqual(st["policy"]["would_act"]["FALLBACK"], 1)
        rows = [json.loads(x) for x in log.read_text().splitlines()]
        self.assertTrue(any(r["event"] == "would_act" and r["acted"] is False for r in rows))
        self.assertEqual(sum(1 for r in rows if r["event"] == "disabled"), 1)
        c.session_ended()
        self.assertEqual(c.status()["mode"], "live")
        self.assertFalse(hasattr(c, "enable"))

    def test_inject_requires_flag_live_and_loopback(self):
        """Step 3: 403 unless both flags; loopback only; absent from status otherwise."""
        c, fs, _ = self.make()
        self.assertEqual(c.inject("FALLBACK")[0], 403)
        self.assertNotIn("inject_enabled", c.status())
        c2, fs2, _ = self.make({live.MODE_ENV: "live", live.INJECT_ENV: "1"})
        self.assertTrue(c2.status()["inject_enabled"])
        self.assertEqual(c2.inject("BOGUS")[0], 400)
        t = self.drive(c2, fs2, 60, 0, **CLEAN)
        code, body = c2.inject("FALLBACK")
        self.assertEqual(code, 200)
        for _ in range(200):
            if c2._inflight is None:
                break
            time.sleep(0.005)
        self.assertEqual(fs2.calls, [5000])
        t = self.drive(c2, fs2, 15, t, **CLEAN)
        code, body = c2.inject("FALLBACK")
        self.assertEqual(body["events"][0]["reason"], "hold_down")
        self.assertEqual(fs2.calls, [5000])
        c2.disable()
        self.assertEqual(c2.inject("FALLBACK")[0], 403)

    def test_routes(self):
        with tempfile.TemporaryDirectory() as d:
            saved = live._INSTANCE
            try:
                live._INSTANCE = ab.AdaptiveBitrateShadow(Path(d), environ={})
                self.assertEqual(live.handle_route(Path(d), "inject", "class=FALLBACK", "127.0.0.1")[0], 403)
                self.assertEqual(live.handle_route(Path(d), "disable", "", "203.0.113.9")[0], 200)
                self.assertEqual(live.handle_route(Path(d), "enable", "", "127.0.0.1")[0], 404)
                live._INSTANCE = live.LiveController(Path(d), environ={live.MODE_ENV: "live",
                                                                       live.INJECT_ENV: "1"})
                self.assertEqual(live.handle_route(Path(d), "inject", "class=FALLBACK", "203.0.113.9")[0], 403)
                code, body = live.handle_route(Path(d), "disable", "", "203.0.113.9")
                self.assertEqual((code, body["effective_mode"]), (200, "shadow"))
            finally:
                live._INSTANCE = saved

    def test_one_sample_row_per_report(self):
        """C3-L4-L2: live writes a sample row per client report."""
        c, fs, log = self.make()
        t = self.drive(c, fs, 40, 0, **CLEAN)
        self.drive(c, fs, 5, t, **FALLBACK_GAP)
        rows = [json.loads(x) for x in log.read_text().splitlines()]
        samples = [r for r in rows if r["event"] == "sample"]
        self.assertEqual(len(samples), 45)
        for key in ("session_elapsed_ms", "fps", "queue_depth", "output_gap_ms", "fresh", "clean",
                    "disposition", "window_reports", "window_clean", "state", "level_kbps",
                    "blackout_remaining", "holds"):
            self.assertIn(key, samples[0])
        self.assertTrue(all(r["acted"] is False for r in samples))
        self.assertEqual(samples[0]["disposition"], "evaluated")
        self.assertIs(samples[0]["clean"], True)

    def test_recovery_restart_notification_blacks_out(self):
        c, fs, log = self.make()
        self.drive(c, fs, 40, 0, **CLEAN)
        c.note_recovery_restart("recovery_restart")
        self.assertEqual(c.status()["policy"]["blackout_remaining_reports"], 3)

    def test_session_ended_resets(self):
        c, fs, _ = self.make()
        t = self.drive(c, fs, 40, 0, **CLEAN)
        self.drive(c, fs, 5, t, **FALLBACK_GAP)
        c.session_ended()
        st = c.status()
        self.assertEqual(st["transitions_this_session"], 0)
        self.assertEqual(st["policy"]["level_kbps"], 7000)

    def test_capacity_through_the_wrapper_acts_once(self):
        c, fs, log = self.make()
        t = self.drive(c, fs, 40, 0, **CLEAN)
        self.drive(c, fs, 8, t, **CAP)
        self.assertEqual(fs.calls, [5000])
        rows = [json.loads(x) for x in log.read_text().splitlines()]
        tr = [r for r in rows if r.get("event") == "transition"]
        self.assertEqual((tr[0]["reason"], tr[0]["trigger"]), ("capacity", "capacity"))
        self.assertTrue(any(r.get("event") == "transition_done" for r in rows))

    def test_backstop_through_the_wrapper(self):
        """The games plugin calls note_recovery_restart once per recovery
        encoder restart; the controller arms, waits for PLAYING and the
        blackout, then acts once through the same actuator."""
        c, fs, log = self.make()
        t = self.drive(c, fs, 40, 0, **CLEAN)
        fs.recovery = "PAUSED_RECOVERING"
        c.note_recovery_restart("recovery_restart")
        c.note_recovery_restart("recovery_restart")
        self.assertIsNotNone(c.status()["policy"]["recovery_escalation"]["armed"])
        t = self.drive(c, fs, 6, t, **CLEAN)
        self.assertEqual(fs.calls, [])                # recovery not PLAYING: it waits
        fs.recovery = "PLAYING"
        self.drive(c, fs, 1, t, **CLEAN)
        self.assertEqual(fs.calls, [5000])
        rows = [json.loads(x) for x in log.read_text().splitlines()]
        self.assertEqual([r["event"] for r in rows if r.get("event") in ("escalation_armed", "transition")],
                         ["escalation_armed", "transition"])
        self.assertTrue(any(r.get("event") == "sample" and r.get("escalation_armed") for r in rows))

    def test_status_level_after_session_end_is_the_reference(self):
        """C3-L4-N2: night 2 read `level 5000` after BACK (the cached stream bitrate)."""
        c, fs, _ = self.make()
        fs.kbps = 5000
        self.drive(c, fs, 5, 0, **CLEAN)
        self.assertEqual(c.status()["level"], 5000)
        c.session_ended()
        self.assertEqual(c.status()["level"], 7000)

    def test_off_and_shadow_do_not_construct_the_live_controller(self):
        """Constraint 6: off (default) and shadow are the shadow module's own instance."""
        import os
        saved_env, saved = os.environ.get(live.MODE_ENV), live._INSTANCE
        try:
            for value in (None, "shadow", "bogus"):
                live._INSTANCE = None
                if value is None:
                    os.environ.pop(live.MODE_ENV, None)
                else:
                    os.environ[live.MODE_ENV] = value
                ab._INSTANCE = None
                with tempfile.TemporaryDirectory() as d:
                    inst = live.get_controller(Path(d))
                    self.assertIsInstance(inst, ab.AdaptiveBitrateShadow)
                    self.assertFalse(live.is_live(inst))
        finally:
            live._INSTANCE = saved
            ab._INSTANCE = None
            if saved_env is None:
                os.environ.pop(live.MODE_ENV, None)
            else:
                os.environ[live.MODE_ENV] = saved_env



# ---------------------------------------------------------------------------
# C5-M5: the 1080p rung (handoffs/C5-M5_1080P_RUNG_TASK.md sections 2-3;
# pre-registered in evidence/c5_m5_2026-10-03/c5_m5_preregistration.txt).
class RungFeeder(Feeder):
    def __init__(self, top=True, **kw):
        super().__init__(**kw)
        self.p = live.LivePolicy(top_1080p=top)

    def enter(self):
        """450 clean reports from a fresh session -> the entry (asserted)."""
        ev = self.feed(live.RUNG_WINDOW_REPORTS, **CLEAN)
        tr = self.transitions(ev)
        assert tr and tr[-1]["to_kbps"] == live.RUNG_KBPS, tr
        return tr[-1]


MILD = dict(fps=55.0, queue=0, gap=20, lost=60)


class C5M5Rung(unittest.TestCase):
    """C5-M5: entry, leave, re-entry hold-down, rung oscillation, sizes, the
    flag's absence; the actuator argv and recovery at the rung."""

    def test_flag_is_exactly_1080p(self):
        for raw, on in (("1080p", True), (" 1080P ", True), ("1080", False), ("on", False), ("", False), (None, False)):
            env = {} if raw is None else {live.TOP_ENV: raw}
            self.assertEqual(live.top_from_env(env), on, raw)

    def test_entry_fires_at_415_of_450(self):
        # C5-M5B: the threshold is the selection's 415 of 450 (C5-M5 built 435).
        self.assertEqual((live.RUNG_WINDOW_REPORTS, live.RUNG_CLEAN_NEEDED), (450, 415))
        f = RungFeeder()
        f.feed(35, **UNCLEAN_GAP)
        ev = f.feed(414, **CLEAN)
        self.assertEqual(f.transitions(ev), [])
        ev = f.feed(1, **CLEAN)                          # 450 reports, 415 clean
        tr = f.transitions(ev)
        self.assertEqual(len(tr), 1)
        self.assertEqual((tr[0]["from_kbps"], tr[0]["to_kbps"], tr[0]["class"]), (7000, 12600, "INCREASE"))
        self.assertEqual((tr[0]["reason"], tr[0]["trigger"]), ("increase_1080p", "increase_1080p"))
        self.assertEqual((tr[0]["from_size"], tr[0]["to_size"]), ("1280x720", "1920x1080"))

    def test_entry_does_not_fire_at_414_of_450(self):
        f = RungFeeder()
        f.feed(36, **UNCLEAN_GAP)
        ev = f.feed(414, **CLEAN)                        # 450 reports, 414 clean
        self.assertEqual(f.transitions(ev), [])
        self.assertEqual(f.p.status()["rung_1080p"]["window"], {"reports": 450, "clean": 414,
                                                              "window_needed": 450, "clean_needed": 415})
        ev = f.feed(1, **CLEAN)                          # the window rolls: 415 of 450
        self.assertEqual([t["to_kbps"] for t in f.transitions(ev)], [12600])

    def test_entry_with_unclean_reports_spread_through_the_window(self):
        # C5-M5B: 35 unclean reports spread through the window (as on the real holds) do not stop the
        # entry; 36 do. One unclean report every 13th.
        for unclean, fires in ((35, True), (36, False)):
            f = RungFeeder()
            ev, fed_unclean = [], 0
            for i in range(450):
                bad = i % 12 == 5 and i // 12 < unclean
                fed_unclean += bad
                ev += f.feed(1, **(UNCLEAN_GAP if bad else CLEAN))
            self.assertEqual(fed_unclean, unclean)
            self.assertEqual([t["to_kbps"] for t in f.transitions(ev)], [12600] if fires else [], unclean)

    def test_entry_only_from_7000(self):
        f = RungFeeder()
        f.p.level_kbps = 6000
        f.feed(live.RUNG_WINDOW_REPORTS + 50, **CLEAN)
        tos = [t["to_kbps"] for t in f.transitions()]
        self.assertEqual(tos[0], 7000)                  # the blend's one rung first, never straight to the rung
        self.assertNotIn(12600, tos[:1])
        self.assertTrue(all(t["from_kbps"] == 7000 for t in f.transitions() if t["to_kbps"] == 12600))
        # at the rung itself a full clean window decides nothing (the entry is a 7000 rule only)
        g = RungFeeder()
        g.enter()
        ev = g.feed(3 + live.RUNG_WINDOW_REPORTS + 10, **CLEAN)
        self.assertEqual([e for e in ev if e.get("trigger") == "increase_1080p"], [])
        self.assertEqual(g.p.level_kbps, 12600)

    def test_no_rung_without_the_flag(self):
        f = RungFeeder(top=False)
        f.feed(1200, **CLEAN)
        self.assertEqual(f.transitions(), [])
        self.assertEqual(f.p.level_kbps, 7000)
        self.assertEqual(f.p.ladder, (5000, 5500, 6000, 7000))
        self.assertNotIn("rung_1080p", f.p.status())
        self.assertNotIn("rung_window_reports", f.p.holds_in_force())
        self.assertEqual([e for e in f.events if e.get("trigger") == "increase_1080p"], [])   # not even a refusal
        self.assertEqual(f.inject("INCREASE_1080P")[0]["reason"], "no_rung")

    def test_window_restarts_after_an_ssrc_change(self):
        f = RungFeeder()
        f.feed(440, **CLEAN)
        f.p.note_ssrc_change("recovery_restart")
        ev = f.feed(3 + 449, **CLEAN)                     # blackout, then one short of a full window
        self.assertEqual(f.transitions(ev), [])
        self.assertEqual([t["to_kbps"] for t in f.transitions(f.feed(1, **CLEAN))], [12600])

    def test_leave_on_the_first_mild_bar_to_7000_at_720p(self):
        f = RungFeeder()
        f.enter()
        ev = f.feed(3 + 50, **CLEAN) + f.feed(5, **MILD)  # the bar met inside the 60-report hold after an up
        self.assertEqual(f.transitions(ev), [])
        self.assertTrue(f.refused("hold_down", ev))
        f2 = RungFeeder()
        f2.enter()
        f2.feed(3 + 60, **CLEAN)
        ev = f2.feed(5, **MILD)
        tr = f2.transitions(ev)
        self.assertEqual(len(tr), 1)
        self.assertEqual((tr[0]["from_kbps"], tr[0]["to_kbps"], tr[0]["class"], tr[0]["trigger"]),
                         (12600, 7000, "ROUTINE", "capacity_mild"))
        self.assertEqual(tr[0]["to_size"], "1280x720")
        self.assertEqual(tr[0]["rung_leave"], 1)

    def test_strict_from_the_rung_is_fallback_5000(self):
        f = RungFeeder()
        f.enter()
        f.feed(3 + 60, **CLEAN)
        tr = f.transitions(f.feed(5, **FALLBACK))
        self.assertEqual([(t["from_kbps"], t["to_kbps"], t["class"]) for t in tr], [(12600, 5000, "FALLBACK")])

    def test_reentry_hold_is_ten_minutes(self):
        f = RungFeeder()
        f.p.inject  # noqa: B018
        f.enter()
        f.feed(3 + 60, **CLEAN)
        f.feed(5, **MILD)                                # leave at t0
        left_at = f.p.rung_left_clock_ms
        f.feed(3 + 60, **CLEAN)                          # the INCREASE hold after a down (60) has passed
        ev = f.inject("INCREASE_1080P")
        self.assertEqual(ev[0]["event"], "refused")
        self.assertEqual(ev[0]["reason"], "rung_reentry_hold")
        while f.t - left_at < live.RUNG_REENTRY_HOLD_MS:
            f.feed(1, **CLEAN)
        ev = f.inject("INCREASE_1080P")
        self.assertEqual([(e["from_kbps"], e["to_kbps"]) for e in f.transitions(ev)], [(7000, 12600)])

    def test_leave_entry_leave_closes_the_rung(self):
        f = RungFeeder()
        f.enter()
        f.feed(3 + 60, **CLEAN)
        f.feed(5, **MILD)                                # leave 1
        while f.t - f.p.rung_left_clock_ms < live.RUNG_REENTRY_HOLD_MS:
            f.feed(1, **CLEAN)
        self.assertEqual(f.transitions(f.inject("INCREASE_1080P"))[0]["to_kbps"], 12600)   # entry 2
        f.feed(3 + 60, **CLEAN)
        ev = f.feed(5, **MILD)                           # leave 2 -> carried out, then HOLD
        self.assertEqual([(t["from_kbps"], t["to_kbps"]) for t in f.transitions(ev)], [(12600, 7000)])
        self.assertTrue([e for e in ev if e["event"] == "hold" and e["reason"] == "oscillation_rung"])
        self.assertTrue(f.p.rung_closed)
        ev = f.feed(200, **FALLBACK)                     # nothing acts for the rest of the session
        self.assertEqual(f.transitions(ev), [])
        self.assertEqual(f.p.state, ab.HOLD)
        self.assertEqual(f.inject("INCREASE_1080P")[0]["reason"], "oscillation")
        f.p.end_session()
        self.assertFalse(f.p.rung_closed)
        self.assertEqual(f.p.rung_leaves, 0)

    def test_injected_capacity_mild_from_the_rung(self):
        f = RungFeeder()
        f.feed(60, **CLEAN)
        tr = f.transitions(f.inject("INCREASE_1080P"))
        self.assertEqual([(t["to_kbps"], t["reason"], t["injected"]) for t in tr], [(12600, "increase_1080p", True)])
        self.assertEqual(f.inject("CAPACITY_MILD")[0]["reason"], "blackout")
        f.feed(3 + 60, **CLEAN)
        tr = f.transitions(f.inject("CAPACITY_MILD"))
        self.assertEqual([(t["from_kbps"], t["to_kbps"], t["trigger"]) for t in tr], [(12600, 7000, "capacity_mild")])

    def test_size_on_every_level(self):
        for k in (5000, 5500, 6000, 7000):
            self.assertEqual(live.level_size(k), (1280, 720))
        self.assertEqual(live.level_size(12600), (1920, 1080))
        self.assertEqual(live.LivePolicy(top_1080p=True).ladder, (5000, 5500, 6000, 7000, 12600))

    def test_mild_one_rung_down_below_the_rung_unchanged(self):
        f = RungFeeder()
        f.p.level_kbps = 6000
        f.feed(70, **CLEAN)
        f.p.level_kbps, f.p.last_direction, f.p.reports_since_action = 6000, None, None
        tr = f.transitions(f.feed(5, **MILD))
        self.assertEqual([(t["from_kbps"], t["to_kbps"]) for t in tr], [(6000, 5500)])

    def test_controller_status_and_start_row_carry_the_rung_only_with_the_flag(self):
        with tempfile.TemporaryDirectory() as d:
            on = live.LiveController(Path(d), environ={live.TOP_ENV: "1080p"})
            self.assertIn("rung_1080p", on.status()["policy"])
            self.assertEqual(on.status()["validated_ladder_kbps"], [5000, 5500, 6000, 7000, 12600])
            self.assertEqual(on.status()["level_size"], "1280x720")
            off = live.LiveController(Path(d), environ={})
            self.assertNotIn("rung_1080p", off.status()["policy"])
            self.assertEqual(off.status()["validated_ladder_kbps"], [5000, 5500, 6000, 7000])
            rows = [json.loads(x) for x in (Path(d) / "logs" / "games" / ab.LOG_NAME).read_text().splitlines()]
            starts = [r for r in rows if r["event"] == "controller_start"]
            self.assertEqual(starts[0].get("top"), "1080p")
            self.assertNotIn("top", starts[1])


PAUSED = {"recovery_playing": False, "game_not_paused": False}


class C5CloseRungWindow(unittest.TestCase):
    """C5-CLOSE (the user's call after S2b): the rung window skips every report
    while recovery is not PLAYING; the window keeps what it held and resumes
    counting when PLAYING returns. Behind the flag only."""

    def paused(self, f, n, **kw):
        f.guards.update(PAUSED)
        ev = f.feed(n, **kw)
        f.guards.update(GOOD_GUARDS)
        return ev

    def test_a_paused_stretch_neither_counts_nor_qualifies(self):
        f = RungFeeder()
        f.feed(300, **CLEAN)
        ev = self.paused(f, 300, **CLEAN)                 # 600 clean reports, 300 of them paused
        self.assertEqual(f.transitions(ev), [])
        self.assertEqual([e for e in ev if e.get("trigger") == "increase_1080p"], [])   # not even a refusal
        self.assertEqual(f.p.status()["rung_1080p"]["window"]["reports"], 300)
        self.assertEqual(f.p.rung_skipped_not_playing, 300)

    def test_the_window_survives_the_pause_and_resumes_on_playing(self):
        f = RungFeeder()
        f.feed(300, **CLEAN)
        self.paused(f, 200, **CLEAN)
        ev = f.feed(149, **CLEAN)                         # 449 counted
        self.assertEqual(f.transitions(ev), [])
        self.assertEqual([t["to_kbps"] for t in f.transitions(f.feed(1, **CLEAN))], [12600])

    def test_unclean_and_resync_reports_while_paused_are_skipped_too(self):
        f = RungFeeder()
        f.feed(449, **CLEAN)
        self.paused(f, 50, **UNCLEAN_GAP)                 # counted, these 50 would hold the window under 415
        self.paused(f, 5, idr=True, **CLEAN)
        self.assertEqual(f.p.status()["rung_1080p"]["window"], {"reports": 449, "clean": 449,
                                                              "window_needed": 450, "clean_needed": 415})
        self.assertEqual([t["to_kbps"] for t in f.transitions(f.feed(1, **CLEAN))], [12600])

    def test_reports_without_the_recovery_guard_count(self):
        # Only an explicit "recovery not PLAYING" is skipped (a ctx without guards, as some replays feed, counts).
        f = RungFeeder()
        for _ in range(live.RUNG_WINDOW_REPORTS - 1):
            f.t += ab.REPORT_INTERVAL_MS
            f._after(f.p.feed(ab._sample(telemetry(f.t, **CLEAN)), {"clock_ms": f.t}))
        self.assertEqual(f.p.rung_skipped_not_playing, 0)
        self.assertEqual(len(f.p.rung_window), live.RUNG_WINDOW_REPORTS - 1)

    def test_the_status_field_carries_the_rule(self):
        f = RungFeeder()
        f.feed(10, **CLEAN)
        self.paused(f, 7, **CLEAN)
        st = f.p.status()["rung_1080p"]
        self.assertEqual(st["window_rule"], "reports while recovery is not PLAYING are skipped")
        self.assertEqual(st["skipped_not_playing"], 7)
        self.assertEqual(f.p.holds_in_force()["rung_skipped_not_playing"], 7)
        f.p.end_session()
        self.assertEqual(f.p.status()["rung_1080p"]["skipped_not_playing"], 0)

    def test_without_the_flag_nothing_is_skipped_or_shown(self):
        f = RungFeeder(top=False)
        f.feed(20, **CLEAN)
        self.paused(f, 20, **CLEAN)
        self.assertEqual(f.p.rung_skipped_not_playing, 0)
        self.assertNotIn("rung_1080p", f.p.status())
        self.assertNotIn("rung_skipped_not_playing", f.p.holds_in_force())


class C5M5Actuator(unittest.TestCase):
    """The sized actuator against C3-F1's fake manager: the real builder and
    the real encoder-only cycle, nothing spawned."""

    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import test_c3_f1_recovery_restart as f1
        from diagnostics import c3_linux_actuator_probe as probe
        self.f1, self.probe = f1, probe

    def _cycle(self, m, fn, **kw):
        spawned = []

        def popen(argv, **k):
            p = self.f1.FakeProc(argv)
            spawned.append(p)
            return p
        clock = self.f1.Clock()
        out = fn(m, popen_factory=popen, monotonic=clock, sleep=lambda s: None,
                 perf_counter_ns=lambda: int(clock() * 1e9), **kw)
        return out, spawned[0].argv

    def _vf(self, argv):
        return argv[argv.index("-vf") + 1]

    def test_up_down_and_recovery_at_the_rung(self):
        m = self.f1.fake_manager(7000)
        m._active_width, m._active_height = 1280, 720
        out, argv = self._cycle(m, self.probe.run_c3_linux_level_transition, target_bitrate_kbps=12600)
        self.assertTrue(out["ok"])
        self.assertIn("scale=1920:1080", self._vf(argv))
        self.assertEqual((argv[argv.index("-b:v") + 1], argv[argv.index("-maxrate") + 1]), ("12600k", "12600k"))
        self.assertEqual((m._active_bitrate_kbps, m._active_width, m._active_height), (12600, 1920, 1080))
        self.assertEqual((out["from_size"], out["target_size"]), ("1280x720", "1920x1080"))
        out, argv = self._cycle(m, self.probe.run_c3_linux_recovery_restart)       # recovery at the rung
        self.assertIn("scale=1920:1080", self._vf(argv))
        self.assertEqual((m._active_bitrate_kbps, m._active_width), (12600, 1920))
        out, argv = self._cycle(m, self.probe.run_c3_linux_level_transition, target_bitrate_kbps=5000)
        self.assertIn("scale=1280:720", self._vf(argv))
        self.assertEqual((m._active_bitrate_kbps, m._active_width, m._active_height), (5000, 1280, 720))

    def test_the_c3_route_never_reaches_the_rung(self):
        m = self.f1.fake_manager(7000)
        with self.assertRaises(RuntimeError):
            self._cycle(m, self.probe.run_c3_linux_validated_bitrate_transition, target_bitrate_kbps=12600)

    def test_rung_argv_is_the_c3_arm_golden_and_720p_unchanged(self):
        import re
        import native_stream as ns
        ev = Path(__file__).resolve().parents[1] / "docs" / "memory" / "evidence" / "c5_m2_2026-09-29"
        M = ns.NativeStreamManager
        m = object.__new__(M)
        m._apply_profile_selection()
        m._linux_display = lambda: ":0"
        m._linux_vaapi_device = lambda: Path("/dev/dri/renderD128")

        def line(**kw):
            argv = m._build_linux_ffmpeg_command(Path("/usr/bin/ffmpeg"), {"_window_id": 12345}, **kw)
            return re.sub(r"rtp://[0-9.]+", "rtp://<ipv4>", "argv: " + " ".join(argv))

        def golden(name):
            return [x for x in (ev / name).read_text().splitlines() if x.startswith("argv:")][0]
        self.assertEqual(line(bitrate_kbps=12600, max_bitrate_kbps=12600, width=1920, height=1080),
                         golden("golden_after_native_game_1080p60_c3_80pct_cap90.txt"))
        self.assertEqual(line(), golden("golden_after_unset.txt"))

if __name__ == "__main__":
    unittest.main()
