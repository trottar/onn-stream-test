#!/usr/bin/env python3
"""LINK-L1 A1 -- every >= 15-minute hold on the adopted profile with adaptive off or silent since
D-BASE closed, from the records already on disk. Read-only. Descriptive: it does not enter the
classification (the pre-registration).

    link_l1_history.py [--json out.json]

Per hold: date, UTC start (PLAYING, from the run's index.txt), local hour (America/New_York; EDT,
UTC-4, for every date here), minutes, loss/min (post-FEC video lost_packets / min), max output gap,
spikes >= 20 ms / min, rendered fps (rendered_frames / duration), and from the run's T2 samples
inside [start, end]: the onn's link rate and RSSI (medians), the Opal's signal (median), the
Opal's tx retries per hold (last - first of the onn's station row) and the retry share of tx
packets. Channel utilization was not sampled in any of these runs (T2 does not read it; only O1,
before D-BASE closed, did).
"""
import json, os, re, statistics, sys
from datetime import datetime, timedelta, timezone

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # docs/memory/evidence
TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

# (label, run dir, hold name, t2 file relative to evidence/, adaptive note, APK)
OLD, NEW = "f31b1c18", "de072762"
HOLDS = [
    ("closeout C", "d_base_closeout_2026-09-23/runs", "C", "d_base_closeout_2026-09-23/t2_samples.jsonl", "off", OLD),
    ("closeout W", "d_base_closeout_2026-09-23/runs", "W", "d_base_closeout_2026-09-23/t2_samples.jsonl", "off", OLD),
    ("CTRL-L1 C", "ctrl_l1_2026-09-24/runs", "C", "ctrl_l1_2026-09-24/t2_samples.jsonl", "off", OLD),
    ("CTRL-L1 W1", "ctrl_l1_2026-09-24/runs", "W1", "ctrl_l1_2026-09-24/t2_samples.jsonl", "off", OLD),
    ("CTRL-L1 W2", "ctrl_l1_2026-09-24/runs", "W2", "ctrl_l1_2026-09-24/t2_samples.jsonl", "off", OLD),
    ("S1 H1", "c3_l4_s1_2026-09-24/runs", "H1", "c3_l4_s1_2026-09-24/t2_samples.jsonl", "shadow (silent)", OLD),
    ("S1 H2", "c3_l4_s1_2026-09-24/runs", "H2", "c3_l4_s1_2026-09-24/t2_samples.jsonl", "shadow (silent)", OLD),
    ("S1 H3 (60 min)", "c3_l4_s1_2026-09-24/runs", "H3", "c3_l4_s1_2026-09-24/t2_samples.jsonl", "shadow (silent)", OLD),
    ("S1 H4", "c3_l4_s1_2026-09-24/runs", "H4", "c3_l4_s1_2026-09-24/t2_samples.jsonl", "shadow (silent)", OLD),
    ("C4-M1 B1", "c4_m1_2026-09-25/runs", "B1", "c4_m1_2026-09-25/t2_samples.jsonl", "off", OLD),
    ("C4-M1 B2", "c4_m1_2026-09-25/runs", "B2", "c4_m1_2026-09-25/t2_samples.jsonl", "off", OLD),
    ("C4-M1 B3", "c4_m1_2026-09-25/runs", "B3", "c4_m1_2026-09-25/t2_samples.jsonl", "off", OLD),
    ("L1 A (30 min)", "c3_l4_l1_2026-09-28/runs", "A", "c3_l4_l1_2026-09-28/t2_samples.jsonl", "live (silent)", OLD),
    ("C5-M1 B1", "c5_m1_2026-09-28/runs", "B1", "c5_m1_2026-09-28/t2_samples.jsonl", "off", OLD),
    ("C5-M1 B2", "c5_m1_2026-09-28/runs", "B2", "c5_m1_2026-09-28/t2_samples.jsonl", "off", OLD),
    ("C5-M1 B3", "c5_m1_2026-09-28/runs", "B3", "c5_m1_2026-09-28/t2_samples.jsonl", "off", OLD),
    ("N1 H (30 min)", "c3_l4_n1_2026-09-29/runs", "H", "c3_l4_n1_2026-09-29/t2_samples.jsonl", "live (silent)", OLD),
    ("N2 H (30 min)", "c3_l4_n2_2026-09-29/runs", "H", "c3_l4_n2_2026-09-29/t2_samples.jsonl", "live (silent)", OLD),
    ("C5-M2 n1 B1", "c5_m2_2026-09-29/runs_n1", "B1", "c5_m2_2026-09-29/runs_n1/t2_samples.jsonl", "off", OLD),
    ("C5-M2 n1 B2", "c5_m2_2026-09-29/runs_n1", "B2", "c5_m2_2026-09-29/runs_n1/t2_samples.jsonl", "off", OLD),
    ("C5-M2 n1 B3", "c5_m2_2026-09-29/runs_n1", "B3", "c5_m2_2026-09-29/runs_n1/t2_samples.jsonl", "off", OLD),
    ("C5-M2 n1 B4", "c5_m2_2026-09-29/runs_n1", "B4", "c5_m2_2026-09-29/runs_n1/t2_samples.jsonl", "off", OLD),
    ("C5-M2 n1r B1", "c5_m2_2026-09-29/runs_n1r", "B1", "c5_m2_2026-09-29/runs_n1r/t2_samples.jsonl", "off", OLD),
    ("C5-M2 n1r B2", "c5_m2_2026-09-29/runs_n1r", "B2", "c5_m2_2026-09-29/runs_n1r/t2_samples.jsonl", "off", OLD),
    ("C5-M2 n1r B3", "c5_m2_2026-09-29/runs_n1r", "B3", "c5_m2_2026-09-29/runs_n1r/t2_samples.jsonl", "off", OLD),
    ("C5-M2 n1r B4", "c5_m2_2026-09-29/runs_n1r", "B4", "c5_m2_2026-09-29/runs_n1r/t2_samples.jsonl", "off", OLD),
    ("C5-M3 B1", "c5_m3_2026-09-29/runs", "B1", "c5_m3_2026-09-29/runs/t2_samples.jsonl", "off", OLD),
    ("C5-M3 B2", "c5_m3_2026-09-29/runs", "B2", "c5_m3_2026-09-29/runs/t2_samples.jsonl", "off", OLD),
    ("C5-M3 B3", "c5_m3_2026-09-29/runs", "B3", "c5_m3_2026-09-29/runs/t2_samples.jsonl", "off", OLD),
    ("C5-M3 B4", "c5_m3_2026-09-29/runs", "B4", "c5_m3_2026-09-29/runs/t2_samples.jsonl", "off", OLD),
    ("C5-M3 rerun B1", "c5_m3_2026-09-29/runs_rerun", "B1", "c5_m3_2026-09-29/runs_rerun/t2_samples.jsonl", "off", OLD),
    ("C5-M3 rerun B2", "c5_m3_2026-09-29/runs_rerun", "B2", "c5_m3_2026-09-29/runs_rerun/t2_samples.jsonl", "off", OLD),
    ("C5-M3 rerun B3", "c5_m3_2026-09-29/runs_rerun", "B3", "c5_m3_2026-09-29/runs_rerun/t2_samples.jsonl", "off", OLD),
    ("C5-M3 rerun B4", "c5_m3_2026-09-29/runs_rerun", "B4", "c5_m3_2026-09-29/runs_rerun/t2_samples.jsonl", "off", OLD),
    ("CL-B1 N1", "cl_b1_apk_2026-09-30/runs", "N1", "cl_b1_apk_2026-09-30/runs/t2_samples.jsonl", "off", NEW),
    ("CL-B1 O1", "cl_b1_apk_2026-09-30/runs_old", "O1", "cl_b1_apk_2026-09-30/runs_old/t2_samples.jsonl", "off", OLD),
]
EXCLUDED = [
    ("L1 B", "injection session: the controller acted (7000 -> 5000)"),
    ("L2 B2", "injection session: the controller acted (the climb 5000 -> 7000)"),
    ("C3.L3a R2/R3/R4 sessions", "the probe's bitrate transitions during the session"),
    ("C3-L4 nft nights 1-3", "injected faults"),
    ("C4-M1 A1-A3, C5-M1 A1-A3, C5-M2 C1-C3, C5-M3 L3/L4/S5", "non-adopted arms (FEC scheme / 1080p / low rungs)"),
    ("D-BASE P9/P9a/T2/T3 (2026-09-23 before 22:31Z), D-BASE-S3 (2026-09-22)", "before D-BASE closed / before the adopted cushion and redundancy"),
]


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def med(a):
    a = [x for x in a if x is not None]
    return statistics.median(a) if a else None


