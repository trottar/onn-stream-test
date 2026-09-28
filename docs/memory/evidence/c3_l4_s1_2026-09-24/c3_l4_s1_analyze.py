#!/usr/bin/env python3
"""C3-L4-S1: score the shadow night. Read-only.

Per hold (runs/index.txt T0..T1): the close-out rows from the decoder report
(as d_base_closeout_2026-09-23/closeout_score.py defines them), the shadow
decision log's lines inside the hold (shadow_log.jsonl, the night's slice of
logs/games/adaptive_bitrate_shadow.jsonl), the status at the end of the hold
(runs/status_end_*.json: adaptive_bitrate counters), onn thermal (t2).

Pre-registered reading (handoffs/C3-L4-S1_SHADOW_CONTROLLER_TASK.md):
  a hold is HEALTHY if every close-out target row passes (spikes/min < 200,
  rendered fps >= 59.5, stale drops/min < 20, video loss/min post-FEC < 10,
  audio underruns/min < 5; max output gap reported, verdict bound <= 250 ms);
  a hold failing a target row has its would-acts reported separately and not
  counted against the controller.
  On healthy holds: SILENT if 0 FALLBACK and 0 ROUTINE would-acts across all
  four; NOISY otherwise, every would-act listed. TELEMETRY_STALE entries are
  reported, never would-acts.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")
ARMS = ["H1", "H2", "H3", "H4"]
idx = {}
for line in open(os.path.join(R, "index.txt")):
    f = line.split()
    if f and f[0] in ARMS and len(f) >= 6:
        idx[f[0]] = f
log = [json.loads(l) for l in open(os.path.join(HERE, "shadow_log.jsonl"))] \
    if os.path.exists(os.path.join(HERE, "shadow_log.jsonl")) else []
heat = [json.loads(l) for l in open(os.path.join(HERE, "t2_samples.jsonl"))] \
    if os.path.exists(os.path.join(HERE, "t2_samples.jsonl")) else []
TARGETS = [("spikes_20_per_min", lambda x: x < 200, "< 200"),
           ("rendered_fps", lambda x: x >= 59.5, ">= 59.5"),
           ("stale_output_drops_per_min", lambda x: x < 20, "< 20"),
           ("video_lost_per_min_post_fec", lambda x: x < 10, "< 10"),
           ("audio_underruns_per_min", lambda x: x < 5, "< 5")]

print("C3-L4-S1 shadow night -- read-only scoring")
print(f"shadow log lines {len(log)}, t2 rows {len(heat)}")
healthy_acts, other_acts, summary = [], [], []
for arm in ARMS:
    if arm not in idx:
        print(f"\n== {arm}: NOT RUN / no index line")
        continue
    f = idx[arm]
    t0, t1 = f[4], f[5]
    rp = os.path.join(R, f"report_{arm}.json")
    print(f"\n== {arm}: {t0} .. {t1} (hold {f[2]} s), report {f[3]}")
    rows, healthy = {}, None
    if os.path.exists(rp):
        rep = json.load(open(rp))["report"]
        d, v, a = rep["decoder"], rep["video"], rep["audio"]
        secs = rep["duration_ms"] / 1000.0
        mins = secs / 60.0
        rows = {"spikes_20_per_min": d["spike_20_ms"] / mins, "rendered_fps": d["rendered_frames"] / secs,
                "stale_output_drops_per_min": d["stale_output_drops"] / mins,
                "video_lost_per_min_post_fec": v["lost_packets"] / mins,
                "audio_underruns_per_min": a["underruns"] / mins}
        fails = [k for k, ok, _ in TARGETS if not ok(rows[k])]
        healthy = not fails
        for k, ok, txt in TARGETS:
            print(f"   {k:<30} {rows[k]:9.2f}  target {txt:<8} {'PASS' if ok(rows[k]) else 'FAIL'}")
        print(f"   {'max_output_gap_ms':<30} {d['max_output_gap_ms']:9}  (transport row; bound <= 250)")
        print(f"   duration {mins:.2f} min; audio underruns total {a['underruns']}; ssrc_changes {v['ssrc_changes']}")
        print(f"   -> {'HEALTHY' if healthy else 'NOT HEALTHY (' + ', '.join(fails) + ')'} by the close-out target rows")
    else:
        print("   no decoder report: health not scorable")
    onn = [(x.get("onn") or {}).get("cpu_thermal_c") for x in heat if t0 <= x["at_utc"][:19] + "Z" <= t1]
    onn = [x for x in onn if x]
    if onn:
        print(f"   onn cpu-thermal {min(onn):.1f}-{max(onn):.1f} C, warm (>= 67.5) share "
              f"{100.0 * sum(1 for x in onn if x >= 67.5) / len(onn):.0f} %")
    inside = [r for r in log if t0 <= r["at_utc"][:19] + "Z" <= t1]
    acts = [r for r in inside if r.get("event") == "would_act"]
    holds = [r for r in inside if r.get("event") == "hold"]
    stale = [r for r in inside if r.get("event") == "state" and r.get("to") == "TELEMETRY_STALE"]
    states = {}
    for r in inside:
        if r.get("event") == "state":
            states[r["to"] + "/" + r["reason"]] = states.get(r["to"] + "/" + r["reason"], 0) + 1
    print(f"   shadow lines in hold {len(inside)}: would-acts {len(acts)} "
          f"(FALLBACK {sum(1 for r in acts if r['class'] == 'FALLBACK')}, ROUTINE "
          f"{sum(1 for r in acts if r['class'] == 'ROUTINE')}, up {sum(1 for r in acts if r['direction'] == 'up')}), "
          f"oscillation holds {len(holds)}, TELEMETRY_STALE entries {len(stale)}")
    print(f"   state changes: {states}")
    print(f"   acted true anywhere: {any(r.get('acted') is not False for r in inside)}")
    se = os.path.join(R, f"status_end_{arm}.json")
    if os.path.exists(se):
        ab = json.load(open(se)).get("adaptive_bitrate") or {}
        print(f"   status at end of hold: mode {ab.get('mode')}, state {ab.get('state')}, reason {ab.get('reason')}, "
              f"reports_evaluated {ab.get('reports_evaluated')}, would_act {ab.get('would_act')}, "
              f"suppressed {ab.get('suppressed')}, stale events {ab.get('telemetry_stale_events')}, "
              f"telemetry_age_ms {ab.get('telemetry_age_ms')}, acted {ab.get('acted')}")
    for r in acts:
        print(f"     WOULD-ACT {r['at_utc']} elapsed {r.get('session_elapsed_ms')} {r['class']} {r['direction']} "
              f"{r.get('from_kbps')}->{r.get('to_kbps')}: {json.dumps(r.get('measurements'))}")
    (healthy_acts if healthy else other_acts).extend(
        [(arm, r) for r in acts if r["class"] in ("FALLBACK", "ROUTINE")])
    summary.append((arm, healthy, len(acts)))

print("\n== READING (pre-registered)")
hh = [s for s in summary if s[1]]
print(f"holds scored {len(summary)}; healthy {len(hh)} ({', '.join(s[0] for s in hh) or 'none'}); "
      f"FALLBACK/ROUTINE would-acts on healthy holds {len(healthy_acts)}, on the others {len(other_acts)}")
if not hh:
    print("-> no healthy hold: the SILENT / NOISY reading has no hold to apply to (see the record)")
elif not healthy_acts:
    print(f"-> SILENT on the {len(hh)} healthy hold(s)")
else:
    print("-> NOISY")
