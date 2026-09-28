#!/usr/bin/env python3
"""C4-M1: unit tests for the xor8_2 codec pair (relay encoder + reference decoder).

    python3 -m unittest tools/test_fec_xor8_2.py -v

The relay is driven without sockets (its `_send` is a capture) over synthetic
RTP built from the recorded H.264 sample; every group's datagrams are then
re-decoded under every loss pattern. Also the golden rule: with the scheme
unset, the relay's bytes equal the unmodified relay's (sha256 recorded in
docs/memory/evidence/c4_m1_2026-09-25/golden_before.txt).
"""

from __future__ import annotations

import hashlib
import itertools
import os
import random
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "companion"))

import native_fec_rs as rs  # noqa: E402

GOLDEN_UNSET_SHA = "d208174479755d38ac12e8251ef38ad407ed3ab7805ef6d7096a110ed4e69e2f"


def drive(scheme):
    if scheme:
        os.environ["PRIVYHUB_FEC_SCHEME"] = scheme
    else:
        os.environ.pop("PRIVYHUB_FEC_SCHEME", None)
    os.environ.pop("PRIVYHUB_FEC_PACING_US", None)
    import native_fec_relay as r
    relay = r.NativeVideoFecRelay(pacing_us=0)
    out = []
    relay._send = lambda packet, parity: out.append((bool(parity), bytes(packet)))  # noqa: E731
    data = (ROOT / "logs/games/a1_sample.h264").read_bytes()[:600_000]
    rng = random.Random(20260925)
    pos, seq, ts, ssrc = 0, 1000, 90_000, 0x1234ABCD
    while pos < len(data) - 20_000:
        n = rng.choice([1, 2, 3, 5, 7, 8, 9, 12, 15, 16, 17, 24, 40])
        for i in range(n):
            size = rng.randint(200, 1188)
            payload = data[pos:pos + size]
            pos += size
            marker = 0x80 if i == n - 1 else 0
            relay._handle_rtp(struct.pack("!BBHII", 0x80, marker | 96, seq & 0xFFFF, ts, ssrc) + payload)
            seq += 1
        ts += 1500
    os.environ.pop("PRIVYHUB_FEC_SCHEME", None)
    return relay, out


def groups(out):
    """[(data payloads by index, P packet, Q packet)] from the captured stream."""
    rtp = {}
    res = []
    pend = {}
    for is_p, pkt in out:
        if not is_p:
            seq = struct.unpack("!H", pkt[2:4])[0]
            rtp[seq] = pkt[12:]
            continue
        magic, ver, count, base, ts, ssrc, mm, b0, pt, lx, plen = struct.unpack("!4sBBHIIBBBHH", pkt[:23])
        key = (ts, base)
        pend.setdefault(key, {})[ver] = (count, lx, pkt[23:23 + plen])
    for (ts, base), d in pend.items():
        count = d[1][0]
        data = {i: rtp[(base + i) & 0xFFFF] for i in range(count)}
        res.append((data, d.get(1), d.get(2)))
    return res


class CodecTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _, cls.out_unset = drive(None)
        cls.relay82, cls.out82 = drive("xor8_2")
        cls.g = groups(cls.out82)

    def test_golden_unset_bytes_unchanged(self):
        """Rule: scheme unset -> the relay's datagrams equal the unmodified relay's (golden)."""
        blob = b"".join(struct.pack("!BI", 1 if p else 0, len(x)) + x for p, x in self.out_unset)
        self.assertEqual(hashlib.sha256(blob).hexdigest(), GOLDEN_UNSET_SHA)

    def test_xor8_2_keeps_rtp_and_p_identical(self):
        """Rule: under xor8_2 the RTP and the v1 parity datagrams are the same bytes, in order;
        each group gains exactly one v2 datagram."""
        strip = [x for p, x in self.out82 if not (p and x[4] == 2)]
        self.assertEqual(strip, [x for _, x in self.out_unset])
        v1 = sum(1 for p, x in self.out82 if p and x[4] == 1)
        v2 = sum(1 for p, x in self.out82 if p and x[4] == 2)
        self.assertEqual(v1, v2)
        self.assertGreater(v2, 100)

    def test_status_reports_scheme(self):
        """Rule: the relay's status names the scheme and its source."""
        st = self.relay82.status()
        self.assertEqual((st["version"], st["scheme_source"]), ("xor8_2", "env"))
        self.assertGreater(st["q_parity_packets"], 0)

    def test_unknown_scheme_is_ignored(self):
        """Rule: an unknown value reads xor8_1, source env_ignored."""
        os.environ["PRIVYHUB_FEC_SCHEME"] = "xor8_9"
        import native_fec_relay as r
        relay = r.NativeVideoFecRelay(pacing_us=0)
        os.environ.pop("PRIVYHUB_FEC_SCHEME", None)
        self.assertEqual((relay.fec_scheme, relay.fec_scheme_source), ("xor8_1", "env_ignored"))

    def test_every_single_loss_recovers_from_q_when_p_is_lost(self):
        """Rule: one data packet and its P lost -> Q alone recovers it (all groups, all positions)."""
        for data, p, q in self.g:
            count, lq, qpar = q
            for x in range(count):
                known = {i: d for i, d in data.items() if i != x}
                rec, n = rs.recover_one_from_q(qpar, lq, known, x)
                self.assertEqual((rec, n), (data[x], len(data[x])))

    def test_every_two_loss_pattern_recovers(self):
        """Rule: any two data packets of a group lost (consecutive or not) -> P + Q recover both."""
        checked = 0
        for data, p, q in self.g:
            count, lx, ppar = p
            _, lq, qpar = q
            for x, y in itertools.combinations(range(count), 2):
                known = {i: d for i, d in data.items() if i not in (x, y)}
                (dx, nx), (dy, ny) = rs.recover_two(ppar, lx, qpar, lq, known, x, y)
                self.assertEqual((dx, dy), (data[x], data[y]))
                self.assertEqual((nx, ny), (len(data[x]), len(data[y])))
                checked += 1
        self.assertGreater(checked, 1000)

    def test_p_parity_is_the_relays(self):
        """Rule: the reference P equals the relay's v1 parity (so the decoder's inputs are right)."""
        for data, p, q in self.g:
            count, lx, ppar = p
            self.assertEqual(rs.p_parity([data[i] for i in range(count)], len(ppar)), ppar)

    def test_three_losses_are_not_recoverable(self):
        """Rule: three missing packets exceed two parities -- the two-erasure solve over any
        pair, fed the third packet's absence, does not reproduce the data."""
        data, p, q = next(g for g in self.g if g[1][0] == 8)
        count, lx, ppar = p
        _, lq, qpar = q
        known = {i: d for i, d in data.items() if i not in (2, 3, 4)}
        (dx, _), (dy, _) = rs.recover_two(ppar, lx, qpar, lq, known, 2, 3)
        self.assertFalse(dx == data[2] and dy == data[3])

    def test_gf_field(self):
        """Rule: GF(256) with 0x11d: every non-zero element has an inverse; g generates."""
        for a in range(1, 256):
            self.assertEqual(rs.gf_mul(a, rs.gf_inv(a)), 1)
        self.assertEqual(len({rs.gen_pow(i) for i in range(255)}), 255)


if __name__ == "__main__":
    unittest.main()
