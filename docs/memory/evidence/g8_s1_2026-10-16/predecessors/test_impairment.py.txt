#!/usr/bin/env python3
"""G8-P1: the impairment shim — the parser, each stage on a fake clock, the
bounded queue, both placements against the real FEC sender, and the hook's
inertness without the flag.

    python3 -m unittest discover -s tests/impairment -v

Loopback sockets only (ephemeral ports); no stream, no companion.
"""

from __future__ import annotations

import ast
import os
import socket
import struct
import sys
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import impairment as imp  # noqa: E402
import native_fec_relay as relay_mod  # noqa: E402

PKT = 1200


def rtp(seq: int, ts: int, marker: bool = False, size: int = PKT) -> bytes:
    hdr = struct.pack("!BBHII", 0x80, (0x80 if marker else 0) | 96, seq & 0xFFFF, ts, 0x1234ABCD)
    return hdr + bytes((seq + i) & 0xFF for i in range(size - len(hdr)))


def run_offers(spec: str, n: int, pps: float = 730.0, size: int = PKT):
    p = imp.parse(spec)
    t0 = 1000.0
    im = imp.Impairer(p, t0)
    out = []
    for i in range(n):
        now = t0 + i / pps
        im.offer(now, i.to_bytes(4, "big") + bytes(size - 4))
        out += [(now, int.from_bytes(d[:4], "big")) for d in im.due(now)]
    end = t0 + n / pps
    for k in range(1, 400):                       # drain
        now = end + k * 0.01
        out += [(now, int.from_bytes(d[:4], "big")) for d in im.due(now)]
    return im, out


class Parse(unittest.TestCase):
    def test_specs(self):
        p = imp.parse("loss-1")
        self.assertEqual((p.loss, p.placement, p.seed), (0.01, "pre-fec", 1))
        p = imp.parse("loss-1+delay-50+jitter-30@post-fec,seed=7")
        self.assertEqual((p.loss, p.delay_ms, p.jitter_ms, p.placement, p.seed), (0.01, 50.0, 30.0, "post-fec", 7))
        self.assertEqual(p.label, "loss-1+delay-50+jitter-30")
        for bad in ("", "nope", "loss-1@mid", "loss-1,sed=3", "loss-1,seed=x"):
            with self.assertRaises(ValueError):
                imp.parse(bad)
        self.assertIsNone(imp.from_environ({}))
        self.assertIsNone(imp.from_environ({imp.FLAG_ENV: "  "}))
        self.assertEqual(set(imp.PROFILES), {"loss-1", "loss-5", "burst-50x20", "delay-50", "delay-150",
                                             "jitter-30", "reorder-5", "cap-6000", "cap-4500"})


class Stages(unittest.TestCase):
    def test_none_passes_everything_in_order(self):
        im, out = run_offers("delay-50", 2000)
        self.assertEqual([s for _, s in out], list(range(2000)))

    def test_random_loss(self):
        for spec, rate in (("loss-1", 0.01), ("loss-5", 0.05)):
            im, out = run_offers(spec, 50_000)
            got = 1 - len(out) / 50_000
            self.assertAlmostEqual(got, rate, delta=rate * 0.15, msg=spec)
            self.assertEqual(im.counters.dropped_loss, 50_000 - len(out))

    def test_seeded(self):
        a = [s for _, s in run_offers("loss-5,seed=3", 5000)[1]]
        b = [s for _, s in run_offers("loss-5,seed=3", 5000)[1]]
        c = [s for _, s in run_offers("loss-5,seed=4", 5000)[1]]
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_bursts(self):
        im, out = run_offers("burst-50x20", int(730 * 60))
        got = {s for _, s in out}
        missing = sorted(set(range(int(730 * 60))) - got)
        runs, prev = [], None
        for s in missing:
            if prev is None or s != prev + 1:
                runs.append(1)
            else:
                runs[-1] += 1
            prev = s
        self.assertEqual(runs, [50, 50, 50])            # at 10, 30, 50 s

    def test_delay_and_jitter(self):
        im, out = run_offers("delay-150", 1000)
        sent = {i: 1000.0 + i / 730.0 for i in range(1000)}
        d = [(t - sent[s]) * 1000 for t, s in out]
        self.assertTrue(all(150 <= x <= 161 for x in d))  # the drain step is 10 ms
        im, out = run_offers("jitter-30", 5000)
        self.assertEqual([s for _, s in out], list(range(5000)))   # FIFO: never reordered
        d = [(t - sent.get(s, 1000.0 + s / 730.0)) * 1000 for t, s in out]
        self.assertTrue(min(d) >= 0 and max(d) <= 45)

    def test_reorder(self):
        im, out = run_offers("reorder-5", 20_000)
        seqs = [s for _, s in out]
        self.assertEqual(sorted(seqs), list(range(20_000)))        # nothing lost
        late = sum(1 for a, b in zip(seqs, seqs[1:]) if b < a)
        self.assertAlmostEqual(late / 20_000, 0.05, delta=0.01)

    def test_cap_bounded_queue(self):
        im, out = run_offers("cap-4500", 730 * 20)                 # 7 Mbit/s into 4.5
        dur = out[-1][0] - out[0][0]
        kbps = len(out) * PKT * 8 / dur / 1000
        self.assertAlmostEqual(kbps, 4500, delta=4500 * 0.05)
        limit = int(4500e3 / 8 * imp.QUEUE_LIMIT_S / PKT) + 2
        self.assertLessEqual(im.counters.queue_max, limit)          # bounded
        self.assertGreater(im.counters.dropped_queue, 0)


