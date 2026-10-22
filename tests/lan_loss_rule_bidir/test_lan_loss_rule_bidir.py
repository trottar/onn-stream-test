#!/usr/bin/env python3
"""LAN-R2: the loss rule renamed to its purpose -- step down when the link is bidirectionally bad
(`PRIVYHUB_LAN_LOSS_RULE=bidir`): LAN-R1's windows (each >= 4 unrecoverable groups) AND, in each window, >= 2 uplink
silences >= 400 ms. LAN-R1's own suite (tests/lan_loss_rule) is untouched.

    python3 -m unittest discover -s tests/lan_loss_rule_bidir -v
"""

from __future__ import annotations

import ast
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tests" / "lan_loss_rule"))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402
import lan_loss_rule as llr  # noqa: E402
import test_lan_loss_rule as T1  # noqa: E402  (LAN-R1's helpers: tel, GUARDS)


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


def drive(rule, policy, clock, specs, start=60_000):
    """(spec, n, uplink_ms_list_per_report) blocks: each report 2 s; silences noted to end inside the report."""
    out, el = [], start
    for spec, n, ups in specs:
        for _ in range(n):
            el += 2000
            clock.t += 2.0
            for k, ms in enumerate(ups):
                end = clock.t - 0.1 * (k + 1)
                rule.uplink.note(end - ms / 1000.0, end)
            t = T1.tel(el, **spec)
            ctx = {"guards": T1.GUARDS, "clock_ms": el, "stream_kbps": policy.level_kbps}
            out.extend(rule.feed(policy, ab._sample(t), ctx, t))
            if policy.pending:
                policy.actuation_done(True, actual_kbps=policy.pending["to_kbps"])
    return out


def bidir():
    c = Clock()
    return llr.LanBidirRule(uplink=llr.UplinkSilences(), clock=c), c


BAD = dict(unrec=1)
CLEAN = dict(unrec=0)


class Flag(unittest.TestCase):
    def test_values(self):
        self.assertIsInstance(llr.from_environ({llr.FLAG_ENV: "bidir"}), llr.LanBidirRule)
        self.assertIsInstance(llr.from_environ({llr.FLAG_ENV: " bidir "}), llr.LanBidirRule)
        r1 = llr.from_environ({llr.FLAG_ENV: "1"})
        self.assertIs(type(r1), llr.LanLossRule)                 # LAN-R1, unchanged
        for v in (None, "", "0", "Bidir", "bi", "2"):
            self.assertIsNone(llr.from_environ({} if v is None else {llr.FLAG_ENV: v}), v)
        self.assertFalse(llr.flag_on({llr.FLAG_ENV: "bidir"}))    # LAN-R1's flag_on, unchanged


