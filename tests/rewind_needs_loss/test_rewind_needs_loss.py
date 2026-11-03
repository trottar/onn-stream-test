#!/usr/bin/env python3
"""B33: no rewind without loss -- a stall or silence under 1 s with no loss behind it releases with `resume`, not
`state` (inside the adopted `PRIVYHUB_LINK_RECOVERY=1`; `PRIVYHUB_REWIND_NEEDS_LOSS=0` off, `=1` on alone).

    python3 -m unittest discover -s tests/rewind_needs_loss -v

B9's loopback fake core, the real recovery, B4's Rewinder with B9's Cores, B7's StallSignal and B12's StallOwner
(B12's `Down` client), the rule wired as `rewind_cores.wire` wires it. Heartbeats are fed to the rule with their
receive times on its clock; the controller's uplink loss counter is the fake controller's `_lost_packets`.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tests" / "rewind_cores"))
sys.path.insert(0, str(ROOT / "tests" / "stall_owner"))

import hold_rewind as hr  # noqa: E402
import rewind_cores as rc  # noqa: E402
import rewind_needs_loss as rnl  # noqa: E402
import stall_signal as ss  # noqa: E402
import test_rewind_cores as b9  # noqa: E402
import test_stall_owner as b12  # noqa: E402

PSX = b9.PSX
ON = {"PRIVYHUB_REWIND_NEEDS_LOSS": "1"}


def hb(lost=0, unrec=0, gap=40):
    return {"lost_packets": lost, "fec_unrecoverable_groups": unrec, "audio_max_arrival_gap_ms": gap}


def wire_rule(rig):
    rig.ctrl._lost_packets = 0
    return rnl.wire(rig.rw.b9, rig.rec, rig.ctrl, ON)


def releases(rec):
    return [r for r in b9.rows(rec) if r["event"] in ("input_release", "rewind_skipped", "rewind_failed")]


class Stall(unittest.TestCase):
    """A 450-ms picture stall (B12's Down: stalls every 50 ms from 150, the pause at 400, stall_end at 450)."""

    def run_stall(self, beats, uplink_lost_during=0):
        d = b12.Down(core=PSX)
        rule = wire_rule(d.rig)
        t = time.monotonic()
        for dt, rec in beats:                                     # the heartbeats the host has, by receive time
            rule.note_heartbeat(rec, now=t + dt)
        d.until_paused()
        d.rig.wait_saves(1)
        d.rig.ctrl._lost_packets += uplink_lost_during
        d.stall(450, real=True)
        d.stall(10, kind=ss.KIND_END)
        return d, rule

    def test_450_ms_no_loss_pauses_then_resumes_with_no_load(self):
        d, rule = self.run_stall([(-4.0, hb(5, 1)), (-1.0, hb(5, 1))])
        try:
            self.assertEqual(d.rec.calls, ["pause", "resume"])
            saved = [r for r in b9.rows(d.rec) if r["event"] == "state_saved"]
            self.assertEqual((len(saved), saved[0]["kind"]), (1, "stall"))          # the save still happens
            rel = releases(d.rec)
            self.assertEqual(len(rel), 1)
            r = rel[0]
            self.assertEqual((r["event"], r["method"], r["why"], r["via"]),
                             ("input_release", "resume", "no_loss_under_1s", "stall_end"))
            self.assertTrue(400 <= r["held_ms"] < 1000, r)
            self.assertEqual((r["window_lost_packets"], r["window_unrecoverable_groups"], r["uplink_lost_packets"]),
                             (0, 0, 0))
            self.assertNotIn("slot", r)
            time.sleep(0.05)
            self.assertEqual(d.rig.core.loads, [])                                  # no LOAD at the core
            self.assertNotIn("PAUSE_TOGGLE", d.rig.core.log)
            self.assertIsNone(d.rig.rw.b9.last_save)
            self.assertEqual([e for e in d.events() if e[0] == "resumed"], [("resumed", "stall_end")])
            self.assertEqual((rule.resumes, rule.loads), (1, 0))
        finally:
            d.stop()

    def test_the_same_with_loss_loads_as_today(self):
        d, rule = self.run_stall([(-4.0, hb(5, 1)), (-1.0, hb(8, 1))])
        try:
            r = releases(d.rec)[0]
            self.assertEqual((r["event"], r["method"], r["why"], r["slot"]), ("input_release", "state", "loss", 9))
            self.assertEqual(r["window_lost_packets"], 3)
            self.assertEqual(d.rig.core.loads, [True])
            self.assertEqual(d.rec.calls, ["pause", "resume"])
        finally:
            d.stop()

    def test_unrecoverable_groups_alone_are_loss(self):
        d, _ = self.run_stall([(-4.0, hb(5, 1)), (-1.0, hb(5, 2))])
        try:
            self.assertEqual(releases(d.rec)[0]["why"], "loss")
            self.assertEqual(d.rig.core.loads, [True])
        finally:
            d.stop()

    def test_a_dark_span_loads(self):
        d, _ = self.run_stall([(-4.0, hb()), (-1.0, hb(gap=300))])
        try:
            self.assertEqual((releases(d.rec)[0]["method"], releases(d.rec)[0]["why"]), ("state", "dark_span"))
            self.assertEqual(d.rig.core.loads, [True])
        finally:
            d.stop()

    def test_uplink_loss_loads(self):
        d, _ = self.run_stall([(-4.0, hb()), (-1.0, hb())], uplink_lost_during=2)
        try:
            r = releases(d.rec)[0]
            self.assertEqual((r["method"], r["why"], r["uplink_lost_packets"]), ("state", "uplink_loss", 2))
        finally:
            d.stop()

    def test_no_heartbeat_in_the_window_loads(self):
        d, _ = self.run_stall([(-9.0, hb()), (-7.0, hb())])
        try:
            self.assertEqual((releases(d.rec)[0]["method"], releases(d.rec)[0]["why"]), ("state", "no_heartbeat"))
        finally:
            d.stop()

    def test_a_counter_reset_loads(self):
        d, _ = self.run_stall([(-4.0, hb(9)), (-1.0, hb(0))])
        try:
            self.assertEqual(releases(d.rec)[0]["why"], "counter_reset")
        finally:
            d.stop()


class Silence(unittest.TestCase):
    """B2's hold: the save at 400 ms of silence (B9's mark), the release at the first packet back."""

    def run_silence(self, silence_s):
        rig = b9.Rig("1", PSX)
        rule = wire_rule(rig)
        last = time.monotonic() - silence_s
        rule.note_heartbeat(hb(), now=last - 3.0)
        rule.note_heartbeat(hb(), now=last - 0.5)
        rig.det.on_quiet(last + 0.41, last)
        rig.wait_saves(1)
        rig.pause_for_hold(last, last + 0.95)
        row = rig.rw.rewind(rig.rec, "input_release")
        return rig, row

    def test_a_2_s_silence_loads(self):
        rig, row = self.run_silence(2.0)
        try:
            self.assertEqual((row["method"], row["why"], row["slot"]), ("state", "long", 9))
            self.assertGreaterEqual(row["held_ms"], 2000)
            self.assertEqual(b9.rows(rig.rec)[-1]["event"], "input_release")
            self.assertEqual(rig.core.loads, [True])
        finally:
            rig.stop()

    def test_a_sub_second_silence_with_no_loss_resumes(self):
        rig, row = self.run_silence(0.93)
        try:
            self.assertEqual((row["method"], row["why"]), ("resume", "no_loss_under_1s"))
            self.assertTrue(930 <= row["held_ms"] < 1000, row)
            time.sleep(0.05)
            self.assertEqual(rig.core.loads, [])
        finally:
            rig.stop()


class TheSwitch(unittest.TestCase):
    def test_mode(self):
        self.assertEqual(rnl.mode({}), (False, None))
        self.assertEqual(rnl.mode({"PRIVYHUB_LINK_RECOVERY": "1"}), (True, "implied by PRIVYHUB_LINK_RECOVERY=1"))
        self.assertEqual(rnl.mode({"PRIVYHUB_LINK_RECOVERY": "1", rnl.FLAG_ENV: "0"}), (False, "explicit 0"))
        self.assertEqual(rnl.mode({rnl.FLAG_ENV: "1"}), (True, "explicit 1"))
        on, how = rnl.mode({"PRIVYHUB_LINK_RECOVERY": "1", rnl.FLAG_ENV: "yes"})
        self.assertTrue(on)
        self.assertIn("ignored", how)
        self.assertFalse(rnl.mode({rnl.FLAG_ENV: "yes"})[0])
        self.assertFalse(rnl.mode({"PRIVYHUB_LINK_RECOVERY": "0"})[0])

    def _wired(self, env):
        rig = b9.Rig("1", PSX)
        try:
            base = dict(rig.env, **env)
            rec2 = b9.recovery()
            rw = hr.wire(rec2, rig.ctrl, rig.emu, base)
            return rw.b9.no_loss, rec2
        finally:
            rig.stop()

    def test_the_umbrella_wires_it_through_rewind_cores(self):
        rule, rec = self._wired({"PRIVYHUB_LINK_RECOVERY": "1"})
        self.assertIsNotNone(rule)
        self.assertIs(rec._rewind_needs_loss, rule)
        cfg = [r for r in b9.rows(rec) if r["event"] == "rewind_needs_loss_config"]
        self.assertEqual((len(cfg), cfg[0]["how"], cfg[0]["short_ms"]), (1, "implied by PRIVYHUB_LINK_RECOVERY=1", 1000.0))
        rec.note_heartbeat(dict(hb(), last_output_age_ms=10))                    # the recovery feeds it
        self.assertEqual(len(rule._hb), 1)

    def test_zero_absent_and_junk_alone_wire_nothing(self):
        for env in ({"PRIVYHUB_LINK_RECOVERY": "1", rnl.FLAG_ENV: "0"}, {}, {rnl.FLAG_ENV: "yes"}):
            rule, rec = self._wired(env)
            self.assertIsNone(rule, env)
            self.assertIsNone(rec._rewind_needs_loss)
            self.assertNotIn("rewind_needs_loss_config", [r["event"] for r in b9.rows(rec)])

    def test_not_imported_without_it(self):
        code = ("import sys; sys.path.insert(0, 'companion'); sys.path.insert(0, 'tests/rewind_cores');"
                "import test_rewind_cores as b9; r = b9.Rig('1', b9.PSX); r.stop();"
                "print('rewind_needs_loss' in sys.modules)")
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, env=env)
        self.assertEqual(out.stdout.strip(), "False", out.stderr)

    def test_hook_shapes(self):
        src = (ROOT / "companion" / "rewind_cores.py").read_text()
        tree = ast.parse(src)
        imports = [n for n in ast.walk(tree) if isinstance(n, ast.Import)
                   and any(a.name == "rewind_needs_loss" for a in n.names)]
        self.assertEqual(len(imports), 1)                                          # one guarded import, in wire()


if __name__ == "__main__":
    unittest.main()
