#!/usr/bin/env python3
"""CL-B2 close: the host-CPU split and the rung mix per PS1-STREAM run, read from the run files only.

Per run: host CPU mean, the per-process means (% of one core) from sampler_summary.json, the ladder's
bitrate_kbps as polled (status_poll.jsonl) and the ladder's acted decisions (decisions.jsonl).
E4-S1's PS1-STREAM run (the 10.9 % reference) is read the same way. Writes cl_b2_cpu_split.json.
"""
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = {
    "R1 runs/E1-PS1-STREAM/run1": os.path.join(HERE, "runs/E1-PS1-STREAM/run1"),
    "R2 runs/E1-PS1-STREAM_flag/run1": os.path.join(HERE, "runs/E1-PS1-STREAM_flag/run1"),
    "R3 runs/E1-PS1-STREAM/run2": os.path.join(HERE, "runs/E1-PS1-STREAM/run2"),
    "E4-S1 reference e4_s1_2026-10-09/runs/E1-PS1-STREAM/run1": os.path.join(
        HERE, "..", "e4_s1_2026-10-09/runs/E1-PS1-STREAM/run1"),
}
PROCS = ("companion", "retroarch", "encoder", "xorg", "pulseaudio", "ffmpeg_other", "other")


def one(d):
    s = json.load(open(os.path.join(d, "sampler_summary.json")))["host"]  # flat dotted keys
    out = {"host_cpu_mean_pct": s["cpu.mean_pct"]["mean"],
           "cpu_mhz_mean": s["freq.cpu_mhz_mean"]["mean"],
           "gpu_busy_pct_mean": s["gpu.busy_pct"]["mean"],
           "procs_cpu_pct_of_core": {p: s["procs.%s.cpu_pct" % p]["mean"] for p in PROCS
                                     if "procs.%s.cpu_pct" % p in s}}
    enc = s["procs.encoder.cpu_pct"]
    out["encoder_cpu_pct_range"] = [enc["min"], enc["max"]]
    rungs = Counter()
    for line in open(os.path.join(d, "status_poll.jsonl")):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r.get("bitrate_kbps"), (int, float)):
            rungs[int(r["bitrate_kbps"])] += 1
    out["status_poll_bitrate_kbps"] = {str(k): v for k, v in sorted(rungs.items())}
    acts = []
    for line in open(os.path.join(d, "decisions.jsonl")):
        r = json.loads(line)
        if r.get("acted"):
            acts.append({"at_utc": r.get("at_utc"), "event": r.get("event"),
                         "from_kbps": r.get("from_kbps"), "to_kbps": r.get("to_kbps")})
    out["ladder_acted"] = acts
    return out


def main():
    res = {k: one(v) for k, v in RUNS.items()}
    with open(os.path.join(HERE, "cl_b2_cpu_split.json"), "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
