#!/usr/bin/env python3
"""UX-R2 §1 (UX-R1's timeline script, parameterised by the span): one evening from the preserved copies, read-only.
    ux_r2_timeline.py EVE_START EVE_END   (UTC, e.g. 2026-10-21T04:42 2026-10-21T05:27; the span must not cross 00:00Z)

Per client session (one decoder health report each): title / core, start / end, and the per-minute rates.
Per wall-clock minute: the heartbeat deltas (rendered, loss, FEC, resyncs, underruns, concealment, starvation,
arrival gaps), host control gaps, the ladder rung, host CPU / load, the wire rate.
Then: the first 5 minutes against the rest, SNES against PS1, and the same per-report rates for the week's
windows (2026-10-15..19 before the span) and for 2026-09-21 (D-BASE-S1 / S2).
    ux_r1_timeline.py            -> timeline.txt + timeline.json beside this script
"""
import glob, json, os, re, statistics, sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "session/logs/games")
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
LIVE_REPORTS = os.path.join(ROOT, "logs/games/decoder_sessions")
EVE_START, EVE_END = sys.argv[1], sys.argv[2]
DAY = EVE_START[:10]
EDT = timezone(timedelta(hours=-4))


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def jl(p):
    for line in open(p, errors="replace"):
        try:
            yield json.loads(line)
        except ValueError:
            pass


# ---- games: title / core / start from the game logs (file names are host-local time) ----
games = []
for p in sorted(glob.glob(os.path.join(S, "20261*-game_*.log"))):
    stamp = re.match(r"(\d{8}-\d{6})", os.path.basename(p)).group(1)
    start = datetime.strptime(stamp, "%Y%m%d-%H%M%S").replace(tzinfo=EDT).astimezone(timezone.utc)
    txt = open(p, errors="replace").read(4000)
    title = re.search(r"^Title: (.*)$", txt, re.M).group(1)
    core = re.search(r"^Core: (.*)$", txt, re.M).group(1).replace("_libretro.so", "")
    games.append({"start": start, "title": title, "core": core,
                  "system": "SNES" if "snes" in os.path.basename(p) else "PS1"})
games = [g for g in games if g["start"].isoformat() >= EVE_START]


def game_at(t):
    cur = None
    for g in games:
        if g["start"] <= t:
            cur = g
    return cur


# ---- per-report summary (the client's health report) ----
def summarize(path):
    d = json.load(open(path))
    r = d["report"]
    end = ts(d["received_at_utc"])
    dur_s = r["duration_ms"] / 1000
    m = dur_s / 60 or 1
    # older reports (September, PCM) lack some fields: missing counters read 0, missing gauges None
    v, dec, a = (defaultdict(int, r.get(k) or {}) for k in ("video", "decoder", "audio"))
    o = a.get("opus") or {}
    unit_ms = 10 if a.get("codec") == "opus" else 5
    out = {
        "report": os.path.basename(path), "end_utc": end.strftime("%H:%M:%S"),
        "start_utc": (end - timedelta(seconds=dur_s)).strftime("%H:%M:%S"),
        "start_dt": end - timedelta(seconds=dur_s), "dur_min": round(m, 2),
        "codec": a.get("codec", "pcm"), "capture": r.get("capture_description", "").splitlines()[0][:60],
        "rendered_fps": round(dec["rendered_frames"] / dur_s, 2) if dur_s and dec["rendered_frames"] else None,
        # lost_packets is post-FEC (MEMORY.md: "video loss ... (post-FEC)"); FEC recoveries are counted apart
        "post_fec_loss_per_min": round(v["lost_packets"] / m, 1),
        "fec_rec_per_min": round(v["fec_recovered_packets"] / m, 1),
        "fec_unrec_per_min": round(v["fec_unrecoverable_groups"] / m, 2),
        "stale_per_min": round(dec["stale_output_drops"] / m, 1),
        "resyncs": v["sequence_resyncs"], "ssrc_changes": v["ssrc_changes"],
        "underruns_per_min": round(a["underruns"] / m, 2), "underruns": a["underruns"],
        "concealed_underruns_per_min": round(a["concealed_underruns"] / m, 1),
        "starvation_per_min": round(a["prolonged_starvation_events"] / m, 1),
        "net_audio_loss_ms_per_min": round(a["lost_packets"] * unit_ms / m, 1),
        "arrival_holes_per_min": round((a["arrival_holes"] or {}).get("total", 0) / m, 1),
        "max_queue_residence_ms": a["max_queue_residence_ms"],
        "spike50_per_min": round(dec["spike_50_ms"] / m, 2), "spike250_per_min": round(dec["spike_250_ms"] / m, 2),
        "max_output_gap_ms": dec["max_output_gap_ms"], "max_codec_ms": dec["max_codec_ms"],
        "max_rx_to_decode_ms": dec["max_rx_to_decode_ms"], "dec_queue_max": dec["max_queue_depth"],
        "opus_q_depth_max": o.get("decode_queue_depth_max"),
        "opus_q_wait_max_ms": round(o["decode_queue_wait_max_us"] / 1000, 1) if o.get("decode_queue_wait_max_us") is not None else None,
        "opus_decode_avg_us": round(o["decode_avg_us"]) if o.get("decode_avg_us") is not None else None,
        "opus_decode_max_ms": round(o["decode_max_us"] / 1000, 1) if o.get("decode_max_us") is not None else None,
        "opus_decode_errors": o.get("decode_errors"), "opus_drain_timeouts": o.get("drain_timeouts"),
        "thermal_status_max": r.get("thermal", {}).get("status_max"),
    }
    return out


