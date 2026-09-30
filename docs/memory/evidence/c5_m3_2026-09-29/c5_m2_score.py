#!/usr/bin/env python3
"""C5-M2 / C5-M3: score a night of 20-minute holds. Read-only. Derived from
c5_m1_2026-09-28/c5_m1_score.py (the same rows, the same S1 cost rule); the
hold list, each hold's profile and its cap now come from the run directory
(index.txt and armcheck_<hold>.json), not from the letters A / B.

usage: c5_m2_score.py screen  <runs_dir> [baseline_prefix=B]
       c5_m2_score.py confirm <runs_dir>

Rows (close-out definitions) and targets, per hold:
  spikes >= 20 ms / min   decoder.spike_20_ms / min            < 200
  rendered fps            decoder.rendered_frames / s          >= 59.5
  stale drops / min       decoder.stale_output_drops / min     < 20
  video loss / min        video.lost_packets / min (post-FEC)  < 10
  max output gap          decoder.max_output_gap_ms            <= 250
  audio underruns         reported
Reported, not gated: on-air Mbit/s (client-received video payload incl.
parity), frames of >= 80 packets / min, cap hits / min (seconds whose largest
frame was >= 95 % of the hold's cap), the per-second largest frame p50 / p90 /
max (with GOP 15 at 60 fps every second holds four IDRs, so the largest frame
of a second is an IDR's size or above it -- the IDR-size proxy), decoder
queue max and codec ms, host CPU / GPU busy, encoder CPU, onn and host
temperature (T2).

SCREEN (C5-M2 night 1, C5-M3; pre-registered in the task): an arm passes if
its hold meets every target. C5-M2: among passing arms the confirmation
candidate is the one with the lowest post-FEC loss, ties broken by the higher
bitrate; if none passes, NOT CAPABLE (all arms). If two or more baseline holds
miss the baseline: INCONCLUSIVE (link), re-run once.

CONFIRM (C5-M2 night 2, C5-M1's rule): holds B1 A1 B2 A2 B3 A3. NOT CAPABLE
if any A hold misses any row; INCOMPLETE if fewer than three A holds scored;
INCONCLUSIVE if a B hold misses a row; CAPABLE WITH COST if a cost row is
worse than noise (all three A worse than the worst B AND the A median beyond
it by more than the B spread; fps lower is worse); else CAPABLE.
"""
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODE = sys.argv[1]
R = sys.argv[2] if os.path.isabs(sys.argv[2]) else os.path.join(HERE, sys.argv[2])
BPFX = sys.argv[3] if len(sys.argv) > 3 else "B"
TARGETS = [("spikes", "spikes >= 20 ms / min", lambda x: x < 200, "< 200"),
           ("fps", "rendered fps", lambda x: x >= 59.5, ">= 59.5"),
           ("stale", "stale drops / min", lambda x: x < 20, "< 20"),
           ("vloss", "video loss / min post-FEC", lambda x: x < 10, "< 10"),
           ("maxgap", "max output gap ms", lambda x: x <= 250, "<= 250")]
COST = [("spikes", True), ("fps", False), ("stale", True), ("vloss", True), ("maxgap", True), ("aund", True)]


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def mean(a):
    a = [x for x in a if x is not None]
    return sum(a) / len(a) if a else None


def pct(a, p):
    a = sorted(a)
    return a[min(len(a) - 1, int(round(p * (len(a) - 1))))] if a else None


order, idx = [], {}
for line in open(os.path.join(R, "index.txt")):
    f = line.split()
    if f and len(f) >= 6 and f[1] == "H":
        idx[f[0]] = f
        order.append(f[0])
    elif f and len(f) >= 2 and f[1] == "NOT_RUN":
        order.append(f[0])
