#!/usr/bin/env python3
"""BENCH-R2's record reader (read-only over bench_r2_2026-10-22/; writes only into record/ and adds each cell's client
report under runs/<cell>/logs_run1/decoder_sessions/, the core's version token masked).

Per cell (the session = the recovery log's session_started .. session_ended):
  - hitch seconds per 10 min and the longest run: UX-R3's `evening` / `counts`, exec'd unedited (sha256 checked);
  - the uplink silences >= 250 ms per 10 min and their length distribution: B6's gap_distribution.py `measure`, exec'd
    unedited from the file (its definitions only, sha256 checked), over the session (10 s at each edge excluded, B6's rule);
  - unattended frames core-running, plain and --net (tools/unattended_frames.py, sha256 = the pre-registration's), whole
    session and per blackout;
  - every hold / release / handover / cap / stall / stall_end / stall_quiet / ready-after-hold / rewind row with timing;
  - the per-blackout table (b1, b2, c1): uplink gaps, client output gaps, heartbeat hold, loss, the recovery rows, the
    hold's age, the resume relative to the link's return (blackout start + 4.0 s), new client sessions, c1's pause relative
    to the client's last frame (the client_stall row's age_ms);
  - the ladder: the rung path, the lan_loss_rule rows (lan_bidir), their uplink_windows;
  - the client report: wifi_lock_* / stall_signal_* / link columns, the video / decoder counters;
  - per minute post-FEC loss and FEC-unrecoverable groups from the heartbeats (the user's 16:05-16:17Z observation).
Blackout times: b1 / b2 from the ~4-s control gaps; c1 (@down) from the client's own >= 3-s output gaps (the client's last
frame before each dark span): BENCH-R1's shim-offset anchor disagreed by ~1.8 s in this run (its offset range 1.7 s), both
kept in the output.      python3 -B record/bench_r2_record_read.py   (from bench_r2_2026-10-22/)
"""
import hashlib, json, re, statistics, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
B = HERE.parent
EV = B.parent
REPO = B.parents[3]
UX = EV / "ux_r3_2026-10-21/ux_r3_seconds.py"
GD = EV / "b6_2026-10-22/gap_distribution.py"
UNATT = REPO / "tools/unattended_frames.py"
TOOLS = {l.split()[1]: l.split()[0] for l in (B / "tools_at_preregistration_sha256.txt").read_text().splitlines()}
CELLS = sorted((json.loads(l) for l in open(B / "cells.jsonl")), key=lambda c: c["n"])
REPORTS = REPO / "logs/games/decoder_sessions"
WIN_BEFORE, WIN_AFTER, REC_AFTER, DARK_S = 1.0, 10.0, 15.0, 4.0
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
OBS = ("2026-10-22T16:05:00", "2026-10-22T16:17:59")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ts(v):
    return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp() if "+" in str(v) or str(v).endswith("Z") \
        else datetime.fromisoformat(str(v)).replace(tzinfo=timezone.utc).timestamp()


