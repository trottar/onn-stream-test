#!/usr/bin/env python3
"""B90: the measurement's table from results.jsonl (made-up lists; counts and seconds only)."""
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
def mem_ok(d):
    m = (d.get("mem") or {}).get("READ_CORE_RAM") or []
    want = [x["want"].lower() for x in m]
    got = [x["got"].lower().split() for x in m]
    return f"{sum(w in g for w, g in zip(want, got))}/{len(m)}" if m else "—"
print("| core | list | picks | today's walk (HEAD's code): s / pulses | staged (B90): s / pulses | staged: verified | core memory holds the picks (staged) |")
print("| --- | --- | --- | --- | --- | --- | --- |")
for sysname in ("n64", "snes", "ps1"):
    for n in (12, 188, 677, 2092):
        for k in (1, 2, 4):
            w = next((d for d in rows if d.get("system") == sysname and d.get("mode") == "walk" and d["entries"] == n and d["picks"] == k), None)
            s = next((d for d in rows if d.get("system") == sysname and d.get("mode") == "staged" and d["entries"] == n and d["picks"] == k), None)
            core = {"n64": "Mupen64Plus-Next", "snes": "snes9x", "ps1": "Beetle PSX HW"}[sysname]
            wt = f"{w['activation_s']:.1f} s / {w['pulses']}" + (f" (error: {w['error']})" if w.get("error") else "") if w else "—"
            st = f"{s['activation_s']:.2f} s / {s['pulses']}" if s else "—"
            print(f"| {core} | {n:,} | {k} | {wt} | {st} | {s.get('activation_verified') if s else '—'}{' (error: ' + s['error'] + ')' if s and s.get('error') else ''} | {mem_ok(s) if s else '—'} |")
fails = [d for d in rows if "failed" in d]
print(f"\nruns failed to complete: {len(fails)}; RetroArch left running at the end: {[d['retroarch_left'] for d in rows if 'retroarch_left' in d]}")
