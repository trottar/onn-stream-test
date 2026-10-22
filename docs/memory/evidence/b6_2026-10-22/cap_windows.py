#!/usr/bin/env python3
"""B6: per session, the most gaps >= H that START inside any rolling 60-s (and 10-s) window -- how often B2's cap
(6 per 60 s) would bind at H = 250 (B2) and at the chosen H. Read-only; reuses gap_distribution.py's loaders.
    python3 -I cap_windows.py"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gap_distribution as G  # noqa: E402  (re-runs the distribution; same inputs, same outputs)
H = G.res["H_chosen"]
SRC = {"BENCH-R1 01_loss-1_plain": G.R1 / "runs/01_loss-1_plain/logs_run1", "BENCH-R1 08_none_hold": G.R1 / "runs/08_none_hold/logs_run1",
       "BENCH-R1 05 (room, blackouts excluded)": G.R1 / "runs/05_blackout-both_plain/logs_run1",
       "BENCH-R1 06 (room, blackouts excluded)": G.R1 / "runs/06_blackout-both_hold/logs_run1",
       "UX-R2 evening": G.UX2, "UX-R1 Sunday": G.UX1}
out = {}
for name, d in SRC.items():
    s = [x for x in G.sets if x["name"].startswith(name.split(" (")[0].split(" evening")[0].split(" Sunday")[0])]
    a, b = s[0]["span"] if s else (0, 1e12)
    key = {"05": "05_blackout-both_plain", "06": "06_blackout-both_hold"}.get(name.split()[1][:2]) if name.startswith("BENCH-R1 0") else None
    ex = [(G.ts("2026-10-22T" + t) - 1, G.ts("2026-10-22T" + t) + 10) for t in G.blackouts.get(key, [])]
    gl = [(st, en) for st, en in G.gaps(d) if a <= st < b and not any(x <= st < y for x, y in ex)]
    row = {}
    for h in (250, H):
        starts = [st for st, en in gl if (en - st) * 1000 >= h]
        row[str(h)] = {"gaps": len(starts),
                       "max_in_60s": max((sum(1 for y in starts if x <= y < x + 60) for x in starts), default=0),
                       "max_in_10s": max((sum(1 for y in starts if x <= y < x + 10) for x in starts), default=0),
                       "windows_60s_at_or_over_6": sum(1 for x in starts if sum(1 for y in starts if x <= y < x + 60) >= 6)}
    out[name] = row
print(json.dumps({"H": H, "sets": out}, indent=1))
(Path(__file__).resolve().parent / "cap_windows.json").write_text(json.dumps({"H": H, "sets": out}, indent=1) + "\n")
