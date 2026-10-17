#!/usr/bin/env python3
"""G4-S1 (Part 2): the remote row's runs, read from the files only -- runs/E1-PS1-STREAM-REMOTE/run<n>/ (summary.json,
telemetry.jsonl, status_poll.jsonl, path.jsonl, sampler summary inside summary.json), the companion's heartbeat log
(logs/games/native_stream_heartbeat.log*), recovery log (logs/games/native_stream_recovery.log*), controller-gap log
(logs/games/native_stream_ctrl_gaps.log*) and the session audit (logs/session_audit.jsonl), reduced. Read-only. No
address, token or device id is written: the audit is reduced to time, event, reason, path class, routing evidence,
sig_v, overlay_declared and "paired" / "host-local". -> g4_s1_read.json, g4_s1_table.md, validity.json.

Spans: each run's 600-s window (summary.window); run 2 is also split at the files' own boundaries (the recovery log's
session_ended / session_started around the hotspot toggle) into its overlay part and its later part."""
import glob
import json
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNS = HERE / "runs" / "E1-PS1-STREAM-REMOTE"
LOGS = REPO / "logs"
PLAN_MBIT = (10.0, 11.0)        # ROADMAP §G4's planning figure, outbound
HOME_7000_MBIT = 11.6           # E2-S1 §6: 720p/7000 at home, 1.45 MB/s on the wire
C5M3_4000_MBIT = 5.0            # C5-M3: 720p/4000 passed transport at 5.0 Mbit/s on the wire


def jl(paths):
    out = []
    for p in paths:
        try:
            for l in open(p):
                try:
                    out.append(json.loads(l))
                except ValueError:
                    pass
        except OSError:
            pass
    return out


def logs(name):
    return sorted(glob.glob(str(LOGS / "games" / (name + ".*")))) + [str(LOGS / "games" / name)]


HB = jl(logs("native_stream_heartbeat.log"))
REC = jl(logs("native_stream_recovery.log"))
GAPS = jl(logs("native_stream_ctrl_gaps.log"))


def audit(t0, t1):
    rows = []
    for d in jl([LOGS / "session_audit.jsonl"]):
        if t0 <= d.get("t", "") <= t1:
            cid = d.get("client_id")
            rows.append({**{k: d[k] for k in ("t", "event", "reason", "routing_evidence", "host_local", "sig_v",
                                               "overlay_declared", "media_token_used", "permissions") if k in d},
                         "path": ("/games/box_art/<file>" if str(d.get("path", "")).startswith("/games/box_art/") else d.get("path")),
                         "client": "paired" if str(cid).startswith("dev-") else cid})
    return rows


def span(t0, t1, rd):
    tel = [r for r in jl([rd / "telemetry.jsonl"]) if r.get("fresh") and t0 <= r.get("at_utc", "") <= t1]
    rec = [r.get("receiver") or {} for r in tel]
    lat = [(r.get("latency") or {}).get("control_round_trip_ms") for r in tel]
    lat = [x for x in lat if isinstance(x, (int, float))]
    mins = (len(tel) * 2) / 60 if tel else 0
    lost = sum(r.get("lost_packets_delta") or 0 for r in rec)
    hb = [h for h in HB if t0 <= h.get("received_at_utc", "") <= t1]

    def hbdelta(key):
        tot, prev = 0, None
        for h in hb:                       # cumulative per stream session; a drop = a new session
            v = h.get(key)
            if not isinstance(v, (int, float)):
                continue
            if prev is not None:
                tot += v - prev if v >= prev else v
            prev = v
        return tot
    hb_mins = (len(hb) * 2) / 60 if hb else 0
    rec_hb, lost_hb, unrec = hbdelta("fec_recovered_packets"), hbdelta("lost_packets"), hbdelta("fec_unrecoverable_groups")
    good = [r.get("recent_mbps") for r in rec if isinstance(r.get("recent_mbps"), (int, float))]
    return {"from": t0, "to": t1, "reports": len(tel), "minutes_of_reports": round(mins, 2),
            "goodput_kbps_mean": round(1000 * statistics.mean(good), 1) if good else None,
            "post_fec_lost_per_min_telemetry": round(lost / mins, 2) if mins else None,
            "rtt_ms_median": statistics.median(lat) if lat else None,
            "rtt_ms_p95": sorted(lat)[int(0.95 * (len(lat) - 1))] if lat else None,
            "heartbeats": len(hb), "post_fec_lost_per_min_heartbeat": round(lost_hb / hb_mins, 2) if hb_mins else None,
            "fec_recovered_per_min_heartbeat": round(rec_hb / hb_mins, 2) if hb_mins else None,
            "pre_fec_per_min_heartbeat": round((lost_hb + rec_hb) / hb_mins, 2) if hb_mins else None,
            "fec_unrecoverable_groups": unrec,
            "resyncs_heartbeat": hbdelta("stream_resyncs"),
            "audio_underruns_heartbeat": hbdelta("audio_underruns"),
            "recovery_events": [{k: r.get(k) for k in ("at_utc", "event", "state", "trigger") if k in r}
                                for r in REC if t0 <= r.get("at_utc", "") <= t1],
            "ctrl_gaps": [{"start_utc": g.get("start_utc"), "gap_ms": g.get("gap_ms")} for g in GAPS if t0 <= g.get("start_utc", "") <= t1]}


