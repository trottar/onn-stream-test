#!/usr/bin/env python3
"""G8-S4: the encodes through the shim's cap profiles, in process (G8-S2's harness).

    PYTHONDONTWRITEBYTECODE=1 python3 -I docs/memory/evidence/g8_s4_2026-10-18/shim_proof.py <scratch_dir>

Each case: the per-frame sizes and pts of one encode_proof.py encode (`frames_<T>_<profile>.json`
in <scratch_dir>), packetized at 1,188 B with the marker on each frame's last packet -> the REAL
FEC sender (`NativeVideoFecRelay`, its default pacing) -> the shim @post-fec (G8-S2's injection:
`RelayShim` with no log file, so nothing reaches the repo's logs/) -> a loopback capture. Loopback
ephemeral ports only, never the companion's. 60 s each, in real time.

Cells: 5000 under cap-6000 and 4000 under cap-4500, each flag absent / tight / headroom.
Reported: the shim's input, the tail-dropped fraction overall and per second (median, p95, max),
the share of seconds with any drop, FEC-recovered / unrecoverable groups, packets lost after FEC,
complete frames. **No claim about PLAYING or the picture.**
Writes shim_proof.json next to this script.
"""

from __future__ import annotations

import importlib.util
import json
import statistics
import struct
import sys
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "companion"))

spec = importlib.util.spec_from_file_location("g8_s2_cap_proof", REPO / "docs/memory/evidence/g8_s2_2026-10-17/cap_proof.py")
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)
imp, relay_mod = cp.imp, cp.relay_mod

CELLS = ((5000, "cap-6000"), (4000, "cap-4500"))
PROFILES = ("absent", "tight", "headroom")


def run_case(cap_profile: str, frames: list[tuple[float, int]]) -> dict:
    packets, seq_frame, n_pkts = cp.packetize(frames)
    cap = cp.Capture()
    spec_ = f"{cap_profile}@post-fec"
    shims = []

    def relay_shim(environ, relay_port, client, root):
        rs = imp.RelayShim(imp.parse(spec_), relay_port, client, None)
        shims.append(rs)
        return rs

    saved = relay_mod._impairment
    relay_mod._impairment = types.SimpleNamespace(relay_shim_from_environ=relay_shim, PRE_FEC=imp.PRE_FEC)
    try:
        r = relay_mod.NativeVideoFecRelay(local_port=0)
        r.start(cp.LOOP, cap.port)
        cp.send((cp.LOOP, r._recv_socket.getsockname()[1]), packets)
        time.sleep(0.6)
        lines = list(shims[0].shim.lines)
        counters = shims[0].shim.counters()
        r.stop()
    finally:
        relay_mod._impairment = saved
    got = cap.finish()
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
        group = list(range(base, base + n)) if base + n <= 65536 else []
        miss = [s for s in group if s not in rtp]
        if len(miss) == 1:
            rec_g += 1
            have.add(miss[0])
        elif len(miss) > 1:
            unrec_g += 1
    lost = [s for s in range(n_pkts) if s not in have]
    frame_ok = [True] * len(frames)
    for s in lost:
        frame_ok[seq_frame[s]] = False
    per = [l["dropped_queue"] / l["packets_in"] for l in lines if l["packets_in"] > 0]
    srt = sorted(per)
    return {
        "seconds": len(per),
        "shim_in_kbps_mean": round(sum(l["bytes_in"] for l in lines) * 8 / max(1, len(lines)) / 1000, 1),
        "shim_in_kbps_p95": round(sorted(l["bytes_in"] * 8 / 1000 for l in lines)[int(0.95 * (len(lines) - 1))], 1),
        "tail_dropped_fraction": round(counters["dropped_queue"] / max(1, counters["packets_in"]), 4),
        "per_second_drop_median": round(statistics.median(per), 4),
        "per_second_drop_p95": round(srt[int(round(0.95 * (len(srt) - 1)))], 4),
        "per_second_drop_max": round(max(per), 4),
        "share_seconds_with_drop": round(sum(1 for x in per if x > 0) / len(per), 4),
        "queue_max": counters["queue_max"], "packets_in": counters["packets_in"],
        "fec_recovered_groups": rec_g, "fec_unrecoverable_groups": unrec_g,
        "lost_after_fec": len(lost), "complete_frames_fraction": round(sum(frame_ok) / len(frames), 4),
    }


def main(scratch: Path) -> int:
    out: dict = {}
    for target, cap in CELLS:
        for profile in PROFILES:
            rows = json.loads((scratch / f"frames_{target}_{profile}.json").read_text())
            frames = [(float(t), int(s)) for t, s in rows if 0 <= float(t) < 60]
            r = run_case(cap, frames)
            out[f"{target}|{cap}|{profile}"] = r
            print(target, cap, profile, json.dumps(r), flush=True)
    (HERE / "shim_proof.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
