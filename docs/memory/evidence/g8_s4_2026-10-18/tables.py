#!/usr/bin/env python3
"""G8-S4: the record's tables from encode_proof.json, shim_proof.json, quality_content.json and the
per-frame files in <scratch_dir>. Read only. Writes tables.md next to this script.

    python3 -I docs/memory/evidence/g8_s4_2026-10-18/tables.py <scratch_dir>
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def busy_stats(rows, target, start=12):
    b: dict[int, int] = {}
    for t, s in rows:
        b[int(t)] = b.get(int(t), 0) + s
    kb = [b[k] * 8 / 1000 for k in sorted(b) if start <= k < 60]
    srt = sorted(kb)
    p95 = srt[min(len(srt) - 1, int(round(0.95 * (len(srt) - 1))))]
    return {"n": len(kb), "mean": statistics.fmean(kb), "p95": p95, "max": max(kb),
            "over": sum(1 for x in kb if x > target) / len(kb), "over110": sum(1 for x in kb if x > 1.1 * target) / len(kb)}


def main(scratch: Path) -> int:
    enc = json.loads((HERE / "encode_proof.json").read_text())
    shim = json.loads((HERE / "shim_proof.json").read_text())
    qc = json.loads((HERE / "quality_content.json").read_text())
    L = ["# G8-S4 tables", "", "## Per-second output (kbit/s), 60 s, `reference.mkv`", "",
         "| target | profile | mean | p95 | max | over T | over 1.10 T | p95/mean | max/mean | largest frame (B) | "
         "busy s 12-59: mean / p95 / max / over T / over 1.10 T |",
         "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for t in (4000, 5000, 7000):
        for p in ("absent", "tight", "headroom"):
            e = enc["encodes"][f"{t}|{p}"]
            rows = json.loads((scratch / f"frames_{t}_{p}.json").read_text())
            bs = busy_stats(rows, t)
            L.append(f"| {t} | {p} | {e['mean']:,.0f} | {e['p95']:,.0f} | {e['max']:,.0f} | "
                     f"{100 * e['share_over_target']:.1f} % | {100 * e['share_over_1_10']:.1f} % | {e['p95_over_mean']} | "
                     f"{e['max_over_mean']} | {e['largest_frame_bytes']:,} | {bs['mean']:,.0f} / {bs['p95']:,.0f} / "
                     f"{bs['max']:,.0f} / {100 * bs['over']:.0f} % / {100 * bs['over110']:.0f} % |")
    L += ["", "## Through the shim (real FEC sender -> RelayShim @post-fec), 60 s each", "",
          "| cell | profile | shim in mean / p95 (kbit/s) | tail-dropped | per-second drop median / p95 / max | "
          "seconds with a drop | lost after FEC | complete frames |", "| --- | --- | --- | ---: | --- | ---: | ---: | ---: |"]
    for t, cap in ((5000, "cap-6000"), (4000, "cap-4500")):
        for p in ("absent", "tight", "headroom"):
            s = shim[f"{t}|{cap}|{p}"]
            L.append(f"| {t} @ {cap} | {p} | {s['shim_in_kbps_mean']:,.0f} / {s['shim_in_kbps_p95']:,.0f} | "
                     f"{100 * s['tail_dropped_fraction']:.2f} % | {100 * s['per_second_drop_median']:.2f} / "
                     f"{100 * s['per_second_drop_p95']:.2f} / {100 * s['per_second_drop_max']:.2f} % | "
                     f"{100 * s['share_seconds_with_drop']:.0f} % | {s['lost_after_fec']:,} | "
                     f"{100 * s['complete_frames_fraction']:.1f} % |")
    L += ["", "## Picture (PSNR dB avg / min, SSIM All): whole frame and content area (876x720)", "",
          "| target | profile | vs reference, whole | vs reference, content | vs flag absent, whole | vs flag absent, content |",
          "| ---: | --- | --- | --- | --- | --- |"]
    f = lambda q: f"{q['psnr_avg_db']:.2f} / {q['psnr_min_db']:.2f} / {q['ssim_all']:.4f}" if q else "—"
    for t in (4000, 5000, 7000):
        for p in ("absent", "tight", "headroom"):
            w = enc["quality"][f"{t}|{p}"]
            c = qc[f"{t}|{p}"]
            L.append(f"| {t} | {p} | {f(w['vs_reference'])} | {f(c['vs_reference'])} | {f(w.get('vs_absent'))} | "
                     f"{f(c.get('vs_absent'))} |")
    b = enc["baseline"]
    L += ["", "## Host CPU (ffmpeg process, user + sys, s, 60 s of video)", "",
          f"Decode-only baseline (same input and filter, no hwupload / encode): {b['cpu_user_s'] + b['cpu_sys_s']:.2f} s.", "",
          "| target | absent | tight | headroom |", "| ---: | ---: | ---: | ---: |"]
    for t in (4000, 5000, 7000):
        L.append(f"| {t} | " + " | ".join(f"{enc['encodes'][f'{t}|{p}']['cpu_s']:.2f} "
                                         f"({enc['encodes'][f'{t}|{p}']['cpu_over_baseline_s']:+.2f})"
                                         for p in ("absent", "tight", "headroom")) + " |")
    (HERE / "tables.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
