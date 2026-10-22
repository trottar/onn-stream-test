#!/usr/bin/env python3
"""B6: every uplink silence >= 250 ms on file, binned, per 10 min; the clean sessions chosen before computing; H chosen
as the smallest value (50-ms grid, 250-2000) with <= 1 gap >= H per 10 min on EACH clean session (and pooled); what H
catches of the death and Sunday's bursts and the bench's room. Read-only over the evidence copies. Writes
gap_distribution.json and gap_distribution.md.   python3 -I gap_distribution.py"""
import glob, json, math
from datetime import datetime, timezone
from pathlib import Path
HERE = Path(__file__).resolve().parent
EV = HERE.parent
BINS = [250, 300, 400, 500, 600, 800, 1000, 1500]
EDGE_S = 10.0                         # start-up / teardown excluded at each session end


def ts(t):
    t = t.rstrip("Z"); f = "%Y-%m-%dT%H:%M:%S.%f" if "." in t else "%Y-%m-%dT%H:%M:%S"
    return datetime.strptime(t, f).replace(tzinfo=timezone.utc).timestamp()


def jl(p):
    for line in Path(p).read_text(errors="replace").splitlines():
        try:
            yield json.loads(line)
        except Exception:
            pass


def gaps(d):
    out = {}
    for p in sorted(glob.glob(str(d / "native_stream_ctrl_gaps.log*"))):
        for r in jl(p):
            if r.get("start_utc") and r.get("end_utc"):
                out[(r["start_utc"], r["end_utc"])] = (ts(r["start_utc"]), ts(r["end_utc"]))
    return sorted(out.values())


def frame_seconds(d):
    s = set()
    for p in sorted(glob.glob(str(d / "native_frame_sizes.jsonl*"))):
        for r in jl(p):
            if r.get("at_utc") and isinstance(r.get("frames"), (int, float)) and r["frames"] > 0:
                s.add(math.floor(ts(r["at_utc"])))
    return s


def sessions(d, a, b):
    rows = sorted((ts(r["at_utc"]), r["event"]) for p in sorted(glob.glob(str(d / "native_stream_recovery.log*")))
                  for r in jl(p) if r.get("event") in ("session_started", "session_ended") and r.get("at_utc"))
    return [t for t, _ in rows if a - 60 <= t <= b + 60]


def measure(name, d, a, b, exclude=(), clean=True, note=""):
    bounds = sessions(d, a, b) + [a, b]
    ex = [(x - EDGE_S, x + EDGE_S) for x in bounds] + list(exclude)
    inside = lambda t: a <= t < b and not any(x <= t < y for x, y in ex)
    secs = sum(1 for s in frame_seconds(d) if inside(s + 0.5))
    g = [(s, e) for s, e in gaps(d) if inside(s) and (e - s) >= 0.25]
    ms = [round((e - s) * 1000.0) for s, e in g]
    bins = {f"{lo}-{BINS[i + 1] if i + 1 < len(BINS) else 'inf'}": sum(1 for m in ms if lo <= m < (BINS[i + 1] if i + 1 < len(BINS) else 1e12))
            for i, lo in enumerate(BINS)}
    per10 = lambda n: round(n * 600.0 / secs, 2) if secs else None
    ge = {h: sum(1 for m in ms if m >= h) for h in range(250, 2001, 50)}
    return {"name": name, "clean": clean, "note": note, "span": [a, b], "streaming_s": secs, "gaps": len(ms),
            "per10": per10(len(ms)), "bins": bins, "bins_per10": {k: per10(v) for k, v in bins.items()},
            "ge": ge, "ge_per10": {h: per10(n) for h, n in ge.items()}, "max_ms": max(ms) if ms else 0,
            "gaps_ms": sorted(ms, reverse=True)[:40]}


R1 = EV / "bench_r1_2026-10-22"
cells = json.loads((R1 / "record" / "record_read.json").read_text())["cells"]
sets = []
for key, clean, note in [("01_loss-1_plain", True, "uplink unimpaired (loss-1 is downlink post-FEC); the hold off"),
                         ("08_none_hold", True, "no impairment; the hold on (B2, 250)"),
                         ("02_loss-1_lan_rule", False, "uplink unimpaired; shown, not used for H"),
                         ("03_loss-5_lan_rule", False, "uplink unimpaired; shown, not used for H"),
                         ("04_burst-50x20_lan_rule", False, "uplink unimpaired; shown, not used for H")]:
    a, b = (ts(x) for x in cells[key]["session"])
    sets.append(measure(f"BENCH-R1 {key}", R1 / "runs" / key / "logs_run1", a, b, clean=clean, note=note))
# cells 5-7 outside the blackouts: [blackout start - 1 s, + 10 s] excluded (BENCH-R1's own window), the room on that hour
blackouts = {"05_blackout-both_plain": ["03:33:35", "03:35:35", "03:37:35", "03:39:35", "03:41:35"],
             "06_blackout-both_hold": ["03:47:54", "03:49:54", "03:51:54", "03:53:54", "03:55:54"],
             "07_blackout-down_plain": ["04:02:35", "04:04:35", "04:06:35", "04:08:35", "04:10:35"]}
for key, starts in blackouts.items():
    a, b = (ts(x) for x in cells[key]["session"])
    ex = [(ts("2026-10-22T" + s) - 1, ts("2026-10-22T" + s) + 10) for s in starts]
    sets.append(measure(f"BENCH-R1 {key} (outside blackouts)", R1 / "runs" / key / "logs_run1", a, b, ex, clean=False,
                        note="the room outside the shim's blackouts; shown, not used for H"))
