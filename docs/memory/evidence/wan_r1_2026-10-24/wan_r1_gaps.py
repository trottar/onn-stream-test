#!/usr/bin/env python3
"""WAN-R1: what a WAN link's gaps look like. Read-only over copies; nothing run, nothing changed.

Two distributions, per off-site session and per overlay path class (direct / relayed / no-peer / not sampled), against
the 5-GHz LAN's (LINK-R1, G-A3, CL-B10 cell 1, CL-B11 cell 1, CL-B12 cell 1):
  UPLINK SILENCES: the host's control-gap log (every client->host silence >= 250 ms, start + length). B6's method:
    per 10 min over streaming seconds, 10 s at every session start / end excluded (start-up, teardown, the user's
    exits). A gap >= 3 s is a REAL DROP (G4-S4's rule) and is listed apart; the thresholds act on the rest:
    the silence save at 400 ms, the hold at H 950.
  OUTPUT GAPS: the client's decoder report (`slow_events_ge_50_ms`, output_gap_ms; the last 1,024 retained, so
    coverage is stated) and its whole-session counts (spike_20_ms / spike_50_ms), per minute; output gaps >= 400 ms
    (the stall pause, B9) per 10 min. Placed by the report's own clock (end - duration + elapsed).
STREAMING SECONDS: seconds with frames on the host (native_frame_sizes, 1 s) where the copies hold them (G4-S4, the
  LAN cells); for G4-S1..S3 (their frame-size logs rotated out) the 10-s status polls with the stream active, each
  interval credited to the path sample nearest its middle -- a coarser clock, disclosed.
PATH CLASS: G4-S1..S3 from their path.jsonl (10 s); G4-S4 from the driver's slow samples (60 s; "not sampled" beyond
  60 s); the LAN cells "lan".
THE THRESHOLDS FOR B (not changed here): per class, the smallest H (50-ms grid, 250-2,950) with <= 1 non-drop uplink
  silence >= H per 10 min on each session of the class and pooled; the same for the stall threshold on output gaps
  (grid 150-2,000).

    wan_r1_gaps.py [--copy]   (--copy first copies G4-S1..S3's rows from the hub's logs into copies/)
    -> copies/..., wan_r1_tables.json, wan_r1_tables.md
"""
import glob
import json
import math
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE.parent
REPO = EV.parents[2]
LOGS = REPO / "logs/games"
EDGE = 10.0
DROP_MS = 3000


def ts(t):
    t = t.rstrip("Z")
    return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%f" if "." in t else "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()


def iso(x):
    return datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def jl(p):
    try:
        for line in open(p, errors="replace"):
            try:
                yield json.loads(line)
            except ValueError:
                pass
    except OSError:
        return


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    return xs[min(len(xs) - 1, int(math.ceil(q / 100 * len(xs))) - 1)]


# ---------------------------------------------------------------- the sessions
G4 = {
    "G4-S1 run 1 (7000, PCM, hotspot)": {"dir": EV / "g4_s1_2026-10-16/runs/E1-PS1-STREAM-REMOTE/run1", "key": "s1r1"},
    "G4-S1 run 2 (7000, PCM, hotspot; the toggle)": {"dir": EV / "g4_s1_2026-10-16/runs/E1-PS1-STREAM-REMOTE/run2", "key": "s1r2"},
    "G4-S2 run 1 (4000, PCM, hotspot)": {"dir": EV / "g4_s2_2026-10-17/runs/run1_capped/E1-PS1-STREAM-REMOTE/run1", "key": "s2r1",
                                         "ladder": EV / "g4_s2_2026-10-17/runs/run1_capped/ladder_log.jsonl",
                                         "wan": EV / "g4_s2_2026-10-17/runs/run1_capped/wan_poll.jsonl"},
    "G4-S3 (4000, Opus, hotspot)": {"dir": EV / "g4_s3_2026-10-19/runs/run1_capped/E1-PS1-STREAM-REMOTE/run1", "key": "s3r1",
                                    "ladder": EV / "g4_s3_2026-10-19/runs/run1_capped/ladder_log.jsonl",
                                    "wan": EV / "g4_s3_2026-10-19/runs/run1_capped/wan_poll.jsonl"},
}
S4 = EV / "g4_s4_2026-10-24"
LAN = {
    "LINK-R1 (5 GHz)": EV / "link_r1_2026-10-23/runs/logs_run1",
    "G-A3 (5 GHz)": EV / "g_a3_2026-10-23/runs/logs_run1",
    "CL-B10 cell 1 (5 GHz)": EV / "cl_b10_2026-10-23/runs/1_snes_5ghz_restart_guard/logs_run1",
    "CL-B11 cell 1 (5 GHz)": EV / "cl_b11_2026-10-24/runs/1_snes_5ghz_restart_guard_all_paths/logs_run1",
    "CL-B12 cell 1 (5 GHz)": EV / "cl_b12_2026-10-24/runs/1_snes_5ghz_two_home_presses/logs_run1",
}


