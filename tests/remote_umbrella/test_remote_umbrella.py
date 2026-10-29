#!/usr/bin/env python3
"""B28: `PRIVYHUB_REMOTE=1` -- the four WAN lines, each acting only on a remote-class session; the LAN as today.

    python3 -m unittest discover -s tests/remote_umbrella -v

No stream, no companion. This process carries no flag, so every hook's global is None (today). The umbrella is built
with a fake path read (the provider's path) and a fake service module; G3's overlay test is the real one, on addresses
built from integers. The stream start runs the real `_start_linux_locked` on G8-S2's stubbed manager; the ladder rows
come from a real `LiveController` on a temp root (G8-S2's drive, synchronous actuations).
"""

from __future__ import annotations

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
sys.path.insert(0, str(ROOT / "tests" / "start_rung"))

import adaptive_bitrate_live as live  # noqa: E402
import native_stream as ns  # noqa: E402
import remote_ladder as rl  # noqa: E402
import remote_umbrella as ru  # noqa: E402
import stub_manager as stub  # noqa: E402
from diagnostics import c3_linux_actuator_probe as probe  # noqa: E402

OVERLAY = str(rl.OVERLAY_NETWORKS[0][77])
LAN = str(ipaddress.ip_address(0xC0A80117))
GLOBALS = ((ns, "START_RUNG"), (live, "START_RUNG"), (live, "REMOTE_LADDER"), (live, "REMOTE_CAP"),
           (probe, "REMOTE_LADDER"))


class Rec:
    def __init__(self):
        self.rows = []

    def _log(self, event, **kw):
        self.rows.append(dict(kw, event=event))


class FakeController:
    def __init__(self):
        self.calls = 0

    def status(self):
        self.calls += 1
        return {"ok": True}


def fake_service(root):
    svc = types.ModuleType("b28_fake_service")
    svc.CONTROLLER = FakeController()
    svc.STREAM_TELEMETRY_STORE = object()
    svc.PROJECT_ROOT = Path(root)
    svc.WAN_TELEMETRY = None
    svc.OVERLAY_STATUS = None
    return svc


class _SyncThread:
    def __init__(self, target, args=(), **kw):
        self._t, self._a = target, args

    def start(self):
        self._t(*self._a)


def tel(el, fps=59.9, lost=0):
    return {"available": True, "fresh": True, "session_elapsed_ms": el,
            "receiver": {"recent_fps": fps, "waiting_for_idr": False, "lost_packets_delta": lost},
            "decoder": {"queue_depth": 0, "stale_output_drops_delta": 0}, "latency": {"output_gap_ms": 16}, "fec": {}}


def rate(argv):
    return tuple(argv[argv.index(f) + 1] for f in ("-b:v", "-maxrate", "-bufsize"))


class Base(unittest.TestCase):
    def setUp(self):
        self.saved = [(m, a, getattr(m, a)) for m, a in GLOBALS]
        for m, a in GLOBALS:
            self.assertIsNone(getattr(m, a), f"{a}: this process must carry no flag")
        self.tmp = tempfile.mkdtemp(prefix="b28_")
        self.svc = fake_service(self.tmp)
        self.rec = Rec()
        self.path = "direct"
        self.saved_thread = live.threading
        live.threading = types.SimpleNamespace(Thread=_SyncThread, RLock=threading.RLock)
        self.state = {"kbps": 7000}
        self.c = live.LiveController(Path(self.tmp), environ={})
        self.c.bind(actuator=lambda k: self.state.__setitem__("kbps", k) or {"ok": True, "target_bitrate_kbps": k},
                    context=lambda: {"game_active": True, "game_paused": False, "recovery_state": "PLAYING"},
                    serial_lock=None, recovery_state=lambda: "PLAYING")

    def tearDown(self):
        live.threading = self.saved_thread
        for m, a, v in self.saved:
            setattr(m, a, v)

    def umbrella(self, environ=None):
        return ru.RemoteUmbrella(self.rec, environ or {}, controller=self.c, live=live, native=ns,
                                 service=lambda: self.svc, probe=lambda: probe,
                                 overlay_path=lambda: self.path, threaded=False)

    def session(self, u, target, n):
        """games.py's order: the umbrella before the start; the spawn's rung; the ladder's class after it; reports."""
        if u is not None:
            u.note_stream_start(target)
        out = stub.run_start(ns, target)                           # the real _start_linux_locked
        self.state["kbps"] = out["active_bitrate_kbps"]
        if live.REMOTE_LADDER is not None:
            live.REMOTE_LADDER.note_stream_start(target)
        self.c.session_ended()
        mark = len(self.rows())
        for i in range(n):
            nsd = {"active": True, "profile_id": live.REFERENCE_PROFILE_ID, "profile": {"bitrate_kbps": 7000},
                   "encoder_overrides": {"any_override": False}, "bitrate_kbps": self.state["kbps"]}
            self.c.observe(tel(2000 * (i + 1)), stream_bitrate_kbps=self.state["kbps"], native_status=nsd)
            if self.svc.WAN_TELEMETRY is not None:                 # the service's report path
                self.svc.WAN_TELEMETRY.observe(tel(2000 * (i + 1)), nsd)
        return out, self.rows()[mark:]

    def rows(self):
        p = self.c.log_path
        return [json.loads(x) for x in p.read_text().splitlines()] if p.is_file() else []

    @staticmethod
    def shape(rows):
        drop = {"at_utc", "clock_ms"}
        return [{k: v for k, v in r.items() if k not in drop} for r in rows]

    def wan_rows(self):
        p = Path(self.tmp) / "logs" / "wan_sessions.jsonl"
        return p.read_text().splitlines() if p.is_file() else []


