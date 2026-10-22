#!/usr/bin/env python3
"""LAN-R1: the LAN loss rule (one rung down on sustained FEC-unrecoverable groups), with hand fixtures.

    python3 -m unittest discover -s tests/lan_loss_rule -v

No stream, no companion: `LanLossRule` with the live ladder's real `LivePolicy`, then the controller's hook.
"""

from __future__ import annotations

import ast
import importlib
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402
import lan_loss_rule as llr  # noqa: E402

GUARDS = {"stream_active": True, "game_active": True, "game_not_paused": True, "recovery_playing": True,
          "reference_profile": True, "no_override": True, "actuator_bound": True}


def tel(elapsed, fps=59.9, queue=0, gap=16, lost=0, unrec=0, idr=False, fec=True):
    return {"available": True, "fresh": True, "session_elapsed_ms": elapsed,
            "receiver": {"recent_fps": fps, "waiting_for_idr": idr, "lost_packets_delta": lost},
            "decoder": {"queue_depth": queue}, "latency": {"output_gap_ms": gap},
            "fec": {"unrecoverable_groups_delta": unrec} if fec else {}}


CLEAN = dict(unrec=0)
BAD = dict(unrec=1)          # 5 per window: >= T = 4


def drive(rule, policy, specs, start=60_000, guards=None, done=True):
    """Feed (spec, n) blocks; return all events."""
    out = []
    el = start
    for spec, n in specs:
        for _ in range(n):
            el += 2000
            t = tel(el, **spec)
            ctx = {"guards": guards or GUARDS, "clock_ms": el, "stream_kbps": policy.level_kbps}
            evs = rule.feed(policy, ab._sample(t), ctx, t) if rule else policy.feed(ab._sample(t), ctx)
            out.extend(evs)
            if done and policy.pending:
                policy.actuation_done(True, actual_kbps=policy.pending["to_kbps"])
    return out


def transitions(evs):
    return [(e["from_kbps"], e["to_kbps"], e.get("reason")) for e in evs if e["event"] == "transition"]


class Flag(unittest.TestCase):
    def test_flag(self):
        self.assertTrue(llr.flag_on({llr.FLAG_ENV: "1"}))
        for v in (None, "", "0", "true", "yes", " 2", "on"):
            self.assertFalse(llr.flag_on({} if v is None else {llr.FLAG_ENV: v}), v)
        self.assertIsNone(llr.from_environ({}))
        self.assertIsInstance(llr.from_environ({llr.FLAG_ENV: " 1 "}), llr.LanLossRule)

    def test_ladder_import_guarded(self):
        tree = ast.parse((ROOT / "companion" / "adaptive_bitrate_live.py").read_text())
        top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any("lan_loss_rule" in ast.unparse(n) for n in top))
        guarded = [n for n in tree.body if isinstance(n, ast.If) and "lan_loss_rule" in ast.unparse(n)]
        self.assertEqual(len(guarded), 1)
        self.assertIn("PRIVYHUB_LAN_LOSS_RULE", ast.unparse(guarded[0].test))

    def test_absent_is_none_in_the_ladder(self):
        if os.environ.get(llr.FLAG_ENV, "").strip() != "1":
            self.assertIsNone(live.LAN_LOSS_RULE)


class Windows(unittest.TestCase):
    def test_exactly_t_on_both_windows_fires(self):
        r = llr.LanLossRule()
        evs = drive(r, live.LivePolicy(), [(CLEAN, 40), (BAD, 4), (dict(unrec=0), 1),
                                           (BAD, 3), (dict(unrec=1), 1), (dict(unrec=0), 1)])
        # windows: [1,1,1,1,0] = 4 and [1,1,1,1,0] = 4 -> fires on the 10th report of the block
        self.assertEqual(transitions(evs), [(7000, 6000, "lan_loss")])

    def test_t_minus_one_on_either_window_does_not(self):
        r = llr.LanLossRule()
        evs = drive(r, live.LivePolicy(), [(CLEAN, 40), (BAD, 3), (CLEAN, 2), (BAD, 4), (CLEAN, 1), (CLEAN, 20)])
        self.assertEqual(transitions(evs), [])
        self.assertEqual(r.asks, 0)

    def test_one_window_is_not_enough(self):
        r = llr.LanLossRule()
        evs = drive(r, live.LivePolicy(), [(CLEAN, 40), (dict(unrec=5), 1), (CLEAN, 4), (CLEAN, 20)])
        self.assertEqual(transitions(evs), [])

    def test_missing_fec_counts_zero(self):
        self.assertEqual(llr.unrec_of(tel(1000, fec=False)), 0)
        self.assertEqual(llr.unrec_of(None), 0)
        self.assertEqual(llr.unrec_of({"fec": {"unrecoverable_groups_delta": True}}), 0)
        self.assertEqual(llr.unrec_of({"fec": {"unrecoverable_groups_delta": -3}}), 0)
        self.assertEqual(llr.unrec_of({"fec": {"unrecoverable_groups_delta": 7}}), 7)

    def test_only_evaluated_reports_count(self):
        r = llr.LanLossRule()
        p = live.LivePolicy()
        drive(r, p, [(CLEAN, 40)])
        # resync reports (waiting_for_idr) are not evaluated: they never enter the rule's windows
        drive(r, p, [(dict(unrec=9, idr=True), 20)], start=p.last_elapsed_ms)
        self.assertEqual(sum(r.values), 0)
        self.assertEqual(r.asks, 0)

    def test_session_reset_clears(self):
        r = llr.LanLossRule()
        p = live.LivePolicy()
        drive(r, p, [(CLEAN, 40), (BAD, 6)])          # windows 5 and 1: no ask yet
        self.assertEqual((len(r.values), sum(r.values), r.asks), (10, 6, 0))   # the newest K x 5 evaluated reports
        drive(r, p, [(BAD, 1)], start=1000)          # elapsed went back: a new client session
        self.assertLessEqual(sum(r.values), 1)       # the old session's 6 are gone

    def test_blackout_rearm_clears(self):
        r = llr.LanLossRule()
        p = live.LivePolicy()
        drive(r, p, [(CLEAN, 40), (BAD, 7)])
        p.note_ssrc_change("recovery_restart", clock_ms=p.last_elapsed_ms)
        drive(r, p, [(BAD, 1)], start=p.last_elapsed_ms)
        self.assertEqual(r.values, [])                 # cleared by the re-armed blackout (that report is blackout)


