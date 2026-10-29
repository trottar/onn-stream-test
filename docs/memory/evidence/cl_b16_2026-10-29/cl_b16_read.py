#!/usr/bin/env python3
"""CL-B16 stage 3's reader: cl_b15_read.py with its cells table set to CL-B16's three, the report keys plus
loss_guard_max_hold_ms and the stall signal's counters, every client_stall / desync_pause row with its age and the
guard's heartbeat counters around it (cell 3 has the host flag, so its heartbeats carry them), and the ladder's and the
wan_sessions rows per cell. Below: CL-B15 Part 2's reader. Lines 1-160 are CL-B14's cl_b14_read.py (its own lines 1-147 CL-B13's cl_b13_read.py (CL-B12's imports, pins, span / blackouts / sessions_underruns unedited),
plus returns() for cells 1 and 2 and the remote-class rows for 3a / 3b. Original docstring:
CL-B12 stage 3's reader (read-only over cl_b12_2026-10-24/runs/; writes record_read.json and prints). From
cl_b11_read.py (itself from cl_b10_p2_read.py); CL-B12 adds the teardown rows (session_end_bye, state_save_skipped,
input_hold_skipped_*) and cell 1's per-press rows and per-session underruns. B6's gap_distribution.py `measure` and UX-R3's `evening` / `counts`, exec'd unedited and asserted
against LINK-R1's pins, over cell 1's named spans. Plus, per blackout of cells 2 and 3 (the recovery log):
  the onset: @both the controller gap's start (native_stream_ctrl_gaps.log, the gap >= 3 s); @down the client's last
    frame = the desync_pause's at_utc - its age_ms;
  the return: @both the gap's end (the first controller packet back); @down the onset + 4,000 ms (the shim's 4-s span;
    its 1-s lines give 5 lines per span, and @both's gaps read 4,004-4,013 ms);
  the resume's distance from the return; held = onset -> resume;
  saves outside the blackouts: state_saved not within [onset - 0.1 s, return + 2 s] of any blackout.
And cell 1's heartbeats per 2-s interval (audio_underruns deltas; a counter reset is a new count).
    python3 -B cl_b11_read.py
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
            "rssi": c("link_rssi_dbm"), "notice": c("link_notice")}


def blackouts(cell, both):
    ld = HERE / "runs" / cell / "logs_run1"
    rec = jl(ld / "native_stream_recovery.log")
    gaps = [g for g in jl(ld / "native_stream_ctrl_gaps.log") if (g.get("gap_ms") or 0) >= 3000]
    rows, cur = [], None
    for r in rec:
        e = r["event"]
        if e == "desync_pause":
            t = ts(r["at_utc"])
            if both:
                g = min(gaps, key=lambda g: abs(ts(g["start_utc"]) - t))
                onset, back = ts(g["start_utc"]), ts(g["end_utc"])
            else:
                onset = t - (r.get("age_ms") or 0) / 1000
                back = onset + 4.0
            sv = [x for x in rec if x["event"] == "state_saved" and onset - 0.1 <= ts(x["at_utc"]) <= t + 0.001]
            cur = {"pause_at": r["at_utc"][11:23], "trigger": r.get("trigger"), "pause_age_ms": r.get("age_ms"),
                   "onset": utc(onset)[11:23], "return": utc(back)[11:23], "_onset": onset, "_back": back,
                   "save_kind": sv[-1].get("kind") if sv else None, "save_after_onset_ms": sv[-1].get("save_after_onset_ms") if sv else None,
                   "save_before_pause_ms": round((t - ts(sv[-1]["at_utc"])) * 1000, 1) if sv else None}
            rows.append(cur)
        elif cur is not None and e in ("input_release", "resumed", "encoder_restart", "recovery_escalation", "stall_handover_v2",
                                       "input_hold_handover", "client_ready_after_stall", "client_ready_after_hold", "stall_end_late"):
            if e == "input_release":
                cur.update({"method": r.get("method"), "load_ack": r.get("load_ack"), "frames_restored": r.get("frames_restored"),
                            "net": r.get("net_unattended_frames")})
            elif e == "resumed":
                tr = ts(r["at_utc"])
                cur.update({"via": r.get("via"), "resumed_at": r["at_utc"][11:23], "recovering_ms": r.get("recovering_ms"),
                            "restarts": r.get("restarts"), "resume_after_return_ms": round((tr - cur["_back"]) * 1000),
                            "held_s": round(tr - cur["_onset"], 2)})
            else:
                cur[e] = cur.get(e, 0) + 1
    win = [(x["_onset"] - 0.1, x["_back"] + 2.0) for x in rows]
    outside = [{"at": x["at_utc"][11:23], "kind": x.get("kind"), "save_after_onset_ms": x.get("save_after_onset_ms")}
               for x in rec if x["event"] == "state_saved" and not any(a <= ts(x["at_utc"]) <= b for a, b in win)]
    ends = [x["at_utc"][11:23] for x in rec if x["event"] == "session_ended"]
    for x in rows:
        x.pop("_onset"); x.pop("_back")
    pauses = sum(1 for x in rec if x["event"] == "desync_pause")
    cfg = next((x for x in rec if x["event"] == "stall_resume_config"), {})
    tear = [{"at": x["at_utc"][11:23], "event": x["event"], **{k_: x.get(k_) for k_ in ("reason", "silence_ms", "age_ms") if k_ in x}}
            for x in rec if x["event"] in ("session_end_bye", "state_save_skipped", "input_hold_skipped_ending",
                                            "input_hold_skipped_paused", "session_ended")]
    lr = next((x for x in rec if x["event"] == "link_recovery_config"), {})
    mods = {x["event"]: {k_: x.get(k_) for k_ in ("threshold_ms", "mode", "fast_ready", "save_from_signal", "v2_newest_s", "hold_ms")
                         if k_ in x} for x in rec if x["event"].endswith("_config") and x["event"] != "link_recovery_config"}
    return {"blackouts": rows, "saves_outside": outside, "session_ended": ends, "desync_pauses": pauses, "teardown": tear,
            "link_recovery_config": {k_: lr.get(k_) for k_ in ("umbrella", "implied", "explicit")}, "module_configs": mods,
            "sessions_started": sum(1 for x in rec if x["event"] == "session_started"),
            "stall_resume_config": {k: cfg.get(k) for k in ("fast_ready", "save_from_signal", "v2_newest_s", "v2_ms")},
            "counts": dict(collections.Counter(x["event"] for x in rec if not x["event"].endswith("_config")))}


def underruns(cell):
    hb = jl(HERE / "runs" / cell / "logs_run1/native_stream_heartbeat.log")
    out, prev = [], None
    for r in hb:
        u = r.get("audio_underruns")
        if isinstance(u, int):
            d = u if prev is None or u < prev else u - prev
            out.append((r["received_at_utc"][11:23], r.get("elapsed_ms"), d))
            prev = u
    return out


def sessions_underruns(cell):
    """Per client session (elapsed_ms resets): the session's first heartbeat, and the audio_underruns delta per 2-s
    interval (the first heartbeat's value is its first interval)."""
    hb = jl(HERE / "runs" / cell / "logs_run1/native_stream_heartbeat.log")
    out, cur, prev_e = [], None, None
    for r in hb:
        e = r.get("elapsed_ms")
        if cur is None or (isinstance(e, int) and isinstance(prev_e, int) and e < prev_e):
            cur = {"first_hb": r["received_at_utc"][11:23], "rows": []}
            out.append(cur)
        cur["rows"].append((r["received_at_utc"][11:23], e, r.get("audio_underruns")))
        prev_e = e
    for sg in out:
        u, d, last = [x[2] for x in sg.pop("rows")], [], None
        for v in u:
            if isinstance(v, int):
                d.append(v if last is None or v < last else v - last)
                last = v
        sg.update({"heartbeats": len(u), "first_intervals": d[:4], "max_interval": max(d) if d else None, "sum": sum(d),
                   "intervals_above_15": sum(1 for x in d if x > 15)})
    return out



C1, C2, C3A, C3B = "1_snes_home_presses_restart_fast", "2_snes_home_presses_no_flag", "3a_snes_blackout_both_wan", "3b_snes_blackout_down_wan"


# CL-B13's REP / RK / jtime (its lines 148-156, unedited)
REP = HERE.parents[3] / "logs/games/decoder_sessions"
RK = ("restart_fast_released_by", "restart_fast_response_to_switch_ms", "restart_fast_switch_to_release_ms",
      "restart_fast_response_to_release_ms", "restart_fast_report_wait_ms", "restart_fast_gate_resets", "restart_fast_gate_last_reset")


def jtime(l):
    return datetime.fromisoformat(l.split()[0]).timestamp()



# ---------------------------------------------------------------- CL-B15 (new below this line)
# Per cell (L, C): the report's guard keys and AU drops; the heartbeats' guard counters per UTC minute (cumulative per
# client session -> deltas); the host's keyframe_requests rows per minute (cumulative -> deltas); the recovery log's
# config / save / hold / teardown rows; silences / hitch over the session (B6 / UX-R3, pinned, via span()).
CELLS14 = {"1": "1_snes_lan_remote_umbrella", "2": "2_snes_overlay_remote_umbrella", "3": "3_ps1_loss-1_guard_flag_b29"}
REPK = ("loss_guard_mode", "frames_after_dropped_reference", "loss_guard_episodes", "loss_guard_frames_held",
        "loss_guard_timeouts", "loss_guard_max_wait_ms", "loss_guard_max_hold_ms", "keyframe_requests_sent",
        "link_notice_shown", "duration_ms", "stall_signal_ms", "stall_signal_stalls_sent", "stall_signal_ends_sent")
VIDK = ("lost_packets", "lost_packets_in_resyncs", "dropped_frames", "sequence_gap_au_drops", "incomplete_au_drops",
        "non_idr_aus_dropped_waiting_for_idr")
DECK = ("rendered_frames", "dropped_frames", "max_output_gap_ms")


def report_for(rec):
    s0 = ts(next(r["at_utc"] for r in rec if r["event"] == "session_started"))
    s1 = ts(next(r["at_utc"] for r in reversed(rec) if r["event"] == "session_ended"))
    cands = []
    for p in REP.glob("native_decoder_*.json"):
        t = datetime.strptime(p.name[15:34], "%Y%m%d_%H%M%S_%f").replace(tzinfo=timezone.utc).timestamp()
        if s0 < t <= s1 + 30:
            cands.append((t, p))
    t, p = max(cands)
    d = json.loads(p.read_text())["report"]
    return p.name, {**{k: d.get(k) for k in REPK}, "video": {k: d["video"].get(k) for k in VIDK},
                    "decoder": {k: d["decoder"].get(k) for k in DECK}}, s0, s1


def cell_read(key):
    c = CELLS14[key]
    ld = HERE / "runs" / c / "logs_run1"
    rec = jl(ld / "native_stream_recovery.log")
    name, rep, s0, s1 = report_for(rec)
    hb = jl(ld / "native_stream_heartbeat.log")
    per, prev = collections.OrderedDict(), None
    for h in hb:
        t = ts(h["received_at_utc"])
        if not (s0 - 5 <= t <= s1 + 5):
            continue
        cur = {k: h.get(k) for k in ("frames_after_dropped_reference", "loss_guard_frames_held", "loss_guard_episodes",
                                      "lost_packets", "rendered_frames")}
        if prev is not None and all(isinstance(cur[k], int) and isinstance(prev[k], int) for k in cur):
            reset = (h.get("elapsed_ms") or 0) < (prev.get("_e") or 0)
            m = per.setdefault(utc(t)[11:16], {"hb": 0, "counter": 0, "held": 0, "episodes": 0, "lost": 0, "rendered": 0})
            m["hb"] += 1
            for k, n in (("frames_after_dropped_reference", "counter"), ("loss_guard_frames_held", "held"),
                         ("loss_guard_episodes", "episodes"), ("lost_packets", "lost"), ("rendered_frames", "rendered")):
                m[n] += cur[k] if reset else cur[k] - prev[k]
        prev = dict(cur, _e=h.get("elapsed_ms"))
    for m in per.values():
        m["unheld"] = m["counter"] - m["held"]
    kr = [r for r in rec if r["event"] == "keyframe_requests"]
    kpm, last = [], {"received": 0, "acted": 0, "rate_limited": 0, "forced": 0}
    for r in kr:
        kpm.append({"at": r["at_utc"][11:19], **{k: r[k] - last[k] for k in last}, "received_total": r["received"],
                    "forced_total": r["forced"], "reason": r.get("reason", "")[:60]})
        last = {k: r[k] for k in last}
    ev = collections.Counter(r["event"] for r in rec if ts(r["at_utc"]) >= s0 - 200)
    hold_ev = ("input_hold_carry", "input_hold_handover", "input_release", "desync_pause", "client_ready_after_hold")
    sp = span(c, f"cell {key}", utc(s0), utc(s1))
    full = [m for m in list(per.values())[1:-1]]                 # full minutes (the first / last partial left out)
    mins = (s1 - s0) / 60
    out = {"report_file": name, "report": rep, "session": [utc(s0), utc(s1)], "session_min": round(mins, 2),
           "per_minute": per, "keyframe_requests": kpm,
           "config_rows": [{k: v for k, v in r.items() if k != "schema"} for r in rec
                           if r["event"] in ("loss_guard_config", "restart_fast_config", "restart_fast_unlock_config")],
           "events": {k: ev[k] for k in ("state_saved", "keyframe_requests", "loss_guard_config", "session_started",
                                         "session_ended", "session_end_bye", "state_save_skipped") if k in ev},
           "holds": sum(ev[k] for k in hold_ev), "stall_rows": sum(n for k, n in ev.items() if k.startswith("stall_") and not k.endswith("_config")),
           "teardown": [{"at": r["at_utc"][11:23], "event": r["event"], **{k: r.get(k) for k in ("reason", "silence_ms") if k in r}}
                        for r in rec if r["event"] in ("session_end_bye", "state_save_skipped", "session_ended")][-3:],
           "silences": {k: sp[k] for k in ("streaming_s", "silences", "silences_per10", "bins", "max_ms")},
           "hitch": sp["hitch"], "freq": sp["freq"], "notice": sp["notice"], "heartbeats": sp["heartbeats"],
           "cost": {"episodes_per_min": round(rep["loss_guard_episodes"] / mins, 1) if rep["loss_guard_episodes"] is not None else None,
                    "held_per_min": round(rep["loss_guard_frames_held"] / mins, 1) if rep["loss_guard_frames_held"] is not None else None,
                    "frames_per_episode": round(rep["loss_guard_frames_held"] / rep["loss_guard_episodes"], 2) if rep["loss_guard_episodes"] else None,
                    "ms_per_episode_at_60fps": round(1000 * rep["loss_guard_frames_held"] / rep["loss_guard_episodes"] / 60) if rep["loss_guard_episodes"] else None,
                    "full_minute_episodes": [m["episodes"] for m in full], "full_minute_counter": [m["counter"] for m in full]}}
    stalls = []
    hbt = [(ts(h["received_at_utc"]), h) for h in hb]
    for r in rec:
        if r["event"] not in ("client_stall", "desync_pause") or not (s0 - 5 <= ts(r["at_utc"]) <= s1 + 5):
            continue
        t = ts(r["at_utc"])
        before = [h for x, h in hbt if t - 4 <= x <= t]
        after = [h for x, h in hbt if t < x <= t + 4]
        g = lambda h, k_: h.get(k_) if h else None
        b_, a_ = (before[-1] if before else None), (after[0] if after else None)
        held_d = (g(a_, "loss_guard_frames_held") - g(b_, "loss_guard_frames_held")) if isinstance(g(a_, "loss_guard_frames_held"), int) and isinstance(g(b_, "loss_guard_frames_held"), int) else None
        ep_d = (g(a_, "loss_guard_episodes") - g(b_, "loss_guard_episodes")) if isinstance(g(a_, "loss_guard_episodes"), int) and isinstance(g(b_, "loss_guard_episodes"), int) else None
        gaps = [x for x in jl(ld / "native_stream_ctrl_gaps.log") if abs(ts(x["start_utc"]) - t) <= 2 and (x.get("gap_ms") or 0) >= 250]
        stalls.append({"at": r["at_utc"][11:23], "event": r["event"], "age_ms": r.get("age_ms"), "trigger": r.get("trigger"),
                       "guard_held_delta_around": held_d, "guard_episodes_delta_around": ep_d,
                       "uplink_silence_ge250_within_2s": [round(x["gap_ms"], 1) for x in gaps]})
    out["stall_rows_detail"] = stalls
    lad = jl(ld / "adaptive_bitrate_shadow.jsonl")
    out["ladder_states"] = dict(collections.Counter(f'{r.get("level_kbps")} {r.get("state")} {r.get("reason")}' for r in lad if r.get("event") == "sample"))
    out["ladder_events"] = [{k: r.get(k) for k in ("at_utc", "event", "level_kbps", "from_kbps", "to_kbps", "reason", "path_class")}
                            for r in lad if r.get("event") not in ("sample",)]
    return out


res = {k: cell_read(k) for k in CELLS14 if (HERE / "runs" / CELLS14[k] / "logs_run1").exists()}
(HERE / "record_read.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
for k, r in res.items():
    print(f"== cell {k}", r["report_file"], r["session"], r["session_min"], "min")
    print(" report", json.dumps(r["report"]))
    print(" cost", json.dumps(r["cost"]))
    print(" events", r["events"], "holds", r["holds"], "stall rows", r["stall_rows"], "teardown", r["teardown"])
    print(" config", [(x["event"], {a: b for a, b in x.items() if a in ("ignored", "control", "min_interval_ms")}) for x in r["config_rows"]])
    print(" silences", json.dumps(r["silences"]), "| hitch", json.dumps(r["hitch"]), "| freq", r["freq"], "| notice", r["notice"])
    print(" minute | hb | counter | held | unheld | episodes | lost | rendered")
    for m, x in r["per_minute"].items():
        print(" ", m, x["hb"], x["counter"], x["held"], x["unheld"], x["episodes"], x["lost"], x["rendered"], sep=" | ")
    for x in r["keyframe_requests"]:
        print("  kf", json.dumps(x))
    for x in r["stall_rows_detail"]:
        print("  stall", json.dumps(x))
    print(" ladder states", json.dumps(r["ladder_states"]))
