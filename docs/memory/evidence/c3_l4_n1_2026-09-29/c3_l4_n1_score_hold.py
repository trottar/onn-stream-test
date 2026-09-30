#!/usr/bin/env python3
"""C3-L4-N1 section 4: score the silent live hold (Session H). Read-only.
Rules: c3_l4_n1_hold_preregistration.txt (written before the hold).

Inputs (runs/): index.txt; report_H.json; decision_log_H.jsonl (the
controller log's slice, one `sample` row per report); armcheck_H.json;
status_end_H.json; abr_series_H.jsonl; recovery_log_H.jsonl (the companion's
recovery log sliced to the hold).
"""
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")
TARGETS = [("spikes_20_per_min", lambda x: x < 200, "< 200"),
           ("rendered_fps", lambda x: x >= 59.5, ">= 59.5"),
           ("stale_output_drops_per_min", lambda x: x < 20, "< 20"),
           ("video_lost_per_min_post_fec", lambda x: x < 10, "< 10"),
           ("audio_underruns_per_min", lambda x: x < 5, "< 5")]


def jl(p):
    return [json.loads(x) for x in open(p) if x.strip()] if os.path.exists(p) else []


idx = [l.split() for l in open(os.path.join(R, "index.txt")) if l.split() and l.split()[0] == "H"]
if not idx:
    print("H NOT RUN")
    raise SystemExit(0)
f = idx[-1]
t0, t1 = f[4], f[5]
print("C3-L4-N1 Session H -- the silent live hold, read-only scoring (rules: c3_l4_n1_hold_preregistration.txt)")
print(f"   {t0} .. {t1}, report {f[3]}")
ac = json.load(open(os.path.join(R, "armcheck_H.json")))
anyo = (ac.get("encoder_overrides") or {}).get("any_override")
abr = ac.get("adaptive_bitrate") or {}
pol = abr.get("policy") or {}
print(f"   at PLAYING: any_override {anyo}; adaptive_bitrate mode {abr.get('mode')} configured "
      f"{abr.get('configured_mode')} inject {bool(abr.get('inject_enabled'))}; bitrate {ac.get('bitrate_kbps')}; "
      f"profile {ac.get('profile_id')}")
print(f"   the new rules in force (status): capacity {(pol.get('capacity_trigger') or {}).get('rule')}; "
      f"backstop {(pol.get('recovery_escalation') or {}).get('rule')}")

rep = json.load(open(os.path.join(R, "report_H.json")))["report"] if os.path.exists(os.path.join(R, "report_H.json")) else None
fails = None
if rep:
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    secs = rep["duration_ms"] / 1000.0
    mins = secs / 60.0
    rows = {"spikes_20_per_min": d["spike_20_ms"] / mins, "rendered_fps": d["rendered_frames"] / secs,
            "stale_output_drops_per_min": d["stale_output_drops"] / mins,
            "video_lost_per_min_post_fec": v["lost_packets"] / mins, "audio_underruns_per_min": a["underruns"] / mins}
    fails = [k for k, ok, _ in TARGETS if not ok(rows[k])]
    for k, ok, txt in TARGETS:
        print(f"   {k:<30} {rows[k]:9.2f}  target {txt:<8} {'PASS' if ok(rows[k]) else 'FAIL'}")
    print(f"   {'max_output_gap_ms':<30} {d['max_output_gap_ms']:9}  (reported; bound <= 250)")
    print(f"   duration {mins:.2f} min; ssrc_changes {v.get('ssrc_changes')}; sequence_resyncs "
          f"{v.get('sequence_resyncs')}; lost {v.get('lost_packets')} (in resyncs {v.get('lost_packets_in_resyncs')})")

