#!/usr/bin/env python3
"""G5-S2: the WAN adaptation rules, per rule, with hand fixtures.

    python3 -m unittest discover -s tests/wan_adaptation -v

No stream, no companion: the rules (`WanRules`) alone, then `WanAdaptation`
with the live ladder's real `LivePolicy`. Addresses are built from integers.
"""

from __future__ import annotations

import ast
import ipaddress
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402
import wan_adaptation as wa  # noqa: E402
import wan_telemetry as wt  # noqa: E402

GUARDS = {"stream_active": True, "game_active": True, "game_not_paused": True, "recovery_playing": True,
          "reference_profile": True, "no_override": True, "actuator_bound": True}


def tel(elapsed, fps=59.9, queue=0, gap=16, lost=0, stale=0, idr=False):
    return {"available": True, "fresh": True, "session_elapsed_ms": elapsed,
            "receiver": {"recent_fps": fps, "waiting_for_idr": idr, "lost_packets_delta": lost},
            "decoder": {"queue_depth": queue, "stale_output_drops_delta": stale},
            "latency": {"output_gap_ms": gap}, "fec": {}}


def rep(**kw):
    return wt.report_from_telemetry(tel(kw.pop("elapsed", 1000), **kw))


CLEAN = dict(fps=59.9, queue=0, gap=16, lost=0)
LATENCY = dict(fps=58.0, queue=2, gap=300, lost=0)
CAPACITY = dict(fps=45.0, queue=0, gap=16, lost=120)
LOSSY = dict(fps=59.0, queue=0, gap=16, lost=3)        # 15 lost per window of 10 s = 90 / min, fps held


def fill(rules, spec, n, level=7000, path=wa.PATH_LAN, top=7000):
    out = None
    for i in range(n):
        rules.add_report(rep(elapsed=len(rules.reports) * 2000 + 2000, **spec))
        out = rules.tick(level, path, top_kbps=top)
    return out


class Flag(unittest.TestCase):
    def test_flag(self):
        self.assertTrue(wa.flag_on({wa.FLAG_ENV: "1"}))
        for v in (None, "", "0", "true", "yes", " 2"):
            self.assertFalse(wa.flag_on({} if v is None else {wa.FLAG_ENV: v}), v)
        self.assertIsNone(wa.from_environ({}))
        self.assertIsInstance(wa.from_environ({wa.FLAG_ENV: "1"}), wa.WanAdaptation)

    def test_ladder_imports_only_under_the_flag(self):
        self.assertIsNone(live.WAN_ADAPTATION)          # this process carries no flag
        tree = ast.parse((ROOT / "companion" / "adaptive_bitrate_live.py").read_text())
        top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any("wan_adaptation" in ast.unparse(n) for n in top))
        guarded = [n for n in tree.body if isinstance(n, ast.If) and "wan_adaptation" in ast.unparse(n)]
        self.assertEqual(len(guarded), 1)
        self.assertIn("PRIVYHUB_WAN_ADAPTATION", ast.unparse(guarded[0].test))

    def test_overlay_block_is_g3s(self):
        import session_identity as si   # read only: the same block, built the same way
        self.assertEqual(wa.OVERLAY_NETWORKS, si.OVERLAY_NETWORKS)
        self.assertEqual(wa.path_class({}), wa.PATH_LAN)
        self.assertEqual(wa.path_class({"path_class": "remote"}), wa.PATH_REMOTE)
        self.assertEqual(wa.path_class({"target_address": str(wa.OVERLAY_NETWORKS[0][77])}), wa.PATH_REMOTE)
        self.assertEqual(wa.path_class({"target_address": str(ipaddress.ip_address(0xC0A86439))}), wa.PATH_LAN)


class R1PathChanged(unittest.TestCase):
    def test_hold_then_no_step_up_until_the_window_refills(self):
        r = wa.WanRules()
        fill(r, CLEAN, 100, level=6000)
        r.note_path_event()
        seen = []
        for _ in range(95):
            seen.append(fill(r, CLEAN, 1, level=6000))
        self.assertEqual([s.rule for s in seen[:3]], ["R1.1"] * 3)
        self.assertEqual({s.rule for s in seen[3:89]}, {"R1.2"})
        self.assertEqual(seen[-1].kind, "none")             # 18 clean windows and the window refilled

    def test_recovery_and_overlay_changes_are_events(self):
        r = wa.WanRules()
        self.assertFalse(r.observe_context({"guards": {"recovery_playing": True}}))
        self.assertTrue(r.observe_context({"guards": {"recovery_playing": False}}))
        self.assertEqual(r.since_event, 0)
        r2 = wa.WanRules()
        r2.observe_context({"overlay_path": "direct"})
        self.assertTrue(r2.observe_context({"overlay_path": "relayed"}))

    def test_never_at_the_top(self):
        r = wa.WanRules()
        fill(r, CLEAN, 20)
        r.note_path_event()
        self.assertEqual(fill(r, CLEAN, 1, level=7000).kind, "none")


