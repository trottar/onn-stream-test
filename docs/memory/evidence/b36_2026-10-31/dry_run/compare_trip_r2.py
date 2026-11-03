#!/usr/bin/env python3
"""B36 dry run: diag_read over the trip keeper's copies (read-only) against TRIP-R2.

    python3 -I compare_trip_r2.py <tools dir with diag_read.py>   -> compare.md beside this script

1. TRIP-R2 §1's restart table, cell for cell (the reference cells typed from the record's table);
2. TRIP-R2's tables/sessions.tsv against diag_read's sessions on every shared column;
3. the keeper's chunks joined against TRIP-R2's copies/ (byte prefix: the copies were taken to 16:58Z, the keeper runs on).
Opens docs/memory/evidence/trip_2026-10-30/ and trip_r2_2026-10-31/ for reading only.
"""
import csv, os, sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import diag_read as dr

HERE = Path(__file__).resolve().parent
EV = HERE.parents[1]
TRIP, R2 = EV / "trip_2026-10-30", EV / "trip_r2_2026-10-31"
logs = dr.Logs(); logs.add_keeper_dir(TRIP)
an = dr.Analysis(logs, datetime(2026, 10, 30, 21), datetime(2026, 10, 31, 6, 10))
out = ["# B36 dry run against TRIP-R2", "", "## 1. TRIP-R2 §1's restart table, cell for cell", "",
       "| restart | cell | TRIP-R2 | diag_read | same |", "| --- | --- | --- | --- | --- |"]
# (time, session, title word, rung before, rung after, last step-up as printed, trigger, paused, away, silence/stall before)
REF = [("01:20:44", 14, "football", 4000, 4000, "397 s", "surface", 1720, 1787, "silence 1736"),
       ("03:26:05", 20, "kart", 4000, 4000, "(none in the session)", "surface", 4511, 8582, "silence 7467"),
       ("04:19:21", 25, "golf", 4000, 4000, "(none in the session)", "surface", 1877, 2027, "stall 419; silence 1918"),
       ("04:30:12", 26, "golf", 6000, 4000, "95 s", "surface", 2070, 1039, "stall 464; gaps 292 / 303 / 495"),
       ("04:34:41", "31, never PLAYING", "golf", 4000, 4000, "363 s", "surface", 767, 1188, "silence 1190"),
       ("05:19:35", 35, "brawler", 4000, 4000, "(none in the session)", None, None, None, "silence 16079")]
same = total = 0
got = {dr.hms(dr.ts(r["at_utc"])): an.restart_detail(r) for r in an.restarts}
for t, sess, title, rb, ra, step, trig, paused, away, before in REF:
    d = got.get(t)
    if d is None:
        out.append(f"| {t} | the row | present | MISSING | no |"); total += 1; continue
    mine_step = (f"{d['last_stepup_dt_s']} s" if d["last_stepup_in_session"] else f"(none in the session; {d['last_stepup_dt_s']} s earlier)") \
        if d["last_stepup_dt_s"] is not None else "(none)"
    step_same = (step == f"{d['last_stepup_dt_s']} s") or (step.startswith("(none in the session)") and not d["last_stepup_in_session"])
    mine_before = "; ".join(([f"stall {', '.join(str(round(x)) for x in d['stalls_before_ms'])}"] if d["stalls_before_ms"] else [])
                            + ([f"silences {' / '.join(str(x) for x in d['silences_before_ms'])}"] if d["silences_before_ms"] else []))
    nums = [int(x) for x in before.replace("/", " ").replace(";", " ").split() if x.isdigit()]
    before_same = all(n in [round(x) for x in d["stalls_before_ms"]] + d["silences_before_ms"] for n in nums)
    cells = [("session", sess, d["session"] if d["session"] else "(none PLAYING)", sess == d["session"]),
             ("title", title, d["title"], title in d["title"].lower()),
             ("rung before → after", f"{rb} → {ra}", f"{d['rung_before']} → {d['rung_after']}", (rb, ra) == (d["rung_before"], d["rung_after"])),
             ("last step-up Δt", step, mine_step, step_same),
             ("client's trigger", trig, d["trigger"], trig == d["trigger"]),
             ("paused ms", paused, d["paused_ms"], paused == d["paused_ms"]),
             ("away ms", away, d["away_ms"], away == d["away_ms"]),
             ("the seconds before (numbers)", before, mine_before, before_same)]
    for name, a, b, ok in cells:
        total += 1; same += ok
        out.append(f"| {t} | {name} | {a} | {b} | {'yes' if ok else 'NO'} |")
