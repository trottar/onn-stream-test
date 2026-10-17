#!/usr/bin/env python3
"""G5-S4: the remote rung cap -- the user's data saver on a remote path.

    python3 -m unittest discover -s tests/remote_cap -v

No stream, no companion. This process carries neither flag, so the globals are
None; `Flags` sets them as the two flags would and restores them; one test runs
child interpreters with the real variables.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402
import remote_cap as rc  # noqa: E402
import remote_ladder as rl  # noqa: E402
import wan_adaptation as wa  # noqa: E402
from diagnostics import c3_linux_actuator_probe as probe  # noqa: E402

GUARDS = {"stream_active": True, "game_active": True, "game_not_paused": True, "recovery_playing": True,
          "reference_profile": True, "no_override": True, "actuator_bound": True}
CLEAN = dict(fps=59.9, queue=0, gap=16, lost=0)
MILD = dict(fps=54.0, queue=0, gap=16, lost=80)
STRICT = dict(fps=45.0, queue=0, gap=16, lost=120)


def tel(elapsed, fps=59.9, queue=0, gap=16, lost=0, stale=0, idr=False):
    return {"available": True, "fresh": True, "session_elapsed_ms": elapsed,
            "receiver": {"recent_fps": fps, "waiting_for_idr": idr, "lost_packets_delta": lost},
            "decoder": {"queue_depth": queue, "stale_output_drops_delta": stale},
            "latency": {"output_gap_ms": gap}, "fec": {}}


class Flags:
    """G5-S3's shared instance (with a class) and a cap, as the flags would set them."""

    def __init__(self, cap: str | None, evidence: str | None = rl.EVIDENCE_OVERLAY, ladder: bool = True):
        self.r = rl.RemoteLadder() if ladder else None
        if self.r is not None and evidence:
            self.r.set_routing_evidence(evidence)
        self.c = rc.from_environ({rc.FLAG_ENV: cap} if cap is not None else {}, self.r)

    def __enter__(self):
        self.saved = (live.REMOTE_LADDER, live.REMOTE_CAP, probe.REMOTE_LADDER, wa.REMOTE_LADDER)
        live.REMOTE_LADDER = probe.REMOTE_LADDER = wa.REMOTE_LADDER = self.r
        live.REMOTE_CAP = self.c
        return self

    def __exit__(self, *exc):
        live.REMOTE_LADDER, live.REMOTE_CAP, probe.REMOTE_LADDER, wa.REMOTE_LADDER = self.saved


def drive(policy, specs, flags=None, adapt=None, start=0):
    """The controller's report path in order: context hook, feed (or the rules), the cap's move; sync actuation."""
    out = []
    el = start
    for spec, n in specs:
        for _ in range(n):
            el += 2000
            t = tel(el, **spec)
            ctx = {"guards": GUARDS, "clock_ms": el, "stream_kbps": policy.level_kbps}
            if live.REMOTE_LADDER is not None:
                live.REMOTE_LADDER.apply(policy, ctx)
            s = ab._sample(t)
            evs = adapt.feed(policy, s, ctx, t) if adapt else policy.feed(s, ctx)
            if live.REMOTE_CAP is not None:
                evs = live.REMOTE_CAP.after_feed(policy, s, ctx, evs)
            out.extend(evs)
            if policy.pending:
                policy.actuation_done(True, actual_kbps=policy.pending["to_kbps"])
    return out


def transitions(evs):
    return [(e["from_kbps"], e["to_kbps"], e["reason"]) for e in evs if e.get("event") == "transition"]


