#!/usr/bin/env python3
"""C3-L4-N1 section 1: score the user's first nft night, READ-ONLY.

    python3 c3_l4_n1_score_night1.py [run_dir] > c3_l4_n1_night1_score.txt

Rules: the night's own `preregistration.txt` (sha256 fb5ca63f...), rows F1a-d,
F2a, F3a-b, Ka-c and the all-sessions rows. Default input is the redacted
copy `evidence/c3_l4_nft_night1_2026-09-29/` (the original run dir,
`logs/streaming/c3_l4_nft_night_20260929_151942Z/`, gives the same output:
the redaction touched only the address fields of the status/report JSON).

Phases come from the harness's own events.jsonl (fault_on / fault_off / did /
back); the per-report figures from the controller's `sample` rows in
decision_log.jsonl; recovery cycles from recovery_log.jsonl; the close-out
rows from each session's decoder report (reported, as the pre-registration
says).
"""
import hashlib
import json
import os
import statistics
import sys
from collections import Counter
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "c3_l4_nft_night1_2026-09-29")
PREREG_SHA = "fb5ca63fe559e5b2f99eb670d38fb21532f55f2fdd98883ca3f3f0678f57c531"
TARGETS = [("spikes_20_per_min", lambda x: x < 200, "< 200"),
           ("rendered_fps", lambda x: x >= 59.5, ">= 59.5"),
           ("stale_output_drops_per_min", lambda x: x < 20, "< 20"),
           ("video_lost_per_min_post_fec", lambda x: x < 10, "< 10"),
           ("audio_underruns_per_min", lambda x: x < 5, "< 5")]


def jl(name):
    p = os.path.join(RUN, name)
    return [json.loads(x) for x in open(p) if x.strip()]


def ts(t):
    return datetime.strptime(t[:23], "%Y-%m-%dT%H:%M:%S.%f").timestamp()


def q(vals, p):
    v = sorted(vals)
    return v[min(len(v) - 1, int(round(p * (len(v) - 1))))] if v else None


out = []
P = out.append
pre = open(os.path.join(RUN, "preregistration.txt"), "rb").read()
sha = hashlib.sha256(pre).hexdigest()
P("C3-L4-N1 section 1 -- the user's first nft night, scored read-only against its pre-registration")
P(f"run: c3_l4_nft_night_20260929_151942Z; preregistration.txt sha256 {sha[:16]}... "
  f"{'MATCHES' if sha == PREREG_SHA else 'DOES NOT MATCH'} the recorded fb5ca63f...")
summ = json.load(open(os.path.join(RUN, "summary.json")))
ev = jl("events.jsonl")
log = jl("decision_log.jsonl")
rec = jl("recovery_log.jsonl")
samples = [r for r in log if r.get("event") == "sample"]
P(f"rows: decision log {len(log)} ({len(samples)} sample rows), recovery log {len(rec)}, events {len(ev)}")
cal = summ["calibration"]
P(f"calibration: 7000 wire rate {cal['rate_7000_bytes_per_s'] / 1000:.0f} kB/s ({cal['source']}); cap "
  f"{cal['cap_kbytes_per_s']} kbytes/s (nft kbytes = 1024 B) = {cal['cap_kbytes_per_s'] * 1024 / 1000:.0f} kB/s "
  f"= {cal['cap_kbytes_per_s'] * 1024 / cal['rate_7000_bytes_per_s']:.3f} x the 7000 rate "
  f"(5500/7000 = 0.786, 5750/7000 = 0.821, 6000/7000 = 0.857: between the 5500 and 6000 wire rates, "
  f"assuming the wire rate scales with the rung)")

