#!/usr/bin/env python3
"""E2-S1 -- the analysis of the 20-min runs, as pre-registered (e2_preregistration.txt, with amendment A1). Read-only.

    e2_analysis.py            -> e2_table.md, e2_conc.md, e2_snes.md, e2_memory.md, e2_analysis.json (in this dir)

  1. the E2 table: every row/run, the 20-min window statistics, E1's 5-min means beside (e1_s1 runs; VOD dry runs);
  2. the CONC question (s3): per-second series aligned on the grab bodies against the E1-PS1-STREAM baseline;
  3. the SNES question (s4); 4. the memory question (s5).
"""
import calendar
import glob
import json
import math
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
R = os.path.join(HERE, os.environ.get("E2_RUNS", "runs"))
E1 = os.path.join(HERE, "..", "e1_s1_2026-10-05", "runs")
E1VOD = os.path.join(HERE, "vod", "runs")
ROWS = ["E1-IDLE", "E1-PS1-LOCAL", "E1-PS1-STREAM", "E1-PS1-1080P", "E1-META", "E1-VOD", "E1-SNES-STREAM", "E1-CONC"]


def t(s):
    s = s.rstrip("Z")
    a, _, b = s.partition(".")
    return calendar.timegm(time.strptime(a, "%Y-%m-%dT%H:%M:%S")) + (float("0." + b) if b else 0.0)


def jl(path):
    out = []
    if os.path.exists(path):
        for line in open(path, errors="replace"):
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def runs_of(base, wid):
    return sorted(glob.glob(os.path.join(base, wid, "run*", "summary.json")))


def hm(summ, key, stat="mean"):
    v = ((summ.get("host") or {}).get("host") or {}).get(key)
    return v.get(stat) if v else None


def f(v, nd=1):
    if v is None:
        return "—"
    if isinstance(v, str):
        return v
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    return f"{v:.{nd}f}"


def sd(xs):
    return statistics.pstdev(xs) if len(xs) > 1 else 0.0


