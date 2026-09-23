#!/usr/bin/env python3
"""D-BASE-P10 analysis: audio redundancy (2 copies, 4 ticks apart) against
off, warm, interleaved A1 / B1 / A2 / B2 (10-minute holds).

Inputs: runs/report_<arm>.json, runs/status_<arm>.json (sender counters),
runs/heartbeat_<arm>.jsonl, runs/index.txt (prestart onn cpu),
t2_samples.jsonl (onn cpu-thermal, encoder CPU %).

Terms the handoff leaves loose, FIXED HERE BEFORE THE DATA:
  * per-minute rates use the report's duration_ms.
  * "recovered_by_duplicate ≈ the A-level loss": B's raw sequence-gap
    packets/min (lost + recovered, before recovery) within 0.5-1.5x the A
    mean lost/min -- a check that the path lost about as much.
  * "crossfaded_packets falls in step": B's crossfade reduction (A mean −
    B, per min) >= 70 % of its loss reduction (A mean − B, per min).
  * "underruns inside the 3/8 noise band (4-20, P9a)": B total <= 20
    (the 20-minute band applied as is to 10-minute holds).
  * "within their A range" (fps, spikes/min, fec_recovered/min): the
    min..max of A1, A2 widened by 10 % of its midpoint each side (two points
    make a range too tight to hold noise).
  * residence: |B − A mean| <= 10 ms; P8 holes: |B / A mean − 1| <= 20 %.
  * wire cost: (originals + duplicates) x 1,004 B (16 header + 960 PCM +
    28 IP/UDP) x 8 / duration, from the sender's own counters.
Readings (handoffs/D-BASE-P10_TASK.md), both B holds:
  ADOPT     loss/min >= 80 % below the A mean AND every clause above
  PARTIAL   20-80 % -> report the histogram, the offset that would cover
            the p90 gap event; implement nothing more
  DOES NOT  < 20 %, or (>= 80 % but a clause fails) -> say which
"""
import json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")
ARMS = ["A1", "B1", "A2", "B2"]
WIRE_BYTES = 16 + 960 + 28


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


prestart = {}
for line in open(os.path.join(R, "index.txt")):
    w = line.split()
    if w and w[0] == "prestart":
        prestart[w[1]] = float(w[3])
heat = jl(os.path.join(HERE, "t2_samples.jsonl"))

rows = {}
for arm in ARMS:
    rp = os.path.join(R, f"report_{arm}.json")
    if not os.path.exists(rp):
        continue
    rep = json.load(open(rp))["report"]
    a, d, v = rep["audio"], rep["decoder"], rep["video"]
    dur_s = rep["duration_ms"] / 1000.0
    mins = dur_s / 60.0
    stt = json.load(open(os.path.join(R, f"status_{arm}.json")))
    sa = stt.get("audio") or {}
    idx = [l.split() for l in open(os.path.join(R, "index.txt")) if l.startswith(arm + " ")]
    t0, t1 = (idx[0][3], idx[0][4]) if idx else (None, None)
    in_hold = [h for h in heat if t0 and t0 <= h["at_utc"][:19] + "Z" <= t1]
    enc = [((h.get("host") or {}).get("encoder") or {}).get("cpu_pct") for h in in_hold]
    enc = [x for x in enc if x is not None]
    onn = [(h.get("onn") or {}).get("cpu_thermal_c") for h in in_hold]
    onn = [x for x in onn if x]
    hg = a["arrival_holes"]["histograms"]
    orig, dup = sa.get("packets_sent") or 0, sa.get("duplicates_sent") or 0
    rows[arm] = {
        "copies": a.get("redundancy_copies"), "offset": a.get("redundancy_offset_packets"),
        "source": a.get("redundancy_source"), "duration_s": round(dur_s, 1),
        "onn_cpu_prestart_c": prestart.get(arm), "onn_cpu_mean_c": round(st.mean(onn), 2) if onn else None,
        "lost_packets": a["lost_packets"], "lost_per_min": a["lost_packets"] / mins,
        "recovered_by_duplicate": a.get("recovered_by_duplicate"),
        "duplicates_dropped": a.get("duplicates_dropped"), "late_unplaced": a.get("late_unplaced"),
        "sequence_gap_packets": a.get("sequence_gap_packets"),
        "raw_gap_per_min": (a.get("sequence_gap_packets") or 0) / mins,
        "sequence_gap_histogram": a.get("sequence_gap_histogram"),
        "crossfaded_packets": a["crossfaded_packets"], "crossfaded_per_min": a["crossfaded_packets"] / mins,
        "concealed_loss_packets": a["concealed_loss_packets"], "underruns": a["underruns"],
        "prolonged_starvation_events": a["prolonged_starvation_events"],
        "avg_queue_residence_ms": a["avg_queue_residence_ms"], "max_queue_residence_ms": a["max_queue_residence_ms"],
        "holes": hg["count"][0],
        "sender_packets_sent": orig, "sender_duplicates_sent": dup,
        "sender_send_errors": sa.get("send_errors"), "sender_duplicate_send_errors": sa.get("duplicate_send_errors"),
        "audio_wire_kbps": (orig + dup) * WIRE_BYTES * 8 / dur_s / 1000.0,
        "encoder_cpu_pct": round(st.mean(enc), 1) if enc else None,
        "rendered_fps": d["rendered_frames"] / dur_s, "spike_20_per_min": d["spike_20_ms"] / mins,
        "max_output_gap_ms": d["max_output_gap_ms"], "video_lost_per_min": v["lost_packets"] / mins,
        "fec_recovered_per_min": v["fec_recovered_packets"] / mins,
    }