class OneRungAndTheFloor(unittest.TestCase):
    def test_one_rung_each_time_down_to_5000_and_never_below(self):
        r = llr.LanLossRule()
        p = live.LivePolicy()
        # the ROUTINE hold-down after a down is 60 reports; stay bad long enough for three steps
        evs = drive(r, p, [(CLEAN, 40), (BAD, 300)])
        downs = [t for t in transitions(evs) if t[2] == "lan_loss"]
        self.assertEqual(downs[:3], [(7000, 6000, "lan_loss"), (6000, 5500, "lan_loss"), (5500, 5000, "lan_loss")])
        self.assertTrue(all(t[1] >= 5000 for t in transitions(evs)))
        self.assertTrue(all(e["level_kbps"] > 5000 for e in evs if e["event"] == "lan_loss_rule"))
        # loss does not make a report unclean: the existing increase rule climbs back from 5000; the rule then
        # steps down again, and the oscillation guard ends the cycle (HOLD) -- the design's stated behaviour
        self.assertTrue(any(e["event"] == "hold" and e.get("reason") == "oscillation" for e in evs)
                        or len(transitions(evs)) <= 6)

    def test_the_increase_rule_climbs_back(self):
        r = llr.LanLossRule()
        p = live.LivePolicy()
        evs = drive(r, p, [(CLEAN, 40), (BAD, 10), (CLEAN, 200)])
        t = transitions(evs)
        self.assertEqual(t[0], (7000, 6000, "lan_loss"))
        self.assertEqual(t[1][:2], (6000, 7000))       # the existing increase rule, not this one
        self.assertNotEqual(t[1][2], "lan_loss")


class Gates(unittest.TestCase):
    def test_session_age_guard(self):
        r = llr.LanLossRule()
        evs = drive(r, live.LivePolicy(), [(BAD, 20)], start=0)     # 10 reports in -> 20 s < 60 s
        self.assertEqual(transitions(evs), [])
        refused = [e for e in evs if e["event"] == "refused"]
        self.assertTrue(refused and refused[0]["reason"] == "guard" and refused[0]["trigger"] == "lan_loss")
        self.assertIn("session_age_60s", refused[0]["guards_failing"])

    def test_not_playing_guard(self):
        r = llr.LanLossRule()
        g = dict(GUARDS, recovery_playing=False, game_not_paused=False)
        evs = drive(r, live.LivePolicy(), [(CLEAN, 40), (BAD, 10)], guards=g)
        self.assertEqual(transitions(evs), [])
        rows = [e for e in evs if e["event"] == "lan_loss_rule"]
        self.assertEqual(rows[0]["ladder_result"], "refused:guard")

    def test_hold_down_after_a_transition(self):
        r = llr.LanLossRule()
        p = live.LivePolicy()
        evs = drive(r, p, [(CLEAN, 40), (BAD, 40)])
        self.assertEqual(transitions(evs), [(7000, 6000, "lan_loss")])
        rows = [e["ladder_result"] for e in evs if e["event"] == "lan_loss_rule"]
        self.assertEqual(rows[0], "transition")
        self.assertTrue(any(x == "refused:hold_down" for x in rows[1:]))

    def test_no_ask_when_the_ladder_decided_this_tick(self):
        r = llr.LanLossRule()
        p = live.LivePolicy()
        drive(r, p, [(CLEAN, 40), (BAD, 9)])
        evs = drive(r, p, [(dict(unrec=1, fps=45.0, lost=120), 1)], start=p.last_elapsed_ms)   # not yet a full capacity window
        # the ladder's own decision this tick (if any) wins; the rule adds at most one ask per tick
        self.assertLessEqual(sum(1 for e in evs if e["event"] in ("transition", "refused") and e.get("trigger") == "lan_loss"), 1)
        q = live.LivePolicy()
        r2 = llr.LanLossRule()
        drive(r2, q, [(CLEAN, 40)])
        ev = [{"event": "refused", "class": "ROUTINE", "reason": "x"}]
        q.window.clear()
        r2.values = [1] * 9
        out = r2.after_feed(q, {"elapsed_ms": q.last_elapsed_ms}, {"guards": GUARDS}, tel(0, unrec=1), list(ev))
        self.assertEqual(out, ev)   # disposition is evaluated but the ladder already decided: nothing added

    def test_pending_blocks(self):
        r = llr.LanLossRule()
        p = live.LivePolicy()
        evs = drive(r, p, [(CLEAN, 40), (BAD, 10)], done=False)
        self.assertEqual(transitions(evs), [(7000, 6000, "lan_loss")])
        self.assertIsNotNone(p.pending)               # the actuator rides the policy's pending, as every transition
        evs2 = drive(r, p, [(BAD, 30)], start=p.last_elapsed_ms, done=False)
        self.assertEqual(transitions(evs2), [])


