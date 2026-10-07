#!/usr/bin/env python3
"""E3-S5C -- the bar as pre-registered (e3_s5c_preregistration.txt); E3-S5B's analysis with clause (a) widened for the spin (sender <= 8 %, companion <= 20 %). Read-only.
-> e3_s5c_table.md/.json, loss_per_minute.txt, e3_s5c_verdict.json"""
import importlib.util
import json
import os
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
E2R = os.path.join(REPO, "docs/memory/evidence/e2_s1_2026-10-05/runs")
R = os.path.join(HERE, "runs")
spec = importlib.util.spec_from_file_location("e2a", os.path.join(REPO, "docs/memory/evidence/e2_s1_2026-10-05/e2_analysis.py"))
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
RUNS = [("C1", "E1-PS1-STREAM/run1"), ("F1", "E1-PS1-STREAM_flag/run1"), ("C2", "E1-PS1-STREAM/run2"),
        ("F2", "E1-PS1-STREAM_flag/run2"), ("F3", "E1-PS1-STREAM_flag/run3")]


def k(s, *p):
    for x in p:
        s = (s or {}).get(x) if isinstance(s, dict) else None
    return s


def minutes(s):
    t0, t1 = A.t(s["window"]["from"]), A.t(s["window"]["to"])
    L = A.hb_loss_series(t0, t1)
    return [round(sum(v for sec, v in L.items() if t0 + 60 * i <= sec < t0 + 60 * (i + 1)), 1) for i in range(20)]


def main():
    subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_table.py"), os.path.join(HERE, "e3_s5c_table.md")]
                   + [f"{n}={R}/{p}" for n, p in RUNS] + [f"E2 PS1-STREAM={E2R}/E1-PS1-STREAM/run1"],
                   check=True, stdout=subprocess.DEVNULL)
    t = json.load(open(os.path.join(HERE, "e3_s5c_table.json")))
    S = {n: json.load(open(os.path.join(R, p, "summary.json"))) for n, p in RUNS}
    e2 = json.load(open(os.path.join(E2R, "E1-PS1-STREAM/run1/summary.json")))
    out, mins = {}, {}
    for n, _ in RUNS:
        s = S[n]
        rf = k(s, "teardown", "report_fields") or {}
        m = (rf.get("duration_ms") or 0) / 60000
        mins[n] = minutes(s)
        dec = [json.loads(l) for l in open(os.path.join(R, dict(RUNS)[n], "decisions.jsonl"))] \
            if os.path.exists(os.path.join(R, dict(RUNS)[n], "decisions.jsonl")) else []
        out[n] = {"sender_cpu": t[n]["threads"].get("audio_sender_cpu"),
                  "companion_cpu": k(s, "host", "host", "procs.companion.cpu_pct", "mean"),
                  "underruns": k(s, "key", "heartbeat", "audio_underruns"),
                  "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"),
                  "retroarch_fps": k(s, "key", "retroarch", "frames_per_s"),
                  "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"),
                  "minutes_gt_100": sum(1 for x in mins[n] if x > 100), "minute_median": statistics.median(mins[n]),
                  "spikes20_per_min": round(rf["decoder.spike_20_ms"] / m, 1) if m and "decoder.spike_20_ms" in rf else None,
                  "stale_per_min": round(rf["decoder.stale_output_drops"] / m, 2) if m and "decoder.stale_output_drops" in rf else None,
                  "report_max_gap_ms": rf.get("decoder.max_output_gap_ms"),
                  "c2_gap_max_ms": k(s, "key", "telemetry", "output_gap_ms_max"),
                  "c2_r2d_median_ms": k(s, "key", "telemetry", "receive_to_decode_ms_median"),
                  "host_cpu": k(s, "host", "host", "cpu.mean_pct", "mean"),
                  "socket_w": k(s, "host", "host", "gpu.socket_power_w", "mean"),
                  "decisions": k(s, "key", "decisions"),
                  "decision_kinds": sorted({str(d.get("decision") or d.get("class") or d.get("event") or "") for d in dec})[:12],
                  "started_utc": s["window"]["from"]}
    e2cpu, e2fps = k(e2, "host", "host", "cpu.mean_pct", "mean"), k(e2, "key", "heartbeat", "rendered_fps")
    comp = all(abs(out[c]["host_cpu"] - e2cpu) <= 2 and abs(out[c]["rendered_fps"] - e2fps) <= 0.5 for c in ("C1", "C2")) \
        and abs(out["C1"]["rendered_fps"] - out["C2"]["rendered_fps"]) <= 0.5
    mx_ur = max(out["C1"]["underruns"], out["C2"]["underruns"])
    for f in ("F1", "F2", "F3"):
        x = out[f]
        x["a"] = x["sender_cpu"] is not None and x["sender_cpu"] <= 8 and x["companion_cpu"] <= 20
        x["b"] = x["underruns"] <= mx_ur + 5 and x["underruns"] <= 20
        x["c"] = x["rendered_fps"] >= 59.5 and abs(x["retroarch_fps"] - 60) <= 0.5
        x["e"] = x["spikes20_per_min"] is not None and x["spikes20_per_min"] < 200 and x["stale_per_min"] < 20
    Fm = mins["F1"] + mins["F2"] + mins["F3"]
    Cm = mins["C1"] + mins["C2"]
    d = {"median_F": statistics.median(Fm), "median_C": statistics.median(Cm),
         "share_F_gt_100": round(sum(1 for x in Fm if x > 100) / len(Fm), 4),
         "share_C_gt_100": round(sum(1 for x in Cm if x > 100) / len(Cm), 4)}
    d["median_holds"] = d["median_F"] <= 3 * d["median_C"]
    d["share_holds"] = d["share_F_gt_100"] <= d["share_C_gt_100"] + 0.10
    d["holds"] = d["median_holds"] and d["share_holds"]
    out["d_pooled"] = d
    out["comparability"] = {"e2_cpu": e2cpu, "e2_fps": e2fps, "holds": comp}
    allok = all(out[f][c] for f in ("F1", "F2", "F3") for c in "abce") and d["holds"]
    out["verdict"] = "INCONCLUSIVE" if not comp else ("ACCEPTED" if allok else "REJECTED")
    json.dump(out, open(os.path.join(HERE, "e3_s5c_verdict.json"), "w"), indent=1)
    with open(os.path.join(HERE, "loss_per_minute.txt"), "w") as fh:
        fh.write("lost video packets per minute of each 20-min window (heartbeat), E3-S5C, in run order\n")
        for n, p in RUNS:
            fh.write(f"{n} ({p}): {mins[n]}  minutes > 100: {out[n]['minutes_gt_100']}; median {out[n]['minute_median']}\n")
        fh.write(f"pooled: F median {d['median_F']}, C median {d['median_C']}; share > 100: F {d['share_F_gt_100']}, "
                 f"C {d['share_C_gt_100']}\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    sys.exit(main())
