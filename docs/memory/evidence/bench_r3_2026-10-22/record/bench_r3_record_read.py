#!/usr/bin/env python3
"""BENCH-R3's record reader, built from bench_r2_record_read.py (read-only over bench_r3_2026-10-22/; writes only into
record/: record_read.json, the per-cell log copies under record/logs/<cell>/ with each cell's client report under
decoder_sessions/, the core's version token masked).

Per cell (the session = the recovery log's session_started .. session_ended):
  - hitch seconds per 10 min and the longest run: UX-R3's `evening` / `counts`, exec'd unedited (sha256 = BENCH-R2's pin;
    it is not in R3's tool list, disclosed);
  - the uplink silences >= 250 ms per 10 min and their distribution: B6's gap_distribution.py `measure`, exec'd unedited
    (sha256 = R3's pre-registration), 10 s at each edge excluded (B6's rule); for the blackout cells also outside them;
  - unattended frames core-running, plain and --net (tools/unattended_frames.py, sha256 = R3's pre-registration), whole
    session and per blackout (window: start - 1 s .. start + 10 s, R2's);
  - every hold / carry / release / handover / stall / stall_end / rewind / state / keyframe row with timing;
  - the per-blackout table (A, B, D): the hold's age, the carry, the handover, the link's return, the resume (via, s
    after the return, heartbeats between), the rewind / release row and its after-check, stall_end_late, the client's
    picture after the resume (rendered frames per s over the 10 s after it, the output age at the first heartbeat), D's
    state rows;
  - E: the loss guard's heartbeat counters per minute, the client report's guard / AU-drop fields, keyframe_requests rows;
  - THE LINK: the report's RSSI / tx / rx per minute (median / min) with post-FEC loss, FEC-unrecoverable groups, the
    shim's drops (per-second lines placed by the offset anchor) and rendered fps; beside every silence >= 500 ms, every
    blackout and every minute with post-FEC loss > 500: the heartbeat before / after and the min over +-10 s, and the
    Opal round nearest in time (wlan1: airtime only; it listed no station in any round).
Heartbeats: one client session per cell, taken in sequence order and placed on the host clock by the client's elapsed
(UX-R3's map), because some arrived late and out of order (E-off 21:27Z); the late ones are listed.
Blackout times: A / D from the ~4-s control gaps (start; the return = the gap's end); B (@down) from the client's own
>= 3-s output gaps (its last frame before each dark span; the return = start + 4.0 s), R2's c1 method.
    python3 -B record/bench_r3_record_read.py   (from bench_r3_2026-10-22/)
"""
import hashlib, json, re, shutil, statistics, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
B = HERE.parent
EV = B.parent
REPO = B.parents[3]
UX = EV / "ux_r3_2026-10-21/ux_r3_seconds.py"
UX_PIN = "e9b2b3f79286bdd320a9bf530d76c0381ca6d89ded6f1adfe3c4d3f3ba8b59b4"      # BENCH-R2's tools list
GD = EV / "b6_2026-10-22/gap_distribution.py"
UNATT = REPO / "tools/unattended_frames.py"
TOOLS = {l.split()[1]: l.split()[0] for l in (B / "tools_at_preregistration_sha256.txt").read_text().splitlines()}
CELLS = sorted((json.loads(l) for l in open(B / "cells.jsonl")), key=lambda c: c["n"])
REPORTS = REPO / "logs/games/decoder_sessions"
OPAL = B / "opal/air.jsonl"
WIN_BEFORE, WIN_AFTER, REC_AFTER, DARK_S, PIC_S, NEAR_S = 1.0, 10.0, 15.0, 4.0, 10.0, 10.0
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
LOGS = ("native_stream_heartbeat.log", "native_stream_ctrl_gaps.log", "native_stream_recovery.log",
        "native_frame_sizes.jsonl", "adaptive_bitrate_shadow.jsonl")


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


