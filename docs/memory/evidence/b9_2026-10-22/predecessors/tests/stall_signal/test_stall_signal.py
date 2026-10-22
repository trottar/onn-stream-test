#!/usr/bin/env python3
"""B7: the client's stall signal, host side, with a fake client through the real receive loop.

    python3 -m unittest discover -s tests/stall_signal -v

The fake client sends controller packets at ~430/s and PHS1 stall datagrams on the same socket on a schedule; B1's
uplink gate makes a @both blackout. The real NativeControllerBridge loop, the real LinkDropRecovery (fake pause /
resume), B2's real detector + dispatcher, a fake B4 rewinder. B2 / B4 / B6's tests are untouched.
"""

from __future__ import annotations

import ast
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import hold_rewind as hr  # noqa: E402
import impairment as imp  # noqa: E402
import input_hold as ih  # noqa: E402
import stall_signal as ss  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402

LOOP = "127.0.0.1"


class FakeRewind:
    def __init__(self, calls):
        self.calls = calls
        self.pending = None
        self.cap = 30

    def set_pending(self, onset, paused_at, rec):
        self.pending = (onset, paused_at)

    def rewind(self, rec, via):
        self.calls.append(f"rewind:{via}")

    # B4's dispatcher hooks (the hold's own pending onset)
    def stamp(self, event, now):
        pass

    def on_handle(self, event):
        pass

    def note_paused(self, ours, paused_at, rec):
        self.pending = ("hold", paused_at) if ours else self.pending


class Rig:
    def __init__(self, threshold=150, hold_ms=None, rewind=True):
        self.calls = []
        self.root = Path(tempfile.mkdtemp(prefix="b7_rec_"))
        self.rec = ldr.LinkDropRecovery(
            self.root, pause_game=lambda: self.calls.append("pause"), resume_game=lambda: self.calls.append("resume"),
            save_recovery_state=lambda: {}, restart_encoder=lambda: {}, full_start_encoder=lambda: {},
            stream_active=lambda: True, end_session=lambda: None, client_packet_age_ms=lambda: 10.0,
            recovery_save_detail=lambda: {})
        self.rec._state = ldr.STATE_PLAYING
        self.rec._state_since = time.monotonic()
        self.rw = FakeRewind(self.calls) if rewind else None
        if rewind:
            self.rec._input_hold_rewind = self.rw
        self.sig = ss.StallSignal(self.rec, threshold)
        self.rec._client_stall = self.sig
        self.det = None
        if hold_ms:
            self.disp = ih.HoldDispatcher(self.rec, lambda: False)
            self.det = ih.InputHoldDetector(hold_ms, self.disp.put)

    def rows(self):
        p = self.rec.log_path()
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []

    def events(self, until=None):
        """until: the wall time the fake client stopped sending (its silence after that is the harness's own)."""
        from datetime import datetime
        keep = (lambda r: until is None or datetime.fromisoformat(r["at_utc"].replace("Z", "+00:00")).timestamp() < until)
        return [(r["event"], r.get("trigger") or r.get("via")) for r in self.rows() if keep(r)]


def stall(kind, gate, seq, frame, age):
    return ss.PACKET.pack(ss.MAGIC, kind, 1 if gate else 0, 0, seq, frame, int(age))


def run(rig, seconds, schedule, gate=None, rate=430):
    """schedule(t) -> (send_controller, stall datagram or None); the stall datagram at most every 50 ms."""
    import native_session_io as nsio
    nsio._impairment_uplink = gate
    try:
        br = nsio.NativeControllerBridge(Path(tempfile.mkdtemp(prefix="b7_bridge_")))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((LOOP, 0))
        sock.settimeout(0.05)
        br._socket, br._client_ip = sock, LOOP
        br._apply_report = lambda **kw: br._neutralized.__setitem__(kw["player"], False)
        br._neutralize = lambda player=None: None
        if rig.det is not None:
            br.set_input_hold(rig.det)
        if rig.sig is not None:
            br.set_stall_signal(rig.sig)
        br._running.set()
        th = threading.Thread(target=br._receive_loop, daemon=True)
        th.start()
        tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        port = sock.getsockname()[1]
        t0 = time.monotonic()
        n, last_stall, ended = 0, -1.0, False
        while (t := time.monotonic() - t0) < seconds:
            due = n / rate
            if due > t:
                time.sleep(min(due - t, 0.002))
                continue
            ctrl, st = schedule(t)
            if ctrl:
                tx.sendto(nsio.NativeControllerBridge.PACKET.pack(nsio.NativeControllerBridge.MAGIC, 1, 0, 0,
                                                                  n & 0xFFFFFFFF, 0, 0, 0, 0, 0, 0, 0, 0), (LOOP, port))
            if st is not None and ((st[0] == ss.KIND_END and not ended) or (st[0] == ss.KIND_STALL and t - last_stall >= 0.05)):
                kind, gate_bit, age = st
                ended = ended or kind == ss.KIND_END
                tx.sendto(stall(kind, gate_bit, n, 1000 + n, age), (LOOP, port))
                if kind == ss.KIND_STALL:
                    last_stall = t
            n += 1
        end_wall = time.time()
        time.sleep(0.4)
        br._running.clear()
        th.join(timeout=2)
        tx.close()
        sock.close()
        return {"t0": t0, "bad": br._bad_packets, "end_wall": end_wall}
    finally:
        nsio._impairment_uplink = None