class R2Latency(unittest.TestCase):
    def test_two_consecutive_windows(self):
        r = wa.WanRules()
        fill(r, CLEAN, 20)
        s = fill(r, LATENCY, 5)
        self.assertNotEqual(s.kind, "step_down")              # one window only
        s = fill(r, LATENCY, 5)
        self.assertEqual((s.kind, s.rule, s.primary), ("step_down", "R2.1", "latency-limited"))

    def test_starved(self):
        r = wa.WanRules()
        s = fill(r, dict(CLEAN, stale=5), 10)             # 25 stale / 10 s = 150 / min >= 20
        self.assertEqual((s.kind, s.rule), ("step_down", "R2.1"))
        self.assertIn("starved", s.classes)

    def test_not_below_the_floor(self):
        r = wa.WanRules()
        self.assertNotEqual(fill(r, LATENCY, 10, level=5000).kind, "step_down")


class R3Capacity(unittest.TestCase):
    def test_step_down(self):
        r = wa.WanRules()
        s = fill(r, CAPACITY, 5, level=6000)
        self.assertEqual((s.kind, s.rule, s.primary), ("step_down", "R3.1", "capacity-limited"))

    def test_lan_floor(self):
        r = wa.WanRules()
        kinds = {fill(r, CAPACITY, 1, level=5000).kind for _ in range(100)}
        self.assertNotIn("step_down", kinds)
        self.assertNotIn("floor_4000", kinds)

    def test_remote_floor_after_the_hold_down_recorded_only(self):
        r = wa.WanRules()
        seen = [fill(r, CAPACITY, 1, level=5000, path=wa.PATH_REMOTE) for _ in range(70)]
        floor = [i for i, s in enumerate(seen) if s.kind == "floor_4000"]
        self.assertTrue(floor)
        # the first full capacity window is report 5; persistence 60 reports from there
        self.assertEqual(floor[0], 4 + wa.R3_FLOOR_PERSIST_REPORTS - 1)
        self.assertEqual(seen[floor[0]].target_kbps, 4000)
        self.assertGreaterEqual(min(s.target_kbps or 4000 for s in seen), wa.REMOTE_FLOOR_KBPS)


class R4Fec(unittest.TestCase):
    def test_no_fec_suggestion(self):
        r = wa.WanRules()
        for spec in (CLEAN, LATENCY, CAPACITY, LOSSY):
            s = fill(r, spec, 10, level=6000)
            self.assertIn(s.kind, ("none", "hold", "no_step_up", "step_down", "floor_4000"))
        self.assertIn("not implemented", wa.R4_NOTE)


class R5Recovery(unittest.TestCase):
    def test_k_clean_windows_lan_and_remote(self):
        for path, k in ((wa.PATH_LAN, 18), (wa.PATH_REMOTE, 36)):
            r = wa.WanRules()
            seen = [fill(r, CLEAN, 1, level=6000, path=path) for _ in range(k * 5 + 1)]
            first_none = next(i for i, s in enumerate(seen) if s.kind == "none")
            self.assertEqual(first_none, k * 5 - 1, path)
            self.assertTrue(all(s.rule == "R5.1" for s in seen[:first_none]))

    def test_lossy_is_not_clean(self):
        r = wa.WanRules()
        fill(r, CLEAN, 90, level=6000)
        s = fill(r, LOSSY, 5, level=6000)
        self.assertEqual((s.kind, s.rule), ("no_step_up", "R5.1"))
        self.assertIn("lossy", s.classes)


class Precedence(unittest.TestCase):
    def test_step_down_beats_hold(self):
        r = wa.WanRules()
        fill(r, CLEAN, 20, level=6000)
        r.note_path_event()
        s = fill(r, CAPACITY, 5, level=6000)
        self.assertEqual(s.kind, "step_down")


# ---- with the real ladder ------------------------------------------------------

def drive(adapt, policy, specs, start=0):
    """Feed (spec, n) blocks; return all events."""
    out = []
    el = start
    for spec, n in specs:
        for _ in range(n):
            el += 2000
            t = tel(el, **spec)
            ctx = {"guards": GUARDS, "clock_ms": el, "stream_kbps": policy.level_kbps}
            evs = adapt.feed(policy, ab._sample(t), ctx, t) if adapt else policy.feed(ab._sample(t), ctx)
            out.extend(evs)
            if policy.pending:
                policy.actuation_done(True, actual_kbps=policy.pending["to_kbps"])
    return out