# ---- phases from the harness's events ------------------------------------
phases = []          # (session, label, t0, t1)
cur_on = {}
sess_play, sess_back = {}, {}
for e in ev:
    s = e.get("session")
    if e["event"] == "playing":
        sess_play[s] = e["at_utc"]
    if e["event"] == "back":
        sess_back[s] = e["at_utc"]
    if e["event"] == "fault_on" and e.get("what") != "calibration counter":
        if s in cur_on:          # F3: the drop replaces the cap (flush chain), no fault_off between
            what, t0 = cur_on.pop(s)
            phases.append((s, f"{what} ON", t0, e["at_utc"]))
        cur_on[s] = (e["what"], e["at_utc"])
    if e["event"] == "fault_off":
        what, t0 = cur_on.pop(s, (e.get("what"), None))
        phases.append((s, f"{what} ON", t0, e["at_utc"]))
dis = next((e for e in ev if e["event"] == "disable"), None)
t_dis = dis["first"][1]["disabled_at_utc"] if dis else None

# the baseline and off windows around each fault
windows = []
for s in ("F1", "F2", "F3", "K"):
    on = [p for p in phases if p[0] == s]
    first_on = min(p[2] for p in on)
    last_off = max(p[3] for p in on)
    windows.append((s, "baseline (PLAYING -> first fault)", sess_play[s], first_on))
    for p in on:
        windows.append(p)
    windows.append((s, "after removal (-> BACK)", last_off, sess_back[s]))


def in_win(r, t0, t1):
    return t0 <= r["at_utc"] < t1


P("")
P("== Per-report figures by phase (controller sample rows; 'evaluated' = fresh, distinct, outside a blackout)")
P("   phase | reports (evaluated) | fps median [p10-p90] min | lost/report median [max] | queue max (reports >= 1) "
  "| gap median [max] ms | clean share")
figs = {}
for s, label, t0, t1 in windows:
    rows = [r for r in samples if in_win(r, t0, t1)]
    evl = [r for r in rows if r.get("disposition") == "evaluated"]
    fps = [r["fps"] for r in evl if isinstance(r.get("fps"), (int, float))]
    lost = [r["lost_packets_delta"] for r in evl if isinstance(r.get("lost_packets_delta"), (int, float))]
    qd = [r["queue_depth"] for r in evl if isinstance(r.get("queue_depth"), (int, float))]
    gap = [r["output_gap_ms"] for r in evl if isinstance(r.get("output_gap_ms"), (int, float))]
    clean = sum(1 for r in evl if r.get("clean"))
    figs[(s, label)] = {"fps": fps, "lost": lost, "q": qd, "gap": gap, "rows": rows, "evl": evl}
    if not evl:
        P(f"   {s} {label}: {len(rows)} rows, none evaluated")
        continue
    P(f"   {s} {label} [{t0[11:19]}-{t1[11:19]}Z]: {len(rows)} ({len(evl)}) | "
      f"{statistics.median(fps):.1f} [{q(fps, .1):.1f}-{q(fps, .9):.1f}] {min(fps):.1f} | "
      f"{statistics.median(lost):.0f} [{max(lost)}] | {max(qd)} ({sum(1 for v in qd if v >= 1)}) | "
      f"{statistics.median(gap):.0f} [{max(gap)}] | {clean}/{len(evl)}")
    disp = Counter(r.get("disposition") for r in rows)
    P(f"      dispositions {dict(disp)}")

# onset: the first reports after each cap
P("")
P("== Onset under the cap (the first reports after the rule went in; every row, any disposition)")
for s, label, t0, t1 in windows:
    if "cap ON" not in label:
        continue
    rows = [r for r in samples if in_win(r, t0, t1)][:10]
    P(f"   {s} {label} from {t0[11:23]}Z:")
    for r in rows:
        P(f"      +{ts(r['at_utc']) - ts(t0):5.1f} s fps {r['fps'] if r['fps'] is None else round(r['fps'], 1)} "
          f"queue {r['queue_depth']} gap {r['output_gap_ms']} lost {r['lost_packets_delta']} "
          f"[{r['disposition']}; state {r['state']}]")
    first50 = next((r for r in [x for x in samples if in_win(x, t0, t1)]
                    if isinstance(r.get("fps"), (int, float)) and r["fps"] < 50), None)
    if first50:
        P(f"      first report under 50 fps: +{ts(first50['at_utc']) - ts(t0):.1f} s")
    allq = [r["queue_depth"] for r in samples if in_win(r, t0, t1) and isinstance(r.get("queue_depth"), (int, float))]
    P(f"      queue depth over the whole phase, every row: max {max(allq)}; rows with queue >= 1: "
      f"{sum(1 for v in allq if v >= 1)} of {len(allq)}")

