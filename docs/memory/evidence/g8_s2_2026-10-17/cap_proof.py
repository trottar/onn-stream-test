#!/usr/bin/env python3
"""G8-S2: the start rung against the shim's cap profiles, in process (G8-P1's proof extended).

    PYTHONDONTWRITEBYTECODE=1 python3 docs/memory/evidence/g8_s2_2026-10-17/cap_proof.py [out_dir]

Loopback only; no stream; no companion; nothing written outside out_dir and the system temp
directory. Each case: a source of H.264-shaped RTP (frames at 60 fps, packets of <= 1200 B, the
marker on each frame's last packet) -> the REAL FEC sender (`native_fec_relay.NativeVideoFecRelay`,
its default pacing, as the companion builds it) -> the shim `cap-6000` / `cap-4500` @post-fec
(G8-S1's placement; given to the relay directly, with no log file -- the environment route would
append to the repo's logs/impairment.jsonl) -> a capture playing the client.

Sources, at a start rung r (7000 / 5000 / 4000):
- `synthetic`: every frame r / 7000 x 14,615 B (the real encoder's 876,900 B/s at 7000 / 60).
- `recorded:<file>@<start>`: the real encoder's recorded stream start, from the evidence tree's
  per-second frame-size log (`privyhub_native_frame_sizes_v1`: frames, payload bytes, the largest
  frame and its instant). Re-timed into frames: the largest at its recorded instant, the rest evenly
  sized; a partial first second's frames at its end. Scaled by r / 7000 (the encoder is CBR) --
  an assumption. The logs hold no per-frame series.

Per case: the shim's input / output kbps and tail-dropped fraction (whole run and steady, after
2.5 s, as G8-S1 §5 reads it), FEC recovered / unrecoverable groups, packets lost after FEC, complete
frames, and G5-S1's window classes over 2-s reports. **No claim about PLAYING.**
"""

from __future__ import annotations

import ipaddress
import json
import math
import os
import socket
import struct
import sys
import threading
import time
import types
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "companion"))

import impairment as imp  # noqa: E402
import native_fec_relay as relay_mod  # noqa: E402
import wan_telemetry as wt  # noqa: E402

LOOP = str(ipaddress.ip_address(0x7F000001))
FPS = 60
PAYLOAD = 1188                       # 1200-B RTP packets (pkt_size=1200), 12-B header
BYTES_PER_FRAME_7000 = 876_900 / 60  # the real encoder at 7000 (c3_l4 nft nights, every full second)
SECONDS = int(os.environ.get("G8_S2_SECONDS", "30"))
EVID = REPO / "docs/memory/evidence"
RECORDED = [("c3_l4_nft_night3_2026-09-30/frames.jsonl", "2026-09-30T13:15:23.000Z"),
            ("c3_l4_nft_night1_2026-09-29/frames.jsonl", "2026-09-29T15:20:34.000Z")]


def ep(t: str) -> float:
    return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()


# ---------------------------------------------------------------- frames ---
def synthetic_frames(rung: int, seconds: int) -> list[tuple[float, int]]:
    b = int(round(BYTES_PER_FRAME_7000 * rung / 7000))
    return [(f / FPS, b) for f in range(FPS * seconds)]


def recorded_frames(rel: str, start: str, rung: int, seconds: int) -> list[tuple[float, int]]:
    rows = [json.loads(l) for l in (EVID / rel).read_text().splitlines() if l.strip().startswith("{")]
    i0 = next(i for i, r in enumerate(rows) if r["at_utc"] == start)
    out: list[tuple[float, int]] = []
    scale = rung / 7000
    for k, r in enumerate(rows[i0:i0 + seconds]):
        n = int(r["frames"])
        if n <= 0:
            continue
        mb, pb = int(r.get("max_bytes") or 0), int(r.get("payload_bytes") or 0)
        rest = (pb - mb) / (n - 1) if n > 1 else 0
        at_max = ep(r["max_bytes_at_utc"]) - ep(r["at_utc"]) if r.get("max_bytes_at_utc") else 0.0
        first_slot = 60 - n if k == 0 else 0           # a partial first second: its frames at its end
        slots = [first_slot + j for j in range(n)]
        jmax = min(range(n), key=lambda j: abs(slots[j] / 60 - at_max))
        for j, s in enumerate(slots):
            b = mb if j == jmax else rest
            out.append((k + s / 60, max(1, int(round(b * scale)))))
    return out