t2 = jl(os.path.join(R, "t2_samples.jsonl"))
rows = {}
print(f"C5 scoring ({MODE}) -- {os.path.relpath(R, HERE)}")
print(f"{'hold':<4} {'profile':<38} {'min':>5} {'spk/m':>6} {'fps':>6} {'stale':>5} {'vloss/m':>7} {'maxgap':>6} "
      f"{'aund/m':>6} | {'Mbps':>6} {'qmax':>4} {'codec':>5} {'cap':>6} {'frmax p50/p90/max':>20} {'caphit/m':>8} "
      f"{'ge80/m':>6} {'CPU':>5} {'GPU':>5} {'enc':>5} {'onnC':>5} {'hostC':>5}")
for h in order:
    rp = os.path.join(R, f"report_{h}.json")
    if h not in idx or not os.path.exists(rp):
        print(f"{h:<4} {'NOT RUN' if h not in idx else 'no report'}")
        continue
    ac = json.load(open(os.path.join(R, f"armcheck_{h}.json")))
    ov = ac.get("encoder_overrides") or {}
    cap = ov.get("max_frame_size_bytes")
    rep = json.load(open(rp))["report"]
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    secs = rep["duration_ms"] / 1000.0
    m = secs / 60.0
    fr = jl(os.path.join(R, f"frames_{h}.jsonl"))
    mx = [r.get("max_bytes", 0) for r in fr if r.get("frames")]
    sysr = jl(os.path.join(R, f"sys_{h}.jsonl"))
    t0, t1 = idx[h][4], idx[h][5]
    tw = [r for r in t2 if t0 <= r.get("at_utc", "")[:19] + "Z" <= t1]
    row = dict(profile=ac.get("profile_id"), bitrate=ac.get("reference_bitrate_kbps") or ac.get("bitrate_kbps"),
               width=ac.get("width"), any_override=ov.get("any_override"), cap=cap, min=m,
               spikes=d["spike_20_ms"] / m, fps=d["rendered_frames"] / secs,
               stale=d["stale_output_drops"] / m, vloss=v["lost_packets"] / m, maxgap=d["max_output_gap_ms"],
               aund=(a.get("underruns") or 0) / m, mbps=8 * v["bytes"] / secs / 1e6,
               qmax=d.get("max_queue_depth"), codec=d.get("max_codec_ms"),
               fr50=pct(mx, .5), fr90=pct(mx, .9), frmax=max(mx) if mx else None,
               caphit=(sum(1 for x in mx if cap and x >= 0.95 * cap) / m) if cap else None,
               ge80=sum(r.get("frames_ge_80", 0) for r in fr) / m,
               cpu=mean([r.get("host_cpu_busy_pct") for r in sysr]), gpu=mean([r.get("gpu_busy_pct") for r in sysr]),
               enc=mean([((r.get("host") or {}).get("encoder") or {}).get("cpu_pct") for r in tw]),
               onn=mean([(r.get("onn") or {}).get("cpu_thermal_c") for r in tw]),
               hostc=mean([((r.get("host") or {}).get("temps_c") or {}).get("k10temp/Tctl") for r in tw]))
    row["pass"] = all(ok(row[k]) for k, _, ok, _ in TARGETS)
    row["misses"] = [f"{name} {round(row[k], 2)} vs {t}" for k, name, ok, t in TARGETS if not ok(row[k])]
    rows[h] = row
    f = lambda x, s: "-" if x is None else format(x, s)
    print(f"{h:<4} {str(row['profile'])[:38]:<38} {m:5.2f} {row['spikes']:6.1f} {row['fps']:6.2f} {row['stale']:5.2f} "
          f"{row['vloss']:7.2f} {row['maxgap']:6} {row['aund']:6.2f} | {row['mbps']:6.2f} {f(row['qmax'], ''):>4} "
          f"{f(row['codec'], ''):>5} {f(cap, ''):>6} {f(row['fr50'], ''):>6}/{f(row['fr90'], ''):>6}/{f(row['frmax'], ''):>6} "
          f"{f(row['caphit'], '.2f'):>8} {row['ge80']:6.2f} {f(row['cpu'], '.1f'):>5} {f(row['gpu'], '.1f'):>5} "
          f"{f(row['enc'], '.1f'):>5} {f(row['onn'], '.1f'):>5} {f(row['hostc'], '.1f'):>5}")
