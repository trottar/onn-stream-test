#!/usr/bin/env python3
"""C5-M1 step 5: score the six holds, as pre-registered in c5_m1_design.txt
(section 5, written before step 4). Read-only.

usage: c5_m1_score.py [runs_dir=runs]
Holds B1 A1 B2 A2 B3 A3 (runs/index.txt; runs/report_*.json; frames_*.jsonl;
sys_*.jsonl; t2_samples.jsonl beside runs/).

Rows (close-out definitions, closeout_score.py) and targets:
  spikes >= 20 ms / min   decoder.spike_20_ms / min          < 200
  rendered fps            decoder.rendered_frames / s        >= 59.5
  stale drops / min       decoder.stale_output_drops / min   < 20
  video loss / min        video.lost_packets / min (post-FEC) < 10
  max output gap          decoder.max_output_gap_ms          <= 250
  audio underruns         audio.underruns (per hold, per min) reported
Outcome order: NOT CAPABLE (any A hold misses any row; a hold without
PLAYING under the candidate is a miss), INCOMPLETE (fewer than three scored
A holds), INCONCLUSIVE (a B hold misses a row: baseline not met), CAPABLE
WITH COST (a cost row worse than noise: all three A worse than the worst B
AND the A median beyond it by more than the B spread; fps: lower is
worse), CAPABLE.
"""
import json, os, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "runs")
HOLDS = ["B1", "A1", "B2", "A2", "B3", "A3"]
CAP = {"A": 200_000, "B": 90_000}
TARGETS = [("spikes", "spikes >= 20 ms / min", lambda x: x < 200, "< 200"),
           ("fps", "rendered fps", lambda x: x >= 59.5, ">= 59.5"),
           ("stale", "stale drops / min", lambda x: x < 20, "< 20"),
           ("vloss", "video loss / min post-FEC", lambda x: x < 10, "< 10"),
           ("maxgap", "max output gap ms", lambda x: x <= 250, "<= 250")]
COST = [("spikes", True), ("fps", False), ("stale", True), ("vloss", True), ("maxgap", True), ("aund", True)]
idx = {}
if os.path.exists(os.path.join(R, "index.txt")):
    for line in open(os.path.join(R, "index.txt")):
        f = line.split()
        if f and f[0] in HOLDS and len(f) >= 6:
            idx[f[0]] = f

def jl(p):
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []

def mean(a):
    a = [x for x in a if x is not None]
    return sum(a) / len(a) if a else None

t2 = jl(os.path.join(HERE, "t2_samples.jsonl"))
rows = {}
print("C5-M1 -- scoring (pre-registered, c5_m1_design.txt section 5)")
hdr = (f"{'hold':<4} {'min':>5} {'spikes/m':>8} {'fps':>6} {'stale/m':>7} {'vloss/m':>7} {'maxgap':>6} "
       f"{'aund':>4} {'aund/m':>6} | {'Mbps rx':>7} {'qmax':>4} {'codec':>5} {'frmax B':>8} {'s>=95%cap/m':>11} "
       f"{'ge80/m':>6} {'hostCPU':>7} {'GPU':>5} {'encCPU':>6} {'onn C':>5} {'host C':>6}")