def packetize(frames):
    """[(t, frame_bytes)] -> [(t, [payload sizes])], and the frame of each sequence number."""
    out, seq_frame, seq = [], {}, 0
    for f, (t, b) in enumerate(frames):
        n = max(1, math.ceil(b / PAYLOAD))
        sizes = [PAYLOAD] * (n - 1) + [b - PAYLOAD * (n - 1)]
        out.append((t, sizes))
        for _ in sizes:
            seq_frame[seq] = f
            seq += 1
    return out, seq_frame, seq


# ---------------------------------------------------------------- the run ---
class Capture:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 * 1024 * 1024)
        self.sock.bind((LOOP, 0))
        self.sock.settimeout(0.2)
        self.got: list[bytes] = []
        self.done = threading.Event()
        self.t = threading.Thread(target=self._run, daemon=True)
        self.t.start()

    @property
    def port(self):
        return self.sock.getsockname()[1]

    def _run(self):
        idle = 0
        while not self.done.is_set() or idle < 5:
            try:
                self.got.append(self.sock.recv(65535))
                idle = 0
            except socket.timeout:
                idle += 1

    def finish(self):
        self.done.set()
        self.t.join(timeout=10)
        self.sock.close()
        return self.got


def send(target, packets):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8 * 1024 * 1024)
    seq, t0 = 0, time.perf_counter()
    for f, (t, sizes) in enumerate(packets):
        due = t0 + t
        while True:
            d = due - time.perf_counter()
            if d <= 0:
                break
            time.sleep(min(d, 0.002))
        for k, n in enumerate(sizes):
            hdr = struct.pack("!BBHII", 0x80, (0x80 if k == len(sizes) - 1 else 0) | 96, seq & 0xFFFF, f * 1500,
                              0x1234ABCD)
            s.sendto(hdr + struct.pack("!I", seq) + bytes(max(0, n - 4)), target)
            seq += 1
    s.close()


