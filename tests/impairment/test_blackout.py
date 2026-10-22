#!/usr/bin/env python3
"""B1: the shim's blackout, both directions.

    python3 -m unittest discover -s tests/impairment -v

The grammar, the one scheduler, the downlink stage, the uplink gate, the hooks' shape and their absence, and a short
run of the real controller bridge's receive loop on the loopback. No stream, no companion.
"""

from __future__ import annotations

import ast
import ipaddress
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

import impairment as imp  # noqa: E402

LOOP = str(ipaddress.ip_address(0x7F000001))
def is_hook(node) -> bool:
    """The one guarded hook form (the service's looks the gate up, for G5-S1's out-of-module handler test)."""
    t = ast.unparse(node.test)
    return (t.startswith("_impairment_uplink is not None and")
            or t.startswith("(_gate := globals().get('_impairment_uplink')) is not None and"))


HOOKED = {"native_session_io.py": ("controller",), "plugins/games.py": ("heartbeat", "desync"),  # B1b: + desync
          "privyhub_service.py": ("client_health",)}


class Grammar(unittest.TestCase):
    def test_defaults_both(self):
        p = imp.parse("blackout-4s@both")
        self.assertEqual((p.blackout_s, p.blackout_every_s, p.blackout_first_s), (4.0, 120.0, 120.0))
        self.assertTrue(p.uplink)
        self.assertEqual(p.placement, imp.POST_FEC)

    def test_down_and_options(self):
        p = imp.parse("blackout-2.5s@down,every=30s,first=5s,seed=9")
        self.assertEqual((p.blackout_s, p.blackout_every_s, p.blackout_first_s, p.seed), (2.5, 30.0, 5.0, 9))
        self.assertFalse(p.uplink)
        self.assertEqual(p.placement, imp.POST_FEC)
        p = imp.parse("blackout-4s+loss-1@both,seed=3,every=60s")
        self.assertEqual((p.loss, p.blackout_s, p.blackout_every_s, p.seed), (0.01, 4.0, 60.0, 3))

    def test_todays_specs_unchanged(self):
        p = imp.parse("loss-1+delay-50+jitter-30@post-fec,seed=7")
        self.assertEqual((p.loss, p.delay_ms, p.jitter_ms, p.placement, p.seed, p.blackout_s, p.uplink),
                         (0.01, 50.0, 30.0, imp.POST_FEC, 7, 0.0, False))
        self.assertEqual(imp.parse("cap-6000").placement, imp.PRE_FEC)

    def test_errors(self):
        for bad in ("loss-1@both", "loss-1@down", "loss-1,every=10s", "blackout-4s@both,every=4s",
                    "blackout-4s@both,every=10", "blackout-0s@both", "blackout-99s@both", "blackout-4@both",
                    "blackout-4s@sideways", "blackout-4s@both,colour=red", "blackout-4s@both,every=9s,every=8s"):
            with self.assertRaises(ValueError, msg=bad):
                imp.parse(bad)


class Scheduler(unittest.TestCase):
    def test_active_spans(self):
        b = imp.Blackout(4, 20, 10, epoch=100.0)
        on = [t for t in range(100, 170) if b.active(float(t))]
        self.assertEqual(on, [110, 111, 112, 113, 130, 131, 132, 133, 150, 151, 152, 153])
        self.assertFalse(b.active(109.999))
        self.assertTrue(b.active(113.999))
        self.assertFalse(b.active(114.0))

    def test_shared_is_one_object(self):
        p = imp.parse("blackout-3s@both,every=50s,first=7s")
        a, b = imp.shared_blackout(p), imp.shared_blackout(imp.parse("blackout-3s@both,every=50s,first=7s"))
        self.assertIs(a, b)
        self.assertIs(imp.uplink_gate(p).blackout, a)
        self.assertIs(imp.uplink_gate(p), imp.uplink_gate(p))

    def test_gate_only_for_both(self):
        self.assertIsNone(imp.uplink_gate(imp.parse("blackout-4s@down")))
        self.assertIsNone(imp.uplink_gate(imp.parse("loss-5@post-fec")))
        self.assertIsNone(imp.uplink_gate_from_environ({}))
        self.assertIsNone(imp.uplink_gate_from_environ({imp.FLAG_ENV: "loss-1"}))
        self.assertIsNone(imp.uplink_gate_from_environ({imp.FLAG_ENV: "not-a-profile"}))
        self.assertIsNotNone(imp.uplink_gate_from_environ({imp.FLAG_ENV: "blackout-4s@both"}))


class Downlink(unittest.TestCase):
    def test_drops_only_in_the_dark(self):
        p = imp.parse("blackout-4s@down,every=20s,first=10s")
        i = imp.Impairer(p, start=0.0)
        out = []
        for k in range(60 * 60):                    # 60 s at 60 packets / s
            t = k / 60.0
            i.offer(t, bytes([k % 256]))
            out += [(t, d) for d in i.due(t)]
        self.assertEqual(i.counters.dropped_blackout, 3 * 4 * 60)
        self.assertEqual(len(out), 60 * 60 - 3 * 4 * 60)
        self.assertEqual(i.counters.dropped_loss + i.counters.dropped_burst + i.counters.dropped_queue, 0)

    def test_shared_scheduler_used(self):
        p = imp.parse("blackout-1s@down,every=10s,first=0s")
        b = imp.Blackout(1, 10, 0, epoch=500.0)
        i = imp.Impairer(p, start=0.0, blackout=b)
        i.offer(500.5, b"x")
        i.offer(501.5, b"y")
        self.assertEqual((i.counters.dropped_blackout, len(i.due(502.0))), (1, 1))


