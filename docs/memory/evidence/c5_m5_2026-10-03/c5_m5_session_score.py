#!/usr/bin/env python3
"""C5-M5 S2 / S3 -- score a rung session by its pre-registered rows (c5_m5_preregistration.txt section 4).
Read-only.   c5_m5_session_score.py <runs dir> <arm> <S2|S3>  -> prints; writes <arm>_session_score.{txt,json}

Inputs: the decision log sliced to the session (decision_log_<arm>.jsonl), the C2 telemetry
(<arm>_telemetry.jsonl), the decoder report, the index line (T0 / T1), the companion's recovery log.

- transitions: every `transition` row, its reason, injected flag, the hold-downs in force before it
  (holds_in_force_before) and the reports since the previous one; "one the rules name" = a reason in
  RULE_REASONS and not injected; "at the spacing the hold-downs allow" = every hold in force before it
  was 0 for its class (the policy enforces it; checked here from the row) and the rung re-entry hold
  (10 min) respected between a leave and the next entry.
- the level over time: from transition_done rows (the stream changed then), T0 .. T1.
- per level: from the C2 telemetry reports in that level's intervals (UTC): rendered fps
  (sum rendered_frames_delta / span), stale/min, loss/min (sum lost_packets_delta), the largest
  per-report output_gap_ms; spikes and audio underruns per minute are the SESSION's (the report's;
  the per-report telemetry carries neither).
- recovery cycles: recovery-log events other than session_started / session_ended in T0 .. T1.
- the longest rung window: from the sample rows (clean flags of evaluated / resync rows since the
  last SSRC change), the best count of clean in the last 450, at 7000.
"""
import json, os, sys
from collections import deque
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
R, A, KIND = os.path.join(HERE, sys.argv[1]), sys.argv[2], sys.argv[3]
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
RULE_REASONS = {"increase_1080p", "capacity_mild", "capacity", "decrease_fallback", "decrease_routine",
                "recovery_escalation", "increase_increase"}
WINDOW, NEEDED, REENTRY_S = 450, 435, 600


def ts(s):
    s = s.rstrip("Z")
    fmt = "%Y-%m-%dT%H:%M:%S.%f" if "." in s else "%Y-%m-%dT%H:%M:%S"
    return datetime.strptime(s[:26], fmt).replace(tzinfo=timezone.utc).timestamp()


def jl(p):
    out = []
    if os.path.exists(p):
        for l in open(p, errors="replace"):
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


idx = [l.split() for l in open(os.path.join(R, "index.txt")) if l.startswith(A + " H ")]
if not idx:
    print(f"{A}: no index line (NOT RUN)")
    sys.exit(1)
T0, T1 = ts(idx[-1][4]), ts(idx[-1][5])
dl = jl(os.path.join(R, f"decision_log_{A}.jsonl"))
tel = [r for r in jl(os.path.join(R, f"{A}_telemetry.jsonl")) if r.get("fresh") and r.get("at_utc")]
rep = json.load(open(os.path.join(R, f"report_{A}.json")))["report"]
dur_min = rep["duration_ms"] / 60000.0
trs = [d for d in dl if d.get("event") == "transition"]
done = [d for d in dl if d.get("event") in ("transition_done", "transition_aborted", "actuator_failed")]
holds = [d for d in dl if d.get("event") == "hold"]
rec = [(r["at_utc"], r.get("event")) for r in jl(os.path.join(REPO, "logs/games/native_stream_recovery.log"))
       if r.get("at_utc") and T0 - 5 <= ts(r["at_utc"]) <= T1 + 5 and r.get("event") not in ("session_started", "session_ended")]

# the level over time
segs, level, t = [], 7000, T0
for d in done:
    if d.get("event") != "transition_done":
        continue
    td = ts(d["at_utc"])
    if td < T0 or td > T1:
        continue
    segs.append((t, td, level))
    level, t = d.get("to_kbps"), td
segs.append((t, T1, level))
by_level = {}
for a, b, lv in segs:
    by_level.setdefault(lv, []).append((a, b))