# ------------------------------------------------------------------ the flag ---
class TheFlag(unittest.TestCase):
    def test_absent_or_empty_is_none(self):
        self.assertIsNone(rc.from_environ({}, rl.RemoteLadder()))
        self.assertIsNone(rc.from_environ({rc.FLAG_ENV: "  "}, rl.RemoteLadder()))
        self.assertIsNone(live.REMOTE_CAP)                           # this process carries no flag

    def test_valid_only_at_a_remote_rung(self):
        for v in ("4000", "5000", "5500", "6000", "7000", " 5000 "):
            c = rc.from_environ({rc.FLAG_ENV: v}, rl.RemoteLadder())
            self.assertTrue(c.active, v)
            self.assertEqual(c.cap_kbps, int(v))
        for v, shown in (("3000", 3000), ("4500", 4500), ("8000", 8000), ("12600", 12600), ("-4000", "non-numeric"),
                         ("4000.0", "non-numeric"), ("data-saver", "non-numeric")):
            c = rc.from_environ({rc.FLAG_ENV: v}, rl.RemoteLadder())
            self.assertFalse(c.active, v)
            row = c.config_row()
            self.assertEqual((row["reason"], row["value"], row["cap_kbps"]), ("not_a_remote_rung", shown, None))

    def test_depends_on_g5_s3(self):
        c = rc.from_environ({rc.FLAG_ENV: "4000"}, None)
        self.assertFalse(c.active)
        self.assertEqual(c.config_row()["reason"], "remote_ladder_flag_absent")
        self.assertFalse(c.applies())

    def test_imports_only_under_the_flag(self):
        tree = ast.parse((ROOT / "companion" / "adaptive_bitrate_live.py").read_text())
        top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any("remote_cap" in ast.unparse(n) for n in top))
        guarded = [n for n in tree.body if isinstance(n, ast.If) and "remote_cap" in ast.unparse(n)]
        self.assertEqual(len(guarded), 1)
        self.assertIn("PRIVYHUB_REMOTE_RUNG_CAP", ast.unparse(guarded[0].test))

    def test_real_environment(self):
        code = ("import sys; sys.path.insert(0, %r)\nimport adaptive_bitrate_live as l\n"
                "c = l.REMOTE_CAP\nprint(None if c is None else [c.active, c.reason, c.ladder is l.REMOTE_LADDER],"
                " 'remote_cap' in sys.modules)\n" % str(ROOT / "companion"))
        base = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        base["PYTHONDONTWRITEBYTECODE"] = "1"

        def run(**env):
            out = subprocess.run([sys.executable, "-c", code], env=dict(base, **env), capture_output=True, text=True,
                                 timeout=60)
            return out.stdout.strip() or out.stderr
        self.assertEqual(run(), "None False")
        self.assertEqual(run(PRIVYHUB_REMOTE_RUNG_CAP="4000"), "[False, 'remote_ladder_flag_absent', True] True")
        self.assertEqual(run(PRIVYHUB_REMOTE_RUNG_CAP="4000", PRIVYHUB_REMOTE_LADDER="1"), "[True, None, True] True")
        self.assertEqual(run(PRIVYHUB_REMOTE_RUNG_CAP="4500", PRIVYHUB_REMOTE_LADDER="1"),
                         "[False, 'not_a_remote_rung', True] True")