print()
for h in order:
    if h in rows:
        r = rows[h]
        print(f"  {h}: {'MEETS EVERY TARGET' if r['pass'] else 'MISSES ' + '; '.join(r['misses'])}"
              f" (any_override {r['any_override']}, {r['width']} wide, bitrate {r['bitrate']})")
print()
if MODE == "screen":
    base = [h for h in order if h.startswith(BPFX) and h in rows]
    arms = [h for h in order if not h.startswith(BPFX) and h in rows]
    base_miss = [h for h in base if not rows[h]["pass"]]
    notrun = [h for h in order if h not in rows]
    print(f"baseline holds {base}: missed {base_miss or 'none'}; arms {arms}; not run / no report {notrun or 'none'}")
    if len(base_miss) >= 2:
        out = "INCONCLUSIVE (link): " + ", ".join(f"{h} {'; '.join(rows[h]['misses'])}" for h in base_miss)
        cand = None
    else:
        passing = [h for h in arms if rows[h]["pass"]]
        for h in arms:
            print(f"  arm {h} {rows[h]['profile']}: {'PASSES' if rows[h]['pass'] else 'does not pass'}")
        if not passing:
            out, cand = "NOT CAPABLE (all arms)", None
        else:
            cand = sorted(passing, key=lambda h: (rows[h]["vloss"], -(rows[h]["bitrate"] or 0)))[0]
            out = f"PASSING {passing}; confirmation candidate {cand} ({rows[cand]['profile']})"
    print(f"\nSCREENING OUTCOME: {out}")
    json.dump({"outcome": out, "candidate": rows[cand]["profile"] if cand else None, "rows": rows},
              open(os.path.join(R, "score.json"), "w"), indent=1, default=str)
else:
    A = [h for h in ("A1", "A2", "A3") if h in rows]
    B = [h for h in ("B1", "B2", "B3") if h in rows]
    misses_a = [(h, m) for h in A for m in rows[h]["misses"]]
    misses_a += [(h, "no PLAYING / no report") for h in ("A1", "A2", "A3") if h in idx and h not in rows]
    misses_b = [(h, m) for h in B for m in rows[h]["misses"]]
    cost = []
    print("cost rows (S1 rule):")
    if len(A) == 3 and len(B) == 3:
        for key, higher_worse in COST:
            b = [rows[h][key] for h in B]
            a = [rows[h][key] for h in A]
            spread = max(b) - min(b)
            if higher_worse:
                worst = max(b)
                worse = all(x > worst for x in a) and statistics.median(a) - worst > spread
            else:
                worst = min(b)
                worse = all(x < worst for x in a) and worst - statistics.median(a) > spread
            if worse:
                cost.append(key)
            print(f"  {key:<7} B {[round(x, 2) for x in b]}  A {[round(x, 2) for x in a]}  worst B {worst:.2f}, B spread "
                  f"{spread:.2f}, A median {statistics.median(a):.2f} -> {'WORSE' if worse else 'within noise'}")
    if misses_a:
        out = "NOT CAPABLE (" + "; ".join(f"{h} {m}" for h, m in misses_a) + ")"
    elif len(A) < 3:
        out = f"INCOMPLETE ({len(A)} of 3 A holds scored)"
    elif misses_b:
        out = "INCONCLUSIVE, baseline not met (" + "; ".join(f"{h} {m}" for h, m in misses_b) + ")"
    elif cost:
        out = "CAPABLE WITH COST (" + ", ".join(cost) + ")"
    else:
        out = "CAPABLE"
    print(f"\nOUTCOME: {out}")
    json.dump({"outcome": out, "cost": cost, "rows": rows}, open(os.path.join(R, "score.json"), "w"), indent=1,
              default=str)
