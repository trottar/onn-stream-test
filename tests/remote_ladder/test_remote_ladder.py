#!/usr/bin/env python3
"""G5-S3: the remote ladder -- the session's path class in the ladder's context,
and 720p/4000 on a remote path only.

    python3 -m unittest discover -s tests/remote_ladder -v

No stream, no companion. This process carries no flag, so every module global
is None; a test that needs the flag sets the globals to one `RemoteLadder` and
restores them (`FlagOn`), and one test runs a child interpreter with the real
environment variable. The actuator runs C3-F1's fake manager through the real
encoder-only cycle: nothing is spawned. Addresses are built from integers.
"""

from __future__ import annotations

import ast
import ipaddress
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
sys.path.insert(0, str(ROOT / "tools"))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402
import remote_ladder as rl  # noqa: E402
import wan_adaptation as wa  # noqa: E402
import test_c3_f1_recovery_restart as f1  # noqa: E402
from diagnostics import c3_linux_actuator_probe as probe  # noqa: E402

GUARDS = {"stream_active": True, "game_active": True, "game_not_paused": True, "recovery_playing": True,
          "reference_profile": True, "no_override": True, "actuator_bound": True}
OVERLAY_V4 = str(rl.OVERLAY_NETWORKS[0][77])
OVERLAY_V6 = str(rl.OVERLAY_NETWORKS[1][5])
LAN_V4 = str(ipaddress.ip_address(0xC0A80117))
LOOPBACK = str(ipaddress.ip_address(0x7F000001))

CLEAN = dict(fps=59.9, queue=0, gap=16, lost=0)
MILD = dict(fps=54.0, queue=0, gap=16, lost=80)          # capacity_mild: < 57 on 4/5, >= 50 lost on 3/5
STRICT = dict(fps=45.0, queue=0, gap=16, lost=120)       # capacity: < 50 on all 5


def tel(elapsed, fps=59.9, queue=0, gap=16, lost=0, stale=0, idr=False):
    return {"available": True, "fresh": True, "session_elapsed_ms": elapsed,
            "receiver": {"recent_fps": fps, "waiting_for_idr": idr, "lost_packets_delta": lost},
            "decoder": {"queue_depth": queue, "stale_output_drops_delta": stale},
            "latency": {"output_gap_ms": gap}, "fec": {}}


class FlagOn:
    """The four hooks' globals set to one shared instance, as the flag would."""

    def __init__(self, evidence: str | None = None):
        self.r = rl.RemoteLadder()
        if evidence:
            self.r.set_routing_evidence(evidence)

    def __enter__(self):
        self.saved = (live.REMOTE_LADDER, probe.REMOTE_LADDER, wa.REMOTE_LADDER)
        live.REMOTE_LADDER = probe.REMOTE_LADDER = wa.REMOTE_LADDER = self.r
        return self.r

    def __exit__(self, *exc):
        live.REMOTE_LADDER, probe.REMOTE_LADDER, wa.REMOTE_LADDER = self.saved


def drive(policy, specs, remote=None, adapt=None, start=0, events=None):
    """Feed (spec, n) blocks through the context hook; actuate synchronously."""
    out = [] if events is None else events
    el = start
    for spec, n in specs:
        for _ in range(n):
            el += 2000
            t = tel(el, **spec)
            ctx = {"guards": GUARDS, "clock_ms": el, "stream_kbps": policy.level_kbps}
            if remote is not None:
                remote.apply(policy, ctx)
            evs = adapt.feed(policy, ab._sample(t), ctx, t) if adapt else policy.feed(ab._sample(t), ctx)
            out.extend(evs)
            if policy.pending:
                policy.actuation_done(True, actual_kbps=policy.pending["to_kbps"])
    return out


def levels(events):
    return [e["to_kbps"] for e in events if e.get("event") == "transition"]