class TheLan(Base):
    def test_a_lan_session_is_todays_in_every_reader(self):
        today_out, today_rows = self.session(None, LAN, 40)
        u = self.umbrella()
        out, rows = self.session(u, LAN, 40)
        self.assertEqual(rate(out["argv"]), ("7000k", "7000k", "7000k"))
        self.assertEqual(out["argv"], today_out["argv"])
        self.assertEqual(self.shape(rows), self.shape(today_rows))          # the same ladder rows, field for field
        self.assertFalse(any("path_class" in r or "start_rung" in r for r in rows))
        self.assertFalse(any(r.get("event") == "remote_cap_config" for r in self.rows()))
        for m, a in GLOBALS:
            self.assertIsNone(getattr(m, a), a)
        self.assertIsNone(self.svc.WAN_TELEMETRY)
        self.assertEqual(self.wan_rows(), [])
        self.assertEqual(self.svc.CONTROLLER.status(), {"ok": True})         # no wrapper on a LAN-only process
        row = [r for r in self.rec.rows if r["event"] == "remote_config"]
        self.assertEqual(len(row), 1)
        self.assertEqual(row[0]["class"], "lan")
        self.assertEqual({k: v["in_force"] for k, v in row[0]["lines"].items()}, dict.fromkeys(ru.LINES, False))


class TheRemote(Base):
    def test_remote_direct_is_g4_s4s_four(self):
        u = self.umbrella()
        out, rows = self.session(u, OVERLAY, 120)
        self.assertEqual(rate(out["argv"]), ("4000k", "4000k", "4000k"))
        first = next(r for r in rows if r.get("event") == "sample")
        self.assertEqual({k: first["start_rung"][k] for k in ("kbps", "source", "active_list", "path_class")},
                         {"kbps": 4000, "source": "floor", "active_list": [4000, 5000, 5500, 6000, 7000],
                          "path_class": "remote"})
        self.assertTrue(all(r.get("path_class") == "remote" for r in rows))
        self.assertIn(4000, self.c._policy.ladder)
        self.assertEqual(probe.REMOTE_LADDER.actuator_levels(), (4000,))
        caps = [r for r in self.rows() if r.get("event") == "remote_cap_config"]
        self.assertEqual(len(caps), 1)
        self.assertEqual((caps[0]["active"], caps[0]["cap_kbps"]), (True, 7000))
        ups = [(r["from_kbps"], r["to_kbps"]) for r in rows if r.get("event") == "transition"]
        self.assertEqual(ups[:1], [(4000, 5000)])                            # the climb from the floor, as G4-S4
        self.assertIs(self.svc.WAN_TELEMETRY, u.telemetry)
        self.assertIn("wan", self.svc.CONTROLLER.status())
        row = [r for r in self.rec.rows if r["event"] == "remote_config"][-1]
        self.assertEqual(row["class"], "remote-direct")
        self.assertEqual({k: v["in_force"] for k, v in row["lines"].items()}, dict.fromkeys(ru.LINES, True))

    def test_relayed_and_unknown_are_remote_too(self):
        for path, cls in (("relayed", "remote-relayed"), ("no-peer", "remote-unknown"), ("unread", "remote-unknown")):
            self.path = path
            u = self.umbrella()
            self.assertEqual(u.note_stream_start(OVERLAY), "remote-unknown")   # the start: pending, counted remote
            self.assertIs(ns.START_RUNG, u.start)
            self.assertEqual(ns.START_RUNG.encoder_kwargs(OVERLAY), {"bitrate_kbps": 4000, "max_bitrate_kbps": 4000})
            self.assertEqual(self.rec.rows[-1]["class"], cls)
            self.assertEqual(u.cls, cls)

    def test_remote_then_lan_then_remote(self):
        u = self.umbrella()
        self.session(u, OVERLAY, 60)
        self.assertIn(4000, self.c._policy.ladder)
        out, rows = self.session(u, LAN, 40)
        self.assertEqual(rate(out["argv"]), ("7000k", "7000k", "7000k"))
        self.assertNotIn(4000, self.c._policy.ladder)                        # the base ladder again
        self.assertFalse(any("path_class" in r or "start_rung" in r for r in rows))
        self.assertFalse(any(r.get("to_kbps") == 4000 for r in rows))
        for m, a in GLOBALS:
            self.assertIsNone(getattr(m, a), a)
        self.assertIsNone(self.svc.WAN_TELEMETRY)
        self.assertEqual(len(self.wan_rows()), 1)                            # the remote session written at the switch
        self.assertNotIn("wan", self.svc.CONTROLLER.status())               # the wrapper stays, adds nothing
        out, rows = self.session(u, OVERLAY, 10)
        self.assertEqual(rate(out["argv"]), ("4000k", "4000k", "4000k"))
        self.assertEqual(next(r for r in rows if r.get("event") == "sample")["start_rung"]["kbps"], 4000)
        self.assertEqual(len([r for r in self.rows() if r.get("event") == "remote_cap_config"]), 1)   # once
        self.assertEqual([r["class"] for r in self.rec.rows if r["event"] == "remote_config"],
                         ["remote-direct", "lan", "remote-direct"])


