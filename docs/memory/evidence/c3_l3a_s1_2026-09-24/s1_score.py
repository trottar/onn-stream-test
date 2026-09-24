#!/usr/bin/env python3
"""C3-L3A-S1 transition soak: score items A-F of handoffs/C3-L3A-S1_TRANSITION_SOAK_TASK.md.

Written before the T1-T3 / H1-H3 data exist (only T0, the headless smoke,
had run). The rules below are copied from the task and are not changed after
the data.

Inputs (runs/): report_<arm>.json (decoder session), state_<arm>.json and
finalize_<arm>/<run_id>.json (T arms), heartbeat_<arm>.jsonl,
armcheck_<arm>.json (native-stream-status at PLAYING), status_end_<arm>.json
(before BACK), index.txt; ../t2_samples.jsonl; the close-out's C and W from
../../d_base_closeout_2026-09-23/closeout_summary.json.

A. Transition cost, T1-T3 Phase A (20 each = 5 jumps + 5 ramps x 3 rungs).
   Per transition, from the probe's finalize (every row anchored on its
   matched ssrc_change): largest output_gap_ms in [ssrc, ssrc + 1 s] and its
   codec_ms, first-IDR ms, jump_packets; from the state: spawn / first RTP
   resume / host verified ms. A session whose alignment spread > 1 s has its
   decoder-axis rows INDETERMINATE. A transition counts if its session
   aligned and its window is fully covered by retained slow events.
   Distributions (n, min, median, p95, max) by shape (jump vs ramp rung),
   direction (down = to < from), state (cold = T1 transitions whose SSRC
   change is in the first 420 s of T1's decoder session; everything else
   warm) and per session.
   Classification: COST CHARACTERIZED if >= 54 of 60 align and are covered;
   otherwise PARTIAL (n). No threshold on the size.

B. Settling, T1-T3 (10 sequences each). settled_s, distinct snapshots,
   sample_interval_ms, never-settled count. A sequence that needed a third
   distinct report or more (distinct > 2, or never settled) is listed with
   its samples.

C. Lifecycle, 60 transitions: fec_send_errors_delta, audio_send_errors_delta,
   controller_bad_packets_delta per transition and totals; decoder
   ssrc_changes vs the probe's expected count per T session.
   CLEAN only if every delta is 0 and every session's SSRC count matches.

D. Close-out rows, six sessions, same counters as closeout_score.py:
   spikes >= 20 ms / min, rendered fps, stale drops / min, video loss / min
   post-FEC, audio underruns per session, prolonged_starvation / min,
   fec_recovered / min (and max output gap, reported, excluded from the
   rule). Band = the five no-transition values H1, H2, H3, close-out C, W.
   Worse = higher, except rendered fps (lower). A row is
   ELEVATED BY TRANSITIONS only if ALL THREE T values are worse than the
   band's worst AND the T median is beyond the band's worst by more than the
   band's width (max - min of the five); otherwise WITHIN THE NIGHT'S NOISE.
   A missing session leaves the rule unevaluable for that row
   (INDETERMINATE), never evaluated on fewer values.
   Baseline stays met in T (the close-out's definition): in every T session
   spikes < 200/min, rendered fps >= 59.5, stale < 20/min, video loss < 10/min
   post-FEC, audio underruns < 5/min. Max output gap is excluded here: in a T
   session it is a transition by construction (it is part of A).

E. Warm-state context: onn cpu-thermal and thermal status nearest each
   session's start and end (t2 samples); audio loss per minute per session
   (decoder report, after de-duplication) under the same band rule as D; the
   per-minute heartbeat series of audio_lost_packets.

F. Controller transport, zero input: lost_packets and packets_received at
   PLAYING (armcheck) and before BACK (status_end), per minute between the
   two files' write times; for T arms also the probe state's
   conditions_before / conditions_after. Recorded, not judged.

Writes s1_score.txt and s1_summary.json beside this script.
"""
import glob, json, os, statistics as st
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")
CLOSE = os.path.join(HERE, "..", "d_base_closeout_2026-09-23", "closeout_summary.json")
T_ARMS, H_ARMS = ["T1", "T2", "T3"], ["H1", "H2", "H3"]
OUT = []


def p(*a):
    OUT.append(" ".join(str(x) for x in a))


def load(path):
    try:
        return json.load(open(path))
    except Exception:
        return None