log = jl(os.path.join(R, "decision_log_H.jsonl"))
samples = [r for r in log if r.get("event") == "sample"]
acted = [r for r in log if r.get("event") in ("transition", "would_act", "hold")]
armed = [r for r in log if r.get("event") == "escalation_armed"]
ref = [r for r in log if r.get("event") == "refused"]
ssrc = [r for r in log if r.get("event") == "ssrc_change"]
print(f"   decision log: {len(log)} rows, {len(samples)} sample rows; events {dict(Counter(r.get('event') for r in log))}")
print(f"   transitions / would_act / holds {len(acted)}; escalation_armed {len(armed)}; refused {len(ref)} "
      f"{[(r.get('class'), r.get('reason'), r.get('trigger')) for r in ref]}; ssrc_change {len(ssrc)}")
disp = Counter(s.get("disposition") for s in samples)
evl = [s for s in samples if s.get("disposition") == "evaluated"]
print(f"   sample dispositions {dict(disp)}; clean (the blend) {sum(1 for s in evl if s.get('clean'))}/{len(evl)}")
# the capacity bar's near misses: over every 5 consecutive evaluated reports
best_fps, best_loss, both = 0, 0, 0
for i in range(len(evl) - 4):
    w = evl[i:i + 5]
    nf = sum(1 for s in w if isinstance(s.get("fps"), (int, float)) and s["fps"] < 50)
    nl = sum(1 for s in w if isinstance(s.get("lost_packets_delta"), (int, float)) and s["lost_packets_delta"] >= 50)
    best_fps, best_loss = max(best_fps, nf), max(best_loss, nl)
    both = max(both, min(nf, 5) if nl >= 3 else 0)
fps = [s["fps"] for s in evl if isinstance(s.get("fps"), (int, float))]
lost = [s["lost_packets_delta"] for s in evl if isinstance(s.get("lost_packets_delta"), (int, float))]
print(f"   capacity bar near misses (any 5 evaluated): most under 50 fps {best_fps}/5; most with lost >= 50 "
      f"{best_loss}/5 (the bar: 5/5 AND 3/5); reports under 50 fps {sum(1 for x in fps if x < 50)}, with lost >= 50 "
      f"{sum(1 for x in lost if x >= 50)}; max lost per report {max(lost) if lost else None}; min fps "
      f"{min(fps) if fps else None}")
rec = jl(os.path.join(R, "recovery_log_H.jsonl"))
rec_ev = [r["event"] for r in rec]
print(f"   recovery log in the hold: {rec_ev}")
st = (json.load(open(os.path.join(R, "status_end_H.json"))).get("adaptive_bitrate") or {})
print(f"   status before BACK: mode {st.get('mode')}, state {st.get('state')}, level {st.get('level')}, transitions "
      f"{st.get('transitions_this_session')}, rate_limited {st.get('rate_limited')}, escalation armed "
      f"{((st.get('policy') or {}).get('recovery_escalation') or {}).get('armed')}")
series = jl(os.path.join(R, "abr_series_H.jsonl"))
print(f"   status poller: {len(series)} rows; levels {dict(Counter(x.get('level') for x in series))}; "
      f"transitions max {max((x.get('transitions_this_session') or 0) for x in series) if series else None}")
silent = (not acted and not armed and (st.get("transitions_this_session") == 0) and fails == [])
missed = []
if acted or armed or st.get("transitions_this_session"):
    missed.append("transitions")
if fails:
    missed.append("close-out rows " + ", ".join(fails))
cls = "SILENT" if silent else "NOT SILENT (" + "; ".join(missed) + ")"
print(f"   -> Session H: {cls}")
json.dump({"classification": cls, "closeout_fails": fails, "any_override_at_playing": anyo,
           "acted": len(acted), "escalation_armed": len(armed), "refused": len(ref),
           "sample_dispositions": dict(disp), "near_miss": {"fps_under_50_of_5": best_fps,
                                                            "lost_ge_50_of_5": best_loss},
           "recovery_events": rec_ev}, open(os.path.join(HERE, "c3_l4_n1_hold_summary.json"), "w"), indent=1)
