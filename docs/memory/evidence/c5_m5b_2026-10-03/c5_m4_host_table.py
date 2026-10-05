#!/usr/bin/env python3
"""C5-M4 section 2 -- score the host table as pre-registered (c5_m4_preregistration.txt).

    c5_m4_host_table.py <runs dir>      -> prints the table; writes c5_m4_host_table_<runs dir name>.{txt,json} beside it

Per hold (a_<s>, b_<s>, c_<s>):
  R1  RetroArch's frame counter (<hold>_title.txt, "|| Frames: n" every 256 frames, xprop -spy
      timestamps): fps over the hold >= 59.88, and no 256-frame interval > 256/60 s + 12 ms. The
      estimated frames lost in long intervals = sum(round((dt - 256/60) * 60)).
  R2  (b, c) the encoder's capture rate: per-progress-line fps (delta frame / delta time= in the
      ffmpeg progress the companion writes to native_video_alpha.log, sliced per hold), median >= 59.5,
      and dup + drop <= 0.5 % of frames.
  R3  (b, c) codec_ms growth: NOT EVALUABLE as worded (no codec_ms in the C2 telemetry); substitutes
      are reported (see r3()). HOLDS 60 is read on R1 and R2.
  HOLDS 60: (a) R1; (b, c) R1 and R2.
Reported, not judged: host CPU mean / busiest logical CPU p95, GPU busy mean / p95, GPU power,
RetroArch and encoder CPU (% of one core), Tctl / GPU edge max; for b, c the client rows (fps,
spikes >= 20 ms/min, stale/min, video loss/min post-FEC, max gap), the per-second largest frame
p50/p90/max, cap hits s/min (>= 95 % of the cap), frames >= 80 packets/min, Mbit/s received, and the
adaptive controller's events in the hold.
"""
import glob, json, os, re, statistics, sys

R = sys.argv[1]
OUT_DIR = os.path.dirname(os.path.abspath(R))
NOMINAL = 256 / 60.0


def jl(p):
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p, errors="replace"):
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def pct(a, q):
    a = sorted(x for x in a if x is not None)
    return a[min(len(a) - 1, int(round(q * (len(a) - 1))))] if a else None


def mean(a):
    a = [x for x in a if x is not None]
    return statistics.fmean(a) if a else None


def r1(hold):
    rows = []
    for line in open(os.path.join(R, f"{hold}_title.txt"), errors="replace"):
        m = re.match(r"([0-9.]+) .*FPS:\s*([0-9.]+) \|\| Frames: (\d+)", line)
        if m:
            rows.append((float(m.group(1)), float(m.group(2)), int(m.group(3))))
    if len(rows) < 3:
        return {"r1": None, "note": "too few counter updates"}
    rows = rows[1:]                                  # the first update after the sampler starts may straddle
    dts = [(b[0] - a[0], b[2] - a[2]) for a, b in zip(rows, rows[1:])]
    iv = [dt for dt, df in dts if df == 256]
    span_f = rows[-1][2] - rows[0][2]
    span_t = rows[-1][0] - rows[0][0]
    fps = span_f / span_t if span_t else None
    long_iv = [dt for dt in iv if dt > NOMINAL + 0.012]
    lost = sum(max(0, round((dt - NOMINAL) * 60)) for dt in long_iv)
    ok = fps is not None and fps >= 59.88 and not long_iv
    return {"r1": ok, "ra_fps": round(fps, 3) if fps else None, "frames": span_f, "seconds": round(span_t, 1),
            "intervals": len(iv), "interval_median_ms": round(1000 * statistics.median(iv), 1) if iv else None,
            "interval_max_ms": round(1000 * max(iv), 1) if iv else None, "long_intervals": len(long_iv),
            "est_frames_lost": lost, "title_fps_min": min(r[1] for r in rows)}


