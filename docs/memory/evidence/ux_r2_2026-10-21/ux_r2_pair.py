#!/usr/bin/env python3
"""UX-R2 §1: the two evenings paired by play-minute (5-min blocks from each evening's first frame), read-only.
Reads the per-minute rows of UX-R1's and UX-R2's timeline.json (heartbeat deltas; minutes with < 30 s of heartbeat
are left out of the rates, as in the timelines' aggregates).
    ux_r2_pair.py   -> pair.txt + pair.json beside this script
"""
import json, os, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
EVES = {"UX-R1 (10-20, 04:19Z)": os.path.join(HERE, "../ux_r1_2026-10-20/timeline.json"),
        "UX-R2 (10-21, 04:42Z)": os.path.join(HERE, "timeline.json")}
F = ["post_fec", "fec_rec", "concealed", "underruns"]


def blocks(path):
    t = json.load(open(path))
    rows = t["minutes"]
    h0, m0 = map(int, rows[0]["utc"].split(":"))
    out = {}
    for r in rows:
        h, m = map(int, r["utc"].split(":"))
        pm = (h * 60 + m) - (h0 * 60 + m0)
        out.setdefault(pm // 5, []).append(r)
    res = []
    for b, rs in sorted(out.items()):
        full = [r for r in rs if r["hb_s"] >= 30]
        n = sum(r["hb_s"] for r in full) / 60
        row = {"block": f"{b * 5:02d}-{b * 5 + 4:02d}", "utc": f"{rs[0]['utc']}-{rs[-1]['utc']}",
               "systems": "/".join(sorted({r["system"] for r in rs})), "minutes": round(n, 1)}
        for f in F:
            row[f + "/min"] = round(sum(r[f] for r in full) / n, 1) if n else None
        row["fps"] = round(statistics.mean(r["fps"] for r in full), 2) if full else None
        res.append(row)
    return res


pair = {k: blocks(v) for k, v in EVES.items()}
L = ["UX-R2: the two evenings by play-minute (5-min blocks from the first frame; per-minute rates from the heartbeat)\n"]
cols = ["utc", "systems", "minutes"] + [f + "/min" for f in F] + ["fps"]
n = max(len(v) for v in pair.values())
names = list(pair)
L.append("| play-min | " + " | ".join(f"{nm} {c}" for nm in ("R1", "R2") for c in cols) + " |")
L.append("|" + " --- |" * (1 + 2 * len(cols)))
for i in range(n):
    cells = [pair[names[0]][i]["block"] if i < len(pair[names[0]]) else pair[names[1]][i]["block"]]
    for nm in names:
        r = pair[nm][i] if i < len(pair[nm]) else None
        cells += [str(r[c]) if r else "" for c in cols]
    L.append("| " + " | ".join(cells) + " |")
open(os.path.join(HERE, "pair.txt"), "w").write("\n".join(L) + "\n")
json.dump(pair, open(os.path.join(HERE, "pair.json"), "w"), indent=1)
print("\n".join(L))
