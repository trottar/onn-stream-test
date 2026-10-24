#!/usr/bin/env python3
"""CL-B10 stage 3's reader (read-only over cl_b10_2026-10-23/runs/; writes p2_record_read.json and prints).
Silences >= 250 ms per 10 min (B6's gap_distribution.py `measure`, exec'd unedited) and hitch seconds per 10 min (UX-R3's
`evening` / `counts`, exec'd unedited; both asserted against LINK-R1's pins) over named spans of cells 1 and 4:
  cell 1 (5 GHz): its playing spans (session_started .. the Home silence's onset / session_ended);
  cell 4: 2.4 GHz from PLAYING to the switch's silence onset; 5 GHz from the new session's start to session_ended.
Plus the per-blackout rows of cells 2 and 3 from their recovery logs, and the link keys per span.
    python3 -B cl_b10_p2_read.py
"""
import collections, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE.parent
UX = EV / "ux_r3_2026-10-21/ux_r3_seconds.py"
GD = EV / "b6_2026-10-22/gap_distribution.py"
PINS = {l.split()[1].rsplit("/", 1)[-1]: l.split()[0] for l in (EV / "link_r1_2026-10-23/tools_at_preregistration_sha256.txt").read_text().splitlines()}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(UX) == PINS["ux_r3_seconds.py"] and sha(GD) == PINS["gap_distribution.py"]
src = UX.read_text(); UXNS = {"__file__": str(UX)}
exec(compile(src[:src.index("out, L = {}, []")], str(UX), "exec"), UXNS)
gsrc = GD.read_text(); GDNS = {"__file__": str(GD)}
exec(compile(gsrc[:gsrc.index("R1 = EV /")], str(GD), "exec"), GDNS)


def ts(v):
    return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()


def utc(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def span(cell, name, a, b):
    ld = HERE / "runs" / cell / "logs_run1"
    g = GDNS["measure"](name, ld, ts(a), ts(b))
    rows, _, cover, play_s = UXNS["evening"]({"dir": str(ld), "start": a[:19], "end": b[:19]})
    h = UXNS["counts"](rows, play_s)
    hb = [x for x in jl(ld / "native_stream_heartbeat.log") if ts(a) <= ts(x["received_at_utc"]) <= ts(b)]
    c = lambda k: dict(sorted(collections.Counter(x.get(k) for x in hb).items(), key=lambda kv: str(kv[0])))
    return {"name": name, "span": [a, b], "streaming_s": g["streaming_s"], "silences": g["gaps"], "silences_per10": g["per10"],
            "bins": g["bins"], "max_ms": g["max_ms"], "hitch": h, "heartbeats": len(hb), "freq": c("link_frequency_mhz"),
            "rssi": c("link_rssi_dbm"), "tx": c("link_tx_mbps"), "notice": c("link_notice")}


res = {"spans": [
    span("1_snes_5ghz_restart_guard", "cell 1, 5 GHz, before Home", "2026-10-24T03:35:03.259Z", "2026-10-24T03:38:37.649Z"),
    span("1_snes_5ghz_restart_guard", "cell 1, 5 GHz, after the return", "2026-10-24T03:38:50.765Z", "2026-10-24T03:39:12.155Z"),
    span("1_snes_5ghz_restart_guard", "cell 1, 5 GHz, the user's re-entry", "2026-10-24T03:41:48.983Z", "2026-10-24T03:42:21.100Z"),
    span("4_snes_24ghz_notice", "cell 4, 2.4 GHz", "2026-10-24T03:54:46.080Z", "2026-10-24T04:04:29.878Z"),
    span("4_snes_24ghz_notice", "cell 4, 5 GHz after the switch", "2026-10-24T04:05:01.224Z", "2026-10-24T04:09:18.035Z"),
]}
bl = {}
for cell in ("2_snes_blackout_both_state_stall", "3_snes_blackout_down_state_stall"):
    rows, cur = [], None
    for r in jl(HERE / "runs" / cell / "logs_run1/native_stream_recovery.log"):
        e = r["event"]
        if e == "desync_pause":
            cur = {"pause_at": r["at_utc"][11:23], "pause_age_ms": r.get("age_ms"), "trigger": r.get("trigger")}
            rows.append(cur)
            prev_save = saves[-1] if (saves := [x for x in jl(HERE / "runs" / cell / "logs_run1/native_stream_recovery.log")
                                                if x["event"] == "state_saved" and ts(x["at_utc"]) <= ts(r["at_utc"])]) else None
            cur["save_kind"], cur["save_after_onset_ms"] = (prev_save or {}).get("kind"), (prev_save or {}).get("save_after_onset_ms")
        elif cur is not None and e in ("input_release", "resumed", "encoder_restart", "recovery_escalation", "stall_end_late"):
            if e == "input_release":
                cur.update({"method": r.get("method"), "load_ack": r.get("load_ack"), "frames_restored": r.get("frames_restored"),
                            "net": r.get("net_unattended_frames"), "onset_to_pause_ms": r.get("onset_to_pause_ms")})
            elif e == "resumed":
                cur.update({"via": r.get("via"), "packets_back_to_resume_ms": r.get("packets_back_to_resume_ms"),
                            "recovering_ms": r.get("recovering_ms"), "restarts": r.get("restarts")})
            else:
                cur[e] = cur.get(e, 0) + 1
    bl[cell] = rows
res["blackouts"] = bl
(HERE / "p2_record_read.json").write_text(json.dumps(res, indent=1) + "\n")
for s in res["spans"]:
    print(s["name"], "| s", s["streaming_s"], "| silences", s["silences"], "per10", s["silences_per10"], "max", s["max_ms"],
          "| hitch", s["hitch"].get("hitch_seconds"), "per10", s["hitch"].get("per_10_min"), "longest", s["hitch"].get("longest_run_s"),
          "| hb", s["heartbeats"], "freq", s["freq"], "notice", s["notice"], "rssi", s["rssi"])
for c, rows in bl.items():
    print(c)
    for r in rows:
        print(" ", json.dumps(r))
