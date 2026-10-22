#!/usr/bin/env python3
"""LAN-R2: the extended search, declared after the first search found no passing pair (rule_search.md): the uplink
term counted over BOTH windows (20 s) or required in both; the base at T 3 K 3 (LAN-R1's other zero-false cell).
Read-only; reuses lan_r2_analysis's series.   python3 -I lan_r2_extended.py -> rule_search_extended.md / .json"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lan_r2_analysis as R  # noqa: E402

lad, hb, gl = R.ladder_rows(), R.heartbeats(), R.gaps()
spans = R.L.SPANS + R.CELL_SPANS
ser = {sp[0]: R.series(sp, lad, hb, gl) for sp in spans}
sun, r2 = ser[R.L.SPANS[0][0]], ser[R.L.SPANS[1][0]]
r2_clean = {m for m, v in R.A.minutes_table(R.EV / "lan_r1_2026-10-21/inputs/ux_r2/timeline.json").items() if R.A.clean_minute(v)}
cleans, cells = [sp[0] for sp in R.L.SPANS[2:]], [sp[0] for sp in R.CELL_SPANS]


def fires(s, T, K, term):
    out = []
    for sess in R.A.sessions_of(s):
        win = []
        for x in sess:
            if x["disposition"] != "evaluated":
                continue
            win.append(x)
            if len(win) < 5 * K or not isinstance(x["elapsed_ms"], (int, float)) or x["elapsed_ms"] < 60_000:
                continue
            ws = [win[len(win) - 5 * (i + 1): len(win) - 5 * i] for i in range(K)]
            if all(sum(R.num(y["unrec"]) for y in W) >= T for W in ws) and term(ws):
                out.append(x["at_utc"])
    return out


terms = []
for G in (250, 300, 400, 500):
    for N in (2, 3, 4, 5, 6, 8):
        terms.append((f"uplink >= {G} ms, >= {N} over both windows", lambda ws, G=G, N=N: sum(1 for W in ws for x in W if x["up_max"] >= G) >= N))
    for N in (1, 2):
        terms.append((f"uplink >= {G} ms, >= {N} in EACH window", lambda ws, G=G, N=N: all(sum(1 for x in W if x["up_max"] >= G) >= N for W in ws)))
rows = []
for T, K in ((4, 2), (3, 3), (3, 2)):
    for label, term in terms:
        r = {"T": T, "K": K, "term": label, "cells": [R.episodes(fires(ser[c], T, K, term)) for c in cells],
             "clean": sum(R.episodes(fires(ser[c], T, K, term)) for c in cleans)}
        f2 = fires(r2, T, K, term)
        r["r2_clean_false"] = sorted({t[11:16] for t in f2 if t[11:16] in r2_clean})
        sf = fires(sun, T, K, term)
        r["sunday_first"] = sf[0][11:19] if sf else None
        r["sunday_minutes"] = sorted({t[11:16] for t in sf})
        r["ok"] = r["cells"][0] == 0 and r["cells"][1] == 0 and r["clean"] == 0 and not r["r2_clean_false"] and bool(r["sunday_first"]) and r["sunday_first"] < "05:06:00"
        r["ok_bidirectional"] = all(c == 0 for c in r["cells"]) and r["clean"] == 0 and not r["r2_clean_false"] and bool(r["sunday_first"])
        rows.append(r)
(HERE / "rule_search_extended.json").write_text(json.dumps(rows, indent=1) + "\n")
md = ["# LAN-R2 — the extended search (`lan_r2_extended.py`)", "",
      "`ok` = 0 in cells 1-2, the clean windows and last night's clean minutes, and Sunday before 05:06. "
      "`ok (bidir)` = 0 in all four cells (random / burst downlink loss) and the clean windows, and fires on Sunday at all.", "",
      "| T/K | term | cells 1 / 2 / 3 / 4 | clean | last night false | Sunday first | Sunday minutes | ok | ok (bidir) |",
      "| --- | --- | --- | ---: | --- | --- | --- | --- | --- |"]
for r in rows:
    md.append(f"| {r['T']}/{r['K']} | {r['term']} | {' / '.join(map(str, r['cells']))} | {r['clean']} | {', '.join(r['r2_clean_false']) or '—'} | "
              f"{r['sunday_first'] or '—'} | {', '.join(r['sunday_minutes'][:7]) or '—'} | {'**yes**' if r['ok'] else ''} | {'yes' if r['ok_bidirectional'] else ''} |")
(HERE / "rule_search_extended.md").write_text("\n".join(md) + "\n")
print("\n".join(l for l in md if "**yes**" in l or "| yes |" in l or l.startswith("| T/K")))
print("passing (ok):", sum(r["ok"] for r in rows), " passing (bidir):", sum(r["ok_bidirectional"] for r in rows))
