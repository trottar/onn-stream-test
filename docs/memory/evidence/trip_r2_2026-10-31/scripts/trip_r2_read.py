#!/usr/bin/env python3
"""TRIP-R2: Friday 2026-10-30's play, from the copies only (read-only).

    python3 -I trip_r2_read.py   -> ../tables/*.md, ../tables/*.tsv, ../seconds/*.tsv beside this script

Inputs: ../copies/ (the keeper's chunks joined; the keeper's directory is never opened for writing).
UX-R3's hitch definition, unchanged: a UTC second is a hitch second if
  R  the heartbeat interval ending in it rendered < 50 fps;
  C  a host control gap >= 250 ms starts in it;
  G  an output gap >= 200 ms is recorded in it (the ladder sample's output_gap_ms, or a client-report top-16 gap
     placed by the client's elapsed clock);
  L  the heartbeat interval ending in it lost >= 30 packets after FEC.
The user's own exits (a control gap containing a session_end_bye) are not hitches.
Titles appear as class + short tag only.
"""
import bisect, glob, json, os, re, statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))
C = os.path.join(OUT, "copies")
T0, T1 = "2026-10-30T21:00:00", "2026-10-31T06:10:00"

# game id prefix (first 4 hex of the library id, as in the game log's filename) -> class + tag
TAGS = {"04ff": "PS1 platformer", "ee3b": "SNES action-adventure", "2ef9": "PS1 first-person RPG",
        "3699": "PS1 football (Blitz)", "7bf5": "PS1 brawler", "6d53": "PS1 kart racer", "33df": "PS1 golf",
        "9f2b": "PS1 hockey A", "e2cd": "PS1 hockey B"}
EPISODES = [  # (label, start, end) placed by the rows (see the reading)
    ("E4 movie", "2026-10-30T21:18:00", "2026-10-30T21:23:00"),
    ("E3 Blitz", "2026-10-31T01:07:00", "2026-10-31T01:25:00"),
    ("E3 Blitz", "2026-10-31T03:32:00", "2026-10-31T04:10:00"),
    ("E1 restarts + E2 golf", "2026-10-31T04:13:00", "2026-10-31T04:47:00"),
]


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)