class Parse(unittest.TestCase):
    def test_flag_and_decode(self):
        self.assertEqual(ss.parse(None), (None, None))
        self.assertEqual(ss.parse("1"), (150, None))
        self.assertEqual(ss.parse("400"), (400, None))
        for bad in ("0", "149", "2001", "on", "x"):
            t, why = ss.parse(bad)
            self.assertIsNone(t, bad)
            self.assertTrue(why.startswith("ignored"))
        self.assertEqual(ss.PACKET.size, 24)
        self.assertEqual(ss.decode(stall(1, True, 7, 12345, 431)), (1, True, 7, 12345, 431))
        self.assertIsNone(ss.decode(b"PHS1" + b"\0" * 19))
        self.assertIsNone(ss.decode(b"PHI1" + b"\0" * 20))
        self.assertIsNone(ss.decode(stall(9, False, 1, 1, 1)))


class Down(unittest.TestCase):
    """@down: the uplink alive; the client's frames stop at 0.85 s and return at 2.0 s."""

    def _sched(self, end=True, ages_from=0.85, stop=2.0):
        def s(t):
            if ages_from + 0.15 <= t < stop:
                return True, (ss.KIND_STALL, False, (t - ages_from) * 1000.0)
            if end and stop <= t < stop + 0.01:
                return True, (ss.KIND_END, False, 10)
            return True, None
        return s

    def test_stall_pauses_stall_end_resumes_with_the_rewind(self):
        rig = Rig()
        r = run(rig, 2.6, self._sched())
        ev = rig.events()
        self.assertEqual(ev[0], ("desync_pause", "client_stall"), ev)
        self.assertIn(("client_stall", None), ev)
        self.assertEqual(ev[-1], ("resumed", "stall_end"))
        self.assertEqual(rig.calls, ["pause", "rewind:stall_end", "resume"])
        onset, paused_at = rig.rw.pending
        self.assertAlmostEqual(onset - r["t0"], 0.85, delta=0.03)          # the client's last frame, host clock
        pause_row = [x for x in rig.rows() if x["event"] == "desync_pause"][0]
        self.assertGreaterEqual(pause_row["age_ms"], 150)
        self.assertLessEqual(pause_row["age_ms"], 230)
        self.assertEqual(rig.sig.ends, 1)

    def test_below_the_hosts_threshold_nothing(self):
        rig = Rig(threshold=400)
        run(rig, 1.6, self._sched(stop=1.2))                               # ages 150-350 ms
        self.assertEqual(rig.events(), [])
        self.assertEqual(rig.calls, [])

    def test_a_lost_stall_end_resumes_after_300_ms_quiet(self):
        rig = Rig()
        run(rig, 2.8, self._sched(end=False))
        ev = rig.events()
        self.assertEqual(ev[-1], ("resumed", "stall_quiet"), ev)
        self.assertEqual(rig.calls, ["pause", "rewind:stall_quiet", "resume"])


class Both(unittest.TestCase):
    """@both: the uplink dark 1.0-2.0 s (B1's gate); the client stalled from 1.15 s and in its gate until 2.6 s."""

    def _gate(self):
        return imp.UplinkGate(imp.Blackout(1.0, 100.0, 1.0, epoch=time.monotonic()))

    def test_the_hold_hands_over_to_the_stall_and_resumes_at_stall_end(self):
        rig = Rig(hold_ms=250)

        def s(t):
            if 1.15 <= t < 2.6:
                return True, (ss.KIND_STALL, t >= 2.1, 900 if t < 2.1 else 20)   # frames back at 2.1, gate until 2.6
            if 2.6 <= t < 2.61:
                return True, (ss.KIND_END, False, 15)
            return True, None
        r = run(rig, 3.1, s, gate=self._gate())
        ev = rig.events(until=r["end_wall"])
        self.assertEqual([e for e in ev if e[0] == "desync_pause"], [("desync_pause", "input_hold")], ev)
        self.assertIn(("input_hold_handover", "client_stall"), ev)
        self.assertNotIn(("resumed", "input_release"), ev)                 # not resumed behind the overlay
        self.assertEqual(ev[-1], ("resumed", "stall_end"))
        self.assertEqual(rig.calls[:3], ["pause", "rewind:stall_end", "resume"])   # (a 4th = the harness's own end)
        resumed = [x for x in rig.rows() if x["event"] == "resumed"][0]
        handover = [x for x in rig.rows() if x["event"] == "input_hold_handover"][0]
        self.assertGreaterEqual(resumed["recovering_ms"], 1200)            # the pause stood to ~2.6 s

    def test_no_stall_b2s_release_after_the_short_wait(self):
        rig = Rig(hold_ms=250)
        r = run(rig, 2.6, lambda t: (True, None), gate=self._gate())
        ev = rig.events(until=r["end_wall"])
        self.assertEqual(ev, [("desync_pause", "input_hold"), ("resumed", "input_release")], ev)
        held = [x for x in rig.rows() if x["event"] == "resumed"][0]["held_ms"]
        self.assertAlmostEqual(held, 1000.0, delta=120.0)