# ---- the controller's own rows ---------------------------------------------
P("")
P("== Controller rows (every non-sample, non-state row)")
acted = [r for r in log if r.get("event") in ("transition", "transition_done", "transition_aborted",
                                                "actuator_failed", "would_act", "hold")]
ref = [r for r in log if r.get("event") == "refused"]
P(f"   transitions / would_act / holds: {len(acted)}")
P(f"   refused rows: {len(ref)}")
for r in ref:
    sess = next((w[0] for w in windows if in_win(r, w[2], w[3])), "?")
    m = r.get("measurements") or {}
    P(f"      {r['at_utc'][11:23]}Z {sess} {r['class']} -> {r['to_kbps']} refused {r['reason']} "
      f"guards failing {r.get('guards_failing')}; window fps {[round(x, 1) for x in m.get('fps', [])]} "
      f"queue {m.get('queue_depth')} gap {m.get('output_gap_ms')}")
ss = [r for r in log if r.get("event") == "ssrc_change"]
P(f"   ssrc_change rows: {len(ss)}, sources {dict(Counter(r.get('source') for r in ss))}")
ls = [r for r in log if r.get("event") == "level_sync"]
P(f"   level_sync rows: {len(ls)}; rate_limited in any sample/status: "
  f"{any((r.get('rate_limited') or False) for r in jl('abr_series.jsonl'))}")
lv = Counter(r.get("stream_kbps") for r in samples)
P(f"   stream_kbps over every sample row: {dict(lv)}")
st = Counter(r.get("state") for r in samples)
P(f"   controller state over every sample row: {dict(st)}")

# ---- the recovery cycles ------------------------------------------------------
P("")
P("== Recovery log per session (trigger; encoder restarts with the gap to the previous restart)")
rec_by = {}
for s in ("F1", "F2", "F3", "K"):
    t0, t1 = sess_play[s], sess_back[s]
    rows = [r for r in rec if t0 <= r["at_utc"] <= t1]
    rec_by[s] = rows
    er = [r for r in rows if r["event"] == "encoder_restart"]
    dp = [r for r in rows if r["event"] == "desync_pause"]
    rs = [r for r in rows if r["event"] == "resumed"]
    P(f"   {s}: desync_pause {len(dp)} (triggers {dict(Counter(r.get('trigger') for r in dp))}), "
      f"encoder_restart {len(er)}, resumed {len(rs)}")
    prev = None
    for r in er:
        gap = f"{ts(r['at_utc']) - ts(prev['at_utc']):6.1f} s after the previous" if prev else "first"
        P(f"      {r['at_utc'][11:23]}Z restart #{r['attempt']} {r['method']} backoff {r['backoff_ms']} "
          f"age pair {r.get('age_pair_ms')} first RTP {round((r.get('cycle') or {}).get('first_rtp_resume_ms') or 0)} ms"
          f" -- {gap}")
        prev = r
    if rs:
        P(f"      recovering_ms per resume: {[r['recovering_ms'] for r in rs]}")
    if er:
        span = (ts(er[-1]['at_utc']) - ts(er[0]['at_utc'])) / 60
        pairs = sum(1 for a, b in zip(er, er[1:]) if ts(b['at_utc']) - ts(a['at_utc']) <= 180)
        P(f"      {len(er)} restarts over {span:.1f} min; consecutive pairs within 180 s: {pairs}")
tail = [r for r in rec if datetime.fromtimestamp(ts(sess_back["F3"]) - 10).isoformat() <= r["at_utc"] <= sess_play["K"]]
if tail:
    P(f"   around F3's BACK: {[(r['at_utc'][11:23], r['event'], r.get('state'), r.get('trigger')) for r in tail]}")