# ------------------------------------------------------------------ the flag ---
class Flag(unittest.TestCase):
    def test_flag_exactly_one(self):
        self.assertTrue(rl.flag_on({rl.FLAG_ENV: "1"}))
        for v in (None, "", "0", "true", "yes", "2", "remote"):
            self.assertFalse(rl.flag_on({} if v is None else {rl.FLAG_ENV: v}), v)
        self.assertIsNone(rl.shared_from_environ({}))

    def test_this_process_has_no_flag(self):
        self.assertIsNone(live.REMOTE_LADDER)
        self.assertIsNone(probe.REMOTE_LADDER)
        self.assertIsNone(wa.REMOTE_LADDER)

    def test_imports_only_under_the_flag(self):
        for rel in ("companion/adaptive_bitrate_live.py", "companion/wan_adaptation.py",
                    "companion/diagnostics/c3_linux_actuator_probe.py"):
            tree = ast.parse((ROOT / rel).read_text())
            top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
            self.assertFalse(any("remote_ladder" in ast.unparse(n) for n in top), rel)
            guarded = [n for n in tree.body if isinstance(n, ast.If) and "remote_ladder" in ast.unparse(n)]
            self.assertEqual(len(guarded), 1, rel)
            self.assertIn("PRIVYHUB_REMOTE_LADDER", ast.unparse(guarded[0].test), rel)
        games = (ROOT / "companion" / "plugins" / "games.py").read_text()
        self.assertNotIn("import remote_ladder", games)
        self.assertEqual(games.count("adaptive_bitrate_live.REMOTE_LADDER is not None"), 1)

    def test_one_shared_instance_under_the_real_flag(self):
        code = ("import sys; sys.path.insert(0, %r)\n"
                "import adaptive_bitrate_live as l, wan_adaptation as w\n"
                "from diagnostics import c3_linux_actuator_probe as p\n"
                "print(l.REMOTE_LADDER is not None and l.REMOTE_LADDER is w.REMOTE_LADDER is p.REMOTE_LADDER)\n"
                % str(ROOT / "companion"))
        env = dict(os.environ, PRIVYHUB_REMOTE_LADDER="1", PYTHONDONTWRITEBYTECODE="1")
        out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(out.stdout.strip(), "True", out.stderr)
        env["PRIVYHUB_REMOTE_LADDER"] = "0"
        code0 = code.replace("print(l.REMOTE_LADDER is not None and l.REMOTE_LADDER is w.REMOTE_LADDER "
                             "is p.REMOTE_LADDER)",
                             "print(l.REMOTE_LADDER is None and w.REMOTE_LADDER is None and "
                             "p.REMOTE_LADDER is None and 'remote_ladder' not in sys.modules)")
        self.assertNotEqual(code0, code)
        out = subprocess.run([sys.executable, "-c", code0], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(out.stdout.strip(), "True", out.stderr)


# ----------------------------------------------------------------- the class ---
class TheClass(unittest.TestCase):
    def test_overlay_block_is_g3s(self):
        import session_identity as si    # read only
        self.assertEqual(rl.OVERLAY_NETWORKS, si.OVERLAY_NETWORKS)

    def test_routing_evidence_is_g3s_overlay_test(self):
        import session_identity as si    # read only: G3's classifier, no LAN table needed for overlay
        c = si.RoutingClassifier(lan_reader=lambda: [])
        for addr in (OVERLAY_V4, OVERLAY_V6, "::ffff:" + OVERLAY_V4, LAN_V4, LOOPBACK, "not-an-address", ""):
            want = rl.EVIDENCE_OVERLAY if c.classify(addr) == si.ROUTING_OVERLAY else rl.EVIDENCE_NOT_OVERLAY
            self.assertEqual(rl.routing_evidence_of(addr), want, addr)
        self.assertEqual(rl.routing_evidence_of(OVERLAY_V4), rl.EVIDENCE_OVERLAY)
        self.assertEqual(rl.routing_evidence_of(LAN_V4), rl.EVIDENCE_NOT_OVERLAY)

    def test_set_at_every_stream_start_and_no_address_kept(self):
        r = rl.RemoteLadder()
        self.assertEqual(r.path_class, rl.PATH_LAN)                  # G5-S2's default
        self.assertEqual(r.note_stream_start(OVERLAY_V4), rl.PATH_REMOTE)
        self.assertEqual(r.note_stream_start(LAN_V4), rl.PATH_LAN)    # a re-setup over the LAN
        self.assertEqual(r.note_stream_start(OVERLAY_V6), rl.PATH_REMOTE)
        self.assertEqual(r.stream_starts, 3)
        blob = repr(vars(r)) + repr(r.status())
        for addr in (OVERLAY_V4, OVERLAY_V6, LAN_V4):
            self.assertNotIn(addr, blob)
        self.assertIsNone(r.note_stream_start(object.__new__(_Boom)))  # never raises

    def test_games_plugin_hook(self):
        g = load_games_plugin()
        calls = []

        class Emu:
            def status(self):
                return {"active": True, "paused": True, "pid": 1}

        p = object.__new__(g.GamesPlugin)
        p._emulator = Emu()
        p._recovery = types.SimpleNamespace(note_stream_start=lambda: calls.append("recovery"))
        p._native_stream = types.SimpleNamespace(start=lambda **kw: calls.append("start") or {"ok": True})
        p._diagnostic_heartbeat_interval_ms = lambda: 2000
        p.handle_post_request("native-stream-start", "port=48100", OVERLAY_V4)    # flag absent: nothing
        with FlagOn() as r:
            p.handle_post_request("native-stream-start", "port=48100", OVERLAY_V4)
            self.assertEqual((r.path_class, r.routing_evidence), (rl.PATH_REMOTE, rl.EVIDENCE_OVERLAY))
            p.handle_post_request("native-stream-start", "port=48100", LAN_V4)
            self.assertEqual(r.path_class, rl.PATH_LAN)
            self.assertEqual(r.stream_starts, 2)
        self.assertEqual(calls.count("start"), 3)


def load_games_plugin():
    """`plugins/games.py` alone: importing the `plugins` package would construct every
    plugin (its `__init__` builds PLUGINS), and GamesPlugin() writes the startup
    reconcile's status file under logs/. This loads the module and constructs nothing."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("g5_s3_games_plugin", ROOT / "companion" / "plugins" / "games.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Boom:
    def __str__(self):
        raise RuntimeError("boom")


# --------------------------------------------------------------- the context ---
class TheContext(unittest.TestCase):
    def ctl(self, **kw):
        d = tempfile.mkdtemp(prefix="g5_s3_test_")
        return live.LiveController(Path(d), environ=kw.get("environ", {}))

    def test_without_the_flag_as_today(self):
        c = self.ctl()
        ctx = c._ctx({"bitrate_kbps": 7000})
        self.assertNotIn("path_class", ctx)
        self.assertEqual(set(ctx), {"stream_kbps", "guards", "clock_ms"})
        self.assertEqual(c._policy.ladder, live.LADDER_KBPS)

    def test_with_the_flag_by_class(self):
        with FlagOn() as r:
            c = self.ctl()
            self.assertEqual(c._ctx({})["path_class"], "lan")
            self.assertEqual(c._policy.ladder, (5000, 5500, 6000, 7000))
            r.set_routing_evidence(rl.EVIDENCE_OVERLAY)
            self.assertEqual(c._ctx({})["path_class"], "remote")
            self.assertEqual(c._policy.ladder, (4000, 5000, 5500, 6000, 7000))
            self.assertEqual(c.status()["validated_ladder_kbps"], [4000, 5000, 5500, 6000, 7000])
            r.set_routing_evidence(rl.EVIDENCE_NOT_OVERLAY)
            self.assertEqual(c._ctx({})["path_class"], "lan")
            self.assertEqual(c._policy.ladder, (5000, 5500, 6000, 7000))

    def test_with_the_1080p_rung(self):
        with FlagOn(rl.EVIDENCE_OVERLAY):
            c = self.ctl(environ={live.TOP_ENV: live.TOP_1080P})
            c._ctx({})
            self.assertEqual(c._policy.ladder, (4000,) + live.LADDER_WITH_RUNG_KBPS)

    def test_wan_rules_read_the_class(self):
        with FlagOn(rl.EVIDENCE_OVERLAY):
            c = self.ctl()
            self.assertEqual(wa.path_class(c._ctx({})), wa.PATH_REMOTE)    # G5-S2 finding 2, closed
        self.assertEqual(wa.path_class(self.ctl()._ctx({})), wa.PATH_LAN)


# ---------------------------------------------------------------- the policy ---
class ThePolicy(unittest.TestCase):
    def test_remote_steps_down_to_4000_and_no_further(self):
        r = rl.RemoteLadder()
        r.set_routing_evidence(rl.EVIDENCE_OVERLAY)
        p = live.LivePolicy()
        evs = drive(p, [(CLEAN, 40), (MILD, 600)], remote=r)
        self.assertEqual(levels(evs), [6000, 5500, 5000, 4000])
        self.assertEqual(p.level_kbps, 4000)
        at4000 = [e for e in evs if e.get("event") == "refused" and e.get("from_kbps") == 4000]
        self.assertEqual({e["reason"] for e in at4000}, {"hold_down", "at_floor"})   # the hold-down first
        self.assertTrue(all(e["to_kbps"] == 4000 for e in at4000 if e["reason"] == "at_floor"))
        self.assertGreaterEqual(min(e["to_kbps"] for e in evs if e.get("event") == "transition"), 4000)

    def test_lan_never_reaches_4000(self):
        r = rl.RemoteLadder()                     # lan
        for remote in (r, None):                  # with the flag on the LAN, and without the flag
            p = live.LivePolicy()
            evs = drive(p, [(CLEAN, 40), (MILD, 600), (STRICT, 200)], remote=remote)
            self.assertEqual(levels(evs), [6000, 5500, 5000])
            self.assertEqual(p.level_kbps, 5000)
            self.assertNotIn(4000, [e.get("to_kbps") for e in evs])

    def test_strict_fallback_still_names_5000(self):
        r = rl.RemoteLadder()
        r.set_routing_evidence(rl.EVIDENCE_OVERLAY)
        p = live.LivePolicy()
        evs = drive(p, [(CLEAN, 40), (STRICT, 200)], remote=r)
        self.assertEqual(levels(evs), [5000])                  # TARGET_KBPS unchanged
        self.assertTrue(any(e.get("event") == "refused" and e.get("reason") == "at_floor" for e in evs))

    def test_increase_from_4000_is_5000(self):
        r = rl.RemoteLadder()
        r.set_routing_evidence(rl.EVIDENCE_OVERLAY)
        p = live.LivePolicy()
        evs = drive(p, [(CLEAN, 40), (MILD, 600), (CLEAN, 200)], remote=r)
        ups = [(e["from_kbps"], e["to_kbps"]) for e in evs if e.get("event") == "transition" and e["direction"] == "up"]
        self.assertEqual(ups[0], (4000, 5000))


# -------------------------------------------------------------- the actuator ---
class TheActuator(unittest.TestCase):
    def cycle(self, m, fn, **kw):
        spawned = []

        def popen(argv, **k):
            p = f1.FakeProc(argv)
            spawned.append(p)
            return p
        clock = f1.Clock()
        out = fn(m, popen_factory=popen, monotonic=clock, sleep=lambda s: None,
                 perf_counter_ns=lambda: int(clock() * 1e9), **kw)
        return out, spawned[0].argv

    def rate(self, argv):
        return tuple(argv[argv.index(f) + 1] for f in ("-b:v", "-maxrate", "-bufsize"))

    def test_remote_4000_transition_recovery_and_back(self):
        with FlagOn(rl.EVIDENCE_OVERLAY):
            m = f1.fake_manager(5000)
            out, argv = self.cycle(m, probe.run_c3_linux_validated_bitrate_transition, target_bitrate_kbps=4000)
            self.assertTrue(out["ok"])
            self.assertEqual(out["schema"], probe.BIDIRECTIONAL_SCHEMA)
            self.assertEqual(self.rate(argv), ("4000k", "4000k", "4000k"))
            self.assertEqual(m._active_bitrate_kbps, 4000)
            out, argv = self.cycle(m, probe.run_c3_linux_recovery_restart)        # C3-F1 at 4000
            self.assertTrue(out["ok"])
            self.assertEqual((self.rate(argv)[0], m._active_bitrate_kbps), ("4000k", 4000))
            out, argv = self.cycle(m, probe.run_c3_linux_validated_bitrate_transition, target_bitrate_kbps=5000)
            self.assertEqual((self.rate(argv)[0], m._active_bitrate_kbps), ("5000k", 5000))

    def test_4000_argv_is_5000s_but_the_rate(self):
        with FlagOn(rl.EVIDENCE_OVERLAY):
            _, a4 = self.cycle(f1.fake_manager(7000), probe.run_c3_linux_validated_bitrate_transition,
                               target_bitrate_kbps=4000)
        _, a5 = self.cycle(f1.fake_manager(7000), probe.run_c3_linux_validated_bitrate_transition,
                           target_bitrate_kbps=5000)
        self.assertEqual([x.replace("4000k", "5000k") for x in a4], a5)

    def test_refused_on_the_lan_and_without_the_flag(self):
        for ctx in (FlagOn(), FlagOn(rl.EVIDENCE_NOT_OVERLAY), None):
            with (ctx or _Nothing()):
                m = f1.fake_manager(5000)
                with self.assertRaisesRegex(RuntimeError, "unsupported_validated_bitrate"):
                    self.cycle(m, probe.run_c3_linux_validated_bitrate_transition, target_bitrate_kbps=4000)
                self.assertEqual(m._active_bitrate_kbps, 5000)
                m4 = f1.fake_manager(4000)                     # a stream left at 4000 is not "validated" here
                with self.assertRaises(RuntimeError):
                    self.cycle(m4, probe.run_c3_linux_recovery_restart)
                with self.assertRaisesRegex(RuntimeError, "validated_transition_requires_validated_start"):
                    self.cycle(m4, probe.run_c3_linux_validated_bitrate_transition, target_bitrate_kbps=5000)

    def test_below_4000_refused_everywhere(self):
        for ctx in (FlagOn(rl.EVIDENCE_OVERLAY), FlagOn(), None):
            with (ctx or _Nothing()):
                for fn, kw in ((probe.run_c3_linux_validated_bitrate_transition, {"target_bitrate_kbps": 3000}),
                               (probe.run_c3_linux_level_transition, {"target_bitrate_kbps": 3000}),
                               (probe.run_c3_linux_validated_bitrate_transition, {"target_bitrate_kbps": 3500})):
                    with self.assertRaisesRegex(RuntimeError, "unsupported_validated_bitrate"):
                        self.cycle(f1.fake_manager(5000), fn, **kw)
                with self.assertRaises(RuntimeError):
                    self.cycle(f1.fake_manager(3000), probe.run_c3_linux_recovery_restart)

    def test_manager_routes_4000_to_the_validated_transition(self):
        import native_stream as ns
        seen = []
        saved = probe.run_c3_linux_validated_bitrate_transition
        probe.run_c3_linux_validated_bitrate_transition = lambda m, **kw: seen.append(kw) or {"ok": True}
        try:
            m = f1.fake_manager(5000)
            self.assertTrue(ns.NativeStreamManager.adaptive_level_transition(m, 4000)["ok"])
        finally:
            probe.run_c3_linux_validated_bitrate_transition = saved
        self.assertEqual(seen, [{"target_bitrate_kbps": 4000}])


class _Nothing:
    def __enter__(self):
        return None

    def __exit__(self, *exc):
        return False


# ------------------------------------------------------- G5-S2's floor_4000 ---
class TheFloor(unittest.TestCase):
    def run_floor(self, evidence=None, flag=True):
        """7000 -> 5000 by the strict trigger, then capacity-limited at 5000 for 200 reports."""
        p = live.LivePolicy()
        adapt = wa.WanAdaptation()
        if flag:
            with FlagOn(evidence) as r:
                evs = drive(p, [(CLEAN, 40), (STRICT, 260)], remote=r, adapt=adapt)
                return p, evs
        ctx_path = {"path_class": "remote"} if evidence == rl.EVIDENCE_OVERLAY else {}
        out, el = [], 0
        for spec, n in [(CLEAN, 40), (STRICT, 260)]:
            for _ in range(n):
                el += 2000
                t = tel(el, **spec)
                ctx = {"guards": GUARDS, "clock_ms": el, "stream_kbps": p.level_kbps, **ctx_path}
                out.extend(adapt.feed(p, ab._sample(t), ctx, t))
                if p.pending:
                    p.actuation_done(True, actual_kbps=p.pending["to_kbps"])
        return p, out

    def test_without_the_flag_recorded_only(self):
        p, evs = self.run_floor(rl.EVIDENCE_OVERLAY, flag=False)      # remote read from the context
        floor = [e for e in evs if e.get("suggestion") == "floor_4000"]
        self.assertTrue(floor)
        self.assertTrue(all(e["ladder_result"] in ("none",) or e["ladder_result"].startswith("refused")
                            for e in floor))
        self.assertEqual(p.level_kbps, 5000)

    def test_with_the_flag_on_remote_actuated_through_the_gates(self):
        p, evs = self.run_floor(rl.EVIDENCE_OVERLAY)
        tr = [e for e in evs if e.get("event") == "transition" and e["to_kbps"] == 4000]
        self.assertEqual(len(tr), 1)
        self.assertEqual((tr[0]["from_kbps"], tr[0]["reason"], tr[0]["measurements"]["wan_rule"]),
                         (5000, "wan_rules", "R3.2"))
        self.assertEqual(p.level_kbps, 4000)
        self.assertGreaterEqual(min(levels(evs)), 4000)
        rows = [e for e in evs if e.get("suggestion") == "floor_4000"]
        self.assertTrue(any(e["ladder_result"] == "transition" for e in rows))

    def test_with_the_flag_on_the_lan_no_floor(self):
        p, evs = self.run_floor()
        self.assertFalse([e for e in evs if e.get("suggestion") == "floor_4000"])
        self.assertEqual(p.level_kbps, 5000)


# ------------------------------------------------------------------ the rows ---
class _SyncThread:
    def __init__(self, target, args=(), **kw):
        self._t, self._a = target, args

    def start(self):
        self._t(*self._a)


class TheRows(unittest.TestCase):
    def run_controller(self, evidence=None, flag=True):
        d = tempfile.mkdtemp(prefix="g5_s3_rows_")
        saved_threading = live.threading
        live.threading = types.SimpleNamespace(Thread=_SyncThread, RLock=threading.RLock)
        state = {"kbps": 7000}

        def actuator(k):
            state["kbps"] = k
            return {"ok": True, "target_bitrate_kbps": k}
        try:
            with (FlagOn(evidence) if flag else _Nothing()):
                c = live.LiveController(Path(d), environ={})
                c.bind(actuator=actuator,
                       context=lambda: {"game_active": True, "game_paused": False, "recovery_state": "PLAYING"},
                       serial_lock=None, recovery_state=lambda: "PLAYING")
                el = 0
                for spec, n in [(CLEAN, 40), (MILD, 600)]:
                    for _ in range(n):
                        el += 2000
                        ns = {"active": True, "profile_id": live.REFERENCE_PROFILE_ID,
                              "profile": {"bitrate_kbps": 7000}, "encoder_overrides": {"any_override": False},
                              "bitrate_kbps": state["kbps"]}
                        c.observe(tel(el, **spec), stream_bitrate_kbps=state["kbps"], native_status=ns)
        finally:
            live.threading = saved_threading
        import json
        return [json.loads(x) for x in c.log_path.read_text().splitlines()]

    def test_every_row_carries_the_class_and_4000_is_labelled(self):
        rows = self.run_controller(rl.EVIDENCE_OVERLAY)
        self.assertTrue(all(r.get("path_class") == "remote" for r in rows))
        tr = [r for r in rows if r.get("event") == "transition" and r.get("to_kbps") == 4000]
        done = [r for r in rows if r.get("event") == "transition_done" and r.get("to_kbps") == 4000]
        self.assertEqual((len(tr), len(done)), (1, 1))
        self.assertTrue(tr[0]["remote_rung"] and done[0]["remote_rung"])
        self.assertEqual(tr[0]["trigger"], "capacity_mild")
        self.assertEqual(done[0]["decision"]["trigger"], "capacity_mild")
        self.assertEqual(done[0]["decision_sequence"], tr[0]["decision_sequence"])
        self.assertFalse([r for r in rows if r.get("remote_rung") and r.get("event") not in
                          ("transition", "transition_done", "refused")])

    def test_lan_rows_and_no_flag_rows(self):
        lan = self.run_controller()
        self.assertTrue(all(r.get("path_class") == "lan" for r in lan))
        self.assertFalse(any(r.get("remote_rung") for r in lan))
        off = self.run_controller(flag=False)
        self.assertFalse(any("path_class" in r or "remote_rung" in r or "decision" in r for r in off))
        strip = lambda rs: [{k: v for k, v in r.items() if k not in ("at_utc", "actuation_ms", "path_class",
                                                                        "decision")} for r in rs]
        self.assertEqual(strip(lan), strip(off))      # on the LAN the flag adds the class and the decision copy
        self.assertTrue(any("decision" in r for r in lan if r.get("event") == "transition_done"))


if __name__ == "__main__":
    unittest.main()