def free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((imp.LOOPBACK, 0))
    p = s.getsockname()[1]
    s.close()
    return p


class Placements(unittest.TestCase):
    def _run(self, spec, frames=120, per=8):
        cap = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cap.bind((imp.LOOPBACK, 0))
        cap.settimeout(0.3)
        got: list[bytes] = []
        done = threading.Event()

        def reader():       # read while sending: a capture buffer must not be the loss
            idle = 0
            while not done.is_set() or idle < 2:
                try:
                    got.append(cap.recv(65535))
                    idle = 0
                except socket.timeout:
                    idle += 1

        rt = threading.Thread(target=reader, daemon=True)
        rt.start()
        old = relay_mod._impairment
        os.environ[imp.FLAG_ENV] = spec
        relay_mod._impairment = imp
        try:
            r = relay_mod.NativeVideoFecRelay(local_port=free_port(), pacing_us=0)
            r.start(imp.LOOPBACK, cap.getsockname()[1])
            src = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            seq = 0
            for f in range(frames):
                for k in range(per):
                    src.sendto(rtp(seq, f * 1500, marker=(k == per - 1)), (imp.LOOPBACK, r.local_port))
                    seq += 1
                time.sleep(1 / 120)
            done.set()
            rt.join(timeout=5)
            src.close()
            shim = r._shim
            r.stop()
            return got, shim, seq
        finally:
            relay_mod._impairment = old
            os.environ.pop(imp.FLAG_ENV, None)
            cap.close()

    def test_pre_fec_the_shim_takes_the_port(self):
        got, shim, sent = self._run("delay-50@pre-fec")
        self.assertEqual(shim.profile.placement, "pre-fec")
        rtp_pkts = [g for g in got if not g.startswith(relay_mod.FEC_MAGIC)]
        parity = [g for g in got if g.startswith(relay_mod.FEC_MAGIC)]
        self.assertEqual(len(rtp_pkts), sent)
        self.assertEqual(len(parity), sent // 8)                    # delay alone loses nothing

    def test_post_fec_parity_is_impaired_too(self):
        got, shim, sent = self._run("loss-5@post-fec,seed=2", frames=400)
        c = shim.shim.counters()
        self.assertEqual(c["packets_in"], sent + sent // 8)        # RTP and parity both pass the shim
        self.assertEqual(len(got), c["packets_out"])
        self.assertGreater(c["dropped_loss"], 0)

    def test_stop_releases_the_port(self):
        got, shim, _ = self._run("loss-1")
        for _ in range(20):
            if not any(t.name == "PrivyHub-Impairment" and t.is_alive() for t in threading.enumerate()):
                break
            time.sleep(0.05)
        self.assertFalse(any(t.name == "PrivyHub-Impairment" and t.is_alive() for t in threading.enumerate()))


class FlagAbsent(unittest.TestCase):
    def test_not_imported_and_inert(self):
        self.assertIsNone(relay_mod._impairment)                  # this process carries no flag
        tree = ast.parse((ROOT / "companion" / "native_fec_relay.py").read_text())
        top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any("impairment" in ast.unparse(n) for n in top))
        guarded = [n for n in tree.body if isinstance(n, ast.If) and "impairment" in ast.unparse(n)]
        self.assertEqual(len(guarded), 1)
        self.assertIn("PRIVYHUB_IMPAIRMENT", ast.unparse(guarded[0].test))

    def test_same_port_same_target_no_thread(self):
        cap = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cap.bind((imp.LOOPBACK, 0))
        port = free_port()
        r = relay_mod.NativeVideoFecRelay(local_port=port, pacing_us=0)
        r.start(imp.LOOPBACK, cap.getsockname()[1])
        try:
            self.assertEqual(r._recv_socket.getsockname()[1], port)
            self.assertEqual(r._client, (imp.LOOPBACK, cap.getsockname()[1]))
            self.assertIsNone(getattr(r, "_shim", None))
            self.assertFalse(any(t.name == "PrivyHub-Impairment" for t in threading.enumerate()))
        finally:
            r.stop()
            cap.close()


if __name__ == "__main__":
    unittest.main()
