#!/usr/bin/env python3
"""C4-M1 step 0: replay the recorded post-FEC gap series (the C4-D1 inputs)
through 8+1, depth-2 interleaved 8+1 and 8+2. Read-only.

Inputs: the same corpus and heartbeat windows as C4-D1
(`../c4_d1_2026-09-24/c4_d1_analyze.py` is imported for them).

Model (stated, not hidden):
  * 8+1 recovers exactly one missing data packet per 8-group of ONE frame;
    what it leaves is recorded per 2 s heartbeat window as L lost in G
    forward-gap events (post-FEC). A post-FEC gap of b consecutive packets
    is, under 8+1, a run whose every 8-group part holds >= 2 missing
    packets (a part of 1 would have been recovered), or a single packet
    whose group parity was lost (b = 1).
  * For each b the gap's offset inside the 16-packet block (two 8-groups)
    is uniform over the offsets CONSISTENT with 8+1 having recovered none of
    it; the expected recovery of each scheme is averaged over them:
      - interleaved 8+1, depth 2: groups are the even and the odd packets of
        each 16-packet block (8 + 8); a group recovers iff it misses exactly
        one packet;
      - 8+2: groups are the same 8-groups as today; a group recovers iff it
        misses <= 2 packets.
    b = 1 (parity lost): interleaving recovers 0 (the one parity is still
    lost); 8+2 recovers it (the second parity).
  * Gap sizes are exact in windows with one gap event; windows with several
    events use the session's own exact-size distribution (population's when
    the session has < 20 exact packets), preserving the window's L.
  * Ignored, and so the estimate is an upper bound on interleaving's gain:
    frame boundaries (a group never spans frames; frames average 13.6
    packets, so many 16-blocks are partial), two independent singles
    landing in one 16-packet interleaved group (8+1 had them in separate
    8-groups), and the one-group-later parity (latency, reported separately).
  * The 8+1 row must reproduce the recorded post-FEC loss: it is the
    recorded L by construction of the model; printed as a check.
Pre-registered (handoffs/C4-M1_FEC_MEASURED_ARM_TASK.md): build interleaved if
it recovers >= 40 % of the residual at the corpus median; else 8+2 if >= 40 %;
else DEFER.
Corpus: EXACTLY the C4-D1 inputs -- its 38 sessions (V1 through rerun
session 3 and the rebuilt session 2); later reports are excluded.
"At the corpus median" has three readings: (a) the median over sessions of
each session's recovered share, (b) 1 - median L after / median L before,
(c) median recovered/min over median L/min. Decided before the 38-session
numbers were seen (a first pass on 44 sessions had shown (a) and (b) on
either side of 40 % for interleaving): a scheme passes only if it reaches
40 % on EVERY reading -- the rule is not loosened by picking a reading.
Usage: c4_m1_simulate.py <repo root>
"""
import os
import statistics
import sys
from collections import Counter
from itertools import product

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


