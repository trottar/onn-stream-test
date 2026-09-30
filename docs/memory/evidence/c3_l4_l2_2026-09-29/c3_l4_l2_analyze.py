#!/usr/bin/env python3
"""C3-L4-L2: score Session B2 (the climb under the blend). Read-only.
Rules: c3_l4_l2_b2_preregistration.txt (written before B2 ran).

Inputs (runs/): index.txt; report_B2.json; decision_log_B2.jsonl (the
controller log's slice -- now with one `sample` row per report);
abr_series_B2.jsonl; armcheck_B2.json; status_end_B2.json; inject1_B2.json,
inject2_B2.json; runs/recovery_log.jsonl.
Output gap per SSRC change: the largest output_gap_ms among the report's
retained slow events in [ssrc, ssrc + 1 s] (as C3.L3a-S1 and L1 scored it).
"""
import json
import os
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")
S1_MEDIAN_MS = 186.5
TARGETS = [("spikes_20_per_min", lambda x: x < 200, "< 200"),
           ("rendered_fps", lambda x: x >= 59.5, ">= 59.5"),
           ("stale_output_drops_per_min", lambda x: x < 20, "< 20"),
           ("video_lost_per_min_post_fec", lambda x: x < 10, "< 10"),
           ("audio_underruns_per_min", lambda x: x < 5, "< 5")]


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def jf(p):
    if not os.path.exists(p):
        return None
    body, code = open(p).read().rsplit("\nHTTP ", 1)
    return {"http": int(code.strip()), "body": json.loads(body)}


idx = {l.split()[0]: l.split() for l in open(os.path.join(R, "index.txt")) if l.split() and l.split()[0] == "B2"}
if "B2" not in idx:
    print("B2 NOT RUN")
    raise SystemExit(0)
f = idx["B2"]
t0, t1 = f[4], f[5]
print("C3-L4-L2 Session B2 -- read-only scoring (rules: c3_l4_l2_b2_preregistration.txt)")
print(f"   {t0} .. {t1}, report {f[3]}")
ac = json.load(open(os.path.join(R, "armcheck_B2.json")))
anyo = (ac.get("encoder_overrides") or {}).get("any_override")
print(f"   at PLAYING: any_override {anyo}; adaptive_bitrate {(ac.get('adaptive_bitrate') or {}).get('mode')}; "
      f"bitrate {ac.get('bitrate_kbps')}; profile {ac.get('profile_id')}")

rep = json.load(open(os.path.join(R, "report_B2.json")))["report"] if os.path.exists(os.path.join(R, "report_B2.json")) else None
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
    print(f"   duration {mins:.2f} min; ssrc_changes {v['ssrc_changes']}")

log = jl(os.path.join(R, "decision_log_B2.jsonl"))
samples = [r for r in log if r.get("event") == "sample"]
tr = [r for r in log if r.get("event") == "transition"]
done = [r for r in log if r.get("event") in ("transition_done", "transition_aborted", "actuator_failed")]
ref = [r for r in log if r.get("event") == "refused"]
holds = [r for r in log if r.get("event") == "hold"]
i1, i2 = jf(os.path.join(R, "inject1_B2.json")), jf(os.path.join(R, "inject2_B2.json"))
ssrc = [x["elapsed_ms"] for x in ((rep or {}).get("stream_discontinuities") or []) if x.get("type") == "ssrc_change"]
print(f"   decision log: {len(log)} rows, {len(samples)} sample rows; transitions {len(tr)}; done "
      f"{[(r['event'], r.get('actuation_ms')) for r in done]}; refusals {[(r['class'], r['reason'], r.get('injected')) for r in ref]}; holds {len(holds)}")
print(f"   injection 1: HTTP {i1 and i1['http']} {[(e.get('event'), e.get('class'), e.get('from_kbps'), e.get('to_kbps')) for e in (i1 or {}).get('body', {}).get('events', [])]}")
print(f"   injection 2: HTTP {i2 and i2['http']} {[(e.get('event'), e.get('reason'), e.get('hold_down_left_reports')) for e in (i2 or {}).get('body', {}).get('events', [])]}")
print(f"   decoder ssrc_change elapsed_ms: {ssrc}")