def r2(hold):
    p = os.path.join(R, f"alpha_{hold}.log")
    if not os.path.exists(p):
        return {"r2": None}
    txt = open(p, errors="replace").read().replace("\r", "\n")
    pr = []
    for line in txt.splitlines():
        m = re.match(r"frame=\s*(\d+).*?time=(\d+):(\d+):([\d.]+)", line)
        if m:
            t = int(m.group(2)) * 3600 + int(m.group(3)) * 60 + float(m.group(4))
            dup = re.search(r"dup=(\d+)", line)
            drop = re.search(r"drop=(\d+)", line)
            pr.append((int(m.group(1)), t, int(dup.group(1)) if dup else 0, int(drop.group(1)) if drop else 0))
    pr = [x for x in pr if x[1] >= 5.0]              # past the encoder's start-up
    if len(pr) < 3:
        return {"r2": None}
    f = [(b[0] - a[0]) / (b[1] - a[1]) for a, b in zip(pr, pr[1:]) if b[1] > a[1]]
    med = statistics.median(f)
    frames = pr[-1][0] - pr[0][0]
    dd = (pr[-1][2] - pr[0][2]) + (pr[-1][3] - pr[0][3])
    overall = frames / (pr[-1][1] - pr[0][1])
    ok = med >= 59.5 and dd <= 0.005 * frames
    return {"r2": ok, "enc_fps_median": round(med, 2), "enc_fps_overall": round(overall, 3), "enc_frames": frames,
            "dup_drop": dd}


def r3(hold):
    """R3 as pre-registered named the C2 telemetry's codec_ms. The C2 per-report telemetry carries no
    codec_ms (its decoder block has queue and drop deltas; its latency block receive_to_decode_ms and
    output_gap_ms), so R3 is NOT EVALUABLE as worded and HOLDS 60 is read on R1 and R2. Reported
    beside it, as substitutes that decide nothing: the decoder report's per-slow-event codec_ms
    (events >= 50 ms) in the first and the last full minute, the report's max and end codec_ms, and the
    telemetry's receive_to_decode_ms median in the first and the last minute."""
    out = {"r3": None}
    rp = os.path.join(R, f"report_{hold}.json")
    if os.path.exists(rp):
        rep = json.load(open(rp))["report"]
        cols = rep.get("slow_event_columns") or []
        ev = rep.get("slow_events_ge_50_ms") or []
        if "elapsed_ms" in cols and "codec_ms" in cols:
            ie, ic = cols.index("elapsed_ms"), cols.index("codec_ms")
            end = rep["duration_ms"]
            f = [e[ic] for e in ev if 60000 <= e[ie] < 120000]
            l = [e[ic] for e in ev if end - 60000 <= e[ie] < end]
            out.update({"slow_ev_first_min": len(f), "slow_ev_last_min": len(l),
                        "slow_codec_med_first": statistics.median(f) if f else None,
                        "slow_codec_med_last": statistics.median(l) if l else None,
                        "slow_retained": rep.get("slow_event_retained"), "slow_capacity": rep.get("slow_event_capacity")})
        out["codec_max"] = rep["decoder"].get("max_codec_ms")
        out["codec_end"] = rep["decoder"].get("latest_codec_ms")
    rows = [r for r in jl(os.path.join(R, f"{hold}_telemetry.jsonl")) if r.get("fresh")]
    rtd = [(r.get("latency") or {}).get("receive_to_decode_ms") for r in rows]
    rtd = [v for v in rtd if v is not None]
    if len(rtd) >= 60:
        out["rx2dec_first_min_med"] = statistics.median(rtd[:30])
        out["rx2dec_last_min_med"] = statistics.median(rtd[-30:])
    return out


def host(hold):
    h = jl(os.path.join(R, f"{hold}_host.jsonl"))
    return {"cpu_mean": mean([r.get("cpu_mean_pct") for r in h]),
            "cpu_busiest_p95": pct([r.get("cpu_max_pct") for r in h], .95),
            "gpu_mean": mean([r.get("gpu_busy_pct") for r in h]), "gpu_p95": pct([r.get("gpu_busy_pct") for r in h], .95),
            "gpu_w": mean([r.get("gpu_power_w") for r in h]),
            "ra_cpu": mean([r.get("retroarch_cpu_pct") for r in h]), "enc_cpu": mean([r.get("encoder_cpu_pct") for r in h]),
            "tctl_max": max([r.get("tctl_c") or 0 for r in h] or [0]) or None,
            "gpu_edge_max": max([r.get("gpu_edge_c") or 0 for r in h] or [0]) or None, "host_samples": len(h),
            **t2_proc(hold)}


