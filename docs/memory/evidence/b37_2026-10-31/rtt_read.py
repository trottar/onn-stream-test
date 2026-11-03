#!/usr/bin/env python3
"""B37: the control echo (`latency.control_round_trip_ms`) as recorded, read-only.
(1) every e1_suite telemetry.jsonl under docs/memory/evidence (the LAN bench at home, e1_suite polls of the hub's
    /status every 2 s; one sample per client report, deduplicated by the report's elapsed_ms), grouped by record;
(2) the WAN rows: wan_sessions.jsonl in the trip read's copies (Friday) and in the G4-S4 dir if present.
Prints aggregate numbers only (no rows, no addresses)."""
import glob, json, statistics, sys
from pathlib import Path
EV = Path(__file__).resolve().parents[1]

def pct(v, q):
    v = sorted(v)
    return None if not v else v[min(len(v) - 1, int(round(q * (len(v) - 1))))]

out = {"lan_bench": {}, "wan_sessions": {}}
for f in sorted(EV.glob("*/runs/**/telemetry.jsonl")):
    rec = f.relative_to(EV).parts[0]
    if rec.startswith("trip_") or rec.startswith("g4_"):
        continue
    seen = {}
    for line in f.open(errors="replace"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if not r.get("fresh"):
            continue
        v = (r.get("latency") or {}).get("control_round_trip_ms")
        if isinstance(v, (int, float)):
            seen[r.get("elapsed_ms")] = v
    if seen:
        out["lan_bench"].setdefault(rec, []).extend(seen.values())
summ = {}
for rec, v in out["lan_bench"].items():
    summ[rec] = {"n": len(v), "min": min(v), "p10": pct(v, .1), "p50": pct(v, .5), "p95": pct(v, .95), "max": max(v)}
allv = [x for v in out["lan_bench"].values() for x in v]
summ["ALL_LAN"] = {"n": len(allv), "min": min(allv), "p10": pct(allv, .1), "p25": pct(allv, .25), "p50": pct(allv, .5),
                   "p75": pct(allv, .75), "p95": pct(allv, .95), "max": max(allv)}
res = {"lan_bench_by_record": summ}
for label, pat in (("trip_friday", "trip_r2_2026-10-31/copies/wan_sessions.jsonl"), ("g4_s4", "g4_s4_2026-10-24/**/wan_sessions*.jsonl")):
    rows = []
    for f in sorted(EV.glob(pat)):
        for line in f.open():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            m = ((r.get("measures") or {}).get("rtt_ms") or {}).get("value") or {}
            if m.get("p50") is not None:
                rows.append((m["p50"], m.get("p95"), r.get("reports"), ((r.get("measures") or {}).get("overlay_path") or {}).get("value")))
    if rows:
        p50s = [x[0] for x in rows]; p95s = [x[1] for x in rows if x[1] is not None]
        res[label] = {"sessions": len(rows), "p50_of_session_p50": pct(p50s, .5), "session_p50_range": [min(p50s), max(p50s)],
                      "p50_of_session_p95": pct(p95s, .5), "session_p95_range": [min(p95s), max(p95s)],
                      "paths": sorted({str(x[3]) for x in rows}),
                      "per_session_p50_p95_reports": [[x[0], x[1], x[2]] for x in rows]}
json.dump(res, sys.stdout, indent=1)
print()
