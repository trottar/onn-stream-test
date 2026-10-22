#!/usr/bin/env python3
"""BENCH-R1's record reader (read-only over bench_r1_2026-10-22/; writes only into record/).

Per cell, from the driver's files (cells.jsonl, runs/<cell>/logs_run1/, the client report copied in):
  - the session span (recovery log session_started / session_ended);
  - the rung path and every lan_loss_rule row, timed from session_started (cells 2-4 against LAN-R1 §3);
  - hitch seconds per 10 min and the longest run: UX-R3's definition and code -- ux_r3_seconds.py's own `evening`
    and `counts`, exec'd unedited from the script (its sha256 checked against the pre-registration's tool hash),
    pointed at the cell's logs over the client session;
  - unattended frames (core running), whole session and per blackout: tools/unattended_frames.py as hashed at the
    pre-registration (git show b909735, sha256 checked), --window per blackout;
  - the hold rows and the time held (6, 8);
  - the per-blackout table (5-7): uplink (control) gaps, output gaps (client report rows placed by UX-R3's elapsed
    map, and the ladder sample's output_gap_ms), the heartbeat hold (the longest heartbeat inter-arrival), post-FEC
    loss and FEC-unrecoverable groups (heartbeat intervals ending in the window), the recovery rows.
The blackout times: cells 5-6 from the ~4-s control gaps (the uplink is dark); cell 7 (@down, uplink live) from the
shim's dark spans, anchored by the offset measured on cells 5-6 (shim t_s -> UTC), checked against cell 7's own
client output gaps.

    python3 -B record/bench_r1_record_read.py      (from bench_r1_2026-10-22/)
"""
import hashlib, json, os, re, statistics, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
B = HERE.parent
EV = B.parent
UX = EV / "ux_r3_2026-10-21/ux_r3_seconds.py"
UNATT = HERE / "unattended_frames_at_b909735.py"
TOOLS = {l.split()[1]: l.split()[0] for l in (B / "tools_at_preregistration_sha256.txt").read_text().splitlines()}
CELLS = [json.loads(l) for l in open(B / "cells.jsonl")]
REPORTS = B.parents[3] / "logs/games/decoder_sessions"
WIN_BEFORE, WIN_AFTER = 1.0, 10.0          # a blackout's window: [start - 1 s, start + 10 s]
REC_AFTER = 15.0                           # its recovery rows: to start + 15 s
DEATH = {"uplink_gaps": "5 gaps, 2.65 s silent of 4 s, longest 967 ms", "output_gaps_ms": "410 / 307",
         "heartbeat_hold": "~1.5 s", "post_fec_lost": 61, "unattended_core_running": 83.8}
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ts(v):
    return datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()


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
assert sha(UNATT) == TOOLS["tools/unattended_frames.py"], "unattended_frames.py is not the hashed one"
src = UX.read_text()
UXNS = {"__file__": str(UX)}
exec(compile(src[:src.index("out, L = {}, []")], str(UX), "exec"), UXNS)   # the definitions only, unedited


def copy_reports(cell, ldir):
    """The cell's client report(s) (received in the run's span) into logs_run1/decoder_sessions/, the core's
    version token in capture_description masked (the only address-like string in a report)."""
    d = ldir / "decoder_sessions"
    d.mkdir(exist_ok=True)
    n = []
    for p in sorted(REPORTS.glob("native_decoder_20261022_*.json")):
        j = json.load(open(p))
        if cell["start_utc"] <= j.get("received_at_utc", "") <= cell["end_utc"]:
            s = re.sub(r"(Beetle PSX HW )\d+(\.\d+){3}", r"\1<version>", json.dumps(j))
            assert not IP.search(s), p.name
            (d / p.name).write_text(s + "\n")
            n.append(p.name)
    return n


def unatt(ldir, a, b, windows=(), name="x"):
    out = HERE / f"unattended_{name}.json"
    cmd = [sys.executable, "-B", str(UNATT), "--logs", str(ldir), "--span", utc(a)[:23], utc(b)[:23], "--json", str(out)]
    for name, x, y in windows:
        cmd += ["--window", name, utc(x)[:23], utc(y)[:23]]
    subprocess.run(cmd, capture_output=True, check=True, timeout=300)
    return json.loads(out.read_text())


def blackout_starts(cell, ldir, rec_start, offset=None):
    """UTC of each blackout's start. @both: the control gaps >= 3.5 s. @down: the shim's dark spans + offset."""
    sh = cell.get("shim") or {}
    spans = sh.get("dark_spans") or []
    if cell["cell"].startswith(("05", "06")):
        g = [ts(x["start_utc"]) for x in jl(ldir / "native_stream_ctrl_gaps.log") if x["gap_ms"] >= 3500]
        return g, spans
    if cell["cell"].startswith("07") and offset is not None:
        return [rec_start + s["t_s_from"] + offset for s in spans], spans
    return [], spans