print("== raw, per hold (run order)")
keys = [k for k in next(iter(rows.values())) if k != "sequence_gap_histogram"]
print(f"{'field':30s}" + "".join(f"{a:>12s}" for a in rows))
for k in keys:
    print(f"{k:30s}" + "".join(f"{rows[a][k]:12.2f}" if isinstance(rows[a][k], float) else f"{str(rows[a][k]):>12s}" for a in rows))
print("\n== sequence-gap histogram (gap events, first arrivals, before recovery)")
for a in rows:
    print(f"  {a}: {rows[a]['sequence_gap_histogram']}")

verdict = {}
if all(a in rows for a in ARMS):
    A = [rows["A1"], rows["A2"]]
    am = lambda k: st.mean(x[k] for x in A)
    def in_range(k, x):
        lo, hi = min(y[k] for y in A), max(y[k] for y in A)
        pad = 0.10 * (lo + hi) / 2
        return lo - pad <= x <= hi + pad
    print(f"\n== reading against A mean: lost/min {am('lost_per_min'):.2f}, crossfaded/min {am('crossfaded_per_min'):.2f}, "
          f"residence {am('avg_queue_residence_ms'):.2f} ms, holes {am('holes'):.0f}")
    for b in ("B1", "B2"):
        x = rows[b]
        drop = 1 - x["lost_per_min"] / am("lost_per_min") if am("lost_per_min") else None
        d_loss = am("lost_per_min") - x["lost_per_min"]
        d_xf = am("crossfaded_per_min") - x["crossfaded_per_min"]
        c = {
            "crossfades_in_step": d_xf >= 0.7 * d_loss,
            "raw_loss_like_A": 0.5 * am("lost_per_min") <= x["raw_gap_per_min"] <= 1.5 * am("lost_per_min"),
            "underruns_le_20": x["underruns"] <= 20,
            "residence_within_10ms": abs(x["avg_queue_residence_ms"] - am("avg_queue_residence_ms")) <= 10,
            "holes_within_20pct": abs(x["holes"] / am("holes") - 1) <= 0.20,
            "fps_in_A_range": in_range("rendered_fps", x["rendered_fps"]),
            "spikes_in_A_range": in_range("spike_20_per_min", x["spike_20_per_min"]),
            "fec_recovered_in_A_range": in_range("fec_recovered_per_min", x["fec_recovered_per_min"]),
        }
        verdict[b] = {"loss_drop": drop, **c}
        print(f"  {b}: loss drop {('%.1f%%' % (100 * drop)) if drop is not None else 'n/a (A lost 0)'}; " + ", ".join(f"{k} {'PASS' if v else 'FAIL'}" for k, v in c.items()))
    drops = [verdict[b]["loss_drop"] if verdict[b]["loss_drop"] is not None else 0.0 for b in ("B1", "B2")]
    clauses_ok = all(all(v for k, v in verdict[b].items() if k != "loss_drop") for b in ("B1", "B2"))
    if min(drops) >= 0.80 and clauses_ok:
        reading = "ADOPT"
    elif min(drops) >= 0.80:
        reading = "DOES NOT WORK (a clause failed)"
    elif min(drops) >= 0.20:
        reading = "PARTIAL"
    else:
        reading = "DOES NOT WORK (< 20 %)"
    verdict["reading"] = reading
    print(f"  READING: {reading}")
    # which gap sizes carry the residual / the p90 gap event
    for b in ("B1", "B2"):
        h = rows[b]["sequence_gap_histogram"] or {}
        tot = sum(h.values())
        cum, p90 = 0, None
        for k in ("1", "2", "3", "4-7", "8+"):
            cum += h.get(k, 0)
            if p90 is None and tot and cum / tot >= 0.9:
                p90 = k
        verdict[b]["p90_gap_bin"] = p90
        print(f"  {b}: gap events {tot}, p90 gap bin {p90}; residual lost {rows[b]['lost_packets']}, late_unplaced {rows[b]['late_unplaced']}")

json.dump({"rows": rows, "verdict": verdict}, open(os.path.join(HERE, "p10_summary.json"), "w"), indent=1)