class WithTheLadder(unittest.TestCase):
    def test_no_suggestion_means_the_ladder_unchanged(self):
        specs = [(CLEAN, 200)]
        a = drive(None, live.LivePolicy(), specs)
        b = [e for e in drive(wa.WanAdaptation(), live.LivePolicy(), specs) if e["event"] != "wan_suggestion"]
        self.assertEqual(a, b)

    def test_increase_blocked_by_r5(self):
        # down to 6000 by the ladder's own capacity trigger, then a lossy-but-ladder-clean stretch
        specs = [(CLEAN, 40), (CAPACITY, 6), (dict(LOSSY, fps=59.5), 200)]
        plain = drive(None, live.LivePolicy(), specs)
        self.assertTrue(any(e["event"] == "transition" and e["direction"] == "up" for e in plain))
        p = live.LivePolicy()
        evs = drive(wa.WanAdaptation(), p, specs)
        self.assertFalse(any(e["event"] == "transition" and e["direction"] == "up" for e in evs))
        refused = [e for e in evs if e["event"] == "refused" and e["reason"] == "wan_no_step_up"]
        self.assertTrue(refused)
        rows = [e for e in evs if e["event"] == "wan_suggestion"]
        self.assertTrue(any(r["ladder_result"] == "blocked_increase" for r in rows))
        self.assertTrue(all(r["source"] == "wan_rules" for r in rows))
        self.assertLess(p.level_kbps, 7000)
        self.assertFalse(hasattr(p, "_decide") and "_decide" in vars(p))    # the wrapper removed

    def test_forced_step_down_through_the_gates(self):
        # latency on 2 windows that the ladder's own rules do not act on (queue 1 on 3 of 5 and
        # gap <= 250 is ROUTINE-level only for the ladder at fps < 57; here fps holds at 58)
        lat = dict(fps=58.5, queue=1, gap=120, lost=0)
        p = live.LivePolicy()
        plain = drive(None, live.LivePolicy(), [(CLEAN, 40), (lat, 10)])
        self.assertFalse(any(e["event"] == "transition" for e in plain))
        evs = drive(wa.WanAdaptation(), p, [(CLEAN, 40), (lat, 10)])
        tr = [e for e in evs if e["event"] == "transition"]
        self.assertEqual(len(tr), 1)
        self.assertEqual((tr[0]["from_kbps"], tr[0]["to_kbps"], tr[0]["reason"], tr[0]["trigger"]),
                         (7000, 6000, "wan_rules", "wan_rules"))
        # the next suggestions meet the ladder's ROUTINE hold-down: refused, not acted
        adapt = wa.WanAdaptation()
        p2 = live.LivePolicy()
        evs3 = drive(adapt, p2, [(CLEAN, 40), (lat, 30)])
        downs = [e for e in evs3 if e["event"] == "transition"]
        refusals = [e for e in evs3 if e["event"] == "refused" and e.get("trigger") == "wan_rules"]
        self.assertEqual(len(downs), 1)
        self.assertTrue(refusals and all(e["reason"] in ("hold_down",) for e in refusals))

    def test_session_age_guard_applies(self):
        lat = dict(fps=58.5, queue=1, gap=120, lost=0)
        evs = drive(wa.WanAdaptation(), live.LivePolicy(), [(lat, 12)])      # < 60 s into the session
        self.assertFalse(any(e["event"] == "transition" for e in evs))
        self.assertTrue(any(e["event"] == "refused" and e["reason"] == "guard" for e in evs))

    def test_one_suggestion_per_tick(self):
        adapt = wa.WanAdaptation()
        p = live.LivePolicy()
        el = 0
        for spec, n in [(CLEAN, 40), (CAPACITY, 20), (LATENCY, 20), (LOSSY, 40)]:
            for _ in range(n):
                el += 2000
                t = tel(el, **spec)
                evs = adapt.feed(p, ab._sample(t), {"guards": GUARDS, "clock_ms": el, "stream_kbps": p.level_kbps}, t)
                self.assertLessEqual(sum(1 for e in evs if e["event"] == "wan_suggestion"), 1)
                if p.pending:
                    p.actuation_done(True, actual_kbps=p.pending["to_kbps"])

    def test_never_below_the_ladder_floor(self):
        p = live.LivePolicy()
        drive(wa.WanAdaptation(), p, [(CLEAN, 40), (CAPACITY, 400)])
        self.assertGreaterEqual(p.level_kbps, 5000)

    def test_new_session_resets_the_rules(self):
        adapt = wa.WanAdaptation()
        p = live.LivePolicy()
        drive(adapt, p, [(CLEAN, 30)], start=100_000)
        drive(adapt, p, [(CLEAN, 2)], start=0)                 # elapsed went back: a new session
        self.assertEqual(len(adapt.rules.reports), 2)


if __name__ == "__main__":
    unittest.main()
