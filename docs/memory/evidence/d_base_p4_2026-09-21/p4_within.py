#!/usr/bin/env python3
"""D-BASE-P4: inside the 20-minute session.

The client's heartbeat carries rx_packets every ~2 s with its own timestamp,
so its per-tick receive RATE is precise (unlike the counter-difference loss
series, which the interpolation noise destroys). A loss episode shows up as a
dip in that rate. Each tick is then matched to the nearest row of the onn's
own 3 s radio ring.
"""
import json, os, statistics as st
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LABEL = "L20"


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def rank(xs):
    o = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0]*len(xs); i = 0
    while i < len(o):
        j = i
        while j+1 < len(o) and xs[o[j+1]] == xs[o[i]]:
            j += 1
        for k in range(i, j+1):
            r[o[k]] = (i+j)/2.0 + 1
        i = j+1
    return r


def spearman(a, b):
    p = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(p) < 4:
        return None, len(p)
    xs, ys = rank([q[0] for q in p]), rank([q[1] for q in p])
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    num = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    dx = sum((x-mx)**2 for x in xs)**.5; dy = sum((y-my)**2 for y in ys)**.5
    return (num/(dx*dy) if dx and dy else None), n


for line in open(f"{HERE}/index.txt"):
    lab, hold, report, t0, t1 = line.split()
    if lab == LABEL:
        break
T0, T1 = ts(t0), ts(t1)

hb = sorted((ts(x["received_at_utc"]), x["rx_packets"], x.get("last_output_age_ms"))
            for x in (json.loads(l) for l in open(f"{HERE}/heartbeat_{LABEL}.jsonl")))
hb = [h for h in hb if T0 <= h[0] <= T1]

h = json.load(open(f"{HERE}/air_harvest_{LABEL}.json"))
ring = sorted((ts(r["at_utc"]), r) for r in h["score_report_rows"]
              if r["at_utc"] and T0 <= ts(r["at_utc"]) <= T1)


def radio_at(t):
    if not ring:
        return None
    best = min(ring, key=lambda r: abs((r[0]-t).total_seconds()))
    return best[1] if abs((best[0]-t).total_seconds()) <= 4 else None


ticks = []
for (ta, va, _), (tb, vb, age) in zip(hb, hb[1:]):
    dt = (tb-ta).total_seconds()
    if dt <= 0:
        continue
    rate = (vb-va)/dt
    r = radio_at(tb)
    ticks.append(dict(t=tb, rate=rate, age=age,
                      rssi=float(r["rssi"]) if r else None,
                      tx=float(r["txLinkSpeed"]) if r else None,
                      rx=float(r["rxLinkSpeed"]) if r else None))

rates = [x["rate"] for x in ticks]
med = st.median(rates)
print(f"===== {LABEL}: {len(ticks)} heartbeat ticks over {(T1-T0).total_seconds():.0f} s =====")
print(f"receive rate packets/s: median {med:.0f}  min {min(rates):.0f}  max {max(rates):.0f}")
print(f"  p05 {sorted(rates)[len(rates)//20]:.0f}   p95 {sorted(rates)[-len(rates)//20]:.0f}")

# a dip is a tick whose rate falls well below the session median
DIP = 0.90
dips = [x for x in ticks if x["rate"] < med*DIP]
print(f"\nticks below {DIP:.0%} of median rate: {len(dips)} of {len(ticks)} "
      f"({100*len(dips)/len(ticks):.1f} %)")
print(f"  {'utc':<10}{'pkt/s':>8}{'vs med':>8}{'rssi':>6}{'tx':>6}{'rx':>6}{'out_age_ms':>11}")
for x in sorted(dips, key=lambda d: d["rate"])[:20]:
    print(f"  {x['t'].strftime('%H:%M:%S'):<10}{x['rate']:>8.0f}"
          f"{100*x['rate']/med-100:>7.0f}%"
          + ("-" if x["rssi"] is None else f"{x['rssi']:>6.0f}")
          + ("-" if x["tx"] is None else f"{x['tx']:>6.0f}")
          + ("-" if x["rx"] is None else f"{x['rx']:>6.0f}")
          + (f"{x['age']:>11}" if x["age"] is not None else f"{'-':>11}"))

print(f"\n===== Spearman at heartbeat resolution (n up to {len(ticks)}) =====")
for k, name in (("rssi", "receive rate vs rssi"),
                ("tx", "receive rate vs txLinkSpeed"),
                ("rx", "receive rate vs rxLinkSpeed")):
    rho, n = spearman(rates, [x[k] for x in ticks])
    flag = "   <-- |rho| >= 0.5" if rho is not None and abs(rho) >= 0.5 else ""
    print(f"  {name:<34} rho={'None' if rho is None else f'{rho:+.3f}'} n={n}{flag}")

print("\n===== per-minute receive rate, whole session =====")
buckets = {}
for x in ticks:
    m = int((x["t"]-T0).total_seconds()//60)
    buckets.setdefault(m, []).append(x)
print(f"  {'min':>4}{'pkt/s med':>11}{'min':>8}{'dips':>6}{'rssi med':>10}{'tx med':>8}")
for m in sorted(buckets):
    b = buckets[m]
    rr = [y["rate"] for y in b]
    rs = [y["rssi"] for y in b if y["rssi"] is not None]
    tt = [y["tx"] for y in b if y["tx"] is not None]
    print(f"  {m:>4}{st.median(rr):>11.0f}{min(rr):>8.0f}"
          f"{sum(1 for y in b if y['rate'] < med*DIP):>6}"
          + (f"{st.median(rs):>10.0f}" if rs else f"{'-':>10}")
          + (f"{st.median(tt):>8.0f}" if tt else f"{'-':>8}"))