class Uplink(unittest.TestCase):
    def test_gate_counts_by_kind(self):
        clock = {"t": 0.0}
        g = imp.UplinkGate(imp.Blackout(2, 10, 1, epoch=0.0), clock=lambda: clock["t"])
        self.assertFalse(g.drop("controller"))
        clock["t"] = 1.5
        self.assertTrue(g.drop("controller"))
        self.assertTrue(g.drop("heartbeat"))
        self.assertTrue(g.drop("client_health"))
        clock["t"] = 3.0
        self.assertFalse(g.drop("heartbeat"))
        self.assertEqual(g.dropped, {"controller": 1, "heartbeat": 1, "client_health": 1})
        self.assertEqual(g.total, 3)

    def test_counters_have_the_new_fields(self):
        c = imp.Counters().as_dict()
        self.assertEqual((c["dropped_blackout"], c["uplink_dropped"]), (0, 0))


class Hooks(unittest.TestCase):
    def test_guarded_imports_and_hook_shape(self):
        for rel, kind in HOOKED.items():
            tree = ast.parse((ROOT / "companion" / rel).read_text())
            top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
            self.assertFalse(any("impairment" in ast.unparse(n) for n in top), rel)
            guarded = [n for n in tree.body if isinstance(n, ast.If) and "import impairment" in ast.unparse(n)]
            self.assertEqual(len(guarded), 1, rel)
            self.assertIn("PRIVYHUB_IMPAIRMENT", ast.unparse(guarded[0].test))
            hooks = [n for n in ast.walk(tree) if isinstance(n, ast.If) and is_hook(n)]
            self.assertEqual(len(hooks), len(kind), rel)
            for k in kind:
                self.assertTrue(any(f"drop('{k}')" in ast.unparse(h.test) for h in hooks), (rel, k))

    def test_flag_absent_not_imported(self):
        env = {k: v for k, v in os.environ.items() if k != imp.FLAG_ENV}
        code = ("import sys; sys.path.insert(0, 'companion'); import native_session_io as n; "
                "print('impairment' in sys.modules, n._impairment_uplink)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True,
                             text=True, timeout=120)
        self.assertEqual(out.stdout.strip(), "False None", out.stderr[-500:])

    def test_downlink_profile_leaves_the_loop_ungated(self):
        env = dict(os.environ, **{imp.FLAG_ENV: "loss-1@post-fec"})
        code = ("import sys; sys.path.insert(0, 'companion'); import native_session_io as n; "
                "print(n._impairment_uplink)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True,
                             text=True, timeout=120)
        self.assertEqual(out.stdout.strip(), "None", out.stderr[-500:])


def run_bridge(seconds: float, gate, silence_ms: float = 500.0, rate: int = 430):
    """The real NativeControllerBridge receive loop on the loopback, gamepads stubbed. Returns the observations."""
    import native_session_io as nsio
    nsio._impairment_uplink = gate
    try:
        br = nsio.NativeControllerBridge(Path(tempfile.mkdtemp(prefix="b1_bridge_")))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((LOOP, 0))
        sock.settimeout(0.05)
        br._socket, br._client_ip = sock, LOOP
        applied, neutralized, silences = [], [], []
        br._apply_report = lambda **kw: (applied.append(time.monotonic()),
                                         br._neutralized.__setitem__(kw["player"], False))
        def neutralize(player=None):                 # the loop's exit calls it with no player: all of them
            neutralized.append((time.monotonic(), player))
            for p in ([player] if player is not None else range(br.MAX_PLAYERS)):
                br._neutralized[p] = True

        br._neutralize = neutralize
        br.set_client_silence_callback(lambda ms: silences.append((time.monotonic(), ms)), silence_ms)
        br._running.set()
        th = threading.Thread(target=br._receive_loop, daemon=True)
        th.start()
        tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        port = sock.getsockname()[1]
        t0 = time.monotonic()
        n = 0
        while time.monotonic() - t0 < seconds:
            due = t0 + n / rate
            d = due - time.monotonic()
            if d > 0:
                time.sleep(min(d, 0.002))
                continue
            pkt = nsio.NativeControllerBridge.PACKET.pack(nsio.NativeControllerBridge.MAGIC, 1, 0, 0, n & 0xFFFFFFFF,
                                                          0, 0, 0, 0, 0, 0, 0, 0)
            tx.sendto(pkt, (LOOP, port))
            n += 1
        time.sleep(0.2)
        br._running.clear()
        th.join(timeout=2)
        tx.close()
        sock.close()
        return {"t0": t0, "sent": n, "applied": applied, "neutralized": neutralized, "silences": silences}
    finally:
        nsio._impairment_uplink = None


class BridgeShort(unittest.TestCase):
    def test_the_real_receive_loop_goes_dark_and_reports_silence(self):
        epoch = time.monotonic()
        gate = imp.UplinkGate(imp.Blackout(1.0, 3.0, 1.0, epoch=epoch))
        r = run_bridge(6.5, gate, silence_ms=500.0)
        gaps = [(a, b - a) for a, b in zip(r["applied"], r["applied"][1:]) if b - a > 0.06]
        self.assertEqual(len(gaps), 2, gaps)                       # dark at 1-2 s and 4-5 s
        for a, g in gaps:
            self.assertAlmostEqual(g, 1.0, delta=0.08)
        self.assertEqual(len(r["silences"]), 2)                    # once per episode
        self.assertGreater(gate.dropped["controller"], 0)
        self.assertGreaterEqual(len(r["neutralized"]), 2)


if __name__ == "__main__":
    unittest.main()