def t2_proc(hold):
    """RetroArch / encoder CPU from the T2 sampler (10 s) inside the hold's window. The RA% column is
    T2's for every hold: the 1 s sampler's RetroArch match is unreliable on the AppImage's process pair
    (none found on the 1x holds; a CPU-idle process of the pair from 2x on), so its ra_cpu is not used."""
    w = WINDOWS.get(hold)
    if not w:
        return {}
    rows = [r for r in jl(os.path.join(R, "t2_samples.jsonl")) if w[0] <= r.get("at_utc", "")[:19] + "Z" <= w[1]]
    return {"t2_ra_cpu": mean([((r.get("host") or {}).get("retroarch") or {}).get("cpu_pct") for r in rows]),
            "t2_enc_cpu": mean([((r.get("host") or {}).get("encoder") or {}).get("cpu_pct") for r in rows])}


def client(hold):
    rp = os.path.join(R, f"report_{hold}.json")
    if not os.path.exists(rp):
        return {}
    rep = json.load(open(rp))["report"]
    d, v = rep["decoder"], rep["video"]
    secs = rep["duration_ms"] / 1000.0
    m = secs / 60.0
    ac = json.load(open(os.path.join(R, f"armcheck_{hold}.json")))
    ov = ac.get("encoder_overrides") or {}
    cap = ov.get("max_frame_size_bytes")
    fr = jl(os.path.join(R, f"frames_{hold}.jsonl"))
    mx = [r.get("max_bytes", 0) for r in fr if r.get("frames")]
    dl = jl(os.path.join(R, f"decision_log_{hold}.jsonl"))
    ev = {}
    for r in dl:
        if r.get("event") != "sample":
            ev[r.get("event")] = ev.get(r.get("event"), 0) + 1
    return {"profile": ac.get("profile_id"), "size": f"{ac.get('width')}x{ac.get('height')}",
            "kbps": ac.get("bitrate_kbps"), "cap": cap, "any_override": ov.get("any_override"),
            "capture": f"{(ac.get('capture_target') or {}).get('width')}x{(ac.get('capture_target') or {}).get('height')}",
            "min": round(m, 2), "fps": round(d["rendered_frames"] / secs, 2), "spikes": round(d["spike_20_ms"] / m, 1),
            "stale": round(d["stale_output_drops"] / m, 2), "vloss": round(v["lost_packets"] / m, 2),
            "maxgap": d["max_output_gap_ms"], "max_codec_ms": d.get("max_codec_ms"),
            "mbps": round(8 * v["bytes"] / secs / 1e6, 2),
            "frmax_p50": pct(mx, .5), "frmax_p90": pct(mx, .9), "frmax_max": max(mx) if mx else None,
            "caphit_s_min": round(sum(1 for x in mx if cap and x >= 0.95 * cap) / m, 1) if cap else None,
            "ge80_min": round(sum(r.get("frames_ge_80", 0) for r in fr) / m, 1), "abr_events": ev}


holds = []
WINDOWS = {}
for line in open(os.path.join(R, "index.txt")):
    f = line.split()
    if f and f[0][:2] in ("a_", "b_", "c_"):
        ts = [x for x in f if re.match(r"\d{4}-\d\d-\d\dT", x)]
        if len(ts) >= 2:
            WINDOWS[f[0]] = (ts[0], ts[1])
    if f and re.match(r"[abc]_\w+$", f[0]) and f[0] not in holds:
        holds.append(f[0])
res = {}
for h in holds:
    row = {"hold": h}
    row.update(r1(h))
    if h.startswith("a_"):
        row["holds_60"] = row.get("r1")
    else:
        row.update(r2(h))
        row.update(r3(h))
        row["holds_60"] = all(row.get(k) for k in ("r1", "r2"))   # R3 not evaluable as worded (see r3)
    row.update(host(h))
    row.update(client(h))
    res[h] = row