def utc(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def jl(p):
    out = []
    try:
        for l in open(p, errors="replace"):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    except OSError:
        pass
    return out


assert sha(UX) == TOOLS["docs/memory/evidence/ux_r3_2026-10-21/ux_r3_seconds.py"], "ux_r3_seconds.py changed"
assert sha(GD) == TOOLS["docs/memory/evidence/b6_2026-10-22/gap_distribution.py"], "gap_distribution.py changed"
assert sha(UNATT) == TOOLS["tools/unattended_frames.py"], "unattended_frames.py changed"
src = UX.read_text()
UXNS = {"__file__": str(UX)}
exec(compile(src[:src.index("out, L = {}, []")], str(UX), "exec"), UXNS)
gsrc = GD.read_text()
GDNS = {"__file__": str(GD)}
exec(compile(gsrc[:gsrc.index("R1 = EV /")], str(GD), "exec"), GDNS)


def copy_reports(cell, ldir):
    d = ldir / "decoder_sessions"
    d.mkdir(exist_ok=True)
    n = []
    for p in sorted(REPORTS.glob("native_decoder_20261022_*.json")):
        j = json.load(open(p))
        if cell["start_utc"] <= j.get("received_at_utc", "") <= cell["end_utc"]:
            s = re.sub(r"(Beetle PSX HW |snes9x )(\d+(?:\.\d+){1,3})", r"\1<version>", json.dumps(j))
            assert not IP.search(s), p.name
            (d / p.name).write_text(s + "\n")
            n.append(p.name)
    return n


def unatt(ldir, a, b, name, windows=()):
    out = {}
    for net in (False, True):
        f = HERE / f"unattended_{name}{'_net' if net else ''}.json"
        cmd = [sys.executable, "-B", str(UNATT), "--logs", str(ldir), "--span", utc(a)[:23], utc(b)[:23], "--json", str(f)]
        for w, x, y in windows:
            cmd += ["--window", w, utc(x)[:23], utc(y)[:23]]
        if net:
            cmd.append("--net")
        subprocess.run(cmd, capture_output=True, check=True, timeout=300)
        out["net" if net else "plain"] = json.loads(f.read_text())
    return out


def report_cols(ldir):
    out = []
    for p in sorted((ldir / "decoder_sessions").glob("*.json")):
        r = json.load(open(p))["report"]
        v, dec = r.get("video") or {}, r.get("decoder") or {}
        out.append({"report": p.name, "duration_s": round((r.get("duration_ms") or 0) / 1000, 1),
                    **{k: r.get(k) for k in r if k.startswith(("wifi_lock", "stall_signal", "link"))},
                    "video": {k: v.get(k) for k in ("lost_packets", "fec_recovered_packets", "fec_unrecoverable_groups",
                                                   "sequence_gap_au_drops", "incomplete_au_drops", "dropped_frames",
                                                   "sequence_resyncs", "idr_frames", "max_frames_between_idr", "frames")},
                    "decoder": {k: dec.get(k) for k in ("rendered_frames", "dropped_frames", "stale_output_drops",
                                                       "timestamp_anomalies", "max_output_gap_ms", "spike_50_ms", "spike_80_ms",
                                                       "codec_name", "hardware_accelerated")}})
    return out


def client_dark_starts(ld):
    """The client's >= 3-s output gaps (its report, placed by UX-R3's elapsed map): start = gap end - gap length."""
    rep = json.load(open(sorted((ld / "decoder_sessions").glob("*.json"))[0]))
    r = rep["report"]
    hb = jl(ld / "native_stream_heartbeat.log")
    end = ts(rep["received_at_utc"])
    s = [h for h in hb if end - r["duration_ms"] / 1000 - 30 <= ts(h["received_at_utc"]) <= end + 5]
    off = statistics.median(ts(h["received_at_utc"]) * 1000 - h["elapsed_ms"] for h in s)
    gi = r["slow_event_columns"].index("output_gap_ms")
    ev = sorted({(e[0], e[gi]) for e in (r.get("slow_events_top_gap") or []) + (r.get("slow_events_ge_50_ms") or []) if e[gi] >= 3000})
    return [(off + el - g) / 1000 for el, g in ev]


def per_minute(hb, a, b):
    """Post-FEC lost and FEC-unrecoverable groups per UTC minute from the heartbeats (deltas within a client session)."""
    rows = {}
    s = [h for h in hb if a - 5 <= ts(h["received_at_utc"]) <= b + 5]
    for x, y in zip(s, s[1:]):
        if y["sequence"] <= x["sequence"]:
            continue
        m = y["received_at_utc"][:16]
        r = rows.setdefault(m, {"lost": 0, "unrec": 0, "fec_rec": 0, "rendered": 0, "s": 0.0})
        r["lost"] += max(0, y["lost_packets"] - x["lost_packets"])
        r["unrec"] += max(0, y["fec_unrecoverable_groups"] - x["fec_unrecoverable_groups"])
        r["fec_rec"] += max(0, y["fec_recovered_packets"] - x["fec_recovered_packets"])
        r["rendered"] += max(0, y["rendered_frames"] - x["rendered_frames"])
        r["s"] += (y["elapsed_ms"] - x["elapsed_ms"]) / 1000
    for r in rows.values():
        r["fps"] = round(r["rendered"] / r["s"], 1) if r["s"] else None
    return rows


def main():
    res = {"tools": {"ux_r3_seconds.py": sha(UX), "gap_distribution.py": sha(GD), "unattended_frames.py": sha(UNATT)},
           "window_s": [-WIN_BEFORE, WIN_AFTER], "cells": {}}
    offsets, pre = [], {}
    for c in CELLS:
        ld = B / "runs" / c["cell"] / "logs_run1"
        rec = jl(ld / "native_stream_recovery.log")
        s0 = next(ts(r["at_utc"]) for r in rec if r["event"] == "session_started")
        s1 = next(ts(r["at_utc"]) for r in reversed(rec) if r["event"] == "session_ended")
        spans = (c.get("shim") or {}).get("dark_spans") or []
        starts = [ts(x["start_utc"]) for x in jl(ld / "native_stream_ctrl_gaps.log") if x["gap_ms"] >= 3500] \
            if c["cell"].startswith(("b1", "b2")) else []
        if starts and len(starts) == len(spans):
            offsets += [st - (s0 + sp["t_s_from"]) for st, sp in zip(starts, spans)]
        pre[c["cell"]] = (ld, rec, s0, s1, spans, starts)
    off = statistics.median(offsets)
    res["shim_offset_s"] = {"median": round(off, 3), "range": [round(min(offsets), 3), round(max(offsets), 3)], "n": len(offsets)}
    for c in CELLS:
        copy_reports(c, pre[c["cell"]][0])
    for c in CELLS:
        ld, rec, s0, s1, spans, starts = pre[c["cell"]]
        if c["cell"].startswith("c1"):
            # the shim-offset anchor (BENCH-R1's method) disagreed by ~1.8 s here (offset range 1.7 s), so c1's blackouts are
            # anchored on the client's own >= 3-s output gaps: their start = the client's last frame before the dark span
            out_anchor = {"shim_offset_starts": [utc(s0 + sp["t_s_from"] + off)[11:23] for sp in spans]}
            starts = client_dark_starts(ld)
            out_anchor["client_output_gap_starts"] = [utc(x)[11:23] for x in starts]
        out = {"anchor": out_anchor if c["cell"].startswith("c1") else None, "n": c["n"], "wid": c["wid"], "spec": c["spec"], "extra": c["extra"], "props": c["props_set"],
               "session": [utc(s0), utc(s1)], "session_min": round((s1 - s0) / 60, 2), "reports": copy_reports(c, ld)}
        # hitch (UX-R3)
        rows, _, cover, play_s = UXNS["evening"]({"dir": str(ld), "start": utc(s0)[:19], "end": utc(s1 + 1)[:19]})
        out["hitch"] = UXNS["counts"](rows, play_s)
        # uplink silences (B6's measure; for the blackout cells also outside the blackouts)
        g = GDNS["measure"](c["cell"], ld, s0, s1)
        out["silences"] = {k: g[k] for k in ("streaming_s", "gaps", "per10", "bins", "bins_per10", "max_ms")}
        out["silences"]["ge_per10"] = {str(h): g["ge_per10"][h] for h in (250, 400, 500, 800, 950, 1000, 1500)}
        if starts:
            ex = [(st - WIN_BEFORE, st + WIN_AFTER) for st in starts]
            g2 = GDNS["measure"](c["cell"] + " outside blackouts", ld, s0, s1, ex)
            out["silences_outside_blackouts"] = {k: g2[k] for k in ("streaming_s", "gaps", "per10", "max_ms")}
        # unattended, plain and --net, whole session and per blackout
        wins = [(f"b{i + 1}", st - WIN_BEFORE, st + WIN_AFTER) for i, st in enumerate(starts)]
        u = unatt(ld, s0, s1, c["cell"], wins)
        P, N = u["plain"], u["net"]
        out["unattended"] = {k: P.get(k) for k in ("streaming_s", "gaps", "episodes", "unattended_frames_core_running",
                                                     "unattended_frames_core_running_per_10min", "recovery_paused_spans")}
        out["unattended_net"] = {k: v for k, v in (N.get("net") or {}).items() if k != "episodes"}
        # the recovery rows
        keep = ("at_utc", "event", "trigger", "via", "age_ms", "held_ms", "client_frame", "in_gate", "requested_frames",
                "rewound_frames", "onset_to_pause_ms", "counter_before", "counter_after", "reason", "recovering_ms")
        rr = [{k: r.get(k) for k in keep if r.get(k) is not None} for r in rec if not r["event"].endswith("_config")]
        out["recovery_rows_n"] = len(rr)
        ev = {}
        for r in rec:
            k = r["event"] + (":" + r["trigger"] if r.get("trigger") else "") + (":" + r["via"] if r.get("via") else "")
            ev[k] = ev.get(k, 0) + 1
        out["recovery_events"] = ev
        mins = (s1 - s0) / 60
        per10 = lambda n: round(n * 10 / mins, 2) if mins else None
        holds = [r for r in rec if r["event"] == "desync_pause" and r.get("trigger") == "input_hold"]
        stalls = [r for r in rec if r["event"] == "desync_pause" and r.get("trigger") == "client_stall"]
        out["holds"], out["holds_per10"] = len(holds), per10(len(holds))
        out["stall_pauses"], out["stall_pauses_per10"] = len(stalls), per10(len(stalls))
        out["rewind_failed"] = sum(1 for r in rec if r["event"] == "rewind_failed")
        out["rewind_ok"] = [{k: r.get(k) for k in ("at_utc", "requested_frames", "rewound_frames")} for r in rec
                            if r["event"] == "input_release" and r.get("rewound_frames") is not None]
        out["rewind_failed_requested"] = sorted(r.get("requested_frames") for r in rec if r["event"] == "rewind_failed")
        out["rewind_failed_reasons"] = sorted({re.sub(r"\d+", "N", str(r.get("reason"))) for r in rec if r["event"] == "rewind_failed"})
        if c["cell"][:2] in ("b1", "b2", "c1", "d1", "d2", "f2", "f4"):
            out["recovery_rows"] = rr
        # per blackout
        if starts:
            hb = [h for h in jl(ld / "native_stream_heartbeat.log") if s0 <= ts(h["received_at_utc"]) <= s1 + 1]
            gl = jl(ld / "native_stream_ctrl_gaps.log")
            lad = [a for a in jl(ld / "adaptive_bitrate_shadow.jsonl") if a.get("event") == "sample"]
            neteps = (N.get("net") or {}).get("episodes") or []
            table = []
            for (name, a, b), st in zip(wins, starts):
                ret = st + DARK_S
                gg = [x for x in gl if a <= ts(x["start_utc"]) <= b]
                secs = [rows[k] for k in rows if a <= ts(k) <= b]
                arr = [ts(h["received_at_utc"]) for h in hb if a - 4 <= ts(h["received_at_utc"]) <= b + 4]
                ia = [round(y - x, 2) for x, y in zip(arr, arr[1:])]
                rw = [r for r in rec if a <= ts(r["at_utc"]) <= st + REC_AFTER and not r["event"].endswith("_config")]
                rows_t = [f"{round(ts(r['at_utc']) - st, 2):+.2f} {r['event']}" + (f":{r['trigger']}" if r.get("trigger") else "")
                          + (f":{r['via']}" if r.get("via") else "")
                          + (f" age {r['age_ms']}" if r.get("age_ms") is not None else "")
                          + (f" held {r['held_ms']}" if r.get("held_ms") is not None else "")
                          + (f" req {r['requested_frames']}" if r.get("requested_frames") is not None else "")
                          + (f" rew {r['rewound_frames']}" if r.get("rewound_frames") is not None else "") for r in rw]
                resumes = [ts(r["at_utc"]) for r in rw if r["event"] == "resumed"]
                first_stall = next((r for r in rw if r["event"] == "desync_pause" and r.get("trigger") == "client_stall"), None)
                first_pause = next((r for r in rw if r["event"] == "desync_pause"), None)
                ne = sum(e["unattended_frames_core_running_net"] for e in neteps if a <= ts(e["start"]) <= b)
                uw = P["windows"][name]
                table.append({"blackout": name, "start_utc": utc(st)[11:23], "s_into_session": round(st - s0, 1),
                              "uplink_gaps_n": len(gg), "uplink_gap_longest_ms": max((x["gap_ms"] for x in gg), default=0),
                              "output_gap_report_max_ms": max((r.get("out_gap_report", 0) for r in secs), default=0),
                              "output_gap_ladder_max_ms": max((x.get("output_gap_ms") or 0 for x in lad if a <= ts(x["at_utc"]) <= b), default=0),
                              "heartbeat_max_interarrival_s": max(ia, default=None),
                              "post_fec_lost": sum(r.get("post_fec") or 0 for r in secs), "fec_unrec_groups": sum(r.get("unrec") or 0 for r in secs),
                              "hitch_seconds": sum(1 for r in secs if r.get("score")),
                              "unattended_core_running": uw["unattended_frames_core_running"], "unattended_raw": uw["unattended_frames"],
                              "unattended_net": round(ne, 1),
                              "first_pause_s": round(ts(first_pause["at_utc"]) - st, 2) if first_pause else None,
                              "first_pause_trigger": first_pause.get("trigger") if first_pause else None,
                              "first_pause_age_ms": first_pause.get("age_ms") if first_pause else None,
                              "first_stall_age_ms": first_stall.get("age_ms") if first_stall else None,
                              "first_stall_s": round(ts(first_stall["at_utc"]) - st, 2) if first_stall else None,
                              "holds": sum(1 for r in rw if r.get("trigger") == "input_hold" and r["event"] == "desync_pause"),
                              "stall_end_resumes": sum(1 for r in rw if r["event"] == "resumed" and r.get("via") == "stall_end"),
                              "resumes": len(resumes), "last_resume_after_return_s": round(max(resumes) - ret, 2) if resumes else None,
                              "first_resume_after_return_s": round(min(x for x in resumes if x >= ret) - ret, 2) if any(x >= ret for x in resumes) else None,
                              "rewind_failed": sum(1 for r in rw if r["event"] == "rewind_failed"),
                              "new_sessions": sum(1 for r in rw if r["event"] == "session_started"),
                              "rows": rows_t})
            out["blackouts"] = table
        # the ladder
        ladr = jl(ld / "adaptive_bitrate_shadow.jsonl")
        out["transitions"] = [{"at": r["at_utc"][11:19], "from": r.get("from_kbps"), "to": r.get("to_kbps"), "reason": r.get("reason")}
                              for r in ladr if r.get("event") == "transition" and r.get("acted")]
        out["lan_rule_rows"] = [{k: r.get(k) for k in ("at_utc", "source", "unrec_windows", "uplink_windows", "ladder_result")}
                                for r in ladr if r.get("event") == "lan_loss_rule"]
        # the report
        out["report"] = report_cols(ld)
        out["host"] = {k: c.get(k) for k in ("host_gates", "host_gates_met", "retroarch_fps", "capture_fps", "dupdrop_per_min",
                                              "host_cpu", "companion_cpu", "encoder_cpu", "retroarch_cpu", "retroarch_rss_kb",
                                              "retroarch_rss_kb_max", "mem_available_mb", "mem_available_mb_min")}
        out["stream"] = {k: c.get(k) for k in ("loss_per_min", "rendered_fps", "resyncs", "max_output_gap_ms", "client_pauses",
                                                "fec_recovered", "fec_unrecoverable", "audio_underruns", "spikes50")}
        if c["cell"].startswith(("e1", "e2")):
            hb_all = jl(ld / "native_stream_heartbeat.log")
            pm = per_minute(hb_all, ts(OBS[0]), ts(OBS[1]))
            out["observation_per_minute"] = dict(sorted(pm.items()))
        res["cells"][c["cell"]] = out
    (HERE / "record_read.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps({"shim_offset_s": res["shim_offset_s"]}))
    for name, o in res["cells"].items():
        print(f"== {name} {o['wid']} {o['session'][0][11:19]}-{o['session'][1][11:19]} ({o['session_min']} min)")
        print("  silences >=250 /10min", o["silences"]["per10"], "n", o["silences"]["gaps"], "max", o["silences"]["max_ms"],
              "ge950", o["silences"]["ge_per10"]["950"], "| outside", o.get("silences_outside_blackouts"))
        print("  bins", o["silences"]["bins"])
        print("  hitch", {k: o["hitch"][k] for k in ("hitch_seconds", "per_10_min", "longest_run_s")}, "| unatt", o["unattended"]["unattended_frames_core_running"],
              o["unattended"]["unattended_frames_core_running_per_10min"], "net", o["unattended_net"])
        print("  holds", o["holds"], o["holds_per10"], "stalls", o["stall_pauses"], o["stall_pauses_per10"], "rewind_failed", o["rewind_failed"],
              "ok", o["rewind_ok"], "transitions", o["transitions"], "lan rows", len(o["lan_rule_rows"]))
        print("  report", json.dumps([{k: v for k, v in r.items() if k not in ("video", "decoder")} for r in o["report"]]))
        for x in o.get("blackouts", []):
            print("   ", json.dumps({k: v for k, v in x.items() if k != "rows"}))
            print("       ", " | ".join(x["rows"])[:900])


if __name__ == "__main__":
    main()
