#!/usr/bin/env python3
"""LINK-L2 -- score the day's holds by the close-out table and classify the day by LINK-L1's rule,
pre-registered verbatim (link_l2_preregistration.txt). Read-only. Derived from link_l1_score.py:
the rows, the targets, shortest_arc / in_arc / classify are LINK-L1's unchanged. Added: excluded holds
(index "H<k> EXCLUDED", link_l2_valid.py) are dropped and their re-run H<k>r scores for block k; the
frame-size columns (C5-M4's formulas) for both days; the decision log's events per hold; the
side-by-side with LINK-L1 by local 4-hour block.

    link_l2_score.py [--runs <dir>] [--json out.json]
"""
import json, os, re, statistics, sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
R = sys.argv[sys.argv.index("--runs") + 1] if "--runs" in sys.argv else os.path.join(HERE, "runs")
L1 = os.path.join(HERE, "..", "link_l1_2026-10-01")
TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
ROWS = [("spikes", "spikes >= 20 ms / min", lambda x: x < 200, "< 200"),
        ("fps", "rendered fps", lambda x: x >= 59.5, ">= 59.5"),
        ("stale", "stale drops / min", lambda x: x < 20, "< 20"),
        ("loss", "video loss / min post-FEC", lambda x: x < 10, "< 10"),
        ("aund", "audio underruns / min", lambda x: x < 5, "< 5"),
        ("maxgap", "max output gap ms", lambda x: x <= 100, "<= 100")]


def jl(p):
    out = []
    if os.path.exists(p):
        for l in open(p, errors="replace"):
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


def med(a):
    a = [x for x in a if x is not None]
    return statistics.median(a) if a else None


def mean(a):
    a = [x for x in a if x is not None]
    return sum(a) / len(a) if a else None


def pct(a, q):
    a = sorted(x for x in a if x is not None)
    return a[min(len(a) - 1, int(round(q * (len(a) - 1))))] if a else None


def local(utc):
    return datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) + timedelta(hours=-4)


def block(hour):
    b = int(hour) // 4 * 4
    return f"{b:02d}-{b + 4:02d}"


def holds(rdir):
    idx, notrun, excl = {}, [], []
    for line in open(os.path.join(rdir, "index.txt")):
        f = line.split()
        if len(f) >= 2 and f[1] == "H":
            ts = TS.findall(line)
            idx[f[0]] = (ts[0], ts[1])
        elif len(f) >= 2 and f[1] == "NOT_RUN":
            notrun.append(f[0])
        elif len(f) >= 2 and f[1] == "EXCLUDED":
            excl.append(f[0])
    return idx, notrun, excl


def frames(rdir, h):
    """C5-M4's client() frame-size formulas (c5_m4_host_table.py), per hold."""
    rep = json.load(open(os.path.join(rdir, f"report_{h}.json")))["report"]
    m = rep["duration_ms"] / 60000.0
    cap = (json.load(open(os.path.join(rdir, f"armcheck_{h}.json"))).get("encoder_overrides") or {}).get("max_frame_size_bytes")
    fr = jl(os.path.join(rdir, f"frames_{h}.jsonl"))
    mx = [r.get("max_bytes", 0) for r in fr if r.get("frames")]
    return dict(frmax_p50=pct(mx, .5), frmax_p90=pct(mx, .9), frmax_max=max(mx) if mx else None,
                caphit_s_min=round(sum(1 for x in mx if cap and x >= 0.95 * cap) / m, 1) if cap else None,
                ge80_min=round(sum(r.get("frames_ge_80", 0) for r in fr) / m, 2), frame_seconds=len(fr))


