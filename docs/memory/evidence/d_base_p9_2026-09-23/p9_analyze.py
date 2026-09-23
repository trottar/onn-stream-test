#!/usr/bin/env python3
"""D-BASE-P9 analysis: the deeper audio cushion against the old one.

Reads runs/report_{A2,B,Bp}.json (decoder session reports, schema v2 +
P9's queue_cushion_source / cushion_applied_before_first_pcm) and, for
reference only, P8 arm A's report. Raw numbers first, then the
pre-registered reading from handoffs/D-BASE-P9_TASK.md applied to B and
B' against A2:

  works    : prolonged_starvation_events/min >= 80 % below A2, underruns
             <= A2, avg_queue_residence_ms up by 35-55 ms
  partial  : drop 20-80 %
  does not : drop < 20 % or underruns rise

Writes p9_summary.json beside this file.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
P8A = os.path.join(HERE, "..", "d_base_p8_2026-09-22", "runs", "report_A.json")
ARMS = [("A2", os.path.join(RUNS, "report_A2.json")),
        ("B", os.path.join(RUNS, "report_B.json")),
        ("Bp", os.path.join(RUNS, "report_Bp.json")),
        ("P8-A", P8A)]

AUDIO = ["queue_target_packets", "queue_capacity_packets", "queue_cushion_source",
         "cushion_applied_before_first_pcm", "underruns", "prolonged_starvation_events",
         "concealed_underruns", "stale_drops", "smooth_latency_trims", "lost_packets",
         "concealed_loss_packets", "avg_queue_residence_ms", "max_queue_residence_ms",
         "buffered_ms", "queue_depth", "max_queue_depth", "startup_wait_ms",
         "startup_prefill_ms", "first_write_elapsed_ms", "packets"]


def load(path):
    if not os.path.exists(path):
        return None
    return json.load(open(path))["report"]


def row(arm, r):
    a, d, v = r["audio"], r["decoder"], r["video"]
    mins = r["duration_ms"] / 60000.0
    hg = a["arrival_holes"]["histograms"]
    edges = hg["length_edges_ms"] + [None]
    out = {"arm": arm, "duration_s": round(r["duration_ms"] / 1000.0, 1)}
    out.update({k: a.get(k) for k in AUDIO})
    out["prolonged_starvation_per_min"] = a["prolonged_starvation_events"] / mins
    out["concealed_underruns_per_min"] = a["concealed_underruns"] / mins
    out["holes"] = hg["count"][0]
    out["holes_per_min"] = hg["count"][0] / mins
    out["holes_ge_40_per_min"] = hg["count"][1] / mins
    out["hole_length_ms"] = {f"{lo}-{hi if hi else 'max'}": c
                             for lo, hi, c in zip(edges, edges[1:], hg["length"])}
    out["rendered_fps"] = d["rendered_frames"] / (r["duration_ms"] / 1000.0)
    out["spike_20_per_min"] = d["spike_20_ms"] / mins
    out["spike_50"] = d["spike_50_ms"]
    out["max_output_gap_ms"] = d["max_output_gap_ms"]
    out["stale_output_drops"] = d["stale_output_drops"]
    out["video_lost_packets_per_min"] = v["lost_packets"] / mins
    return out


rows = {}
for arm, path in ARMS:
    r = load(path)
    if r is None:
        print(f"== {arm}: no report")
        continue
    rows[arm] = row(arm, r)

print("== raw, per session")
keys = [k for k in next(iter(rows.values())) if k not in ("arm", "hole_length_ms")]
print(f"{'field':36s}" + "".join(f"{a:>14s}" for a in rows))
for k in keys:
    cells = []
    for a in rows:
        x = rows[a].get(k)
        cells.append(f"{x:14.2f}" if isinstance(x, float) else f"{str(x):>14s}")
    print(f"{k:36s}" + "".join(cells))
print("\n== hole length histogram (ms: count)")
for a in rows:
    print(f"  {a:5s} {rows[a]['hole_length_ms']}")

verdicts = {}
if "A2" in rows:
    base = rows["A2"]
    print("\n== pre-registered reading against A2")
    for arm in ("B", "Bp"):
        if arm not in rows:
            continue
        x = rows[arm]
        drop = 1 - x["prolonged_starvation_per_min"] / base["prolonged_starvation_per_min"]
        d_res = x["avg_queue_residence_ms"] - base["avg_queue_residence_ms"]
        under_ok = x["underruns"] <= base["underruns"]
        holes_delta = x["holes"] / base["holes"] - 1
        if drop < 0.20 or not under_ok:
            verdict = "DOES NOT WORK (FALSIFIED)"
        elif drop < 0.80:
            verdict = "PARTIAL"
        elif 35 <= d_res <= 55:
            verdict = "WORKS"
        else:
            verdict = "STARVATION CRITERIA MET, COST OUTSIDE 35-55 ms"
        # residual holes against this arm's steady depth (capacity x 5 ms)
        cap_ms = x["queue_capacity_packets"] * 5
        hl = x["hole_length_ms"]
        over70 = sum(c for k, c in hl.items() if k in ("70-100", "100-200", "200-max"))
        over100 = sum(c for k, c in hl.items() if k in ("100-200", "200-max"))
        verdicts[arm] = {
            "starvation_drop": drop, "d_avg_residence_ms": d_res,
            "d_max_residence_ms": x["max_queue_residence_ms"] - base["max_queue_residence_ms"],
            "underruns": [base["underruns"], x["underruns"]], "underruns_ok": under_ok,
            "holes_delta": holes_delta, "holes_within_20pct": abs(holes_delta) <= 0.20,
            "first_write_delta_ms": x["first_write_elapsed_ms"] - base["first_write_elapsed_ms"],
            "steady_depth_ceiling_ms": cap_ms, "holes_over_70_ms": over70,
            "holes_over_100_ms": over100, "verdict": verdict}
        print(f"  {arm}: starvation/min {base['prolonged_starvation_per_min']:.1f} -> "
              f"{x['prolonged_starvation_per_min']:.1f} (drop {drop:.1%}); underruns "
              f"{base['underruns']} -> {x['underruns']}; avg residence "
              f"{base['avg_queue_residence_ms']:.1f} -> {x['avg_queue_residence_ms']:.1f} ms "
              f"({d_res:+.1f}); holes {holes_delta:+.1%}; first_write "
              f"{verdicts[arm]['first_write_delta_ms']:+d} ms -> {verdict}")

json.dump({"rows": rows, "verdicts": verdicts},
          open(os.path.join(HERE, "p9_summary.json"), "w"), indent=1)
