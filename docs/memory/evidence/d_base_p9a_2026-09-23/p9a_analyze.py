#!/usr/bin/env python3
"""D-BASE-P9a analysis: the 12/17 cushion against measured noise.

Arms in run order: A3 (3/8), B2 (12/17), A4 (3/8), B3 (12/17), from
runs/report_<arm>.json and runs/heartbeat_<arm>.jsonl.

Underruns are placed in time from the heartbeat log's cumulative
`audio_underruns` (every 2 s, whole session): the first row's value is the
pre-heartbeat (startup) share, each later tick's delta is placed at that
tick, and the report total minus the last heartbeat value is the tail
after the last tick (BACK). An EVENT is a run of consecutive ticks with a
non-zero delta; the startup share and the tail are events of their own.

The 3/8 noise band: underrun totals of every 3/8 session on record with
the default 2 s heartbeat -- P7, P8-A, P8-B, P9-A2, A3, A4 (P8-C is left
out: 10 s heartbeat) -- and the largest single 3/8 event among those with
a heartbeat log.

Pre-registered reading (handoffs/D-BASE-P9A_TASK.md), per B arm:
starvation/min >= 80 % below mean(A3, A4); avg residence +30-55 ms over
mean(A3, A4); holes within 20 % of the A arms; underrun total <= band max
+ the largest single 3/8 event. All four in both B arms -> adopt 12/17.
Loss: time-driven if A4 >= A3 and B3 >= B2 and the B arms are not
systematically above their neighbouring A arms; cushion-linked if both B
arms exceed both A arms by >= 50 %.
"""
import json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.dirname(HERE)
RUN_ORDER = ["A3", "B2", "A4", "B3"]
SRC = {a: (os.path.join(HERE, "runs", f"report_{a}.json"),
           os.path.join(HERE, "runs", f"heartbeat_{a}.jsonl")) for a in RUN_ORDER}
NOISE_38 = {
    "P7": (f"{EV}/d_base_p7_2026-09-22/report_P7.json", f"{EV}/d_base_p7_2026-09-22/heartbeat_P7.jsonl"),
    "P8-A": (f"{EV}/d_base_p8_2026-09-22/runs/report_A.json", f"{EV}/d_base_p8_2026-09-22/runs/heartbeat_A.jsonl"),
    "P8-B": (f"{EV}/d_base_p8_2026-09-22/runs/report_B.json", f"{EV}/d_base_p8_2026-09-22/runs/heartbeat_B.jsonl"),
    "P9-A2": (f"{EV}/d_base_p9_2026-09-23/runs/report_A2.json", f"{EV}/d_base_p9_2026-09-23/runs/heartbeat_A2.jsonl"),
    "A3": SRC["A3"], "A4": SRC["A4"],
}
CONTEXT_1217 = {"P9-B": (f"{EV}/d_base_p9_2026-09-23/runs/report_B.json",
                         f"{EV}/d_base_p9_2026-09-23/runs/heartbeat_B.jsonl")}


def report(path):
    d = json.load(open(path))
    return d.get("report", d)


def heartbeat(path):
    if not os.path.exists(path):
        return []
    rows = [json.loads(l) for l in open(path) if l.strip()]
    return [r for r in rows if "audio_underruns" in r]


def events(rep, hb):
    """[(label, at_s, count)] -- startup share, per-tick runs, tail."""
    total = rep["audio"]["underruns"]
    if not hb:
        return None
    out = []
    first = hb[0]["audio_underruns"]
    if first:
        out.append(("before first heartbeat", hb[0]["elapsed_ms"] / 1000.0, first))
    run, run_at = 0, None
    for a, b in zip(hb, hb[1:]):
        d = b["audio_underruns"] - a["audio_underruns"]
        if d > 0:
            if run == 0:
                run_at = b["elapsed_ms"] / 1000.0
            run += d
        elif run:
            out.append(("ticks", run_at, run)); run = 0
    if run:
        out.append(("ticks", run_at, run))
    tail = total - hb[-1]["audio_underruns"]
    if tail:
        out.append(("after last heartbeat", hb[-1]["elapsed_ms"] / 1000.0, tail))
    return out


def loss_per_min(hb):
    d = [b["audio_lost_packets"] - a["audio_lost_packets"] for a, b in zip(hb, hb[1:])]
    return [sum(d[i:i + 30]) for i in range(0, len(d), 30)]