class Condition(unittest.TestCase):
    def test_both_terms_in_each_window_fires_labelled_lan_bidir(self):
        r, c = bidir()
        p = live.LivePolicy()
        evs = drive(r, p, c, [(CLEAN, 40, []), (BAD, 10, [450]) ])     # 1 per report: 5 per window >= 2
        rows = [e for e in evs if e.get("event") == "lan_loss_rule"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source"], "lan_bidir")
        self.assertEqual(rows[0]["unrec_windows"], [5, 4])        # fires on the 9th bad report (T = 4), as LAN-R1
        self.assertEqual(rows[0]["uplink_windows"], [5, 4])
        tr = [e for e in evs if e.get("event") == "transition"]
        self.assertEqual([(e["from_kbps"], e["to_kbps"], e["reason"]) for e in tr], [(7000, 6000, "lan_bidir")])

    def test_unrec_alone_is_not_enough(self):
        r, c = bidir()
        evs = drive(r, live.LivePolicy(), c, [(CLEAN, 40, []), (BAD, 30, [])])
        self.assertFalse([e for e in evs if e.get("event") == "lan_loss_rule"])
        r1 = llr.LanLossRule()                                  # LAN-R1 on the same reports: it asks
        p = live.LivePolicy()
        el, out = 60_000, []
        for spec, n in ((CLEAN, 40), (BAD, 30)):
            for _ in range(n):
                el += 2000
                t = T1.tel(el, **spec)
                out += r1.feed(p, ab._sample(t), {"guards": T1.GUARDS, "clock_ms": el, "stream_kbps": p.level_kbps}, t)
                if p.pending:
                    p.actuation_done(True, actual_kbps=p.pending["to_kbps"])
        self.assertTrue([e for e in out if e.get("event") == "lan_loss_rule"])

    def test_uplink_alone_is_not_enough(self):
        r, c = bidir()
        evs = drive(r, live.LivePolicy(), c, [(CLEAN, 60, [600, 600])])
        self.assertFalse([e for e in evs if e.get("event") == "lan_loss_rule"])

    def test_the_boundaries(self):
        # 399-ms silences never count; one 400-ms silence per window is not two
        r, c = bidir()
        evs = drive(r, live.LivePolicy(), c, [(CLEAN, 40, []), (BAD, 10, [399, 399])])
        self.assertFalse([e for e in evs if e.get("event") == "lan_loss_rule"])
        r, c = bidir()
        specs = [(CLEAN, 40, [])] + [(BAD, 1, [400]), (BAD, 4, [])] * 2       # 1 per window
        evs = drive(r, live.LivePolicy(), c, specs)
        self.assertFalse([e for e in evs if e.get("event") == "lan_loss_rule"])
        r, c = bidir()
        specs = [(CLEAN, 40, [])] + [(BAD, 1, [400, 400]), (BAD, 4, [])] * 2  # 2 per window: fires
        evs = drive(r, live.LivePolicy(), c, specs)
        self.assertEqual(len([e for e in evs if e.get("event") == "lan_loss_rule"]), 1)


class Uplink(unittest.TestCase):
    def test_end_attribution_and_bound(self):
        u = llr.UplinkSilences(maxlen=4)
        u.note(10.0, 10.5)                      # 500 ms, ends 10.5
        u.note(11.0, 11.3)                      # 300 ms
        self.assertEqual(u.ended_between(10.0, 11.0, 400), 1)
        self.assertEqual(u.ended_between(10.5, 12.0, 400), 0)  # (a, b]: ended at 10.5 is not after 10.5
        self.assertEqual(u.ended_between(10.0, 12.0, 250), 2)
        for k in range(10):
            u.note(20.0 + k, 20.5 + k)
        self.assertEqual(u.ended_between(0, 100, 0), 4)        # bounded

    def test_the_real_receive_loop_notes_a_silence(self):
        import impairment as imp
        sys.path.insert(0, str(ROOT / "tests" / "impairment"))
        import test_blackout as TB
        import native_session_io as nsio
        sink = llr.UplinkSilences()
        nsio.NativeControllerBridge._uplink_silences = sink
        try:
            gate = imp.UplinkGate(imp.Blackout(0.6, 100.0, 0.5, epoch=time.monotonic()))
            TB.run_bridge(1.6, gate, silence_ms=5000.0)
        finally:
            nsio.NativeControllerBridge._uplink_silences = None
        got = [round((e - s) * 1000) for s, e in list(sink._ring)]
        self.assertTrue(any(550 <= g <= 700 for g in got), got)


class TheLadder(unittest.TestCase):
    def test_the_plugin_sets_the_ladders_rule_only_for_bidir(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        code = ("import sys; sys.path.insert(0, 'companion'); import native_session_io as n, adaptive_bitrate_live as a; "
                "print('lan_loss_rule' in sys.modules, a.LAN_LOSS_RULE, n.NativeControllerBridge._uplink_silences)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=120)
        self.assertEqual(out.stdout.strip(), "False None None", out.stderr[-400:])

    def test_hook_shapes(self):
        def ifs(rel, text):
            tree = ast.parse((ROOT / "companion" / rel).read_text())
            return [n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test).startswith(text)]
        self.assertEqual(len(ifs("native_session_io.py", "self._uplink_silences is not None")), 1)
        self.assertEqual(len(ifs("plugins/games.py", "_lan_bidir is not None")), 1)
        self.assertEqual(len(ifs("plugins/games.py", "(os.environ.get('PRIVYHUB_LAN_LOSS_RULE') or '').strip() == 'bidir'")), 1)
        tree = ast.parse((ROOT / "companion" / "adaptive_bitrate_live.py").read_text())
        guarded = [n for n in tree.body if isinstance(n, ast.If) and "lan_loss_rule" in ast.unparse(n)]
        self.assertEqual(len(guarded), 1)                         # the ladder module itself is untouched

    def test_through_the_real_controller_and_its_actuator(self):
        tc = T1.TheControllerHook()
        mod = live
        old = mod.LAN_LOSS_RULE
        r, c = bidir()
        mod.LAN_LOSS_RULE = r
        try:
            root = Path(tempfile.mkdtemp(prefix="lan_r2_test_"))
            ctl, calls, clock = tc._controller(mod, root)
            el = 60_000
            for spec, n, ups in ((CLEAN, 40, []), (BAD, 12, [450])):
                for _ in range(n):
                    el += 2000
                    clock["t"] += 2.0
                    c.t += 2.0
                    for k, ms in enumerate(ups):
                        r.uplink.note(c.t - 0.1 - ms / 1000.0, c.t - 0.1)
                    ns = {"active": True, "profile_id": live.REFERENCE_PROFILE_ID,
                          "profile": {"bitrate_kbps": live.REFERENCE_KBPS}, "encoder_overrides": {"any_override": False},
                          "bitrate_kbps": ctl._policy.level_kbps}
                    ctl.observe(T1.tel(el, **spec), stream_bitrate_kbps=ctl._policy.level_kbps, native_status=ns)
            import json
            rows = [json.loads(x) for x in ctl.log_path.read_text().splitlines()]
            self.assertEqual(calls, [6000])
            self.assertTrue(any(x.get("event") == "transition" and x.get("reason") == "lan_bidir" for x in rows))
            self.assertTrue(any(x.get("event") == "lan_loss_rule" and x.get("source") == "lan_bidir" for x in rows))
        finally:
            mod.LAN_LOSS_RULE = old
            import importlib
            importlib.reload(mod)


if __name__ == "__main__":
    unittest.main()