def score_hold(rdir, h, t0, t1, t2, air):
    rep = json.load(open(os.path.join(rdir, f"report_{h}.json")))["report"]
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    s = rep["duration_ms"] / 1000.0
    m = s / 60.0
    r = dict(hold=h, block_hold=h.rstrip("r"), start_utc=t0, end_utc=t1, local=local(t0).strftime("%Y-%m-%d %H:%M"),
             local_hour=local(t0).hour + local(t0).minute / 60.0, minutes=m,
             spikes=d["spike_20_ms"] / m, fps=d["rendered_frames"] / s, stale=d["stale_output_drops"] / m,
             loss=v["lost_packets"] / m, aund=(a.get("underruns") or 0) / m, maxgap=d["max_output_gap_ms"],
             fec_recovered_per_min=(v.get("fec_recovered_packets") or 0) / m)
    r["block"] = block(r["local_hour"])
    ac = json.load(open(os.path.join(rdir, f"armcheck_{h}.json")))
    r["any_override"] = (ac.get("encoder_overrides") or {}).get("any_override")
    r["adaptive_mode"] = (ac.get("adaptive_bitrate") or {}).get("mode")
    ad = os.path.join(rdir, f"abr_after_disable_{h}.json")
    r["adaptive_after_disable"] = (json.load(open(ad)).get("adaptive_bitrate") or {}).get("mode") if os.path.exists(ad) else None
    r["profile_id"], r["bitrate_kbps"] = ac.get("profile_id"), ac.get("bitrate_kbps")
    cap = ac.get("capture_target") or {}
    r["capture"] = f"{cap.get('width')}x{cap.get('height')}" if cap else None
    w = [x for x in t2 if t0 <= x.get("at_utc", "")[:19] + "Z" <= t1]
    onn = [x.get("onn") or {} for x in w]
    op = [x.get("opal") or {} for x in w if (x.get("opal") or {}).get("onn_row_found")]
    mcs = [o.get("tx_mcs") for o in op if o.get("tx_mcs") is not None]
    r.update(t2_n=len(w), link_mbps=med([o.get("link_mbps") for o in onn]), rssi_dbm=med([o.get("rssi_dbm") for o in onn]),
             opal_signal_dbm=med([o.get("signal_dbm") for o in op]), tx_mcs=med(mcs),
             mcs1_share_pct=round(100.0 * sum(1 for x in mcs if x <= 1) / len(mcs)) if mcs else None,
             tx_retries=None, retry_pct=None)
    rr = [(o["tx_retries"], o.get("tx_packets") or 0) for o in op if o.get("tx_retries") is not None]
    if len(rr) >= 2 and rr[-1][0] >= rr[0][0]:
        r["tx_retries"] = rr[-1][0] - rr[0][0]
        dp = rr[-1][1] - rr[0][1]
        r["retry_pct"] = 100.0 * r["tx_retries"] / dp if dp > 0 else None
    aw = [x for x in air if x.get("label") == h and not x.get("error") and t0 <= x.get("at_utc", "") <= t1]
    r.update(air_n=len(aw), util_mean_pct=mean([x.get("channel_utilization_pct") for x in aw]),
             util_max_pct=max([x.get("channel_utilization_pct") or 0 for x in aw]) if aw else None,
             noise_dbm=med([x.get("noise_dbm") for x in aw]),
             air_tx_mcs=med([x.get("tx_mcs") for x in aw if x.get("onn_row_found")]),
             air_tx_rate=med([x.get("tx_bitrate_mbps") for x in aw if x.get("onn_row_found")]),
             air_width=med([x.get("width_mhz") for x in aw]))
    r.update(frames(rdir, h))
    ev = {}
    for x in jl(os.path.join(rdir, f"decision_log_{h}.jsonl")):
        if x.get("event") != "sample":
            ev[x.get("event")] = ev.get(x.get("event"), 0) + 1
    r["abr_events"] = ev
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


def day(rdir, air_path):
    idx, notrun, excl = holds(rdir)
    t2 = jl(os.path.join(rdir, "t2_samples.jsonl"))
    air = jl(air_path)
    names = [h for h in sorted(idx) if h not in excl and os.path.exists(os.path.join(rdir, f"report_{h}.json"))]
    return [score_hold(rdir, h, *idx[h], t2, air) for h in names], notrun, excl


F = lambda x, s: "-" if x is None else format(x, s)  # noqa: E731