def expected_recovery(b: int) -> tuple[float, float, int]:
    """(interleaved recovered, 8+2 recovered, consistent offsets) for a post-FEC gap of b."""
    if b == 1:
        return 0.0, 1.0, 1
    tot_i = tot_2 = 0.0
    n = 0
    for off in range(16):
        pos = list(range(off, off + b))
        g8 = Counter(p // 8 for p in pos)
        if any(v == 1 for v in g8.values()):
            continue                    # 8+1 would have recovered that part
        n += 1
        gi = Counter((p // 16, p % 2) for p in pos)
        tot_i += sum(1 for v in gi.values() if v == 1)
        tot_2 += sum(v for v in g8.values() if v <= 2)
    if n == 0:
        return 0.0, 0.0, 0
    return tot_i / n, tot_2 / n, n


def main():
    sys.argv = [sys.argv[0], ROOT]
    here = os.path.join(ROOT, "docs/memory/evidence/c4_d1_2026-09-24")
    sys.path.insert(0, here)
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import c4_d1_analyze as d1          # builds sessions and the exact gap sizes
    print("C4-M1 step 0 -- offline replay of the C4-D1 corpus")
    print(f"sessions {len(d1.sessions)}, exact single-gap windows {len(d1.single_gap_sizes)}")
    print()
    print("expected packets recovered per post-FEC gap of b (offsets consistent with 8+1):")
    print(f"  {'b':>3} {'consistent offsets':>18} {'interleaved':>11} {'8+2':>6}")
    table = {}
    for b in range(1, 33):
        ri, r2, n = expected_recovery(b)
        table[b] = (ri, r2)
        if b <= 12 or b in (16, 24, 32):
            print(f"  {b:3} {n:18} {ri:11.2f} {r2:6.2f}")
    print("  (b > 32: 0 by construction beyond the two edge groups; taken as the b = 32 value)")

    def rec(b):
        return table.get(b, table[32])

    pop = [b for _, b, _ in d1.single_gap_sizes]
    rows = []
    d1.sessions = [s for s in d1.sessions
                   if s["name"] <= "20260924_193658_993" or "rebuilt" in s["name"]]
    print(f"corpus restricted to the C4-D1 inputs: {len(d1.sessions)} sessions")
    print()
    print(f"{'session':<24} {'kind':<10} {'L/min':>6} {'8+1 model':>9} {'intl L/min':>10} {'8+2 L/min':>9} {'intl %':>7} {'8+2 %':>6}")
    for s in d1.sessions:
        mins = s["dur"] / 60.0
        own = [b for n, b, _ in d1.single_gap_sizes if n == s["name"]]
        dist = own if sum(own) >= 20 else pop
        # per-packet recovery fractions from the distribution
        tot = sum(dist)
        fi = sum(rec(b)[0] for b in dist) / tot
        f2 = sum(rec(b)[1] for b in dist) / tot
        L = s["L"]
        li, l2 = L * (1 - fi), L * (1 - f2)
        rows.append(dict(name=s["name"], kind=s["kind"], L=L / mins, Li=li / mins, L2=l2 / mins,
                         pi=100 * fi, p2=100 * f2))
        print(f"{s['name']:<24} {s['kind']:<10} {L / mins:6.2f} {L / mins:9.2f} {li / mins:10.2f} {l2 / mins:9.2f} "
              f"{100 * fi:7.1f} {100 * f2:6.1f}")
    print()
    for label, sel in (("ALL", rows), ("HOLDS", [r for r in rows if r["kind"] == "hold"]),
                       ("TRANSITION", [r for r in rows if r["kind"] == "transition"])):
        m = statistics.median
        print(f"{label:<10} n={len(sel):2}  median L/min {m([r['L'] for r in sel]):.2f} -> interleaved "
              f"{m([r['Li'] for r in sel]):.2f} ({m([r['pi'] for r in sel]):.1f} % of the residual), "
              f"8+2 {m([r['L2'] for r in sel]):.2f} ({m([r['p2'] for r in sel]):.1f} %)")
    m = statistics.median
    readings = {}
    for key, lk in (("interleaved", "Li"), ("8+2", "L2")):
        pk = "pi" if key == "interleaved" else "p2"
        a = m([r[pk] for r in rows])
        b = 100 * (1 - m([r[lk] for r in rows]) / m([r["L"] for r in rows]))
        c = 100 * m([r["L"] - r[lk] for r in rows]) / m([r["L"] for r in rows])
        readings[key] = (a, b, c)
        print(f"{key:<12} recovered share of the residual: (a) {a:.1f} %  (b) {b:.1f} %  (c) {c:.1f} %  "
              f"-> {'PASSES' if min(a, b, c) >= 40 else 'does not pass'} (>= 40 % on every reading)")
    print("rule: build interleaved if it passes; else 8+2 if it passes; else DEFER")
    if min(readings["interleaved"]) >= 40:
        print("-> BUILD INTERLEAVED (xor8_1_i2)")
    elif min(readings["8+2"]) >= 40:
        print("-> BUILD 8+2 (xor8_2)")
    else:
        print("-> DEFER")


if __name__ == "__main__":
    main()