def dist(vals):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return {"n": 0}
    return {"n": len(v), "min": v[0], "median": round(st.median(v), 1),
            "p95": v[min(len(v) - 1, int(round(0.95 * (len(v) - 1))))], "max": v[-1]}


def fmt(d):
    return "n 0" if not d["n"] else f"n {d['n']:>2}  min {d['min']}  median {d['median']}  p95 {d['p95']}  max {d['max']}"


def analysis_of(arm):
    files = glob.glob(os.path.join(R, f"finalize_{arm}", "*.json"))
    return load(files[0]) if files else None


def utc(s):
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


index = {}
for line in open(os.path.join(R, "index.txt")):
    f = line.split()
    if f and f[0] in T_ARMS + H_ARMS + ["T0"] and len(f) >= 6:
        index[f[0]] = {"mode": f[1], "report": f[3], "t0": f[4], "t1": f[5]}

summary = {"sessions": index}

# ---------------------------------------------------------------- A, B, C
rows, settle, life, ssrc = [], [], [], {}
for arm in T_ARMS:
    a, s = analysis_of(arm), load(os.path.join(R, f"state_{arm}.json"))
    if not a or not s:
        p(f"[A] {arm}: no finalize or state -> INDETERMINATE")
        continue
    view = (a.get("decoder") or {}).get("view") or {}
    al = view.get("alignment") or {}
    cov = view.get("slow_event_coverage") or {}
    summary.setdefault("alignment", {})[arm] = {k: al.get(k) for k in ("ok", "pairs", "offset_s", "spread_s", "max_abs_residual_s")}
    summary.setdefault("coverage", {})[arm] = cov
    trans = s["transitions"]
    per = view.get("per_transition") or []
    for i, t in enumerate(trans):
        row = per[i] if i < len(per) else {}
        rows.append({
            "arm": arm, "shape": t["shape"], "rung": t["step_index"],
            "direction": "down" if (t["to_kbps"] or 0) < (t["from_kbps"] or 0) else "up",
            "state": "cold" if arm == "T1" and (row.get("ssrc_elapsed_ms") or 1e12) < 420000 else "warm",
            "aligned": bool(al.get("ok")), "covered": row.get("slow_events_covered") == "full",
            "gap": row.get("max_output_gap_ms_in_1s"), "codec": row.get("max_gap_codec_ms"),
            "idr": row.get("first_idr_ms"), "jump": row.get("jump_packets"),
            "spawn": t.get("ffmpeg_spawn_ms"), "rtp": t.get("first_rtp_resume_ms"),
            "silence": t.get("rtp_silence_after_spawn_ms"), "verified": t.get("host_verified_ms"),
            "deltas": (t.get("fec_send_errors_delta"), t.get("audio_send_errors_delta"), t.get("controller_bad_packets_delta")),
        })
    for q in (a.get("settling") or {}).get("sequences", []):
        settle.append(dict(q, arm=arm))
    dec = a.get("decoder") or {}
    ssrc[arm] = (dec.get("ssrc_changes"), dec.get("expected_ssrc_changes"))
    for e in s["events"]:
        if e["kind"] == "sequence":
            st_ = e.get("settling") or {}
            for q in settle:
                if q["arm"] == arm and q["index"] == e["index"]:
                    q["samples"] = st_.get("samples")

good = [r for r in rows if r["aligned"] and r["covered"]]
p("== A. Transition cost (T1-T3 Phase A)")
for arm in T_ARMS:
    al = summary.get("alignment", {}).get(arm)
    cv = summary.get("coverage", {}).get(arm) or {}
    p(f"  {arm}: alignment {al}; slow events retained {cv.get('retained')}/{cv.get('capacity')} "
      f"(marked {cv.get('retained_marked')}/{cv.get('capacity_marked')}, recent {cv.get('retained_recent')}/{cv.get('capacity_recent')}), "
      f"saturated {cv.get('saturated')}, covered from decoder {cv.get('covered_from_decoder_ms')} ms")
    unc = [f"{r['shape']}#{i}" for i, r in enumerate(x for x in rows if x['arm'] == arm) if not r["covered"]]
    if unc:
        p(f"    not fully covered: {unc}")