def sec(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S")


def hms(t):
    return t.strftime("%H:%M:%S")


def jl(p):
    for line in open(p, errors="replace"):
        line = line.strip()
        if line.startswith("{"):
            try:
                yield json.loads(line)
            except ValueError:
                pass


def inwin(t):
    return ts(T0) <= t < ts(T1)


# ---------------------------------------------------------------- the logs
rec = [r for r in jl(os.path.join(C, "native_stream_recovery.log")) if inwin(ts(r["at_utc"]))]
lad = [r for r in jl(os.path.join(C, "adaptive_bitrate_shadow.jsonl")) if inwin(ts(r["at_utc"]))]
hb = [r for r in jl(os.path.join(C, "native_stream_heartbeat.log")) if inwin(ts(r["received_at_utc"]))]
gaps = [r for r in jl(os.path.join(C, "native_stream_ctrl_gaps.log")) if inwin(ts(r["start_utc"]))]
fsz = {r["at_utc"][:19]: r for r in jl(os.path.join(C, "native_frame_sizes.jsonl")) if inwin(ts(r["at_utc"]))}
host = [r for r in jl(os.path.join(C, "host_resource_samples.jsonl")) if inwin(ts(r["at_utc"]))]
ovl = [r for r in jl(os.path.join(C, "overlay.jsonl")) if inwin(ts(r["at_utc"]))]
reports = []
for f in sorted(glob.glob(os.path.join(C, "decoder_sessions", "*.json"))):
    d = json.load(open(f))
    if inwin(ts(d["received_at_utc"])):
        reports.append(d)

# game launches from the game logs' names (local EDT = UTC-4)
wan = [r for r in jl(os.path.join(C, "wan_sessions.jsonl"))]


def rtt_for(s):
    """The WAN row closed between this session's end and the next session's start (G5-S1's close)."""
    if not s["end"]:
        return ""
    i = sessions.index(s)
    a = (s["end"] - datetime(1970, 1, 1)).total_seconds() - 30
    nxt = sessions[i + 1]["start"] if i + 1 < len(sessions) else s["end"] + timedelta(hours=2)
    b = (nxt - datetime(1970, 1, 1)).total_seconds() + 5
    for r in wan:
        if a <= r.get("closed_unix_s", 0) <= b:
            v = ((r.get("measures") or {}).get("rtt_ms") or {}).get("value") or {}
            return f"{v.get('p50')}/{v.get('p95')}"
    return ""


launches = []
for f in sorted(glob.glob(os.path.join(C, "game_logs", "*.log"))):
    m = re.match(r"(\d{8})-(\d{6})-game_([a-z0-9]+)_([0-9a-f]{4})", os.path.basename(f))
    t = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S") + timedelta(hours=4)
    core = "snes9x" if m.group(3) == "snes" else "beetle-psx-hw"
    launches.append((t, TAGS.get(m.group(4), m.group(3) + " ?"), core))


def title_at(t):
    cur = None
    for lt, tag, core in launches:
        if lt <= t + timedelta(seconds=60):
            cur = (tag, core)
    return cur or ("?", "?")


# ---------------------------------------------------------------- client sessions (recovery log)
sessions = []
cur = None
last_cfg = None
for r in rec:
    t, ev = ts(r["at_utc"]), r["event"]
    if ev == "remote_config":
        last_cfg = r
    elif ev == "session_started":
        cur = {"start": t, "class": (last_cfg or {}).get("class"), "events": [], "end": None, "end_kind": None}
        sessions.append(cur)
    elif cur is not None:
        cur["events"].append(r)
        if ev == "session_end_bye":
            cur["bye"] = True
        if ev == "session_ended" and cur["end"] is None:
            cur["end"] = t
        if ev == "restart_fast" and cur.get("end_kind") is None and cur["end"] and (t - cur["end"]).total_seconds() < 2:
            cur["end_kind"] = "client restart (restart_fast)"
        if ev == "gave_up_saved":
            cur["end_kind"] = "link loss: gave up, saved"
            cur["end"] = cur["end"] or t
        if ev == "ended_after_link_loss":
            cur["end"] = cur["end"] or t
for s in sessions:
    if s["end_kind"] is None:
        s["end_kind"] = "user exit (bye)" if s.get("bye") else "?"
    s["tag"], s["core"] = title_at(s["start"])
# restart_fast rows not attached to a PLAYING session (the 04:34:41 start that never reached session_started)
restarts = [r for r in rec if r["event"] == "restart_fast"]

# heartbeat segments (counters cumulative per client session)
segs = []
for r in hb:
    if not segs or r["sequence"] <= segs[-1][-1]["sequence"]:
        segs.append([])
    segs[-1].append(r)


def seg_for(s):
    best = None
    for g in segs:
        a, b = ts(g[0]["received_at_utc"]), ts(g[-1]["received_at_utc"])
        if a <= (s["end"] or a) and b >= s["start"] - timedelta(seconds=10):
            ov = (min(b, s["end"] or b) - max(a, s["start"])).total_seconds()
            if best is None or ov > best[0]:
                best = (ov, g)
    return best[1] if best else []


def offset(g):
    """UTC - client elapsed, the median over the segment."""
    return statistics.median([(ts(r["received_at_utc"]) - datetime(1970, 1, 1)).total_seconds() - r["elapsed_ms"] / 1000
                              for r in g]) if g else None


def report_for(s):
    best = None
    for d in reports:
        rt = ts(d["received_at_utc"])
        if s["end"] and abs((rt - s["end"]).total_seconds()) < 5:
            best = d
    return best


# ---------------------------------------------------------------- per-second evidence
hitch = defaultdict(set)
row = defaultdict(dict)
for g in segs:
    prev = None
    for r in g:
        t = ts(r["received_at_utc"])
        k = sec(t)
        if prev is not None:
            dt = (r["elapsed_ms"] - prev["elapsed_ms"]) / 1000
            if dt > 0:
                fps = (r["rendered_frames"] - prev["rendered_frames"]) / dt
                lost = r["lost_packets"] - prev["lost_packets"]
                row[k].update(fps=round(fps, 1), lost=lost, rssi=r["link_rssi_dbm"],
                              underruns=r["audio_underruns"] - prev["audio_underruns"],
                              starv=r["audio_prolonged_starvation_events"] - prev["audio_prolonged_starvation_events"],
                              resync=r["stream_resyncs"] - prev["stream_resyncs"], out_age=r["last_output_age_ms"])
                if fps < 50:
                    hitch[k].add("R")
                if lost >= 30:
                    hitch[k].add("L")
        prev = r
bye_times = [ts(r["at_utc"]) for r in rec if r["event"] in ("session_end_bye",)]
for gp in gaps:
    a, b = ts(gp["start_utc"]), ts(gp["end_utc"])
    user = any(a - timedelta(seconds=1) <= bt <= b for bt in bye_times)
    k = sec(a)
    row[k]["ctrl_gap_ms"] = max(row[k].get("ctrl_gap_ms", 0), gp["gap_ms"])
    row[k]["ctrl_gap_user"] = user
    if not user:
        hitch[k].add("C")
for r in lad:
    k = r["at_utc"][:19]
    if r.get("event") == "sample":
        row[k].update(rung=r.get("stream_kbps"), lstate=r.get("state"), ogap=r.get("output_gap_ms"),
                      wfi=r.get("waiting_for_idr"))
        if (r.get("output_gap_ms") or 0) >= 200:
            hitch[k].add("G")
    elif r.get("event") in ("transition", "session_ended_reset"):
        row[k].setdefault("ladder_ev", []).append(
            r["event"] + (f" {r.get('from_kbps')}->{r.get('to_kbps')}" if r["event"] == "transition" else ""))
for r in rec:
    k = r["at_utc"][:19]
    row[k].setdefault("rec", []).append(r["event"] + (f"({r.get('trigger')})" if r.get("trigger") else ""))
# client-report gaps by the client's clock
report_gaps = []
report_disc = []
for s in sessions:
    d = report_for(s)
    off = offset(seg_for(s))
    if not d or off is None:
        continue
    rp = d["report"]
    for x in rp.get("slow_events_top_gap", []):
        t = datetime(1970, 1, 1) + timedelta(seconds=off + x[0] / 1000)
        report_gaps.append((t, x[6], s))
        if x[6] >= 200:
            hitch[sec(t)].add("G")
            row[sec(t)]["report_gap_ms"] = max(row[sec(t)].get("report_gap_ms", 0), x[6])
    for x in rp.get("stream_discontinuities", []):
        t = datetime(1970, 1, 1) + timedelta(seconds=off + x["elapsed_ms"] / 1000)
        report_disc.append((t, x["type"], s))
        row[sec(t)]["disc"] = x["type"]

# ---------------------------------------------------------------- tables
os.makedirs(os.path.join(OUT, "tables"), exist_ok=True)
os.makedirs(os.path.join(OUT, "seconds"), exist_ok=True)
transitions = [r for r in lad if r.get("event") == "transition"]
stalls = [r for r in rec if r["event"] == "client_stall"]


def in_span(t, a, b):
    return a <= t < b


def summarize(a, b):
    """Counts for [a, b)."""
    out = {}
    hs = [k for k in hitch if a <= ts(k) < b]
    out["hitch_s"] = len(hs)
    out["hitch_by"] = {c: sum(1 for k in hs if c in hitch[k]) for c in "RCGL"}
    gs = [g for g in gaps if a <= ts(g["start_utc"]) < b]
    out["silences"] = sum(1 for g in gs if not any(ts(g["start_utc"]) - timedelta(seconds=1) <= bt <= ts(g["end_utc"]) for bt in bye_times))
    out["silences_user"] = len(gs) - out["silences"]
    out["max_silence_ms"] = max([g["gap_ms"] for g in gs], default=0)
    lost = und = starv = res = 0
    fpsl = []
    rssi = []
    for k, v in row.items():
        if a <= ts(k) < b and "fps" in v:
            lost += v["lost"]; und += v["underruns"]; starv += v["starv"]; res += v["resync"]
            fpsl.append(v["fps"]); rssi.append(v["rssi"])
    out.update(lost=lost, underruns=und, starvation=starv, resyncs=res,
               fps_med=round(statistics.median(fpsl), 1) if fpsl else None,
               fps_min=round(min(fpsl), 1) if fpsl else None,
               rssi=f"{min(rssi)}..{max(rssi)}" if rssi else "")
    out["stream_s"] = len({k for k, v in row.items() if a <= ts(k) < b and "fps" in v}) * 2
    out["transitions"] = [f"{hms(ts(r['at_utc']))} {r['from_kbps']}->{r['to_kbps']}" for r in transitions if a <= ts(r["at_utc"]) < b]
    out["stalls"] = [f"{hms(ts(r['at_utc']))} {r['age_ms']}ms" for r in stalls if a <= ts(r["at_utc"]) < b]
    out["restarts"] = [hms(ts(r["at_utc"])) for r in restarts if a <= ts(r["at_utc"]) < b]
    ev = [r for r in rec if a <= ts(r["at_utc"]) < b]
    out["pauses"] = [f"{hms(ts(r['at_utc']))} {r.get('trigger')}" for r in ev if r["event"] == "desync_pause"]
    out["holds"] = sum(1 for r in ev if r["event"].startswith("input_hold"))
    out["byes"] = sum(1 for r in ev if r["event"] == "session_end_bye")
    out["resets"] = sum(1 for r in lad if r.get("event") == "session_ended_reset" and a <= ts(r["at_utc"]) < b)
    rungs = sorted({v["rung"] for k, v in row.items() if a <= ts(k) < b and v.get("rung")})
    out["rungs"] = "/".join(map(str, rungs))
    return out


# sessions table
lines = ["| # | start UTC | end UTC | length | title (class + tag) | core | path | rungs reached (transitions) | end | "
         "resets | loss post-FEC | rendered fps med (min) | resyncs | stalls | pauses | holds | hitch s (R/C/G/L) | "
         "silences (user) | underruns | starvation | RSSI dBm | RTT ms p50/p95 (control echo) |",
         "| --- " * 22 + "|"]
tsv = ["n\tstart\tend\tlength_s\ttitle\tcore\tpath\ttransitions\tend_kind\tresets\tlost\tfps_med\tfps_min\tresyncs\t"
       "stalls\tpauses\tholds\thitch_s\tR\tC\tG\tL\tsilences\tsilences_user\tunderruns\tstarvation\trssi"]
for i, s in enumerate(sessions, 1):
    end = s["end"] or s["start"]
    m = summarize(s["start"], end + timedelta(seconds=1))
    tr = ", ".join(m["transitions"]) or "—"
    L = (end - s["start"]).total_seconds()
    lines.append(f"| {i} | {hms(s['start'])} | {hms(end)} | {int(L // 60)}:{int(L % 60):02d} | {s['tag']} | {s['core']} | "
                 f"{(s['class'] or '').replace('remote-', '')} | {tr} | {s['end_kind']} | {m['resets']} | {m['lost']} | "
                 f"{m['fps_med']} ({m['fps_min']}) | {m['resyncs']} | {', '.join(m['stalls']) or '—'} | "
                 f"{', '.join(m['pauses']) or '—'} | {m['holds']} | {m['hitch_s']} ({'/'.join(str(m['hitch_by'][c]) for c in 'RCGL')}) | "
                 f"{m['silences']} ({m['silences_user']}) | {m['underruns']} | {m['starvation']} | {m['rssi']} | {rtt_for(s)} |")
    tsv.append("\t".join(map(str, [i, sec(s["start"]), sec(end), int(L), s["tag"], s["core"], s["class"], tr, s["end_kind"],
                                   m["resets"], m["lost"], m["fps_med"], m["fps_min"], m["resyncs"], ";".join(m["stalls"]),
                                   ";".join(m["pauses"]), m["holds"], m["hitch_s"], *[m["hitch_by"][c] for c in "RCGL"],
                                   m["silences"], m["silences_user"], m["underruns"], m["starvation"], m["rssi"], rtt_for(s)])))
open(os.path.join(OUT, "tables", "sessions.md"), "w").write("\n".join(lines) + "\n")
open(os.path.join(OUT, "tables", "sessions.tsv"), "w").write("\n".join(tsv) + "\n")

# per-10-min table
lines = ["| 10 min from (UTC) | stream s | sessions started | client restarts | user exits | transitions | stalls | "
         "pauses | hitch s (R/C/G/L) | silences | max silence ms | loss | fps med (min) | underruns | starvation | rungs | RSSI | episode |",
         "| --- " * 18 + "|"]
t = ts(T0)
while t < ts(T1):
    b = t + timedelta(minutes=10)
    m = summarize(t, b)
    started = sum(1 for s in sessions if t <= s["start"] < b)
    ep = "; ".join(sorted({lab for lab, ea, eb in EPISODES if ts(ea) < b and ts(eb) > t}))
    if m["stream_s"] or started or ep:
        lines.append(f"| {t.strftime('%m-%d %H:%M')} | ~{m['stream_s']} | {started} | {len(m['restarts'])} | {m['byes']} | "
                     f"{len(m['transitions'])} | {len(m['stalls'])} | {len(m['pauses'])} | {m['hitch_s']} "
                     f"({'/'.join(str(m['hitch_by'][c]) for c in 'RCGL')}) | {m['silences']} | {round(m['max_silence_ms'])} | "
                     f"{m['lost']} | {m['fps_med']} ({m['fps_min']}) | {m['underruns']} | {m['starvation']} | {m['rungs']} | "
                     f"{m['rssi']} | {ep} |")
    t = b
open(os.path.join(OUT, "tables", "per_10min.md"), "w").write("\n".join(lines) + "\n")

# per hour: restarts, stalls, transitions
lines = ["| hour (UTC) | stream min | client restarts | stalls | transitions | top rung | silences | hitch s | loss |",
         "| --- " * 9 + "|"]
t = ts(T0)
while t < ts(T1):
    b = t + timedelta(hours=1)
    m = summarize(t, b)
    if m["stream_s"]:
        lines.append(f"| {t.strftime('%m-%d %H')}:00 | {round(m['stream_s'] / 60)} | {len(m['restarts'])} | {len(m['stalls'])} | "
                     f"{len(m['transitions'])} | {m['rungs'].split('/')[-1]} | {m['silences']} | {m['hitch_s']} | {m['lost']} |")
    t = b
open(os.path.join(OUT, "tables", "per_hour.md"), "w").write("\n".join(lines) + "\n")

# step-ups: the client's discontinuity and output gap after each transition
lines = ["| transition (host) | session | client discontinuity Δt s | largest client output gap within 5 s (ms) | "
         "host client_stall within 5 s |", "| --- " * 5 + "|"]
for r in transitions:
    tt = ts(r["at_utc"])
    d = [x for x in report_disc if 0 <= (x[0] - tt).total_seconds() < 5]
    g = [x[1] for x in report_gaps if 0 <= (x[0] - tt).total_seconds() < 5]
    st = [x for x in stalls if 0 <= (ts(x["at_utc"]) - tt).total_seconds() < 5]
    sess = next((i for i, s in enumerate(sessions, 1) if s["start"] <= tt <= (s["end"] or tt)), "?")
    lines.append(f"| {hms(tt)} {r['from_kbps']}->{r['to_kbps']} | {sess} | "
                 f"{', '.join(f'{(x[0] - tt).total_seconds():+.1f} {x[1]}' for x in d) or 'no report row'} | "
                 f"{max(g) if g else '<190 or not in the top 16'} | "
                 f"{', '.join(f'{hms(ts(x['at_utc']))} {x['age_ms']} ms' for x in st) or '—'} |")
open(os.path.join(OUT, "tables", "stepups.md"), "w").write("\n".join(lines) + "\n")

# every client restart and the 5 s (and 10 s) before it
lines = []
for r in restarts:
    tt = ts(r["at_utc"])
    lines.append(f"### restart_fast {hms(tt)}\n")
    lines.append("| UTC | recovery | ladder | ctrl gap ms | fps | out age ms | rung | output gap ms | disc |")
    lines.append("| --- " * 9 + "|")
    for k in sorted(row):
        kt = ts(k)
        if tt - timedelta(seconds=10) <= kt <= tt + timedelta(seconds=2):
            v = row[k]
            if any(x in v for x in ("rec", "ladder_ev", "ctrl_gap_ms", "fps", "disc", "report_gap_ms")) or v.get("ogap", 0) >= 100:
                lines.append(f"| {hms(kt)} | {', '.join(v.get('rec', []))} | {', '.join(v.get('ladder_ev', []))} | "
                             f"{round(v['ctrl_gap_ms']) if 'ctrl_gap_ms' in v else ''} | {v.get('fps', '')} | {v.get('out_age', '')} | "
                             f"{v.get('rung', '')} | {v.get('ogap', '')}{(' / report ' + str(v['report_gap_ms'])) if 'report_gap_ms' in v else ''} | "
                             f"{v.get('disc', '')} |")
    prev_tr = [x for x in transitions if ts(x["at_utc"]) <= tt]
    lines.append(f"\nlast transition before: {hms(ts(prev_tr[-1]['at_utc']))} {prev_tr[-1]['from_kbps']}->{prev_tr[-1]['to_kbps']} "
                 f"(Δt {(tt - ts(prev_tr[-1]['at_utc'])).total_seconds():.0f} s)\n" if prev_tr else "\n")
open(os.path.join(OUT, "tables", "restarts_5s.md"), "w").write("\n".join(lines) + "\n")

# per-second views
cols = ["utc", "hitch", "fps", "lost", "out_age", "resync", "underruns", "starv", "rssi", "ctrl_gap_ms", "ctrl_gap_user",
        "rung", "lstate", "ogap", "wfi", "report_gap_ms", "disc", "tx_frames", "tx_packets", "ladder_ev", "rec", "overlay"]
ov_by_min = {r["at_utc"][:16]: r for r in ovl}


def write_seconds(name, a, b):
    out = ["\t".join(cols)]
    t = a
    while t <= b:
        k = sec(t)
        v = row.get(k, {})
        f = fsz.get(k, {})
        o = ov_by_min.get(k[:16]) if t.second == 0 else None
        out.append("\t".join(str(x) for x in [
            k, "".join(sorted(hitch.get(k, ()))), v.get("fps", ""), v.get("lost", ""), v.get("out_age", ""), v.get("resync", ""),
            v.get("underruns", ""), v.get("starv", ""), v.get("rssi", ""), round(v["ctrl_gap_ms"]) if "ctrl_gap_ms" in v else "",
            v.get("ctrl_gap_user", ""), v.get("rung", ""), v.get("lstate", ""), v.get("ogap", ""), v.get("wfi", ""),
            v.get("report_gap_ms", ""), v.get("disc", ""), f.get("frames", ""), f.get("packets", ""),
            ";".join(v.get("ladder_ev", [])), ";".join(v.get("rec", [])),
            (f"{o.get('path')}/{o.get('connected')}" if o else "")]))
        t += timedelta(seconds=1)
    open(os.path.join(OUT, "seconds", name), "w").write("\n".join(out) + "\n")


write_seconds("golf_041300_044700.tsv", ts("2026-10-31T04:13:00"), ts("2026-10-31T04:47:00"))
for r in restarts:
    tt = ts(r["at_utc"])
    write_seconds(f"restart_{tt.strftime('%H%M%S')}_pm60.tsv", tt - timedelta(seconds=60), tt + timedelta(seconds=60))
for r in stalls:
    tt = ts(r["at_utc"])
    write_seconds(f"stall_{tt.strftime('%H%M%S')}_pm60.tsv", tt - timedelta(seconds=60), tt + timedelta(seconds=60))

json.dump({"sessions": len(sessions), "restart_fast": [hms(ts(r["at_utc"])) for r in restarts],
           "client_stall": [(hms(ts(r["at_utc"])), r["age_ms"]) for r in stalls],
           "transitions": len(transitions),
           "session_ended_reset": sum(1 for r in lad if r.get("event") == "session_ended_reset"),
           "session_ended_reset_0400_0438": sum(1 for r in lad if r.get("event") == "session_ended_reset"
                                                and ts("2026-10-31T04:00") <= ts(r["at_utc"]) < ts("2026-10-31T04:38")),
           "hitch_s_total": sum(1 for k in hitch if inwin(ts(k))),
           "overlay_paths": sorted({str(r.get("path")) for r in ovl}),
           "heartbeat_rows": len(hb), "ctrl_gaps": len(gaps)},
          open(os.path.join(OUT, "tables", "counts.json"), "w"), indent=1)
print("ok", len(sessions), "sessions;", len(restarts), "restarts;", len(stalls), "stalls")
