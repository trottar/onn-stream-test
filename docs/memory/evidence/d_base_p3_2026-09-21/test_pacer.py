"""D-BASE-P3 offline check: the paced path must emit exactly the same
packets in exactly the same order as the unpaced path, only spaced out."""
import sys, time, threading
sys.path.insert(0, "/home/privyhub/Projects/onn-stream-test/companion")
from native_fec_relay import NativeVideoFecRelay, PACING_FRAME_BUDGET_US


class FakeSock:
    def __init__(self):
        self.sent = []
        self.times = []
        self.lock = threading.Lock()
    def sendto(self, packet, client):
        with self.lock:
            self.sent.append(bytes(packet))
            self.times.append(time.perf_counter_ns())
        return len(packet)
    def close(self):
        pass


def rtp(seq, ts, marker, payload=b"x" * 1100, ssrc=0x11223344, pt=96):
    b0 = 0x80
    b1 = (0x80 if marker else 0) | pt
    return (bytes([b0, b1]) + seq.to_bytes(2, "big") + ts.to_bytes(4, "big")
            + ssrc.to_bytes(4, "big") + payload)


def run(pacing_us, frames, pkts_per_frame):
    r = NativeVideoFecRelay(local_port=0, group_size=8, pacing_us=pacing_us)
    fake = FakeSock()
    r._send_socket = fake
    r._client = ("127.0.0.1", 1)
    r._running = True
    r.pacing_us = r._configured_pacing_us()
    if r.pacing_us > 0:
        r._pace_thread = threading.Thread(target=r._pace_run, daemon=True)
        r._pace_thread.start()
    seq = 0
    for f in range(frames):
        ts = 3000 * (f + 1)
        for i in range(pkts_per_frame):
            marker = (i == pkts_per_frame - 1)
            r._handle_rtp(rtp(seq, ts, marker))
            seq = (seq + 1) & 0xFFFF
        # real encoder emits a frame's packets back to back, then idles
        time.sleep(0.016)
    time.sleep(0.2)
    st = r.status()
    with r._lock:
        r._running = False
        r._pace_cv.notify_all()
    if r._pace_thread:
        r._pace_thread.join(timeout=1.0)
    return fake, st


FRAMES, PKTS = 8, 14
off_sock, off_st = run(0, FRAMES, PKTS)
on_sock, on_st = run(150, FRAMES, PKTS)

print("=== packet stream equivalence ===")
print("off packets:", len(off_sock.sent), " on packets:", len(on_sock.sent))
same = off_sock.sent == on_sock.sent
print("identical bytes and order:", same)
if not same:
    for i, (a, b) in enumerate(zip(off_sock.sent, on_sock.sent)):
        if a != b:
            print("  first divergence at", i, len(a), len(b)); break
    sys.exit(1)

print()
print("=== counters ===")
for k in ("rtp_packets", "parity_packets", "groups", "skipped_packets",
          "send_calls", "send_errors", "sent_bytes"):
    print(f"  {k:18s} off={off_st[k]:>8}  on={on_st[k]:>8}  "
          f"{'OK' if off_st[k] == on_st[k] else 'DIFFER'}")

print()
print("=== pacing status (on) ===")
for k, v in on_st["pacing"].items():
    print(f"  {k:28s} {v}")
print()
print("=== pacing status (off) ===")
print("  enabled:", off_st["pacing"]["enabled"],
      " paced_frames:", off_st["pacing"]["paced_frames"],
      " p50:", off_st["pacing"]["achieved_spacing_p50_us"])

# measured spacing within frames
gaps = []
t = on_sock.times
for i in range(1, len(t)):
    g = (t[i] - t[i - 1]) / 1000.0
    if g < 4000:
        gaps.append(g)
gaps.sort()
print()
print("=== achieved intra-frame spacing, measured in the test ===")
print(f"  n={len(gaps)} p50={gaps[len(gaps)//2]:.1f}us "
      f"p99={gaps[int(len(gaps)*0.99)]:.1f}us max={gaps[-1]:.1f}us")

# clamp check: a frame bigger than budget/pacing must be clamped
big_sock, big_st = run(400, 3, 40)
p = big_st["pacing"]
print()
print("=== clamp check: 40-packet frames at PACING_US=400 ===")
print("  budget/packets =", PACING_FRAME_BUDGET_US / 45.0, "us")
print("  clamped_frames =", p["clamped_frames"], " last_spacing_us =", p["last_spacing_us"])
print("  late_frames    =", p["late_frames"])