n_all, n_good = len(rows), len(good)
cls_a = "COST CHARACTERIZED" if n_good >= 54 else f"PARTIAL ({n_good} of {n_all})"
p(f"  transitions {n_all}; aligned and covered {n_good} -> {cls_a}")
summary["A"] = {"transitions": n_all, "aligned_covered": n_good, "classification": cls_a, "groups": {}}
groups = [("all", lambda r: True), ("jump", lambda r: r["shape"] == "jump"), ("ramp rung", lambda r: r["shape"] == "ramp"),
          ("down", lambda r: r["direction"] == "down"), ("up", lambda r: r["direction"] == "up"),
          ("cold", lambda r: r["state"] == "cold"), ("warm", lambda r: r["state"] == "warm")] + \
         [(arm, (lambda a: lambda r: r["arm"] == a)(arm)) for arm in T_ARMS]
for name, f in groups:
    g = [r for r in good if f(r)]
    ga = [r for r in rows if f(r)]
    block = {k: dist([r[k] for r in (g if k in ("gap", "codec") else ga)]) for k in
             ("gap", "codec", "idr", "jump", "spawn", "rtp", "silence", "verified")}
    summary["A"]["groups"][name] = block
    p(f"  [{name}]")
    for k, label in (("gap", "max output gap in 1 s (ms)"), ("codec", "its codec_ms"), ("idr", "first IDR (ms)"),
                     ("jump", "jump_packets"), ("spawn", "spawn (ms)"), ("rtp", "first RTP resume (ms)"),
                     ("silence", "RTP silence after spawn (ms)"), ("verified", "host verified (ms)")):
        p(f"    {label:32s} {fmt(block[k])}")

p("")
p("== B. Settling (T1-T3, 10 sequences each)")
vals = [q.get("settled_s") for q in settle if q.get("measured")]
never = [q for q in settle if q.get("measured") and q.get("settled_s") is None]
third = [q for q in settle if q.get("measured") and (q.get("settled_s") is None or (q.get("distinct_snapshots") or 0) > 2)]
p(f"  sequences {len(settle)}; measured {sum(1 for q in settle if q.get('measured'))}; never settled {len(never)}")
p(f"  settled_s {fmt(dist(vals))}")
p(f"  distinct snapshots {sorted(set(q.get('distinct_snapshots') for q in settle))}; "
  f"sample_interval_ms {sorted(set(q.get('sample_interval_ms') for q in settle))}; "
  f"cadence_ms {fmt(dist([q.get('snapshot_cadence_ms') for q in settle]))}; budget_ok {sorted(set(str(q.get('budget_ok')) for q in settle))}")
p(f"  needed a third report or more: {len(third)}")
for q in third:
    p(f"    {q['arm']} seq {q['index']} {q['shape']}: settled {q.get('settled_s')} distinct {q.get('distinct_snapshots')}")
    for smp in q.get("samples") or []:
        if smp.get("new_snapshot") or not smp.get("good"):
            p(f"      {smp}")
summary["B"] = {"n": len(settle), "settled_s": dist(vals), "never": len(never), "third_or_more": len(third)}

p("")
p("== C. Lifecycle")
tot = [sum(int(r["deltas"][i] or 0) for r in rows) for i in range(3)]
nonzero = [r for r in rows if any(int(x or 0) for x in r["deltas"])]
p(f"  transitions {len(rows)}; totals fec_send_errors {tot[0]}, audio_send_errors {tot[1]}, controller_bad_packets {tot[2]}; transitions with a nonzero delta {len(nonzero)}")
for arm in T_ARMS:
    p(f"  {arm}: decoder ssrc_changes {ssrc.get(arm, (None, None))[0]} vs expected {ssrc.get(arm, (None, None))[1]}")
clean = (len(rows) == 60 and not nonzero and all(arm in ssrc and ssrc[arm][0] == ssrc[arm][1] for arm in T_ARMS))
cls_c = "CLEAN" if clean else "NOT CLEAN"
p(f"  -> {cls_c}")
summary["C"] = {"totals": tot, "nonzero": len(nonzero), "ssrc": ssrc, "classification": cls_c}

# ---------------------------------------------------------------- D, E
close = (load(CLOSE) or {}).get("rows", {})


