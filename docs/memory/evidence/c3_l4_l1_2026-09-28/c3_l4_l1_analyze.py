#!/usr/bin/env python3
"""C3-L4-L1: score Session A (silent live hold) and Session B (injected
trigger). Read-only. Rules: c3_l4_l1_preregistration.txt (written before
either session ran).

Inputs (runs/): index.txt; report_<arm>.json (the decoder report);
decision_log_<arm>.jsonl (the controller log's slice for the session);
abr_series_<arm>.jsonl (native-stream-status every 5 s); armcheck_<arm>.json
(status at PLAYING); status_end_<arm>.json (before BACK); inject1_B.json,
inject2_B.json; companion_<arm>.log (redacted journal); ../t2_samples.jsonl;
the recovery log's lines inside each session (read from logs/games).

Output gap per SSRC change: the largest output_gap_ms among the report's
retained slow events (>= 50 ms and top-gap tables) in [ssrc, ssrc + 1 s], as
C3.L3a-S1 scored it; reported against the S1 median 186.5 ms, not ruled.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
S1_MEDIAN_MS = 186.5
TARGETS = [("spikes_20_per_min", lambda x: x < 200, "< 200"),
           ("rendered_fps", lambda x: x >= 59.5, ">= 59.5"),
           ("stale_output_drops_per_min", lambda x: x < 20, "< 20"),
           ("video_lost_per_min_post_fec", lambda x: x < 10, "< 10"),
           ("audio_underruns_per_min", lambda x: x < 5, "< 5")]


def jl(path):
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path, errors="replace"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def jf(path):
    if not os.path.exists(path):
        return None
    txt = open(path).read()
    if "\nHTTP " in txt:
        body, code = txt.rsplit("\nHTTP ", 1)
        try:
            return {"http": int(code.strip()), "body": json.loads(body)}
        except Exception:
            return {"http": code.strip(), "body": body}
    return json.loads(txt)


idx = {}
for line in open(os.path.join(R, "index.txt")) if os.path.exists(os.path.join(R, "index.txt")) else []:
    f = line.split()
    if f and f[0] in ("A", "B") and len(f) >= 6:
        idx[f[0]] = f
heat = jl(os.path.join(HERE, "t2_samples.jsonl"))
recovery = jl(os.path.join(REPO, "logs", "games", "native_stream_recovery.log"))
summary = {}


def closeout(arm):
    rp = os.path.join(R, f"report_{arm}.json")
    if not os.path.exists(rp):
        print("   no decoder report: close-out rows not scorable")
        return None, None
    rep = json.load(open(rp))["report"]
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    secs = rep["duration_ms"] / 1000.0
    mins = secs / 60.0
    rows = {"spikes_20_per_min": d["spike_20_ms"] / mins, "rendered_fps": d["rendered_frames"] / secs,
            "stale_output_drops_per_min": d["stale_output_drops"] / mins,
            "video_lost_per_min_post_fec": v["lost_packets"] / mins,
            "audio_underruns_per_min": a["underruns"] / mins}
    fails = [k for k, ok, _ in TARGETS if not ok(rows[k])]
    for k, ok, txt in TARGETS:
        print(f"   {k:<30} {rows[k]:9.2f}  target {txt:<8} {'PASS' if ok(rows[k]) else 'FAIL'}")
    print(f"   {'max_output_gap_ms':<30} {d['max_output_gap_ms']:9}  (reported; bound <= 250)")
    print(f"   duration {mins:.2f} min; ssrc_changes {v['ssrc_changes']}; audio underruns {a['underruns']}")
    return rep, fails


def thermal(t0, t1):
    onn = [(x.get("onn") or {}).get("cpu_thermal_c") for x in heat if t0 <= x["at_utc"][:19] + "Z" <= t1]
    onn = [x for x in onn if x]
    if onn:
        print(f"   onn cpu-thermal {min(onn):.1f}-{max(onn):.1f} C over {len(onn)} samples")


def rec_lines(t0, t1):
    rows = [r for r in recovery if t0 <= r.get("at_utc", "")[:19] + "Z" <= t1]
    ev = [r["event"] for r in rows]
    return rows, ev


def gap_after(rep, ssrc_ms):
    cols = rep.get("slow_event_columns") or []
    gi, ei = cols.index("output_gap_ms"), cols.index("elapsed_ms")
    rows = (rep.get("slow_events_ge_50_ms") or []) + (rep.get("slow_events_top_gap") or [])
    inside = [r[gi] for r in rows if ssrc_ms <= r[ei] <= ssrc_ms + 1000]
    return max(inside) if inside else None, len(rep.get("slow_events_ge_50_ms") or [])


def armcheck(arm):
    ac = os.path.join(R, f"armcheck_{arm}.json")
    if os.path.exists(ac):
        d = json.load(open(ac))
        o = d.get("encoder_overrides") or {}
        print(f"   at PLAYING: any_override {o.get('any_override')}; adaptive_bitrate mode "
              f"{(d.get('adaptive_bitrate') or {}).get('mode')}; bitrate {d.get('bitrate_kbps')}; "
              f"profile {d.get('profile_id')}")
        return o.get("any_override")
    return None


print("C3-L4-L1 live sessions -- read-only scoring (rules: c3_l4_l1_preregistration.txt)")
print(f"t2 rows {len(heat)}")

# ------------------------------------------------------------------ A ---
print("\n== Session A -- silent live hold")
if "A" not in idx:
    print("   NOT RUN / no index line")
    summary["A"] = {"classification": "NOT RUN"}
else:
    f = idx["A"]
    t0, t1 = f[4], f[5]
    print(f"   {t0} .. {t1} (hold {f[2]} s), report {f[3]}")
    anyo = armcheck("A")
    rep, fails = closeout("A")
    thermal(t0, t1)
    log = jl(os.path.join(R, "decision_log_A.jsonl"))
    tr = [r for r in log if r.get("event") == "transition"]
    ref = [r for r in log if r.get("event") == "refused"]
    other = {}
    for r in log:
        other[r.get("event")] = other.get(r.get("event"), 0) + 1
    print(f"   decision log lines {len(log)}: {other}")
    print(f"   transitions {len(tr)}; refusals {len(ref)} {[(r['class'], r['reason']) for r in ref]}")
    se = os.path.join(R, "status_end_A.json")
    st = (json.load(open(se)).get("adaptive_bitrate") or {}) if os.path.exists(se) else {}
    p = st.get("policy") or {}
    print(f"   status before BACK: mode {st.get('mode')}, state {st.get('state')}, level {st.get('level')}, "
          f"transitions_this_session {st.get('transitions_this_session')}, rate_limited {st.get('rate_limited')}, "
          f"reports_evaluated {p.get('reports_evaluated')}, would_act {p.get('would_act')}, "
          f"suppressed {p.get('suppressed')}, refused {p.get('refused')}, stale {p.get('telemetry_stale_events')}")
    series = jl(os.path.join(R, "abr_series_A.jsonl"))
    lv = sorted({(x.get("bitrate_kbps"), x.get("level")) for x in series})
    print(f"   status series {len(series)} polls; (bitrate, level) seen {lv}")
    rows, ev = rec_lines(t0, t1)
    print(f"   recovery log events in the hold: {ev}")
    silent = (len(tr) == 0 and (st.get("transitions_this_session") in (0, None)) and fails == [])
    cls = "SILENT" if silent else ("NOT SILENT" if tr else "ZERO TRANSITIONS, ROW MISSED: " + ", ".join(fails or ["no report"]))
    for r in tr:
        print(f"     FIRED {r['at_utc']} elapsed {r.get('session_elapsed_ms')} {r['class']} "
              f"{r['from_kbps']}->{r['to_kbps']}: {json.dumps(r.get('measurements'))}")
    print(f"   -> Session A: {cls}")
    summary["A"] = {"classification": cls, "transitions": len(tr), "refusals": len(ref),
                    "fails": fails, "any_override_at_playing": anyo}

# ------------------------------------------------------------------ B ---
print("\n== Session B -- injected trigger")
if "B" not in idx:
    print("   NOT RUN / no index line")
    summary["B"] = {"classification": "NOT RUN"}
else:
    f = idx["B"]
    t0, t1 = f[4], f[5]
    print(f"   {t0} .. {t1}, report {f[3]}")
    anyo = armcheck("B")
    rep, fails = closeout("B")
    thermal(t0, t1)
    log = jl(os.path.join(R, "decision_log_B.jsonl"))
    tr = [r for r in log if r.get("event") == "transition"]
    done = [r for r in log if r.get("event") in ("transition_done", "transition_aborted", "actuator_failed")]
    ref = [r for r in log if r.get("event") == "refused"]
    inj = [r for r in log if r.get("event") == "inject"]
    i1, i2 = jf(os.path.join(R, "inject1_B.json")), jf(os.path.join(R, "inject2_B.json"))
    print(f"   injection 1: HTTP {i1 and i1.get('http')}; events "
          f"{[(e.get('event'), e.get('class'), e.get('reason'), e.get('from_kbps'), e.get('to_kbps')) for e in ((i1 or {}).get('body') or {}).get('events', [])]}")
    print(f"   injection 2: HTTP {i2 and i2.get('http')}; events "
          f"{[(e.get('event'), e.get('class'), e.get('reason'), e.get('hold_down_left_reports')) for e in ((i2 or {}).get('body') or {}).get('events', [])]}")
    print(f"   decision log: inject rows {len(inj)}, transitions {len(tr)}, done/aborted/failed "
          f"{[(r['event'], r.get('actuation_ms')) for r in done]}, refusals {[(r['class'], r['reason'], r.get('injected')) for r in ref]}")
    ssrc = [x["elapsed_ms"] for x in ((rep or {}).get("stream_discontinuities") or []) if x.get("type") == "ssrc_change"]
    print(f"   decoder ssrc_change elapsed_ms: {ssrc}")
    rows_tr = []
    for k, r in enumerate(tr):
        e = r.get("session_elapsed_ms") or 0
        d = done[k] if k < len(done) else {}
        match = next((s for s in ssrc if e <= s <= e + 15000), None)
        gap, retained = gap_after(rep, match) if (rep and match is not None) else (None, None)
        hb = r.get("holds_in_force_before") or {}
        rows_tr.append({"at_utc": r["at_utc"], "elapsed_ms": e, "class": r["class"], "from": r["from_kbps"],
                        "to": r["to_kbps"], "injected": r.get("injected"),
                        "reports_since_prev": hb.get("reports_since_transition"),
                        "clean_reports": hb.get("clean_reports"), "result": d.get("event"),
                        "actuation_ms": d.get("actuation_ms"), "cycle": d.get("cycle"),
                        "ssrc_elapsed_ms": match, "output_gap_ms": gap})
    print("   transitions (time, elapsed, class, from->to, reports since the previous, clean, result, "
          "actuation ms, ssrc, output gap in [ssrc, +1 s] vs 186.5 ms):")
    for x in rows_tr:
        print(f"     {x['at_utc']} e={x['elapsed_ms']} {x['class']:8s} {x['from']}->{x['to']} "
              f"since={x['reports_since_prev']} clean={x['clean_reports']} {x['result']} "
              f"{x['actuation_ms']} ms ssrc@{x['ssrc_elapsed_ms']} gap={x['output_gap_ms']} ms"
              + (f" ({x['output_gap_ms'] - S1_MEDIAN_MS:+.1f} vs 186.5)" if x['output_gap_ms'] is not None else ""))
    if rep:
        print(f"   slow events retained (>= 50 ms table): {len(rep.get('slow_events_ge_50_ms') or [])} "
              "(the table is bounded; a window it no longer covers reads None)")
    se = os.path.join(R, "status_end_B.json")
    st = (json.load(open(se)).get("adaptive_bitrate") or {}) if os.path.exists(se) else {}
    p = st.get("policy") or {}
    print(f"   status before BACK: mode {st.get('mode')}, state {st.get('state')}, level {st.get('level')}, "
          f"transitions_this_session {st.get('transitions_this_session')}, rate_limited {st.get('rate_limited')}, "
          f"suppressed {p.get('suppressed')}, refused {p.get('refused')}, dropped while actuating "
          f"{st.get('reports_dropped_while_actuating')}")
    series = jl(os.path.join(R, "abr_series_B.jsonl"))
    rows, ev = rec_lines(t0, t1)
    print(f"   recovery log events in the session: {ev}")

    first = rows_tr[0] if rows_tr else None
    ups = [x for x in rows_tr if x["class"] == "INCREASE"]
    # B1: exactly one ssrc_change from the first injection, before the increase path
    upper = ups[0]["elapsed_ms"] if ups else 10 ** 12
    b1_n = sum(1 for s in ssrc if first and first["elapsed_ms"] <= s < upper)
    b1 = bool(first and first["injected"] and first["class"] == "FALLBACK" and b1_n == 1)
    b2 = bool(first and first["to"] == 5000 and first["result"] == "transition_done")
    b3 = first["output_gap_ms"] if first else None
    # B4: blackout -- no decision row within 3 reports after each change, and 3 suppressed per transition
    dec_rows = [r for r in log if r.get("event") in ("transition", "refused", "hold")]
    b4_viol = []
    for x in rows_tr:
        if x["ssrc_elapsed_ms"] is None:
            continue
        for r in dec_rows:
            e = r.get("session_elapsed_ms")
            if isinstance(e, (int, float)) and x["ssrc_elapsed_ms"] < e <= x["ssrc_elapsed_ms"] + 3 * 2100 \
                    and not r.get("injected"):
                b4_viol.append((x["at_utc"], r.get("event"), r.get("reason")))
    blk = (p.get("suppressed") or {}).get("blackout")
    b4 = (not b4_viol) and blk is not None and blk >= 3 * len([x for x in rows_tr if x["result"] == "transition_done"])
    # B5: second injection refused by the hold-down, no transition from it
    ev2 = (((i2 or {}).get("body") or {}).get("events") or [])
    b5 = bool(ev2 and ev2[0].get("event") == "refused" and ev2[0].get("reason") == "hold_down"
              and not any(x["injected"] for x in rows_tr[1:]))
    # B6: increases 5000->5500->6000->7000, each >= 93 reports after the previous
    seq = [(x["from"], x["to"]) for x in ups]
    b6 = (seq == [(5000, 5500), (5500, 6000), (6000, 7000)]
          and all((x["reports_since_prev"] or 0) >= 93 and (x["clean_reports"] or 0) >= 90 for x in ups)
          and all(x["result"] == "transition_done" for x in ups))
    # B7: BACK -> report stored; lifecycle clean (session_started before, session_ended at BACK, no
    # desync_pause / encoder_restart / gave_up_saved in between); the controller back at 7000 after
    # BACK (its session_ended_reset row). The level before BACK is reported beside it (B6).
    from datetime import datetime, timedelta
    def _shift(t, s):
        return (datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ") + timedelta(seconds=s)).strftime("%Y-%m-%dT%H:%M:%SZ")
    around, ev_around = rec_lines(_shift(t0, -60), _shift(t1, 60))
    resets = [r for r in log if r.get("event") == "session_ended_reset" and r.get("at_utc", "")[:19] + "Z" >= t1]
    back_to_ref = bool(resets) and resets[0].get("level_kbps") == 7000
    b7 = (bool(rep) and "session_started" in ev_around and "session_ended" in ev_around
          and not any(e in ("desync_pause", "encoder_restart", "gave_up_saved") for e in ev_around)
          and back_to_ref)
    print(f"   B1 one ssrc_change from injection 1 before the increase path: {b1_n} -> {'MET' if b1 else 'NOT MET'}")
    print(f"   B2 level after = 5000 (mapping FALLBACK -> 5000): {'MET' if b2 else 'NOT MET'} "
          f"({first and (first['from'], first['to'], first['result'])})")
    print(f"   B3 output gap of that change: {b3} ms vs 186.5 ms (reported)")
    print(f"   B4 blackout: suppressed.blackout {blk} for {len(rows_tr)} transitions; decision rows inside "
          f"a blackout {b4_viol} -> {'MET' if b4 else 'NOT MET'}")
    print(f"   B5 second injection refused by the hold-down: {'MET' if b5 else 'NOT MET'} "
          f"({[(e.get('event'), e.get('reason'), e.get('hold_down_left_reports')) for e in ev2]})")
    print(f"   B6 increase path one rung per event, >= 93 reports apart: {seq} -> {'MET' if b6 else 'NOT MET'}")
    for x in ups:
        print(f"      {x['at_utc']} {x['from']}->{x['to']} after {x['reports_since_prev']} reports "
              f"({x['clean_reports']} clean)")
    print(f"   B7 BACK -> report stored, lifecycle clean, controller back at 7000: {'MET' if b7 else 'NOT MET'} "
          f"(report {'yes' if rep else 'no'}; recovery events around the session {ev_around}; "
          f"session_ended_reset after BACK {[(r['at_utc'], (r.get('before') or {}).get('level_kbps'), r.get('level_kbps')) for r in resets]}; "
          f"level before BACK {st.get('level')})")
    missed = [n for n, ok in (("B1", b1), ("B2", b2), ("B4", b4), ("B5", b5), ("B6", b6), ("B7", b7)) if not ok]
    cls = "WIRED" if not missed else "PARTIAL (" + ", ".join(missed) + ")"
    print(f"   ssrc_changes over B: {len(ssrc)} (4 expected if WIRED)")
    print(f"   close-out rows over B (reported; B is not ruled on them): fails {fails}")
    print(f"   -> Session B: {cls}")
    summary["B"] = {"classification": cls, "transitions": rows_tr, "missed": missed, "ssrc_changes": ssrc,
                    "b3_gap_ms": b3, "any_override_at_playing": anyo, "closeout_fails": fails}

json.dump(summary, open(os.path.join(HERE, "c3_l4_l1_summary.json"), "w"), indent=1, default=str)
print("\nsummary -> c3_l4_l1_summary.json")
