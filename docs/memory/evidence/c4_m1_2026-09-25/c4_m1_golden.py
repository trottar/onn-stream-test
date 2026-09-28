#!/usr/bin/env python3
"""C4-M1: drive NativeVideoFecRelay._handle_rtp with synthetic RTP built from
the recorded H.264 sample (logs/games/a1_sample.h264, first 600 KB) and write
every datagram the relay emits (RTP + parity) in order. Run against the
UNMODIFIED relay to make the golden; run again after the change with the
scheme unset to prove xor8_1's bytes are unchanged, and with xor8_2 to show
the P packets are still identical and a Q packet follows each.
No sockets: `_send` is replaced by a capture. Usage:
  c4_m1_golden.py <repo root> <out.bin> [scheme]
"""
import hashlib
import os
import random
import struct
import sys

ROOT, OUT = sys.argv[1], sys.argv[2]
SCHEME = sys.argv[3] if len(sys.argv) > 3 else None
if SCHEME:
    os.environ["PRIVYHUB_FEC_SCHEME"] = SCHEME
else:
    os.environ.pop("PRIVYHUB_FEC_SCHEME", None)
os.environ.pop("PRIVYHUB_FEC_PACING_US", None)
sys.path.insert(0, os.path.join(ROOT, "companion"))
import native_fec_relay as r  # noqa: E402

relay = r.NativeVideoFecRelay(pacing_us=0)
if hasattr(relay, "_configure_scheme"):
    relay._configure_scheme()
out = []
relay._send = lambda packet, parity: out.append((bool(parity), bytes(packet)))  # noqa: E731

data = open(os.path.join(ROOT, "logs/games/a1_sample.h264"), "rb").read()[:600_000]
rng = random.Random(20260925)
pos, seq, ts, ssrc = 0, 1000, 90_000, 0x1234ABCD
frames = 0
while pos < len(data) - 20_000:
    n = rng.choice([1, 2, 3, 5, 7, 8, 9, 12, 15, 16, 17, 24, 40])
    for i in range(n):
        size = rng.randint(200, 1188)
        payload = data[pos:pos + size]
        pos += size
        marker = 0x80 if i == n - 1 else 0
        hdr = struct.pack("!BBHII", 0x80, marker | 96, seq & 0xFFFF, ts & 0xFFFFFFFF, ssrc)
        relay._handle_rtp(hdr + payload)
        seq += 1
    ts += 1500
    frames += 1
with open(OUT, "wb") as fh:
    for parity, pkt in out:
        fh.write(struct.pack("!BI", 1 if parity else 0, len(pkt)) + pkt)
par = [p for is_p, p in out if is_p]
v1 = [p for p in par if p[4] == 1]
v2 = [p for p in par if p[4] == 2]
print(f"scheme {SCHEME or 'unset'}: frames {frames}, datagrams {len(out)}, parity {len(par)} (v1 {len(v1)}, v2 {len(v2)})")
print("sha256 all        ", hashlib.sha256(open(OUT, "rb").read()).hexdigest())
print("sha256 rtp + v1   ", hashlib.sha256(b"".join(p for is_p, p in out if not is_p or p[4] == 1)).hexdigest())