def index_line(run_dir, name):
    for line in open(os.path.join(E, run_dir, "index.txt")):
        f = line.split()
        if f and f[0] == name:
            ts = TS.findall(line)
            rep = [x for x in f if x.startswith("native_decoder_")]
            return ts[0], ts[1], (rep[0] if rep else None)
    raise KeyError(name)


def local(utc):
    t = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return t + timedelta(hours=-4)          # EDT for every date in this table and the day


def score(report_path):
    rep = json.load(open(report_path))["report"]
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    s = rep["duration_ms"] / 1000.0
    m = s / 60.0
    return dict(minutes=m, loss=v["lost_packets"] / m, maxgap=d["max_output_gap_ms"], spikes=d["spike_20_ms"] / m,
                fps=d["rendered_frames"] / s, stale=d["stale_output_drops"] / m, aund=(a.get("underruns") or 0) / m)


def t2(path, t0, t1):
    rows = [r for r in jl(os.path.join(E, path)) if t0 <= r.get("at_utc", "")[:19] + "Z" <= t1]
    onn = [r.get("onn") or {} for r in rows]
    op = [r.get("opal") or {} for r in rows if (r.get("opal") or {}).get("onn_row_found")]
    out = dict(n=len(rows), link=med([o.get("link_mbps") for o in onn]), rssi=med([o.get("rssi_dbm") for o in onn]),
               sig=med([o.get("signal_dbm") for o in op]), retries=None, retry_pct=None)
    rr = [(o.get("tx_retries"), o.get("tx_packets")) for o in op if o.get("tx_retries") is not None]
    if len(rr) >= 2 and rr[-1][0] >= rr[0][0]:
        dr, dp = rr[-1][0] - rr[0][0], (rr[-1][1] or 0) - (rr[0][1] or 0)
        out["retries"] = dr
        out["retry_pct"] = 100.0 * dr / dp if dp > 0 else None
    return out