class ReadyAndOrder(unittest.TestCase):
    def _unit(self):
        rig = Rig()
        rig.sig = ss.StallSignal(rig.rec, 150, threaded=False)
        rig.rec._client_stall = rig.sig
        return rig

    def test_a_ready_after_a_stall_resume_is_not_a_new_session(self):
        rig = self._unit()
        now = time.monotonic()
        rig.sig.last_stall_rx = now
        rig.sig.handle((ss.KIND_STALL, False, 1, 500, 300), now)
        rig.sig.handle((ss.KIND_END, False, 2, 501, 10), now + 1.0)
        self.assertEqual(rig.rec.note_gameplay_released(), {"recovered": True, "from_state": "stall_resumed"})
        ev = [e for e, _ in rig.events()]
        self.assertIn("client_ready_after_stall", ev)
        self.assertNotIn("session_started", ev)

    def test_the_ready_first_then_stall_end_one_resume(self):
        rig = self._unit()
        now = time.monotonic()
        rig.sig.last_stall_rx = now
        rig.sig.handle((ss.KIND_STALL, True, 1, 500, 1200), now)
        self.assertEqual(rig.rec.note_gameplay_released()["from_state"], "PAUSED_RECOVERING")   # the gate's path
        rig.sig.handle((ss.KIND_END, False, 2, 501, 10), now + 0.01)
        self.assertEqual(rig.calls, ["pause"])                             # the gate's resume is the plugin's
        self.assertIn(("stall_end_after_gate", None), rig.events())
        self.assertEqual([e for e, v in rig.events() if e == "resumed"], ["resumed"])

    def test_a_client_desync_during_a_stall_pause_is_ignored(self):
        rig = self._unit()
        now = time.monotonic()
        rig.sig.handle((ss.KIND_STALL, False, 1, 500, 300), now)
        rig.rec.note_client_desync("output_silence", 1000.0)
        self.assertEqual(rig.rec._last_desync_reason, "client_stall")
        self.assertEqual(rig.calls, ["pause"])

    def test_b4_set_pending(self):
        class E:
            lock = threading.RLock()
            _network_cmd_port = None
        rw = hr.Rewinder(E(), type("C", (), {"_neutralize": lambda self, p=None: None})(), 30)
        rec = type("R", (), {"_state_since": 5.0, "_log": lambda self, e, **k: None})()
        rw.set_pending(10.0, 10.0 + 20 / 60.0, rec)
        self.assertEqual(rw.counter_before(rw._pending), 16)               # 20 - B4's 4-frame lag
        self.assertEqual(rw._pending["key"], 5.0)


class FlagAbsent(unittest.TestCase):
    def test_not_imported_and_a_stall_datagram_is_a_bad_packet_as_today(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        code = ("import sys; sys.path.insert(0, 'companion'); import native_session_io as n; "
                "from games import link_drop_recovery as l; "
                "print('stall_signal' in sys.modules, n.NativeControllerBridge._stall_signal, l.LinkDropRecovery._client_stall)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=120)
        self.assertEqual(out.stdout.strip(), "False None None", out.stderr[-400:])
        rig = Rig()
        rig.sig = None
        rig.rec._client_stall = None
        r = run(rig, 0.6, lambda t: (True, (ss.KIND_STALL, False, 500) if 0.2 <= t < 0.4 else None))
        self.assertGreaterEqual(r["bad"], 3)                               # counted, ignored, as any unknown datagram
        self.assertEqual(rig.events(), [])

    def test_hook_shapes(self):
        def ifs(rel, text):
            tree = ast.parse((ROOT / "companion" / rel).read_text())
            return [n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test).startswith(text)]
        self.assertEqual(len(ifs("native_session_io.py", "self._stall_signal is not None")), 1)
        self.assertEqual(len(ifs("games/link_drop_recovery.py", "self._client_stall is not None")), 2)
        self.assertEqual(len(ifs("plugins/games.py", "_stall_signal is not None")), 1)


if __name__ == "__main__":
    unittest.main()
