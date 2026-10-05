#!/usr/bin/env python3
"""E1-S1 -- the per-workload host table (window means, run 1 / run 2) from runs/*/run*/summary.json. Read-only."""
import collections, glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "runs")
keys = ["cpu.mean_pct", "cpu.max_pct", "psi_ms_per_s.cpu_some", "gpu.busy_pct", "gpu.vcn_activity_pct", "gpu.socket_power_w",
        "gpu.cpu_power_w", "gpu.soc_power_w", "gpu.tctl_c", "gpu.t_core_max_c", "freq.cpu_mhz_mean", "mem.used_mb",
        "mem.swap_used_mb", "disk.write_kBps", "disk.await_ms", "net.eno1.tx_kBps", "net.eno1.rx_kBps",
        "procs.companion.cpu_pct", "procs.companion.pss_kb", "procs.retroarch.cpu_pct", "procs.retroarch.pss_kb",
        "procs.encoder.cpu_pct", "procs.encoder.pss_kb", "procs.ffmpeg_other.cpu_pct", "procs.epg.cpu_pct",
        "procs.epg.pss_kb", "procs.xorg.cpu_pct", "procs.pulseaudio.cpu_pct", "procs.e1_sampler.cpu_pct",
        "procs.other.cpu_pct", "cost_ms"]
W = ["E1-IDLE", "E1-PS1-LOCAL", "E1-SNES-STREAM", "E1-PS1-STREAM", "E1-PS1-1080P", "E1-META", "E1-CONC"]
D = {(w, r): json.load(open(f"{R}/{w}/run{r}/summary.json")) for w in W for r in (1, 2)}
f = lambda v: "-" if v is None else (f"{v:.0f}" if abs(v) >= 100 else f"{v:.1f}")
print("window means, run 1 / run 2".ljust(30) + "".join(w[3:].ljust(15) for w in W))
for k in keys + ["throttled_samples"]:
    row = k.ljust(30)
    for w in W:
        v = []
        for r in (1, 2):
            if k == "throttled_samples":
                v.append(D[(w, r)]["host"]["throttled_samples"])
            else:
                x = D[(w, r)]["host"]["host"].get(k)
                v.append(x["mean"] if x else None)
        row += (f(v[0]) + "/" + f(v[1])).ljust(15)
    print(row)
print("\nthrottle_status values (count of 1-s samples, nonzero only):")
for p in sorted(glob.glob(f"{R}/*/run*/samples.jsonl")):
    c = collections.Counter(json.loads(l)["gpu"].get("throttle_status") for l in open(p))
    c.pop(0, None)
    if c:
        print(" ", os.path.relpath(p, R), {hex(a): b for a, b in c.items()})
print("\nstream key figures (window):")
for w in ["E1-SNES-STREAM", "E1-PS1-STREAM", "E1-PS1-1080P", "E1-CONC"]:
    for r in (1, 2):
        k = D[(w, r)]["key"]
        print(f"  {w} run{r}: heartbeat {k['heartbeat']}\n      telemetry {k['telemetry']}\n      status {k['status_poll']}")
