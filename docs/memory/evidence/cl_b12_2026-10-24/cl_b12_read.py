#!/usr/bin/env python3
"""CL-B12 stage 3's reader (read-only over cl_b12_2026-10-24/runs/; writes record_read.json and prints). From
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

C1, C2, C3 = "1_snes_5ghz_two_home_presses", "2_snes_blackout_both_umbrella", "3_snes_blackout_down_umbrella"


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


res = {"cell2": blackouts(C2, True), "cell3": blackouts(C3, False)}
res["cell1_recovery"] = [{k_: v for k_, v in r.items() if k_ != "schema"} for r in jl(HERE / "runs" / C1 / "logs_run1/native_stream_recovery.log")
                         if not r["event"].endswith("_config")]
res["cell1_sessions_underruns"] = sessions_underruns(C1)
res["spans"] = [
    span(C1, "cell 1, 5 GHz, session 1 (to press 1)", "2026-10-24T17:12:11.997Z", "2026-10-24T17:15:13.191Z"),
    span(C1, "cell 1, 5 GHz, session 2 (press 1 to press 2)", "2026-10-24T17:15:39.786Z", "2026-10-24T17:18:03.769Z"),
    span(C1, "cell 1, 5 GHz, session 3 (press 2 to the end)", "2026-10-24T17:18:35.773Z", "2026-10-24T17:23:43.518Z"),
]
for c in (C2, C3):
    d = [x for _, _, x in underruns(c)]
    res.setdefault("other_cells_underruns_per_interval_max", {})[c] = max(d) if d else None
(HERE / "record_read.json").write_text(json.dumps(res, indent=1) + "\n")
for c in ("cell2", "cell3"):
    r = res[c]
    print(c, "| link_recovery_config", r["link_recovery_config"], "| modules", r["module_configs"])
    print("  pauses", r["desync_pauses"], "sessions", r["sessions_started"], "| saves outside", r["saves_outside"], "| teardown", r["teardown"])
    for b in r["blackouts"]:
        print(" ", json.dumps(b))
for s_ in res["spans"]:
    print(s_["name"], "| s", s_["streaming_s"], "| silences", s_["silences"], "per10", s_["silences_per10"], "max", s_["max_ms"],
          "| hitch", s_["hitch"].get("hitch_seconds"), "per10", s_["hitch"].get("per_10_min"), "| hb", s_["heartbeats"], "freq", s_["freq"],
          "notice", s_["notice"])
print("cell 1 sessions (underruns per 2-s interval):", json.dumps(res["cell1_sessions_underruns"]))
print("cells 2 / 3 max per interval", res["other_cells_underruns_per_interval_max"])