def g4_span(cfg):
    rows = list(jl(cfg["dir"] / "path.jsonl"))
    return ts(rows[0]["at_utc"]) - 15, ts(rows[-1]["at_utc"]) + 15


def copy_g4():
    """Copy G4-S1..S3's rows (their spans) from the hub's logs, read-only, and the client reports received in them."""
    for name, cfg in G4.items():
        a, b = g4_span(cfg)
        out = HERE / "copies" / cfg["key"]
        (out / "decoder_sessions").mkdir(parents=True, exist_ok=True)
        for fname, key in (("native_stream_ctrl_gaps.log", "start_utc"), ("native_stream_recovery.log", "at_utc")):
            seen, keep = set(), []
            for src in sorted(glob.glob(str(LOGS / "stream_log_archive" / (fname + ".*")))) + [str(LOGS / fname)]:
                for line in open(src, errors="replace"):
                    try:
                        t = json.loads(line).get(key)
                    except ValueError:
                        continue
                    if t and a - 120 <= ts(t) <= b + 120 and line not in seen:
                        seen.add(line)
                        keep.append((t, line))
            keep.sort()
            (out / fname).write_text("".join(l for _, l in keep))
        for p in sorted(glob.glob(str(LOGS / "decoder_sessions/*.json"))):
            try:
                d = json.load(open(p))
                t = ts(d["received_at_utc"])
            except (OSError, ValueError, KeyError):
                continue
            if a <= t <= b + 600:          # a report can arrive minutes after its run (G4-S1 run 1: at the next start)
                (out / "decoder_sessions" / os.path.basename(p)).write_text(open(p).read())
        print("copied", name)
    for name, d in LAN.items():          # the LAN cells' client reports, by their spans (their copies hold none)
        fs = [ts(r["at_utc"]) for r in jl(d / "native_frame_sizes.jsonl") if r.get("at_utc")]
        out = HERE / "copies" / ("lan_" + name.split(" (")[0].replace(" ", "_").replace("-", "").lower()) / "decoder_sessions"
        out.mkdir(parents=True, exist_ok=True)
        for p in sorted(glob.glob(str(LOGS / "decoder_sessions/*.json"))):
            try:
                t = ts(json.load(open(p))["received_at_utc"])
            except (OSError, ValueError, KeyError):
                continue
            if min(fs) <= t <= max(fs) + 120:
                (out / os.path.basename(p)).write_text(open(p).read())


# ---------------------------------------------------------------- the readers
def edges(rec_path, a, b):
    xs = [ts(r["at_utc"]) for r in jl(rec_path) if r.get("event") in ("session_started", "session_ended") and r.get("at_utc")]
    return [x for x in xs if a - 60 <= x <= b + 60] + [a, b]


def gaps_in(path, a, b):
    return [(ts(g["start_utc"]), ts(g["end_utc"])) for g in jl(path) if g.get("start_utc") and a <= ts(g["start_utc"]) < b]