eve = sorted((summarize(p) for p in glob.glob(os.path.join(S, "decoder_sessions/*.json"))),
             key=lambda x: x["start_dt"])
eve = [x for x in eve if x["start_dt"].isoformat() >= EVE_START]
for x in eve:
    g = game_at(x["start_dt"] + timedelta(seconds=5))
    x.update({"title": g["title"] if g else "?", "system": g["system"] if g else "?", "core": g["core"] if g else "?"})

# ---- per wall-clock minute: heartbeat deltas (counters are cumulative per client session) ----
hb = [h for h in jl(os.path.join(S, "native_stream_heartbeat.log"))
      if EVE_START <= h.get("received_at_utc", "") < EVE_END]
CUM = ["rendered_frames", "lost_packets", "fec_recovered_packets", "fec_unrecoverable_groups", "stream_resyncs",
       "audio_underruns", "audio_concealed_underruns", "audio_prolonged_starvation_events", "audio_lost_packets"]
minute = defaultdict(lambda: defaultdict(float))
prev = None
for h in hb:
    t = ts(h["received_at_utc"])
    k = t.strftime("%H:%M")
    if prev is not None and h["sequence"] > prev["sequence"]:
        for c in CUM:
            minute[k][c] += max(0, h.get(c, 0) - prev.get(c, 0))
        minute[k]["hb_s"] += (h["elapsed_ms"] - prev["elapsed_ms"]) / 1000
    minute[k]["max_audio_arrival_gap_ms"] = max(minute[k]["max_audio_arrival_gap_ms"], h.get("audio_max_arrival_gap_ms", 0))
    minute[k]["max_output_age_ms"] = max(minute[k]["max_output_age_ms"], h.get("last_output_age_ms", 0))
    prev = h
for g in jl(os.path.join(S, "native_stream_ctrl_gaps.log")):
    if EVE_START <= g.get("start_utc", "") < EVE_END:
        k = g["start_utc"][11:16]
        minute[k]["ctrl_gaps"] += 1
        if g["gap_ms"] > 1000:
            minute[k]["ctrl_gaps_gt1s"] += 1
        minute[k]["ctrl_gap_max_ms"] = max(minute[k]["ctrl_gap_max_ms"], g["gap_ms"])
rung = {}
for r in jl(os.path.join(S, "adaptive_bitrate_shadow.jsonl")):
    if EVE_START <= r.get("at_utc", "") < EVE_END and r.get("level_kbps"):
        rung[r["at_utc"][11:16]] = r["level_kbps"]
host = defaultdict(list)
for s in jl(os.path.join(S, "host_resource_samples.jsonl")):
    if EVE_START <= s.get("at_utc", "") < EVE_END:
        p = s.get("procs", {})
        host[s["at_utc"][11:16]].append((s["loadavg"][0], (p.get("retroarch") or {}).get("cpu_pct"),
                                         (p.get("encoder") or {}).get("cpu_pct"), s.get("host_thermal_c")))
