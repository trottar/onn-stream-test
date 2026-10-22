#!/usr/bin/env python3
"""UX-R3: the per-second view of an evening, from UX-R1's / UX-R2's preserved copies (read-only).

THE HITCH DEFINITION (written before any ranking; one definition for every evening)
A UTC second S is a HITCH SECOND if at least one of these holds:
  R  the heartbeat interval that ENDS in S rendered < 50 frames per second over that interval
     (heartbeat resolution is ~2 s; the interval is credited to the second it ends in, never split);
  C  a host control gap >= 250 ms STARTS in S (event resolution: the gap log records every uplink silence
     >= 250 ms with its start and length);
  G  an output gap >= 200 ms is recorded in S: a row of the client report (its 16 largest gaps over the
     whole session, and its retained >= 50-ms slow events), placed by the client's elapsed clock; or the
     ladder sample's `output_gap_ms` (the client's latest gap at that report, credited to the sample's second);
  L  the heartbeat interval that ENDS in S lost >= 30 packets after FEC.
Excluded, by rule: the user's own pauses. A control gap that contains a client `session_ended` is the Pause
menu (UX-R2 §2), not a hitch; the heartbeat intervals that span a session boundary do not exist (counters reset).
Score = the number of criteria met (0-4). Ties are ordered by the longest control gap, then the output gap,
then the loss. A RUN is consecutive hitch seconds.

Resolutions, as they are (nothing is interpolated):
  heartbeat (rendered, loss, FEC, underruns, concealed, audio arrival gap max, output age)  ~2 s, cumulative
  native_stream_ctrl_gaps.log                                                            per gap >= 250 ms
  native_frame_sizes.jsonl (frames, packets, bytes, max packets, frames >= 40)            1 s
  adaptive_bitrate_shadow.jsonl samples (fps, queue, output gap, loss delta) and states    per report (~2 s)
  native_stream_recovery.log                                                              per event
  decoder report: top-16 output gaps (whole session); >= 50-ms slow events (last 1,024 only);
                  audio tick series (first 400 ticks, ~200 s); arrival holes (last 300 only)

    ux_r3_seconds.py   -> seconds_r2.tsv, seconds_r1.tsv, ranked.txt, counts.json beside this script
"""
import bisect, glob, json, os, statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(EV, "../../.."))
EVENINGS = {
    "R2": {"dir": os.path.join(EV, "ux_r2_2026-10-21/session/logs/games"),
           "start": "2026-10-21T04:42", "end": "2026-10-21T05:27",
           "zelda": ("2026-10-21T04:42:26", "2026-10-21T05:09:21"), "user_window": ("2026-10-21T04:56", "2026-10-21T05:03:59")},
    "R1": {"dir": os.path.join(EV, "ux_r1_2026-10-20/session/logs/games"),
           "start": "2026-10-20T04:19", "end": "2026-10-20T05:23"},
}


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def sec(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S")


def jl(p):
    for line in open(p, errors="replace"):
        try:
            yield json.loads(line)
        except ValueError:
            pass


def evening(cfg):
    D, lo, hi = cfg["dir"], cfg["start"], cfg["end"]
    rows = defaultdict(dict)
    # ---- heartbeats: per-interval deltas inside one client session; also the elapsed -> UTC map ----
    hb = [h for h in jl(os.path.join(D, "native_stream_heartbeat.log")) if lo <= h["received_at_utc"] < hi]
    sessions, cur = [], []
    for h in hb:
        if cur and h["sequence"] <= cur[-1]["sequence"]:
            sessions.append(cur); cur = []
        cur.append(h)
    if cur:
        sessions.append(cur)
    for s in sessions:
        for a, b in zip(s, s[1:]):
            dt = (b["elapsed_ms"] - a["elapsed_ms"]) / 1000
            k = sec(ts(b["received_at_utc"]))
            r = rows[k]
            r["hb_interval_s"] = round(dt, 2)
            r["rendered"] = b["rendered_frames"] - a["rendered_frames"]
            r["rendered_per_s"] = round(r["rendered"] / dt, 1) if dt else None
            r["post_fec"] = b["lost_packets"] - a["lost_packets"]
            r["fec_rec"] = b["fec_recovered_packets"] - a["fec_recovered_packets"]
            r["unrec"] = b["fec_unrecoverable_groups"] - a["fec_unrecoverable_groups"]
            r["underruns"] = b["audio_underruns"] - a["audio_underruns"]
            r["concealed"] = b["audio_concealed_underruns"] - a["audio_concealed_underruns"]
            r["a_gap_max"] = b.get("audio_max_arrival_gap_ms")
            r["out_age"] = b.get("last_output_age_ms")
    # client elapsed -> host UTC, per client session: the median of (received - elapsed) over its heartbeats
    maps = []
    for s in sessions:
        off = statistics.median(ts(h["received_at_utc"]).timestamp() * 1000 - h["elapsed_ms"] for h in s)
        maps.append((ts(s[0]["received_at_utc"]), ts(s[-1]["received_at_utc"]), off))
    # ---- control gaps (every one), recovery rows, session ends ----
    ends = [ts(r["at_utc"]) for r in jl(os.path.join(D, "native_stream_recovery.log"))
            if lo <= r.get("at_utc", "") < hi and r["event"] == "session_ended"]
    gaps = []
    for g in jl(os.path.join(D, "native_stream_ctrl_gaps.log")):
        if lo <= g.get("start_utc", "") < hi:
            st, en = ts(g["start_utc"]), ts(g["end_utc"])
            pause = any(st <= e <= en + timedelta(seconds=1) for e in ends)
            gaps.append({"start": g["start_utc"], "gap_ms": g["gap_ms"], "pause": pause})
            r = rows[sec(st)]
            r.setdefault("ctrl_gaps", []).append(round(g["gap_ms"]) if not pause else f"{round(g['gap_ms'])}(pause)")
            if not pause:
                r["ctrl_gap_max"] = max(r.get("ctrl_gap_max", 0), g["gap_ms"])
    for e in jl(os.path.join(D, "native_stream_recovery.log")):
        if lo <= e.get("at_utc", "") < hi:
            rows[sec(ts(e["at_utc"]))].setdefault("recovery", []).append(e["event"] + (":" + e["trigger"] if e.get("trigger") else ""))
    # ---- frame sizes (1 s) ----
    for f in jl(os.path.join(D, "native_frame_sizes.jsonl")):
        if lo <= f.get("at_utc", "") < hi:
            r = rows[f["at_utc"][:19]]
            r.update({"tx_frames": f["frames"], "tx_packets": f["packets"], "tx_kbytes": round(f["payload_bytes"] / 1000, 1),
                      "tx_max_pk": f["max_packets"], "tx_ge40": f["frames_ge_40"]})
    # ---- ladder rows ----
    for a in jl(os.path.join(D, "adaptive_bitrate_shadow.jsonl")):
        if lo <= a.get("at_utc", "") < hi:
            r = rows[a["at_utc"][:19]]
            if a["event"] == "sample":
                r.update({"lad_fps": a.get("fps"), "lad_q": a.get("queue_depth"), "lad_gap": a.get("output_gap_ms"),
                          "lad_loss": a.get("lost_packets_delta"), "lad_state": a.get("state"), "lad_reason": a.get("reason"),
                          "lad_disp": a.get("disposition"), "level": a.get("level_kbps")})
                if (a.get("output_gap_ms") or 0) >= 200:
                    r["out_gap_ladder"] = a["output_gap_ms"]
            else:
                r.setdefault("lad_events", []).append(f"{a['event']}:{a.get('reason')}:{a.get('level_kbps')}")
    # ---- the client reports: output-gap rows placed by the elapsed map ----
    cover = []
    for p in sorted(glob.glob(os.path.join(D, "decoder_sessions/*.json"))):
        d = json.load(open(p)); rep = d["report"]; end = ts(d["received_at_utc"])
        if not (lo <= d["received_at_utc"] < hi or lo <= sec(end - timedelta(milliseconds=rep["duration_ms"])) < hi):
            continue
        m = [x for x in maps if x[0] - timedelta(seconds=5) <= end <= x[1] + timedelta(seconds=30)]
        if not m:
            continue
        off = m[-1][2]
        se = rep.get("slow_events_ge_50_ms") or []
        cover.append({"report": os.path.basename(p), "slow_events_from": sec(datetime.fromtimestamp((off + se[0][0]) / 1000, timezone.utc)) if se else None,
                      "session_from": sec(end - timedelta(milliseconds=rep["duration_ms"])), "session_to": sec(end),
                      "max_output_gap_ms": rep["decoder"]["max_output_gap_ms"]})
        seen = set()
        for src, evs in (("top16", rep.get("slow_events_top_gap") or []), ("slow", se)):
            for e in evs:
                if e[6] >= 200 and (e[0], e[6]) not in seen:
                    seen.add((e[0], e[6]))
                    k = sec(datetime.fromtimestamp((off + e[0]) / 1000, timezone.utc))
                    rows[k]["out_gap_report"] = max(rows[k].get("out_gap_report", 0), e[6])
                    rows[k].setdefault("out_gap_src", set()).add(src)
    # ---- the score ----
    for k, r in rows.items():
        crit = []
        if r.get("rendered_per_s") is not None and r["rendered_per_s"] < 50:
            crit.append("R")
        if r.get("ctrl_gap_max", 0) >= 250:
            crit.append("C")
        og = max(r.get("out_gap_report", 0), r.get("out_gap_ladder", 0))
        if og >= 200:
            crit.append("G")
        if (r.get("post_fec") or 0) >= 30:
            crit.append("L")
        r["out_gap"] = og or None
        r["crit"] = "".join(crit)
        r["score"] = len(crit)
        if "out_gap_src" in r:
            r["out_gap_src"] = "+".join(sorted(r["out_gap_src"]))
    play_s = sum((ts(s[-1]["received_at_utc"]) - ts(s[0]["received_at_utc"])).total_seconds() + 2 for s in sessions)
    return rows, gaps, cover, play_s


COLS = ["crit", "score", "rendered", "hb_interval_s", "rendered_per_s", "post_fec", "fec_rec", "unrec", "ctrl_gaps",
        "out_gap", "out_gap_src", "underruns", "concealed", "a_gap_max", "out_age", "tx_frames", "tx_packets", "tx_kbytes",
        "tx_max_pk", "tx_ge40", "level", "lad_fps", "lad_q", "lad_gap", "lad_loss", "lad_state", "lad_reason", "lad_events",
        "recovery"]


def fmt(v):
    if isinstance(v, list):
        return ",".join(map(str, v))
    return "" if v is None else str(v)


def key(item):
    k, r = item
    return (-r["score"], -(r.get("ctrl_gap_max") or 0), -(r.get("out_gap") or 0), -(r.get("post_fec") or 0), k)


def counts(rows, play_s, lo=None, hi=None, only=None):
    ks = sorted(k for k, r in rows.items() if r["score"] and (lo is None or lo <= k <= hi)
                and (only is None or any(c in r["crit"] for c in only)))
    run = best = 0
    prev = None
    for k in ks:
        t = datetime.fromisoformat(k)
        run = run + 1 if prev and (t - prev).total_seconds() == 1 else 1
        best = max(best, run); prev = t
    by = defaultdict(int)
    for k in ks:
        for c in rows[k]["crit"]:
            if only is None or c in only:
                by[c] += 1
    return {"hitch_seconds": len(ks), "play_min": round(play_s / 60, 1),
            "per_10_min": round(len(ks) / (play_s / 600), 1) if play_s else None, "longest_run_s": best,
            "by_criterion": dict(by)}


out, L = {}, []
for name, cfg in EVENINGS.items():
    rows, gaps, cover, play_s = evening(cfg)
    with open(os.path.join(HERE, f"seconds_{name.lower()}.tsv"), "w") as f:
        f.write("utc\t" + "\t".join(COLS) + "\n")
        for k in sorted(rows):
            f.write(k + "\t" + "\t".join(fmt(rows[k].get(c)) for c in COLS) + "\n")
    out[name] = {"all": counts(rows, play_s), "G_only": counts(rows, play_s, only="G"),
                 "control_gaps": gaps, "report_coverage": cover}
    L.append(f"\n## {name}: report coverage (slow events retained from; whole-session top-16 always)")
    for c in cover:
        L.append("  " + json.dumps(c))
    L.append(f"\n## {name}: every control gap >= 250 ms (start UTC, ms; pauses marked)")
    L.append("  " + "; ".join(f"{g['start'][11:23]} {round(g['gap_ms'])}{' PAUSE' if g['pause'] else ''}" for g in gaps))
    sets = [("whole evening", None, None)]
    if "zelda" in cfg:
        z0, z1 = cfg["zelda"]
        zs = sum(1 for k in rows if z0 <= k <= z1 and rows[k].get("hb_interval_s")) * 2.0
        out[name]["zelda"] = counts(rows, zs, z0, z1)
        u0, u1 = cfg["user_window"]
        out[name]["user_window"] = counts(rows, (ts(u1 + "Z") - ts(u0 + "Z")).total_seconds(), u0, u1)
        sets.insert(0, ("Zelda session", z0, z1))
    for label, a, b in sets:
        top = sorted(((k, r) for k, r in rows.items() if r["score"] and (a is None or a <= k <= b)), key=key)[:15]
        L.append(f"\n## {name}: top 15 seconds, {label}")
        L.append("  utc\t" + "\t".join(COLS))
        for k, r in top:
            L.append("  " + k[11:] + "\t" + "\t".join(fmt(r.get(c)) for c in COLS))
L.insert(0, "UX-R3 per-second view: counts\n" + json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("control_gaps", "report_coverage")} for k, v in out.items()}, indent=1))
open(os.path.join(HERE, "ranked.txt"), "w").write("\n".join(L) + "\n")
json.dump(out, open(os.path.join(HERE, "counts.json"), "w"), indent=1, default=str)
print("\n".join(L))


