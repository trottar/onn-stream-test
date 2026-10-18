#!/usr/bin/env python3
"""G8-S4: the encoder's rate-control profile.

    python3 -m unittest discover -s tests/encoder_rc -v

No stream, no companion, no encoder: the command builder runs on G8-S2's stub manager;
the live actuator (the real `run_c3_linux_validated_bitrate_transition` and the sized
`run_c3_linux_level_transition`) on C3-F1's fake manager with a recording Popen. This
process carries no flag, so `native_stream.ENCODER_RC` is None; cases set it and restore
it. Addresses are built from integers.
"""

from __future__ import annotations

import ast
import ipaddress
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests" / "start_rung"))

import encoder_rc as erc  # noqa: E402
import native_stream as ns  # noqa: E402
import stub_manager as stub  # noqa: E402
import test_c3_f1_recovery_restart as f1  # noqa: E402
from diagnostics import c3_linux_actuator_probe as probe  # noqa: E402

LAN = str(ipaddress.ip_address(0xC0A80117))


def rate(argv):
    i, j = argv.index("-b:v"), argv.index("-g")
    return argv[i:j]


class Flag:
    def __init__(self, profile, environ=None):
        self.rc = erc.EncoderRc(profile, log=lambda s: None, environ=environ or {})

    def __enter__(self):
        self.saved = ns.ENCODER_RC
        ns.ENCODER_RC = self.rc
        return self.rc

    def __exit__(self, *a):
        ns.ENCODER_RC = self.saved


def build(target=None, **kw):
    m = stub.stub_manager(ns, [])
    if target is not None:
        kw.update(bitrate_kbps=target, max_bitrate_kbps=target)
    from pathlib import Path as P
    return m._build_linux_ffmpeg_command(ffmpeg=P("/fixture/ffmpeg"), capture_target={"_window_id": 4242}, **kw)


def actuator(target, sized=False, current=7000):
    m = f1.fake_manager(current)
    clock = f1.Clock()
    got = []
    fn = probe.run_c3_linux_level_transition if sized else probe.run_c3_linux_validated_bitrate_transition
    fn(m, target_bitrate_kbps=target, popen_factory=lambda a, **kw: got.append(a) or f1.FakeProc(a),
       monotonic=clock, sleep=lambda s: None, perf_counter_ns=lambda: int(clock() * 1e9))
    return got[0]


class TestParse(unittest.TestCase):
    def test_profiles(self):
        self.assertEqual(erc.parse("tight"), "tight")
        self.assertEqual(erc.parse(" Headroom "), "headroom")
        for raw in ("", "loose", "cbr", "tight,x", None):
            self.assertIsNone(erc.parse(raw), raw)

    def test_rate_options(self):
        self.assertEqual(erc.rate_options("tight", 5000), {"rc_mode": "CBR", "maxrate_kbps": 5000, "bufsize_kbits": 1250})
        self.assertEqual(erc.rate_options("headroom", 5000),
                         {"rc_mode": "VBR", "maxrate_kbps": 5500, "bufsize_kbits": 1250})
        self.assertEqual(erc.rate_options("headroom", 4000)["maxrate_kbps"], 4400)
        self.assertEqual(erc.rate_options("tight", 12600)["bufsize_kbits"], 3150)

    def test_invalid_logged_once_and_inert(self):
        lines = []
        rc = erc.EncoderRc("loose", log=lines.append, environ={})
        cmd = ["-b:v", "5000k", "-maxrate", "5000k", "-bufsize", "5000k"]
        self.assertIs(rc.apply(cmd, 5000), cmd)
        rc.apply(cmd, 5000)
        self.assertEqual(len(lines), 1)
        self.assertIn("ignored", lines[0])

    def test_apply_to_without_rate_options_is_unchanged(self):
        self.assertEqual(erc.apply_to(["-c:v", "x"], "tight", 5000), ["-c:v", "x"])

    def test_bufsize_override_is_replaced_and_said_once(self):
        lines = []
        rc = erc.EncoderRc("tight", log=lines.append, environ={erc.BUFSIZE_OVERRIDE_ENV: "300"})
        out = rc.apply(["-b:v", "5000k", "-maxrate", "5000k", "-bufsize", "300k"], 5000)
        self.assertEqual(out[out.index("-bufsize") + 1], "1250k")
        self.assertTrue(any(erc.BUFSIZE_OVERRIDE_ENV in l for l in lines))


