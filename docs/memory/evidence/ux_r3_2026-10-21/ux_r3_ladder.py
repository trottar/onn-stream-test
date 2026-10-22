#!/usr/bin/env python3
"""UX-R3 §3: the ladder at each top-ranked second (read from the copies; no change proposed) -> ladder_table.txt."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); EV = os.path.dirname(HERE)
def jl(p):
    for l in open(p):
        try: yield json.loads(l)
        except ValueError: pass
src = {"R2": ("ux_r2_2026-10-21/session/logs/games/adaptive_bitrate_shadow.jsonl", "2026-10-21T04:42"),
       "R1": ("ux_r1_2026-10-20/session/logs/games/adaptive_bitrate_shadow.jsonl", "2026-10-20T04:19")}
moments = {"R2": ["2026-10-21T04:42:47", "2026-10-21T04:54:56", "2026-10-21T04:54:59", "2026-10-21T04:55:53",
                  "2026-10-21T04:59:57", "2026-10-21T05:03:10", "2026-10-21T05:12:46", "2026-10-21T05:17:38"],
           "R1": ["2026-10-20T05:06:04", "2026-10-20T05:10:05", "2026-10-20T05:10:55", "2026-10-20T05:20:50", "2026-10-20T05:21:43"]}
L = ["UX-R3 §3: the ladder at each top-ranked second (live mode; read from the copies; no change proposed).",
     "live's step-down rules over the last 5 evaluated reports (10 s): capacity_mild (one rung) fps < 57 on >= 4 of 5 AND loss >= 50 on >= 3 of 5;",
     "  capacity (fallback) fps < 50 on all 5 AND loss >= 50 on >= 3 of 5; queue/gap FALLBACK fps < 50 on all 5 AND (queue >= 2 on >= 3 of 5 OR gap > 250 on >= 2 of 5);",
     "  ROUTINE fps < 57 on >= 4 of 5 AND queue >= 1 on >= 3 of 5; none before 60 s of session age; stale / blackout / resync reports do not count.",
     "evening | second | state / reason at or before | last acted decision this evening | the 5 samples from it (fps / loss / gap / queue / disposition) | fps<57 | fps<50 | loss>=50 | gap>250 | queue>=1 | what capacity_mild needed"]
for ev, ms in moments.items():
    path, eve0 = src[ev]
    rows = [r for r in jl(os.path.join(EV, path)) if r.get("at_utc", "") >= eve0]
    for m in ms:
        before = [r for r in rows if r["at_utc"][:19] <= m]
        st = next((r for r in reversed(before) if r["event"] in ("state", "sample")), {})
        acted = next((r for r in reversed(before) if r.get("acted")), None)
        after = [r for r in rows if r["at_utc"][:19] >= m and r["event"] == "sample"][:5]
        f = [r.get("fps") for r in after]; lo = [r.get("lost_packets_delta") for r in after]
        g = [r.get("output_gap_ms") for r in after]; q = [r.get("queue_depth") for r in after]
        c = lambda xs, p: sum(1 for v in xs if v is not None and p(v))
        n57, n50, nl, ng, nq = c(f, lambda v: v < 57), c(f, lambda v: v < 50), c(lo, lambda v: v >= 50), c(g, lambda v: v > 250), c(q, lambda v: v >= 1)
        need = ([f"{4 - n57} more at fps<57"] if n57 < 4 else []) + ([f"{3 - nl} more with loss>=50"] if nl < 3 else [])
        samples = "; ".join(f"{(v or 0):.0f}/{l}/{gg}/{qq}/{r.get('disposition')}" for v, l, gg, qq, r in zip(f, lo, g, q, after))
        act = f"{acted['at_utc'][11:19]} {acted['event']} {acted.get('reason')} -> {acted.get('level_kbps')}" if acted else "none"
        L.append(f"{ev} | {m[11:]} | {st.get('state')} / {st.get('reason')} | {act} | {samples} | {n57}/5 | {n50}/5 | {nl}/5 | {ng}/5 | {nq}/5 | {'met' if not need else ', '.join(need)}")
open(os.path.join(HERE, "ladder_table.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