# transitions: rules and spacing
rows_t, last_leave = [], None
for d in trs:
    hb = d.get("holds_in_force_before") or {}
    cls = d.get("class")
    key = {"FALLBACK": "fallback_reports", "ROUTINE": "routine_reports", "INCREASE": "increase_reports"}.get(cls)
    spacing_ok = (hb.get("blackout_reports", 0) == 0) and (hb.get(key, 0) == 0 if key else True)
    t_tr = ts(d["at_utc"])
    if d.get("to_kbps") == 12600 and last_leave is not None:
        spacing_ok = spacing_ok and (t_tr - last_leave >= REENTRY_S)
    if d.get("from_kbps") == 12600:
        last_leave = t_tr
    rows_t.append({"at_utc": d["at_utc"], "min_into": round((t_tr - T0) / 60, 1), "class": cls,
                   "from": d.get("from_kbps"), "to": d.get("to_kbps"), "reason": d.get("reason"),
                   "trigger": d.get("trigger"), "injected": d.get("injected"),
                   "named": d.get("reason") in RULE_REASONS and not d.get("injected"),
                   "spacing_ok": spacing_ok, "reports_since_prev": hb.get("reports_since_transition"),
                   "rung_leave": d.get("rung_leave")})


def tel_rows(intervals):
    return [r for r in tel if any(a <= ts(r["at_utc"]) <= b for a, b in intervals)]


def per_level(lv):
    iv = by_level.get(lv, [])
    secs = sum(b - a for a, b in iv)
    rs = tel_rows(iv)
    rf = sum((r.get("decoder") or {}).get("rendered_frames_delta") or 0 for r in rs)
    st = sum((r.get("decoder") or {}).get("stale_output_drops_delta") or 0 for r in rs)
    lost = sum((r.get("receiver") or {}).get("lost_packets_delta") or 0 for r in rs)
    span = 2.0 * len(rs)
    gaps = [(r.get("latency") or {}).get("output_gap_ms") for r in rs if (r.get("latency") or {}).get("output_gap_ms") is not None]
    return {"seconds": round(secs, 1), "reports": len(rs),
            "rendered_fps": round(rf / span, 2) if span else None,
            "stale_per_min": round(st / (span / 60), 2) if span else None,
            "loss_per_min": round(lost / (span / 60), 2) if span else None,
            "telemetry_gap_max_ms": max(gaps) if gaps else None}


levels = {lv: per_level(lv) for lv in sorted(by_level)}
d, v, au = rep["decoder"], rep["video"], rep["audio"]
session = {"minutes": round(dur_min, 2), "spikes_per_min": round(d["spike_20_ms"] / dur_min, 1),
           "rendered_fps": round(d["rendered_frames"] / (rep["duration_ms"] / 1000), 2),
           "stale_per_min": round(d["stale_output_drops"] / dur_min, 2),
           "loss_per_min": round(v["lost_packets"] / dur_min, 2),
           "underruns_per_min": round((au.get("underruns") or 0) / dur_min, 2),
           "max_gap_ms": d["max_output_gap_ms"], "ssrc_changes": v.get("ssrc_changes"),
           "sequence_resyncs_beyond_ssrc": (v.get("sequence_resyncs") or 0) - (v.get("ssrc_changes") or 0)}

# the longest rung window at 7000 (sample rows)
win, best, best_at = deque(maxlen=WINDOW), 0, None
lvl = 7000
for r in dl:
    ev = r.get("event")
    if ev in ("transition_done", "ssrc_change") or (ev == "transition" and r.get("acted")):
        win.clear()
        if ev == "transition_done":
            lvl = r.get("to_kbps")
        continue
    if ev == "sample" and r.get("disposition") in ("evaluated", "resync") and lvl == 7000:
        win.append(bool(r.get("clean")))
        if sum(win) > best:
            best, best_at = sum(win), r.get("at_utc")

entries = [x for x in rows_t if x["to"] == 12600]
leaves = [x for x in rows_t if x["from"] == 12600]
rung = levels.get(12600)
client_ok = None
if rung and rung["reports"]:
    client_ok = (session["spikes_per_min"] < 200 and rung["rendered_fps"] >= 59.5 and rung["stale_per_min"] < 20
                 and session["underruns_per_min"] < 5)
