#!/usr/bin/env python3
"""D-BASE-P6: the relay's per-frame BYTE counters, against synthetic RTP.

Extends `d_base_p5_2026-09-21/test_frame_sizes.py`, which still covers the
packet side. Run from the repository root:

    PYTHONPATH=companion python3 \
      docs/memory/evidence/d_base_p6_2026-09-21/test_frame_bytes.py
"""
import os
import struct
import sys

from native_fec_relay import (
    FRAME_BYTE_BUCKET,
    FRAME_BYTE_CAP_ENV,
    NativeVideoFecRelay,
)

FAILS = []


def check(name, got, want):
    if got != want:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")
        print(f"  FAIL {name}: got {got!r}, want {want!r}")
    else:
        print(f"  ok   {name} = {got!r}")


def rtp(seq, ts, marker, payload_len=1188, ssrc=0x11223344):
    byte0 = 0x80
    byte1 = 96 | (0x80 if marker else 0)
    return (
        struct.pack("!BBHII", byte0, byte1, seq & 0xFFFF, ts, ssrc)
        + b"x" * payload_len
    )


def feed(relay, frames, payload_len=1188, ts0=1000, seq0=0):
    seq, ts = seq0, ts0
    for count in frames:
        for i in range(count):
            relay._handle_rtp(
                rtp(seq, ts, marker=(i == count - 1), payload_len=payload_len)
            )
            seq += 1
        ts += 3000
    return seq, ts


def new_relay():
    return NativeVideoFecRelay(local_port=0, group_size=8)


print("1. payload bytes are summed per frame, headers excluded")
r = new_relay()
feed(r, [10], payload_len=1000)
s = r.frame_size_status()
check("frames", s["frames"], 1)
check("packets", s["packets"], 10)
check("payload_bytes", s["payload_bytes"], 10_000)
check("max_bytes", s["max_bytes"], 10_000)
check("bytes_per_packet", s["bytes_per_packet"], 1000.0)
check("max_bytes_at_utc set", isinstance(s["max_bytes_at_utc"], str), True)

print("2. the RTP header is not counted (12 bytes/packet)")
r = new_relay()
feed(r, [5], payload_len=1188)
s = r.frame_size_status()
check("payload_bytes", s["payload_bytes"], 5 * 1188)
check("not header-inclusive", s["payload_bytes"] != 5 * 1200, True)

print("3. byte percentiles are the UPPER EDGE of a 1 KiB bucket")
r = new_relay()
# 90 frames of 1,000 B, 9 of 50,000 B, 1 of 200,000 B.
# Sorted, frames 1-90 are the small ones, so the 90th percentile frame is
# still a 1,000 B frame (bucket 0, upper edge 1,024) -- the percentile is
# of the FRAME POPULATION, not of the byte range.
feed(r, [1] * 90, payload_len=1000)
feed(r, [50] * 9, payload_len=1000, ts0=900_000)
feed(r, [200], payload_len=1000, ts0=2_000_000)
s = r.frame_size_status()
check("frames", s["frames"], 100)
check("p50_bytes", s["p50_bytes"], 1 * FRAME_BYTE_BUCKET)
check("p90_bytes", s["p90_bytes"], 1 * FRAME_BYTE_BUCKET)
check("p99_bytes", s["p99_bytes"], 49 * FRAME_BYTE_BUCKET)
check("max_bytes", s["max_bytes"], 200_000)

# and one more frame tips p99 into the 200 KB bucket
feed(r, [200], payload_len=1000, ts0=3_000_000)
check("p99_bytes after", r.frame_size_status()["p99_bytes"],
      196 * FRAME_BYTE_BUCKET)

print("4. no cap set -> frames_over_cap stays 0 and byte_cap is None")
r = new_relay()
feed(r, [200], payload_len=1000)
s = r.frame_size_status()
check("byte_cap", s["byte_cap"], None)
check("frames_over_cap", s["frames_over_cap"], 0)

print("5. a cap counts only the frames above it, per second and per session")
os.environ[FRAME_BYTE_CAP_ENV] = "40000"
r = new_relay()
feed(r, [10, 50, 200, 30], payload_len=1000)   # 10k, 50k, 200k, 30k
s = r.frame_size_status()
check("byte_cap", s["byte_cap"], 40_000)
check("frames_over_cap", s["frames_over_cap"], 2)
r._roll_frame_bucket_locked()
b = r.frame_size_status()["buckets"][0]
check("bucket frames_over_cap", b["frames_over_cap"], 2)
check("bucket payload_bytes", b["payload_bytes"], 290_000)
check("bucket max_bytes", b["max_bytes"], 200_000)
check("bucket mean_bytes", b["mean_bytes"], 72_500)
del os.environ[FRAME_BYTE_CAP_ENV]

print("6. a malformed cap reads as no cap, it does not raise")
os.environ[FRAME_BYTE_CAP_ENV] = "forty thousand"
r = new_relay()
feed(r, [200], payload_len=1000)
check("byte_cap", r.frame_size_status()["byte_cap"], None)
del os.environ[FRAME_BYTE_CAP_ENV]

print("7. the byte histogram is bounded and overflows into its last bucket")
r = new_relay()
feed(r, [400], payload_len=1000)        # 400 KB, past the 256 KiB range
s = r.frame_size_status()
check("overflow bucket used", s["byte_histogram"][-1], 1)
check("max_bytes still exact", s["max_bytes"], 400_000)

print("8. the packet counters from P5 are untouched")
r = new_relay()
feed(r, [3, 44, 95], payload_len=1188)
s = r.frame_size_status()
check("frames", s["frames"], 3)
check("p50_packets", s["p50_packets"], 44)
check("max_packets", s["max_packets"], 95)
check("frames_ge_40", s["frames_ge_40"], 2)
check("frames_ge_80", s["frames_ge_80"], 1)

print()
if FAILS:
    print(f"FAILED: {len(FAILS)}")
    for f in FAILS:
        print("  " + f)
    sys.exit(1)
print("ALL CHECKS PASSED")