def reports_in(d, a, b):
    out = []
    for p in sorted(glob.glob(str(d / "*.json"))):
        try:
            x = json.load(open(p))
        except (OSError, ValueError):
            continue
        end = ts(x["received_at_utc"])
        r = x["report"]
        st = end - r["duration_ms"] / 1000
        if st <= b and end >= a:
            out.append((st, end, r))
    return out


def new_acc():
    return {"streaming_s": 0.0, "gaps": [], "drops": [], "out": [], "report_min": 0.0, "spike20": 0, "spike50": 0,
            "stalls_sent": 0, "slow_full": 0, "reports": 0, "whole_min": 0.0, "tail_reports": 0}


def add_reports(acc_of, reps, live, cls_at):
    """Output gaps from the client reports, placed by their own clock (end - duration + elapsed), counted only in LIVE
    seconds (streaming, outside the edges): a report's tail after its stream ended (a client "reconnecting") is not
    play. Report minutes = the live seconds the report covers, per class; the whole-session counts (spikes, stalls
    sent) are prorated by those seconds over the report's duration."""
    for st, end, r in reps:
        dur = r["duration_ms"] / 1000
        cov = [x for x in range(math.ceil(st), math.floor(end)) if x in live]
        if not cov or not dur:
            continue
        dec = r.get("decoder") or {}
        whole = len(cov) >= 0.8 * dur     # else a tail after the stream ended dominates the whole-session counts
        by = {}
        for x in cov:
            by[cls_at(x + 0.5)] = by.get(cls_at(x + 0.5), 0) + 1
        for cls, n in by.items():
            acc = acc_of(cls)
            acc["report_min"] += n / 60
            if whole:
                acc["spike20"] += (dec.get("spike_20_ms") or 0) * n / dur
                acc["spike50"] += (dec.get("spike_50_ms") or 0) * n / dur
                acc["stalls_sent"] += (r.get("stall_signal_stalls_sent") or 0) * n / dur
                acc["whole_min"] += n / 60
            else:
                acc["tail_reports"] += 1
            acc["reports"] += 1
            if (r.get("slow_event_retained_recent") or 0) >= (r.get("slow_event_capacity_recent") or 1e9):
                acc["slow_full"] += 1
        seen = set()
        for e in (r.get("slow_events_ge_50_ms") or []) + (r.get("slow_events_top_gap") or []):
            t = st + e[0] / 1000
            if (e[0], e[6]) in seen or math.floor(t) not in live:
                continue
            seen.add((e[0], e[6]))
            if e[6] >= 50:
                acc_of(cls_at(t))["out"].append(e[6])


def summarize(acc):
    s = acc["streaming_s"]
    per10 = lambda n: round(n * 600 / s, 2) if s else None
    g = acc["gaps"]
    ge = {h: sum(1 for m in g if m >= h) for h in range(250, 3000, 50)}
    out = acc["out"]
    rm = acc["report_min"]
    permin = lambda n: round(n / rm, 2) if rm else None
    return {"streaming_min": round(s / 60, 1), "silences_ge_250": len(g), "per10": per10(len(g)),
            "ge_400_per10": per10(ge[400]), "ge_950_per10": per10(ge[950]),
            "pctl_ms": {"p50": pct(g, 50), "p90": pct(g, 90), "p99": pct(g, 99)}, "longest_nondrop_ms": max(g) if g else 0,
            "bins": {f"{lo}-{hi}": sum(1 for m in g if lo <= m < hi) for lo, hi in
                     [(250, 300), (300, 400), (400, 500), (500, 600), (600, 800), (800, 950), (950, 1500), (1500, 3000)]},
            "real_drops_ms": sorted(acc["drops"], reverse=True),
            "ge": ge, "ge_per10": {h: per10(n) for h, n in ge.items()},
            "report_min": round(rm, 1), "reports": acc["reports"], "reports_slow_list_full": acc["slow_full"],
            "out_ge50_per_min": permin(sum(1 for m in out if m >= 50)), "out_ge80_per_min": permin(sum(1 for m in out if m >= 80)),
            "out_ge200_per_min": permin(sum(1 for m in out if m >= 200)),
            "out_ge400_per10": round(sum(1 for m in out if m >= 400) / rm * 10, 2) if rm else None,
            "out_ge": {h: sum(1 for m in out if m >= h) for h in range(150, 2001, 50)},
            "out_longest_ms": max(out) if out else None,
            "spike20_per_min": round(acc["spike20"] / acc["whole_min"], 2) if acc["whole_min"] else None,
            "spike50_per_min": round(acc["spike50"] / acc["whole_min"], 2) if acc["whole_min"] else None,
            "stalls_sent_per10": round(acc["stalls_sent"] / acc["whole_min"] * 10, 2) if acc["whole_min"] else None,
            "tail_reports_counts_excluded": acc["tail_reports"]}


