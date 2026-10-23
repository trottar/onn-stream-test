#!/usr/bin/env python3
"""UX-R4: the per-second view of 2026-10-23 04:54-05:08Z (the user's Zelda session) from session/ (read-only).
UX-R3's `evening` / `counts` / COLS / fmt / key, exec'd unedited (sha256 = BENCH-R2's pin e9b2b3f7...), so the hitch
definition (R / C / G / L, the Pause-menu exclusion) is UX-R3's, unchanged. B6's gap_distribution `measure` for the
silences >= 250 ms. Writes beside this script: seconds_all.tsv (every second), window_<mark>.tsv (mark - 60 s .. + 10 s),
ranked.txt, counts.json.     python3 -B seconds/ux_r4_seconds.py   (from ux_r4_2026-10-23/)"""
import hashlib, json, os
from datetime import datetime, timedelta, timezone
HERE = os.path.dirname(os.path.abspath(__file__))
UXD = os.path.abspath(os.path.join(HERE, ".."))
EV = os.path.abspath(os.path.join(UXD, ".."))
UX = os.path.join(EV, "ux_r3_2026-10-21/ux_r3_seconds.py")
GD = os.path.join(EV, "b6_2026-10-22/gap_distribution.py")
assert hashlib.sha256(open(UX, "rb").read()).hexdigest().startswith("e9b2b3f79286"), "ux_r3_seconds.py changed"
assert hashlib.sha256(open(GD, "rb").read()).hexdigest().startswith("a93d2f57"), "gap_distribution.py changed"
src = open(UX).read(); NS = {"__file__": UX}
exec(compile(src[:src.index("out, L = {}, []")], UX, "exec"), NS)
gsrc = open(GD).read(); GNS = {"__file__": GD}
exec(compile(gsrc[:gsrc.index("R1 = EV /")], GD, "exec"), GNS)
D = os.path.join(UXD, "session/logs/games")
CFG = {"dir": D, "start": "2026-10-23T04:54", "end": "2026-10-23T05:08"}
MARKS = {"save1_045808": "2026-10-23T04:58:08", "save2_050130": "2026-10-23T05:01:30"}
EVENT2 = ("2026-10-23T05:03:20", "2026-10-23T05:04:10")      # the 4.9-s silence after the resume
rows, gaps, cover, play_s = NS["evening"](CFG)
COLS, fmt, key, counts = NS["COLS"], NS["fmt"], NS["key"], NS["counts"]
def dump(path, lo, hi):
    with open(path, "w") as f:
        f.write("utc\t" + "\t".join(COLS) + "\n")
        t = datetime.fromisoformat(lo)
        while t <= datetime.fromisoformat(hi):
            k = t.strftime("%Y-%m-%dT%H:%M:%S")
            r = rows.get(k, {})
            f.write(k + "\t" + "\t".join(fmt(r.get(c)) for c in COLS) + "\n")
            t += timedelta(seconds=1)
dump(os.path.join(HERE, "seconds_all.tsv"), "2026-10-23T04:54:40", "2026-10-23T05:07:15")
out = {"tool_sha256": {"ux_r3_seconds.py": hashlib.sha256(open(UX, "rb").read()).hexdigest(),
                       "gap_distribution.py": hashlib.sha256(open(GD, "rb").read()).hexdigest()},
       "play_s": play_s, "report_coverage": cover, "whole": counts(rows, play_s), "marks": {}}
L = []
def run_before(k_end, k_from):
    """the longest run of consecutive hitch seconds in [k_from, k_end]"""
    best = run = 0; prev = None; best_span = None; start = None
    for k in sorted(x for x, r in rows.items() if r["score"] and k_from <= x <= k_end):
        t = datetime.fromisoformat(k)
        if prev and (t - prev).total_seconds() == 1:
            run += 1
        else:
            run, start = 1, k
        if run > best:
            best, best_span = run, (start, k)
        prev = t
    return best, best_span
