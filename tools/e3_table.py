#!/usr/bin/env python3
"""E3 -- one comparison table over run summaries (E2's rows, unchanged, plus E3's extras). Read-only.

    e3_table.py <out.md> <label>=<run dir or summary.json> [...]     -> <out.md> and <out>.json

The rows are e2_analysis.py's TABLE (evidence/e2_s1_2026-10-05/e2_analysis.py, imported, not copied), plus:
companion PSS / anon / file at the window's first and last sample and its last-15-min slope (E2's "keeps growing"
rule: slope over the last 15 min > 5 % of its level); the companion's threads by E2's A1 roles (audio sender =
SCHED_RR, relay = poll-mode with a clock_nanosleep TID+1, others); the EPG child's CPU-seconds per grab and its
peak PSS per grab (from samples.jsonl's `epg` category and epg.jsonl's grab bodies); RetroArch's thread count.
"""
from __future__ import annotations

import importlib.util
import json
import os
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "e2_analysis", os.path.join(REPO, "docs/memory/evidence/e2_s1_2026-10-05/e2_analysis.py"))
E2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E2)
t, jl, f = E2.t, E2.jl, E2.f


def window_samples(rd: str, s: dict) -> list:
    t0, t1 = t(s["window"]["from"]), t(s["window"]["to"])
    return [r for r in jl(os.path.join(rd, "samples.jsonl")) if t0 <= t(r["at_utc"]) <= t1]


def companion_mem(rows: list) -> dict:
    pts = [(t(r["at_utc"]), ((r.get("procs") or {}).get("companion") or {})) for r in rows]
    pts = [(x, c) for x, c in pts if c.get("pss_kb")]
    if not pts:
        return {}
    first, last = pts[0][1], pts[-1][1]
    end = pts[-1][0]
    tail = [(x, c["pss_kb"]) for x, c in pts if x >= end - 900]
    slope_pct = None
    if len(tail) > 2:
        xs, ys = [p[0] for p in tail], [p[1] for p in tail]
        sl = E2.slope(xs, ys)
        level = statistics.mean(ys)
        slope_pct = round(100 * sl * (xs[-1] - xs[0]) / level, 1) if level else None
    mb = lambda v: round(v / 1024, 1) if v is not None else None
    return {"pss_first_mb": mb(first.get("pss_kb")), "pss_last_mb": mb(last.get("pss_kb")),
            "anon_first_mb": mb(first.get("pss_anon_kb")), "anon_last_mb": mb(last.get("pss_anon_kb")),
            "file_first_mb": mb(first.get("pss_file_kb")), "file_last_mb": mb(last.get("pss_file_kb")),
            "pss_max_mb": mb(max(c["pss_kb"] for _, c in pts)),
            "last15_growth_pct": slope_pct,
            "keeps_growing": None if slope_pct is None else slope_pct > 5.0}


def thread_roles(rd: str, s: dict) -> dict:
    th = ((s.get("host") or {}).get("threads") or {}).get("companion") or []
    if not th:
        return {}
    by = {x["tid"]: x for x in th}
    rr = [x for x in th if x["policy"] == 2]
    relay, _ = E2.relay_tid(rd)
    out = {"audio_sender_cpu": round(sum(x["cpu_mean"] for x in rr), 2) if rr else None,
           "audio_sender_syscall": rr[0]["syscall_mode"] if len(rr) == 1 else None,
           "relay_cpu": by[relay]["cpu_mean"] if relay in by else None,
           "main_cpu": sum(x["cpu_mean"] for x in th if x["is_main"]),
           "companion_threads_seen": len(th)}
    return out