# ---------------------------------------------------------------- 1. the table
TABLE = [
    ("host CPU mean %", lambda s: hm(s, "cpu.mean_pct")),
    ("host CPU p95 %", lambda s: hm(s, "cpu.mean_pct", "p95")),
    ("busiest core p95 % (per-core p95, max)", lambda s: (s.get("host") or {}).get("busiest_core_p95")),
    ("busiest-core-per-second p95 %", lambda s: hm(s, "cpu.max_pct", "p95")),
    ("PSI cpu some ms/s", lambda s: hm(s, "psi_ms_per_s.cpu_some")),
    ("PSI io some ms/s", lambda s: hm(s, "psi_ms_per_s.io_some")),
    ("PSI mem some ms/s", lambda s: hm(s, "psi_ms_per_s.memory_some")),
    ("companion CPU % / PSS MB", lambda s: (hm(s, "procs.companion.cpu_pct"), (hm(s, "procs.companion.pss_kb") or 0) / 1024 or None)),
    ("RetroArch CPU % / PSS MB", lambda s: (hm(s, "procs.retroarch.cpu_pct"), (hm(s, "procs.retroarch.pss_kb") or 0) / 1024 or None)),
    ("encoder CPU % / PSS MB", lambda s: (hm(s, "procs.encoder.cpu_pct"), (hm(s, "procs.encoder.pss_kb") or 0) / 1024 or None)),
    ("EPG child CPU % / PSS MB", lambda s: (hm(s, "procs.epg.cpu_pct"), (hm(s, "procs.epg.pss_kb") or 0) / 1024 or None)),
    ("range_server CPU % / PSS MB", lambda s: (hm(s, "procs.range_server.cpu_pct"), (hm(s, "procs.range_server.pss_kb") or 0) / 1024 or None)),
    ("Xorg CPU %", lambda s: hm(s, "procs.xorg.cpu_pct")),
    ("pulseaudio CPU %", lambda s: hm(s, "procs.pulseaudio.cpu_pct")),
    ("other (non-PrivyHub) CPU %", lambda s: hm(s, "procs.other.cpu_pct")),
    ("sampler CPU %", lambda s: hm(s, "procs.e1_sampler.cpu_pct")),
    ("swap in / out per s", lambda s: (hm(s, "mem.pswpin_per_s"), hm(s, "mem.pswpout_per_s"))),
    ("mem used MB", lambda s: hm(s, "mem.used_mb")),
    ("GPU busy mean / p95 %", lambda s: (hm(s, "gpu.busy_pct"), hm(s, "gpu.busy_pct", "p95"))),
    ("encoder capture fps", lambda s: ((s.get("host") or {}).get("encoder") or {}).get("capture_fps")),
    ("encoder dup + drop per min", lambda s: (lambda e: (e["dup_per_min"] + e["drop_per_min"]) if e else None)(
        (s.get("host") or {}).get("encoder"))),
    ("RetroArch fps", lambda s: ((s.get("key") or {}).get("retroarch") or {}).get("frames_per_s")),
    ("rendered fps (heartbeat)", lambda s: ((s.get("key") or {}).get("heartbeat") or {}).get("rendered_fps")),
    ("RetroArch fps − rendered fps", lambda s: (lambda a, b: a - b if a is not None and b is not None else None)(
        ((s.get("key") or {}).get("retroarch") or {}).get("frames_per_s"),
        ((s.get("key") or {}).get("heartbeat") or {}).get("rendered_fps"))),
    ("disk write kB/s / await ms", lambda s: (hm(s, "disk.write_kBps"), hm(s, "disk.await_ms"))),
    ("disk read kB/s", lambda s: hm(s, "disk.read_kBps")),
    ("eno1 tx / rx kB/s", lambda s: (hm(s, "net.eno1.tx_kBps"), hm(s, "net.eno1.rx_kBps"))),
    ("qdisc + softnet + if tx drops per s", lambda s: sum(x or 0 for x in (hm(s, "netx.qdisc_dropped_per_s"),
                                                                       hm(s, "netx.softnet_dropped_per_s"),
                                                                       hm(s, "netx.if_tx_dropped_per_s"))) if hm(s, "netx.qdisc_dropped_per_s") is not None else None),
    ("qdisc requeues per s", lambda s: hm(s, "netx.qdisc_requeues_per_s")),
    ("C2 receive→decode ms (median)", lambda s: ((s.get("key") or {}).get("telemetry") or {}).get("receive_to_decode_ms_median")),
    ("C2 output gap ms (max)", lambda s: ((s.get("key") or {}).get("telemetry") or {}).get("output_gap_ms_max")),
    ("video loss/min (window)", lambda s: ((s.get("key") or {}).get("heartbeat") or {}).get("video_loss_per_min")),
    ("audio underruns (window)", lambda s: ((s.get("key") or {}).get("heartbeat") or {}).get("audio_underruns")),
    ("resyncs (window)", lambda s: ((s.get("key") or {}).get("heartbeat") or {}).get("stream_resyncs")),
    ("report: spikes ≥20 / ≥50 ms per min (session)", lambda s: (lambda r: (r["decoder.spike_20_ms"] / (r["duration_ms"] / 60000),
                                                                         r["decoder.spike_50_ms"] / (r["duration_ms"] / 60000))
                                                              if r and "decoder.spike_20_ms" in r and r.get("duration_ms") else None)(
        (s.get("teardown") or {}).get("report_fields"))),
    ("report: stale drops / max gap ms (session)", lambda s: (lambda r: (r.get("decoder.stale_output_drops"), r.get("decoder.max_output_gap_ms"))
                                                           if r and "decoder.max_output_gap_ms" in r else None)((s.get("teardown") or {}).get("report_fields"))),
    ("bitrate min–max kbps / at 1920×1080", lambda s: (lambda p: (f"{p.get('bitrate_kbps_min')}–{p.get('bitrate_kbps_max')}", p.get("frac_1920x1080")) if p else None)(
        (s.get("key") or {}).get("status_poll"))),
    ("VOD progress ratio / served kB/s", lambda s: (lambda v: (v.get("progress_ratio"), hm(s, "procs.range_server.rchar_kBps")) if v else None)(
        (s.get("key") or {}).get("vod"))),
    ("EPG grabs ok/failed, median s", lambda s: (lambda e: (f"{e['grabs_ok']}/{e['grabs_failed']}", e.get("grab_s_median")) if e else None)(
        (s.get("key") or {}).get("epg"))),
    ("Tctl mean / core max °C", lambda s: (hm(s, "gpu.tctl_c"), hm(s, "gpu.t_core_max_c", "max"))),
    ("cpufreq mean MHz", lambda s: hm(s, "freq.cpu_mhz_mean")),
    ("throttle_status counts", lambda s: ", ".join(f"{k}: {v}" for k, v in ((s.get("host") or {}).get("throttle_by_value") or {}).items()) or "none"),
    ("socket / CPU / SoC W", lambda s: (hm(s, "gpu.socket_power_w"), hm(s, "gpu.cpu_power_w"), hm(s, "gpu.soc_power_w"))),
]
E1_BESIDE = {"host CPU mean %": "cpu.mean_pct", "GPU busy mean / p95 %": "gpu.busy_pct",
             "socket / CPU / SoC W": "gpu.socket_power_w", "Tctl mean / core max °C": "gpu.tctl_c"}