# ---------------------------------------------------------------- the effect ---
class TheEffect(unittest.TestCase):
    def test_lan_unaffected(self):
        plain = transitions(drive(live.LivePolicy(), [(CLEAN, 40), (MILD, 600)]))
        with Flags("4000", rl.EVIDENCE_NOT_OVERLAY):
            capped = transitions(drive(live.LivePolicy(), [(CLEAN, 40), (MILD, 600)]))
        self.assertEqual(capped, plain)
        self.assertEqual([t[1] for t in plain], [6000, 5500, 5000])

    def test_inactive_cap_is_today(self):
        specs = [(CLEAN, 40), (MILD, 600), (CLEAN, 300)]
        plain = drive(live.LivePolicy(), specs)                       # neither flag
        with Flags("4000", ladder=False):                             # the cap without G5-S3
            self.assertEqual(drive(live.LivePolicy(), specs), plain)
        with Flags(None):                                             # G5-S3 alone, remote
            ladder_only = drive(live.LivePolicy(), specs)
        with Flags("4500"):                                           # G5-S3 + an invalid cap
            self.assertEqual(drive(live.LivePolicy(), specs), ladder_only)

    def test_clean_link_moves_to_each_cap_after_the_guard_and_stays(self):
        for cap in (4000, 5000, 5500, 6000):
            with Flags(str(cap)) as f:
                p = live.LivePolicy()
                evs = drive(p, [(CLEAN, 400)])
            tr = [e for e in evs if e.get("event") == "transition"]
            self.assertEqual([(e["from_kbps"], e["to_kbps"], e["reason"]) for e in tr], [(7000, cap, "remote_cap")], cap)
            self.assertGreaterEqual(min(e["holds_in_force_before"]["reports_since_transition"] or 0 for e in tr), 0)
            self.assertEqual((tr[0]["measurements"]["remote_cap"]["wish_kbps"],
                              tr[0]["measurements"]["remote_cap"]["capped_kbps"]), (7000, cap))
            before = [e for e in evs if e.get("event") == "refused" and e.get("trigger") == "remote_cap"]
            self.assertTrue(before and {e["reason"] for e in before} == {"guard"})   # the 60-s guard first
            blocked = [e for e in evs if e.get("event") == "refused" and e.get("reason") == "remote_cap"]
            self.assertTrue(blocked, cap)                                            # the increase never above
            self.assertTrue(all(e["wish_kbps"] > cap and e["capped_kbps"] == cap and e["source"] == "remote_cap"
                                for e in blocked))
            self.assertEqual(p.level_kbps, cap)
            self.assertGreater(f.c.clamps, 0)
            self.assertEqual(f.c.moves, 1)

    def test_cap_7000_is_no_move(self):
        with Flags("7000"):
            evs = drive(live.LivePolicy(), [(CLEAN, 300)])
        self.assertEqual(transitions(evs), [])

    def test_the_ladders_own_steps_below_the_cap(self):
        with Flags("5000"):
            p = live.LivePolicy()
            evs = drive(p, [(MILD, 400), (CLEAN, 400)])           # the evidence from the start: the ladder decides first
        tr = transitions(evs)
        self.assertEqual(tr[0], (7000, 5000, "capacity_mild"))      # the ladder's 6000 clamped to the cap
        self.assertIn((5000, 4000, "capacity_mild"), tr)            # below the cap: the ladder's own
        self.assertIn((4000, 5000, "increase_increase"), tr)        # up to the cap: allowed
        self.assertFalse([t for t in tr if t[1] > 5000])           # never above it
        first = next(e for e in evs if e.get("event") == "transition")
        self.assertEqual((first["measurements"]["remote_cap"]["wish_kbps"], first["to_kbps"]), (6000, 5000))

    def test_fallback_target_clamped(self):
        with Flags("4000"):
            p = live.LivePolicy()
            drive(p, [(CLEAN, 20)])                                 # before the 60-s guard: no move yet
            evs = p._decide("FALLBACK", {"trigger": "capacity"}, 120_000,
                            live.REMOTE_LADDER.apply(p, {"guards": GUARDS, "clock_ms": 120_000}))
        self.assertEqual((evs[0]["event"], evs[0]["from_kbps"], evs[0]["to_kbps"]), ("transition", 7000, 4000))
        self.assertEqual(evs[0]["measurements"]["remote_cap"]["wish_kbps"], 5000)

    def test_floor_4000_under_a_5000_cap_lands_on_4000(self):
        with Flags("5000"):
            p = live.LivePolicy()
            evs = drive(p, [(CLEAN, 40), (STRICT, 300)], adapt=wa.WanAdaptation())
        tr = [e for e in evs if e.get("event") == "transition"]
        self.assertEqual(tr[0]["to_kbps"], 5000)                     # FALLBACK -> 5000 (at the cap)
        floor = [e for e in tr if e["to_kbps"] == 4000]
        self.assertEqual(len(floor), 1)
        self.assertEqual((floor[0]["reason"], floor[0]["measurements"]["wan_rule"]), ("wan_rules", "R3.2"))
        self.assertEqual(p.level_kbps, 4000)

    def test_full_start_back_at_7000_moves_again(self):
        with Flags("4000"):
            p = live.LivePolicy()
            evs = drive(p, [(CLEAN, 100)])
            el = 202_000
            # a recovery full start: the stream is at 7000 again (C1); the ladder syncs to it
            t = tel(el)
            ctx = live.REMOTE_LADDER.apply(p, {"guards": GUARDS, "clock_ms": el, "stream_kbps": 7000})
            p.note_ssrc_change("recovery_full_start", clock_ms=el)
            evs2 = p.feed(ab._sample(t), ctx)
            self.assertTrue(any(e.get("event") == "level_sync" and e["to_kbps"] == 7000 for e in evs2))
            evs3 = drive(p, [(CLEAN, 80)], start=el)
        self.assertEqual(transitions(evs)[0][1:], (4000, "remote_cap"))
        self.assertIn((7000, 4000, "remote_cap"), transitions(evs3))


