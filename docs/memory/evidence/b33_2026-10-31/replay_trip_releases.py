#!/usr/bin/env python3
"""B33: every input_release of the trip (Friday 2026-10-30/31, TRIP-R2) through rewind_needs_loss.Rule.decide, with the
heartbeats the host had received by each release. Read-only: reads ../trip_r2_2026-10-31/copies/ (the keeper's
redacted copies). The uplink term reads the host's controller-sequence counter, which no log keeps: it is given as
not recorded, with the ctrl-gap rows that overlap the episode beside it. Usage: replay_trip_releases.py COMPANION_DIR"""
import json, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, sys.argv[1])
import rewind_needs_loss as rnl  # noqa: E402

C = Path(__file__).resolve().parent.parent / "trip_r2_2026-10-31" / "copies"
ts = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
rec = [json.loads(x) for x in (C / "native_stream_recovery.log").read_text().splitlines() if x.strip()]
hbs = [json.loads(x) for x in (C / "native_stream_heartbeat.log").read_text().splitlines() if x.strip()]
gaps = [json.loads(x) for x in (C / "native_stream_ctrl_gaps.log").read_text().splitlines() if x.strip()]
hbs.sort(key=lambda r: r["received_at_utc"])
out = []
for i, r in enumerate(rec):
    if r["event"] not in ("input_release", "rewind_skipped", "rewind_failed"):
        continue
    decision = ts(r["at_utc"]) - (r.get("rewind_ms") or 0.0) / 1000.0
    save = next((s for s in reversed(rec[:i]) if s["event"] == "state_saved"), None)
    onset = ts(save["at_utc"]) - save["save_after_onset_ms"] / 1000.0
    rule = rnl.Rule(controller=None, clock=lambda: 0.0)
    for h in hbs:
        t = ts(h["received_at_utc"])
        if decision - 20 <= t <= decision:
            rule.note_heartbeat(h, now=t)
    rule.controller = type("C", (), {"_lost_packets": 0})()      # the uplink term: not recorded (held flat here)
    for s in rule._hb:
        s["uplink"] = 0
    resume, why, d = rule.decide(onset, now=decision)
    ov = [g for g in gaps if ts(g["start_utc"]) <= decision and ts(g["end_utc"]) >= onset - 2.5]
    nxt = next((h for h in hbs if ts(h["received_at_utc"]) > decision), None)
    prev = [h for h in hbs if ts(h["received_at_utc"]) <= decision]
    after = None
    if nxt is not None and prev:
        p = prev[-1]
        after = {"received_after_release_ms": round((ts(nxt["received_at_utc"]) - decision) * 1000.0),
                 "lost_packets": nxt["lost_packets"] - p["lost_packets"],
                 "fec_unrecoverable_groups": nxt["fec_unrecoverable_groups"] - p["fec_unrecoverable_groups"],
                 "stream_resyncs": nxt["stream_resyncs"] - p["stream_resyncs"]}
    out.append({"release_utc": r["at_utc"], "event": r["event"], "via": r.get("via"), "method_then": r.get("method"),
                "net_unattended_frames": r.get("net_unattended_frames"), "onset_utc_from_save": save["at_utc"],
                "new_rule": "resume" if resume else "load", "why": why, **d,
                "uplink": "not recorded (held flat); ctrl gaps overlapping [onset-2.5 s, release]: "
                          + (", ".join(f"{g['gap_ms']} ms (+{g['burst_500ms']} pkts in the 500 ms after)" for g in ov) or "none"),
                "the_next_heartbeat_after_the_release": after})
print(json.dumps(out, indent=1))