def cell(v):
    if isinstance(v, tuple):
        return " / ".join(f(x, 3 if isinstance(x, float) and abs(x) < 2 else 1) for x in v)
    return f(v, 3 if isinstance(v, float) and abs(v) < 2 else 1)


def e1_mean(wid, key):
    base = E1VOD if wid == "E1-VOD" else E1
    vals = [hm(json.load(open(p)), key) for p in runs_of(base, wid)]
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def e1_key(wid, path):
    base = E1VOD if wid == "E1-VOD" else E1
    vals = []
    for p in runs_of(base, wid):
        d = json.load(open(p))
        x = d
        for k in path:
            x = (x or {}).get(k) if isinstance(x, dict) else None
        if isinstance(x, (int, float)):
            vals.append(x)
    return sum(vals) / len(vals) if vals else None


def table(out):
    cols = []
    for wid in ROWS:
        for p in runs_of(R, wid):
            cols.append((wid, os.path.basename(os.path.dirname(p)), json.load(open(p))))
    lines = ["| metric | " + " | ".join(f"{w[3:]} {r}" for w, r, _ in cols) + " |",
             "| --- |" + " --- |" * len(cols)]
    for name, fn in TABLE:
        row = [name]
        for w, r, s in cols:
            try:
                row.append(cell(fn(s)) if s.get("status") == "OK" else s.get("status"))
            except Exception:  # noqa: BLE001
                row.append("—")
        lines.append("| " + " | ".join(row) + " |")
    # E1 5-min means beside
    lines.append("| **E1 5-min means (2 runs)** |" + " |" * len(cols))
    for name, key in (("E1: host CPU mean %", "cpu.mean_pct"), ("E1: GPU busy mean %", "gpu.busy_pct"),
                      ("E1: socket W", "gpu.socket_power_w"), ("E1: Tctl mean °C", "gpu.tctl_c"),
                      ("E1: companion PSS MB", "procs.companion.pss_kb")):
        row = [name]
        for w, r, s in cols:
            v = e1_mean(w, key)
            row.append(f(v / 1024 if v and key.endswith("pss_kb") else v))
        lines.append("| " + " | ".join(row) + " |")
    for name, path in (("E1: rendered fps", ("key", "heartbeat", "rendered_fps")),
                       ("E1: RetroArch fps", ("key", "retroarch", "frames_per_s")),
                       ("E1: video loss/min", ("key", "heartbeat", "video_loss_per_min"))):
        lines.append("| " + " | ".join([name] + [f(e1_key(w, path), 2) for w, r, s in cols]) + " |")
    lines.append("| wall power | " + " | ".join("ABSENT (no meter)" for _ in cols) + " |")
    lines.append("| glass-to-glass latency | " + " | ".join("ABSENT (no camera)" for _ in cols) + " |")
    lines.append("| VCN duty | " + " | ".join("not usable (reads ~0)" for _ in cols) + " |")
    open(os.path.join(HERE, "e2_table.md"), "w").write("\n".join(lines) + "\n")
    out["table_cols"] = [f"{w} {r}" for w, r, _ in cols]


