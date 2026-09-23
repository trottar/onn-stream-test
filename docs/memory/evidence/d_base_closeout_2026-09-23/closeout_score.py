#!/usr/bin/env python3
"""D-BASE close-out: score investigations/BASELINE_STREAM_HEALTH.md's target
table on sessions C (cold) and W (warm), each row from its source counter.

Rows (all from the decoder session report; per-minute = / (duration/60)):
  spikes >= 20 ms / min          decoder.spike_20_ms            target < 200
  rendered fps                   decoder.rendered_frames / s    target >= 59.5
  received-AU fps                video.frames / s               (no target)
  max output gap                 decoder.max_output_gap_ms      target <= 100 (transport row)
  stale output drops / min       decoder.stale_output_drops     target < 20
  lost packets / min, video      video.lost_packets (post-FEC)  target < 10
  lost packets / min, audio      audio.lost_packets (after de-duplication; beside it)
  audio underruns                audio.underruns: the session total (P2) and
                                 per min against the table's literal < 5
  prolonged_starvation_events / min
  frames under 20 ms rx->output  decoder.rx_to_output_histogram_ms[0] / sum
  client fps deficit             received-AU fps - rendered fps

Verdict, FIXED BEFORE THE DATA (handoffs/D-BASE-CLOSE_TASK.md):
  BASELINE MET      every numeric-target row except max output gap passes in
                    BOTH sessions, and max output gap <= 250 ms in both
  BASELINE NOT MET  otherwise -- name the row(s)
  Client decision (D-BASE Step 5): triggered if spikes >= 200/min or rendered
  fps < 59.5 in either session.
"""
import json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")
SESS = ["C", "W"]
heat = [json.loads(l) for l in open(os.path.join(HERE, "t2_samples.jsonl")) if l.strip()] \
    if os.path.exists(os.path.join(HERE, "t2_samples.jsonl")) else []
idx = {l.split()[0]: l.split() for l in open(os.path.join(R, "index.txt")) if l.split() and l.split()[0] in SESS}


def score(s):
    rep = json.load(open(os.path.join(R, f"report_{s}.json")))["report"]
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    secs = rep["duration_ms"] / 1000.0
    mins = secs / 60.0
    h = d["rx_to_output_histogram_ms"]
    t0, t1 = idx[s][3], idx[s][4]
    onn = [(x.get("onn") or {}).get("cpu_thermal_c") for x in heat if t0 <= x["at_utc"][:19] + "Z" <= t1]
    onn = [x for x in onn if x]
    st_ = [(x.get("onn") or {}).get("thermal_status") for x in heat if t0 <= x["at_utc"][:19] + "Z" <= t1]
    rend, recv = d["rendered_frames"] / secs, v["frames"] / secs
    return {
        "duration_s": round(secs, 1),
        "spikes_20_per_min": d["spike_20_ms"] / mins,
        "rendered_fps": rend,
        "received_au_fps": recv,
        "max_output_gap_ms": d["max_output_gap_ms"],
        "stale_output_drops_per_min": d["stale_output_drops"] / mins,
        "video_lost_per_min_post_fec": v["lost_packets"] / mins,
        "video_fec_recovered_per_min": v["fec_recovered_packets"] / mins,
        "audio_lost_per_min_after_dedup": a["lost_packets"] / mins,
        "audio_recovered_by_duplicate": a.get("recovered_by_duplicate"),
        "audio_underruns_total": a["underruns"],
        "audio_underruns_per_min": a["underruns"] / mins,
        "prolonged_starvation_per_min": a["prolonged_starvation_events"] / mins,
        "frames_under_20ms_pct": 100.0 * h[0] / sum(h) if sum(h) else None,
        "client_fps_deficit": recv - rend,
        "avg_queue_residence_ms": a["avg_queue_residence_ms"],
        "redundancy": f"{a.get('redundancy_copies')}/{a.get('redundancy_offset_packets')} {a.get('redundancy_source')}",
        "cushion": f"{a.get('queue_target_packets')}/{a.get('queue_capacity_packets')} {a.get('queue_cushion_source')}",
        "onn_cpu_mean_c": round(st.mean(onn), 2) if onn else None,
        "onn_cpu_max_c": round(max(onn), 2) if onn else None,
        "onn_thermal_status_values": sorted({x for x in st_ if x is not None}),
        "_raw": {"minutes": mins, "spike": d["spike_20_ms"], "stale": d["stale_output_drops"],
                 "vlost": v["lost_packets"], "alost": a["lost_packets"], "rendered": d["rendered_frames"],
                 "frames": v["frames"], "under": a["underruns"], "hist": h},
    }