print(hdr)
for h in HOLDS:
    arm = h[0]
    rp = os.path.join(R, f"report_{h}.json")
    if h not in idx or not os.path.exists(rp):
        print(f"{h:<4} {'NOT RUN' if h not in idx else 'no report'}")
        continue
    rep = json.load(open(rp))["report"]
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    secs = rep["duration_ms"] / 1000.0; m = secs / 60.0
    fr = jl(os.path.join(R, f"frames_{h}.jsonl"))
    cap = CAP[arm]
    near = sum(1 for r in fr if r.get("max_bytes", 0) >= 0.95 * cap)
    ge80 = sum(r.get("frames_ge_80", 0) for r in fr)
    sysr = jl(os.path.join(R, f"sys_{h}.jsonl"))
    t0, t1 = idx[h][4], idx[h][5]
    tw = [r for r in t2 if t0 <= r.get("at_utc", "")[:19] + "Z" <= t1]
    enc = mean([((r.get("host") or {}).get("encoder") or {}).get("cpu_pct") for r in tw])
    onn = mean([(r.get("onn") or {}).get("cpu_thermal_c") for r in tw])
    hostc = mean([((r.get("host") or {}).get("temps_c") or {}).get("k10temp/Tctl") for r in tw])
    row = dict(min=m, spikes=d["spike_20_ms"] / m, fps=d["rendered_frames"] / secs,
               stale=d["stale_output_drops"] / m, vloss=v["lost_packets"] / m,
               maxgap=d["max_output_gap_ms"], aund_n=a.get("underruns"), aund=(a.get("underruns") or 0) / m,
               mbps=8 * v["bytes"] / secs / 1e6, qmax=d.get("max_queue_depth"), codec=d.get("max_codec_ms"),
               frmax=max((r.get("max_bytes", 0) for r in fr), default=None),
               near=near / m, ge80=ge80 / m,
               cpu=mean([r["host_cpu_busy_pct"] for r in sysr]), gpu=mean([r["gpu_busy_pct"] for r in sysr]),
               enc=enc, onn=onn, hostc=hostc, width=rep.get("paused_frame_width"))
    rows[h] = row
    f = lambda x, s: "-" if x is None else format(x, s)
    print(f"{h:<4} {m:5.2f} {row['spikes']:8.1f} {row['fps']:6.2f} {row['stale']:7.2f} {row['vloss']:7.2f} "
          f"{row['maxgap']:6} {row['aund_n']:4} {row['aund']:6.2f} | {row['mbps']:7.2f} {f(row['qmax'],''):>4} "
          f"{f(row['codec'],''):>5} {f(row['frmax'],''):>8} {row['near']:11.2f} {row['ge80']:6.2f} "
          f"{f(row['cpu'],'.1f'):>7} {f(row['gpu'],'.1f'):>5} {f(row['enc'],'.1f'):>6} {f(row['onn'],'.1f'):>5} {f(row['hostc'],'.1f'):>6}")
print("(Mbps rx = client-received video payload incl. parity; s>=95%cap/m = seconds per minute whose largest\n"
      " encoded frame was >= 95 % of the arm's cap; ge80/m = frames of >= 80 packets per minute; hostCPU / GPU\n"
      " from the 5 s sampler; encCPU, onn C, host C (Tctl) from T2 inside the hold window)")
print()
A = [h for h in ("A1", "A2", "A3") if h in rows]
B = [h for h in ("B1", "B2", "B3") if h in rows]
misses_a = [(h, name, round(rows[h][k], 2), t) for h in A for k, name, ok, t in TARGETS if not ok(rows[h][k])]
misses_a += [(h, "no PLAYING / no report", None, "") for h in ("A1", "A2", "A3") if h in idx and h not in rows]
misses_b = [(h, name, round(rows[h][k], 2), t) for h in B for k, name, ok, t in TARGETS if not ok(rows[h][k])]
print("targets per hold:")
for h in HOLDS:
    if h in rows:
        print(f"  {h}: " + ", ".join(f"{name} {'MET' if ok(rows[h][k]) else 'MISSED'}" for k, name, ok, t in TARGETS))
cost = []
print("\ncost rows (S1 rule):")
if len(A) == 3 and len(B) == 3:
    for key, higher_worse in COST:
        b = [rows[h][key] for h in B]; a = [rows[h][key] for h in A]
        spread = max(b) - min(b)
        if higher_worse:
            worst = max(b); worse = all(x > worst for x in a) and statistics.median(a) - worst > spread
        else:
            worst = min(b); worse = all(x < worst for x in a) and worst - statistics.median(a) > spread
        if worse:
            cost.append(key)
        print(f"  {key:<7} B {[round(x, 2) for x in b]}  A {[round(x, 2) for x in a]}  worst B {worst:.2f}, "
              f"B spread {spread:.2f}, A median {statistics.median(a):.2f} -> {'WORSE' if worse else 'within noise'}")
else:
    print("  incomplete")
if misses_a:
    out = "NOT CAPABLE (" + "; ".join(f"{h} {n} {v} vs {t}" for h, n, v, t in misses_a) + ")"
elif len(A) < 3:
    out = f"INCOMPLETE ({len(A)} of 3 A holds scored)"
elif misses_b:
    out = "INCONCLUSIVE, baseline not met (" + "; ".join(f"{h} {n} {v} vs {t}" for h, n, v, t in misses_b) + ")"
elif cost:
    out = "CAPABLE WITH COST (" + ", ".join(cost) + ")"
else:
    out = "CAPABLE"
print(f"\nOUTCOME: {out}")