def score(arm):
    rep = load(os.path.join(R, f"report_{arm}.json"))
    if not rep:
        return None
    r = rep["report"]
    d, v, a = r["decoder"], r["video"], r["audio"]
    mins = r["duration_ms"] / 60000.0
    return {"duration_min": round(mins, 2), "spikes_20_per_min": d["spike_20_ms"] / mins,
            "rendered_fps": d["rendered_frames"] / (mins * 60), "stale_output_drops_per_min": d["stale_output_drops"] / mins,
            "video_lost_per_min_post_fec": v["lost_packets"] / mins, "audio_underruns_total": a["underruns"],
            "audio_underruns_per_min": a["underruns"] / mins,
            "prolonged_starvation_per_min": a["prolonged_starvation_events"] / mins,
            "video_fec_recovered_per_min": v["fec_recovered_packets"] / mins,
            "audio_lost_per_min_after_dedup": a["lost_packets"] / mins, "max_output_gap_ms": d["max_output_gap_ms"]}


S = {arm: score(arm) for arm in T_ARMS + H_ARMS}
S["C"], S["W"] = close.get("C"), close.get("W")
summary["rows"] = S
RULE_ROWS = [("spikes_20_per_min", "spikes >= 20 ms / min", +1), ("rendered_fps", "rendered fps", -1),
             ("stale_output_drops_per_min", "stale drops / min", +1),
             ("video_lost_per_min_post_fec", "video loss / min post-FEC", +1),
             ("audio_underruns_total", "audio underruns / session", +1),
             ("prolonged_starvation_per_min", "prolonged starvation / min", +1),
             ("video_fec_recovered_per_min", "fec_recovered / min", +1)]


def band_rule(key, sign):
    band = [S[k][key] if S.get(k) else None for k in H_ARMS + ["C", "W"]]
    tv = [S[k][key] if S.get(k) else None for k in T_ARMS]
    if None in band or None in tv:
        return "INDETERMINATE (a session is missing)", band, tv, None
    worst = max(band) if sign > 0 else min(band)
    width = max(band) - min(band)
    tmed = st.median(tv)
    beyond = (tmed - worst) * sign
    all_worse = all((x - worst) * sign > 0 for x in tv)
    verdict = "ELEVATED BY TRANSITIONS" if all_worse and beyond > width else "WITHIN THE NIGHT'S NOISE"
    return verdict, band, tv, {"band_worst": worst, "band_width": width, "t_median": tmed,
                               "t_median_beyond_worst": beyond, "all_three_worse": all_worse}


p("")
p("== D. Close-out rows: six sessions against the night's band (H1 H2 H3 + close-out C W)")
cols = T_ARMS + H_ARMS + ["C", "W"]
p("  " + f"{'row':30s}" + "".join(f"{c:>9s}" for c in cols))
for key, label, _ in RULE_ROWS + [("audio_underruns_per_min", "(audio underruns / min)", 0),
                                   ("max_output_gap_ms", "max output gap (ms) [not ruled]", 0),
                                   ("duration_min", "(duration min)", 0)]:
    p("  " + f"{label:30s}" + "".join(f"{S[c][key]:9.2f}" if S.get(c) and S[c].get(key) is not None else f"{'-':>9s}" for c in cols))
summary["D"] = {}
for key, label, sign in RULE_ROWS:
    verdict, band, tv, m = band_rule(key, sign)
    summary["D"][key] = {"verdict": verdict, **(m or {})}
    if m:
        p(f"  {label:30s} {verdict}: T {[round(x, 2) for x in tv]} median {m['t_median']:.2f}; band worst {m['band_worst']:.2f}, "
          f"width {m['band_width']:.2f}; T median beyond worst by {m['t_median_beyond_worst']:+.2f}; all three worse {m['all_three_worse']}")
    else:
        p(f"  {label:30s} {verdict}")
TARGETS = [("spikes_20_per_min", lambda x: x < 200, "< 200"), ("rendered_fps", lambda x: x >= 59.5, ">= 59.5"),
           ("stale_output_drops_per_min", lambda x: x < 20, "< 20"), ("video_lost_per_min_post_fec", lambda x: x < 10, "< 10"),
           ("audio_underruns_per_min", lambda x: x < 5, "< 5 / min")]