# ---------------------------------------------------------------- 2. CONC
def relay_tid(rd):
    """Amendment A1: the non-main SCHED_OTHER poll-mode companion thread whose TID+1 is a clock_nanosleep thread."""
    s = json.load(open(os.path.join(rd, "summary.json")))
    th = ((s.get("host") or {}).get("threads") or {}).get("companion") or []
    by = {x["tid"]: x for x in th}
    cands = [x["tid"] for x in th if not x["is_main"] and x["policy"] == 0 and x["syscall_mode"] == "7"
             and (by.get(x["tid"] + 1) or {}).get("syscall_mode") == "230"]
    return (cands[0] if len(cands) == 1 else None), cands


def per_second(rd, t0, t1, relay):
    """{second(int epoch): {busiest, dupdrop, relay, txdrops, compcpu}} in [t0, t1]."""
    S = {}
    for r in jl(os.path.join(rd, "samples.jsonl")):
        ts = t(r["at_utc"])
        if t0 <= ts <= t1:
            x = r.get("netx") or {}
            S[int(ts)] = {"busiest": (r.get("cpu") or {}).get("max_pct"),
                          "txdrops": (x.get("qdisc_dropped_per_s") or 0) + (x.get("softnet_dropped_per_s") or 0)
                          + (x.get("if_tx_dropped_per_s") or 0),
                          "compcpu": ((r.get("procs") or {}).get("companion") or {}).get("cpu_pct")}
    prev = None
    for r in jl(os.path.join(rd, "encoder.jsonl")):
        if not r.get("records"):
            continue
        ts = int(t(r["at_utc"]))
        if prev and ts in S and r["dup"] >= prev["dup"] and r["drop"] >= prev["drop"]:
            S[ts]["dupdrop"] = (r["dup"] - prev["dup"]) + (r["drop"] - prev["drop"])
        prev = r
    for r in jl(os.path.join(rd, "threads.jsonl")):
        ts = int(t(r["at_utc"]))
        if ts in S:
            for pid, tid, cpu, pol, sc in (r.get("threads") or {}).get("companion") or []:
                if tid == relay:
                    S[ts]["relay"] = cpu
    return S


def hb_loss_series(t0, t1):
    files = sorted(glob.glob(REPO + "/logs/games/stream_log_archive/native_stream_heartbeat.log*")) + \
        [REPO + "/logs/games/native_stream_heartbeat.log"]
    rows = []
    for fp in files:
        for r in jl(fp):
            if "lost_packets" in r and t0 <= t(r["received_at_utc"]) <= t1:
                rows.append(r)
    rows.sort(key=lambda r: r["received_at_utc"])
    out = {}
    for a, b in zip(rows, rows[1:]):
        if b["elapsed_ms"] > a["elapsed_ms"] and b["lost_packets"] >= a["lost_packets"]:
            dt = (b["elapsed_ms"] - a["elapsed_ms"]) / 1000
            rate = (b["lost_packets"] - a["lost_packets"]) / dt
            for sec in range(int(t(a["received_at_utc"])), int(t(b["received_at_utc"]))):
                out[sec + 1] = rate
    return out


SIGNALS = [("busiest", "busiest core %"), ("dupdrop", "encoder dup+drop /s"), ("relay", "relay thread CPU %"),
           ("txdrops", "eno1 tx drops /s (qdisc+softnet+if)")]