def main():
    rows, notrun, excl = day(R, os.path.join(HERE, "air_loop.jsonl"))
    l1, _, _ = day(os.path.join(L1, "runs"), os.path.join(L1, "air_loop.jsonl"))
    out = ["LINK-L2 -- the day's holds on the 40 MHz link, adopted profile at 7000, 4x PS1 source, adaptive shadow "
           "(close-out targets)",
           f"{'hold':<4} {'local start':<16} {'UTC start':<20} {'min':>5} {'spk/m':>6} {'fps':>6} {'stale':>5} "
           f"{'loss/m':>7} {'aund/m':>6} {'gap':>4} | {'link':>4} {'rssi':>4} {'sig':>4} {'mcs':>3} {'mcs<=1%':>7} {'retries':>8} "
           f"{'ret%':>5} {'util%':>5} {'umax':>5} {'noise':>5} {'wid':>3} | mode->after ovr capture"]
    for r in rows:
        out.append(f"{r['hold']:<4} {r['local']:<16} {r['start_utc']:<20} {r['minutes']:5.2f} {r['spikes']:6.1f} {r['fps']:6.2f} "
                   f"{r['stale']:5.2f} {r['loss']:7.2f} {r['aund']:6.2f} {r['maxgap']:>4} | {F(r['link_mbps'], '.0f'):>4} "
                   f"{F(r['rssi_dbm'], '.0f'):>4} {F(r['opal_signal_dbm'], '.0f'):>4} {F(r['tx_mcs'], '.0f'):>3} "
                   f"{F(r['mcs1_share_pct'], '.0f'):>7} {F(r['tx_retries'], ',.0f'):>8} {F(r['retry_pct'], '.1f'):>5} "
                   f"{F(r['util_mean_pct'], '.2f'):>5} {F(r['util_max_pct'], '.1f'):>5} {F(r['noise_dbm'], '.0f'):>5} "
                   f"{F(r['air_width'], '.0f'):>3} | {r['adaptive_mode']}->{r['adaptive_after_disable']} {r['any_override']} {r['capture']}")
    out.append("")
    for r in rows:
        out.append(f"  {r['hold']}: loss {'MEETS' if r['loss_meets'] else 'MISSES'} ({r['loss']:.2f}/min); "
                   f"{'all rows met' if not r['misses'] else 'misses: ' + '; '.join(r['misses'])}")
    for h in excl:
        out.append(f"  {h}: EXCLUDED (the shadow clause; see validity.txt)")
    for h in notrun:
        out.append(f"  {h}: NOT RUN")
    cls, why = classify(rows)
    out.append(f"\nCLASSIFICATION OF THE DAY: {cls} -- {why}")
    out += ["", "FRAME SIZE (reported; C5-M4's formulas): per-second largest frame p50/p90/max B, cap hits s/min, >= 80-pkt frames/min",
            f"{'day':<5} {'hold':<4} {'block':<6} {'p50':>6} {'p90':>6} {'max':>6} {'cap s/m':>7} {'ge80/m':>6}"]
    for tag, rs in (("L1 1x", l1), ("L2 4x", rows)):
        for r in rs:
            out.append(f"{tag:<5} {r['hold']:<4} {r['block']:<6} {F(r['frmax_p50'], ''):>6} {F(r['frmax_p90'], ''):>6} "
                       f"{F(r['frmax_max'], ''):>6} {F(r['caphit_s_min'], ''):>7} {F(r['ge80_min'], ''):>6}")
        out.append(f"{tag:<5} {'med':<4} {'':<6} {F(med([r['frmax_p50'] for r in rs]), '.0f'):>6} "
                   f"{F(med([r['frmax_p90'] for r in rs]), '.0f'):>6} {'':>6} {F(med([r['caphit_s_min'] for r in rs]), '.1f'):>7} "
                   f"{F(med([r['ge80_min'] for r in rs]), '.2f'):>6}")
    out += ["", "SIDE BY SIDE by local 4-hour block (reported; the classification is LINK-L2's alone)",
            f"{'block':<6} | {'L1 hold':<7} {'loss/m':>7} {'gap':>4} {'retries':>8} {'ret%':>5} {'link':>4} {'mcs':>3} {'mcs<=1%':>7} | "
            f"{'L2 hold':<7} {'loss/m':>7} {'gap':>4} {'retries':>8} {'ret%':>5} {'link':>4} {'mcs':>3} {'mcs<=1%':>7}"]
    by1 = {r["block"]: r for r in l1}
    by2 = {r["block"]: r for r in rows}

    def cell(r):
        if not r:
            return f"{'-':<7} {'-':>7} {'-':>4} {'-':>8} {'-':>5} {'-':>4} {'-':>3} {'-':>7}"
        return (f"{r['hold'] + ' ' + r['local'][11:]:<7} {r['loss']:7.2f} {r['maxgap']:>4} {F(r['tx_retries'], ',.0f'):>8} "
                f"{F(r['retry_pct'], '.1f'):>5} {F(r['link_mbps'], '.0f'):>4} {F(r['tx_mcs'], '.0f'):>3} {F(r['mcs1_share_pct'], '.0f'):>7}")
    for b in ["00-04", "04-08", "08-12", "12-16", "16-20", "20-24"]:
        out.append(f"{b:<6} | {cell(by1.get(b))} | {cell(by2.get(b))}")
    for tag, rs in (("L1", l1), ("L2", rows)):
        out.append(f"{tag}: meets {sum(r['loss_meets'] for r in rs)}/{len(rs)}; loss median {F(med([r['loss'] for r in rs]), '.2f')}; "
                   f"max gap median {F(med([r['maxgap'] for r in rs]), '.0f')}, <= 100 on {sum(r['maxgap'] <= 100 for r in rs)}; "
                   f"retries median {F(med([r['tx_retries'] for r in rs]), ',.0f')}; link median {F(med([r['link_mbps'] for r in rs]), '.0f')}")
    out += ["", "DECISION LOG per hold (non-sample events; the shadow's would-be decisions)"]
    for r in rows:
        out.append(f"  {r['hold']}: {json.dumps(r['abr_events'])}")
    text = "\n".join(out) + "\n"
    print(text)
    if "--json" in sys.argv:
        json.dump({"classification": cls, "why": why, "rows": rows, "not_run": notrun, "excluded": excl, "link_l1_rows": l1},
                  open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)


if __name__ == "__main__":
    main()