class TheExplicitLines(Base):
    def test_an_explicit_start_rung_is_left_alone_in_both_classes(self):
        own = object()
        ns.START_RUNG = own                                                  # its module's own object
        u = self.umbrella({ru.START: "5000"})
        self.assertIsNone(u.start)
        for target in (LAN, OVERLAY):
            u.note_stream_start(target)
            self.assertIs(ns.START_RUNG, own)
        self.assertEqual(self.rec.rows[-1]["lines"][ru.START], {"in_force": True, "how": "explicit 5000"})
        ns.START_RUNG = None

    def test_an_explicit_ladder_off_leaves_no_ladder_and_the_cap_inactive(self):
        u = self.umbrella({ru.LADDER: "0"})
        self.assertIsNone(u.ladder)
        self.assertFalse(u.cap.active)
        self.assertEqual(u.cap.reason, "remote_ladder_flag_absent")
        u.note_stream_start(OVERLAY)
        self.assertIsNone(live.REMOTE_LADDER)
        self.assertIs(live.REMOTE_CAP, u.cap)
        self.assertFalse(u.cap.applies())
        self.assertEqual(self.rec.rows[-1]["lines"][ru.LADDER], {"in_force": False, "how": "explicit 0"})

    def test_no_service_the_telemetry_unavailable_the_rest_in_force(self):
        u = ru.RemoteUmbrella(self.rec, {}, controller=self.c, live=live, native=ns, service=lambda: None,
                              probe=lambda: probe, overlay_path=lambda: "direct", threaded=False)
        u.note_stream_start(OVERLAY)
        lines = self.rec.rows[-1]["lines"]
        self.assertFalse(lines[ru.TELEMETRY]["in_force"])
        self.assertIn("unavailable", lines[ru.TELEMETRY]["note"])
        self.assertTrue(all(lines[k]["in_force"] for k in (ru.LADDER, ru.START, ru.CAP)))


class TheFlag(unittest.TestCase):
    def test_the_table_and_the_config_row(self):
        for v in ("0", "", " ", "yes", "2", "true"):
            self.assertFalse(ru.enabled({ru.FLAG_ENV: v}), v)
            self.assertIsNone(ru.wire(Rec(), {ru.FLAG_ENV: v}))
        self.assertTrue(ru.enabled({ru.FLAG_ENV: " 1 "}))
        rec = Rec()
        u = ru.wire(rec, {ru.FLAG_ENV: "1"}, service=lambda: None, probe=lambda: probe)
        self.assertIsNotNone(u)
        cfg = rec.rows[0]
        self.assertEqual(cfg["event"], "remote_umbrella_config")
        self.assertEqual(cfg["lines"], {ru.LADDER: "implied 1", ru.START: "implied floor", ru.CAP: "implied 7000",
                                        ru.TELEMETRY: "implied 1"})
        self.assertEqual(cfg["cap"]["cap_kbps"], 7000)

    def test_no_address_in_any_row(self):
        rec = Rec()
        u = ru.RemoteUmbrella(rec, {}, live=live, native=ns, service=lambda: None, probe=lambda: probe,
                              overlay_path=lambda: "direct", threaded=False)
        saved = [(m, a, getattr(m, a)) for m, a in GLOBALS]
        try:
            u.note_stream_start(OVERLAY)
            u.note_stream_start(LAN)
        finally:
            for m, a, v in saved:
                setattr(m, a, v)
        text = json.dumps(rec.rows)
        self.assertNotIn(OVERLAY, text)
        self.assertNotIn(LAN, text)

    def test_nothing_imported_without_the_line(self):
        for extra, want in (({}, "False True"), ({"PRIVYHUB_REMOTE": "0"}, "False True"),
                            ({"PRIVYHUB_REMOTE": "yes"}, "False True"), ({"PRIVYHUB_REMOTE": "1"}, "True False")):
            env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
            env.update(extra)
            code = ("import sys, importlib.util; sys.path.insert(0, 'companion');"
                    "s = importlib.util.spec_from_file_location('g', 'companion/plugins/games.py');"
                    "m = importlib.util.module_from_spec(s); s.loader.exec_module(m);"
                    "print('remote_umbrella' in sys.modules, m._remote_umbrella is None)")
            out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True,
                                 text=True, timeout=300)
            self.assertEqual(out.stdout.strip().splitlines()[-1], want, (extra, out.stderr[-400:]))


if __name__ == "__main__":
    unittest.main()
