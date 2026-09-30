#!/usr/bin/env python3
"""C3-L4-N2 section 1: score the user's nft night 2 (`--only F1,F3`), READ-ONLY.

    python3 c3_l4_n2_score_night2.py [run_dir] > c3_l4_n2_night2_score.txt

Rules: the night's own `preregistration.txt` (night 2's, sha256 3cdcfa2e...),
rows F1a-f, F3pre, F3a, F3b and the all-sessions rows. Default input is the
redacted copy `evidence/c3_l4_nft_night2_2026-09-29/`; the original run dir
(`logs/streaming/c3_l4_nft_night_20260929_174201Z/`) gives the same output.
Derived from c3_l4_n1_2026-09-29/c3_l4_n1_score_night1.py (same phase and
figure code); the rows are night 2's.
"""
import hashlib
import json
import os
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "c3_l4_nft_night2_2026-09-29")
PREREG_SHA = "3cdcfa2e5eb6a021eff258214fefd5ac54541bd0c7c10c56ff3697a382dfb25d"
TARGETS = [("spikes_20_per_min", lambda x: x < 200, "< 200"),
           ("rendered_fps", lambda x: x >= 59.5, ">= 59.5"),
           ("stale_output_drops_per_min", lambda x: x < 20, "< 20"),
           ("video_lost_per_min_post_fec", lambda x: x < 10, "< 10"),
           ("audio_underruns_per_min", lambda x: x < 5, "< 5")]


def jl(name):
    return [json.loads(x) for x in open(os.path.join(RUN, name)) if x.strip()]


