#!/usr/bin/env python3
"""UX-R4 §2: LAN-R2's `bidir` condition (lan_loss_rule.py: T_UNREC 4, K_WINDOWS 2, WINDOW_REPORTS 5, UPLINK_MIN_MS 400,
UPLINK_PER_WINDOW 2) replayed OFFLINE on tonight's heartbeats (the client's 2-s reports, standing in for the ladder's
reports, which carry the same counter) and the host's control-gap log. Not the controller; no ladder gates (floor 5000,
session age) beyond the floor. Read-only.   python3 -B seconds/bidir_replay.py   (from ux_r4_2026-10-23/)"""
import json, os
from datetime import datetime, timezone
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "session/logs/games")
ts = lambda v: datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()
hb = [json.loads(l) for l in open(os.path.join(D, "native_stream_heartbeat.log"))]
hb = [h for h in hb if "2026-10-23T04:54" <= h["received_at_utc"] <= "2026-10-23T05:08"]
gaps = [(ts(g["start_utc"]), g["gap_ms"]) for g in map(json.loads, open(os.path.join(D, "native_stream_ctrl_gaps.log")))
        if "2026-10-23T04:54" <= g["start_utc"] <= "2026-10-23T05:08" and g["gap_ms"] >= 400]
sess, cur = [], []
for h in hb:
    if cur and h["sequence"] <= cur[-1]["sequence"]:
        sess.append(cur); cur = []
    cur.append(h)
sess.append(cur)
fires = []
for s in sess:
    d = [(ts(y["received_at_utc"]), max(0, y["fec_unrecoverable_groups"] - x["fec_unrecoverable_groups"]), ts(x["received_at_utc"])) for x, y in zip(s, s[1:])]
    for i in range(9, len(d)):
        win = [d[i - 9:i - 4], d[i - 4:i + 1]]
        un = [sum(u for _, u, _ in w) for w in win]
        up = [sum(1 for t, _ in gaps if w[0][2] <= t < w[-1][0]) for w in win]
        if all(u >= 4 for u in un) and all(n >= 2 for n in up):
            fires.append({"at": datetime.fromtimestamp(d[i][0], timezone.utc).strftime("%H:%M:%S"), "unrec_windows": un, "uplink_ge400_windows": up})
out = {"condition": "each of 2 consecutive 5-report windows: unrec >= 4 AND uplink silences >= 400 ms >= 2",
       "would_ask": len(fires), "first": fires[0] if fires else None, "all": fires}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bidir_replay.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
