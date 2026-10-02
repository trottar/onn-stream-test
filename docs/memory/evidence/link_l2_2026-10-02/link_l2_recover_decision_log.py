#!/usr/bin/env python3
"""LINK-L2 (written after H4, before H5) -- recover a hold's decision-log slice when the controller log
rotated mid-hold. link_l2_run.sh slices the log by byte offset (`tail -c +MARK`); the companion rotates
adaptive_bitrate_shadow.jsonl at 4 MiB (keep 3), so after a rotation the live file is shorter than the
mark and the slice is empty. This re-slices by time instead: every row of the rotated stream_log_archive/....1 and the live
file whose at_utc lies in [from, to] -- the run's companion restart (before launch) and the moment
the run sliced the log (after BACK), from the hold's log. Read-only on the logs.

    link_l2_recover_decision_log.py <from utc> <to utc> <out.jsonl>
"""
import json, sys
REPO = "/home/privyhub/Projects/onn-stream-test"
t0, t1, out = sys.argv[1:4]
rows, seen = [], set()
for p in (f"{REPO}/logs/games/stream_log_archive/adaptive_bitrate_shadow.jsonl.1", f"{REPO}/logs/games/adaptive_bitrate_shadow.jsonl"):
    for line in open(p, errors="replace"):
        line = line.strip()
        if not line or line in seen:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if t0 <= r.get("at_utc", "")[:19] + "Z" <= t1:
            seen.add(line)
            rows.append(line)
open(out, "w").write("".join(l + "\n" for l in rows))
print(f"[recover] {len(rows)} rows in {t0} .. {t1} -> {out}")
