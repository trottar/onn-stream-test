#!/usr/bin/env python3
"""E3-A3 §1 -- the user's nft check (2026-10-09 00:11-00:18Z, r3b_run.sh, v2 in e3_flag.conf), read in place from
d_base_r3b_2026-09-21/V2-*/ (cited, not copied) and logs/games/native_stream_ctrl_gaps.log. Read-only.
-> nft_table.md, nft_table.json, nft_gap_lines.jsonl (the gap lines 00:11-00:18Z, the only copy made: a log excerpt)"""
import json
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
R3B = os.path.join(REPO, "docs/memory/evidence/d_base_r3b_2026-09-21")
GAPS = [os.path.join(REPO, "logs/games/native_stream_ctrl_gaps.log.1"), os.path.join(REPO, "logs/games/native_stream_ctrl_gaps.log")]
RUNS = [("V2-N3", "host->client 48100,48101, 3 s"), ("V2-N15", "host->client 48100,48101, 15 s"),
        ("V2-C2", "client->host 48102, 2 s"), ("V2-C8", "client->host 48102, 8 s")]
tt = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
utc = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%H:%M:%S.%f")[:-3] + "Z"

gaps = []
for f in GAPS:
    if os.path.exists(f):
        for l in open(f):
            r = json.loads(l)
            if "2026-10-09T00:11" <= r["start_utc"] <= "2026-10-09T00:18:59":
                gaps.append(r)
with open(os.path.join(HERE, "nft_gap_lines.jsonl"), "w") as fh:
    fh.writelines(json.dumps(g) + "\n" for g in gaps)
out, md = {}, ["| run | fault | t_on → t_off (UTC; s) | recovery events (offset from t_on / t_off) | gap lines > 1 s in the fault window (start offset from t_on; gap ms; burst) |",
               "| --- | --- | --- | --- | --- |"]
for name, fault in RUNS:
    d = os.path.join(R3B, name)
    t = dict(l.strip().split("=", 1) for l in open(os.path.join(d, "timings.txt")) if "=" in l)
    on, off = float(t["t_on"]), float(t["t_off"])
    ev = [json.loads(l) for l in open(os.path.join(d, "recovery_lines.jsonl"))]
    evs = [{"at_utc": e["at_utc"], "event": e["event"], "trigger": e.get("trigger"), "via": e.get("via"),
            "from_on_s": round(tt(e["at_utc"]) - on, 2), "from_off_s": round(tt(e["at_utc"]) - off, 2)}
           for e in ev if e["event"] not in ("session_started", "session_ended")]
    g = [x for x in gaps if on - 1 <= tt(x["start_utc"]) <= off + 1]
    out[name] = {"fault": fault, "t_on_utc": utc(on), "t_off_utc": utc(off), "fault_s": round(off - on, 2), "events": evs,
                 "gaps": [{"start_from_on_s": round(tt(x["start_utc"]) - on, 3), "gap_ms": x["gap_ms"], "burst_500ms": x["burst_500ms"]} for x in g],
                 "files": sorted(os.listdir(d))}
    e_txt = "; ".join(f"{e['event']}{' ' + e['trigger'] if e['trigger'] else ''}{' via ' + e['via'] if e['via'] else ''} "
                      f"({e['from_on_s']:+.2f} / {e['from_off_s']:+.2f})" for e in evs) or "**none**"
    g_txt = "; ".join(f"{x['start_from_on_s']:+.2f} s; {x['gap_ms']}; {x['burst_500ms']}" for x in out[name]["gaps"] if x["gap_ms"] > 1000) or "none > 1 s"
    md.append(f"| {name} | {fault} | {utc(on)} → {utc(off)}; {off - on:.2f} | {e_txt} | {g_txt} |")
json.dump(out, open(os.path.join(HERE, "nft_table.json"), "w"), indent=1)
open(os.path.join(HERE, "nft_table.md"), "w").write("\n".join(md) + "\n")
print("\n".join(md))
print(len(gaps), "gap lines 00:11-00:18Z")