F = lambda x, s="": "-" if x is None else format(x, s)
lines = ["C5-M4 host table -- " + os.path.relpath(R, OUT_DIR), "",
         f"{'hold':<7} {'HOLDS60':<7} {'RA fps':>7} {'lost':>4} {'ivmax':>6} {'enc fps':>7} {'dupdrop':>7} "
         f"{'slowcodec 1/L/max':>18} | {'CPU':>5} {'core95':>6} {'GPU':>5} {'GPU95':>5} {'GPU W':>5} {'RA%':>5} {'enc%':>5} "
         f"{'Tctl':>5} {'edge':>5}"]
for h, r in res.items():
    cod = "-" if r.get("codec_max") is None else f"{F(r.get('slow_codec_med_first'))}/{F(r.get('slow_codec_med_last'))}/{r['codec_max']}"
    lines.append(f"{h:<7} {str(r['holds_60']):<7} {F(r.get('ra_fps'), '.3f'):>7} {F(r.get('est_frames_lost')):>4} "
                 f"{F(r.get('interval_max_ms')):>6} {F(r.get('enc_fps_median')):>7} {F(r.get('dup_drop')):>7} {cod:>18} | "
                 f"{F(r['cpu_mean'], '.1f'):>5} {F(r['cpu_busiest_p95'], '.1f'):>6} {F(r['gpu_mean'], '.1f'):>5} "
                 f"{F(r['gpu_p95']):>5} {F(r['gpu_w'], '.1f'):>5} {F(r.get('t2_ra_cpu'), '.1f'):>5} {F(r['enc_cpu'], '.1f'):>5} "
                 f"{F(r['tctl_max'], '.1f'):>5} {F(r['gpu_edge_max'], '.1f'):>5}")
lines += ["", "R3 (codec_ms growth) is NOT EVALUABLE as pre-registered: the C2 per-report telemetry carries no codec_ms.",
          "HOLDS60 is read on R1 and R2. Substitutes (decide nothing): slow events (>= 50 ms) per minute and their",
          "codec_ms median, first full minute -> last minute; receive_to_decode_ms median first -> last minute.",
          f"{'hold':<7} {'slow ev 1st/last min':>20} {'codec med 1st/last':>18} {'codec max/end':>13} {'rx2dec 1st/last':>15}"]
for h, r in res.items():
    if h.startswith("a_"):
        continue
    lines.append(f"{h:<7} {F(r.get('slow_ev_first_min')) + '/' + F(r.get('slow_ev_last_min')):>20} "
                 f"{F(r.get('slow_codec_med_first')) + '/' + F(r.get('slow_codec_med_last')):>18} "
                 f"{F(r.get('codec_max')) + '/' + F(r.get('codec_end')):>13} "
                 f"{F(r.get('rx2dec_first_min_med')) + '/' + F(r.get('rx2dec_last_min_med')):>15}")
lines += ["", "client rows (b, c; reported, not judged)",
          f"{'hold':<7} {'profile':<36} {'capture':>9} {'min':>5} {'fps':>6} {'spk/m':>6} {'stale':>5} {'loss/m':>6} "
          f"{'gap':>4} {'codecmx':>7} {'Mbps':>6} {'frmax p50/p90/max':>20} {'cap s/m':>7} {'ge80/m':>6} abr events"]
for h, r in res.items():
    if "profile" not in r:
        continue
    lines.append(f"{h:<7} {str(r['profile'])[:36]:<36} {r['capture']:>9} {r['min']:5.2f} {r['fps']:6.2f} {r['spikes']:6.1f} "
                 f"{r['stale']:5.2f} {r['vloss']:6.2f} {r['maxgap']:4} {F(r['max_codec_ms']):>7} {r['mbps']:6.2f} "
                 f"{F(r['frmax_p50']):>6}/{F(r['frmax_p90']):>6}/{F(r['frmax_max']):>6} {F(r['caphit_s_min']):>7} "
                 f"{r['ge80_min']:6.1f} {json.dumps(r['abr_events'])}")
text = "\n".join(lines) + "\n"
print(text)
tag = os.path.basename(os.path.abspath(R))
open(os.path.join(OUT_DIR, f"c5_m4_host_table_{tag}.txt"), "w").write(text)
json.dump(res, open(os.path.join(OUT_DIR, f"c5_m4_host_table_{tag}.json"), "w"), indent=1)