osc = [h for h in holds if h.get("reason") in ("oscillation", "oscillation_rung")]
lines = [f"C5-M5 {KIND} ({A}) -- {datetime.fromtimestamp(T0, timezone.utc):%Y-%m-%d %H:%M:%S}Z .. "
         f"{datetime.fromtimestamp(T1, timezone.utc):%H:%M:%S}Z ({(T1 - T0) / 60:.1f} min)", "",
         "transitions (min into the hold, class, from -> to, reason, named by a rule, spacing):"]
for x in rows_t:
    lines.append(f"  {x['min_into']:6.1f} {x['class']:8s} {x['from']} -> {x['to']}  {x['reason']:16s} "
                 f"{'NAMED' if x['named'] else 'NOT NAMED'} {'spacing ok' if x['spacing_ok'] else 'SPACING VIOLATED'}"
                 f" (reports since previous {x['reports_since_prev']}){' leave ' + str(x['rung_leave']) if x['rung_leave'] else ''}")
if not rows_t:
    lines.append("  (none)")
lines.append(f"oscillation holds: {[(h.get('at_utc'), h.get('reason')) for h in osc] or 'none'}")
lines.append(f"recovery-log events in the hold: {rec or 'none'}")
lines.append(f"longest rung window at 7000: {best} clean of the last {WINDOW} (needed {NEEDED}) at {best_at}")
lines.append("\nper level (C2 telemetry in the level's intervals; spikes and underruns are the session's):")
for lv, x in levels.items():
    lines.append(f"  {lv}: {x['seconds'] / 60:.1f} min, {x['reports']} reports, fps {x['rendered_fps']}, stale/min "
                 f"{x['stale_per_min']}, loss/min {x['loss_per_min']}, telemetry gap max {x['telemetry_gap_max_ms']} ms")
lines.append(f"session (decoder report): {json.dumps(session)}")
all_named = all(x["named"] for x in rows_t)
all_spaced = all(x["spacing_ok"] for x in rows_t)
no_rec = not rec
if KIND == "S2":
    if not entries:
        verdict = f"ENTRY NOT REACHED (the rung window's best was {best} of {WINDOW}, needed {NEEDED})"
    else:
        ok = all_named and all_spaced and no_rec and (session["spikes_per_min"] < 200 and session["rendered_fps"] >= 59.5
                                                      and session["stale_per_min"] < 20 and session["underruns_per_min"] < 5)
        verdict = "RUNG SHOWN" if ok else "RUNG NOT SHOWN"
    lines.append(f"\nrows: entry by its own rule {'yes' if entries and not entries[0]['injected'] else 'no'}; every transition "
                 f"named {all_named}; spacing {all_spaced}; 0 recovery cycles {no_rec}; client rows over the hold "
                 f"(spikes < 200, fps >= 59.5, stale < 20, underruns < 5) "
                 f"{session['spikes_per_min'] < 200 and session['rendered_fps'] >= 59.5 and session['stale_per_min'] < 20 and session['underruns_per_min'] < 5}")
else:
    if not entries:
        verdict = f"ENTRY NOT REACHED (the rung window's best was {best} of {WINDOW}, needed {NEEDED})"
    else:
        osc_ok = (not osc) or all(h.get("reason") == "oscillation_rung" for h in osc)
        ok = all_named and all_spaced and osc_ok and no_rec and bool(client_ok)
        verdict = "WORKS AS A RUNG" if ok else "DOES NOT WORK AS A RUNG (see rows)"
    lines.append(f"\nrows: every transition named {all_named}; spacing {all_spaced}; oscillation hold "
                 f"{'none' if not osc else [h.get('reason') for h in osc]}; 0 recovery cycles {no_rec} "
                 f"({len(rec)} events); client rows over the 1080p minutes {client_ok}")
lines.append(f"\n{KIND}: {verdict}")
text = "\n".join(lines) + "\n"
print(text)
open(os.path.join(HERE, f"{A.lower()}_session_score.txt"), "w").write(text)
json.dump({"verdict": verdict, "transitions": rows_t, "levels": levels, "session": session, "recovery": rec,
           "oscillation_holds": [(h.get("at_utc"), h.get("reason")) for h in osc], "best_rung_window": best,
           "entries": len(entries), "leaves": len(leaves)},
          open(os.path.join(HERE, f"{A.lower()}_session_score.json"), "w"), indent=1, default=str)