def conc(out):
    base_rd = os.path.dirname(runs_of(R, "E1-PS1-STREAM")[0])
    bs = json.load(open(os.path.join(base_rd, "summary.json")))
    b0, b1 = t(bs["window"]["from"]), t(bs["window"]["to"])
    brelay, bc = relay_tid(base_rd)
    B = per_second(base_rd, b0, b1, brelay)
    BL = hb_loss_series(b0, b1)
    base = {}
    for k, _ in SIGNALS + [("compcpu", "")]:
        xs = [v[k] for v in B.values() if v.get(k) is not None]
        base[k] = (statistics.mean(xs) if xs else None, sd(xs) if xs else None, len(xs))
    bl = list(BL.values())
    base["loss"] = (statistics.mean(bl) if bl else None, sd(bl) if bl else None, len(bl))
    res = {"baseline": {"run": base_rd[len(R) + 1:], "relay_tid": brelay, "relay_candidates": bc,
                        "stats": {k: v for k, v in base.items()}}}
    md = ["# E2-S1 — the CONC question (pre-registered §3, amendment A1)", "",
          f"Baseline: E1-PS1-STREAM ({res['baseline']['run']}), relay thread "
          f"{'identified' if brelay else 'UNIDENTIFIED'} (candidates {len(bc)}).", ""]
    for p in runs_of(R, "E1-CONC"):
        rd = os.path.dirname(p)
        s = json.load(open(p))
        if s.get("status") != "OK":
            continue
        w0, w1 = t(s["window"]["from"]), t(s["window"]["to"])
        relay, cands = relay_tid(rd)
        S = per_second(rd, w0, w1, relay)
        L = hb_loss_series(w0, w1)
        grabs = [(t(g["start_utc"]), t(g["end_utc"])) for g in jl(os.path.join(rd, "epg.jsonl"))
                 if g.get("kind") == "grab" and w0 <= t(g["start_utc"]) and t(g["end_utc"]) <= w1]
        inbody = lambda sec: any(a <= sec <= b for a, b in grabs)
        r = {"relay_tid": relay, "relay_candidates": cands, "grabs": len(grabs), "signals": {}, "aligned": {}}
        sig_list = SIGNALS if relay else [x if x[0] != "relay" else ("compcpu", "companion CPU % (relay UNIDENTIFIED)")
                                          for x in SIGNALS]
        for k, label in sig_list + [("loss", "lost packets /s (heartbeat)")]:
            src = L if k == "loss" else {sec: v.get(k) for sec, v in S.items()}
            body = [v for sec, v in src.items() if v is not None and inbody(sec)]
            bm, bsd, _ = base[k]
            mag = None
            if body and bm is not None:
                mag = (statistics.mean(body) - bm) / bsd if bsd else (math.inf if statistics.mean(body) > bm else 0.0)
            aligned = []
            for off in range(0, 11):
                vals = [src.get(int(a) + off) for a, b in grabs if int(a) + off <= b and src.get(int(a) + off) is not None]
                aligned.append(round(statistics.mean(vals), 3) if vals else None)
            thr = None if bm is None else bm + 2 * (bsd or 0)
            first = next((off for off, v in enumerate(aligned) if v is not None and thr is not None and v > thr), None)
            r["signals"][k] = {"label": label, "body_mean": round(statistics.mean(body), 3) if body else None,
                               "baseline_mean": None if bm is None else round(bm, 3),
                               "baseline_sd": None if bsd is None else round(bsd, 3),
                               "magnitude_sd": None if mag is None else (round(mag, 2) if math.isfinite(mag) else "inf"),
                               "first_rise_s": first, "threshold": None if thr is None else round(thr, 3)}
            r["aligned"][k] = aligned
        cand = {k: v for k, v in r["signals"].items() if k != "loss" and v["magnitude_sd"] is not None}
        mags = {k: (math.inf if v["magnitude_sd"] == "inf" else v["magnitude_sd"]) for k, v in cand.items()}
        firsts = {k: v["first_rise_s"] for k, v in cand.items() if v["first_rise_s"] is not None}
        mx = max(mags.values()) if mags else None
        r["most"] = sorted(k for k, v in mags.items() if v == mx) if mags else []
        mf = min(firsts.values()) if firsts else None
        r["first"] = sorted(k for k, v in firsts.items() if v == mf) if firsts else []
        res[rd[len(R) + 1:]] = r
        md += [f"## {rd[len(R) + 1:]} — {len(grabs)} grab bodies in the window; relay thread "
               f"{'identified' if relay else 'UNIDENTIFIED (companion total CPU used)'}", "",
               "| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |",
               "| --- | --- | --- | --- | --- |"]
        for k, v in r["signals"].items():
            md.append(f"| {v['label']} | {f(v['baseline_mean'], 2)} ({f(v['baseline_sd'], 2)}) | {f(v['body_mean'], 2)} | "
                      f"{v['magnitude_sd'] if v['magnitude_sd'] is not None else '—'} | "
                      f"{v['first_rise_s'] if v['first_rise_s'] is not None else 'never'} |")
        md += ["", f"**Most:** {', '.join(r['most']) or '—'}; **first:** {', '.join(r['first']) or '—'}.", "",
               "Aligned on the grab start (mean across grabs, by offset in s):", "",
               "| offset s | " + " | ".join(str(o) for o in range(11)) + " |", "| --- |" + " --- |" * 11]
        for k, v in r["aligned"].items():
            md.append(f"| {r['signals'][k]['label']} | " + " | ".join(f(x, 2) for x in v) + " |")
        md.append("")
    open(os.path.join(HERE, "e2_conc.md"), "w").write("\n".join(md) + "\n")
    out["conc"] = res


