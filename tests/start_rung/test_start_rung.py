#!/usr/bin/env python3
"""G8-S2: the start rung.

    python3 -m unittest discover -s tests/start_rung -v

No stream, no companion. This process carries no flag, so both hooks' globals are
None; `Flags` sets them (and G5-S3 / G5-S4's, when a case needs them) and restores
them. The stream start runs the real `_start_linux_locked` on a stubbed manager
(`stub_manager.py`): nothing spawned, no socket. Addresses are built from integers.
"""

from __future__ import annotations

import ast
import ipaddress
import json
import os
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(HERE))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402
import native_stream as ns  # noqa: E402
import remote_cap as rc  # noqa: E402
import remote_ladder as rl  # noqa: E402
import start_rung as sr  # noqa: E402
import stub_manager as stub  # noqa: E402
import test_c3_f1_recovery_restart as f1  # noqa: E402
from diagnostics import c3_linux_actuator_probe as probe  # noqa: E402

OVERLAY = str(rl.OVERLAY_NETWORKS[0][77])
LAN = str(ipaddress.ip_address(0xC0A80117))


class Flags:
    def __init__(self, spec: str | None, remote_ladder: bool = False, cap: str | None = None):
        self.logs: list[str] = []
        self.s = sr.from_environ_fresh({sr.FLAG_ENV: spec} if spec is not None else {}, log=self.logs.append)
        self.r = rl.RemoteLadder() if remote_ladder else None
        self.c = rc.from_environ({rc.FLAG_ENV: cap}, self.r) if cap is not None else None

    def __enter__(self):
        self.saved = (ns.START_RUNG, live.START_RUNG, live.REMOTE_LADDER, live.REMOTE_CAP, probe.REMOTE_LADDER)
        ns.START_RUNG = live.START_RUNG = self.s
        live.REMOTE_LADDER = probe.REMOTE_LADDER = self.r
        live.REMOTE_CAP = self.c
        return self

    def __exit__(self, *exc):
        ns.START_RUNG, live.START_RUNG, live.REMOTE_LADDER, live.REMOTE_CAP, probe.REMOTE_LADDER = self.saved


def rate(argv):
    return tuple(argv[argv.index(f) + 1] for f in ("-b:v", "-maxrate", "-bufsize"))