def med(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return statistics.median(xs) if xs else None


assert sha(UX) == UX_PIN, "ux_r3_seconds.py changed"
assert sha(GD) == TOOLS["docs/memory/evidence/b6_2026-10-22/gap_distribution.py"], "gap_distribution.py changed"
assert sha(UNATT) == TOOLS["tools/unattended_frames.py"], "unattended_frames.py changed"
src = UX.read_text()
UXNS = {"__file__": str(UX)}
exec(compile(src[:src.index("out, L = {}, []")], str(UX), "exec"), UXNS)
gsrc = GD.read_text()
GDNS = {"__file__": str(GD)}
exec(compile(gsrc[:gsrc.index("R1 = EV /")], str(GD), "exec"), GDNS)


def copy_cell(cell):
    """The cell's five log copies (runs/<cell>/logs_run1, the driver's) into record/logs/<cell>/, and the client's report(s)
    received inside the cell into its decoder_sessions/ (the core's version token masked; no address)."""
    src, d = B / "runs" / cell["cell"] / "logs_run1", HERE / "logs" / cell["cell"]
    (d / "decoder_sessions").mkdir(parents=True, exist_ok=True)
    for n in LOGS:
        shutil.copyfile(src / n, d / n)
    n = []
    for p in sorted(REPORTS.glob("native_decoder_20261022_*.json")):
        j = json.load(open(p))
        if cell["start_utc"] <= j.get("received_at_utc", "") <= cell["end_utc"]:
            s = re.sub(r"(Beetle PSX HW |snes9x )(\d+(?:\.\d+){1,3})", r"\1<version>", json.dumps(j))
            assert not IP.search(s), p.name
            (d / "decoder_sessions" / p.name).write_text(s + "\n")
            n.append(p.name)
    return d, n


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


def the_report(ld):
    out = []
    for p in sorted((ld / "decoder_sessions").glob("*.json")):
        r = json.load(open(p))["report"]
        v, dec = r.get("video") or {}, r.get("decoder") or {}
        out.append({"report": p.name, "duration_s": round((r.get("duration_ms") or 0) / 1000, 1),
                    **{k: r.get(k) for k in r if k.startswith(("wifi_lock", "stall_signal", "link", "loss_guard",
                                                                  "frames_after", "keyframe"))},
                    "video": {k: v.get(k) for k in ("lost_packets", "fec_recovered_packets", "fec_unrecoverable_groups",
                                                   "sequence_gap_au_drops", "incomplete_au_drops", "dropped_frames",
                                                   "non_idr_aus_dropped_waiting_for_idr", "sequence_resyncs", "idr_frames",
                                                   "max_frames_between_idr", "frames")},
                    "decoder": {k: dec.get(k) for k in ("rendered_frames", "dropped_frames", "stale_output_drops",
                                                       "max_output_gap_ms", "spike_50_ms", "spike_80_ms")}})
    return out


def client_dark_starts(ld):
    """R2's c1 method: the client's >= 3-s output gaps (its report, placed by the heartbeats' elapsed map)."""
    rep = json.load(open(sorted((ld / "decoder_sessions").glob("*.json"))[0]))
    r = rep["report"]
    hb = jl(ld / "native_stream_heartbeat.log")
    end = ts(rep["received_at_utc"])
    s = [h for h in hb if end - r["duration_ms"] / 1000 - 30 <= ts(h["received_at_utc"]) <= end + 5]
    off = statistics.median(ts(h["received_at_utc"]) * 1000 - h["elapsed_ms"] for h in s)
    gi = r["slow_event_columns"].index("output_gap_ms")
    ev = sorted({(e[0], e[gi]) for e in (r.get("slow_events_top_gap") or []) + (r.get("slow_events_ge_50_ms") or []) if e[gi] >= 3000})
    return [(off + el - g) / 1000 for el, g in ev]


def opal_rows():
    return [{"at": r["at_utc"], "t": ts(r["at_utc"]), "seq": r["seq"], "channel": (r.get("airtime") or {}).get("channel"),
             "util_pct": (r.get("airtime") or {}).get("utilization_pct"), "noise_dbm": (r.get("airtime") or {}).get("noise_dbm"),
             "stations": len(r.get("stations") or []), "log_events": len(r.get("log_events") or []),
             "wlan1_tx_packets": ((r.get("iface_stats") or {}).get("wlan1") or {}).get("tx_packets")} for r in jl(OPAL)]


OPAL_ROWS = opal_rows()


def opal_near(t):
    o = min(OPAL_ROWS, key=lambda r: abs(r["t"] - t), default=None)
    return None if o is None else {"seq": o["seq"], "at": o["at"][11:19], "s_from_event": round(o["t"] - t), "util_pct": o["util_pct"],
                                   "noise_dbm": o["noise_dbm"], "stations": o["stations"]}


def shim_seconds(cell_dir, s0, off):
    """The shim's per-second lines placed on the wall clock: s0 (session_started) + t_s + off."""
    out = []
    for r in jl(cell_dir / "impairment_run1.jsonl"):
        drops = sum(r.get(k) or 0 for k in ("dropped_loss", "dropped_burst", "dropped_queue", "dropped_blackout"))
        out.append((s0 + (r.get("t_s") or 0) + off, drops, r.get("uplink_dropped") or 0))
    return out


def placed(hb):
    """The cell's heartbeats (one client session) in sequence order, each with _t = the client's elapsed placed on the host
    clock by the median (received - elapsed), UX-R3's map; and the late arrivals (received > placed + 2 s)."""
    s = sorted(hb, key=lambda h: h["sequence"])
    assert len({h["sequence"] for h in s}) == len(s), "more than one client session"
    off = statistics.median(ts(h["received_at_utc"]) * 1000 - h["elapsed_ms"] for h in s) if s else 0
    for h in s:
        h["_t"] = (off + h["elapsed_ms"]) / 1000
    late = [{"seq": h["sequence"], "placed": utc(h["_t"])[11:23], "received": h["received_at_utc"][11:23],
             "late_s": round(ts(h["received_at_utc"]) - h["_t"], 1)} for h in s if ts(h["received_at_utc"]) - h["_t"] > 2.0]
    return s, late


def per_minute(hb, a, b, shim):
    """Per UTC minute from the heartbeats (deltas inside a client session): post-FEC lost, FEC-unrecoverable groups,
    rendered fps, the loss guard's counters; the link's RSSI / tx / rx (median / min); the shim's drops that minute."""
    rows = {}
    s = [h for h in hb if a - 5 <= h["_t"] <= b + 5]
    for h in s:
        m = utc(h["_t"])[:16]
        r = rows.setdefault(m, {"hb": 0, "lost": 0, "unrec": 0, "rendered": 0, "s": 0.0, "rssi": [], "tx": [], "rx": [],
                                "far": 0, "held": 0, "episodes": 0, "shim_drops": 0, "shim_uplink": 0})
        r["hb"] += 1
        for k_, x in (("rssi", "link_rssi_dbm"), ("tx", "link_tx_mbps"), ("rx", "link_rx_mbps")):
            if isinstance(h.get(x), (int, float)):
                r[k_].append(h[x])
    for x, y in zip(s, s[1:]):
        if y["sequence"] <= x["sequence"]:
            continue
        r = rows[utc(y["_t"])[:16]]
        d = lambda k_: max(0, (y.get(k_) or 0) - (x.get(k_) or 0))
        r["lost"] += d("lost_packets")
        r["unrec"] += d("fec_unrecoverable_groups")
        r["rendered"] += d("rendered_frames")
        r["far"] += d("frames_after_dropped_reference")
        r["held"] += d("loss_guard_frames_held")
        r["episodes"] += d("loss_guard_episodes")
        r["s"] += (y["elapsed_ms"] - x["elapsed_ms"]) / 1000
    for t, drops, up in shim:
        m = utc(t)[:16]
        if m in rows:
            rows[m]["shim_drops"] += drops
            rows[m]["shim_uplink"] += up
    out = {}
    for m, r in sorted(rows.items()):
        out[m] = {"hb": r["hb"], "rssi_med": med(r["rssi"]), "rssi_min": min(r["rssi"], default=None),
                  "tx_med": med(r["tx"]), "tx_min": min(r["tx"], default=None), "rx_med": med(r["rx"]),
                  "rx_min": min(r["rx"], default=None), "post_fec_lost": r["lost"], "fec_unrec": r["unrec"],
                  "fps": round(r["rendered"] / r["s"], 1) if r["s"] else None, "shim_drops": r["shim_drops"],
                  "shim_uplink_drops": r["shim_uplink"], "frames_after_dropped_reference": r["far"],
                  "loss_guard_frames_held": r["held"], "loss_guard_episodes": r["episodes"]}
    return out


def link_beside(hb, a, b):
    """The heartbeat just before a, the first after b, and the min / median over [a - 10, b + 10]."""
    lk = lambda h: {"at": utc(h["_t"])[11:23], "rssi": h.get("link_rssi_dbm"), "tx": h.get("link_tx_mbps"),
                    "rx": h.get("link_rx_mbps")}
    bef = [h for h in hb if h["_t"] < a]
    aft = [h for h in hb if h["_t"] > b]
    near = [h for h in hb if a - NEAR_S <= h["_t"] <= b + NEAR_S]
    col = lambda x: [h.get(x) for h in near if isinstance(h.get(x), (int, float))]
    return {"before": lk(bef[-1]) if bef else None, "after": lk(aft[0]) if aft else None, "n_near": len(near),
            "rssi_min": min(col("link_rssi_dbm"), default=None), "tx_min": min(col("link_tx_mbps"), default=None),
            "rx_min": min(col("link_rx_mbps"), default=None), "rssi_med": med(col("link_rssi_dbm")),
            "tx_med": med(col("link_tx_mbps")), "rx_med": med(col("link_rx_mbps"))}


def picture_after(hb, t):
    """The client's picture after a resume at t: the first heartbeat after t (its output age), the rendered frames per s
    over (t, t + PIC_S], and the first heartbeat whose rendered count advanced."""
    s = [h for h in hb if t - 3 <= h["_t"] <= t + PIC_S + 3]
    aft = [h for h in s if h["_t"] > t]
    bef = [h for h in s if h["_t"] <= t]
    if not aft or not bef:
        return None
    x0 = bef[-1]
    inwin = [h for h in aft if h["_t"] <= t + PIC_S] or aft[:1]
    x1 = inwin[-1]
    dt = (x1["elapsed_ms"] - x0["elapsed_ms"]) / 1000
    adv = next((h for h in aft if h["rendered_frames"] > x0["rendered_frames"]), None)
    return {"first_hb_s": round(aft[0]["_t"] - t, 2), "first_hb_output_age_ms": aft[0].get("last_output_age_ms"),
            "first_advance_s": round(adv["_t"] - t, 2) if adv else None,
            "fps_10s": round((x1["rendered_frames"] - x0["rendered_frames"]) / dt, 1) if dt > 0 else None}


def main():
    res = {"tools": {"ux_r3_seconds.py": sha(UX), "gap_distribution.py": sha(GD), "unattended_frames.py": sha(UNATT)},
           "window_s": [-WIN_BEFORE, WIN_AFTER], "opal": OPAL_ROWS, "cells": {}}
    pre, offsets = {}, []
    for c in CELLS:
        ld, reps = copy_cell(c)
        rec = jl(ld / "native_stream_recovery.log")
        s0 = next(ts(r["at_utc"]) for r in rec if r["event"] == "session_started")
        s1 = next(ts(r["at_utc"]) for r in reversed(rec) if r["event"] == "session_ended")
        spans = (c.get("shim") or {}).get("dark_spans") or []
        gl = [x for x in jl(ld / "native_stream_ctrl_gaps.log") if x["gap_ms"] >= 3500 and s0 <= ts(x["start_utc"]) <= s1]
        starts = [(ts(x["start_utc"]), ts(x["end_utc"])) for x in gl] if c.get("uplink") else []
        if starts and len(starts) == len(spans):
            offsets += [st - (s0 + sp["t_s_from"]) for (st, _), sp in zip(starts, spans)]
        pre[c["cell"]] = (ld, reps, rec, s0, s1, spans, starts)
    off = statistics.median(offsets)
    res["shim_offset_s"] = {"median": round(off, 3), "range": [round(min(offsets), 3), round(max(offsets), 3)], "n": len(offsets)}
    for c in CELLS:
        ld, reps, rec, s0, s1, spans, starts = pre[c["cell"]]
        anchor = None
        if c["profile"] == "blackout-4s" and not c.get("uplink"):
            st_ = client_dark_starts(ld)
            anchor = {"shim_offset_starts": [utc(s0 + sp["t_s_from"] + off)[11:23] for sp in spans],
                      "client_output_gap_starts": [utc(x)[11:23] for x in st_]}
            starts = [(x, x + DARK_S) for x in st_]
        out = {"anchor": anchor, "n": c["n"], "wid": c["wid"], "spec": c["spec"], "extra": c["extra"], "props": c["props_set"],
               "session": [utc(s0), utc(s1)], "session_min": round((s1 - s0) / 60, 2), "reports": reps}
        rows, _, cover, play_s = UXNS["evening"]({"dir": str(ld), "start": utc(s0)[:19], "end": utc(s1 + 1)[:19]})
        out["hitch"] = UXNS["counts"](rows, play_s)
        g = GDNS["measure"](c["cell"], ld, s0, s1)
        out["silences"] = {k: g[k] for k in ("streaming_s", "gaps", "per10", "bins", "bins_per10", "max_ms")}
        out["silences"]["ge_per10"] = {str(h): g["ge_per10"][h] for h in (250, 400, 500, 800, 950, 1000, 1500)}
        if starts:
            ex = [(st - WIN_BEFORE, st + WIN_AFTER) for st, _ in starts]
            g2 = GDNS["measure"](c["cell"] + " outside blackouts", ld, s0, s1, ex)
            out["silences_outside_blackouts"] = {k: g2[k] for k in ("streaming_s", "gaps", "per10", "max_ms")}
            out["silences_outside_blackouts"]["ge500_per10"] = g2["ge_per10"][500]
        wins = [(f"b{i + 1}", st - WIN_BEFORE, st + WIN_AFTER) for i, (st, _) in enumerate(starts)]
        u = unatt(ld, s0, s1, c["cell"], wins)
        P, N = u["plain"], u["net"]
        out["unattended"] = {k: P.get(k) for k in ("streaming_s", "gaps", "episodes", "unattended_frames_core_running",
                                                     "unattended_frames_core_running_per_10min")}
        out["unattended_net"] = {k: v for k, v in (N.get("net") or {}).items() if k != "episodes"}
        keep = ("at_utc", "event", "trigger", "via", "age_ms", "held_ms", "client_frame", "in_gate", "pre_hold_frames",
                "stall_frames", "requested_frames", "rewound_frames", "onset_to_pause_ms", "reason", "recovering_ms",
                "packets_back_to_resume_ms", "since_resume_ms", "ignored_gate_stalls", "save_after_onset_ms", "silence_ms",
                "method", "frames_restored", "net_unattended_frames", "load_ack", "received", "acted", "rate_limited",
                "forced", "window_s")
        rr = [{k: r.get(k) for k in keep if r.get(k) is not None} for r in rec if not r["event"].endswith("_config")]
        out["recovery_rows"] = rr
        out["config_rows"] = [r for r in rec if r["event"].endswith("_config")]
        ev = {}
        for r in rec:
            k = r["event"] + (":" + r["trigger"] if r.get("trigger") else "") + (":" + r["via"] if r.get("via") else "")
            ev[k] = ev.get(k, 0) + 1
        out["recovery_events"] = ev
        mins = (s1 - s0) / 60
        per10 = lambda n: round(n * 10 / mins, 2) if mins else None
        inside = lambda t: any(st - WIN_BEFORE <= t <= st + REC_AFTER for st, _ in starts)
        holds = [r for r in rec if r["event"] == "desync_pause" and r.get("trigger") == "input_hold"]
        stalls = [r for r in rec if r["event"] == "desync_pause" and r.get("trigger") == "client_stall"]
        out["holds"], out["holds_per10"] = len(holds), per10(len(holds))
        out["stall_pauses"], out["stall_pauses_per10"] = len(stalls), per10(len(stalls))
        hout = [r for r in holds if not inside(ts(r["at_utc"]))]
        sout = [r for r in stalls if not inside(ts(r["at_utc"]))]
        out["holds_outside_blackouts"] = [{"at": r["at_utc"][11:23], "age_ms": r.get("age_ms")} for r in hout]
        out["holds_outside_per10"] = per10(len(hout))
        out["stall_pauses_outside_blackouts"] = [{"at": r["at_utc"][11:23], "age_ms": r.get("age_ms")} for r in sout]
        out["stall_pauses_outside_per10"] = per10(len(sout))
        hb, late = placed(jl(ld / "native_stream_heartbeat.log"))
        hb = [h for h in hb if s0 - 5 <= h["_t"] <= s1 + 5]
        out["heartbeats_late"] = late
        if starts:
            table = []
            for (name, a, b), (st, ret) in zip(wins, starts):
                rw = [r for r in rec if a <= ts(r["at_utc"]) <= st + REC_AFTER and not r["event"].endswith("_config")]
                pick = lambda e, **kw: next((r for r in rw if r["event"] == e and all(r.get(k_) == v for k_, v in kw.items())), None)
                hold, carry, hand = pick("desync_pause", trigger="input_hold"), pick("input_hold_carry"), pick("input_hold_handover")
                stall = pick("desync_pause", trigger="client_stall")
                resumes = [r for r in rw if r["event"] == "resumed"]
                rel = [r for r in rw if r["event"] in ("input_release", "rewind_failed", "rewind_skipped")]
                late = pick("stall_end_late")
                saved = pick("state_saved")
                first_res = resumes[0] if resumes else None
                tr = ts(first_res["at_utc"]) if first_res else None
                pic = picture_after(hb, tr) if tr else None
                last_res = resumes[-1] if resumes else None
                pic_last = picture_after(hb, ts(last_res["at_utc"])) if last_res and last_res is not first_res else None
                hb_between = sum(1 for h in hb if ret < h["_t"] < tr) if tr else None
                ne = sum(e["unattended_frames_core_running_net"] for e in (N.get("net") or {}).get("episodes") or []
                         if a <= ts(e["start"]) <= b)
                uw = P["windows"][name]
                rows_t = [f"{round(ts(r['at_utc']) - st, 2):+.2f} {r['event']}" + (f":{r['trigger']}" if r.get("trigger") else "")
                          + (f":{r['via']}" if r.get("via") else "") + (f" age {r['age_ms']}" if r.get("age_ms") is not None else "")
                          + (f" held {r['held_ms']}" if r.get("held_ms") is not None else "")
                          + (f" pre {r['pre_hold_frames']}" if r.get("pre_hold_frames") is not None else "")
                          + (f" stall {r['stall_frames']}" if r.get("stall_frames") is not None else "")
                          + (f" req {r['requested_frames']}" if r.get("requested_frames") is not None else "")
                          + (f" rew {r['rewound_frames']}" if r.get("rewound_frames") is not None else "")
                          + (f" restored {r['frames_restored']} net {r['net_unattended_frames']}" if r.get("frames_restored") is not None else "")
                          for r in rw]
                table.append({
                    "blackout": name, "start_utc": utc(st)[11:23], "return_utc": utc(ret)[11:23], "s_into_session": round(st - s0, 1),
                    "dark_s": round(ret - st, 2),
                    "hold_s": round(ts(hold["at_utc"]) - st, 2) if hold else None, "hold_age_ms": hold.get("age_ms") if hold else None,
                    "carry": {k: carry.get(k) for k in ("pre_hold_frames", "stall_frames")} if carry else None,
                    "handover_s": round(ts(hand["at_utc"]) - st, 2) if hand else None, "held_ms": hand.get("held_ms") if hand else None,
                    "stall_pause_s": round(ts(stall["at_utc"]) - st, 2) if stall else None,
                    "stall_age_ms": stall.get("age_ms") if stall else None, "stall_in_gate": stall.get("in_gate") if stall else None,
                    "pauses": sum(1 for r in rw if r["event"] == "desync_pause"),
                    "resumes": [f"{r.get('via') or 'recovery'} {round(ts(r['at_utc']) - ret, 2):+.2f}" for r in resumes],
                    "first_resume_via": (first_res.get("via") or "recovery") if first_res else None,
                    "first_resume_after_return_s": round(tr - ret, 2) if tr else None, "heartbeats_between": hb_between,
                    "packets_back_to_resume_ms": first_res.get("packets_back_to_resume_ms") if first_res else None,
                    "release_rows": [{k: r.get(k) for k in ("event", "via", "method", "requested_frames", "rewound_frames",
                                                             "frames_restored", "net_unattended_frames", "load_ack", "reason")
                                      if r.get(k) is not None} for r in rel],
                    "after_check_playing": (None if not rel else all(r["event"] == "input_release" for r in rel)),
                    "stall_end_late_ms": late.get("since_resume_ms") if late else None,
                    "ignored_gate_stalls": late.get("ignored_gate_stalls") if late else None,
                    "state_saved_after_onset_ms": saved.get("save_after_onset_ms") if saved else None,
                    "encoder_restarts": sum(1 for r in rw if r["event"] == "encoder_restart"),
                    "new_sessions": sum(1 for r in rw if r["event"] == "session_started"),
                    "picture_after_first_resume": pic, "picture_after_last_resume": pic_last,
                    "unattended_core_running": uw["unattended_frames_core_running"], "unattended_raw": uw["unattended_frames"],
                    "unattended_net": round(ne, 1), "link": link_beside(hb, st, ret), "opal": opal_near(st), "rows": rows_t})
            out["blackouts"] = table
        shim = shim_seconds(B / "runs" / c["cell"], s0, off)
        pm = per_minute(hb, s0, s1, shim)
        out["per_minute"] = pm
        lim = [h["_t"] for h in hb]
        out["link_cell"] = {"rows": len(hb), "with_link": sum(1 for h in hb if "link_rssi_dbm" in h),
                            "rssi_med": med([h.get("link_rssi_dbm") for h in hb]), "rssi_min": min((h["link_rssi_dbm"] for h in hb if "link_rssi_dbm" in h), default=None),
                            "rssi_max": max((h["link_rssi_dbm"] for h in hb if "link_rssi_dbm" in h), default=None),
                            "tx_med": med([h.get("link_tx_mbps") for h in hb]), "tx_min": min((h["link_tx_mbps"] for h in hb if "link_tx_mbps" in h), default=None),
                            "rx_med": med([h.get("link_rx_mbps") for h in hb]), "rx_min": min((h["link_rx_mbps"] for h in hb if "link_rx_mbps" in h), default=None),
                            "freq": sorted({h.get("link_frequency_mhz") for h in hb if "link_frequency_mhz" in h}),
                            "standard": sorted({h.get("link_wifi_standard") for h in hb if "link_wifi_standard" in h}),
                            "interval_med_s": med([y - x for x, y in zip(lim, lim[1:])])}
        sil = []
        for x in jl(ld / "native_stream_ctrl_gaps.log"):
            t0, t1 = ts(x["start_utc"]), ts(x["end_utc"])
            if s0 + 10 <= t0 <= s1 - 10 and x["gap_ms"] >= 500:
                sil.append({"start": x["start_utc"][11:23], "gap_ms": round(x["gap_ms"]), "in_blackout": inside(t0),
                            "link": link_beside(hb, t0, t1), "opal": opal_near(t0)})
        out["silences_ge500"] = sil
        flap = []
        for m, r in pm.items():
            if r["post_fec_lost"] > 500:
                t = ts(m + ":30")
                flap.append({"minute": m[11:16], "post_fec_lost": r["post_fec_lost"], "shim_drops": r["shim_drops"],
                             "no_shim_drop": r["shim_drops"] == 0, "rssi_med": r["rssi_med"], "rssi_min": r["rssi_min"],
                             "tx_med": r["tx_med"], "tx_min": r["tx_min"], "rx_med": r["rx_med"], "rx_min": r["rx_min"],
                             "fps": r["fps"], "opal": opal_near(t)})
        out["loss_gt500_minutes"] = flap
        ladr = jl(ld / "adaptive_bitrate_shadow.jsonl")
        out["transitions"] = [{"at": r["at_utc"][11:19], "from": r.get("from_kbps"), "to": r.get("to_kbps"), "reason": r.get("reason")}
                              for r in ladr if r.get("event") == "transition" and r.get("acted")]
        out["report"] = the_report(ld)
        out["keyframe_rows"] = [r for r in rec if r["event"] in ("keyframe_requests", "keyframe_forced")]
        out["host"] = {k: c.get(k) for k in ("host_gates", "host_gates_met", "retroarch_fps", "capture_fps", "dupdrop_per_min",
                                              "host_cpu", "companion_cpu", "encoder_cpu", "retroarch_cpu", "retroarch_rss_kb",
                                              "retroarch_rss_kb_max", "mem_available_mb", "mem_available_mb_min")}
        out["stream"] = {k: c.get(k) for k in ("loss_per_min", "rendered_fps", "resyncs", "max_output_gap_ms", "client_pauses",
                                                "fec_recovered", "fec_unrecoverable", "audio_underruns", "spikes50",
                                                "wire_bitrate_kbps_seen", "encoder_rc_seen", "rung_path", "s_to_playing",
                                                "playing_attempt", "suite_attempts", "validity", "profile_applied",
                                                "flags_absent_after", "props_set", "props_after", "environ_at_stream_count",
                                                "environ_under_load_count", "retroarch_log")}
        out["shim"] = {k: (c.get("shim") or {}).get(k) for k in ("packets_in", "dropped_loss", "dropped_blackout", "uplink_dropped",
                                                                  "loss_frac", "dark_span_lines_s", "dark_span_starts_apart_s",
                                                                  "shim_cpu_pct_core", "duration_s")}
        res["cells"][c["cell"]] = out
    (HERE / "record_read.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps({"shim_offset_s": res["shim_offset_s"]}))
    for name, o in res["cells"].items():
        print(f"== {name} {o['wid']} {o['session'][0][11:19]}-{o['session'][1][11:19]} ({o['session_min']} min) reports {o['reports']}")
        print("  silences >=250 /10min", o["silences"]["per10"], "n", o["silences"]["gaps"], "max", o["silences"]["max_ms"],
              "ge500/10", o["silences"]["ge_per10"]["500"], "| outside", o.get("silences_outside_blackouts"))
        print("  bins", o["silences"]["bins"])
        print("  hitch", {k: o["hitch"][k] for k in ("hitch_seconds", "per_10_min", "longest_run_s", "by_criterion")},
              "| unatt", o["unattended"]["unattended_frames_core_running"], o["unattended"]["unattended_frames_core_running_per_10min"],
              "net", o["unattended_net"])
        print("  holds", o["holds"], o["holds_per10"], "outside", o["holds_outside_blackouts"], "| stalls", o["stall_pauses"],
              o["stall_pauses_per10"], "outside", len(o["stall_pauses_outside_blackouts"]), o["stall_pauses_outside_per10"])
        print("  link", o["link_cell"], "| transitions", o["transitions"], "| late heartbeats", o["heartbeats_late"])
        print("  report", json.dumps([{k: v for k, v in r.items() if k != "decoder"} for r in o["report"]]))
        print("  silences>=500", json.dumps([(s["start"], s["gap_ms"], s["in_blackout"], s["link"]["rssi_min"], s["link"]["tx_min"], s["link"]["rx_min"]) for s in o["silences_ge500"]]))
        print("  loss>500 minutes", json.dumps([(f["minute"], f["post_fec_lost"], f["shim_drops"], f["rssi_min"], f["tx_min"], f["rx_min"], f["fps"]) for f in o["loss_gt500_minutes"]]))
        if o["keyframe_rows"]:
            print("  keyframe rows", json.dumps([{k: v for k, v in r.items() if k not in ("schema", "state")} for r in o["keyframe_rows"]])[:900])
        for x in o.get("blackouts", []):
            print("   ", json.dumps({k: v for k, v in x.items() if k not in ("rows", "link", "opal")}))
            print("       link", json.dumps(x["link"]), "opal", json.dumps(x["opal"]))


if __name__ == "__main__":
    main()
