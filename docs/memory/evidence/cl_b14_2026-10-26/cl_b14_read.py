#!/usr/bin/env python3
"""CL-B14 stage 2's reader. Lines 1-147 are CL-B13's cl_b13_read.py (CL-B12's imports, pins, span / blackouts / sessions_underruns unedited),
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



# ---------------------------------------------------------------- CL-B14 (new below this line)
# Per guarded return, R1-R7 as pre-registered (cl_b14_preregistration.txt §3), with CL-B13 §2's methods:
#   R1 the one clock: startSession (heartbeat 1's arrival less its elapsed_ms) less create_to_start_ms; the events read
#      (the onn's clock, EDT -> UTC +4 h) beside it, and the offset (one clock - the onn's);
#   R2 the old encoder's row for the entry's second at 60 fps from the second's start; beside it a bound that needs no
#      fps assumption (the relay's stop, and the end of the entry's second when the old encoder has no picture row after);
#   R3 restart_fast_done; R4 the relay's rows per second; R5 the order; R6 the audio rows and the first interval;
#   R7 the heartbeats' link_notice, link_notice_shown rows, the reports' link_notice_shown.
C = "1_snes_home_returns_restart_fast_unlock"
LD = HERE / "runs" / C / "logs_run1"
RUN = HERE / "runs" / C / "E1-SNES-STREAM_flag/run1"
DAY = "2026-10-27T"
RK2 = RK + ("link_notice_shown", "link_notice_last_reasons")


def creates14():
    out = []
    for l in open(HERE / "adb_reads/logcat_events_cell.txt"):
        if "wm_on_create_called: activity=NativeStreamActivity" in l:
            out.append(datetime.strptime("2026-" + l[:18], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp() + 4 * 3600)
    return out


def tiny(f):
    return f["frames"] == 1 and f["packets"] == 1 and (f.get("payload_bytes") or 0) <= 16


def returns14():
    rec = jl(LD / "native_stream_recovery.log")
    hb = jl(LD / "native_stream_heartbeat.log")
    fr = jl(LD / "native_frame_sizes.jsonl")
    jr = [l.rstrip("\n") for l in open(HERE / "journal_precise_cell.txt")]
    creates = creates14()
    t0r, t1r = ts(rec[0]["at_utc"]), ts(rec[-1]["at_utc"])
    reps = sorted(p for p in REP.glob("native_decoder_*.json")
                  if t0r - 5 <= datetime.strptime(p.name[15:30], "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc).timestamp() <= t1r + 60)
    reps = [(datetime.strptime(p.name[15:34], "%Y%m%d_%H%M%S_%f").replace(tzinfo=timezone.utc).timestamp(), json.loads(p.read_text())["report"]) for p in reps]
    ends = [r for r in rec if r["event"] == "session_ended"]
    starts = [ts(r["at_utc"]) for r in rec if r["event"] == "session_started"]
    ev = lambda name: [r for r in rec if r["event"] == name]
    rf, rfd, ras, ra = ev("restart_fast"), ev("restart_fast_done"), ev("restart_fast_audio_stop"), ev("restart_fast_audio")
    sess = sessions_underruns(C)
    out = []
    for e in ends:
        te = ts(e["at_utc"])
        start_resp = [jtime(l) for l in jr if "native-stream-start" in l and "guard_end=1" in l and te - 1 <= jtime(l) <= te + 5]
        if not start_resp:
            continue                      # the teardown's session_ended (no return)
        tresp = start_resp[0]
        old_rep = next((t for t, _ in reps if t >= te - 0.5), None)
        ss = next((t for t in starts if t > te), None)
        nrep = next((r for t, r in reps if ss and t > ss), None) or {}
        cause = nrep.get("restart_cause") or {}
        h1 = next((h for h in hb if ss and ts(h["received_at_utc"]) > te and h.get("sequence") == 1), None)
        start_session = ts(h1["received_at_utc"]) - h1["elapsed_ms"] / 1000 if h1 else None
        act_host = start_session - (cause.get("create_to_start_ms") or 0) / 1000 if start_session else None
        act_ev = next((c for c in creates if te - 3 <= c <= te + 1), None)
        r1 = next((r for r in rf if te - 0.05 <= ts(r["at_utc"]) <= te + 1), None)
        d1 = next((r for r in rfd if te <= ts(r["at_utc"]) <= te + 5), None)
        as1 = next((r for r in ras if te <= ts(r["at_utc"]) <= te + 15), None)
        a1 = next((r for r in ra if te <= ts(r["at_utc"]) <= te + 15), None)
        w0 = ts(d1["at_utc"]) - d1["unlocked_ms"] / 1000 if d1 else None      # the worker's t0 (its own ms are from it)
        at = lambda key: (w0 + d1[key] / 1000) if d1 and d1.get(key) is not None else None
        t_relay, t_rel, t_spawn = at("relay_stopped_ms"), at("released_ms"), at("spawned_ms")
        # R2: the old encoder's picture rows in the entry's second (closed before the kill), at 60 fps from its start
        sec = int(te)
        in_sec = [f for f in fr if int(ts(f["at_utc"])) == sec and not tiny(f)]
        old = [f for f in in_sec if f.get("max_at_utc") and t_rel and ts(f["max_at_utc"]) < t_rel and ts(f["max_at_utc"]) <= te + 0.05]
        old_last = (sec + (old[0]["frames"] - 1) / 60) if old else None
        nxt_old = [f for f in fr if int(ts(f["at_utc"])) == sec + 1 and not tiny(f) and t_rel and f.get("max_at_utc") and ts(f["max_at_utc"]) < t_rel]
        bound = min(x for x in (t_relay, (sec + 1) if not nxt_old else None) if x is not None) if t_relay else None
        tn = [f for f in fr if tiny(f) and te <= ts(f["max_at_utc"]) <= te + 5]
        # R4: seconds after the switch second (its own and the next) with more than one relay row, to +60 s
        per = collections.Counter(int(ts(f["at_utc"])) for f in fr if sec + 2 <= int(ts(f["at_utc"])) <= sec + 60)
        sw = sorted({int(ts(f["at_utc"])) for f in fr if sec <= int(ts(f["at_utc"])) <= sec + 1})
        first_after = None
        if h1 and ss:
            t_h1 = ts(h1["received_at_utc"])
            nx = next((ts(h["received_at_utc"]) for h in hb if ts(h["received_at_utc"]) > t_h1 and h.get("sequence") == 1), 1e18)
            hs = [h for h in hb if t_h1 <= ts(h["received_at_utc"]) < nx]
            k = next((i for i, h in enumerate(hs) if ts(h["received_at_utc"]) > ss), None)
            if k is not None:
                first_after = hs[k]["audio_underruns"] - (hs[k - 1]["audio_underruns"] if k > 0 else 0)
        sg = next((s for s in sess if h1 and abs(ts(DAY + s["first_hb"] + "Z") - ts(h1["received_at_utc"])) < 0.01), None)
        out.append({
            "entry_session_ended": e["at_utc"][11:23], "start_response_journal": utc(tresp)[11:23],
            "old_report_received": utc(old_rep)[11:23] if old_rep else None,
            "old_report_after_response_ms": round((old_rep - tresp) * 1000) if old_rep else None,
            "session_started": utc(ss)[11:23] if ss else None,
            "R5_order_ended_oldreport_started": bool(old_rep and ss and te < old_rep < ss),
            "restart_fast": ({"at": r1["at_utc"][11:23], "response_ms": r1.get("response_ms"), "lock_ms": r1.get("lock_ms"),
                              "after_session_ended_ms": round((ts(r1["at_utc"]) - te) * 1000, 1)} if r1 else None),
            "restart_fast_done": ({k_: d1.get(k_) for k_ in ("relay_stopped_ms", "released_ms", "spawned_ms", "checked_ms", "unlocked_ms")} if d1 else None),
            "R3_unlocked_minus_checked_ms": round(d1["unlocked_ms"] - d1["checked_ms"], 1) if d1 else None,
            "worker_t0_after_entry_ms": round((w0 - te) * 1000, 1) if w0 else None,
            "relay_stopped_after_entry_s": round(t_relay - te, 3) if t_relay else None,
            "released_after_entry_s": round(t_rel - te, 3) if t_rel else None,
            "R2_old_last_frame_after_entry_s_method": round(old_last - te, 3) if old_last else None,
            "R2_old_row": ({"frames": old[0]["frames"], "max_at": old[0]["max_at_utc"][11:23]} if old else None),
            "R2_bound_after_entry_s": round(bound - te, 3) if bound else None,
            "tiny_rows": [{"at": f["max_at_utc"][11:23], "bytes": f.get("payload_bytes"), "unmarked": f.get("unmarked_frames"),
                           "after_entry_s": round(ts(f["max_at_utc"]) - te, 3),
                           "vs_released_ms": round((ts(f["max_at_utc"]) - t_rel) * 1000, 1) if t_rel else None} for f in tn],
            "R4_switch_seconds_rows": {utc(s_)[11:19]: [(f["frames"], f["packets"]) for f in fr if int(ts(f["at_utc"])) == s_] for s_ in sw},
            "R4_seconds_after_switch_with_2plus_rows": [utc(s_)[11:19] for s_, n_ in per.items() if n_ > 1],
            "startSession_host": utc(start_session)[11:23] if start_session else None,
            "create_to_start_ms": cause.get("create_to_start_ms"),
            "new_activity_host_clock": utc(act_host)[11:23] if act_host else None,
            "new_activity_to_entry_s": round(te - act_host, 3) if act_host else None,
            "R1_picture_back_one_clock_s": round(ss - act_host, 2) if act_host and ss else None,
            "new_activity_events_onn_clock": utc(act_ev)[11:23] if act_ev else None,
            "picture_back_events_s": round(ss - act_ev, 2) if act_ev and ss else None,
            "onn_clock_offset_s": round(act_host - act_ev, 2) if act_host and act_ev else None,
            "restart_cause": {k_: cause.get(k_) for k_ in ("flush", "host_ended_session", "stop_posted", "old_report_posted", "trigger", "away_ms")},
            "report": {k_: nrep.get(k_) for k_ in RK2 if k_ in nrep},
            "R6_audio_stop": ({k_: as1.get(k_) for k_ in ("restart_fast_audio_stop_ms", "restart_fast_audio_stop_end_ms", "capture_returncode",
                                                           "capture_killed_at_bound", "joined")} if as1 else None),
            "R6_audio": ({k_: a1.get(k_) for k_ in ("started", "new_audio_ms", "why")} if a1 else None),
            "R6_audio_after_session_started_s": round(ts(a1["at_utc"]) - ss, 3) if a1 and ss else None,
            "R6_first_interval_after_session_started_underruns": first_after,
            "new_session_max_interval": sg["max_interval"] if sg else None,
        })
    shown = [r for r in rec if r["event"] in ("link_notice_shown", "link_notice_cleared")]
    hbn = collections.Counter(h.get("link_notice", "<absent>") for h in hb)
    return {"returns": out, "restart_fast_failed": len(ev("restart_fast_failed")),
            "restart_fast_rows": collections.Counter(r["event"] for r in rec if r["event"].startswith("restart_fast")),
            "separate_native_stream_stop": sum(1 for l in jr if "native-stream-stop" in l),
            "sessions_underruns": sess,
            "R7": {"heartbeats": len(hb), "link_notice_values": dict(hbn), "link_notice_rows": len(shown),
                   "freq": dict(collections.Counter(h.get("link_frequency_mhz") for h in hb)),
                   "reports_link_notice_shown": [r.get("link_notice_shown") for _, r in reps]},
            "teardown": [{"at": x["at_utc"][11:23], "event": x["event"], **{k_: x.get(k_) for k_ in ("reason", "silence_ms") if k_ in x}}
                         for x in rec if x["event"] in ("session_end_bye", "state_save_skipped", "session_ended")][-3:]}


def capture_without_kill_pairs(kills):
    """E4-S5D's segcap with the pairs spanning an old encoder's kill left out (CL-B13 §1's disclosure)."""
    S = __import__("importlib.util").util
    spec = S.spec_from_file_location("s5d", EV / "e4_s5d_2026-10-15/e4_s5d_analysis.py")
    m = S.module_from_spec(spec)
    spec.loader.exec_module(m)
    s = json.load(open(RUN / "summary.json"))
    t0, t1 = s["window"]["from"], s["window"]["to"]
    rows = [r for r in jl(RUN / "encoder.jsonl") if r.get("records") and t0 <= r["at_utc"] <= t1]
    fr = dt = 0.0
    left = 0
    for a, b in zip(rows, rows[1:]):
        d = ts(b["at_utc"]) - ts(a["at_utc"])
        if b["frame"] < a["frame"] or d > 3 or b["dup"] < a["dup"] or b["drop"] < a["drop"]:
            continue
        if any(ts(a["at_utc"]) <= k <= ts(b["at_utc"]) for k in kills):
            left += 1
            continue
        fr += b["frame"] - a["frame"]
        dt += d
    return {"segcap": m.segcap(str(RUN), s), "without_kill_pairs": round(fr / dt, 3) if dt else None, "pairs_left_out": left,
            "window": [t0, t1]}


def sess_spans14():
    rec = jl(LD / "native_stream_recovery.log")
    st = [r["at_utc"] for r in rec if r["event"] == "session_started"]
    en = [r["at_utc"] for r in rec if r["event"] == "session_ended"]
    gaps = [g for g in jl(LD / "native_stream_ctrl_gaps.log") if (g.get("gap_ms") or 0) >= 3000]
    out = []
    for a in st:
        z = next((e for e in en if e > a), rec[-1]["at_utc"])
        g = [x["start_utc"] for x in gaps if a < x["start_utc"] < z]
        out.append((a, g[-1] if g else z))
    return out


res = {"cell": returns14()}
kills = []
for x in res["cell"]["returns"]:
    if x["released_after_entry_s"] is not None:
        kills.append(ts(DAY + x["entry_session_ended"] + "Z") + x["released_after_entry_s"])
res["capture"] = capture_without_kill_pairs(kills)
res["spans"] = []
for i, (a, z) in enumerate(sess_spans14()):
    if ts(z) - ts(a) > 30:
        res["spans"].append(span(C, f"session {i + 1}", a, z))
res["whole_cell"] = span(C, "whole cell", jl(LD / "native_stream_recovery.log")[0]["at_utc"], jl(LD / "native_stream_recovery.log")[-1]["at_utc"])
(HERE / "record_read.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
r = res["cell"]
print("restart_fast rows", dict(r["restart_fast_rows"]), "failed", r["restart_fast_failed"], "| separate stop", r["separate_native_stream_stop"])
for x in r["returns"]:
    print(json.dumps(x))
print("R7", json.dumps(r["R7"]))
print("teardown", r["teardown"])
print("capture", res["capture"])
for s_ in res["spans"] + [res["whole_cell"]]:
    print(s_["name"], "| s", s_["streaming_s"], "| silences", s_["silences"], "per10", s_["silences_per10"], "max", s_["max_ms"],
          "| hitch", s_["hitch"].get("hitch_seconds"), "per10", s_["hitch"].get("per_10_min"), "| freq", s_["freq"], "| notice", s_["notice"])