# ------------------------------------------------------------------ the flag ---
class TheFlag(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(sr.parse("floor"), ("floor", "floor"))
        self.assertEqual(sr.parse(" CAP "), ("cap", "cap"))
        self.assertEqual(sr.parse("5000"), ("kbps", 5000))
        for v in ("", "low", "-4000", "4000.0", "5k"):
            self.assertEqual(sr.parse(v)[0], "invalid", v)
        self.assertIsNone(sr.shared_from_environ({}))
        self.assertIsNone(sr.shared_from_environ({sr.FLAG_ENV: "  "}))

    def test_this_process_has_no_flag(self):
        self.assertIsNone(ns.START_RUNG)
        self.assertIsNone(live.START_RUNG)

    def test_imports_only_under_the_flag(self):
        for rel in ("companion/native_stream.py", "companion/adaptive_bitrate_live.py"):
            tree = ast.parse((ROOT / rel).read_text())
            top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
            self.assertFalse(any("start_rung" in ast.unparse(n) for n in top), rel)
            guarded = [n for n in tree.body if isinstance(n, ast.If) and "start_rung" in ast.unparse(n)]
            self.assertEqual(len(guarded), 1, rel)
            self.assertIn("PRIVYHUB_START_RUNG", ast.unparse(guarded[0].test), rel)

    def test_real_environment_one_instance(self):
        code = ("import sys; sys.path.insert(0, %r)\nimport native_stream as n, adaptive_bitrate_live as l\n"
                "print(n.START_RUNG is not None and n.START_RUNG is l.START_RUNG, 'start_rung' in sys.modules)\n"
                % str(ROOT / "companion"))
        base = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        base["PYTHONDONTWRITEBYTECODE"] = "1"
        run = lambda **e: subprocess.run([sys.executable, "-c", code], env=dict(base, **e), capture_output=True,
                                         text=True, timeout=60).stdout.strip()
        self.assertEqual(run(PRIVYHUB_START_RUNG="floor"), "True True")
        self.assertEqual(run(), "False False")


# ------------------------------------------------------------- the choice ---
class TheChoice(unittest.TestCase):
    def choose(self, spec, target, **kw):
        with Flags(spec, **kw) as f:
            return f.s.choose(target), f.logs

    def test_floor_lan_and_remote(self):
        self.assertEqual(self.choose("floor", LAN)[0]["kbps"], 5000)
        self.assertEqual(self.choose("floor", OVERLAY)[0]["kbps"], 5000)              # G5-S3 off: the LAN list
        rec, _ = self.choose("floor", OVERLAY, remote_ladder=True)
        self.assertEqual((rec["kbps"], rec["source"], rec["active_list"], rec["path_class"]),
                         (4000, "floor", [4000, 5000, 5500, 6000, 7000], "remote"))
        rec, _ = self.choose("floor", LAN, remote_ladder=True)                       # G5-S3 on, a LAN start
        self.assertEqual((rec["kbps"], rec["path_class"]), (5000, "lan"))

    def test_cap_with_and_without_g5_s4(self):
        rec, logs = self.choose("cap", OVERLAY, remote_ladder=True, cap="5000")
        self.assertEqual((rec["kbps"], rec["source"]), (5000, "cap"))
        rec, logs = self.choose("cap", OVERLAY, remote_ladder=True)                  # no cap set
        self.assertEqual((rec["kbps"], rec["source"]), (4000, "cap→floor"))
        self.assertEqual(len(logs), 1)
        rec, _ = self.choose("cap", LAN, remote_ladder=True, cap="4000")             # G5-S4 is remote-only
        self.assertEqual((rec["kbps"], rec["source"]), (5000, "cap→floor"))
        rec, _ = self.choose("cap", OVERLAY, remote_ladder=True, cap="4500")         # an invalid cap is inactive
        self.assertEqual((rec["kbps"], rec["source"]), (4000, "cap→floor"))

    def test_a_value_in_and_out_of_the_list(self):
        self.assertEqual(self.choose("5500", LAN)[0]["kbps"], 5500)
        rec, logs = self.choose("4000", LAN)                                         # 4000 is not a LAN rung
        self.assertEqual((rec["kbps"], rec["source"]), (5000, "value→floor"))
        self.assertEqual(len(logs), 1)
        self.assertEqual(self.choose("4000", OVERLAY, remote_ladder=True)[0]["kbps"], 4000)
        self.assertEqual(self.choose("3000", OVERLAY, remote_ladder=True)[0]["kbps"], 4000)   # never below
        self.assertEqual(self.choose("12600", LAN)[0]["kbps"], 5000)
        self.assertEqual(self.choose("7000", LAN)[0]["source"], "value")

    def test_invalid_ignored_logged_once(self):
        with Flags("low") as f:
            a, b = f.s.choose(LAN), f.s.choose(LAN)
            self.assertEqual((a["kbps"], a["source"], b["kbps"]), (7000, "invalid→today", 7000))
            self.assertEqual(len(f.logs), 1)
            self.assertEqual(f.s.encoder_kwargs(LAN), {})

    def test_no_address_kept(self):
        with Flags("floor", remote_ladder=True) as f:
            f.s.choose(OVERLAY)
            blob = repr(vars(f.s))
        self.assertNotIn(OVERLAY, blob)


# --------------------------------------------------------------- the start ---
class TheStart(unittest.TestCase):
    def test_absent_is_today(self):
        out = stub.run_start(ns, LAN)
        self.assertEqual(rate(out["argv"]), ("7000k", "7000k", "7000k"))
        self.assertEqual(out["active_bitrate_kbps"], 7000)

    def test_floor_starts_at_5000_and_the_status_says_so(self):
        with Flags("floor"):
            out = stub.run_start(ns, LAN)
        self.assertEqual(rate(out["argv"]), ("5000k", "5000k", "5000k"))
        self.assertEqual((out["active_bitrate_kbps"], out["payload"]["bitrate_kbps"]), (5000, 5000))

    def test_7000_chosen_is_todays_argv(self):
        base = stub.run_start(ns, LAN)["argv"]
        for spec in ("7000", "nonsense"):
            with Flags(spec):
                self.assertEqual(stub.run_start(ns, LAN)["argv"], base, spec)

    def test_the_start_argv_is_the_ladders_transition_argv(self):
        with Flags("floor", remote_ladder=True) as f:
            f.r.set_routing_evidence(rl.EVIDENCE_OVERLAY)
            for spec, target, k in (("floor", OVERLAY, 4000), ("5000", LAN, 5000), ("6000", LAN, 6000)):
                f.s = sr.from_environ_fresh({sr.FLAG_ENV: spec}, log=lambda *_: None)
                ns.START_RUNG = f.s
                start = stub.run_start(ns, target)["argv"]
                m = f1.fake_manager(7000)
                clock = f1.Clock()
                got = []
                probe.run_c3_linux_validated_bitrate_transition(
                    m, target_bitrate_kbps=k, popen_factory=lambda a, **kw: got.append(a) or f1.FakeProc(a),
                    monotonic=clock, sleep=lambda s: None, perf_counter_ns=lambda: int(clock() * 1e9))
                norm = lambda a: [x for x in a if "4242" not in x and not x.startswith("rtp://")]
                self.assertEqual(rate(start), rate(got[0]), spec)
                self.assertEqual(norm(start)[norm(start).index("-c:v"):], norm(got[0])[norm(got[0]).index("-c:v"):],
                                 spec)

    def test_a_recovery_full_start_uses_the_rung_too(self):
        with Flags("floor"):
            first = stub.run_start(ns, LAN)
            again = stub.run_start(ns, LAN)            # the same start() a recovery full start calls
        self.assertEqual((first["active_bitrate_kbps"], again["active_bitrate_kbps"]), (5000, 5000))


# ---------------------------------------------------------- the ladder row ---
class _SyncThread:
    def __init__(self, target, args=(), **kw):
        self._t, self._a = target, args

    def start(self):
        self._t(*self._a)


def tel(el, fps=59.9, lost=0):
    return {"available": True, "fresh": True, "session_elapsed_ms": el,
            "receiver": {"recent_fps": fps, "waiting_for_idr": False, "lost_packets_delta": lost},
            "decoder": {"queue_depth": 0, "stale_output_drops_delta": 0}, "latency": {"output_gap_ms": 16}, "fec": {}}


class TheRecordAndTheClimb(unittest.TestCase):
    def drive(self, spec, n, target=LAN, remote=False):
        d = tempfile.mkdtemp(prefix="g8_s2_rows_")
        saved = live.threading
        live.threading = types.SimpleNamespace(Thread=_SyncThread, RLock=threading.RLock)
        state = {"kbps": 7000}
        try:
            with Flags(spec, remote_ladder=remote) as f:
                if f.r is not None:
                    f.r.set_routing_evidence(rl.EVIDENCE_OVERLAY if target == OVERLAY else rl.EVIDENCE_NOT_OVERLAY)
                c = live.LiveController(Path(d), environ={})
                c.bind(actuator=lambda k: state.__setitem__("kbps", k) or {"ok": True, "target_bitrate_kbps": k},
                       context=lambda: {"game_active": True, "game_paused": False, "recovery_state": "PLAYING"},
                       serial_lock=None, recovery_state=lambda: "PLAYING")
                if f.s is not None:
                    state["kbps"] = f.s.choose(target)["kbps"]     # the stream started at the rung
                c.session_ended()                                  # native-stream-ready's reset
                for i in range(n):
                    nsd = {"active": True, "profile_id": live.REFERENCE_PROFILE_ID, "profile": {"bitrate_kbps": 7000},
                           "encoder_overrides": {"any_override": False}, "bitrate_kbps": state["kbps"]}
                    c.observe(tel(2000 * (i + 1)), stream_bitrate_kbps=state["kbps"], native_status=nsd)
        finally:
            live.threading = saved
        return [json.loads(x) for x in c.log_path.read_text().splitlines()]

    def test_the_first_sample_row_carries_the_start_rung_once(self):
        rows = self.drive("floor", 5)
        marked = [r for r in rows if "start_rung" in r]
        self.assertEqual(len(marked), 1)
        first_sample = next(r for r in rows if r.get("event") == "sample")
        self.assertIn("start_rung", first_sample)
        self.assertEqual({k: first_sample["start_rung"][k] for k in ("kbps", "source", "active_list")},
                         {"kbps": 5000, "source": "floor", "active_list": [5000, 5500, 6000, 7000]})
        self.assertTrue(any(r.get("event") == "level_sync" and r["to_kbps"] == 5000 for r in rows))

    def test_absent_no_record(self):
        rows = self.drive(None, 5)
        self.assertFalse(any("start_rung" in r for r in rows))

    def test_the_climb_is_the_ladders_own_and_as_the_design_computed(self):
        rows = self.drive("floor", 300)
        ups = [(r["from_kbps"], r["to_kbps"], r["session_elapsed_ms"] // 2000) for r in rows
               if r.get("event") == "transition"]
        self.assertEqual([u[:2] for u in ups], [(5000, 5500), (5500, 6000), (6000, 7000)])
        self.assertEqual([u[2] for u in ups], [90, 183, 276])            # design §3: 90 + 93 + 93 reports
        rows = self.drive("floor", 400, target=OVERLAY, remote=True)
        ups = [(r["from_kbps"], r["to_kbps"], r["session_elapsed_ms"] // 2000) for r in rows
               if r.get("event") == "transition"]
        self.assertEqual([u[:2] for u in ups], [(4000, 5000), (5000, 5500), (5500, 6000), (6000, 7000)])
        self.assertEqual([u[2] for u in ups], [90, 183, 276, 369])


if __name__ == "__main__":
    unittest.main()