def main():
    res = {"tools": {"ux_r3_seconds.py": sha(UX), "unattended_frames_at_b909735.py": sha(UNATT)}, "death_ux_r3": DEATH,
           "window_s": [-WIN_BEFORE, WIN_AFTER], "cells": {}}
    offsets = []
    order = sorted(CELLS, key=lambda c: c["n"])
    for c in order:
        cd = B / "runs" / c["cell"]
        ld = cd / "logs_run1"
        rec = jl(ld / "native_stream_recovery.log")
        s0 = next(ts(r["at_utc"]) for r in rec if r["event"] == "session_started")
        s1 = next(ts(r["at_utc"]) for r in reversed(rec) if r["event"] == "session_ended")
        reps = copy_reports(c, ld)
        out = {"session": [utc(s0), utc(s1)], "session_min": round((s1 - s0) / 60, 2), "window": c.get("window"),
               "reports": reps, "playing_attempt": c.get("playing_attempt"), "s_to_playing": c.get("s_to_playing")}
        # ---- the ladder: the path and every lan_loss_rule row, timed from session_started ----
        lad = jl(ld / "adaptive_bitrate_shadow.jsonl")
        out["transitions"] = [{"at": r["at_utc"][11:19], "min_in": round((ts(r["at_utc"]) - s0) / 60, 2),
                               "from": r.get("from_kbps"), "to": r.get("to_kbps"), "reason": r.get("reason"), "class": r.get("class")}
                              for r in lad if r.get("event") == "transition" and r.get("acted")]
        out["lan_loss_rule"] = [{"at": r["at_utc"][11:19], "s_in": round((ts(r["at_utc"]) - s0), 1),
                                 "session_elapsed_s": round((r.get("session_elapsed_ms") or 0) / 1000, 1),
                                 "level": r.get("level_kbps"), "unrec_windows": r.get("unrec_windows"),
                                 "ladder_result": r.get("ladder_result")} for r in lad if r.get("event") == "lan_loss_rule"]
        # ---- hitch seconds: UX-R3's own code over the client session ----
        cfg = {"dir": str(ld), "start": utc(s0)[:19], "end": utc(s1 + 1)[:19]}
        rows, gaps, cover, play_s = UXNS["evening"](cfg)
        out["hitch"] = UXNS["counts"](rows, play_s)
        w0, w1 = c["window"]["from"][:19], c["window"]["to"][:19]
        out["hitch_window"] = UXNS["counts"](rows, ts(c["window"]["to"]) - ts(c["window"]["from"]), w0, w1)
        out["hitch_report_coverage"] = cover
        # ---- the hold rows (6, 8) ----
        hold = [r for r in rec if r["event"].startswith("input_") or r.get("trigger") == "input_hold"
                or r.get("via") == "input_release"]
        out["hold_rows"] = [{k: r.get(k) for k in ("at_utc", "event", "trigger", "via", "age_ms", "held_ms", "reason") if r.get(k) is not None}
                            for r in hold]
        held = [r["held_ms"] for r in rec if r.get("via") == "input_release" and r.get("held_ms") is not None]
        out["holds"] = sum(1 for r in rec if r["event"] == "desync_pause" and r.get("trigger") == "input_hold")
        out["releases"] = len([r for r in rec if r.get("via") == "input_release"])
        out["held_ms_total"], out["held_ms_median"] = round(sum(held), 1), (round(statistics.median(held), 1) if held else None)
        out["recovery_rows"] = [{k: r.get(k) for k in ("at_utc", "event", "trigger", "via", "age_ms", "held_ms", "recovering_ms") if r.get(k) is not None}
                                for r in rec if r["event"] not in ("session_started", "session_ended")]
        # ---- unattended frames and the per-blackout table ----
        starts, spans = blackout_starts(c, ld, s0)
        if c["cell"].startswith(("05", "06")) and spans and len(starts) == len(spans):
            offsets += [st - (s0 + sp["t_s_from"]) for st, sp in zip(starts, spans)]
        out["_s0"], out["_spans"], out["_starts"] = s0, spans, starts
        res["cells"][c["cell"]] = out
    off = statistics.median(offsets) if offsets else None
    res["shim_offset_s"] = {"median": round(off, 3) if off is not None else None,
                            "range": [round(min(offsets), 3), round(max(offsets), 3)] if offsets else None, "n": len(offsets),
                            "meaning": "control-gap start minus (session_started + the shim's first dark t_s), cells 5-6"}
    for c in order:
        out = res["cells"][c["cell"]]
        ld = B / "runs" / c["cell"] / "logs_run1"
        s0, s1 = ts(out["session"][0]), ts(out["session"][1])
        starts = out.pop("_starts")
        spans = out.pop("_spans")
        out.pop("_s0")
        if c["cell"].startswith("07"):
            starts, _ = blackout_starts(c, ld, s0, off)
        wins = [(f"b{i + 1}", st - WIN_BEFORE, st + WIN_AFTER) for i, st in enumerate(starts)]
        u = unatt(ld, s0, s1, wins, c["cell"])
        out["unattended"] = {k: u[k] for k in ("streaming_s", "gaps", "episodes", "unattended_frames", "unattended_frames_per_10min",
                                                "unattended_frames_core_running", "unattended_frames_core_running_per_10min",
                                                "held_episodes", "held_episodes_per_10min", "recovery_paused_spans")}
        if not starts:
            continue
        rows, _, _, _ = UXNS["evening"]({"dir": str(ld), "start": utc(s0)[:19], "end": utc(s1 + 1)[:19]})
        hb = [h for h in jl(ld / "native_stream_heartbeat.log") if s0 <= ts(h["received_at_utc"]) <= s1 + 1]
        gl = jl(ld / "native_stream_ctrl_gaps.log")
        rec = jl(ld / "native_stream_recovery.log")
        lad = [a for a in jl(ld / "adaptive_bitrate_shadow.jsonl") if a.get("event") == "sample"]
        table = []
        for (name, a, b), st in zip(wins, starts):
            g = [x for x in gl if a <= ts(x["start_utc"]) <= b]
            secs = [rows[k] for k in rows if a <= ts(k + "Z") <= b]
            arr = [ts(h["received_at_utc"]) for h in hb if a - 4 <= ts(h["received_at_utc"]) <= b + 4]
            ia = [round(y - x, 2) for x, y in zip(arr, arr[1:])]
            uw = u["windows"][name]
            rr = [f"{r['at_utc'][11:23]} {r['event']}" + (f":{r['trigger']}" if r.get("trigger") else "")
                  + (f":{r['via']}" if r.get("via") else "") + (f" held {r['held_ms']}" if r.get("held_ms") is not None else "")
                  for r in rec if a <= ts(r["at_utc"]) <= st + REC_AFTER and r["event"] not in ("session_started", "session_ended")]
            table.append({"blackout": name, "start_utc": utc(st)[11:23], "s_into_session": round(st - s0, 1),
                          "uplink_gaps_n": len(g), "uplink_gap_longest_ms": max((x["gap_ms"] for x in g), default=0),
                          "uplink_silent_ms": round(sum(x["gap_ms"] for x in g), 1),
                          "output_gap_report_max_ms": max((r.get("out_gap_report", 0) for r in secs), default=0),
                          "output_gap_ladder_max_ms": max((a_.get("output_gap_ms") or 0 for a_ in lad if a <= ts(a_["at_utc"]) <= b), default=0),
                          "heartbeat_max_interarrival_s": max(ia, default=None),
                          "post_fec_lost": sum(r.get("post_fec") or 0 for r in secs), "fec_unrec_groups": sum(r.get("unrec") or 0 for r in secs),
                          "hitch_seconds": sum(1 for r in secs if r.get("score")),
                          "unattended_frames": uw["unattended_frames"], "unattended_frames_core_running": uw["unattended_frames_core_running"],
                          "holds": sum(1 for r in rec if a <= ts(r["at_utc"]) <= b and r.get("trigger") == "input_hold"),
                          "releases": sum(1 for r in rec if a <= ts(r["at_utc"]) <= st + REC_AFTER and r.get("via") == "input_release"),
                          "recovery_rows": rr})
        out["blackouts"] = table
        inside = sum(x["unattended_frames_core_running"] for x in table)
        out["unattended_core_running_in_blackouts"] = round(inside, 1)
        out["unattended_core_running_per_blackout"] = round(inside / len(table), 1)
        out["unattended_core_running_outside_blackouts"] = round(u["unattended_frames_core_running"] - inside, 1)
    (HERE / "record_read.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "cells"}, default=str))
    for name, o in res["cells"].items():
        print(f"== {name} session {o['session'][0][11:19]}-{o['session'][1][11:19]} ({o['session_min']} min) reports {len(o['reports'])}")
        print("  hitch", o["hitch"], "| window", {k: o["hitch_window"][k] for k in ("hitch_seconds", "per_10_min", "longest_run_s")})
        print("  unattended", {k: o["unattended"][k] for k in ("gaps", "episodes", "unattended_frames_core_running", "unattended_frames_core_running_per_10min", "held_episodes")})
        print("  transitions", o["transitions"])
        print("  holds", o["holds"], "releases", o["releases"], "held total", o["held_ms_total"], "median", o["held_ms_median"])
        for x in o.get("blackouts", []):
            print("   ", json.dumps(x)[:700])
        if "blackouts" in o:
            print("  per blackout core-running", o["unattended_core_running_per_blackout"], "outside", o["unattended_core_running_outside_blackouts"])


if __name__ == "__main__":
    main()