# ---- the close-out rows per session (reported) --------------------------------
P("")
P("== Close-out rows per session (decoder report; reported, as the pre-registration says)")
closeout = {}
for s in ("F1", "F2", "F3", "K"):
    p = os.path.join(RUN, f"report_{s}.json")
    rep = json.load(open(p))["report"]
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    secs = rep["duration_ms"] / 1000.0
    mins = secs / 60.0
    rows = {"spikes_20_per_min": d["spike_20_ms"] / mins, "rendered_fps": d["rendered_frames"] / secs,
            "stale_output_drops_per_min": d["stale_output_drops"] / mins,
            "video_lost_per_min_post_fec": v["lost_packets"] / mins, "audio_underruns_per_min": a["underruns"] / mins}
    fails = [k for k, ok, _ in TARGETS if not ok(rows[k])]
    closeout[s] = {"rows": rows, "fails": fails, "max_gap": d["max_output_gap_ms"], "min": mins,
                   "ssrc": v.get("ssrc_changes"), "resyncs": v.get("sequence_resyncs"),
                   "lost_in_resyncs": v.get("lost_packets_in_resyncs")}
    P(f"   {s} ({mins:.1f} min): " + "; ".join(f"{k} {rows[k]:.2f}" for k, _, _ in TARGETS)
      + f"; max gap {d['max_output_gap_ms']} ms; ssrc_changes {v.get('ssrc_changes')}; sequence_resyncs "
        f"{v.get('sequence_resyncs')}; lost in resyncs {v.get('lost_packets_in_resyncs')} -> misses {fails or 'none'}")

# ---- the rows ---------------------------------------------------------------
S = summ["sessions"]
P("")
P("== Rows")
res = {}
f1 = S["F1"]
f1_tr = f1["cap_on"]["transitions"] + f1["cap_off"]["transitions"]
res["F1a"] = ("NOT MET", f"no decrease in 12 min under the cap (transitions {len(f1_tr)}); the controller stayed at "
              f"7000 in PRESSURE; its only FALLBACK decisions ({f1['cap_on']['refused']}) came during freezes, "
              f"when recovery was already PAUSED_RECOVERING, and were refused by the recovery guard")
res["F1b"] = ("NOT APPLICABLE", "no decrease, so no climb under the cap to score")
res["F1c"] = ("MET", f"rate_limited never true (cap on {f1['cap_on']['rate_limited_ever']}, off "
              f"{f1['cap_off']['rate_limited_ever']}); no transitions, so no spacing or ramp to break")
res["F1d"] = ("NOT APPLICABLE", "the stream never left 7000, so there was nothing to climb back; BACK reset the "
              "controller at 7000 (session_ended_reset, level 7000, transitions 0)")
f2 = S["F2"]
res["F2a"] = ("MET", f"0 decreases in the 10 min of 2 % loss and after (transitions "
              f"{len(f2['loss_on']['transitions']) + len(f2['loss_off']['transitions'])}); loss alone did not move "
              f"the controller; no recovery event in F2")
f3 = S["F3"]
f3_ref = [r for r in ref if in_win(r, sess_play["F3"], sess_back["F3"])]
f3_ok = all("recovery_playing" in (r.get("guards_failing") or []) for r in f3_ref)
res["F3a"] = ("MET" if f3_ok and not f3["cap_to_5000"]["transitions"] and not f3["drop"]["transitions"] else "NOT MET",
              f"no controller transition in F3; its {len(f3_ref)} FALLBACK decisions were refused guard "
              f"(recovery_playing false) while recovery was PAUSED_RECOVERING")
res["F3b"] = ("NOT TESTED", "the precondition (the stream at 5000 before the drop) was never met: the cap did not "
              "bring the stream down (F1a), so the drop hit a stream at 7000. What happened instead: recovery "
              "restarted at 7000 (C3-F1 level-preserving at 7000), each restart logged ssrc_change source "
              "recovery_restart with a 3-report blackout, and no level_sync occurred (the level never changed)")
