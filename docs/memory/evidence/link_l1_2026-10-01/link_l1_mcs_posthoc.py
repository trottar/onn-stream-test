#!/usr/bin/env python3
"""LINK-L1 -- POST HOC, not pre-registered: the share of each hold's T2 samples at which the Opal
sent to the onn at MCS 1, for the history holds (history.json) and the day's (score.json), against
loss/min. Descriptive only; nothing here enters the classification."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from link_l1_history import HOLDS, index_line  # noqa: E402


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def share(rows, t0, t1):
    w = [(x.get("opal") or {}).get("tx_mcs") for x in rows if t0 <= x.get("at_utc", "")[:19] + "Z" <= t1]
    w = [m for m in w if m is not None]
    return (100.0 * sum(1 for m in w if m == 1) / len(w), len(w)) if w else (None, 0)


def ranks(a):
    s = sorted(range(len(a)), key=lambda i: a[i]); r = [0.0] * len(a); i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and a[s[j + 1]] == a[s[i]]:
            j += 1
        for k in range(i, j + 1):
            r[s[k]] = (i + j) / 2.0
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = ranks(x), ranks(y); n = len(x); mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den


hist = {r["label"]: r for r in json.load(open(os.path.join(HERE, "history.json")))["rows"]}
cache, pts = {}, []
print("POST HOC -- MCS-1 share of T2 samples (Opal -> onn) against loss/min; descriptive, no rule")
for label, run_dir, name, t2f, _, _ in HOLDS:
    t0, t1, _ = index_line(run_dir, name)
    rows = cache.setdefault(t2f, jl(os.path.join(E, t2f)))
    s, n = share(rows, t0, t1)
    pts.append(("history", label, s, hist[label]["loss"]))
    print(f"  {label:<16} loss {hist[label]['loss']:6.2f}  MCS-1 share {s:5.1f}% (n {n})")
day = json.load(open(os.path.join(HERE, "score.json")))["rows"]
t2 = jl(os.path.join(HERE, "runs", "t2_samples.jsonl"))
for r in day:
    s, n = share(t2, r["start_utc"], r["end_utc"])
    pts.append(("day", r["hold"], s, r["loss"]))
    print(f"  day {r['hold']:<12} loss {r['loss']:6.2f}  MCS-1 share {s:5.1f}% (n {n})")
for name, sel in (("history (36)", [p for p in pts if p[0] == "history"]), ("the day (6)", [p for p in pts if p[0] == "day"]),
                  ("all (42)", pts)):
    x, y = [p[2] for p in sel], [p[3] for p in sel]
    hi = [p[3] for p in sel if p[2] >= 50]; lo = [p[3] for p in sel if p[2] < 50]
    print(f"{name}: Spearman rho {spearman(x, y):+.3f}; holds >= 50 % at MCS 1: {len(hi)}, meeting < 10: "
          f"{sum(1 for v in hi if v < 10)}; holds < 50 %: {len(lo)}, meeting: {sum(1 for v in lo if v < 10)}")