def gap_after(ms):
    cols = rep.get("slow_event_columns") or []
    gi, ei = cols.index("output_gap_ms"), cols.index("elapsed_ms")
    rows = (rep.get("slow_events_ge_50_ms") or []) + (rep.get("slow_events_top_gap") or [])
    inside = [r[gi] for r in rows if ms <= r[ei] <= ms + 1000]
    return max(inside) if inside else None


out = []
prev_done_at = None
for k, r in enumerate(tr):
    e = r.get("session_elapsed_ms") or 0
    dn = done[k] if k < len(done) else {}
    match = next((s for s in ssrc if e <= s <= e + 15000), None)
    since = [s for s in samples if prev_done_at and prev_done_at < s["at_utc"] <= r["at_utc"]
             and s.get("disposition") in ("evaluated", "blackout", "resync")]
    m = r.get("measurements") or {}
    out.append({"at_utc": r["at_utc"], "elapsed_ms": e, "class": r["class"], "from": r["from_kbps"], "to": r["to_kbps"],
                "injected": r.get("injected"), "window_reports": m.get("window_reports"),
                "clean_reports": m.get("clean_reports"), "reports_since_prev_change": len(since) if prev_done_at else None,
                "result": dn.get("event"), "actuation_ms": dn.get("actuation_ms"), "cycle": dn.get("cycle"),
                "ssrc_elapsed_ms": match, "gap_ms": gap_after(match) if (rep and match is not None) else None})
    prev_done_at = dn.get("at_utc")
print("   transitions (time, class, from->to, window reports/clean, reports since the previous SSRC change, "
      "result, actuation, ssrc, gap in [ssrc, +1 s] vs 186.5):")
for x in out:
    print(f"     {x['at_utc']} {x['class']:8s} {x['from']}->{x['to']} window {x['window_reports']}/{x['clean_reports']} "
          f"since {x['reports_since_prev_change']} {x['result']} {x['actuation_ms']} ms ssrc@{x['ssrc_elapsed_ms']} "
          f"gap {x['gap_ms']} ms" + (f" ({x['gap_ms'] - S1_MEDIAN_MS:+.1f})" if x['gap_ms'] is not None else ""))

st = (json.load(open(os.path.join(R, "status_end_B2.json"))).get("adaptive_bitrate") or {})
p = st.get("policy") or {}
print(f"   status before BACK: mode {st.get('mode')}, state {st.get('state')}, level {st.get('level')}, transitions "
      f"{st.get('transitions_this_session')}, rate_limited {st.get('rate_limited')}, suppressed {p.get('suppressed')}, "
      f"window {p.get('increase_window', {}).get('reports')}/{p.get('increase_window', {}).get('clean')}")

# the per-report samples: dispositions and the clean share by level
from collections import Counter
disp = Counter(s.get("disposition") for s in samples)
by_level = {}
for s in samples:
    if s.get("disposition") == "evaluated":
        b = by_level.setdefault(s.get("level_kbps"), [0, 0])
        b[0] += 1
        b[1] += 1 if s.get("clean") else 0
print(f"   sample dispositions {dict(disp)}; clean share by level "
      f"{ {k: f'{v[1]}/{v[0]} ({100 * v[1] / v[0]:.1f} %)' for k, v in sorted(by_level.items())} }")
unclean_why = Counter()
for s in samples:
    if s.get("disposition") == "evaluated" and not s.get("clean"):
        why = []
        if (s.get("fps") or 0) < 57:
            why.append("fps<57")
        if (s.get("queue_depth") or 0) > 1:
            why.append("queue>1")
        if (s.get("output_gap_ms") or 0) > 150:
            why.append("gap>150")
        unclean_why[" & ".join(why) or "other"] += 1
print(f"   why a report was not clean: {dict(unclean_why)}")