def run(n):
    rd = RUNS / f"run{n}"
    if not (rd / "summary.json").exists():
        return {"run": n, "status": "no summary"}
    s = json.loads((rd / "summary.json").read_text())
    if s.get("status") != "OK" or not s.get("window"):
        return {"run": n, "status": s.get("status"), "error": s.get("error"), "gap": s.get("gap")}
    w = s["window"]
    h = s["host"]["host"]
    g = lambda key: (h.get(key) or {}).get("mean")
    paths = jl([rd / "path.jsonl"])
    inwin = [p for p in paths if w["from"] <= p.get("at_utc", "") <= w["to"]]
    seq = [(p["at_utc"], (p.get("overlay") or {}).get("path")) for p in paths]
    changes = [(t, a, b) for (t0, a), (t, b) in zip(seq, seq[1:]) if a != b]
    lastw = Counter((p.get("wan") or {}).get("last_window") for p in inwin if isinstance(p.get("wan"), dict))
    tx = g("net.tailscale0.tx_kBps")
    out = {"run": n, "status": "OK", "playing_utc": s.get("playing_utc"), "window": w, "endpoint": s.get("endpoint"),
           "profile_at_playing": s.get("profile_at_playing"), "teardown": s.get("teardown"),
           "key": s.get("key"), "retroarch_titles_with_fps": (s["host"].get("retroarch") or {}).get("titles"),
           "host_cpu": g("cpu.mean_pct"), "companion_cpu": g("procs.companion.cpu_pct"),
           "retroarch_cpu": g("procs.retroarch.cpu_pct"), "encoder_cpu": g("procs.encoder.cpu_pct"),
           "overlay_iface_tx_kBps": tx, "overlay_iface_tx_mbit": round(tx * 8 / 1000, 2) if tx else None,
           "lan_iface_tx_kBps": g("net.eno1.tx_kBps"),
           "path_counts_window": dict(Counter((p.get("overlay") or {}).get("path") for p in inwin)),
           "path_changes_all": changes, "wan_last_window_counts": dict(lastw),
           "wan_class_last": ((inwin[-1].get("wan") or {}).get("class") if inwin else None),
           "rung_polls": dict(Counter(r.get("bitrate_kbps") for r in jl([rd / "status_poll.jsonl"]))),
           "full": span(w["from"], w["to"], rd)}
    if n == 2:
        ends = [r["at_utc"] for r in REC if r.get("event") == "session_ended" and w["from"] <= r.get("at_utc", "") <= w["to"]]
        starts = [r["at_utc"] for r in REC if r.get("event") == "session_started" and w["from"] <= r.get("at_utc", "") <= w["to"]]
        if ends:
            out["part_overlay"] = span(w["from"], ends[0], rd)
            if starts:
                out["part_after"] = span(starts[0], w["to"], rd)
                out["outage_s_recovery_log"] = round(
                    (__import__("datetime").datetime.fromisoformat(starts[0].replace("Z", "+00:00"))
                     - __import__("datetime").datetime.fromisoformat(ends[0].replace("Z", "+00:00"))).total_seconds(), 1)
    return out


def main():
    res = [run(n) for n in (1, 2, 3)]
    evening = {"audit": audit("2026-10-16T22:30:00Z", "2026-10-16T23:59:59Z"),
               "recovery_log": [{k: r.get(k) for k in ("at_utc", "event", "state", "trigger") if k in r}
                                for r in REC if "2026-10-16T22:30" <= r.get("at_utc", "") <= "2026-10-16T23:59:59"],
               "heartbeat_sessions": []}
    prev = None
    for h in HB:
        t = h.get("received_at_utc", "")
        if not ("2026-10-16T22:30" <= t <= "2026-10-16T23:59:59"):
            continue
        e = h.get("elapsed_ms") or 0
        if prev is None or e < prev[1]:
            evening["heartbeat_sessions"].append({"first": t, "last": t, "beats": 1})
        else:
            evening["heartbeat_sessions"][-1].update(last=t, beats=evening["heartbeat_sessions"][-1]["beats"] + 1)
        prev = (t, e)
    doc = {"runs": res, "evening": evening,
           "planning": {"plan_mbit": PLAN_MBIT, "home_7000_mbit": HOME_7000_MBIT, "c5m3_4000_mbit": C5M3_4000_MBIT}}
    (HERE / "g4_s1_read.json").write_text(json.dumps(doc, indent=1, default=str) + "\n")
    (HERE / "validity.json").write_text(json.dumps(
        {f"run{r['run']}": ("valid (PLAYING over the overlay)" if r.get("status") == "OK" and (r.get("endpoint") or {}).get("class") == "overlay"
                            else ("not started" if r.get("status") in ("FAILED", "no summary") else r.get("status"))) for r in res}, indent=1) + "\n")
    print(json.dumps(doc, indent=1, default=str)[:12000])


if __name__ == "__main__":
    main()