wire = defaultdict(float)
tail = defaultdict(lambda: defaultdict(int))   # the frame-size tail per minute (MEMORY.md: loss tracks the tail)
for f in jl(os.path.join(S, "native_frame_sizes.jsonl")):
    if EVE_START <= f.get("at_utc", "") < EVE_END:
        k = f["at_utc"][11:16]
        wire[k] += f.get("payload_bytes", 0) * 8 / 1000 / 60
        tail[k]["ge40"] += f.get("frames_ge_40", 0)
        tail[k]["ge80"] += f.get("frames_ge_80", 0)
        tail[k]["over_cap"] += f.get("frames_over_cap", 0)
        tail[k]["max_pk"] = max(tail[k]["max_pk"], f.get("max_packets", 0))
recov = [r for r in jl(os.path.join(S, "native_stream_recovery.log"))
         if EVE_START <= r.get("at_utc", "") < EVE_END and r["event"] not in ("session_started", "session_ended")]

rows = []
for k in sorted(minute):
    mm = minute[k]
    hs = mm["hb_s"] or None
    t = datetime.fromisoformat(f"{DAY}T{k}:30+00:00")
    g = game_at(t)
    hv = host.get(k, [])
    rows.append({
        "utc": k, "system": g["system"] if g else "?", "title": (g["title"] if g else "?")[:22],
        "fps": round(mm["rendered_frames"] / hs, 1) if hs else None, "hb_s": round(mm["hb_s"]),
        "post_fec": int(mm["lost_packets"]), "fec_rec": int(mm["fec_recovered_packets"]),
        "unrec": int(mm["fec_unrecoverable_groups"]), "resync": int(mm["stream_resyncs"]),
        "underruns": int(mm["audio_underruns"]), "concealed": int(mm["audio_concealed_underruns"]),
        "starv": int(mm["audio_prolonged_starvation_events"]), "a_lost": int(mm["audio_lost_packets"]),
        "a_gap_max": int(mm["max_audio_arrival_gap_ms"]), "out_age_max": int(mm["max_output_age_ms"]),
        "ctrl_gt1s": int(mm["ctrl_gaps_gt1s"]), "ctrl_max": int(mm["ctrl_gap_max_ms"]),
        "rung": rung.get(k), "kbit_s": round(wire.get(k, 0)),
        "ge40": tail[k]["ge40"], "ge80": tail[k]["ge80"], "max_pk": tail[k]["max_pk"],
        "load1": round(statistics.mean(h[0] for h in hv), 2) if hv else None,
        "ra_cpu": round(statistics.mean(h[1] for h in hv if h[1] is not None), 1) if any(h[1] is not None for h in hv) else None,
        "enc_cpu": round(statistics.mean(h[2] for h in hv if h[2] is not None), 1) if any(h[2] is not None for h in hv) else None,
        "host_c": round(max(h[3] for h in hv if h[3] is not None), 1) if any(h[3] is not None for h in hv) else None,
    })