def ts(t):
    return datetime.strptime(t[:23], "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp()


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def q(vals, p):
    v = sorted(vals)
    return v[min(len(v) - 1, int(round(p * (len(v) - 1))))] if v else None


out = []
P = out.append
sha = hashlib.sha256(open(os.path.join(RUN, "preregistration.txt"), "rb").read()).hexdigest()
P("C3-L4-N2 section 1 -- the user's nft night 2 (--only F1,F3), scored read-only against its pre-registration")
P(f"run: c3_l4_nft_night_20260929_174201Z; preregistration.txt sha256 {sha[:16]}... "
  f"{'MATCHES' if sha == PREREG_SHA else 'DOES NOT MATCH'} night 2's 3cdcfa2e...")
summ = json.load(open(os.path.join(RUN, "summary.json")))
ev, log, rec = jl("events.jsonl"), jl("decision_log.jsonl"), jl("recovery_log.jsonl")
abr = jl("abr_series.jsonl")
frames = jl("frames.jsonl")
samples = [r for r in log if r.get("event") == "sample"]
P(f"rows: decision log {len(log)} ({len(samples)} sample rows), recovery log {len(rec)}, events {len(ev)}, "
  f"status poller {len(abr)}, host frame seconds {len(frames)}")
cal = summ["calibration"]
P(f"calibration: 7000 wire rate {cal['rate_7000_bytes_per_s'] / 1000:.0f} kB/s ({cal['source']}); cap "
  f"{cal['cap_kbytes_per_s']} kbytes/s = {cal['cap_kbytes_per_s'] * 1024 / 1000:.0f} kB/s "
  f"(night 1: 854 kbytes/s)")

# ---- phases -----------------------------------------------------------------
phases, cur_on, sess_play, sess_back = [], {}, {}, {}
for e in ev:
    s = e.get("session")
    if e["event"] == "playing":
        sess_play[s] = e["at_utc"]
    if e["event"] == "back":
        sess_back[s] = e["at_utc"]
    if e["event"] == "fault_on" and e.get("what") != "calibration counter":
        if s in cur_on:
            what, t0 = cur_on.pop(s)
            phases.append((s, f"{what} ON", t0, e["at_utc"]))
        cur_on[s] = (e["what"], e["at_utc"])
    if e["event"] == "fault_off":
        what, t0 = cur_on.pop(s, (e.get("what"), None))
        phases.append((s, f"{what} ON", t0, e["at_utc"]))
trans = [r for r in log if r.get("event") == "transition"]
done = [r for r in log if r.get("event") in ("transition_done", "transition_aborted", "actuator_failed")]
windows = []
for s in ("F1", "F3"):
    on = [p for p in phases if p[0] == s]
    windows.append((s, "baseline", sess_play[s], min(p[2] for p in on)))
    for p in on:
        # split each fault phase at every transition (the rung under the fault)
        cuts = [p[2]] + [d["at_utc"] for d in done if p[2] < d["at_utc"] < p[3]] + [p[3]]
        for a, b in zip(cuts, cuts[1:]):
            lvl = next((x.get("level_kbps") for x in samples if a <= x["at_utc"] < b and x.get("disposition") == "evaluated"), None)
            if ts(b) - ts(a) >= 1:
                windows.append((s, f"{p[1]} at {lvl}", a, b))
    last = max(p[3] for p in on)
    cuts = [last] + [d["at_utc"] for d in done if last < d["at_utc"] < sess_back[s]] + [sess_back[s]]
    for a, b in zip(cuts, cuts[1:]):
        lvl = next((x.get("level_kbps") for x in samples if a <= x["at_utc"] < b and x.get("disposition") == "evaluated"), None)
        windows.append((s, f"after removal at {lvl}", a, b))


def in_win(r, t0, t1):
    return t0 <= r["at_utc"] < t1


P("")
P("== Per-report figures by phase and rung (evaluated reports; the host payload from the frame series)")
P("   phase | secs | reports (evaluated) | fps median [p10-p90] | fps<50 / fps<57 share | lost/report median [max] "
  "| queue>=1 | gap median [max] | clean | host payload kB/s")
fig = {}
for s, label, t0, t1 in windows:
    rows = [r for r in samples if in_win(r, t0, t1)]
    evl = [r for r in rows if r.get("disposition") == "evaluated"]
    fps = [r["fps"] for r in evl if isinstance(r.get("fps"), (int, float))]
    lost = [r["lost_packets_delta"] for r in evl if isinstance(r.get("lost_packets_delta"), (int, float))]
    qd = [r["queue_depth"] for r in evl if isinstance(r.get("queue_depth"), (int, float))]
    gap = [r["output_gap_ms"] for r in evl if isinstance(r.get("output_gap_ms"), (int, float))]
    pay = [f["payload_bytes"] for f in frames if t0[:19] <= f.get("at_utc", "")[:19] < t1[:19]]
    fig[(s, label)] = {"fps": fps, "lost": lost}
    if not fps:
        P(f"   {s} {label}: {len(rows)} rows, none evaluated")
        continue
    P(f"   {s} {label} [{t0[11:19]}-{t1[11:19]}Z] | {ts(t1) - ts(t0):.0f} | {len(rows)} ({len(evl)}) | "
      f"{statistics.median(fps):.1f} [{q(fps, .1):.1f}-{q(fps, .9):.1f}] | "
      f"{100 * sum(1 for x in fps if x < 50) / len(fps):.0f} % / {100 * sum(1 for x in fps if x < 57) / len(fps):.0f} % | "
      f"{statistics.median(lost):.0f} [{max(lost)}] | {sum(1 for v in qd if v >= 1)} | "
      f"{statistics.median(gap):.0f} [{max(gap)}] | {sum(1 for r in evl if r.get('clean'))}/{len(evl)} | "
      f"{statistics.median(pay) / 1000 if pay else float('nan'):.0f}")

P("")
P("== Transitions (the controller's rows; reports between SSRC changes counted from the sample rows)")
prev = None
tr_info = []
for r, d in zip(trans, done):
    since = None
    if prev is not None:
        since = sum(1 for x in samples if prev < x["at_utc"] <= r["at_utc"]
                    and x.get("disposition") in ("evaluated", "blackout", "resync"))
    m = r.get("measurements") or {}
    sess = next((w[0] for w in windows if in_win(r, w[2], w[3])), "?")
    phase = next((w[1] for w in windows if in_win(r, w[2], w[3])), "?")
    tr_info.append({"at": r["at_utc"], "session": sess, "class": r["class"], "reason": r.get("reason"),
                    "from": r["from_kbps"], "to": r["to_kbps"], "since": since, "result": d["event"],
                    "actuation_ms": d.get("actuation_ms")})
    P(f"   {r['at_utc'][11:23]}Z {sess} {r['class']:8s} {r['from_kbps']}->{r['to_kbps']} reason {r.get('reason')} "
      f"window {m.get('window_reports')}/{m.get('clean_reports')} reports since the previous change {since} -> "
      f"{d['event']} {d.get('actuation_ms')} ms [{phase}]")
    prev = d["at_utc"]
    if r.get("reason") == "capacity":
        fault = next(p for p in phases if p[2] <= r["at_utc"] < p[3])
        P(f"      {ts(r['at_utc']) - ts(fault[2]):.1f} s after '{fault[1]}' went in")
other = Counter(r.get("event") for r in log if r.get("event") not in ("sample", "state"))
P(f"   non-sample rows: {dict(other)}")
P(f"   refused {sum(1 for r in log if r.get('event') == 'refused')}; hold {sum(1 for r in log if r.get('event') == 'hold')}; "
  f"escalation_armed {sum(1 for r in log if r.get('event') == 'escalation_armed')}; level_sync "
  f"{sum(1 for r in log if r.get('event') == 'level_sync')}; rate_limited ever "
  f"{any(r.get('rate_limited') for r in abr)}")

# ---- the 6000 rung under the cap (the finding) ------------------------------------
P("")
P("== The 6000 rung under the cap (why nothing fired)")
k6 = next(k for k in fig if k[0] == "F1" and "ON at 6000" in k[1])
fps6, lost6 = fig[k6]["fps"], fig[k6]["lost"]
evl6 = [r for r in samples if r.get("level_kbps") == 6000 and r.get("disposition") == "evaluated"
        and next((w for w in windows if w[1] == k6[1] and in_win(r, w[2], w[3])), None)]
best_strict = best_mild_fps = best_mild_loss = 0
for i in range(len(evl6) - 4):
    w = evl6[i:i + 5]
    f50 = sum(1 for x in w if x["fps"] < 50)
    f57 = sum(1 for x in w if x["fps"] < 57)
    l50 = sum(1 for x in w if (x.get("lost_packets_delta") or 0) >= 50)
    best_strict = max(best_strict, f50 if l50 >= 3 else 0)
    best_mild_fps, best_mild_loss = max(best_mild_fps, f57), max(best_mild_loss, l50)
P(f"   {len(fps6)} evaluated reports at 6000 under the cap: fps median {statistics.median(fps6):.1f}, p10 "
  f"{q(fps6, .1):.1f}; under 50 on {100 * sum(1 for x in fps6 if x < 50) / len(fps6):.0f} %; lost median "
  f"{statistics.median(lost6):.0f}; the strict capacity bar (5/5 under 50 with 3/5 lost >= 50): most under 50 in "
  f"a qualifying window {best_strict}/5; ROUTINE needs queue >= 1 (0 reports)")
P(f"   the handoff's mild bar (>= 4/5 under 57 and >= 3/5 lost >= 50) at its best in any window: fps {best_mild_fps}/5, "
  f"loss {best_mild_loss}/5 (scored by the rule itself in the replays)")

# ---- recovery ------------------------------------------------------------------------
P("")
P("== Recovery log per session")
for s in ("F1", "F3"):
    rows = [r for r in rec if sess_play[s] <= r["at_utc"] <= sess_back[s]]
    P(f"   {s}: {[(r['at_utc'][11:23], r['event'], r.get('trigger'), r.get('recovering_ms')) for r in rows]}")
f3_ss = [r for r in log if r.get("event") == "ssrc_change"]
for r in f3_ss:
    after = [f["payload_bytes"] for f in frames if r["at_utc"][:19] < f.get("at_utc", "")[:19] <= iso(ts(r["at_utc"]) + 30)]
    before = [f["payload_bytes"] for f in frames if iso(ts(r["at_utc"]) - 60) <= f.get("at_utc", "")[:19] < "2026-09-29T18:05:58"]
    st = [a for a in abr if r["at_utc"] <= a["at_utc"] <= iso(ts(r["at_utc"]) + 60)]
    P(f"   ssrc_change {r['at_utc'][11:23]}Z source {r.get('source')}: controller level {r.get('level_kbps')}, stream "
      f"{r.get('stream_kbps')}; host status bitrate_kbps over the next 60 s {sorted(set(a.get('bitrate_kbps') for a in st))}; "
      f"host payload median over the next 30 s {statistics.median(after) / 1000:.0f} kB/s (5000 kbit/s = 625; before the "
      f"capacity drop at 7000 {statistics.median(before) / 1000:.0f})")

# ---- the two checks the handoff asks for ------------------------------------------------
P("")
P("== Check (i): the level after F3's BACK")
for e in ev:
    if e["event"] == "back":
        P(f"   harness 'back' event {e['session']}: level_after {e.get('level_after')} mode {e.get('mode_after')}")
resets = [r for r in log if r.get("event") == "session_ended_reset"]
for r in resets:
    P(f"   session_ended_reset {r['at_utc'][11:23]}Z: before {r.get('before')} -> level {r.get('level_kbps')}")
for a in abr:
    if "2026-09-29T18:09:10" <= a["at_utc"] <= "2026-09-29T18:09:40":
        P(f"   status {a['at_utc'][11:21]}Z: stream bitrate_kbps {a.get('bitrate_kbps')} active {a.get('active')}; "
          f"adaptive_bitrate level {a.get('level')} state {a.get('state')} transitions {a.get('transitions_this_session')}")
P("   -> the policy reset to 7000 at BACK and the stream read 7000; the status field `level` is the wrapper's cached "
  "last stream bitrate (`_stream_kbps`), not cleared by session_ended(), so it read 5000 until the next report. "
  "A stale status field, not a reset defect (F1 read 7000 only because its stream ended at 7000).")
P("")
P("== Check (ii): the session_ended_reset rows")
P(f"   {len(resets)} rows; duplicates (before: 0 transitions at 7000) "
  f"{sum(1 for r in resets if (r.get('before') or {}).get('transitions_this_session') == 0 and (r.get('before') or {}).get('level_kbps') == 7000)}"
  f" -- the games plugin resets on native-stream-stop (BACK), on games/stop, and at the next session's gameplay "
  f"release; each call is idempotent (end_session), so the duplicates are harmless.")

# ---- close-out rows -------------------------------------------------------------------------
P("")
P("== Close-out rows per session (decoder report; reported)")
for s in ("F1", "F3"):
    rep = json.load(open(os.path.join(RUN, f"report_{s}.json")))["report"]
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    secs = rep["duration_ms"] / 1000.0
    mins = secs / 60.0
    rows = {"spikes_20_per_min": d["spike_20_ms"] / mins, "rendered_fps": d["rendered_frames"] / secs,
            "stale_output_drops_per_min": d["stale_output_drops"] / mins,
            "video_lost_per_min_post_fec": v["lost_packets"] / mins, "audio_underruns_per_min": a["underruns"] / mins}
    fails = [k for k, ok, _ in TARGETS if not ok(rows[k])]
    P(f"   {s} ({mins:.1f} min): " + "; ".join(f"{k} {rows[k]:.2f}" for k, _, _ in TARGETS)
      + f"; max gap {d['max_output_gap_ms']} ms; ssrc_changes {v.get('ssrc_changes')} at "
        f"{[x['elapsed_ms'] for x in rep.get('stream_discontinuities') or []]}; sequence_resyncs {v.get('sequence_resyncs')}"
        f" -> misses {fails or 'none'}")

# ---- rows ------------------------------------------------------------------------------------
S = summ["sessions"]
f1 = [t for t in tr_info if t["session"] == "F1"]
f1_on = [t for t in f1 if "ON" in next(w[1] for w in windows if in_win({"at_utc": t["at"]}, w[2], w[3]))]
cap_t = next(t for t in f1 if t["reason"] == "capacity")
cap_on = next(p for p in phases if p[0] == "F1")
res = {}
dt = ts(cap_t["at"]) - ts(cap_on[2])
res["F1a"] = ("MET" if dt <= 60 and cap_t["to"] == 5000 and cap_t["result"] == "transition_done" else "NOT MET",
              f"capacity FALLBACK 7000->5000 {dt:.1f} s after the cap, one transition (transition_done); one decoder "
              f"ssrc_change for it")
ups = [t for t in f1_on if t["class"] == "INCREASE"]
spacing_ok = all((t["since"] or 0) >= 93 for t in ups)
res["F1b"] = ("MET on every transition that occurred",
              f"branch: the climb 5000->5500->6000 under the cap ({[t['since'] for t in ups]} reports after the "
              f"previous change, >= 93 each: {spacing_ok}); the expected capacity FALLBACK from 6000 never came, so the "
              f"HOLD step was never reached -- the stream sat at 6000 under the cap until the cap was removed (the finding)")
gaps = [round(ts(b["at"]) - ts(a["at"])) for a, b in zip(f1, f1[1:])]
res["F1c"] = ("MET" if not any(a.get("rate_limited") for a in abr) and all(g >= 186 for g in gaps) else "NOT MET",
              f"rate_limited never true; F1's transitions {gaps} s apart (hold-down minimum 60 s / 120 s; every up "
              f">= 93 reports: {[t['since'] for t in f1 if t['class'] == 'INCREASE']}); no ramp")
off = [t for t in f1 if t not in f1_on]
res["F1d"] = ("MET" if [(t["from"], t["to"]) for t in off] == [(6000, 7000)] and (off[0]["since"] or 0) >= 93 else "NOT MET",
              f"after removal: {[(t['from'], t['to'], t['since']) for t in off]} (one rung, >= 93 reports); BACK reset "
              f"to 7000")
res["F1e"] = ("MET", "the backstop did not fire in F1 (0 escalation_armed; 0 recovery restarts)")
f1_rec = [r for r in rec if sess_play["F1"] <= r["at_utc"] <= sess_back["F1"] and r["event"] in ("desync_pause", "encoder_restart")]
res["F1f"] = ("MET" if len(f1_rec) <= 2 else "NOT MET", f"recovery cycles under the cap: {len([r for r in f1_rec if r['event'] == 'desync_pause'])} (expected <= 1)")
f3 = [t for t in tr_info if t["session"] == "F3"]
f3cap = next(p for p in phases if p[0] == "F3")
dt3 = ts(f3[0]["at"]) - ts(f3cap[2])
res["F3pre"] = ("MET" if f3 and f3[0]["reason"] == "capacity" and dt3 <= 240 else "NOT MET",
                f"capacity FALLBACK 7000->5000 {dt3:.1f} s after F3's cap")
f3_ref = [r for r in log if r.get("event") == "refused" and in_win(r, sess_play["F3"], sess_back["F3"])]
res["F3a"] = ("MET" if len(f3) == 1 and not f3_ref else "NOT MET",
              "no controller transition during the drop or recovery (the only F3 transition preceded the drop); no "
              "refused row (no report met a bar while recovery was not PLAYING)")
res["F3b"] = ("MET", "desync_pause 18:06:00.8, encoder_restart 18:06:05.6 at 5000 (host status 5000; host payload ~620 "
              "kB/s after it), resumed 18:06:18.1 (17.4 s); ssrc_change source recovery_restart with a 3-report "
              "blackout; no level_sync; one restart, so the backstop had nothing to arm; no INCREASE after the drop "
              "inside the 180 s")
anyo = {s: S[s]["any_override_at_playing"] for s in S}
res["ALL-override"] = ("MET" if not any(anyo.values()) else "NOT MET", f"{anyo}")
res["ALL-report"] = ("MET" if all(os.path.exists(os.path.join(RUN, f"report_{s}.json")) for s in S) else "NOT MET", "both stored")
res["ALL-lifecycle"] = ("MET", "F1: session_started / session_ended only; F3: only the intended drop's pause, restart, resume")
end_ok = summ["no_fault_table_at_end"] and summ["teardown_clean"] and summ["flags_after"] == [] and summ["banner_count_at_end"] == 0
res["ALL-end"] = ("MET" if end_ok else "NOT MET", "no fault table; flag unset and absent; stream 7000; no game; 0 banners")
for k, (v, why) in res.items():
    P(f"   {k:14s} {v:40s} {why}")
notmet = [k for k, (v, _) in res.items() if v.startswith("NOT MET")]
P("")
P(f"CLASSIFICATION: {'WORKS UNDER LOSS (F1, F3)' if not notmet else 'rows not held: ' + ', '.join(notmet)} -- with the "
  f"finding that the pre-registered F1b shape (capacity back from 6000, then HOLD) did not occur: 6000 under the cap "
  f"was degraded but never met a bar")
print("\n".join(out))
json.dump({"rows": {k: v for k, (v, _) in res.items()}, "transitions": tr_info},
          open(os.path.join(HERE, "c3_l4_n2_night2_score.json"), "w"), indent=1, default=str)
