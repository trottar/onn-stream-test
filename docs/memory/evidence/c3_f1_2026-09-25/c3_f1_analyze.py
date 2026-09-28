#!/usr/bin/env python3
"""C3-F1: score the four sessions against c3_f1_preregistration.txt. Read-only.

Per level: sessions.json (the driver's record), report_<level>.json (the
client's decoder report), heartbeat_<level>.jsonl (host received time vs the
client's elapsed_ms, to put the restart on the client clock).
"""
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
S1_MEDIAN_GAP_MS = 186.5
WINDOW_S = 3.0


def ts(s):
    return datetime.strptime(s[:23], "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp()


sessions = [s for s in json.loads((HERE / "sessions.json").read_text()) if "level" in s]
rows = []
print("C3-F1 -- the four restarts")
for s in sessions:
    lv = s["level"]
    rep = json.loads((HERE / f"report_{lv}.json").read_text())["report"]
    hb = [json.loads(l) for l in open(HERE / f"heartbeat_{lv}.jsonl")]
    # client elapsed = host epoch + offset (median over heartbeats)
    offs = [r["elapsed_ms"] / 1000.0 - ts(r["received_at_utc"]) for r in hb]
    off = statistics.median(offs)
    t_client = ts(s["restart"]["at_utc"]) + off
    disc = [x for x in rep["stream_discontinuities"] if x.get("type") == "ssrc_change"]
    near = [(i, x) for i, x in enumerate(rep["stream_discontinuities"])
            if x.get("type") == "ssrc_change" and -1.0 <= x["elapsed_ms"] / 1000.0 - t_client <= WINDOW_S]
    idr = rep.get("first_idr_after_discontinuity") or []
    gap = None
    idr_row = None
    if len(near) == 1:
        i, x = near[0]
        e0 = x["elapsed_ms"]
        idr_row = idr[i] if i < len(idr) else None
        cols = rep["slow_event_columns"]
        E, G = cols.index("elapsed_ms"), cols.index("output_gap_ms")
        ev = rep["slow_events_ge_50_ms"] + rep["slow_events_top_gap"]
        inwin = [r[G] for r in ev if 0 <= r[E] - e0 <= 1000]
        gap = max(inwin) if inwin else None
    rr = s["restart"]
    ok = (rr["http"] == 200 and rr.get("ok") is True and s["bitrate_before_restart"] == lv
          and s["bitrate_after_restart"] == lv and rr.get("target") in (lv, None) and len(near) == 1
          and s["journal"]["native_stream_start_posts"] <= 1
          and not any(e.get("method") == "full_start" for e in s["recovery_events"]))
    ev = [e["event"] for e in s["recovery_events"]]
    row = dict(level=lv, http=rr["http"], ok=rr.get("ok"), schema=rr.get("schema"), mode=rr.get("mode"),
               before=s["bitrate_before_restart"], after=s["bitrate_after_restart"],
               recent_mbps=s.get("recent_mbps_after_restart"), ssrc_total=len(disc),
               ssrc_near_restart=len(near), idr=(idr_row or {}).get("resync_to_idr_ms"), gap_ms=gap,
               first_rtp_resume_ms=(rr.get("video") or {}).get("first_rtp_resume_ms"),
               native_stream_start_posts=s["journal"]["native_stream_start_posts"],
               full_start=any(e.get("method") == "full_start" for e in s["recovery_events"]),
               session_started=ev.count("session_started"), session_ended=ev.count("session_ended"),
               any_override=s.get("any_override_at_playing"), bitrate_at_end=s.get("bitrate_at_end"),
               game_active_after=s.get("game_active_after"), restart_ok=ok, alpha=s.get("alpha_log"))
    rows.append(row)
    print(json.dumps({k: v for k, v in row.items() if k != "alpha"}))
    for l in row["alpha"]:
        print("   log:", l)
print()
by = {r["level"]: r for r in rows}
w7000 = by.get(7000, {}).get("restart_ok")
others = [lv for lv in (6000, 5500, 5000) if not by.get(lv, {}).get("restart_ok")]
if w7000 and not others and len(rows) == 4:
    out = "WORKING"
elif not w7000:
    out = "BROKEN"
else:
    out = f"PARTIAL (failed: {others})"
gaps = [r["gap_ms"] for r in rows if r["gap_ms"] is not None]
print(f"restart output gaps ms: {[(r['level'], r['gap_ms']) for r in rows]} vs S1 median {S1_MEDIAN_GAP_MS} "
      f"(not a gate); more than double: {[g for g in gaps if g > 2 * S1_MEDIAN_GAP_MS]}")
print(f"OUTCOME: {out}")