def build(holds):
    rows = []
    for label, run_dir, name, t2f, mode, apk in holds:
        t0, t1, _ = index_line(run_dir, name)
        rp = os.path.join(E, run_dir, f"report_{name}.json")
        r = dict(label=label, run_dir=run_dir, hold=name, adaptive=mode, apk=apk, start_utc=t0, end_utc=t1,
                 local=local(t0).strftime("%Y-%m-%d %H:%M"), local_hour=local(t0).hour,
                 date=local(t0).strftime("%Y-%m-%d"))
        r.update(score(rp))
        r.update({"t2_" + k: v for k, v in t2(t2f, t0, t1).items()})
        rows.append(r)
    return rows


def f(x, s):
    return "-" if x is None else format(x, s)


def table(rows, title):
    print(title)
    print(f"{'hold':<16} {'local start':<16} {'UTC start':<20} {'h':>2} {'min':>5} {'loss/m':>7} {'gap':>4} "
          f"{'spk/m':>6} {'fps':>6} {'adaptive':<15} {'apk':<8} | {'link':>4} {'rssi':>4} {'opal sig':>8} "
          f"{'retries':>9} {'retry%':>6} {'t2 n':>4}")
    for r in rows:
        print(f"{r['label']:<16} {r['local']:<16} {r['start_utc']:<20} {r['local_hour']:>2} {r['minutes']:5.1f} "
              f"{r['loss']:7.2f} {r['maxgap']:>4} {r['spikes']:6.1f} {r['fps']:6.2f} {r['adaptive']:<15} {r['apk']:<8} | "
              f"{f(r['t2_link'], '.0f'):>4} {f(r['t2_rssi'], '.0f'):>4} {f(r['t2_sig'], '.0f'):>8} "
              f"{f(r['t2_retries'], ',.0f'):>9} {f(r['t2_retry_pct'], '.1f'):>6} {r['t2_n']:>4}")


def buckets(rows, key, title):
    print(title)
    groups = {}
    for r in rows:
        groups.setdefault(key(r), []).append(r["loss"])
    for k in sorted(groups):
        a = groups[k]
        meets = sum(1 for x in a if x < 10)
        print(f"  {k:<14} n {len(a):>2}  median {statistics.median(a):6.2f}  min {min(a):6.2f}  max {max(a):6.2f}"
              f"  meets < 10: {meets}/{len(a)}")
    return {k: dict(n=len(v), median=statistics.median(v), min=min(v), max=max(v),
                    meets=sum(1 for x in v if x < 10)) for k, v in groups.items()}


def block(h):
    b = (h // 4) * 4
    return f"{b:02d}-{b + 4:02d}"


def main():
    rows = build(HOLDS)
    table(rows, "A1 -- every >= 15-min hold on the adopted profile, adaptive off or silent, since D-BASE closed")
    print()
    bb = buckets(rows, lambda r: block(r["local_hour"]), "loss/min by local 4-hour block (EDT)")
    print()
    bd = buckets(rows, lambda r: r["date"], "loss/min by local date")
    print()
    print("Excluded (not adaptive-off-or-silent on the adopted profile, or before the close):")
    for a, b in EXCLUDED:
        print(f"  {a}: {b}")
    print("Channel utilization: not sampled in any of these runs (T2 does not read it).")
    if "--json" in sys.argv:
        json.dump({"rows": rows, "by_block": bb, "by_date": bd, "excluded": EXCLUDED},
                  open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)


if __name__ == "__main__":
    main()