def epg_cost(rd: str, s: dict, rows: list) -> dict:
    """CPU-seconds and peak PSS of the epg category per grab body (grab start .. end + 1 s)."""
    t0, t1 = t(s["window"]["from"]), t(s["window"]["to"])
    grabs = [(t(g["start_utc"]), t(g["end_utc"]), g) for g in jl(os.path.join(rd, "epg.jsonl"))
             if g.get("kind") == "grab" and t0 <= t(g["start_utc"]) and t(g["end_utc"]) <= t1]
    if not grabs:
        return {}
    per_s = [(t(r["at_utc"]), ((r.get("procs") or {}).get("epg") or {})) for r in rows]
    cpu_s, peak = [], []
    for a, b, g in grabs:
        body = [e for x, e in per_s if a <= x <= b + 1.0]
        cpu_s.append(sum((e.get("cpu_pct") or 0) / 100.0 for e in body))
        pk = max((e.get("pss_kb") or 0 for e in body), default=0)
        if pk:
            peak.append(pk / 1024)
    tot = sum((e.get("cpu_pct") or 0) / 100.0 for _, e in per_s)
    return {"grabs": len(grabs), "cpu_s_per_grab_median": round(statistics.median(cpu_s), 2),
            "cpu_s_per_grab_mean": round(statistics.mean(cpu_s), 2),
            "cpu_s_window_total": round(tot, 1), "cpu_s_per_grab_window_avg": round(tot / len(grabs), 2),
            "peak_pss_mb_median": round(statistics.median(peak), 1) if peak else None,
            "peak_pss_mb_max": round(max(peak), 1) if peak else None,
            "channels": len({g.get("channel") for _, _, g in grabs})}


def figures(path: str) -> tuple:
    sp = path if path.endswith("summary.json") else os.path.join(path, "summary.json")
    rd = os.path.dirname(sp)
    s = json.load(open(sp))
    out = {"status": s.get("status")}
    if s.get("status") != "OK":
        return s, out
    rows = window_samples(rd, s)
    out["companion_mem"] = companion_mem(rows)
    out["threads"] = thread_roles(rd, s)
    out["epg_cost"] = epg_cost(rd, s, rows)
    ra = ((s.get("host") or {}).get("threads") or {}).get("retroarch") or []
    out["retroarch_threads"] = len(ra)
    out["retroarch_threads_over_30pct"] = sum(1 for x in ra if x["cpu_mean"] >= 30)
    out["window"] = s.get("window")
    return s, out


EXTRA = [
    ("companion PSS first → last MB (window)", lambda x: (x["companion_mem"].get("pss_first_mb"), x["companion_mem"].get("pss_last_mb"))),
    ("companion anon first → last MB", lambda x: (x["companion_mem"].get("anon_first_mb"), x["companion_mem"].get("anon_last_mb"))),
    ("companion file first → last MB", lambda x: (x["companion_mem"].get("file_first_mb"), x["companion_mem"].get("file_last_mb"))),
    ("companion PSS last-15-min growth % (keeps growing > 5)", lambda x: x["companion_mem"].get("last15_growth_pct")),
    ("audio sender thread CPU % (SCHED_RR)", lambda x: x["threads"].get("audio_sender_cpu")),
    ("relay thread CPU % (A1 rule)", lambda x: x["threads"].get("relay_cpu")),
    ("EPG CPU-s per grab, median (1-s samples)", lambda x: x["epg_cost"].get("cpu_s_per_grab_median")),
    ("EPG CPU-s per grab, window total / grabs", lambda x: x["epg_cost"].get("cpu_s_per_grab_window_avg")),
    ("EPG peak PSS per grab MB, median / max", lambda x: (x["epg_cost"].get("peak_pss_mb_median"), x["epg_cost"].get("peak_pss_mb_max"))),
    ("RetroArch threads / ≥ 30 % of a core", lambda x: (x.get("retroarch_threads"), x.get("retroarch_threads_over_30pct"))),
]


def main(argv: list) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    out_md, cols = argv[0], []
    for a in argv[1:]:
        label, _, p = a.partition("=")
        s, x = figures(p)
        cols.append((label, s, x))
    lines = ["| metric | " + " | ".join(c[0] for c in cols) + " |", "| --- |" + " --- |" * len(cols)]
    for name, fn in E2.TABLE:
        row = [name]
        for _, s, _x in cols:
            try:
                row.append(E2.cell(fn(s)) if s.get("status") == "OK" else str(s.get("status")))
            except Exception:  # noqa: BLE001
                row.append("—")
        lines.append("| " + " | ".join(row) + " |")
    for name, fn in EXTRA:
        row = [name]
        for _, s, x in cols:
            try:
                row.append(E2.cell(fn(x)) if s.get("status") == "OK" else str(s.get("status")))
            except Exception:  # noqa: BLE001
                row.append("—")
        lines.append("| " + " | ".join(row) + " |")
    open(out_md, "w").write("\n".join(lines) + "\n")
    json.dump({c[0]: c[2] for c in cols}, open(os.path.splitext(out_md)[0] + ".json", "w"), indent=1, default=str)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