class WithoutTheRule(unittest.TestCase):
    def test_the_plain_ladder_ignores_unrecoverable_groups(self):
        evs = drive(None, live.LivePolicy(), [(CLEAN, 40), (BAD, 300)])
        self.assertEqual(transitions(evs), [])        # today: loss alone never steps down

    def test_rule_with_no_signal_is_the_plain_ladder(self):
        specs = [(CLEAN, 40), (dict(fps=45.0, lost=120), 12), (CLEAN, 150)]
        a = drive(None, live.LivePolicy(), specs)
        b = [e for e in drive(llr.LanLossRule(), live.LivePolicy(), specs) if e["event"] != "lan_loss_rule"]
        self.assertEqual(json.dumps(a, sort_keys=True, default=str), json.dumps(b, sort_keys=True, default=str))


class TheControllerHook(unittest.TestCase):
    def _controller(self, mod, root):
        class _Sync:
            def __init__(self, target, args=(), **kw):
                self.t, self.a = target, args

            def start(self):
                self.t(*self.a)

        clock = {"t": 0.0}
        mod.threading = types.SimpleNamespace(Thread=_Sync, RLock=mod.threading.RLock)
        mod.time = types.SimpleNamespace(monotonic=lambda: clock["t"], time=lambda: clock["t"])
        c = mod.LiveController(root, environ={live.MODE_ENV: "live"})
        calls = []
        c.bind(actuator=lambda kbps: calls.append(kbps) or {"ok": True, "target_bitrate_kbps": kbps},
               context=lambda: {"game_active": True, "game_paused": False, "recovery_state": "PLAYING"},
               serial_lock=None, recovery_state=lambda: "PLAYING")
        return c, calls, clock

    def _run(self, mod, specs):
        root = Path(tempfile.mkdtemp(prefix="lan_r1_test_"))
        c, calls, clock = self._controller(mod, root)
        el = 60_000
        for spec, n in specs:
            for _ in range(n):
                el += 2000
                clock["t"] += 2.0
                ns = {"active": True, "profile_id": live.REFERENCE_PROFILE_ID,
                      "profile": {"bitrate_kbps": live.REFERENCE_KBPS}, "encoder_overrides": {"any_override": False},
                      "bitrate_kbps": c._policy.level_kbps}
                c.observe(tel(el, **spec), stream_bitrate_kbps=c._policy.level_kbps, native_status=ns)
        rows = [json.loads(x) for x in c.log_path.read_text().splitlines()]
        return rows, calls

    def test_flag_on_steps_through_the_existing_actuator(self):
        with mock.patch.dict(os.environ, {llr.FLAG_ENV: "1"}):
            mod = importlib.reload(live)
        try:
            self.assertIsNotNone(mod.LAN_LOSS_RULE)
            rows, calls = self._run(mod, [(CLEAN, 40), (BAD, 12)])
            self.assertEqual(calls, [6000])
            self.assertTrue(any(r.get("event") == "transition" and r.get("reason") == "lan_loss" for r in rows))
            self.assertTrue(any(r.get("event") == "lan_loss_rule" for r in rows))
        finally:
            os.environ.pop(llr.FLAG_ENV, None)
            importlib.reload(live)

    def test_flag_absent_no_rule_row(self):
        mod = importlib.reload(live)
        self.assertIsNone(mod.LAN_LOSS_RULE)
        rows, calls = self._run(mod, [(CLEAN, 40), (BAD, 12)])
        self.assertEqual(calls, [])
        self.assertFalse(any(r.get("event") == "lan_loss_rule" for r in rows))


if __name__ == "__main__":
    unittest.main()