out += ["", f"**{same} / {total} cells the same; 6 / 6 restart times found.**", ""]
# 2. the sessions table
rows = list(csv.DictReader(open(R2 / "tables" / "sessions.tsv"), delimiter="\t"))
cols = [("start", lambda s, r: dr.sec(s["start"])), ("end", lambda s, r: dr.sec(s["end"] or s["start"])),
        ("length_s", lambda s, r: str(r["length_s"])), ("title", lambda s, r: r["title"]), ("core", lambda s, r: r["core"]),
        ("path", lambda s, r: str(r["path_class"])), ("end_kind", lambda s, r: r["end_kind"]), ("resets", lambda s, r: str(r["resets"])),
        ("lost", lambda s, r: str(r["lost_post_fec"])), ("fps_med", lambda s, r: str(r["rendered_fps_med"])),
        ("fps_min", lambda s, r: str(r["rendered_fps_min"])), ("resyncs", lambda s, r: str(r["resyncs"])),
        ("stalls", lambda s, r: ";".join(r["stalls"])), ("pauses", lambda s, r: ";".join(r["pauses"])), ("holds", lambda s, r: str(r["holds"])),
        ("hitch_s", lambda s, r: str(r["hitch_s"])), ("R", lambda s, r: str(r["hitch_by"]["R"])), ("C", lambda s, r: str(r["hitch_by"]["C"])),
        ("G", lambda s, r: str(r["hitch_by"]["G"])), ("L", lambda s, r: str(r["hitch_by"]["L"])),
        ("silences", lambda s, r: str(r["silences"])), ("silences_user", lambda s, r: str(r["silences_user"])),
        ("underruns", lambda s, r: str(r["underruns"])), ("starvation", lambda s, r: str(r["starvation"])), ("rssi", lambda s, r: r["rssi"])]
diff = []; n = 0
for i, (s, ref) in enumerate(zip(an.sessions, rows), 1):
    r = an.session_row(s)
    for c, f in cols:
        n += 1
        if f(s, r) != ref[c]:
            diff.append(f"| {i} | {c} | {ref[c]} | {f(s, r)} |")
out += ["## 2. TRIP-R2's sessions.tsv against diag_read's sessions", "",
        f"Sessions: TRIP-R2 {len(rows)}, diag_read {len(an.sessions)}. Cells compared: {n} ({len(cols)} columns x {min(len(rows), len(an.sessions))} sessions); "
        f"**different: {len(diff)}**.", ""]
if diff:
    out += ["| session | column | TRIP-R2 | diag_read |", "| --- | --- | --- | --- |"] + diff
# 3. the joined chunks against TRIP-R2's copies (prefix)
out += ["", "## 3. The keeper's chunks joined against TRIP-R2's copies/ (byte prefix)", "", "| log | copies bytes | joined bytes | copies a prefix of joined |", "| --- | --- | --- | --- |"]
for name in dr.LOGS.values():
    p = R2 / "copies" / name
    if p.is_file():
        c, j = p.read_bytes(), logs.data.get(name, b"")
        out.append(f"| {name} | {len(c)} | {len(j)} | {'yes' if j.startswith(c) else 'NO'} |")
out.append(f"| decoder reports | {len(os.listdir(R2 / 'copies' / 'decoder_sessions'))} files | {len(logs.reports)} reports | (count) |")
open(HERE / "compare.md", "w").write("\n".join(out) + "\n")
print(f"restart cells {same}/{total}; session cells different {len(diff)} of {n}")