def run_g4(name, cfg):
    a, b = g4_span(cfg)
    c = HERE / "copies" / cfg["key"]
    paths = [(ts(r["at_utc"]), (r.get("overlay") or {}).get("path") or "unknown") for r in jl(cfg["dir"] / "path.jsonl")]
    cls_at = lambda t: min(paths, key=lambda p: abs(p[0] - t))[1]
    ex = [(x - EDGE, x + EDGE) for x in edges(c / "native_stream_recovery.log", a, b)]
    inside = lambda t: a <= t < b and not any(x <= t < y for x, y in ex)
    accs = {}
    acc_of = lambda k: accs.setdefault(k, new_acc())
    polls = [(ts(r["at_utc"]), bool(r.get("active"))) for r in jl(cfg["dir"] / "status_poll.jsonl")]
    live = set()
    for (t0, a0), (t1, a1) in zip(polls, polls[1:]):
        if a0 and a1 and t1 - t0 <= 30:
            # the interval's seconds, each kept only if outside the edges; each credited to the class nearest it
            for k in range(int(t1 - t0)):
                x = math.floor(t0) + k
                if inside(x + 0.5):
                    live.add(x)
    for x in live:
        acc_of(cls_at(x + 0.5))["streaming_s"] += 1
    for s, e in gaps_in(c / "native_stream_ctrl_gaps.log", a, b):
        if inside(s):
            ms = round((e - s) * 1000)
            acc_of(cls_at(s))["drops" if ms >= DROP_MS else "gaps"].append(ms)
    add_reports(acc_of, reports_in(c / "decoder_sessions", a, b), live, cls_at)
    rtt = []
    for r in jl(cfg.get("wan", Path("/nonexistent"))):
        v = (((r.get("wan") or {}).get("measures") or {}).get("rtt_ms") or {}).get("value")
        if isinstance(v, dict):
            rtt.append((r["at_utc"][11:16], v.get("p50"), v.get("p95")))
    if not rtt:
        for r in jl(cfg["dir"] / "path.jsonl"):
            v = (((r.get("wan") or {}).get("measures") or {}).get("rtt_ms") or {}).get("value")
            if isinstance(v, dict):
                rtt.append((r["at_utc"][11:16], v.get("p50"), v.get("p95")))
    rungs = sorted({r.get("level_kbps") for r in jl(cfg.get("ladder", Path("/nonexistent"))) if r.get("event") == "sample"} - {None})
    return {"span": [iso(a), iso(b)], "classes": {k: summarize(v) for k, v in accs.items()},
            "rtt_by_minute": sorted({x[0]: x for x in rtt}.values()), "rungs_seen": rungs or None}