# ------------------------------------------------------------------ the rows ---
class _SyncThread:
    def __init__(self, target, args=(), **kw):
        self._t, self._a = target, args

    def start(self):
        self._t(*self._a)


class TheRows(unittest.TestCase):
    def rows(self, cap, evidence=rl.EVIDENCE_OVERLAY, ladder=True, n=200):
        d = tempfile.mkdtemp(prefix="g5_s4_rows_")
        saved = live.threading
        live.threading = types.SimpleNamespace(Thread=_SyncThread, RLock=threading.RLock)
        state = {"kbps": 7000}

        def actuator(k):
            state["kbps"] = k
            return {"ok": True, "target_bitrate_kbps": k}
        try:
            with Flags(cap, evidence, ladder):
                c = live.LiveController(Path(d), environ={})
                c.bind(actuator=actuator, context=lambda: {"game_active": True, "game_paused": False,
                                                           "recovery_state": "PLAYING"},
                       serial_lock=None, recovery_state=lambda: "PLAYING")
                for i in range(n):
                    ns = {"active": True, "profile_id": live.REFERENCE_PROFILE_ID, "profile": {"bitrate_kbps": 7000},
                          "encoder_overrides": {"any_override": False}, "bitrate_kbps": state["kbps"]}
                    c.observe(tel(2000 * (i + 1)), stream_bitrate_kbps=state["kbps"], native_status=ns)
        finally:
            live.threading = saved
        return [json.loads(x) for x in c.log_path.read_text().splitlines()]

    def test_config_row_once_and_the_clamp_recorded(self):
        rows = self.rows("4000")
        cfg = [r for r in rows if r.get("event") == "remote_cap_config"]
        self.assertEqual(len(cfg), 1)
        self.assertEqual((cfg[0]["active"], cfg[0]["cap_kbps"]), (True, 4000))
        tr = [r for r in rows if r.get("event") == "transition"]
        self.assertEqual(len(tr), 1)
        self.assertEqual({k: tr[0][k] for k in ("source", "wish_kbps", "capped_kbps", "cap_kbps", "path_class",
                                                 "reason")},
                         {"source": "remote_cap", "wish_kbps": 7000, "capped_kbps": 4000, "cap_kbps": 4000,
                          "path_class": "remote", "reason": "remote_cap"})
        done = [r for r in rows if r.get("event") == "transition_done"]
        self.assertEqual(done[0]["decision"]["source"], "remote_cap")

    def test_inactive_says_so_once_and_nothing_else(self):
        for cap, ladder, reason in (("4500", True, "not_a_remote_rung"), ("4000", False, "remote_ladder_flag_absent")):
            rows = self.rows(cap, ladder=ladder)
            cfg = [r for r in rows if r.get("event") == "remote_cap_config"]
            self.assertEqual([(r["active"], r["reason"]) for r in cfg], [(False, reason)])
            self.assertFalse([r for r in rows if r.get("event") == "transition"])
            self.assertFalse([r for r in rows if r.get("source") == "remote_cap" and r.get("event") != "remote_cap_config"])

    def test_lan_rows_no_clamp(self):
        rows = self.rows("4000", evidence=rl.EVIDENCE_NOT_OVERLAY)
        self.assertFalse([r for r in rows if r.get("event") == "transition"])
        self.assertFalse([r for r in rows if r.get("source") == "remote_cap" and r.get("event") != "remote_cap_config"])


if __name__ == "__main__":
    unittest.main()
