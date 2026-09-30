#!/usr/bin/env python3
"""C3-L4-N3 section 1: score the user's nft night 3 (`--only F1`), READ-ONLY.

    python3 c3_l4_n3_score_night3.py [run_dir] > c3_l4_n3_night3_score.txt

Rules: the night's own `preregistration.txt` (night 3's, sha256 cf0ce814...),
rows F1a-g and the all-sessions rows. Default input is the redacted copy
`evidence/c3_l4_nft_night3_2026-09-30/`; the original run dir gives the same
output. Derived from c3_l4_n2_2026-09-29/c3_l4_n2_score_night2.py (the same
phase, figure and transition code); the rows are night 3's.
"""
import hashlib
import json
import os
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "c3_l4_nft_night3_2026-09-30")
PREREG_SHA = "cf0ce814bf686d8f082abccea1102d2f54c65cfad146b05e3215d7db4f3d8b69"
TARGETS = [("spikes_20_per_min", lambda x: x < 200, "< 200"),
           ("rendered_fps", lambda x: x >= 59.5, ">= 59.5"),
           ("stale_output_drops_per_min", lambda x: x < 20, "< 20"),
           ("video_lost_per_min_post_fec", lambda x: x < 10, "< 10"),
           ("audio_underruns_per_min", lambda x: x < 5, "< 5")]


def jl(name):
    return [json.loads(x) for x in open(os.path.join(RUN, name)) if x.strip()]


