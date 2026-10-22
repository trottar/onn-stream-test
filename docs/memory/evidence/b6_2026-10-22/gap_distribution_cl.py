#!/usr/bin/env python3
"""B6 correction (found during LAN-R2): the CL-B5/6/7 clean windows DO have control-gap rows, in the live
`logs/games/native_stream_ctrl_gaps.log*` (read-only), which B6's search of the evidence copies missed. This adds
them as clean sessions (600 s each, the e1 suite's window; no frame log that old) and re-applies B6's rule.
    python3 -I gap_distribution_cl.py   -> gap_distribution_cl.json / .md"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "lan_r1_2026-10-21"))
import gap_distribution as G  # noqa: E402  (re-runs B6's own distribution, same inputs)
import lan_r1_series as L  # noqa: E402
rows = {}
for p in ["logs/games/stream_log_archive/native_stream_ctrl_gaps.log.1", "logs/games/native_stream_ctrl_gaps.log"]:
    for r in L.jl(REPO / p):
        if r.get("start_utc") and r.get("end_utc"):
            rows[(r["start_utc"], r["end_utc"])] = round((L.ts(r["end_utc"]) - L.ts(r["start_utc"])) * 1000)
starts = {k[0]: v for k, v in rows.items()}
cl = []
for name, kind, a, b in L.SPANS[2:10]:                       # CL-B5 A/B/L, CL-B6 1/2, CL-B7 x3 (G4-S3 is remote)
    ta, tb = L.ts(a), L.ts(b)
    ms = [m for s, m in starts.items() if ta <= L.ts(s) < tb and m >= 250]
    cl.append({"name": name, "streaming_s": 600, "gaps": len(ms),
               "ge_per10": {h: sum(1 for m in ms if m >= h) for h in range(250, 2001, 50)}, "max_ms": max(ms, default=0)})
B6clean = [s for s in G.sets if s["clean"]]
H = None
for h in range(250, 2001, 50):
    if max([s["ge_per10"][h] for s in B6clean] + [c["ge_per10"][h] for c in cl]) <= 1.0:
        H = h; break
out = {"cl_windows": cl, "H_with_cl": H, "H_b6": G.res["H_chosen"]}
(HERE / "gap_distribution_cl.json").write_text(json.dumps(out, indent=1) + "\n")
L2 = ["# B6 correction: the CL-B5/6/7 clean windows added (their control gaps are in the live logs)", "",
      "| window (600 s) | gaps >= 250 | >= 500 | >= 900 | >= 950 | longest ms |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
for c in cl:
    g = c["ge_per10"]
    L2.append(f"| {c['name']} | {c['gaps']} | {g[500]} | {g[900]} | {g[950]} | {c['max_ms']} |")
L2 += ["", f"**H by B6's rule with these added: {H} ms** (B6's own: {G.res['H_chosen']} ms). The idle room of 10-18/19 made "
       "59-81 uplink silences >= 250 ms per 10 min in CL-B5/B6 -- more than cell 8's 16 -- and 0-1 >= 950."]
(HERE / "gap_distribution_cl.md").write_text("\n".join(L2) + "\n")
print("\n".join(L2))