for name, m in MARKS.items():
    mt = datetime.fromisoformat(m)
    lo, hi = (mt - timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%S"), (mt + timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%S")
    dump(os.path.join(HERE, f"window_{name}.tsv"), lo, hi)
    secs = [(k, r) for k, r in rows.items() if lo <= k <= hi and r["score"]]
    top = sorted(secs, key=key)
    run, span = run_before(m, lo)
    out["marks"][name] = {"mark": m, "window": [lo, hi], "hitch_seconds": len(secs), "by_score": {s: sum(1 for _, r in secs if r["score"] == s) for s in (1, 2, 3, 4)},
                          "by_criterion": {c: sum(1 for _, r in secs if c in r["crit"]) for c in "RCGL"},
                          "longest_run_before_mark": run, "longest_run_span": span,
                          "ranked": [{"utc": k[11:], **{c: r.get(c) for c in ("crit", "score", "ctrl_gap_max", "out_gap", "post_fec", "rendered_per_s")}} for k, r in top]}
    L.append(f"\n## {name}: mark {m}Z, window {lo[11:]}-{hi[11:]}Z: {len(secs)} hitch seconds; longest run before the mark {run} s {span}")
    L.append("  utc\t" + "\t".join(COLS))
    for k, r in top:
        L.append("  " + k[11:] + "\t" + "\t".join(fmt(r.get(c)) for c in COLS))
dump(os.path.join(HERE, "window_event2_0503.tsv"), *EVENT2)
e2 = sorted(((k, r) for k, r in rows.items() if EVENT2[0] <= k <= EVENT2[1] and r["score"]), key=key)
out["event2"] = {"window": EVENT2, "hitch_seconds": len(e2), "ranked": [{"utc": k[11:], "crit": r["crit"], "ctrl_gap_max": r.get("ctrl_gap_max"),
                 "out_gap": r.get("out_gap"), "post_fec": r.get("post_fec"), "rendered_per_s": r.get("rendered_per_s")} for k, r in e2]}
L.append(f"\n## event 2 {EVENT2[0][11:]}-{EVENT2[1][11:]}Z: {len(e2)} hitch seconds")
for k, r in e2:
    L.append("  " + k[11:] + "\t" + "\t".join(fmt(r.get(c)) for c in COLS))
# per client session and per 10 min: hitch seconds, the longest run, silences >= 250 ms (B6), post-FEC loss
sess = []
rec = list(NS["jl"](os.path.join(D, "native_stream_recovery.log")))
st = [r["at_utc"] for r in rec if CFG["start"] <= r.get("at_utc", "") < CFG["end"] and r["event"] == "session_started"]
en = [r["at_utc"] for r in rec if CFG["start"] <= r.get("at_utc", "") < CFG["end"] and r["event"] == "session_ended"]
hb = [h for h in NS["jl"](os.path.join(D, "native_stream_heartbeat.log")) if CFG["start"] <= h["received_at_utc"] < CFG["end"]]
for i, s in enumerate(st):
    e = min([x for x in en if x > s] + ([st[i + 1]] if i + 1 < len(st) else []) + [CFG["end"]])
    a, b = s[:19], e[:19]
    secs_play = (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds()
    c = counts(rows, secs_play, a, b)
    ta, tb = NS["ts"](s).timestamp(), NS["ts"](e).timestamp()
    g = GNS["measure"](f"session {i + 1}", __import__("pathlib").Path(D), ta, tb)
    lost = sum(r.get("post_fec") or 0 for k, r in rows.items() if a <= k <= b)
    sess.append({"session": i + 1, "from": a[11:], "to": b[11:], "s": round(secs_play), "ended_by": "session_ended" if e in en else "next session_started (no session_ended)",
                 "hitch_seconds": c["hitch_seconds"], "per_10_min": c["per_10_min"], "longest_run_s": c["longest_run_s"], "by": c["by_criterion"],
                 "silences_ge250": g["gaps"], "silences_per10": g["per10"], "silence_max_ms": g["max_ms"], "silence_bins": g["bins"],
                 "post_fec_lost": lost, "lost_per_min": round(lost * 60 / secs_play, 1) if secs_play else None})
out["sessions"] = sess
tot_s = sum(x["s"] for x in sess)
out["whole_per_10min"] = {"play_s": tot_s, "hitch_seconds": sum(x["hitch_seconds"] for x in sess),
                          "hitch_per_10": round(sum(x["hitch_seconds"] for x in sess) * 600 / tot_s, 1),
                          "silences_ge250": sum(x["silences_ge250"] for x in sess),
                          "post_fec_lost_per_min": round(sum(x["post_fec_lost"] for x in sess) * 60 / tot_s, 1)}
L.insert(0, "UX-R4 per-second view\n" + json.dumps({k: v for k, v in out.items() if k in ("whole", "whole_per_10min", "sessions")}, indent=1))
open(os.path.join(HERE, "ranked.txt"), "w").write("\n".join(L) + "\n")
json.dump(out, open(os.path.join(HERE, "counts.json"), "w"), indent=1, default=str)
print("\n".join(L))
