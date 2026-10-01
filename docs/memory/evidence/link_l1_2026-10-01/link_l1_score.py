#!/usr/bin/env python3
"""LINK-L1 A3/A4 -- score the day's holds by the close-out table and classify the day by the
pre-registered rule (link_l1_preregistration.txt). Read-only.

    link_l1_score.py [--json out.json]

Rows per hold (close-out targets): spikes/min < 200, rendered fps >= 59.5, stale/min < 20,
video loss/min post-FEC < 10 (the classifying row), audio underruns/min < 5, max output gap
<= 100 ms (reported). Beside them: T2 (onn link / RSSI, the Opal's signal, tx retries per hold and
retry share) and the air loop (channel utilization mean, noise) inside the hold's window.
"""
import json, os, re, statistics, sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")
TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
ROWS = [("spikes", "spikes >= 20 ms / min", lambda x: x < 200, "< 200"),
        ("fps", "rendered fps", lambda x: x >= 59.5, ">= 59.5"),
        ("stale", "stale drops / min", lambda x: x < 20, "< 20"),
        ("loss", "video loss / min post-FEC", lambda x: x < 10, "< 10"),
        ("aund", "audio underruns / min", lambda x: x < 5, "< 5"),
        ("maxgap", "max output gap ms", lambda x: x <= 100, "<= 100")]


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def med(a):
    a = [x for x in a if x is not None]
    return statistics.median(a) if a else None


def mean(a):
    a = [x for x in a if x is not None]
    return sum(a) / len(a) if a else None


def local(utc):
    return datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) + timedelta(hours=-4)


def holds():
    idx, notrun = {}, []
    for line in open(os.path.join(R, "index.txt")):
        f = line.split()
        if len(f) >= 2 and f[1] == "H":
            ts = TS.findall(line)
            idx[f[0]] = (ts[0], ts[1])
        elif len(f) >= 2 and f[1] == "NOT_RUN":
            notrun.append(f[0])
    return idx, notrun


def score_hold(h, t0, t1, t2, air):
    rep = json.load(open(os.path.join(R, f"report_{h}.json")))["report"]
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    s = rep["duration_ms"] / 1000.0
    m = s / 60.0
    r = dict(hold=h, start_utc=t0, end_utc=t1, local=local(t0).strftime("%Y-%m-%d %H:%M"),
             local_hour=local(t0).hour + local(t0).minute / 60.0, minutes=m,
             spikes=d["spike_20_ms"] / m, fps=d["rendered_frames"] / s, stale=d["stale_output_drops"] / m,
             loss=v["lost_packets"] / m, aund=(a.get("underruns") or 0) / m, maxgap=d["max_output_gap_ms"],
             fec_recovered_per_min=(v.get("fec_recovered_packets") or 0) / m)
    ac = json.load(open(os.path.join(R, f"armcheck_{h}.json")))
    r["any_override"] = (ac.get("encoder_overrides") or {}).get("any_override")
    r["adaptive_mode"] = (ac.get("adaptive_bitrate") or {}).get("mode")
    r["profile_id"], r["bitrate_kbps"] = ac.get("profile_id"), ac.get("bitrate_kbps")
    w = [x for x in t2 if t0 <= x.get("at_utc", "")[:19] + "Z" <= t1]
    onn = [x.get("onn") or {} for x in w]
    op = [x.get("opal") or {} for x in w if (x.get("opal") or {}).get("onn_row_found")]
    r.update(t2_n=len(w), link_mbps=med([o.get("link_mbps") for o in onn]), rssi_dbm=med([o.get("rssi_dbm") for o in onn]),
             opal_signal_dbm=med([o.get("signal_dbm") for o in op]), tx_mcs=med([o.get("tx_mcs") for o in op]),
             tx_retries=None, retry_pct=None)
    rr = [(o["tx_retries"], o.get("tx_packets") or 0) for o in op if o.get("tx_retries") is not None]
    if len(rr) >= 2 and rr[-1][0] >= rr[0][0]:
        r["tx_retries"] = rr[-1][0] - rr[0][0]
        dp = rr[-1][1] - rr[0][1]
        r["retry_pct"] = 100.0 * r["tx_retries"] / dp if dp > 0 else None
    aw = [x for x in air if x.get("label") == h and not x.get("error") and t0 <= x.get("at_utc", "") <= t1]
    r.update(air_n=len(aw), util_mean_pct=mean([x.get("channel_utilization_pct") for x in aw]),
             util_max_pct=max([x.get("channel_utilization_pct") or 0 for x in aw]) if aw else None,
             noise_dbm=med([x.get("noise_dbm") for x in aw]))
    r["meets"] = [name for k, name, ok, _ in ROWS if ok(r[k])]
    r["misses"] = [f"{name} {round(r[k], 2)} vs {t}" for k, name, ok, t in ROWS if not ok(r[k])]
    r["loss_meets"] = r["loss"] < 10
    return r