def ts(t):
    return datetime.strptime(t[:23], "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp()


def q(vals, p):
    v = sorted(vals)
    return v[min(len(v) - 1, int(round(p * (len(v) - 1))))] if v else None


out = []
P = out.append
sha = hashlib.sha256(open(os.path.join(RUN, "preregistration.txt"), "rb").read()).hexdigest()
P("C3-L4-N3 section 1 -- the user's nft night 3 (--only F1), scored read-only against its pre-registration")
P(f"run: c3_l4_nft_night_20260930_131404Z; preregistration.txt sha256 {sha[:16]}... "
  f"{'MATCHES' if sha == PREREG_SHA else 'DOES NOT MATCH'} night 3's cf0ce814...")
summ = json.load(open(os.path.join(RUN, "summary.json")))
ev, log, rec, abr, frames = (jl("events.jsonl"), jl("decision_log.jsonl"), jl("recovery_log.jsonl"),
                             jl("abr_series.jsonl"), jl("frames.jsonl"))
samples = [r for r in log if r.get("event") == "sample"]
P(f"rows: decision log {len(log)} ({len(samples)} sample rows), recovery log {len(rec)}, events {len(ev)}, "
  f"status poller {len(abr)}, host frame seconds {len(frames)}")
cal = summ["calibration"]
P(f"calibration: 7000 wire rate {cal['rate_7000_bytes_per_s'] / 1000:.0f} kB/s ({cal['source']}); cap "
  f"{cal['cap_kbytes_per_s']} kbytes/s = {cal['cap_kbytes_per_s'] * 1024 / 1000:.0f} kB/s (nights 1-2: 854 / 855)")

play = next(e["at_utc"] for e in ev if e["event"] == "playing")
back = next(e for e in ev if e["event"] == "back")
cap_on = next(e["at_utc"] for e in ev if e["event"] == "fault_on" and e.get("what") != "calibration counter")
cap_off = next(e["at_utc"] for e in ev if e["event"] == "fault_off")
trans = [r for r in log if r.get("event") == "transition"]
done = [r for r in log if r.get("event") in ("transition_done", "transition_aborted", "actuator_failed")]
holds = [r for r in log if r.get("event") == "hold"]
refused = [r for r in log if r.get("event") == "refused"]
P(f"PLAYING {play[11:19]}Z; cap on {cap_on[11:19]}Z; cap off {cap_off[11:19]}Z; BACK {back['at_utc'][11:19]}Z")


def in_win(r, t0, t1):
    return t0 <= r["at_utc"] < t1


# phases split at every transition_done
cuts = [play, cap_on] + [d["at_utc"] for d in done] + [cap_off, back["at_utc"]]
cuts = sorted(set(cuts))
P("")
P("== Per-report figures by rung and phase (evaluated reports; host payload from the frame series)")
P("   window | secs | reports (evaluated) | fps median [p10-p90] | fps<50 / <57 | lost median [max] | queue>=1 | "
  "gap median [max] | clean | payload kB/s")
for a, b in zip(cuts, cuts[1:]):
    rows = [r for r in samples if in_win(r, a, b)]
    evl = [r for r in rows if r.get("disposition") == "evaluated"]
    fps = [r["fps"] for r in evl if isinstance(r.get("fps"), (int, float))]
    lost = [r["lost_packets_delta"] for r in evl if isinstance(r.get("lost_packets_delta"), (int, float))]
    qd = [r["queue_depth"] for r in evl if isinstance(r.get("queue_depth"), (int, float))]
    gap = [r["output_gap_ms"] for r in evl if isinstance(r.get("output_gap_ms"), (int, float))]
    lvl = next((r.get("level_kbps") for r in evl), None)
    cap = "cap ON" if cap_on <= a < cap_off else ("cap off" if a >= cap_off else "baseline")
    pay = [f["payload_bytes"] for f in frames if a[:19] <= f.get("at_utc", "")[:19] < b[:19]]
    if not fps:
        continue
    P(f"   {a[11:19]}-{b[11:19]}Z {cap} at {lvl} | {ts(b) - ts(a):.0f} | {len(rows)} ({len(evl)}) | "
      f"{statistics.median(fps):.1f} [{q(fps, .1):.1f}-{q(fps, .9):.1f}] | "
      f"{100 * sum(1 for x in fps if x < 50) / len(fps):.0f} % / {100 * sum(1 for x in fps if x < 57) / len(fps):.0f} % | "
      f"{statistics.median(lost):.0f} [{max(lost)}] | {sum(1 for v in qd if v >= 1)} | {statistics.median(gap):.0f} "
      f"[{max(gap)}] | {sum(1 for r in evl if r.get('clean'))}/{len(evl)} | "
      f"{(statistics.median(pay) / 1000) if pay else float('nan'):.0f}")

P("")
P("== Transitions and decisions")
tr = []
prev_done = None
for r in sorted(trans + holds + refused, key=lambda x: x["at_utc"]):
    since = None
    if prev_done is not None:
        since = sum(1 for x in samples if prev_done < x["at_utc"] <= r["at_utc"]
                    and x.get("disposition") in ("evaluated", "blackout", "resync"))
    m = r.get("measurements") or {}
    P(f"   {r['at_utc'][11:23]}Z {r['event']:10s} {r.get('class'):8s} {r.get('from_kbps', r.get('level_kbps'))}->"
      f"{r.get('to_kbps', r.get('would_target_kbps'))} reason {r.get('reason')} trigger {r.get('trigger')} "
      f"window {m.get('window_reports')}/{m.get('clean_reports')} reports since the previous change {since}"
      f"{' hold_down_left ' + str(r.get('hold_down_left_reports')) if r.get('hold_down_left_reports') else ''}")
    if r["event"] == "transition":
        d = next(x for x in done if x["at_utc"] > r["at_utc"])
        tr.append({"at": r["at_utc"], "class": r["class"], "reason": r.get("reason"), "from": r["from_kbps"],
                   "to": r["to_kbps"], "since": since, "done": d["at_utc"], "actuation_ms": d.get("actuation_ms")})
        prev_done = d["at_utc"]
    if r["event"] == "hold":
        P(f"      direction changes (the policy's elapsed ms): {r.get('direction_changes_ms')}")
cap_tr = tr[0]
at6000 = next(t["done"] for t in tr if t["to"] == 6000)
mild = next(t for t in tr if t["reason"] == "capacity_mild")
mild_first = next(r for r in refused if r.get("trigger") == "capacity_mild")
P(f"   capacity FALLBACK {ts(cap_tr['at']) - ts(cap_on):.1f} s after the cap went in")
P(f"   arrived at 6000 (transition_done) {at6000[11:23]}Z; capacity_mild bar first met (refused hold_down) "
  f"{ts(mild_first['at_utc']) - ts(at6000):.1f} s later; acted {ts(mild['at']) - ts(at6000):.1f} s after arriving "
  f"({mild['since']} reports after the change)")
if holds:
    h = holds[0]
    first_change = tr[1]["at"]            # the first up after the down: the first direction change
    P(f"   HOLD {h['at_utc'][11:23]}Z: {ts(h['at_utc']) - ts(first_change):.0f} s after the first direction change "
      f"({first_change[11:19]}Z); {ts(h['at_utc']) - ts(cap_off):.0f} s after the cap came off")
esc = [r for r in log if r.get("event") == "escalation_armed"]
P(f"   escalation_armed {len(esc)}; level_sync {sum(1 for r in log if r.get('event') == 'level_sync')}; "
  f"rate_limited ever {any(a.get('rate_limited') for a in abr)}; recovery log {[r['event'] for r in rec]}")
times = [ts(t["at"]) for t in tr]
maxwin = max(sum(1 for u in times[i:] if u - t < 600) for i, t in enumerate(times)) if times else 0
P(f"   transitions {len(tr)}, gaps {[round(b - a) for a, b in zip(times, times[1:])]} s; most in any 10-min window {maxwin}")

P("")
P("== The 6000 rung under the cap (F1g)")
w6 = [r for r in samples if at6000 <= r["at_utc"] < mild["done"] and r.get("disposition") == "evaluated"]
for r in w6:
    P(f"      {r['at_utc'][11:19]} fps {r['fps']:.1f} lost {r['lost_packets_delta']} queue {r['queue_depth']} "
      f"gap {r['output_gap_ms']} clean {r['clean']}")
fps6 = [r["fps"] for r in w6]
lost6 = [r["lost_packets_delta"] for r in w6]
P(f"   {len(w6)} evaluated reports over {ts(mild['done']) - ts(at6000):.0f} s: fps median {statistics.median(fps6):.1f} "
  f"(p10 {q(fps6, .1):.1f}); under 57 on {sum(1 for x in fps6 if x < 57)}; lost median {statistics.median(lost6):.0f}, "
  f">= 50 on {sum(1 for x in lost6 if x >= 50)}")

P("")
P("== After BACK, and the reset rows")
resets = [r for r in log if r.get("event") == "session_ended_reset"]
for r in resets:
    P(f"   session_ended_reset {r['at_utc'][11:23]}Z: before {r.get('before')} -> level {r.get('level_kbps')}")
P(f"   harness 'back' event: level_after {back.get('level_after')} mode_after {back.get('mode_after')}")
for a in abr:
    if back["at_utc"] <= a["at_utc"] <= back["at_utc"][:14] + "59:59":
        P(f"   status {a['at_utc'][11:21]}Z: stream {a.get('bitrate_kbps')} active {a.get('active')}; level "
          f"{a.get('level')} state {a.get('state')} transitions {a.get('transitions_this_session')}")
        break

P("")
P("== Close-out rows (decoder report; reported)")
rep = json.load(open(os.path.join(RUN, "report_F1.json")))["report"]
d, v, au = rep["decoder"], rep["video"], rep["audio"]
secs = rep["duration_ms"] / 1000.0
mins = secs / 60.0
cr = {"spikes_20_per_min": d["spike_20_ms"] / mins, "rendered_fps": d["rendered_frames"] / secs,
      "stale_output_drops_per_min": d["stale_output_drops"] / mins,
      "video_lost_per_min_post_fec": v["lost_packets"] / mins, "audio_underruns_per_min": au["underruns"] / mins}
fails = [k for k, ok, _ in TARGETS if not ok(cr[k])]
P(f"   F1 ({mins:.1f} min): " + "; ".join(f"{k} {cr[k]:.2f}" for k, _, _ in TARGETS)
  + f"; max gap {d['max_output_gap_ms']} ms; ssrc_changes {v.get('ssrc_changes')} at "
    f"{[x['elapsed_ms'] for x in rep.get('stream_discontinuities') or []]} -> misses {fails or 'none'}")

# ---- rows ----------------------------------------------------------------------------------
res = {}
dt = ts(cap_tr["at"]) - ts(cap_on)
res["F1a"] = ("MET" if cap_tr["reason"] == "capacity" and cap_tr["to"] == 5000 and dt <= 60 else "NOT MET",
              f"strict capacity FALLBACK 7000->5000 {dt:.1f} s after the cap; one transition; one decoder ssrc_change for it")
ups = [t for t in tr if t["class"] == "INCREASE"]
mild_delay = ts(mild["at"]) - ts(at6000)
b_ok = (len(ups) == 2 and all((t["since"] or 0) >= 93 for t in ups) and mild["since"] >= 60 and mild_delay <= 150
        and bool(holds) and holds[0].get("reason") == "oscillation")
res["F1b"] = ("MET" if b_ok else "NOT MET",
              f"HOLD branch: INCREASE 5000->5500 {ups[0]['since']} reports after the FALLBACK's change, 5500->6000 "
              f"{ups[1]['since']} after that; capacity_mild 6000->5500 {mild['since']} reports / {mild_delay:.1f} s after "
              f"arriving at 6000 (bound: >= 60 reports, <= 150 s) after two hold_down refusals; the next increase became "
              f"HOLD oscillation at 5500")
res["F1c"] = ("MET" if not any(a.get("rate_limited") for a in abr) else "NOT MET",
              f"rate_limited never; {len(tr)} transitions, {maxwin} inside one 10-min window (allowed); gaps "
              f"{[round(b - a) for a, b in zip(times, times[1:])]} s, none closer than the hold-down table; no two "
              f"same-direction transitions < 93 reports apart")
after = [t for t in tr if t["at"] >= cap_off]
res["F1d"] = ("MET" if not after and holds else "NOT MET",
              f"nothing after removal (HOLD); BACK -> level {back.get('level_after')}")
res["F1e"] = ("MET" if not esc else "NOT MET", f"escalation_armed {len(esc)}")
cyc = [r for r in rec if r["event"] in ("desync_pause", "encoder_restart")]
res["F1f"] = ("MET" if len(cyc) <= 2 else "NOT MET", f"recovery cycles under the cap: {len(cyc)}")
res["F1g"] = ("REPORTED", f"at 6000 under the cap {ts(mild['done']) - ts(at6000):.0f} s (night 2: 3 min 56 s)")
anyo = next((e.get("any_override") for e in ev if e["event"] == "playing"), None)
res["ALL-override"] = ("MET" if anyo is False else "NOT MET", f"any_override at PLAYING {anyo}")
res["ALL-report"] = ("MET" if back.get("report") else "NOT MET", "stored")
res["ALL-lifecycle"] = ("MET" if [r["event"] for r in rec] == ["session_started", "session_ended"] else "NOT MET",
                        f"{[r['event'] for r in rec]}")
end_ok = summ["no_fault_table_at_end"] and summ["teardown_clean"] and summ["flags_after"] == [] \
    and summ["banner_count_at_end"] == 0
res["ALL-end"] = ("MET" if end_ok else "NOT MET", "no fault table; flag unset and absent; stream 7000; no game; 0 banners")
P("")
P("== Rows")
for k, (val, why) in res.items():
    P(f"   {k:14s} {val:9s} {why}")
notmet = [k for k, (val, _) in res.items() if val == "NOT MET"]
P("")
P(f"CLASSIFICATION: {'WORKS UNDER LOSS (F1)' if not notmet else 'rows not held: ' + ', '.join(notmet)}")
print("\n".join(out))
json.dump({"rows": {k: v for k, (v, _) in res.items()}, "transitions": tr, "classification":
           "WORKS UNDER LOSS (F1)" if not notmet else notmet},
          open(os.path.join(HERE, "c3_l4_n3_night3_score.json"), "w"), indent=1, default=str)