# ---------------------------------------------------------------- 3. SNES
def snes(out):
    res = {}
    md = ["# E2-S1 — the SNES question (pre-registered §4)", ""]
    for p in runs_of(R, "E1-SNES-STREAM"):
        rd = os.path.dirname(p)
        s = json.load(open(p))
        if s.get("status") != "OK":
            continue
        h = s["host"]
        w0, w1 = t(s["window"]["from"]), t(s["window"]["to"])
        ra = (s["key"].get("retroarch") or {}).get("frames_per_s")
        enc = h.get("encoder") or {}
        cap = enc.get("capture_fps")
        dd = (enc.get("dup_per_min") or 0) + (enc.get("drop_per_min") or 0) if enc else None
        rend = (s["key"].get("heartbeat") or {}).get("rendered_fps")
        # rendered fps per minute from the heartbeat
        files = sorted(glob.glob(REPO + "/logs/games/stream_log_archive/native_stream_heartbeat.log*")) + \
            [REPO + "/logs/games/native_stream_heartbeat.log"]
        hb = sorted([r for fp in files for r in jl(fp) if "rendered_frames" in r and w0 <= t(r["received_at_utc"]) <= w1],
                    key=lambda r: r["received_at_utc"])
        permin = []
        for m in range(int((w1 - w0) // 60)):
            seg = [r for r in hb if w0 + 60 * m <= t(r["received_at_utc"]) <= w0 + 60 * (m + 1)]
            if len(seg) > 1 and seg[-1]["elapsed_ms"] > seg[0]["elapsed_ms"]:
                permin.append(round((seg[-1]["rendered_frames"] - seg[0]["rendered_frames"]) /
                                    ((seg[-1]["elapsed_ms"] - seg[0]["elapsed_ms"]) / 1000), 2))
        # capture fps per minute
        er = [r for r in jl(os.path.join(rd, "encoder.jsonl")) if r.get("records") and w0 <= t(r["at_utc"]) <= w1]
        capmin = []
        for m in range(int((w1 - w0) // 60)):
            seg = [r for r in er if w0 + 60 * m <= t(r["at_utc"]) <= w0 + 60 * (m + 1)]
            if len(seg) > 1:
                capmin.append(round((seg[-1]["frame"] - seg[0]["frame"]) / (t(seg[-1]["at_utc"]) - t(seg[0]["at_utc"])), 2))
        th = (h.get("threads") or {})
        rth = th.get("retroarch") or []
        eth = th.get("encoder") or []
        if ra is not None and ra >= 59.9 and ((cap is not None and cap < 59.5) or (dd or 0) > 0):
            reading = "the emulator's load starves the capture/encoder"
        elif ra is not None and ra < 59.9:
            reading = "the encoder starves the emulator (RetroArch < 59.9 while the encoder is busy)"
        elif ra is not None and ra >= 59.9 and rend is not None and rend < 59.5:
            reading = "the loss is after the encoder (transport / client)"
        else:
            reading = "none of the pre-registered readings (all >= 59.5)"
        r = {"retroarch_fps": ra, "capture_fps": cap, "dupdrop_per_min": dd, "rendered_fps": rend,
             "rendered_per_min": permin, "capture_per_min": capmin, "busiest_core_p95": h.get("busiest_core_p95"),
             "busiest_per_second_p95": hm(s, "cpu.max_pct", "p95"), "psi_cpu": hm(s, "psi_ms_per_s.cpu_some"),
             "retroarch_threads_seen": len(rth), "retroarch_top": rth[:6], "encoder_top": eth[:4],
             "retroarch_cpu": hm(s, "procs.retroarch.cpu_pct"), "encoder_cpu": hm(s, "procs.encoder.cpu_pct"),
             "video_loss_per_min": (s["key"].get("heartbeat") or {}).get("video_loss_per_min"), "reading": reading}
        res[rd[len(R) + 1:]] = r
        md += [f"## {rd[len(R) + 1:]}", "",
               f"- RetroArch {f(ra, 3)} fps; capture {f(cap, 3)} fps; encoder dup+drop {f(dd, 2)}/min; rendered {f(rend, 3)} fps; "
               f"video loss {f(r['video_loss_per_min'], 1)}/min.",
               f"- RetroArch {f(r['retroarch_cpu'])} % of a core over {len(rth)} threads; encoder {f(r['encoder_cpu'])} %; "
               f"busiest core p95 {f(r['busiest_core_p95'])} %; busiest-per-second p95 {f(r['busiest_per_second_p95'])} %; PSI cpu "
               f"{f(r['psi_cpu'])} ms/s.",
               "- RetroArch's busiest threads (% of a core, mean / p95; policy; syscall mode): " +
               "; ".join(f"{x['cpu_mean']:.1f} / {x['cpu_p95']:.1f} ({x['policy']}, {x['syscall_mode']})" for x in rth[:6]) + ".",
               "- Encoder's busiest threads: " + "; ".join(f"{x['cpu_mean']:.1f} / {x['cpu_p95']:.1f}" for x in eth[:4]) + ".",
               f"- Rendered fps per minute: {permin}", f"- Capture fps per minute: {capmin}",
               f"- **Reading (pre-registered): {reading}.**", ""]
    open(os.path.join(HERE, "e2_snes.md"), "w").write("\n".join(md) + "\n")
    out["snes"] = res


# ---------------------------------------------------------------- 4. memory
def slope(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0


def memory(out):
    res = {}
    md = ["# E2-S1 — the memory question (pre-registered §5)", "",
          "| run | PSS before first grab (anon / file) MB | after first grab | window end | growth anon / file share | last-15-min slope (% of level per 15 min) | reading | node PSS per grab, first / last (MB) |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for wid in ("E1-META", "E1-CONC"):
        for p in runs_of(R, wid):
            rd = os.path.dirname(p)
            s = json.load(open(p))
            if s.get("status") != "OK":
                continue
            w0, w1 = t(s["window"]["from"]), t(s["window"]["to"])
            rows = [(t(r["at_utc"]), (r.get("procs") or {}).get("companion"), (r.get("procs") or {}).get("epg"))
                    for r in jl(os.path.join(rd, "samples.jsonl"))]
            grabs = [(t(g["start_utc"]), t(g["end_utc"])) for g in jl(os.path.join(rd, "epg.jsonl")) if g.get("kind") == "grab"]
            if not grabs:
                continue
            g0s, g0e = grabs[0]
            before = [c for ts, c, e in rows if ts < g0s and c]
            after = [c for ts, c, e in rows if g0e + 1 <= ts <= g0e + 5 and c]
            end = [c for ts, c, e in rows if w1 - 5 <= ts <= w1 and c]
            pick = lambda lst: (lst[-1]["pss_kb"] / 1024, lst[-1].get("pss_anon_kb", 0) / 1024, lst[-1].get("pss_file_kb", 0) / 1024) if lst else (None, None, None)
            b, a, e = pick(before), pick(after[:1] and after or after), pick(end)
            ga = (a[1] - b[1]) if a[1] is not None and b[1] is not None else None
            gf = (a[2] - b[2]) if a[2] is not None and b[2] is not None else None
            share = (ga / (ga + gf)) if ga is not None and gf is not None and (ga + gf) else None
            last = [(ts, c["pss_kb"]) for ts, c, ep in rows if w1 - 900 <= ts <= w1 and c]
            sl = slope([x for x, _ in last], [y for _, y in last]) if len(last) > 10 else None
            lvl = statistics.mean([y for _, y in last]) if last else None
            pct = sl * 900 / lvl * 100 if sl is not None and lvl else None
            reading = None if pct is None else ("keeps growing" if pct > 5 else "plateaus")
            permin = []
            for m in range(int((w1 - w0) // 60) + 1):
                seg = [c["pss_kb"] for ts, c, ep in rows if w0 + 60 * m <= ts < w0 + 60 * (m + 1) and c]
                if seg:
                    permin.append(round(statistics.mean(seg) / 1024, 1))
            npg = []
            for gs, ge in grabs:
                vals = [ep["pss_kb"] for ts, c, ep in rows if gs <= ts <= ge and ep]
                if vals:
                    npg.append(max(vals) / 1024)
            r = {"before_mb": b, "after_first_grab_mb": a, "window_end_mb": e, "growth_anon_share": share,
                 "last15_slope_pct": pct, "reading": reading, "pss_per_min_mb": permin,
                 "node_pss_peak_first_last_mb": (npg[0], npg[-1]) if npg else None,
                 "node_pss_peak_mean_mb": statistics.mean(npg) if npg else None, "grabs": len(grabs)}
            res[rd[len(R) + 1:]] = r
            md.append(f"| {rd[len(R) + 1:]} | {f(b[0])} ({f(b[1])} / {f(b[2])}) | {f(a[0])} ({f(a[1])} / {f(a[2])}) | "
                      f"{f(e[0])} ({f(e[1])} / {f(e[2])}) | {f(share * 100 if share is not None else None)} % anon | "
                      f"{f(pct, 2)} | {reading} | {f(npg[0] if npg else None)} / {f(npg[-1] if npg else None)} |")
    md.append("")
    for k, v in res.items():
        md.append(f"- {k}: companion PSS per minute of the window (MB): {v['pss_per_min_mb']}")
    open(os.path.join(HERE, "e2_memory.md"), "w").write("\n".join(md) + "\n")
    out["memory"] = res


def main():
    out = {}
    table(out)
    for fn in (conc, snes, memory):
        try:
            fn(out)
        except Exception as exc:  # noqa: BLE001 -- partial data while runs are pending
            out[fn.__name__ + "_error"] = f"{type(exc).__name__}: {exc}"
    json.dump(out, open(os.path.join(HERE, "e2_analysis.json"), "w"), indent=1, default=str)
    print(json.dumps({k: (v if k.endswith("error") else "ok") for k, v in out.items()}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
