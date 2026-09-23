#!/usr/bin/env python3
"""D-BASE-T2, EXPLORATORY (written after the pre-registered reading came out
MIXED; not a pre-registered test). For each sampled signal: does one
threshold separate the session minutes with audio loss < 10/min (LOW) from
those with >= 30/min (HIGH)? Reports, per signal, the LOW and HIGH ranges
and how many minutes sit on the wrong side of the best single cut
(misclassified / (LOW + HIGH)). Reuses t2_analyze.py's minute table via
t2_summary.json is not enough (it has no per-minute signals), so the
minute construction is re-run by importing t2_analyze as a module.
"""
import io, contextlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import t2_analyze as A
low = [m for m in A.minutes if m["audio"] < 10]
high = [m for m in A.minutes if m["audio"] >= 30]
print(f"minutes: LOW (<10/min) {len(low)}, HIGH (>=30/min) {len(high)}, between {len(A.minutes)-len(low)-len(high)}")
out = []
for k in A.SIGNALS:
    lv = [m[k] for m in low if m[k] is not None]
    hv = [m[k] for m in high if m[k] is not None]
    if len(lv) < 5 or len(hv) < 5:
        continue
    best = None
    for cut in sorted(set(lv + hv)):
        for sign in (1, -1):   # HIGH above the cut, or below it
            wrong = sum(1 for v in lv if sign * v >= sign * cut) + sum(1 for v in hv if sign * v < sign * cut)
            if best is None or wrong < best[0]:
                best = (wrong, cut, "above" if sign == 1 else "below")
    out.append((best[0] / (len(lv) + len(hv)), k, min(lv), max(lv), min(hv), max(hv), best))
for frac, k, l0, l1, h0, h1, best in sorted(out)[:14]:
    print(f"  {frac:5.1%} wrong  {k:28s} LOW {l0:8.2f}-{l1:8.2f}  HIGH {h0:8.2f}-{h1:8.2f}  best cut: HIGH {best[2]} {best[1]:.2f} ({best[0]} wrong)")
json.dump([{"signal": k, "misclassified": f, "low_range": [l0, l1], "high_range": [h0, h1],
            "cut": b[1], "high_side": b[2]} for f, k, l0, l1, h0, h1, b in sorted(out)],
          open(os.path.join(HERE, "t2_separation.json"), "w"), indent=1)
