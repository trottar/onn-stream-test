#!/usr/bin/env python3
"""D-BASE-P8 analysis: where the audio arrival holes sit against the 2 s senders.

Reads runs/report_<arm>.json (audio.arrival_holes, schema v2) for A, B, C.
Uses the on-device whole-session histograms (build v2: the raw ring keeps
only the last 300 rows, so rows are used for nothing but a spot check).
Per arm: hole count and rate per minute, the length distribution, and the
distribution of ms since the last heartbeat start in 50 ms bins over
0-2,000 ms (0-10,000 ms for C), with the share inside 0-100 ms -- the
pre-registered statistic. The same for the client-health post (the other
2 s sender), reported beside it. prolonged_starvation_events/min beside
P7's 32.5.

Primary population: every hole the ring holds (gap > 15 ms), as the task
defines it. Secondary, labelled: holes >= 40 ms, the P7 "55-60 ms hole".
Under no alignment a 2 s sender puts 100/2000 = 5 % of holes in 0-100 ms.
"""
import json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
ARMS = [("A", 2000), ("B", 2000), ("C", 10000)]
P7_PSE_PER_MIN = 32.5


def load(arm):
    p = os.path.join(RUNS, f"report_{arm}.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p))["report"]


def hist(values, span, width=50):
    bins = [0] * (span // width)
    out = 0
    for v in values:
        if v is None or v < 0 or v >= span:
            out += 1
            continue
        bins[int(v // width)] += 1
    return bins, out


def describe(label, which, hg, span, dur_min):
    n = hg["count"][which]
    print(f"  [{label}] holes {n}, {n / dur_min:.1f}/min")
    res = {"n": n, "per_min": n / dur_min}
    if which == 0:
        edges = hg["length_edges_ms"] + [None]
        dist = {f"{a}-{b if b else 'max'}": c for a, b, c in zip(edges, edges[1:], hg["length"])}
        print(f"    length ms: {dist}")
        res["length_dist"] = dist
    for name, key, sp in (("heartbeat", "since_heartbeat", span), ("health", "since_health", 2000)):
        allbins = hg[f"{key}_{'all' if which == 0 else 'long'}"]
        bins = allbins[: sp // 50]
        beyond = sum(allbins[sp // 50:])
        out = hg[f"{key}_outside"][which] + beyond
        valid = sum(bins)
        first2 = bins[0] + bins[1]
        share = first2 / valid if valid else float("nan")
        flat = st.mean(bins[2:]) if len(bins) > 2 else 0
        inflight = hg["heartbeat_in_flight"][which] if name == "heartbeat" else None
        print(f"    since {name} start: 0-100 ms {first2}/{valid} = {share:.1%} "
              f"(uniform {100 / sp:.1%}); first 4 bins {bins[:4]}, mean of rest {flat:.1f}; "
              f"outside 0-{sp}: {out}" + (f"; in-flight {inflight}" if inflight is not None else ""))
        res[name] = {"share_0_100": share, "bins": bins, "outside": out, "in_flight": inflight}
    return res


summary = {}
for arm, span in ARMS:
    r = load(arm)
    if r is None:
        print(f"== {arm}: no report"); continue
    a = r["audio"]
    h = a.get("arrival_holes") or {}
    rows = h.get("rows", [])
    dur_min = r["duration_ms"] / 60000.0
    pse = a.get("prolonged_starvation_events")
    print(f"== {arm}: {r['duration_ms'] / 1000:.0f} s, heartbeat_interval_ms {a.get('heartbeat_interval_ms')}, "
          f"ring total {h.get('total')} retained {h.get('retained')} (cap {h.get('capacity')}); "
          f"prolonged_starvation_events {pse} = {pse / dur_min:.1f}/min (P7 {P7_PSE_PER_MIN})")
    summary[arm] = {"duration_min": dur_min, "pse_per_min": pse / dur_min,
                    "ring_total": h.get("total"), "ring_retained": h.get("retained"),
                    "heartbeat_interval_ms": a.get("heartbeat_interval_ms"),
                    "all": describe("all > 15 ms", 0, h["histograms"], span, dur_min),
                    "ge40": describe("secondary: >= 40 ms", 1, h["histograms"], span, dur_min)}

print("\n== pre-registered reading ==")
if all(k in summary for k in "ABC"):
    A, B, C = (summary[k]["all"] for k in "ABC")
    hb_aligned = A["heartbeat"]["share_0_100"] >= 0.70 and B["heartbeat"]["share_0_100"] >= 0.70
    c_drop = 1 - C["per_min"] / A["per_min"]
    b_drop = 1 - B["per_min"] / A["per_min"]
    print(f"heartbeat share 0-100 ms: A {A['heartbeat']['share_0_100']:.1%}, B {B['heartbeat']['share_0_100']:.1%} (>= 70 % needed)")
    print(f"C rate vs A: {C['per_min']:.1f} vs {A['per_min']:.1f}/min, change {-c_drop:+.0%} (heartbeat-caused needs a fall >= 60 %)")
    print(f"B rate vs A: {B['per_min']:.1f} vs {A['per_min']:.1f}/min, change {-b_drop:+.0%} (sampler-caused needs a fall >= 50 %)")
    within20 = abs(b_drop) <= 0.20 and abs(c_drop) <= 0.20
    if hb_aligned and c_drop >= 0.60:
        verdict = "HEARTBEAT-CAUSED"
    elif b_drop >= 0.50 and not hb_aligned:
        verdict = "SAMPLER-CAUSED"
    elif not hb_aligned and within20:
        verdict = "NEITHER (the path)"
    else:
        verdict = "NO PRE-REGISTERED OUTCOME MATCHES"
    print("verdict:", verdict)
    summary["verdict"] = verdict
json.dump(summary, open(os.path.join(HERE, "p8_summary.json"), "w"), indent=1)
