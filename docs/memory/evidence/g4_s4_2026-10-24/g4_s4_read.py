#!/usr/bin/env python3
"""G4-S4 Part 2: the reading of the whole off-site play, from copies/ (g4_s4_assemble.py) and samples/ (the driver's).
Read-only.

THE HITCH DEFINITION is UX-R3 §1's, unchanged (ux_r3_2026-10-21/ux_r3_seconds.py): a UTC second is a hitch second if
  R the heartbeat interval ending in it rendered < 50 fps; C a host control gap >= 250 ms starts in it;
  G an output gap >= 200 ms is recorded in it (a client-report row placed by the elapsed map, or a ladder sample's
    output_gap_ms); L the heartbeat interval ending in it lost >= 30 packets after FEC.
  The user's own pauses (a control gap containing a session_ended, within 1 s of its end) are excluded.
SILENCES: control gaps >= 250 ms, the pauses excluded.
THE STACK'S ROWS: every state_saved / desync_pause / input_hold_handover / hold_return_armed / input_release /
  rewind_* / stall row. A hold (desync_pause) is tagged REAL DROP if a control gap >= 3 s contains it or a dark span
  (no heartbeat for >= 3 s) touches it; else FALSE HOLD (the link alive on both sides). A real drop whose gap contains a
  session_ended is noted "user (Home / exit)".
THE LINES: fourteen (ten + the four) from the drop-in's read-back (20:02:56Z) to its removal (21:21:02Z); ten otherwise.
THE PATH: the driver's overlay sample within 60 s, else "not sampled".

    g4_s4_read.py -> sessions.tsv, bins_10min.tsv, stack_rows.tsv, seconds.tsv, counts.json, read_console.txt
"""
import bisect
import glob
import json
import os
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "copies/logs/games")
S = os.path.join(HERE, "samples")
FOUR = ("2026-10-24T20:02:56", "2026-10-24T21:21:02")