rows = {s: score(s) for s in SESS if os.path.exists(os.path.join(R, f"report_{s}.json"))}
if len(rows) == 2:
    c, w = rows["C"]["_raw"], rows["W"]["_raw"]
    mins = c["minutes"] + w["minutes"]
    secs = mins * 60
    hist = [x + y for x, y in zip(c["hist"], w["hist"])]
    rend, recv = (c["rendered"] + w["rendered"]) / secs, (c["frames"] + w["frames"]) / secs
    rows["pair"] = {
        "spikes_20_per_min": (c["spike"] + w["spike"]) / mins, "rendered_fps": rend, "received_au_fps": recv,
        "max_output_gap_ms": max(rows["C"]["max_output_gap_ms"], rows["W"]["max_output_gap_ms"]),
        "stale_output_drops_per_min": (c["stale"] + w["stale"]) / mins,
        "video_lost_per_min_post_fec": (c["vlost"] + w["vlost"]) / mins,
        "audio_lost_per_min_after_dedup": (c["alost"] + w["alost"]) / mins,
        "audio_underruns_total": c["under"] + w["under"],
        "audio_underruns_per_min": (c["under"] + w["under"]) / mins,
        "frames_under_20ms_pct": 100.0 * hist[0] / sum(hist), "client_fps_deficit": recv - rend,
    }

keys = [k for k in rows["C"] if not k.startswith("_")]
print(f"{'row':34s}" + "".join(f"{s:>16s}" for s in rows))
for k in keys:
    cells = []
    for s in rows:
        x = rows[s].get(k, "")
        cells.append(f"{x:16.2f}" if isinstance(x, float) else f"{str(x):>16s}")
    print(f"{k:34s}" + "".join(cells))

TARGETS = [("spikes_20_per_min", lambda x: x < 200, "< 200"),
           ("rendered_fps", lambda x: x >= 59.5, ">= 59.5"),
           ("stale_output_drops_per_min", lambda x: x < 20, "< 20"),
           ("video_lost_per_min_post_fec", lambda x: x < 10, "< 10"),
           ("audio_underruns_per_min", lambda x: x < 5, "< 5 / min (table's wording; total also reported)")]
fails = []
print("\n== rows with a numeric target, per session")
for k, ok, txt in TARGETS:
    res = {s: ok(rows[s][k]) for s in SESS}
    print(f"  {k:30s} {txt:48s} " + "  ".join(f"{s} {rows[s][k]:.2f} {'PASS' if res[s] else 'FAIL'}" for s in SESS))
    fails += [(k, s, rows[s][k], txt) for s in SESS if not res[s]]
gap = {s: rows[s]["max_output_gap_ms"] for s in SESS}
gap_ok = all(g <= 250 for g in gap.values())
print(f"  max_output_gap_ms (transport row; <= 100 target, verdict bound <= 250): " +
      "  ".join(f"{s} {g} {'<=250' if g <= 250 else '>250'}" for s, g in gap.items()))
if not fails and gap_ok:
    verdict = "BASELINE MET"
else:
    verdict = "BASELINE NOT MET"
if not gap_ok:
    fails.append(("max_output_gap_ms", [s for s in SESS if gap[s] > 250], gap, "<= 250 (verdict bound)"))
trig = any(rows[s]["spikes_20_per_min"] >= 200 or rows[s]["rendered_fps"] < 59.5 for s in SESS)
print(f"\n== VERDICT: {verdict}" + ("" if not fails else f" -- failing: {fails}"))
print(f"== client decision (Step 5): {'TRIGGERED' if trig else 'NOT TRIGGERED'} "
      f"(spikes {rows['C']['spikes_20_per_min']:.1f} / {rows['W']['spikes_20_per_min']:.1f} per min; "
      f"fps {rows['C']['rendered_fps']:.2f} / {rows['W']['rendered_fps']:.2f})")
json.dump({"rows": {s: {k: v for k, v in r.items() if not k.startswith("_")} for s, r in rows.items()},
           "verdict": verdict, "failing": [list(map(str, f)) for f in fails], "client_decision_triggered": trig},
          open(os.path.join(HERE, "closeout_summary.json"), "w"), indent=1)
