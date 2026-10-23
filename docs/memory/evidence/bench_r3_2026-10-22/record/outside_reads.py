#!/usr/bin/env python3
"""BENCH-R3 record: two readings outside named windows, with the same tools as bench_r3_record_read.py (exec'd unedited):
the hitch seconds per 10 min outside the blackouts (A, B, D; window start - 1 .. start + 15 s), and E-on's uplink silences
per 10 min outside its 21:42:20-21:43:25Z cluster.   python3 -B record/outside_reads.py   (from bench_r3_2026-10-22/)"""
import importlib.util, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("rr", HERE / "bench_r3_record_read.py")
rr = importlib.util.module_from_spec(spec); spec.loader.exec_module(rr)
R = json.load(open(HERE / "record_read.json"))
out = {}
for c, o in R["cells"].items():
    ld = HERE / "logs" / c
    s0, s1 = rr.ts(o["session"][0]), rr.ts(o["session"][1])
    rows, _, _, play_s = rr.UXNS["evening"]({"dir": str(ld), "start": rr.utc(s0)[:19], "end": rr.utc(s1 + 1)[:19]})
    wins = [(rr.ts(o["session"][0][:11] + b["start_utc"] + "Z") - 1, rr.ts(o["session"][0][:11] + b["start_utc"] + "Z") + 15)
            for b in o.get("blackouts", [])]
    inw = lambda k: any(a <= rr.ts(k + "Z") < b for a, b in wins)
    hit_in = sum(1 for k, r in rows.items() if r["score"] and inw(k))
    hit_out = sum(1 for k, r in rows.items() if r["score"] and not inw(k))
    ex_s = sum(b - a for a, b in wins)
    out[c] = {"hitch_total": o["hitch"]["hitch_seconds"], "play_s": play_s, "hitch_in_blackouts": hit_in, "hitch_outside": hit_out,
              "outside_s": round(play_s - ex_s), "hitch_outside_per10": round(hit_out * 600 / (play_s - ex_s), 1) if wins else None}
    if c.startswith("E-on"):
        a, b = rr.ts("2026-10-22T21:42:20Z"), rr.ts("2026-10-22T21:43:25Z")
        g = rr.GDNS["measure"](c + " outside the cluster", ld, s0, s1, [(a, b)])
        gi = rr.GDNS["measure"](c + " the cluster", ld, a, b)
        out[c]["silences_outside_cluster"] = {"per10": g["per10"], "gaps": g["gaps"], "ge500_per10": g["ge_per10"][500], "max_ms": g["max_ms"]}
        out[c]["silences_in_cluster"] = {"gaps_ge250": sum(1 for s, e in rr.GDNS["gaps"](ld) if a <= s < b and e - s >= 0.25)}
        hc = sum(1 for k, r in rows.items() if r["score"] and a <= rr.ts(k + "Z") < b)
        out[c]["hitch_in_cluster"] = hc
        out[c]["hitch_outside_cluster_per10"] = round((o["hitch"]["hitch_seconds"] - hc) * 600 / (play_s - (b - a)), 1)
(HERE / "outside_reads.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