# ---- does the loss follow the frame-size tail tonight? (Spearman over full minutes) ----
def spearman(x, y):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for kk in range(i, j + 1):
                r[o[kk]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    return round(statistics.correlation(rx, ry), 3) if len(x) > 2 else None


full = [r for r in rows if r["hb_s"] >= 50]
tail_corr = {"minutes": len(full),
             "rho_post_fec_vs_frames_ge40": spearman([r["post_fec"] for r in full], [r["ge40"] for r in full]),
             "rho_post_fec_vs_max_packets": spearman([r["post_fec"] for r in full], [r["max_pk"] for r in full]),
             "rho_post_fec_vs_minute_of_evening": spearman([r["post_fec"] for r in full], list(range(len(full)))),
             "rho_concealed_vs_post_fec": spearman([r["concealed"] for r in full], [r["post_fec"] for r in full]),
             "rho_concealed_vs_minute_of_evening": spearman([r["concealed"] for r in full], list(range(len(full)))),
             "rho_fec_rec_vs_frames_ge40": spearman([r["fec_rec"] for r in full], [r["ge40"] for r in full])}

# ---- aggregates: per-minute rates over a set of minutes ----
def agg(rs):
    rs = [r for r in rs if r["hb_s"] >= 30]
    n = sum(r["hb_s"] for r in rs) / 60
    if not n:
        return {}
    s = lambda f: sum(r[f] for r in rs)
    return {"minutes": round(n, 1), "fps": round(statistics.mean(r["fps"] for r in rs), 2),
            "post_fec/min": round(s("post_fec") / n, 1), "fec_rec/min": round(s("fec_rec") / n, 1),
            "unrec/min": round(s("unrec") / n, 2), "resyncs": s("resync"),
            "underruns/min": round(s("underruns") / n, 2), "concealed/min": round(s("concealed") / n, 1),
            "starvation/min": round(s("starv") / n, 1), "audio_lost/min": round(s("a_lost") / n, 2),
            "audio_gap_max_ms": max(r["a_gap_max"] for r in rs), "ctrl>1s": s("ctrl_gt1s"),
            "ctrl_max_ms": max(r["ctrl_max"] for r in rs),
            "kbit_s": round(statistics.mean(r["kbit_s"] for r in rs)),
            "frames_ge40/min": round(s("ge40") / n, 1), "frames_ge80/min": round(s("ge80") / n, 2),
            "loss_per_ge40_frame": round(s("post_fec") / s("ge40"), 2) if s("ge40") else None,
            "enc_cpu": round(statistics.mean(r["enc_cpu"] for r in rs if r["enc_cpu"] is not None), 1),
            "ra_cpu": round(statistics.mean(r["ra_cpu"] for r in rs if r["ra_cpu"] is not None), 1)}


FIRST_FRAME = eve[0]["start_dt"]
first5_end = (FIRST_FRAME + timedelta(minutes=5)).strftime("%H:%M")
cols = {f"first 5 min ({FIRST_FRAME:%H:%M}-{first5_end})": agg([r for r in rows if r["utc"] < first5_end]),
        f"after ({first5_end}-{EVE_END[11:]})": agg([r for r in rows if r["utc"] >= first5_end]),
        "PS1": agg([r for r in rows if r["system"] == "PS1"]),
        "SNES": agg([r for r in rows if r["system"] == "SNES"])}
for g, nxt in zip(games, games[1:] + [None]):
    lo, hi = g["start"].strftime("%H:%M"), (nxt["start"].strftime("%H:%M") if nxt else "99:99")
    cols[f"{g['system']} {g['title'][:28]}"] = agg([r for r in rows if lo <= r["utc"] < hi])


# ---- the comparison: the same per-report rates for other windows ----
def report_group(prefixes, lo=None, hi=None):
    out = []
    for p in sorted(glob.glob(os.path.join(LIVE_REPORTS, "*.json"))):
        if not any(os.path.basename(p).startswith("native_decoder_" + x) for x in prefixes):
            continue
        try:
            x = summarize(p)
        except (KeyError, ValueError, TypeError):
            continue
        if lo and x["start_dt"].isoformat() < lo or hi and x["start_dt"].isoformat() >= hi:
            continue
        if x["dur_min"] >= 1:
            out.append(x)
    return out


def report_rates(xs):
    if not xs:
        return {}
    tm = sum(x["dur_min"] for x in xs)
    w = lambda f: round(sum(x[f] * x["dur_min"] for x in xs if x[f] is not None) / tm, 2)
    mx = lambda f: max((x[f] for x in xs if x.get(f) is not None), default=None)
    return {"reports": len(xs), "minutes": round(tm, 1), "codecs": sorted({x["codec"] for x in xs}),
            "rendered_fps": w("rendered_fps"), "fec_rec/min": w("fec_rec_per_min"), "post_fec/min": w("post_fec_loss_per_min"),
            "unrec/min": w("fec_unrec_per_min"), "stale/min": w("stale_per_min"), "resyncs": sum(x["resyncs"] for x in xs),
            "underruns/min": w("underruns_per_min"), "concealed/min": w("concealed_underruns_per_min"),
            "starvation/min": w("starvation_per_min"), "net_audio_loss_ms/min": w("net_audio_loss_ms_per_min"),
            "arrival_holes/min": w("arrival_holes_per_min"), "spike50/min": w("spike50_per_min"),
            "spike250/min": w("spike250_per_min"), "max_output_gap_ms": mx("max_output_gap_ms"),
            "opus_q_wait_max_ms": mx("opus_q_wait_max_ms"), "opus_q_depth_max": mx("opus_q_depth_max"),
            "opus_decode_errors": sum(x["opus_decode_errors"] or 0 for x in xs)}


eve_ps1 = [x for x in eve if x["system"] == "PS1"]
eve_snes = [x for x in eve if x["system"] == "SNES"]
cut = (FIRST_FRAME + timedelta(minutes=5)).strftime("%H:%M:%S")
compare = {
    f"evening {EVE_START[11:]}-{EVE_END[11:]}Z (all)": report_rates(eve),
    f"evening, first 5 min of play (reports starting < {cut})": report_rates([x for x in eve if x["start_utc"] < cut]),
    "evening, after": report_rates([x for x in eve if x["start_utc"] >= cut]),
    "evening PS1": report_rates(eve_ps1), "evening SNES": report_rates(eve_snes),
}

# ---- the trend inside the evening: per report against minutes since the evening's first frame ----
t0 = eve[0]["start_dt"]
trend = [{"min_into_evening": round((x["start_dt"] - t0).total_seconds() / 60, 1), "system": x["system"],
          "dur_min": x["dur_min"], "underruns/min": x["underruns_per_min"], "concealed/min": x["concealed_underruns_per_min"],
          "post_fec/min": x["post_fec_loss_per_min"], "spike50/min": x["spike50_per_min"],
          "opus_q_wait_max_ms": x["opus_q_wait_max_ms"], "opus_decode_avg_us": x["opus_decode_avg_us"],
          "max_output_gap_ms": x["max_output_gap_ms"]} for x in eve]

# ---- write ----
with open(os.path.join(HERE, "timeline.json"), "w") as f:
    json.dump({"games": [{**g, "start": g["start"].isoformat()} for g in games],
               "reports": [{k: v for k, v in x.items() if k != "start_dt"} for x in eve],
               "minutes": rows, "recovery_rows": recov, "tail_correlation": tail_corr, "first5_vs_rest_and_by_game": cols,
               "compare_per_report": compare, "trend": trend}, f, indent=1, default=str)

L = []
p = L.append
p(f"UX-R2 timeline {EVE_START}-{EVE_END}Z (from the preserved copies; read-only)\n")
p("## Games (start UTC from the game log's host-local stamp)")
for g in games:
    p(f"  {g['start'].strftime('%H:%M:%S')}Z  {g['system']:4s} {g['core']:18s} {g['title']}")
p("\n## Client sessions (one health report each)")
hdr = ["start_utc", "end_utc", "dur_min", "system", "rendered_fps", "post_fec_loss_per_min", "fec_rec_per_min",
       "fec_unrec_per_min", "stale_per_min", "resyncs", "underruns", "underruns_per_min", "concealed_underruns_per_min",
       "starvation_per_min", "net_audio_loss_ms_per_min", "spike50_per_min", "spike250_per_min", "max_output_gap_ms",
       "max_codec_ms", "opus_q_depth_max", "opus_q_wait_max_ms", "opus_decode_avg_us", "opus_decode_errors",
       "opus_drain_timeouts", "thermal_status_max"]
p("  " + " | ".join(hdr))
for x in eve:
    p("  " + " | ".join(str(x[h]) for h in hdr) + f" | {x['title'][:30]}")
p("\n## Recovery rows (non start/end)")
for r in recov:
    p(f"  {r['at_utc'][11:23]} {r['event']} {r.get('trigger', '')} {r.get('recovering_ms', '')}")
p("\n## Per minute (UTC)")
mh = ["utc", "system", "fps", "hb_s", "post_fec", "fec_rec", "unrec", "resync", "underruns", "concealed", "starv",
      "a_lost", "a_gap_max", "out_age_max", "ctrl_gt1s", "ctrl_max", "rung", "kbit_s", "ge40", "ge80", "max_pk", "load1", "ra_cpu", "enc_cpu", "host_c"]
p("  " + " ".join(f"{h:>9s}" for h in mh))
for r in rows:
    p("  " + " ".join(f"{str(r[h]):>9s}" for h in mh))
p("\n## First 5 minutes against the rest; PS1 against SNES; per game (per-minute rates from the heartbeat)")
for k, v in cols.items():
    p(f"  {k}: {json.dumps(v)}")
p("\n## The same per-report rates, the evening against the week's windows and before October")
for k, v in compare.items():
    p(f"  {k}: {json.dumps(v)}")
p("\n## Does tonight's loss follow the frame-size tail? (Spearman, full minutes)")
p("  " + json.dumps(tail_corr))
p("\n## Trend: each client session against minutes into the evening")
for t in trend:
    p("  " + json.dumps(t))
open(os.path.join(HERE, "timeline.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