fails = [(arm, k, round(S[arm][k], 2), t) for arm in T_ARMS if S.get(arm) for k, ok, t in TARGETS if not ok(S[arm][k])]
missing = [arm for arm in T_ARMS if not S.get(arm)]
met = "YES" if not fails and not missing else ("NO" if fails else "INDETERMINATE")
p(f"  Baseline stays met in the T sessions: {met}" + (f" -- failing {fails}" if fails else "") + (f" -- missing {missing}" if missing else ""))
summary["D"]["baseline_met_in_T"] = {"answer": met, "failing": fails, "missing": missing}

p("")
p("== E. Warm-state context")
heat = [json.loads(l) for l in open(os.path.join(HERE, "t2_samples.jsonl")) if l.strip()] \
    if os.path.exists(os.path.join(HERE, "t2_samples.jsonl")) else []


def near(ts):
    if not heat:
        return None
    t = utc(ts)
    best = min(heat, key=lambda x: abs((utc(x["at_utc"]) - t).total_seconds()))
    o = best.get("onn") or {}
    return {"at": best["at_utc"][11:19], "cpu_c": o.get("cpu_thermal_c"), "status": o.get("thermal_status")}


summary["E"] = {"thermal": {}, "audio_loss_series": {}}
for arm in ["T0"] + [x for pair in zip(T_ARMS, H_ARMS) for x in pair]:
    if arm not in index:
        continue
    a0, a1 = near(index[arm]["t0"]), near(index[arm]["t1"])
    summary["E"]["thermal"][arm] = {"start": a0, "end": a1}
    series = []
    hb = os.path.join(R, f"heartbeat_{arm}.jsonl")
    if os.path.exists(hb):
        rows_h = [json.loads(l) for l in open(hb) if l.strip()]
        by_min = {}
        for h in rows_h:
            by_min.setdefault(int(h["elapsed_ms"] // 60000), []).append(h)
        prev = None
        for m_ in sorted(by_min):
            last = by_min[m_][-1]
            if prev is not None:
                series.append(last.get("audio_lost_packets", 0) - prev.get("audio_lost_packets", 0))
            prev = last
    summary["E"]["audio_loss_series"][arm] = series
    p(f"  {arm} ({index[arm]['mode']}) {index[arm]['t0'][11:19]}-{index[arm]['t1'][11:19]}Z onn cpu {a0 and a0['cpu_c']} -> {a1 and a1['cpu_c']} C, "
      f"status {a0 and a0['status']}/{a1 and a1['status']}; audio lost per minute (heartbeat) {series}")
verdict, band, tv, m = band_rule("audio_lost_per_min_after_dedup", +1)
summary["E"]["audio_loss_rule"] = {"verdict": verdict, **(m or {})}
p(f"  audio loss / min after de-dup, band rule: {verdict}" + (f": T {[round(x, 2) for x in tv]}, band {[round(x, 2) for x in band]}, "
  f"T median beyond worst by {m['t_median_beyond_worst']:+.2f} vs width {m['band_width']:.2f}" if m else ""))

p("")
p("== F. Controller transport, zero input")
summary["F"] = {}
for arm in ["T0"] + [x for pair in zip(T_ARMS, H_ARMS) for x in pair]:
    a0p, a1p = os.path.join(R, f"armcheck_{arm}.json"), os.path.join(R, f"status_end_{arm}.json")
    a0, a1 = load(a0p), load(a1p)
    if not a0 or not a1:
        continue
    c0, c1 = a0.get("controller") or {}, a1.get("controller") or {}
    mins = (os.path.getmtime(a1p) - os.path.getmtime(a0p)) / 60.0
    lost = (c1.get("lost_packets") or 0) - (c0.get("lost_packets") or 0)
    rx = (c1.get("packets_received") or 0) - (c0.get("packets_received") or 0)
    rec = {"minutes": round(mins, 2), "lost": lost, "received": rx, "lost_per_min": round(lost / mins, 1),
           "received_per_min": round(rx / mins, 1), "bad_packets_end": c1.get("bad_packets")}
    s = load(os.path.join(R, f"state_{arm}.json"))
    if s:
        rec["probe_conditions"] = [s["conditions_before"].get("controller_lost_packets"), s["conditions_after"].get("controller_lost_packets")]
    summary["F"][arm] = rec
    p(f"  {arm}: {rec}")

open(os.path.join(HERE, "s1_score.txt"), "w").write("\n".join(OUT) + "\n")
json.dump(summary, open(os.path.join(HERE, "s1_summary.json"), "w"), indent=1, default=str)
print("\n".join(OUT))
