#!/usr/bin/env python3
"""E1-S1 -- read-only: in E1-CONC, does the stream's loss sit at the end of each EPG grab (the companion-side
work after the grabber child exits) or across the whole grab (the child's run)? Per 2-s heartbeat interval:
lost packets, against the time since the current grab started and the time to its end."""
import json, glob, os, statistics, sys, calendar, time
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
def t(s):
    s = s.rstrip("Z"); a, _, b = s.partition(".")
    return calendar.timegm(time.strptime(a, "%Y-%m-%dT%H:%M:%S")) + (float("0." + b) if b else 0)
for run in (1, 2):
    d = json.load(open(f"{HERE}/runs/E1-CONC/run{run}/summary.json"))
    w0, w1 = t(d["window"]["from"]), t(d["window"]["to"])
    grabs = [json.loads(l) for l in open(f"{HERE}/runs/E1-CONC/run{run}/epg.jsonl")]
    grabs = [(t(g["start_utc"]), t(g["end_utc"])) for g in grabs if g["kind"] == "grab"]
    hb = []
    for f in sorted(glob.glob(REPO + "/logs/games/stream_log_archive/native_stream_heartbeat.log*")) + [REPO + "/logs/games/native_stream_heartbeat.log"]:
        for l in open(f, errors="replace"):
            try: r = json.loads(l)
            except ValueError: continue
            if "lost_packets" in r and w0 <= t(r["received_at_utc"]) <= w1: hb.append(r)
    hb.sort(key=lambda r: r["received_at_utc"])
    tail, body = [], []
    for a, b in zip(hb, hb[1:]):
        mid = (t(a["received_at_utc"]) + t(b["received_at_utc"])) / 2
        lost = b["lost_packets"] - a["lost_packets"]
        g = next(((s, e) for s, e in grabs if s <= mid <= e), None)
        if not g: continue
        (tail if g[1] - mid <= 1.5 else body).append(lost)
    print(f"run{run}: intervals in the last 1.5 s of a grab n={len(tail)} lost/interval mean {statistics.mean(tail):.1f} median {statistics.median(tail)}; "
          f"earlier in the grab n={len(body)} mean {statistics.mean(body):.1f} median {statistics.median(body)}")