def ts(s):
    s = s if s.endswith("Z") or "+" in s[10:] else s + "Z"
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def sec(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S")


def jl(p):
    if not os.path.exists(p):
        return
    for line in open(p, errors="replace"):
        try:
            yield json.loads(line)
        except ValueError:
            pass


def med(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(statistics.median(xs), 1) if xs else None


# ---------------------------------------------------------------- the inputs
rec = list(jl(os.path.join(D, "native_stream_recovery.log")))
hb = list(jl(os.path.join(D, "native_stream_heartbeat.log")))
gaps_raw = list(jl(os.path.join(D, "native_stream_ctrl_gaps.log")))
lad = list(jl(os.path.join(D, "adaptive_bitrate_shadow.jsonl")))
fsz = list(jl(os.path.join(D, "native_frame_sizes.jsonl")))
fast = list(jl(os.path.join(S, "fast_10s.jsonl")))
slow = list(jl(os.path.join(S, "slow_60s.jsonl")))
reports = []
for p in sorted(glob.glob(os.path.join(D, "decoder_sessions/*.json"))):
    d = json.load(open(p))
    reports.append((os.path.basename(p), d))

starts = [ts(r["at_utc"]) for r in rec if r["event"] == "session_started"]
ends = [ts(r["at_utc"]) for r in rec if r["event"] == "session_ended"]
sessions = []
for st in starts:
    en = next((e for e in ends if e > st), None)
    sessions.append([st, en])

slow_t = [(ts(r["at_utc"]), r) for r in slow]


def path_at(t):
    best = min(slow_t, key=lambda x: abs((x[0] - t).total_seconds()), default=None)
    if best and abs((best[0] - t).total_seconds()) <= 60:
        return best[1]["overlay"].get("path")
    return "not sampled"


def lines_at(t):
    return 14 if FOUR[0] <= sec(t) <= FOUR[1] else 10


# ---------------------------------------------------------------- heartbeats: per interval, per client session
hb_sessions, cur = [], []
for h in hb:
    if cur and h["sequence"] <= cur[-1]["sequence"]:
        hb_sessions.append(cur)
        cur = []
    cur.append(h)
if cur:
    hb_sessions.append(cur)
rows = defaultdict(dict)
intervals, outside = [], []


def in_session(t):
    return any(st <= t <= (en or st) + timedelta(seconds=3) for st, en in sessions)


for s in hb_sessions:
    for a, b in zip(s, s[1:]):
        dt = (b["elapsed_ms"] - a["elapsed_ms"]) / 1000
        k = sec(ts(b["received_at_utc"]))
        if not in_session(ts(b["received_at_utc"])):
            outside.append({"t": k, "dt": dt, "rendered": b["rendered_frames"] - a["rendered_frames"],
                            "underruns": b["audio_underruns"] - a["audio_underruns"]})
            continue
        iv = {"t": ts(b["received_at_utc"]), "dt": dt, "rendered": b["rendered_frames"] - a["rendered_frames"],
              "post_fec": b["lost_packets"] - a["lost_packets"], "fec_rec": b["fec_recovered_packets"] - a["fec_recovered_packets"],
              "unrec": b["fec_unrecoverable_groups"] - a["fec_unrecoverable_groups"], "resyncs": b["stream_resyncs"] - a["stream_resyncs"],
              "underruns": b["audio_underruns"] - a["audio_underruns"],
              "concealed": b["audio_concealed_underruns"] - a["audio_concealed_underruns"],
              "freq": b.get("link_frequency_mhz"), "rssi": b.get("link_rssi_dbm")}
        intervals.append(iv)
        r = rows[k]
        r.update({"hb_interval_s": round(dt, 2), "rendered": iv["rendered"], "rendered_per_s": round(iv["rendered"] / dt, 1) if dt else None,
                  "post_fec": iv["post_fec"], "underruns": iv["underruns"]})
maps = []
for s in hb_sessions:
    off = statistics.median(ts(h["received_at_utc"]).timestamp() * 1000 - h["elapsed_ms"] for h in s)
    maps.append((ts(s[0]["received_at_utc"]), ts(s[-1]["received_at_utc"]), off))
hb_times = sorted(ts(h["received_at_utc"]) for h in hb)

# ---------------------------------------------------------------- control gaps
gaps = []
for g in gaps_raw:
    st, en = ts(g["start_utc"]), ts(g["end_utc"])
    pause = any(st <= e <= en + timedelta(seconds=1) for e in ends)
    gaps.append({"start": st, "end": en, "gap_ms": g["gap_ms"], "pause": pause})
    r = rows[sec(st)]
    r.setdefault("ctrl_gaps", []).append(f"{round(g['gap_ms'])}(pause)" if pause else round(g["gap_ms"]))
    if not pause:
        r["ctrl_gap_max"] = max(r.get("ctrl_gap_max", 0), g["gap_ms"])

# ---------------------------------------------------------------- ladder samples (G from output_gap_ms), levels
levels = []
for a in lad:
    if a.get("event") == "sample":
        t = ts(a["at_utc"])
        levels.append((t, a.get("level_kbps")))
        if (a.get("output_gap_ms") or 0) >= 200:
            rows[sec(t)]["out_gap_ladder"] = a["output_gap_ms"]

# ---------------------------------------------------------------- client reports: G rows by the elapsed map
for name, d in reports:
    rep, end = d["report"], ts(d["received_at_utc"])
    m = [x for x in maps if x[0] - timedelta(seconds=5) <= end <= x[1] + timedelta(seconds=30)]
    if not m:
        continue
    off = m[-1][2]
    seen = set()
    for evs in (rep.get("slow_events_top_gap") or [], rep.get("slow_events_ge_50_ms") or []):
        for e in evs:
            if e[6] >= 200 and (e[0], e[6]) not in seen:
                seen.add((e[0], e[6]))
                k = sec(datetime.fromtimestamp((off + e[0]) / 1000, timezone.utc))
                rows[k]["out_gap_report"] = max(rows[k].get("out_gap_report", 0), e[6])

# ---------------------------------------------------------------- the score (seconds inside a client session only)
for k in [k for k in rows if not in_session(ts(k))]:
    rows.pop(k)
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

# ---------------------------------------------------------------- the stack's rows, tagged
STACK = ("state_saved", "desync_pause", "input_hold_handover", "hold_return_armed", "input_release", "input_hold_skipped_paused",
         "state_save_skipped", "rewind_done", "rewind_skipped", "rewind_failed", "stall_pause", "stall_handover_v2",
         "client_ready_after_hold", "client_ready_after_stall", "resumed")


def dark_near(t, span=3.0):
    i = bisect.bisect_left(hb_times, t)
    prev = hb_times[i - 1] if i else None
    nxt = hb_times[i] if i < len(hb_times) else None
    return bool(prev and nxt and (nxt - prev).total_seconds() >= span + 2.0)    # heartbeats every ~2 s


stack = []
for r in rec:
    if r["event"] not in STACK:
        continue
    t = ts(r["at_utc"])
    row = {"at_utc": r["at_utc"], "event": r["event"], "lines": lines_at(t), "path": path_at(t),
           **{k: v for k, v in r.items() if k not in ("schema", "at_utc", "event", "state")}}
    if r["event"] == "desync_pause":
        g = next((g for g in gaps if g["start"] - timedelta(seconds=0.2) <= t <= g["end"] + timedelta(seconds=0.2)), None)
        real = bool(g and g["gap_ms"] >= 3000) or dark_near(t)
        row["tag"] = "REAL DROP" if real else "FALSE HOLD"
        row["gap_ms"] = round(g["gap_ms"]) if g else None
        row["cause"] = ("user (Home / exit): the gap contains a session_ended" if g and g["pause"] else
                        "link" if real else "the link alive on both sides")
        onset = g["start"] if g else t - timedelta(milliseconds=r.get("age_ms") or 0)
        sv = [x for x in rec if x["event"] == "state_saved" and onset - timedelta(seconds=0.1) <= ts(x["at_utc"]) <= t]
        rw = [x for x in rec if x["event"].startswith("rewind_") and t <= ts(x["at_utc"]) <= (g["end"] if g else t) + timedelta(seconds=30)]
        ho = [x for x in rec if x["event"] == "input_hold_handover" and t <= ts(x["at_utc"]) <= t + timedelta(seconds=30)]
        row["cost"] = {"unattended_before_pause_ms": round((t - onset).total_seconds() * 1000),
                       "save_after_onset_ms": sv[-1].get("save_after_onset_ms") if sv else None,
                       "held_ms_at_handover": ho[0].get("held_ms") if ho else None,
                       "away_s": round(g["gap_ms"] / 1000, 1) if g else None,
                       "rewind": (rw[0]["event"] + " " + json.dumps({k: rw[0].get(k) for k in ("frames_restored", "net_unattended_frames", "reason") if k in rw[0]})) if rw else "none logged (the return was a new client session)"}
    stack.append(row)
holds = [x for x in stack if x["event"] == "desync_pause"]

# ---------------------------------------------------------------- per client session
def in_(t, a, b):
    return a <= t <= b


fast_t = [(ts(r["at_utc"]), r) for r in fast]
sess_rows = []
for i, (st, en) in enumerate(sessions):
    en = en or st
    ivs = [v for v in intervals if in_(v["t"], st, en + timedelta(seconds=3))]
    dur = sum(v["dt"] for v in ivs)
    rendered = sum(v["rendered"] for v in ivs)
    rep = next(((n, d) for n, d in reports if in_(ts(d["received_at_utc"]), en - timedelta(seconds=5), en + timedelta(seconds=90))), (None, None))
    if rep[0] is None:          # a report sent late (the client waited, "reconnecting", after the stream ended): its duration runs past the end
        rep = next(((n, d) for n, d in reports if in_(ts(d["received_at_utc"]), en, en + timedelta(minutes=30))
                    and in_(ts(d["received_at_utc"]) - timedelta(milliseconds=d["report"]["duration_ms"]), st - timedelta(seconds=30), en)), (None, None))
    rn, rd = rep
    rr = rd["report"] if rd else {}
    dec, aud = rr.get("decoder") or {}, rr.get("audio") or {}
    core = (rr.get("capture_description") or "").split("RetroArch ")[-1].split(" ")[0] if rr else None
    lv = [v for t, v in levels if in_(t, st, en)]
    fx = [r for t, r in fast_t if in_(t, st, en) and r.get("active")]
    tx = [r["tailnet_tx_kbps"] for r in fx if isinstance(r.get("tailnet_tx_kbps"), (int, float))]
    pay = sum(f["payload_bytes"] for f in fsz if in_(ts(f["at_utc"]), st, en))
    hs = [k for k, r in rows.items() if r.get("score") and in_(ts(k), st, en)]
    sil = [g for g in gaps if not g["pause"] and g["gap_ms"] >= 250 and in_(g["start"], st, en)]
    hd = [x for x in holds if in_(ts(x["at_utc"]), st, en + timedelta(seconds=1))]
    paths = sorted({path_at(t) for t, _ in fast_t if in_(t, st, en)} or {path_at(st)})
    mins = dur / 60 if dur else 0
    sess_rows.append({
        "n": i + 1, "start": sec(st), "end": sec(en), "play_min": round(mins, 2), "core": core, "lines": lines_at(st),
        "paths": "/".join(paths), "levels_kbps": "→".join(str(x) for j, x in enumerate(lv) if j == 0 or lv[j - 1] != x) or None,
        "rendered_fps": round(rendered / dur, 2) if dur else None,
        "post_fec_lost": sum(v["post_fec"] for v in ivs), "post_fec_per_min": round(sum(v["post_fec"] for v in ivs) / mins, 2) if mins else None,
        "fec_recovered": sum(v["fec_rec"] for v in ivs), "fec_unrec": sum(v["unrec"] for v in ivs),
        "resyncs": sum(v["resyncs"] for v in ivs), "underruns_hb": sum(v["underruns"] for v in ivs),
        "concealed_hb": sum(v["concealed"] for v in ivs),
        "hitch_s": len(hs), "hitch_per_10min": round(len(hs) / mins * 10, 1) if mins else None,
        "silences_ge_250": len(sil), "holds": len(hd), "false_holds": sum(1 for x in hd if x["tag"] == "FALSE HOLD"),
        "report": rn, "report_min": round(rr.get("duration_ms", 0) / 60000, 2) if rr else None,
        "spike_20": dec.get("spike_20_ms"), "spike_50": dec.get("spike_50_ms"),
        "spike_20_per_min": round(dec["spike_20_ms"] / (rr["duration_ms"] / 60000), 1) if dec.get("spike_20_ms") is not None and rr.get("duration_ms") else None,
        "spike_50_per_min": round(dec["spike_50_ms"] / (rr["duration_ms"] / 60000), 1) if dec.get("spike_50_ms") is not None and rr.get("duration_ms") else None,
        "max_output_gap_ms": dec.get("max_output_gap_ms"), "report_underruns": aud.get("underruns"), "audio_lost": aud.get("lost_packets"),
        "discontinuities": len(rr.get("stream_discontinuities") or []) if rr else None,
        "tailnet_tx_kbps_median": med(tx), "tailnet_samples": len(tx), "video_payload_mb": round(pay / 1e6, 1),
        "wifi_mhz": med([v["freq"] for v in ivs]), "rssi_dbm": med([v["rssi"] for v in ivs])})

# ---------------------------------------------------------------- per 10 min (wall clock, play seconds only)
bins = defaultdict(lambda: {"play_s": 0.0, "rendered": 0, "post_fec": 0, "underruns": 0, "resyncs": 0, "hitch": 0, "sil": 0,
                            "holds": 0, "false": 0, "levels": [], "tx": [], "paths": set(), "lines": set()})
bkey = lambda t: t.strftime("%Y-%m-%dT%H:") + f"{t.minute // 10}0"
for v in intervals:
    b = bins[bkey(v["t"])]
    b["play_s"] += v["dt"]
    b["rendered"] += v["rendered"]
    b["post_fec"] += v["post_fec"]
    b["underruns"] += v["underruns"]
    b["resyncs"] += v["resyncs"]
    b["lines"].add(lines_at(v["t"]))
for k, r in rows.items():
    if r.get("score"):
        bins[bkey(ts(k))]["hitch"] += 1
for g in gaps:
    if not g["pause"]:
        bins[bkey(g["start"])]["sil"] += 1
for x in holds:
    bins[bkey(ts(x["at_utc"]))]["holds"] += 1
    bins[bkey(ts(x["at_utc"]))]["false"] += x["tag"] == "FALSE HOLD"
for t, v in levels:
    bins[bkey(t)]["levels"].append(v)
for t, r in fast_t:
    if r.get("active") and isinstance(r.get("tailnet_tx_kbps"), (int, float)):
        bins[bkey(t)]["tx"].append(r["tailnet_tx_kbps"])
    bins[bkey(t)]["paths"].add(path_at(t))
bin_rows = []
for k in sorted(bins):
    b = bins[k]
    if b["play_s"] < 30:
        continue
    m = b["play_s"] / 60
    bin_rows.append({"bin_utc": k, "play_min": round(m, 1), "lines": "/".join(map(str, sorted(b["lines"]))),
                     "paths": "/".join(sorted(b["paths"])) or "not sampled", "rendered_fps": round(b["rendered"] / b["play_s"], 2),
                     "hitch_s": b["hitch"], "hitch_per_10min": round(b["hitch"] / m * 10, 1), "silences_ge_250": b["sil"],
                     "holds": b["holds"], "false_holds": b["false"], "post_fec_per_min": round(b["post_fec"] / m, 2),
                     "underruns": b["underruns"], "resyncs": b["resyncs"],
                     "level_kbps_median": med(b["levels"]), "level_kbps_range": f"{min(b['levels'])}-{max(b['levels'])}" if b["levels"] else None,
                     "tailnet_tx_kbps_median": med(b["tx"])})

# ---------------------------------------------------------------- the wire, the data, RTT, the path
def tx_span(a, b):
    xs = [(t, r) for t, r in fast_t if a <= t <= b and isinstance(r.get("tailnet_tx_bytes"), int)]
    if len(xs) < 2:
        return None
    return {"from": sec(xs[0][0]), "to": sec(xs[-1][0]), "mb": round((xs[-1][1]["tailnet_tx_bytes"] - xs[0][1]["tailnet_tx_bytes"]) / 1e6, 1),
            "rx_mb": round((xs[-1][1]["tailnet_rx_bytes"] - xs[0][1]["tailnet_rx_bytes"]) / 1e6, 1) if xs[0][1].get("tailnet_rx_bytes") is not None else None,
            "hours": round((xs[-1][0] - xs[0][0]).total_seconds() / 3600, 3)}


a1 = tx_span(ts("2026-10-24T19:27:32Z"), ts("2026-10-24T19:42:30Z"))
a2 = tx_span(ts("2026-10-24T19:56:52Z"), ts("2026-10-24T21:21:00Z"))
four = tx_span(ts(FOUR[0] + "Z"), ts(FOUR[1] + "Z"))
play_four_s = sum(v["dt"] for v in intervals if lines_at(v["t"]) == 14)
by_level = defaultdict(list)
for t, r in fast_t:
    if r.get("active") and isinstance(r.get("tailnet_tx_kbps"), (int, float)) and r.get("bitrate_kbps"):
        by_level[r["bitrate_kbps"]].append(r["tailnet_tx_kbps"])
wan = [r for r in slow if isinstance(r.get("wan"), dict)]
rtt = [(r["at_utc"][11:19], (r["wan"].get("measures") or {}).get("rtt_ms", {}).get("value")) for r in wan]
path_seq = []
for t, r in slow_t:
    p = r["overlay"].get("path")
    if not path_seq or path_seq[-1][1] != p:
        path_seq.append((sec(t), p))
wan_last = wan[-1]["wan"] if wan else {}

# ---------------------------------------------------------------- the totals
play_s = sum(v["dt"] for v in intervals)
hit = [k for k, r in rows.items() if r.get("score")]
startup = sum(1 for k in hit if any(0 <= (ts(k) - s).total_seconds() < 15 for s in starts))
sil = [g for g in gaps if not g["pause"] and g["gap_ms"] >= 250]


def tot(sel):
    ivs = [v for v in intervals if sel(v["t"])]
    s_ = sum(v["dt"] for v in ivs)
    h = [k for k in hit if sel(ts(k))]
    m = s_ / 60
    return {"play_min": round(m, 1), "hitch_s": len(h), "hitch_per_10min": round(len(h) / m * 10, 2) if m else None,
            "hitch_s_in_first_15s_of_a_session": sum(1 for k in h if any(0 <= (ts(k) - s).total_seconds() < 15 for s in starts)),
            "silences_ge_250": sum(1 for g in sil if sel(g["start"])),
            "silences_per_10min": round(sum(1 for g in sil if sel(g["start"])) / m * 10, 2) if m else None,
            "holds": sum(1 for x in holds if sel(ts(x["at_utc"]))),
            "false_holds": sum(1 for x in holds if sel(ts(x["at_utc"])) and x["tag"] == "FALSE HOLD"),
            "post_fec_per_min": round(sum(v["post_fec"] for v in ivs) / m, 2) if m else None,
            "rendered_fps": round(sum(v["rendered"] for v in ivs) / s_, 2) if s_ else None,
            "underruns_hb": sum(v["underruns"] for v in ivs), "resyncs": sum(v["resyncs"] for v in ivs),
            "by_criterion": {c: sum(1 for k in h if c in rows[k]["crit"]) for c in "RCGL"}}


counts = {
    "whole_play": tot(lambda t: True),
    "four_lines": tot(lambda t: lines_at(t) == 14),
    "ten_lines_afternoon": tot(lambda t: lines_at(t) == 10 and sec(t) < "2026-10-24T22"),
    "ten_lines_evening_0120": tot(lambda t: sec(t) >= "2026-10-25T00"),
    "client_sessions": len(sessions),
    "heartbeat_intervals_outside_sessions": {"n": len(outside), "minutes": round(sum(x["dt"] for x in outside) / 60, 1),
                                             "rendered": sum(x["rendered"] for x in outside), "underruns": sum(x["underruns"] for x in outside),
                                             "spans": sorted({x["t"][:15] + "x" for x in outside})},
    "control_gaps_all": [{"start": sec(g["start"]), "gap_ms": round(g["gap_ms"]), "pause": g["pause"]} for g in gaps],
    "tailnet": {"attempt1_sampled": a1, "attempt2_sampled": a2, "four_lines_span": four,
                "four_lines_mb_per_hour_of_span": round(four["mb"] / four["hours"]) if four else None,
                "four_lines_play_min": round(play_four_s / 60, 1),
                "tx_kbps_median_by_rung": {k: {"median": med(v), "n": len(v)} for k, v in sorted(by_level.items())}},
    "video_payload_mb_per_play_hour": round(sum(f["payload_bytes"] for f in fsz) / 1e6 / (play_s / 3600)) if play_s else None,
    "rtt_ms_by_wan_sample": rtt[::10] + ([rtt[-1]] if rtt else []),
    "path_sequence": path_seq,
    "wan_last": {k: wan_last.get(k) for k in ("reports", "windows", "class", "window_counts", "loss_per_min_post_fec", "stale_per_min")},
    "wan_last_measures": {k: (wan_last.get("measures") or {}).get(k, {}).get("value") for k in ("delivered_goodput_kbps", "packet_loss_per_min", "rtt_ms", "jitter_ms")},
    "holds": holds,
    "start_rungs": [{"at": a["at_utc"], **a["start_rung"]} for a in lad if isinstance(a.get("start_rung"), dict)],
    "transitions": [f"{a['at_utc'][11:19]} {a.get('stream_kbps')}→{a.get('level_kbps')} {a.get('reason')}" for a in lad if a.get("event") == "transition"],
    "remote_cap_refusals": sum(1 for a in lad if a.get("source") == "remote_cap" and a.get("event") != "remote_cap_config"),
}

# ---------------------------------------------------------------- write
def tsv(name, rs):
    if not rs:
        return
    cols = list(rs[0].keys())
    with open(os.path.join(HERE, name), "w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rs:
            f.write("\t".join("" if r.get(c) is None else (json.dumps(r[c]) if isinstance(r[c], (dict, list)) else str(r[c])) for c in cols) + "\n")


tsv("sessions.tsv", sess_rows)
tsv("bins_10min.tsv", bin_rows)
tsv("stack_rows.tsv", [{k: x.get(k) for k in ("at_utc", "event", "lines", "path", "tag", "cause", "gap_ms", "trigger", "kind", "reason", "via",
                                              "age_ms", "held_ms", "silence_ms", "save_after_onset_ms", "cost")} for x in stack])
SC = ["crit", "score", "rendered", "hb_interval_s", "rendered_per_s", "post_fec", "ctrl_gaps", "out_gap", "underruns"]
with open(os.path.join(HERE, "seconds.tsv"), "w") as f:
    f.write("utc\t" + "\t".join(SC) + "\n")
    for k in sorted(rows):
        f.write(k + "\t" + "\t".join("" if rows[k].get(c) is None else (",".join(map(str, rows[k][c])) if isinstance(rows[k][c], list) else str(rows[k][c])) for c in SC) + "\n")
json.dump(counts, open(os.path.join(HERE, "counts.json"), "w"), indent=1, default=str)
out = [json.dumps({k: counts[k] for k in ("whole_play", "four_lines", "ten_lines_afternoon", "ten_lines_evening_0120", "client_sessions", "heartbeat_intervals_outside_sessions",
                                            "tailnet", "video_payload_mb_per_play_hour", "path_sequence", "wan_last", "wan_last_measures",
                                            "remote_cap_refusals", "transitions")}, indent=1, default=str)]
out.append("\nhitch seconds (all): " + ", ".join(f"{k[11:]} {rows[k]['crit']}" for k in sorted(hit)))
out.append("\nholds: " + json.dumps(holds, indent=1, default=str))
open(os.path.join(HERE, "read_console.txt"), "w").write("\n".join(out) + "\n")
print("\n".join(out))
