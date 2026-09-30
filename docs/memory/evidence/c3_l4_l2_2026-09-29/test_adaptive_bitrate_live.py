#!/usr/bin/env python3
"""C3-L4-L1: unit tests for the LIVE adaptive-bitrate mode.

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
                                                  idr=kw.get("idr", False))), self.ctx())
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
            c.observe(telemetry(t, kw["fps"], kw["queue"], kw["gap"]), fs.kbps, native_status(fs.kbps))
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


if __name__ == "__main__":
    unittest.main()