K = S["K"]
d1, d2, stk = K["disable"]["first"], K["disable"]["second"], K["disable"]["status"]
ka = (d1[0] == 200 and d1[1]["already_disabled"] is False and d2[1]["already_disabled"] is True
      and stk["mode"] == "shadow" and stk["configured_mode"] == "live" and stk["acts"] is False)
res["Ka"] = ("MET" if ka else "NOT MET", f"#1 already_disabled {d1[1]['already_disabled']}, #2 "
             f"{d2[1]['already_disabled']}; status mode {stk['mode']}, configured_mode {stk['configured_mode']}, "
             f"acts {stk['acts']}")
k_after = [r for r in log if t_dis and r["at_utc"] >= t_dis and r.get("event") in ("transition", "transition_done")]
res["Kb"] = ("MET" if not k_after and K["disabled_cap_on"]["level"] == 7000 else "NOT MET",
             f"after the disable: no acted transition ({len(k_after)}); no would_act row either (no trigger "
             f"fired: the same shortfall as F1); level stayed {K['disabled_cap_on']['level']}")
res["Kc"] = ("MET" if K["mode_after_back"] == "live" else "NOT MET", f"mode after BACK {K['mode_after_back']}")
anyo = {s: S[s]["any_override_at_playing"] for s in S}
reps = {s: os.path.exists(os.path.join(RUN, f"report_{s}.json")) for s in S}
unint = {s: sum(1 for r in rec_by[s] if r["event"] == "encoder_restart") for s in ("F1", "F2", "K")}
f3_pre = sum(1 for r in rec_by["F3"] if r["event"] == "encoder_restart" and r["at_utc"] < "2026-09-29T16:05:09")
res["ALL-override"] = ("MET" if not any(anyo.values()) else "NOT MET", f"any_override at PLAYING {anyo}")
res["ALL-report"] = ("MET" if all(reps.values()) else "NOT MET", f"decoder report stored {reps}")
res["ALL-lifecycle"] = ("NOT MET", f"recovery cycles outside F3's intended drop: encoder restarts F1 {unint['F1']}, "
                        f"F2 {unint['F2']}, K {unint['K']}, and F3 {f3_pre} under the cap before the drop -- the "
                        f"cap's freezes, which the controller did not prevent (F1a)")
end_ok = summ["no_fault_table_at_end"] and summ["teardown_clean"] and summ["flags_after"] == [] \
    and summ["banner_count_at_end"] == 0
res["ALL-end"] = ("MET" if end_ok else "NOT MET", f"no privyhub_fault table {summ['no_fault_table_at_end']}; flags "
                  f"after {summ['flags_after']}; teardown clean {summ['teardown_clean']} (stream 7000, no game, "
                  f"flag absent from manager and environ, harness.log TEARDOWN); banners {summ['banner_count_at_end']}")
for k, (v, why) in res.items():
    P(f"   {k:14s} {v:15s} {why}")
held = [k for k, (v, _) in res.items() if v in ("NOT MET",)]
P("")
P(f"CLASSIFICATION: {'WORKS UNDER LOSS' if not held else 'NOT WORKS UNDER LOSS -- rows not held: ' + ', '.join(held)}"
  f"; not applicable: {', '.join(k for k, (v, _) in res.items() if v == 'NOT APPLICABLE')}; not tested: "
  f"{', '.join(k for k, (v, _) in res.items() if v == 'NOT TESTED')}")
print("\n".join(out))
json.dump({"rows": {k: v for k, (v, _) in res.items()}, "closeout": closeout,
           "refused": [{"at_utc": r["at_utc"], "class": r["class"], "reason": r["reason"],
                        "guards_failing": r.get("guards_failing")} for r in ref]},
          open(os.path.join(HERE, "c3_l4_n1_night1_score.json"), "w"), indent=1, default=str)