def row(rep, hb):
    a, d, v = rep["audio"], rep["decoder"], rep["video"]
    mins = rep["duration_ms"] / 60000.0
    hg = a["arrival_holes"]["histograms"]
    edges = hg["length_edges_ms"] + [None]
    ts_under = [(t[0], t[1]) for t in a.get("tick_series", []) if t[1] > 0]
    return {
        "cushion": f"{a['queue_target_packets']}/{a['queue_capacity_packets']}",
        "cushion_source": a.get("queue_cushion_source"),
        "duration_s": round(rep["duration_ms"] / 1000.0, 1),
        "underruns": a["underruns"],
        "tick_series_underruns_first_200s": ts_under,
        "prolonged_starvation_events": a["prolonged_starvation_events"],
        "starvation_per_min": a["prolonged_starvation_events"] / mins,
        "concealed_underruns": a["concealed_underruns"],
        "smooth_latency_trims": a["smooth_latency_trims"],
        "lost_packets": a["lost_packets"],
        "concealed_loss_packets": a["concealed_loss_packets"],
        "avg_queue_residence_ms": a["avg_queue_residence_ms"],
        "max_queue_residence_ms": a["max_queue_residence_ms"],
        "max_queue_depth": a["max_queue_depth"],
        "first_write_elapsed_ms": a["first_write_elapsed_ms"],
        "startup_wait_ms": a["startup_wait_ms"],
        "holes": hg["count"][0],
        "holes_ge_40": hg["count"][1],
        "hole_length_ms": {f"{lo}-{hi if hi else 'max'}": c for lo, hi, c in zip(edges, edges[1:], hg["length"])},
        "rendered_fps": d["rendered_frames"] / (rep["duration_ms"] / 1000.0),
        "spike_20_per_min": d["spike_20_ms"] / mins,
        "max_output_gap_ms": d["max_output_gap_ms"],
        "video_lost_per_min": v["lost_packets"] / mins,
        "underrun_events": events(rep, hb),
        "audio_loss_per_min": loss_per_min(hb) if hb else None,
        "heartbeat_rows": len(hb),
    }


rows = {}
for arm in RUN_ORDER:
    r, h = SRC[arm]
    if os.path.exists(r):
        rows[arm] = row(report(r), heartbeat(h))

print("== raw, the four arms in run order")
scalar = [k for k in next(iter(rows.values())) if not isinstance(next(iter(rows.values()))[k], (list, dict))]
print(f"{'field':30s}" + "".join(f"{a:>12s}" for a in rows))
for k in scalar:
    print(f"{k:30s}" + "".join(
        f"{rows[a][k]:12.2f}" if isinstance(rows[a][k], float) else f"{str(rows[a][k]):>12s}" for a in rows))
print("\n== hole length (ms: count)")
for a in rows:
    print(f"  {a}: {rows[a]['hole_length_ms']}")
print("\n== underruns: tick_series rows (first ~200 s) and whole-session events from the heartbeat")
for a in rows:
    ev = rows[a]["underrun_events"]
    print(f"  {a} ({rows[a]['cushion']}): total {rows[a]['underruns']}; tick_series {rows[a]['tick_series_underruns_first_200s']}")
    print(f"      events ({len(ev)}): " + ", ".join(f"{c}@{t:.0f}s" + ("*" if lab != "ticks" else "") for lab, t, c in ev))
print("      (* = before the first heartbeat / after the last)")

print("\n== the 3/8 noise band (2 s heartbeat sessions)")
band = {}
for name, (r, h) in NOISE_38.items():
    if not os.path.exists(r):
        continue
    rep = report(r)
    ev = events(rep, heartbeat(h))
    band[name] = {"total": rep["audio"]["underruns"],
                  "largest_event": max((c for _, _, c in ev), default=0) if ev is not None else None,
                  "events": ev}
    print(f"  {name:6s} total {band[name]['total']:3d}; largest event {band[name]['largest_event']}; "
          f"events {len(ev) if ev is not None else 'n/a'}")
totals = [b["total"] for b in band.values()]
largest = max(b["largest_event"] for b in band.values() if b["largest_event"] is not None)
band_sum = {"sessions": list(band), "min": min(totals), "max": max(totals),
            "median": st.median(totals), "largest_single_event": largest,
            "allowance": max(totals) + largest}