UX2 = EV / "ux_r2_2026-10-21" / "session" / "logs" / "games"
ux2_ex = [(ts("2026-10-21T04:54:50"), ts("2026-10-21T04:55:05")),           # the death (UX-R3)
          (ts("2026-10-21T05:08:58"), ts("2026-10-21T05:09:21")),           # the user's Zelda pause
          (ts("2026-10-21T05:22:54"), ts("2026-10-21T05:23:06"))]           # the user's SotN pause / save
sets.append(measure("UX-R2 clean minutes (04:42-05:27Z less the death, the two user pauses, session edges)", UX2,
                    ts("2026-10-21T04:42:00"), ts("2026-10-21T05:27:00"), ux2_ex, clean=True,
                    note="the user's evening, real play"))
UX1 = EV / "ux_r1_2026-10-20" / "session" / "logs" / "games"
sets.append(measure("UX-R1 whole evening (Sunday, 04:19-05:23Z)", UX1, ts("2026-10-20T04:19:00"),
                    ts("2026-10-20T05:23:00"), clean=False, note="the bad evening; shown, not used for H"))

clean = [s for s in sets if s["clean"]]
pooled_s = sum(s["streaming_s"] for s in clean)
cand = []
for h in range(250, 2001, 50):
    per = [s["ge_per10"][h] for s in clean]
    pooled = round(sum(s["ge"][h] for s in clean) * 600.0 / pooled_s, 2)
    cand.append({"H": h, "per_session": per, "max": max(per), "pooled": pooled})
H = next(c["H"] for c in cand if c["max"] <= 1.0)
H_pooled = next(c["H"] for c in cand if c["pooled"] <= 1.0)

death = [967, 546, 442, 350, 342]
bursts = {}
for name, x, y in [("Sunday step 04:56-05:05", "04:56:00", "05:05:00"), ("Sunday burst 05:06", "05:06:00", "05:07:00"),
                   ("Sunday burst 05:10-05:11", "05:10:00", "05:12:00"), ("Sunday burst 05:20-05:21", "05:20:00", "05:22:00")]:
    a, b = ts("2026-10-20T" + x), ts("2026-10-20T" + y)
    ms = [round((e - s) * 1000) for s, e in gaps(UX1) if a <= s < b and e - s >= 0.25]
    bursts[name] = {"gaps": len(ms), "ge_H": sum(1 for m in ms if m >= H), "ge_250": len(ms), "longest": max(ms),
                    "silent_ms_ge_H": sum(m for m in ms if m >= H), "silent_ms_all": sum(ms)}
res = {"bins_ms": BINS, "edge_excluded_s": EDGE_S, "sets": sets, "candidates": cand, "H_chosen": H,
       "H_if_pooled": H_pooled, "death_gaps_ms": death, "death_caught_at_H": [m for m in death if m >= H], "bursts": bursts}
(HERE / "gap_distribution.json").write_text(json.dumps(res, indent=1) + "\n")

L = ["# B6 — every uplink silence >= 250 ms on file: the distribution, and H", "",
     "From the control-gap logs (E3-R2's, one row per client->host silence > 250 ms) in the evidence copies, read-only "
     f"(`gap_distribution.py` -> `gap_distribution.json`). Per 10 min = over seconds with frames on the host. {EDGE_S:.0f} s "
     "at every session start / end excluded (start-up, teardown). **Clean sessions (chosen before computing, the "
     "queue's list): BENCH-R1 cells 1 and 8; UX-R2's evening less the death, the two user pauses and session edges.** "
     "The CL-B5/6/7 windows have no gap log (it exists only since E3-R2). Everything else is shown, not used.", "",
     "| session | clean | streaming s | gaps >= 250 | per 10 min | " + " | ".join(f"{k} ms" for k in sets[0]["bins"]) + " | longest ms |",
     "| --- | --- | ---: | ---: | ---: | " + " | ".join("---:" for _ in sets[0]["bins"]) + " | ---: |"]
for s in sets:
    L.append(f"| {s['name']} | {'**yes**' if s['clean'] else 'no'} | {s['streaming_s']} | {s['gaps']} | {s['per10']} | "
             + " | ".join(f"{v} ({s['bins_per10'][k]})" for k, v in s["bins"].items()) + f" | {s['max_ms']} |")
L += ["", "Cells: count (per 10 min).", "", "**Gaps >= H per 10 min, the clean sessions (cell 1 / cell 8 / UX-R2), max, pooled:**", "",
      "| H ms | cell 1 | cell 8 | UX-R2 clean | max | pooled |", "| ---: | ---: | ---: | ---: | ---: | ---: |"]
for c in cand:
    if c["H"] <= 1200 or c["H"] % 250 == 0:
        L.append(f"| {c['H']} | " + " | ".join(str(v) for v in c["per_session"]) + f" | {c['max']} | {c['pooled']} |")
L += ["", f"**H chosen = {H} ms**: the smallest value (50-ms grid) with <= 1 gap >= H per 10 min on each clean session. "
      f"(Pooled over the three, the rule would give {H_pooled} ms.)", "",
      f"**The death's five gaps (967 / 546 / 442 / 350 / 342 ms): H = {H} holds {len(res['death_caught_at_H'])} of them "
      f"({', '.join(map(str, res['death_caught_at_H'])) or 'none'})**; each is held from H to its end.", "",
      "| Sunday window | gaps >= 250 | gaps >= H | longest ms | silent ms in gaps >= H / all |", "| --- | ---: | ---: | ---: | ---: |"]
for k, v in bursts.items():
    L.append(f"| {k} | {v['gaps']} | {v['ge_H']} | {v['longest']} | {v['silent_ms_ge_H']} / {v['silent_ms_all']} |")
(HERE / "gap_distribution.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
