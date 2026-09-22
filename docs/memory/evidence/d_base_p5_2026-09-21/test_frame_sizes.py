#!/usr/bin/env python3
"""D-BASE-P5: the relay's frame-size counters, against synthetic RTP.

No socket, no thread, no file: `_handle_rtp` is called directly with packets
built here, so the test asserts the counting and nothing else. Run from the
repository root:

    PYTHONPATH=companion python3 docs/memory/evidence/d_base_p5_2026-09-21/test_frame_sizes.py
"""
import json
import struct
import sys
import tempfile
from pathlib import Path

from native_fec_relay import (
    FRAME_HUGE_PACKETS,
    FRAME_LARGE_PACKETS,
    NativeVideoFecRelay,
)

FAILS = []


def check(name, got, want):
    if got != want:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")
        print(f"  FAIL {name}: got {got!r}, want {want!r}")
    else:
        print(f"  ok   {name} = {got!r}")


def rtp(seq, ts, marker, payload=b"x" * 900, ssrc=0x11223344):
    byte0 = 0x80
    byte1 = 96 | (0x80 if marker else 0)
    return struct.pack("!BBHII", byte0, byte1, seq & 0xFFFF, ts, ssrc) + payload


def feed(relay, frames, ts0=1000, seq0=0):
    """frames: list of packet counts; each is emitted as one marked frame."""
    seq, ts = seq0, ts0
    for count in frames:
        for i in range(count):
            relay._handle_rtp(rtp(seq, ts, marker=(i == count - 1)))
            seq += 1
        ts += 3000
    return seq, ts


def new_relay(**kw):
    r = NativeVideoFecRelay(local_port=0, group_size=8, **kw)
    # `start()` needs a socket; the counters are reset in __init__ too, and
    # every path under test runs without the receive thread.
    return r


print("1. packets per frame are counted, and the marker ends the frame")
r = new_relay()
feed(r, [3, 17, 61, 95, 8])
s = r.frame_size_status()
check("frames", s["frames"], 5)
check("packets", s["packets"], 3 + 17 + 61 + 95 + 8)
check("max_packets", s["max_packets"], 95)
check("mean_packets", s["mean_packets"], round((3 + 17 + 61 + 95 + 8) / 5, 3))
check("frames_ge_40", s["frames_ge_40"], 2)
check("frames_ge_80", s["frames_ge_80"], 1)
check("unmarked_frames", s["unmarked_frames"], 0)
check("large_threshold", s["large_threshold"], FRAME_LARGE_PACKETS)
check("huge_threshold", s["huge_threshold"], FRAME_HUGE_PACKETS)
check("max_at_utc is set", isinstance(s["max_at_utc"], str), True)

print("2. a frame whose marker never arrives is closed and flagged")
r = new_relay()
seq, ts = 0, 5000
for i in range(12):                       # 12 packets, no marker
    r._handle_rtp(rtp(seq, ts, marker=False)); seq += 1
for i in range(4):                        # new timestamp -> closes the first
    r._handle_rtp(rtp(seq, ts + 3000, marker=(i == 3))); seq += 1
s = r.frame_size_status()
check("frames", s["frames"], 2)
check("unmarked_frames", s["unmarked_frames"], 1)
check("max_packets", s["max_packets"], 12)
check("packets", s["packets"], 16)

print("3. percentiles come off the histogram, exactly")
r = new_relay()
feed(r, [10] * 50 + [20] * 40 + [90] * 9 + [200])
s = r.frame_size_status()
check("frames", s["frames"], 100)
check("p50", s["p50_packets"], 10)
check("p90", s["p90_packets"], 20)
check("p99", s["p99_packets"], 90)
check("max", s["max_packets"], 200)

print("4. an unparseable packet is not attributed to a frame")
r = new_relay()
r._handle_rtp(b"\x00\x01")                # too short to parse
feed(r, [5])
s = r.frame_size_status()
check("frames", s["frames"], 1)
check("packets", s["packets"], 5)

print("5. buckets close by wall-clock second, and carry their own maximum")
r = new_relay()
feed(r, [4, 70])
r._roll_frame_bucket_locked()
s = r.frame_size_status()
check("one bucket", len(s["buckets"]), 1)
b = s["buckets"][0]
check("bucket frames", b["frames"], 2)
check("bucket packets", b["packets"], 74)
check("bucket max", b["max_packets"], 70)
check("bucket ge_40", b["frames_ge_40"], 1)
check("bucket ge_80", b["frames_ge_80"], 0)
check("bucket mean", b["mean_packets"], 37.0)
check("bucket max_at_utc", isinstance(b["max_at_utc"], str), True)

print("6. the ring is bounded at FRAME_BUCKET_SECONDS")
from native_fec_relay import FRAME_BUCKET_SECONDS
r = new_relay()
for n in range(FRAME_BUCKET_SECONDS + 25):
    r._frame_buckets.append({"t": n})
check("ring length", len(r._frame_buckets), FRAME_BUCKET_SECONDS)
check("oldest dropped", r._frame_buckets[0]["t"], 25)

print("7. the log writes one JSON line per closed bucket")
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "native_frame_sizes.jsonl"
    r = new_relay(frame_size_log=path)
    feed(r, [6, 44])
    r._roll_frame_bucket_locked()
    r._flush_frame_log()
    lines = path.read_text().strip().splitlines()
    check("lines", len(lines), 1)
    rec = json.loads(lines[0])
    check("schema", rec["schema"], "privyhub_native_frame_sizes_v1")
    check("logged frames", rec["frames"], 2)
    check("logged max", rec["max_packets"], 44)
    check("logged ge_40", rec["frames_ge_40"], 1)
    check("at_utc present", isinstance(rec["at_utc"], str), True)
    check("log_lines counter", r.frame_size_status()["log_lines"], 1)

print("8. with no log path the counters still work and nothing is written")
r = new_relay()
feed(r, [9])
check("frames", r.frame_size_status()["frames"], 1)
check("log_path", r.frame_size_status()["log_path"], None)
check("log_lines", r.frame_size_status()["log_lines"], 0)

print("9. forwarding is untouched: pacing stays off and off is the old path")
r = new_relay()
check("pacing_us", r.pacing_us, 0)
check("pacing enabled", r.frame_size_status() is not None, True)

print()
if FAILS:
    print(f"FAILED: {len(FAILS)}")
    for f in FAILS:
        print("  " + f)
    sys.exit(1)
print("ALL CHECKS PASSED")