def run_case(cap_profile: str, frames) -> dict:
    packets, seq_frame, n_pkts = packetize(frames)
    cap = Capture()
    spec = f"{cap_profile}@post-fec"
    shims = []

    def relay_shim(environ, relay_port, client, root):        # the shim, without the repo's log file
        rs = imp.RelayShim(imp.parse(spec), relay_port, client, None)
        shims.append(rs)
        return rs
    saved = relay_mod._impairment
    relay_mod._impairment = types.SimpleNamespace(relay_shim_from_environ=relay_shim, PRE_FEC=imp.PRE_FEC)
    try:
        r = relay_mod.NativeVideoFecRelay(local_port=0)
        r.start(LOOP, cap.port)
        send((LOOP, r._recv_socket.getsockname()[1]), packets)
        time.sleep(0.6)
        lines = list(shims[0].shim.lines)
        counters = shims[0].shim.counters()
        r.stop()
    finally:
        relay_mod._impairment = saved
    got = cap.finish()
    # the client's view
    rtp, parity = set(), []
    for d in got:
        if d[:4] == relay_mod.FEC_MAGIC:
            h = relay_mod.FEC_HEADER.unpack(d[:relay_mod.FEC_HEADER.size])
            parity.append((h[3], h[2]))
        elif len(d) >= 16:
            rtp.add(struct.unpack("!I", d[12:16])[0])
    have = set(rtp)
    rec_g = unrec_g = 0
    for base, n in parity:
        group = [s for s in range(base, base + n)] if base + n <= 65536 else []
        miss = [s for s in group if s not in rtp]
        if len(miss) == 1:
            rec_g += 1
            have.add(miss[0])
        elif len(miss) > 1:
            unrec_g += 1
    lost = [s for s in range(n_pkts) if s not in have]
    lost_set = set(lost)
    n_frames = len(frames)
    frame_ok = [True] * n_frames
    for s in lost:
        frame_ok[seq_frame[s]] = False
    pk_per_frame = [len(sz) for _, sz in packets]
    reports, per = [], 2 * FPS
    for r0 in range(0, n_frames, per):
        fr = range(r0, min(r0 + per, n_frames))
        lost_n = sum(1 for s in lost if r0 <= seq_frame[s] < r0 + per)
        reports.append(wt.Report(elapsed_ms=(r0 // per + 1) * 2000, fps=sum(frame_ok[f] for f in fr) / 2.0, queue=0,
                                 gap_ms=16, lost=lost_n, packets=sum(pk_per_frame[f] for f in fr), mbps=None,
                                 jitter_ms=None, rtt_ms=None, stale=0, waiting_for_idr=False, queue_delta=0))
    classes: dict[str, int] = {}
    for i in range(0, len(reports) - 4, 5):
        c = wt.classify_window(reports[i:i + 5], [])["primary"]
        classes[c] = classes.get(c, 0) + 1
    steady = [l for l in lines if l["t_s"] > 2.5]
    s_in = sum(l["packets_in"] for l in steady)
    s_drop = sum(l["dropped_queue"] for l in steady)
    secs = max(1, len(steady))
    return {
        "frames": n_frames, "rtp_packets": n_pkts,
        "shim_in_kbps_steady": round(sum(l["bytes_in"] for l in steady) * 8 / secs / 1000, 1),
        "shim_out_kbps_steady": round(sum(l["bytes_out"] for l in steady) * 8 / secs / 1000, 1),
        "tail_dropped_fraction_steady": round(s_drop / s_in, 4) if s_in else None,
        "tail_dropped_fraction_all": round(counters["dropped_queue"] / max(1, counters["packets_in"]), 4),
        "queue_max": counters["queue_max"], "send_errors": counters["send_errors"],
        "fec_groups": len(parity), "fec_recovered_groups": rec_g, "fec_unrecoverable_groups": unrec_g,
        "lost_after_fec": len(lost), "lost_after_fec_per_min": round(len(lost) * 60 / (n_frames / FPS), 1),
        "complete_frames_fraction": round(sum(frame_ok) / n_frames, 4),
        "first_incomplete_frame_s": (round(frame_ok.index(False) / FPS, 2) if False in frame_ok else None),
        "g5_s1_window_classes": classes,
    }


def main(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    sources = [("synthetic", lambda r: synthetic_frames(r, SECONDS))] + [
        (f"recorded {rel.split('/')[0]} @ {start[11:19]}Z", (lambda rel, start: lambda r: recorded_frames(
            rel, start, r, SECONDS))(rel, start)) for rel, start in RECORDED]
    res = {}
    for cap_p in ("cap-6000", "cap-4500"):
        for rung in (7000, 5000, 4000):
            for name, mk in sources:
                m = run_case(cap_p, mk(rung))
                res[f"{cap_p} / start {rung} / {name}"] = m
                print(cap_p, rung, name, json.dumps(m), flush=True)
    lines = ["# G8-S2 cap proof — the start rung against the shim's cap profiles (in process; no claim about PLAYING)",
             "", f"{SECONDS} s per case; the real FEC sender (default pacing) -> the shim @post-fec -> a capture "
             "playing the client. Predictions (design §4, written before): drop ≈ 1 − cap / (1.179 × rung) "
             "when above the cap.", "",
             "| cap | start | source | shim in kbps (steady) | out kbps | predicted drop | tail-dropped (steady / all) "
             "| FEC recovered / unrecoverable groups | lost after FEC /min | complete frames | first incomplete at | "
             "G5-S1 windows |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for k, m in res.items():
        cap_p, start, name = k.split(" / ")
        c = int(cap_p.split("-")[1])
        r = int(start.split()[1])
        pred = max(0.0, 1 - c / (8.25 * r / 7000 * 1000))
        lines.append(f"| {cap_p} | {r} | {name} | {m['shim_in_kbps_steady']} | {m['shim_out_kbps_steady']} | "
                     f"{100 * pred:.1f} % | {100 * (m['tail_dropped_fraction_steady'] or 0):.1f} % / "
                     f"{100 * m['tail_dropped_fraction_all']:.1f} % | {m['fec_recovered_groups']} / "
                     f"{m['fec_unrecoverable_groups']} | {m['lost_after_fec_per_min']} | "
                     f"{100 * m['complete_frames_fraction']:.1f} % | {m['first_incomplete_frame_s']} | "
                     f"{', '.join(f'{a} {b}' for a, b in sorted(m['g5_s1_window_classes'].items()))} |")
    (out_dir / "cap_proof_tables.md").write_text("\n".join(lines) + "\n")
    (out_dir / "cap_proof.json").write_text(json.dumps(res, indent=1) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE))