rec = [r for r in jl(os.path.join(R, "recovery_log.jsonl"))]
def shift(t, s):
    return (datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ") + timedelta(seconds=s)).strftime("%Y-%m-%dT%H:%M:%SZ")
rec_ev = [r["event"] for r in rec if shift(t0, -60) <= r["at_utc"][:19] + "Z" <= shift(t1, 60)]
resets = [r for r in log if r.get("event") == "session_ended_reset" and r.get("at_utc", "")[:19] + "Z" >= t1]

first = out[0] if out else None
ups = [x for x in out if x["class"] == "INCREASE"]
upper = ups[0]["elapsed_ms"] if ups else 10 ** 12
w1_n = sum(1 for s in ssrc if first and first["elapsed_ms"] <= s < upper)
ev2 = ((i2 or {}).get("body") or {}).get("events") or []
blk = (p.get("suppressed") or {}).get("blackout")
n_done = sum(1 for x in out if x["result"] == "transition_done")
w1 = bool(first and first["injected"] and first["class"] == "FALLBACK" and first["to"] == 5000
          and first["result"] == "transition_done" and w1_n == 1
          and ev2 and ev2[0].get("event") == "refused" and ev2[0].get("reason") == "hold_down"
          and blk is not None and blk >= 3 * n_done)
seq = [(x["from"], x["to"]) for x in ups]
w2 = (seq == [(5000, 5500), (5500, 6000), (6000, 7000)]
      and all((x["reports_since_prev_change"] or 0) >= 93 and x["result"] == "transition_done" for x in ups))
last_up_at = ups[-1]["at_utc"] if ups else None
after_7000 = [x for x in out if last_up_at and x["at_utc"] > last_up_at]
w3 = bool(ups and seq and seq[-1] == (6000, 7000) and not after_7000 and not holds)
# the pre-registration lists "the close-out rows met (reported)" among the WIRED conditions: applied as a row
w4 = (len(ssrc) == 4 and rep is not None and "session_started" in rec_ev and "session_ended" in rec_ev
      and not any(e in ("desync_pause", "encoder_restart", "gave_up_saved") for e in rec_ev)
      and fails == [])
print(f"   W1 one ssrc_change to 5000 ({w1_n}), gap {first and first['gap_ms']} ms, blackout {blk} for {n_done} "
      f"changes, 2nd injection refused hold_down: {'MET' if w1 else 'NOT MET'}")
print(f"   W2 climb {seq}: {'MET' if w2 else 'NOT MET'}")
for x in ups:
    print(f"      {x['at_utc']} {x['from']}->{x['to']}: window {x['window_reports']}/{x['clean_reports']} clean, "
          f"{x['reports_since_prev_change']} reports since the previous change, gap {x['gap_ms']} ms")
if ups and last_up_at:
    held = (datetime.strptime(t1, "%Y-%m-%dT%H:%M:%SZ") - datetime.strptime(last_up_at[:19], "%Y-%m-%dT%H:%M:%S")).total_seconds()
    print(f"   W3 at 7000 from {last_up_at} for {held:.0f} s to the end of the hold, transitions after it "
          f"{len(after_7000)}: {'MET' if w3 else 'NOT MET'}")
else:
    print(f"   W3 at 7000 for the rest of the hold: NOT MET (7000 not reached)")
print(f"   W4 ssrc_changes {len(ssrc)} (4), report {'stored' if rep else 'MISSING'}, recovery events {rec_ev}, "
      f"close-out fails {fails}: {'MET' if w4 else 'NOT MET'}; controller after BACK "
      f"{[(r['at_utc'], (r.get('before') or {}).get('level_kbps'), r.get('level_kbps')) for r in resets]}")
missed = [n for n, ok in (("W1", w1), ("W2", w2), ("W3", w3), ("W4", w4)) if not ok]
cls = "WIRED" if not missed else "PARTIAL (" + ", ".join(missed) + ")"
print(f"   close-out rows (reported): fails {fails}")
print(f"   -> Session B2: {cls}")
json.dump({"classification": cls, "transitions": out, "ssrc_changes": ssrc, "missed": missed,
           "any_override_at_playing": anyo, "closeout_fails": fails, "sample_dispositions": dict(disp),
           "clean_share_by_level": by_level}, open(os.path.join(HERE, "c3_l4_l2_summary.json"), "w"), indent=1, default=str)