# ---- §2 additions: start-up share; the report-only output-gap count, like for like with 2026-09-20 ----
def startup_share(cfg, rows):
    starts = [ts(r["at_utc"]) for r in jl(os.path.join(cfg["dir"], "native_stream_recovery.log"))
              if cfg["start"] <= r.get("at_utc", "") < cfg["end"] and r["event"] == "session_started"]
    hs = [k for k, r in rows.items() if r["score"]]
    n = sum(1 for k in hs if any(0 <= (datetime.fromisoformat(k + "+00:00") - st).total_seconds() < 15 for st in starts))
    return {"hitch_seconds_in_first_15_s_of_a_client_session": n, "client_sessions": len(starts)}


def report_gap_count(paths):
    """Seconds with a report row (top-16 or retained slow event) >= 200 ms, per 10 min of the reports' duration.
    Placed by the report's own clock (end - duration + elapsed); the reports' retention limits are stated."""
    secs, dur, partial = set(), 0.0, 0
    for p in paths:
        d = json.load(open(p)); r = d["report"]; end = ts(d["received_at_utc"])
        start = end - timedelta(milliseconds=r["duration_ms"]); dur += r["duration_ms"] / 1000
        if r.get("slow_event_retained", 0) >= r.get("slow_event_capacity_recent", 1024):
            partial += 1
        for e in (r.get("slow_events_top_gap") or []) + (r.get("slow_events_ge_50_ms") or []):
            if e[6] >= 200:
                secs.add(sec(start + timedelta(milliseconds=e[0])))
    return {"seconds_with_output_gap_ge_200": len(secs), "report_minutes": round(dur / 60, 1),
            "per_10_min": round(len(secs) / (dur / 600), 1) if dur else None, "reports": len(paths),
            "reports_with_slow_list_full (older rows dropped)": partial}


def reports_in(D, lo, hi):
    return [p for p in sorted(glob.glob(os.path.join(D, "decoder_sessions/*.json")))
            if lo <= json.load(open(p))["received_at_utc"] < hi]


extra = {}
for name, cfg in EVENINGS.items():
    rows, _, _, _ = evening(cfg)
    extra[name] = {"startup": startup_share(cfg, rows),
                   "report_only_G": report_gap_count(reports_in(cfg["dir"], cfg["start"], cfg["end"] + ":59"))}
sept = sorted(p for p in glob.glob(os.path.join(ROOT, "logs/games/decoder_sessions/native_decoder_20260920_0[56]*.json"))
              if json.load(open(p))["received_at_utc"] >= "2026-09-20T06:00")
extra["SEPT20"] = {"report_only_G": report_gap_count(sept),
                   "note": "2026-09-20 05:59-06:20Z, the 8 client reports read in place (UX-R2 H5). Its heartbeat and "
                           "control-gap logs have rotated out, so R, C and L cannot be computed; only G, from the reports."}
open(os.path.join(HERE, "counts_extra.json"), "w").write(json.dumps(extra, indent=1))
print("\n## §2 additions\n" + json.dumps(extra, indent=1))