class TestBuilder(unittest.TestCase):
    def test_absent_is_none(self):
        self.assertIsNone(ns.ENCODER_RC)

    def test_absent_rate_args(self):
        self.assertEqual(rate(build()), ["-b:v", "7000k", "-maxrate", "7000k", "-bufsize", "7000k",
                                         "-max_frame_size", "90000"])

    def test_profiles_at_each_target(self):
        for target in (4000, 5000, 5500, 6000, 7000):
            base = build(target)
            for profile, mode, mx in (("tight", "CBR", 1.0), ("headroom", "VBR", 1.10)):
                with Flag(profile):
                    out = build(target)
                self.assertEqual(rate(out), ["-b:v", f"{target}k", "-maxrate", f"{round(target * mx)}k", "-bufsize",
                                             f"{round(target * 0.25)}k", "-rc_mode", mode, "-max_frame_size", "90000"])
                # everything else unchanged: drop the rate block from both
                strip = lambda a: a[:a.index("-b:v")] + a[a.index("-max_frame_size"):]
                self.assertEqual(strip(out), strip(base))

    def test_invalid_profile_is_todays_command(self):
        with Flag("loose"):
            self.assertEqual(build(5000), build_absent(5000))

    def test_the_start_carries_the_profile(self):
        with Flag("tight"):
            out = stub.run_start(ns, LAN)
        self.assertEqual(rate(out["argv"])[:8], ["-b:v", "7000k", "-maxrate", "7000k", "-bufsize", "1750k",
                                                 "-rc_mode", "CBR"])


def build_absent(target):
    saved = ns.ENCODER_RC
    ns.ENCODER_RC = None
    try:
        return build(target)
    finally:
        ns.ENCODER_RC = saved


class TestActuator(unittest.TestCase):
    def test_a_live_rung_change_follows(self):
        for target in (5000, 5500, 6000):
            with Flag("headroom"):
                live = actuator(target)
                built = build(target)
            self.assertEqual(rate(live), rate(built), target)
            self.assertIn("-rc_mode", live)
            self.assertEqual(live[live.index("-maxrate") + 1], f"{round(target * 1.1)}k")

    def test_absent_actuator_is_todays(self):
        live = actuator(5000)
        self.assertEqual(rate(live), ["-b:v", "5000k", "-maxrate", "5000k", "-bufsize", "5000k",
                                      "-max_frame_size", "90000"])
        self.assertNotIn("-rc_mode", live)

    def test_the_sized_rung_follows(self):
        with Flag("tight"):
            live = actuator(12600, sized=True)
        self.assertEqual(rate(live)[:8], ["-b:v", "12600k", "-maxrate", "12600k", "-bufsize", "3150k",
                                          "-rc_mode", "CBR"])


class TestGuardedImport(unittest.TestCase):
    def test_import_only_under_the_flag(self):
        tree = ast.parse((ROOT / "companion" / "native_stream.py").read_text())
        top = [n for n in tree.body if isinstance(n, ast.Import) and any(a.name == "encoder_rc" for a in n.names)]
        guarded = [ast.unparse(n.test) for n in tree.body if isinstance(n, ast.If)
                   and any(isinstance(s, ast.Import) and any(a.name == "encoder_rc" for a in s.names) for s in n.body)]
        self.assertEqual(top, [])
        self.assertEqual(len(guarded), 1)
        self.assertIn("PRIVYHUB_ENCODER_RC", guarded[0])

    def test_one_hook_in_the_builder(self):
        tree = ast.parse((ROOT / "companion" / "native_stream.py").read_text())
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_build_linux_ffmpeg_command")
        ifs = [n for n in ast.walk(fn) if isinstance(n, ast.If) and "ENCODER_RC" in ast.unparse(n.test)]
        self.assertEqual(len(ifs), 1)
        users = [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "ENCODER_RC"]
        self.assertEqual(len(users), 4)      # the global, its assignment, the test, the call

    def test_child_interpreter(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        code = ("import sys; sys.path.insert(0, 'companion'); import native_stream as ns; "
                "print(ns.ENCODER_RC is None, 'encoder_rc' in sys.modules)")
        out = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=env, capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "True False", out.stderr)
        env["PRIVYHUB_ENCODER_RC"] = "headroom"
        code = ("import sys; sys.path.insert(0, 'companion'); import native_stream as ns, encoder_rc as e; "
                "print(ns.ENCODER_RC is e._SHARED, ns.ENCODER_RC.profile)")
        out = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=env, capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "True headroom", out.stderr)


if __name__ == "__main__":
    unittest.main()