def run_frames(d, a, b, cls_at, rec, gaps_path, reports_dir, ladder=None):
    ex = [(x - EDGE, x + EDGE) for x in edges(rec, a, b)]
    inside = lambda t: a <= t < b and not any(x <= t < y for x, y in ex)
    accs = {}
    acc_of = lambda k: accs.setdefault(k, new_acc())
    secs = {math.floor(ts(r["at_utc"])) for r in jl(d / "native_frame_sizes.jsonl") if r.get("at_utc") and (r.get("frames") or 0) > 0}
    live = {x for x in secs if inside(x + 0.5)}
    for x in live:
        acc_of(cls_at(x + 0.5))["streaming_s"] += 1
    for s, e in gaps_in(gaps_path, a, b):
        if inside(s):
            ms = round((e - s) * 1000)
            acc_of(cls_at(s))["drops" if ms >= DROP_MS else "gaps"].append(ms)
    add_reports(acc_of, reports_in(reports_dir, a, b), live, cls_at)
    return {k: summarize(v) for k, v in accs.items()}


def main():
    if "--copy" in sys.argv:
        copy_g4()
    res = {"edge_excluded_s": EDGE, "drop_ms": DROP_MS, "sessions": {}}
    for name, cfg in G4.items():
        res["sessions"][name] = run_g4(name, cfg)
    # G4-S4: the copies; the path from the driver's 60-s samples
    slow = [(ts(r["at_utc"]), r["overlay"].get("path")) for r in jl(S4 / "samples/slow_60s.jsonl")]

    def s4_cls(t):
        best = min(slow, key=lambda p: abs(p[0] - t))
        return best[1] if abs(best[0] - t) <= 60 else "not sampled"
    d = S4 / "copies/logs/games"
    a, b = ts("2026-10-24T19:15:00"), ts("2026-10-25T17:40:00")
    res["sessions"]["G4-S4 (Opus; friend's broadband; ten + four lines)"] = {
        "span": [iso(a), iso(b)],
        "classes": run_frames(d, a, b, s4_cls, d / "native_stream_recovery.log", d / "native_stream_ctrl_gaps.log", d / "decoder_sessions"),
        "rtt_by_minute": [(r["at_utc"][11:16], v.get("p50"), v.get("p95")) for r in jl(S4 / "samples/slow_60s.jsonl")
                          if isinstance(v := ((((r.get("wan") or {}).get("measures") or {}).get("rtt_ms") or {}).get("value")), dict)][::5],
        "rungs_seen": [4000, 5000, 5500, 6000, 7000]}
    for name, ld in LAN.items():
        fs = [ts(r["at_utc"]) for r in jl(ld / "native_frame_sizes.jsonl") if r.get("at_utc")]
        a, b = min(fs), max(fs) + 1
        rd = HERE / "copies" / ("lan_" + name.split(" (")[0].replace(" ", "_").replace("-", "").lower()) / "decoder_sessions"
        res["sessions"][name] = {"span": [iso(a), iso(b)],
                                 "classes": run_frames(ld, a, b, lambda t: "lan", ld / "native_stream_recovery.log",
                                                       ld / "native_stream_ctrl_gaps.log", rd)}
    # ---- pooled per class, and the thresholds for B
    pool = {}
    for sname, s in res["sessions"].items():
        for cls, v in s["classes"].items():
            pool.setdefault(cls, []).append((sname, v))
    th = {}
    for cls, items in pool.items():
        items = [(n, v) for n, v in items if v["streaming_min"] >= 1.0]
        if not items:
            continue
        smin = sum(v["streaming_min"] for _, v in items)
        rmin = sum(v["report_min"] for _, v in items)
        hs = list(range(250, 3000, 50))
        H_each = next((h for h in hs if all((v["ge_per10"][h] or 0) <= 1.0 for _, v in items)), None)
        H_pool = next((h for h in hs if sum(v["ge"][h] for _, v in items) * 10 / smin <= 1.0), None)
        st_pool = next((h for h in range(150, 2001, 50) if rmin and sum(v["out_ge"][h] for _, v in items) * 10 / rmin <= 1.0), None)
        st_each = next((h for h in range(150, 2001, 50) if all(not v["report_min"] or v["out_ge"][h] * 10 / v["report_min"] <= 1.0
                                                               for _, v in items)), None)
        th[cls] = {"sessions": [n for n, _ in items], "streaming_min": round(smin, 1), "report_min": round(rmin, 1),
                   "silences_ge_250_per10_pooled": round(sum(v["silences_ge_250"] for _, v in items) * 10 / smin, 2),
                   "would_save_ge_400_per10_pooled": round(sum(v["ge"][400] for _, v in items) * 10 / smin, 2),
                   "would_hold_ge_950_per10_pooled": round(sum(v["ge"][950] for _, v in items) * 10 / smin, 2),
                   "would_stall_out_ge_400_per10_pooled": round(sum(v["out_ge"][400] for _, v in items) * 10 / rmin, 2) if rmin else None,
                   "H_le_1_per10_each_session": H_each, "H_le_1_per10_pooled": H_pool,
                   "stall_le_1_per10_each_session": st_each, "stall_le_1_per10_pooled": st_pool,
                   "real_drops_ms": sorted((m for _, v in items for m in v["real_drops_ms"]), reverse=True)}
    res["thresholds"] = th
    (HERE / "wan_r1_tables.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    # ---- the markdown tables
    L = ["# WAN-R1 tables (wan_r1_gaps.py)", "",
         "| session | class | streaming min | silences >= 250 | /10 min | >= 400 /10 | >= 950 /10 | p50 / p90 / p99 ms | longest non-drop | real drops (>= 3 s) | report min | out >= 50 / 80 / 200 per min | out >= 400 /10 | spikes >= 20 / 50 per min | stalls sent /10 |",
         "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | ---: | --- | ---: | --- | ---: |"]
    for sname, s in res["sessions"].items():
        for cls, v in sorted(s["classes"].items()):
            p = v["pctl_ms"]
            L.append(f"| {sname} | {cls} | {v['streaming_min']} | {v['silences_ge_250']} | {v['per10']} | {v['ge_400_per10']} | "
                     f"{v['ge_950_per10']} | {p['p50']} / {p['p90']} / {p['p99']} | {v['longest_nondrop_ms']} | "
                     f"{', '.join(map(str, v['real_drops_ms'])) or '—'} | {v['report_min']} | {v['out_ge50_per_min']} / "
                     f"{v['out_ge80_per_min']} / {v['out_ge200_per_min']} | {v['out_ge400_per10']} | {v['spike20_per_min']} / "
                     f"{v['spike50_per_min']} | {v['stalls_sent_per10']} |")
    L += ["", "| class | sessions | streaming min | silences /10 | would save (>= 400) /10 | would hold (>= 950) /10 | would stall (out >= 400) /10 | H <= 1/10 each / pooled | stall <= 1/10 each / pooled | real drops ms |",
          "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |"]
    for cls, t in th.items():
        L.append(f"| {cls} | {len(t['sessions'])} | {t['streaming_min']} | {t['silences_ge_250_per10_pooled']} | {t['would_save_ge_400_per10_pooled']} | "
                 f"{t['would_hold_ge_950_per10_pooled']} | {t['would_stall_out_ge_400_per10_pooled']} | {t['H_le_1_per10_each_session']} / "
                 f"{t['H_le_1_per10_pooled']} | {t['stall_le_1_per10_each_session']} / {t['stall_le_1_per10_pooled']} | "
                 f"{', '.join(map(str, t['real_drops_ms'])) or '—'} |")
    L += ["", "RTT (the client's control echo; running p50 / p95 ms) and rungs:"]
    for sname, s in res["sessions"].items():
        if s.get("rtt_by_minute") or s.get("rungs_seen"):
            L.append(f"- {sname}: rungs {s.get('rungs_seen')}; RTT " + "; ".join(f"{m} {a_}/{b_}" for m, a_, b_ in (s.get('rtt_by_minute') or [])[:14]))
    (HERE / "wan_r1_tables.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
