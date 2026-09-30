#!/usr/bin/env python3
"""CL-B1 APK -- A4 and A5, scored as pre-registered (cl_b1_apk_preregistration.txt). Read-only.

N1 = the 20-min hold on the new APK (runs/), O1 = the paired 20-min hold on the adopted
f31b1c18...8ae7 (runs_old/). The reference ranges are the adopted APK's eight C5-M3 B holds of
2026-09-30 (c5_m3_2026-09-29/runs and runs_rerun).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
C5 = os.path.join(HERE, "..", "c5_m3_2026-09-29")


def rows(run_dir, hold):
    rep = json.load(open(os.path.join(run_dir, f"report_{hold}.json")))["report"]
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    secs = rep["duration_ms"] / 1000.0
    m = secs / 60.0
    return {"min": m, "spikes": d["spike_20_ms"] / m, "fps": d["rendered_frames"] / secs,
            "stale": d["stale_output_drops"] / m, "aund": (a.get("underruns") or 0) / m,
            "fec_rec": v["fec_recovered_packets"] / m, "fec_unrec": v["fec_unrecoverable_groups"] / m,
            "fec_hold": v["fec_max_hold_ms"], "vloss": v["lost_packets"] / m, "maxgap": d["max_output_gap_ms"],
            "slow_cap": rep.get("slow_event_capacity"),
            "recent": rep.get("slow_event_retained_recent"), "marked": rep.get("slow_event_retained_marked")}


ref = []
for d in ("runs", "runs_rerun"):
    for line in open(os.path.join(C5, d, "index.txt")):
        f = line.split()
        if len(f) >= 6 and f[1] == "H" and f[0].startswith("B"):
            ref.append((f"{d}/{f[0]}", rows(os.path.join(C5, d), f[0])))
rng = {k: (min(r[k] for _, r in ref), max(r[k] for _, r in ref)) for k in ("fec_rec", "fec_unrec", "fec_hold", "vloss")}
spread = rng["vloss"][1] - rng["vloss"][0]
n1 = rows(os.path.join(HERE, "runs"), "N1")
o1 = rows(os.path.join(HERE, "runs_old"), "O1") if os.path.exists(os.path.join(HERE, "runs_old", "report_O1.json")) else None
print("CL-B1 APK -- A4 (the new APK's hold) and A5 (the paired adopted hold)")
print(f"reference: the adopted APK's eight C5-M3 B holds: FEC recovered/min {rng['fec_rec'][0]:.2f}-{rng['fec_rec'][1]:.2f}, "
      f"unrecoverable groups/min {rng['fec_unrec'][0]:.2f}-{rng['fec_unrec'][1]:.2f}, fec_max_hold_ms "
      f"{rng['fec_hold'][0]}-{rng['fec_hold'][1]}; loss/min {rng['vloss'][0]:.2f}-{rng['vloss'][1]:.2f} (spread {spread:.2f})")
hdr = (f"{'hold':<4} {'APK':<9} {'min':>5} {'spikes/m':>8} {'fps':>6} {'stale/m':>7} {'aund/m':>6} | {'FEC rec/m':>9} "
       f"{'unrec/m':>7} {'hold ms':>7} | {'loss/m':>7} {'max gap':>7} | {'slow cap':>8} {'recent':>6}")
print(hdr)
for name, apk, r in (("N1", "de072762", n1), ("O1", "f31b1c18", o1)):
    if r:
        print(f"{name:<4} {apk:<9} {r['min']:5.2f} {r['spikes']:8.1f} {r['fps']:6.2f} {r['stale']:7.2f} {r['aund']:6.2f} | "
              f"{r['fec_rec']:9.2f} {r['fec_unrec']:7.2f} {r['fec_hold']:7} | {r['vloss']:7.2f} {r['maxgap']:7} | "
              f"{str(r['slow_cap']):>8} {str(r['recent']):>6}")
a4_rows = {"spikes < 200/min": n1["spikes"] < 200, "rendered fps >= 59.5": n1["fps"] >= 59.5,
           "stale drops < 20/min": n1["stale"] < 20, "audio underruns < 5/min": n1["aund"] < 5}
inside = {k: rng[k][0] <= n1[k] <= rng[k][1] for k in ("fec_rec", "fec_unrec", "fec_hold")}
worse_than_o1 = None
if o1:
    worse_than_o1 = {"fec_rec": False, "fec_unrec": n1["fec_unrec"] > o1["fec_unrec"],
                     "fec_hold": n1["fec_hold"] > o1["fec_hold"]}
fec_ok = all(inside[k] or (worse_than_o1 is not None and not worse_than_o1[k]) for k in inside)
print("A4 rows:")
for k, v in a4_rows.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
for k in inside:
    print(f"  {'inside' if inside[k] else 'OUTSIDE'} the reference range: {k} {n1[k]:.2f}"
          + ("" if inside[k] or worse_than_o1 is None else f" (vs the paired adopted hold {o1[k]:.2f}: "
             f"{'worse' if worse_than_o1[k] else 'not worse'})"))
a4 = all(a4_rows.values()) and fec_ok
print(f"  => A4 {'HOLDS' if a4 else 'DOES NOT HOLD'}")
a5 = None
if o1:
    diff = n1["vloss"] - o1["vloss"]
    a5 = not (diff > spread)
    print(f"A5 (reported; gates only if worse by more than the spread {spread:.2f}): loss/min new {n1['vloss']:.2f} vs adopted "
          f"{o1['vloss']:.2f} (difference {diff:+.2f}); max gap new {n1['maxgap']} vs adopted {o1['maxgap']} -> "
          f"{'does not gate' if a5 else 'NEW APK WORSE BY MORE THAN THE SPREAD'}")
json.dump({"n1": n1, "o1": o1, "reference_range": rng, "spread": spread, "a4": a4, "a5": a5},
          open(os.path.join(HERE, "a4_a5_score.json"), "w"), indent=1)
