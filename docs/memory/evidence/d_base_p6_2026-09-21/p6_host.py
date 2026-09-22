#!/usr/bin/env python3
"""D-BASE-P6: encoder CPU and GPU power per arm, from the T1 sampler.

A tighter rate control can cost encoder time, so the arms are compared on
`procs.encoder.cpu_pct` and `hwmon.amdgpu.power1_w` as well as on loss.
The companion starts `tools/host_resource_sampler.py` with every native
stream session, so this costs the run nothing -- it only slices what is
already on disk by each arm's session window.

usage: p6_host.py <scratch_dir>   (reads <scratch>/index.txt for windows)
"""
import json
import os
import statistics as st
import sys

SAMPLES = ("/home/privyhub/Projects/onn-stream-test"
           "/logs/games/host_resource_samples.jsonl")


def main():
    scratch = sys.argv[1]
    idx = os.path.join(scratch, "index.txt")
    if not os.path.exists(idx):
        print("no index.txt")
        return

    arms = []
    for line in open(idx):
        p = line.split()
        if len(p) >= 5:
            arms.append((p[0], p[3], p[4]))

    rows = []
    for line in open(SAMPLES, errors="replace"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

    print("%-9s %7s  %-18s %-18s %-16s" % (
        "arm", "samples", "encoder cpu_pct", "retroarch cpu_pct",
        "amdgpu power W"))
    out = {}
    for arm, t0, t1 in arms:
        sel = [r for r in rows if t0 <= r.get("at_utc", "") <= t1]

        def series(path):
            vals = []
            for r in sel:
                node = r
                for key in path:
                    node = (node or {}).get(key) if isinstance(node, dict) else None
                if isinstance(node, (int, float)):
                    vals.append(float(node))
            return vals

        enc = series(("procs", "encoder", "cpu_pct"))
        ra = series(("procs", "retroarch", "cpu_pct"))
        gpu = series(("hwmon", "amdgpu", "power1_w"))
        tctl = series(("hwmon", "k10temp", "Tctl_c"))

        def fmt(v):
            if not v:
                return "-"
            return "%.1f (%.1f-%.1f)" % (st.median(v), min(v), max(v))

        print("%-9s %7d  %-18s %-18s %-16s" % (
            arm, len(sel), fmt(enc), fmt(ra), fmt(gpu)))
        out[arm] = {
            "samples": len(sel),
            "encoder_cpu_pct_median": round(st.median(enc), 2) if enc else None,
            "encoder_cpu_pct_range": [min(enc), max(enc)] if enc else None,
            "retroarch_cpu_pct_median": round(st.median(ra), 2) if ra else None,
            "amdgpu_power_w_median": round(st.median(gpu), 2) if gpu else None,
            "amdgpu_power_w_range": [min(gpu), max(gpu)] if gpu else None,
            "k10temp_c_median": round(st.median(tctl), 2) if tctl else None,
        }

    with open(os.path.join(scratch, "p6_host.json"), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