def shortest_arc(hours):
    """The shortest circular arc (start, length) of the 24 h clock containing every hour given."""
    hs = sorted(x % 24 for x in hours)
    if len(hs) == 1:
        return hs[0], 0.0
    gaps = [((hs[(i + 1) % len(hs)] - hs[i]) % 24, i) for i in range(len(hs))]
    g, i = max(gaps)
    start = hs[(i + 1) % len(hs)]
    return start, 24 - g


def in_arc(h, start, length):
    return (h - start) % 24 <= length + 1e-9


def classify(rows):
    n = len(rows)
    meets = [r for r in rows if r["loss_meets"]]
    misses = [r for r in rows if not r["loss_meets"]]
    if len(meets) >= 5:
        return "STILL MET", f"{len(meets)} of {n} holds meet loss < 10/min"
    if len(meets) >= 2 and len(misses) >= 2:
        s, L = shortest_arc([r["local_hour"] for r in misses])
        clean = L <= 12 and not any(in_arc(r["local_hour"], s, L) for r in meets)
        if clean:
            return "TIME OF DAY", (f"misses {[r['hold'] for r in misses]} inside {s % 24:05.2f} + {L:.2f} h "
                                   f"(local), every meet outside it")
    if n >= 5 and len(meets) <= 1:
        return "MOVED", f"{len(meets)} of {n} holds meet"
    if n < 5:
        return "INCOMPLETE", f"{n} holds scored, no rule met"
    return "MIXED", f"{len(meets)} of {n} meet; misses not separable by a <= 12 h window"


def main():
    idx, notrun = holds()
    t2 = jl(os.path.join(R, "t2_samples.jsonl"))
    air = jl(os.path.join(HERE, "air_loop.jsonl"))
    rows = [score_hold(h, *idx[h], t2, air) for h in sorted(idx) if os.path.exists(os.path.join(R, f"report_{h}.json"))]
    print("LINK-L1 -- the day's holds, adopted profile at 7000, adaptive off (close-out targets)")
    print(f"{'hold':<4} {'local start':<16} {'UTC start':<20} {'min':>5} {'spk/m':>6} {'fps':>6} {'stale':>5} "
          f"{'loss/m':>7} {'aund/m':>6} {'gap':>4} | {'link':>4} {'rssi':>4} {'sig':>4} {'mcs':>3} {'retries':>8} "
          f"{'ret%':>5} {'util%':>5} {'umax':>5} {'noise':>5} | mode ovr")
    f = lambda x, s: "-" if x is None else format(x, s)  # noqa: E731
    for r in rows:
        print(f"{r['hold']:<4} {r['local']:<16} {r['start_utc']:<20} {r['minutes']:5.2f} {r['spikes']:6.1f} {r['fps']:6.2f} "
              f"{r['stale']:5.2f} {r['loss']:7.2f} {r['aund']:6.2f} {r['maxgap']:>4} | {f(r['link_mbps'], '.0f'):>4} "
              f"{f(r['rssi_dbm'], '.0f'):>4} {f(r['opal_signal_dbm'], '.0f'):>4} {f(r['tx_mcs'], '.0f'):>3} "
              f"{f(r['tx_retries'], ',.0f'):>8} {f(r['retry_pct'], '.1f'):>5} {f(r['util_mean_pct'], '.2f'):>5} "
              f"{f(r['util_max_pct'], '.1f'):>5} {f(r['noise_dbm'], '.0f'):>5} | {r['adaptive_mode']} {r['any_override']}")
    print()
    for r in rows:
        print(f"  {r['hold']}: loss {'MEETS' if r['loss_meets'] else 'MISSES'} ({r['loss']:.2f}/min); "
              f"{'all rows met' if not r['misses'] else 'misses: ' + '; '.join(r['misses'])}")
    for h in notrun:
        print(f"  {h}: NOT RUN")
    cls, why = classify(rows)
    print(f"\nCLASSIFICATION OF THE DAY: {cls} -- {why}")
    if "--json" in sys.argv:
        json.dump({"classification": cls, "why": why, "rows": rows, "not_run": notrun},
                  open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)


if __name__ == "__main__":
    main()