print(f"  band: min {band_sum['min']}, median {band_sum['median']}, max {band_sum['max']}; "
      f"largest single 3/8 event {largest}; B allowance = max + largest = {band_sum['allowance']}")
for name, (r, h) in CONTEXT_1217.items():
    ev = events(report(r), heartbeat(h))
    print(f"  context {name} (12/17): total {report(r)['audio']['underruns']}; events "
          + ", ".join(f"{c}@{t:.0f}s" for _, t, c in ev))

verdict = {}
if all(a in rows for a in RUN_ORDER):
    A = [rows["A3"], rows["A4"]]
    a_pse = st.mean(x["starvation_per_min"] for x in A)
    a_res = st.mean(x["avg_queue_residence_ms"] for x in A)
    a_holes = st.mean(x["holes"] for x in A)
    print(f"\n== pre-registered reading (A mean: starvation {a_pse:.2f}/min, residence {a_res:.2f} ms, holes {a_holes:.0f})")
    for b in ("B2", "B3"):
        x = rows[b]
        drop = 1 - x["starvation_per_min"] / a_pse
        dres = x["avg_queue_residence_ms"] - a_res
        hdel = x["holes"] / a_holes - 1
        hdel_each = [x["holes"] / y["holes"] - 1 for y in A]
        checks = {
            "starvation_drop_ge_80": drop >= 0.80,
            "residence_30_55": 30 <= dres <= 55,
            "holes_within_20pct": all(abs(h) <= 0.20 for h in hdel_each),
            "underruns_within_allowance": x["underruns"] <= band_sum["allowance"],
        }
        verdict[b] = {"drop": drop, "d_residence_ms": dres, "holes_vs_A_mean": hdel,
                      "holes_vs_each_A": hdel_each, "underruns": x["underruns"],
                      "underruns_le_band_max": x["underruns"] <= band_sum["max"], **checks}
        print(f"  {b}: starvation drop {drop:.1%}; residence {dres:+.1f} ms; holes {hdel:+.1%} "
              f"(vs A3 {hdel_each[0]:+.1%}, A4 {hdel_each[1]:+.1%}); underruns {x['underruns']} "
              f"(band max {band_sum['max']}, allowance {band_sum['allowance']}) -> "
              + ", ".join(f"{k} {'PASS' if v else 'FAIL'}" for k, v in checks.items()))
    adopt = all(all(verdict[b][k] for k in ("starvation_drop_ge_80", "residence_30_55",
                                            "holes_within_20pct", "underruns_within_allowance"))
                for b in ("B2", "B3"))
    verdict["reading"] = "ADOPT 12/17" if adopt else "KEEP 3/8"
    print(f"  READING: {verdict['reading']}")

    L = {a: rows[a]["lost_packets"] for a in RUN_ORDER}
    print("\n== audio loss, run order (total; per-minute series)")
    for a in RUN_ORDER:
        print(f"  {a} ({rows[a]['cushion']}): {L[a]}; {rows[a]['audio_loss_per_min']}")
    time_driven = (L["A4"] >= L["A3"] and L["B3"] >= L["B2"]
                   and not (L["B2"] > max(L["A3"], L["A4"]) and L["B3"] > L["A4"]))
    cushion_linked = min(L["B2"], L["B3"]) >= 1.5 * max(L["A3"], L["A4"])
    loss = ("CUSHION-LINKED" if cushion_linked else
            "TIME-DRIVEN" if time_driven else "NEITHER PRE-REGISTERED PATTERN")
    verdict["loss"] = {"totals": L, "time_driven": time_driven,
                       "cushion_linked": cushion_linked, "reading": loss}
    print(f"  A4>=A3 {L['A4'] >= L['A3']}; B3>=B2 {L['B3'] >= L['B2']}; "
          f"B systematically above neighbouring A {L['B2'] > max(L['A3'], L['A4']) and L['B3'] > L['A4']}; "
          f"both B >= 1.5x both A {cushion_linked} -> {loss}")

json.dump({"rows": rows, "noise_band": {**band_sum, "per_session": band}, "verdict": verdict},
          open(os.path.join(HERE, "p9a_summary.json"), "w"), indent=1)
