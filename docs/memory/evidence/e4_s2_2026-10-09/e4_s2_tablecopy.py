#!/usr/bin/env python3
# E4-S2: a copy of e4_s1_2026-10-09/e4_s1_analysis.py (this line added) (its table helpers only are used; main() is never run from here)
"""E4-S1 -- the reference on the adopted state, analysed as pre-registered (e4_s1_preregistration.txt). Read-only.
Copied from e2_s1_2026-10-05/e2_analysis.py (sha256 c5e5f4ee...c094; its table section, the CONC aligned frame, the
SNES and memory sections) and pointed at these runs, with E2's runs (e2_s1_2026-10-05/runs) beside instead of E1's.

    e4_s1_analysis.py   -> e4_s1_table.md/.json, e4_s1_drift.md, e4_s1_reference.md, validity.json, gaps/,
                           e4_s1_conc.md, e4_s1_snes.md, e4_s1_memory.md, e4_s1_analysis.json (in this dir)
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
R = os.path.join(HERE, "runs")
E2R = os.path.join(HERE, "..", "e2_s1_2026-10-05", "runs")
LOGS = os.path.join(REPO, "logs", "games")
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
def cell(v):
    if isinstance(v, tuple):
        return " / ".join(f(x, 3 if isinstance(x, float) and abs(x) < 2 else 1) for x in v)
    return f(v, 3 if isinstance(v, float) and abs(v) < 2 else 1)


# ---------------------------------------------------------------- E4: the gap log and recovery events per stream run
def gap_recovery(s, rd):
    """The run's window slice of the gap log and the recovery events (from the summary when the runner recorded them,
    otherwise from the repo's logs, as E3-A3B did); gaps/<row>.jsonl written."""
    if s.get("kind") != "stream" or not s.get("window"):
        return None
    t0, t1 = s["window"]["from"], s["window"]["to"]
    key = s.get("key") or {}
    if "gaps" in key and "recovery" in key:
        g = jl(os.path.join(rd, "gaps.jsonl"))
        out = {"gaps": key["gaps"], "recovery": key["recovery"], "source": "runner"}
    else:
        g = [x for x in jl(os.path.join(LOGS, "native_stream_ctrl_gaps.log.1")) + jl(os.path.join(LOGS, "native_stream_ctrl_gaps.log"))
             if t0 <= x.get("start_utc", "") <= t1]
        seen, g2 = set(), []
        for x in g:
            k = json.dumps(x, sort_keys=True)
            if k not in seen:
                seen.add(k)
                g2.append(x)
        g = sorted(g2, key=lambda x: x["start_utc"])
        rec = []
        for fp in sorted(glob.glob(os.path.join(LOGS, "stream_log_archive", "native_stream_recovery.log*"))) + \
                [os.path.join(LOGS, "native_stream_recovery.log.1"), os.path.join(LOGS, "native_stream_recovery.log")]:
            rec += [r for r in jl(fp) if t0 <= (r.get("at_utc") or "") <= t1]
        seen, rec2 = set(), []
        for r in rec:
            k = json.dumps(r, sort_keys=True)
            if k not in seen:
                seen.add(k)
                rec2.append(r)
        rec = sorted(rec2, key=lambda r: r["at_utc"])
        pauses = []
        for i, r in enumerate(rec):
            if r.get("event") != "desync_pause":
                continue
            nxt = next((x for x in rec[i + 1:] if x.get("event") in ("resumed", "gave_up_saved", "session_ended")), None)
            pauses.append({"at_utc": r["at_utc"], "trigger": r.get("trigger"), "next": (nxt or {}).get("event"),
                           "via": (nxt or {}).get("via"), "after_s": round(t(nxt["at_utc"]) - t(r["at_utc"]), 2) if nxt else None})
        ms = [x.get("gap_ms") or 0 for x in g]
        out = {"gaps": {"count": len(g), "over_1s": sum(1 for m in ms if m > 1000), "max_ms": max(ms, default=None)},
               "recovery": {"controller_pauses": [p for p in pauses if p["trigger"] == "controller_silence"],
                            "client_pauses": [p for p in pauses if str(p["trigger"]).startswith("client_")],
                            "other_pauses": [p for p in pauses if p["trigger"] != "controller_silence"
                                             and not str(p["trigger"]).startswith("client_")],
                            "gave_up_saved": [r["at_utc"] for r in rec if str(r.get("event", "")).startswith("gave_up")]},
               "source": "logs"}
    os.makedirs(os.path.join(HERE, "gaps"), exist_ok=True)
    with open(os.path.join(HERE, "gaps", s["workload"] + f"_run{s['run']}.jsonl"), "w") as fh:
        fh.writelines(json.dumps(x) + "\n" for x in g)
    return out


def _gr(s, *path):
    x = s.get("_e4")
    for k in path:
        x = (x or {}).get(k) if isinstance(x, dict) else None
    return x


def capture_seg(s):
    """The encoder's capture fps / dup+drop per min / segments, SEGMENT-AWARE (the sampler's figure is first-to-last
    over the window and is broken by any encoder restart): summed over consecutive progress records of one encoder
    (frame not decreasing, <= 3 s apart). The same function as e4_s2_ladder.py capture()."""
    rd = s.get("_rd")
    if not rd or s.get("kind") != "stream" or not s.get("window"):
        return None
    t0, t1 = s["window"]["from"], s["window"]["to"]
    rows = [r for r in jl(os.path.join(rd, "encoder.jsonl")) if r.get("records") and t0 <= r["at_utc"] <= t1]
    fr = dt = dd = 0.0
    segs = 1 if rows else 0
    for a, b in zip(rows, rows[1:]):
        d = t(b["at_utc"]) - t(a["at_utc"])
        if b["frame"] < a["frame"] or d > 3 or b["dup"] < a["dup"] or b["drop"] < a["drop"]:
            segs += 1
            continue
        fr += b["frame"] - a["frame"]
        dt += d
        dd += (b["dup"] - a["dup"]) + (b["drop"] - a["drop"])
    return (round(fr / dt, 3), round(dd / (dt / 60), 3), segs) if dt else None


TABLE += [
    ("encoder capture fps / dup+drop per min / segments (SEGMENT-AWARE)", capture_seg),
    ("gap log: count / > 1 s / max ms (window)", lambda s: (lambda g: (g["count"], g["over_1s"], g["max_ms"]) if g else None)(_gr(s, "gaps"))),
    ("controller pauses (controller_silence)", lambda s: None if _gr(s, "recovery") is None else len(_gr(s, "recovery", "controller_pauses"))),
    ("client pauses (resume s)", lambda s: None if _gr(s, "recovery") is None else
     f"{len(_gr(s, 'recovery', 'client_pauses'))} (" + ", ".join(str(p['after_s']) for p in _gr(s, 'recovery', 'client_pauses')) + ")"),
    ("gave_up_saved", lambda s: None if _gr(s, "recovery") is None else len(_gr(s, "recovery", "gave_up_saved"))),
    ("decisions: rows / transitions (window)", lambda s: (lambda d: (d.get("rows"), d.get("transitions")) if d else None)((s.get("key") or {}).get("decisions"))),
]


def load_cols():
    """[(wid, label, summary, run dir)] -- per row the E4 run, then E2's run(s) beside."""
    cols = []
    for wid in ROWS:
        for p in runs_of(R, wid):
            s = json.load(open(p))
            s["_rd"] = os.path.dirname(p)
            if s.get("status") == "OK":
                s["_e4"] = gap_recovery(s, os.path.dirname(p))
            cols.append((wid, "E4", s, os.path.dirname(p)))
        e2 = runs_of(E2R, wid)
        for p in e2:
            lab = "E2" if len(e2) == 1 else "E2 " + os.path.basename(os.path.dirname(p)).replace("run", "r")
            s = json.load(open(p))
            s["_rd"] = os.path.dirname(p)
            cols.append((wid, lab, s, os.path.dirname(p)))
    return cols


def table(out, cols):
    lines = ["| metric | " + " | ".join(f"{w[3:]} {lab}" for w, lab, _, _ in cols) + " |",
             "| --- |" + " --- |" * len(cols)]
    js = {}
    for name, fn in TABLE:
        row = [name]
        for w, lab, s, _ in cols:
            try:
                v = fn(s) if s.get("status") == "OK" else s.get("status")
            except Exception:  # noqa: BLE001
                v = None
            row.append(cell(v))
            js.setdefault(f"{w} {lab}", {})[name] = v
        lines.append("| " + " | ".join(row) + " |")
    lines.append("| wall power | " + " | ".join("ABSENT (no meter)" for _ in cols) + " |")
    lines.append("| glass-to-glass latency | " + " | ".join("ABSENT (no camera)" for _ in cols) + " |")
    lines.append("| VCN duty | " + " | ".join("not usable (reads ~0)" for _ in cols) + " |")
    lines.append("| RAPL package energy | " + " | ".join("ABSENT (root-only)" for _ in cols) + " |")
    open(os.path.join(HERE, "e4_s1_table.md"), "w").write(
        "# E4-S1 — the full table (E4 one run per row, 20-min windows; E2's run(s) beside)\n\n"
        "ABSENT rows of the suite: NES, Genesis, Live TV, camera, browser (absent.json).\n\n" + "\n".join(lines) + "\n")
    json.dump(js, open(os.path.join(HERE, "e4_s1_table.json"), "w"), indent=1, default=str)
    out["table_cols"] = [f"{w} {lab}" for w, lab, _, _ in cols]


# ---------------------------------------------------------------- drift (pre-registered §4)
def kk(s, *path):
    x = s
    for k in path:
        x = (x or {}).get(k) if isinstance(x, dict) else None
    return x


DRIFT = [  # (metric, extractor, kind, band, banded by E1 (True) or a reported comparison (False))
    ("host CPU mean %", lambda s: hm(s, "cpu.mean_pct"), "abs", 2.0, True),
    ("GPU busy mean %", lambda s: hm(s, "gpu.busy_pct"), "abs", 3.0, True),
    ("main-process RSS kB", lambda s: hm(s, f"procs.{s.get('main_process')}.rss_kb"), "rel", 0.05, True),
    ("RetroArch fps", lambda s: kk(s, "key", "retroarch", "frames_per_s"), "abs", 0.5, True),
    ("rendered fps", lambda s: kk(s, "key", "heartbeat", "rendered_fps"), "abs", 0.5, True),
    ("median EPG grab s", lambda s: kk(s, "key", "epg", "grab_s_median"), "rel", 0.30, True),
] + [(f"{p} CPU % of a core", (lambda p: lambda s: hm(s, f"procs.{p}.cpu_pct"))(p), "abs", 2.0, False)
     for p in ("companion", "retroarch", "encoder", "epg", "range_server")] + \
    [(f"{p} PSS kB", (lambda p: lambda s: hm(s, f"procs.{p}.pss_kb"))(p), "rel", 0.05, False)
     for p in ("companion", "retroarch", "encoder", "epg", "range_server")]


def explain(wid, metric):
    """The adoption that could explain a drift (written before the E4 data); else 'nothing does'."""
    if wid == "E1-SNES-STREAM" and (metric.startswith(("host CPU", "retroarch", "main-process", "GPU", "encoder"))):
        return "Snes9x (E3-A2): the SNES core changed (bsnes -> Snes9x)"
    if wid in ("E1-META", "E1-CONC") and (metric.startswith("companion") or metric.startswith("host CPU")
                                          or metric.startswith("main-process") and wid == "E1-META"):
        return "the guide index (E3-S6A): grabs read the cached index, no 25.6 MB parse in the companion"
    return "nothing does (no adoption touches this row/metric)"


def drift(out, cols):
    rows, md = [], ["# E4-S1 — drift from E2 (pre-registered §4)", "",
                    "E1's bands (§5); per-process rows as reported comparisons with the same bands. SNES / CONC: E4's run "
                    "against E2's two-run range widened by the band. Link rows are not banded.", "",
                    "| row | metric | E4 | E2 | band | banded by E1? | drift | explained by |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for wid in ROWS:
        e4 = [s for w, lab, s, _ in cols if w == wid and lab == "E4" and s.get("status") == "OK"]
        e2 = [s for w, lab, s, _ in cols if w == wid and lab.startswith("E2") and s.get("status") == "OK"]
        if not e4 or not e2:
            continue
        for name, fn, kind, band, banded in DRIFT:
            v = fn(e4[0])
            ref = [x for x in (fn(s) for s in e2) if x is not None]
            if v is None or not ref:
                continue
            if kind == "abs":
                lo, hi = min(ref) - band, max(ref) + band
                bs = f"± {band:g}"
            else:
                lo, hi = min(ref) * (1 - band), max(ref) * (1 + band)
                bs = f"± {band * 100:g} %"
            moved = not (lo <= v <= hi)
            if moved and v == 0 and max(ref) == 0:
                moved = False
            r = {"row": wid, "metric": name, "e4": v, "e2": ref, "band": bs, "banded": banded, "drift": moved,
                 "explained_by": explain(wid, name) if moved else None}
            rows.append(r)
            if moved:
                md.append(f"| {wid[3:]} | {name} | {f(v, 2)} | {' / '.join(f(x, 2) for x in ref)} | {bs} | "
                          f"{'yes' if banded else 'reported'} | **moved** | {r['explained_by']} |")
    md += ["", f"Every compared metric within its band: {sum(1 for r in rows if not r['drift'])} of {len(rows)}; "
           f"moved: {sum(1 for r in rows if r['drift'])}."]
    open(os.path.join(HERE, "e4_s1_drift.md"), "w").write("\n".join(md) + "\n")
    out["drift"] = rows


# ---------------------------------------------------------------- the four-row reference and the checks
PRIV = ("companion", "retroarch", "encoder", "epg", "range_server")


def ref_row(s):
    cpu = {p: hm(s, f"procs.{p}.cpu_pct") for p in PRIV}
    pss = {p: (hm(s, f"procs.{p}.pss_kb") or 0) / 1024 for p in PRIV}
    return {"host_cpu": hm(s, "cpu.mean_pct"), "host_cpu_p95": hm(s, "cpu.mean_pct", "p95"),
            "busiest_core_p95": (s.get("host") or {}).get("busiest_core_p95"),
            "privyhub_cpu": {p: round(v, 1) for p, v in cpu.items() if v and v >= 0.5},
            "privyhub_cpu_total": round(sum(v or 0 for v in cpu.values()), 1),
            "privyhub_pss_mb": {p: round(v) for p, v in pss.items() if v >= 1},
            "privyhub_pss_total_mb": round(sum(pss.values())),
            "socket_w": hm(s, "gpu.socket_power_w"), "tctl": hm(s, "gpu.tctl_c"),
            "rendered_fps": kk(s, "key", "heartbeat", "rendered_fps"), "loss_per_min": kk(s, "key", "heartbeat", "video_loss_per_min"),
            "eno1_tx_kBps": hm(s, "net.eno1.tx_kBps")}


def reference(out, cols):
    e4 = {w: s for w, lab, s, _ in cols if lab == "E4" and s.get("status") == "OK"}
    e2 = {}
    for w, lab, s, _ in cols:
        if lab.startswith("E2") and s.get("status") == "OK":
            e2.setdefault(w, []).append(s)
    # heaviest = the highest host-CPU row other than the contended one (rule fixed before the data)
    cand = {w: hm(s, "cpu.mean_pct") or 0 for w, s in e4.items() if w != "E1-CONC"}
    heaviest = max(cand, key=cand.get) if cand else None
    four = [("idle", "E1-IDLE"), ("streaming", "E1-PS1-STREAM"), ("contended", "E1-CONC"), ("heaviest", heaviest)]
    md = ["| workload | row | host CPU % (p95) | busiest core p95 % | PrivyHub CPU (% of one core) | PrivyHub PSS MB | socket W | Tctl °C | stream |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    res = {}
    for lab, w in four:
        if w not in e4:
            md.append(f"| {lab} | {w} | not run | | | | | | |")
            continue
        r = ref_row(e4[w])
        r2 = [ref_row(s) for s in e2.get(w, [])]
        res[lab] = {"row": w, "e4": r, "e2": r2}
        e2s = lambda k, nd=1: " / ".join(f(x[k], nd) for x in r2) if r2 else "—"
        stream = (f"{f(r['rendered_fps'], 2)} fps, loss {f(r['loss_per_min'])}/min [E2 {e2s('rendered_fps', 2)} fps, "
                  f"{e2s('loss_per_min')}/min]") if r["rendered_fps"] else "—"
        md.append(f"| {lab} | {w[3:]} | {f(r['host_cpu'])} ({f(r['host_cpu_p95'])}) [E2 {e2s('host_cpu')}] | "
                  f"{f(r['busiest_core_p95'])} [E2 {e2s('busiest_core_p95')}] | "
                  f"{' + '.join(f'{k} {v}' for k, v in r['privyhub_cpu'].items()) or '~0'} = {r['privyhub_cpu_total']} "
                  f"[E2 {e2s('privyhub_cpu_total')}] | "
                  f"{' + '.join(f'{k} {v}' for k, v in r['privyhub_pss_mb'].items())} = {r['privyhub_pss_total_mb']} "
                  f"[E2 {e2s('privyhub_pss_total_mb', 0)}] | {f(r['socket_w'])} [E2 {e2s('socket_w')}] | "
                  f"{f(r['tctl'], 0)} [E2 {e2s('tctl', 0)}] | {stream} |")
    md2 = ["| row | host CPU % (p95) | busiest core p95 | PrivyHub CPU total | PrivyHub PSS MB | socket W | Tctl | rendered fps | loss/min |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for w in ROWS:
        if w in e4:
            r = ref_row(e4[w])
            md2.append(f"| {w[3:]} | {f(r['host_cpu'])} ({f(r['host_cpu_p95'])}) | {f(r['busiest_core_p95'])} | {r['privyhub_cpu_total']} | "
                       f"{r['privyhub_pss_total_mb']} | {f(r['socket_w'])} | {f(r['tctl'], 0)} | {f(r['rendered_fps'], 2)} | {f(r['loss_per_min'])} |")
    open(os.path.join(HERE, "e4_s1_reference.md"), "w").write(
        "# E4-S1 — the known-good reference for this host on the adopted state, 2026-10-09; no floor and no lower-tier claim.\n\n"
        f"The ROADMAP's four-row form (heaviest = the highest host-CPU row other than the contended one: {heaviest}). "
        "E2 (2026-10-06, before E3's adoptions) in brackets.\n\n" + "\n".join(md) + "\n\nEvery row:\n\n" + "\n".join(md2) + "\n")
    out["reference"] = res
    out["heaviest"] = heaviest


def checks(out, cols):
    val = {}
    for w, lab, s, rd in cols:
        if lab != "E4":
            continue
        failed = sorted(glob.glob(os.path.join(rd, "summary_failed_attempt*.json")))
        v = {"status": s.get("status"), "valid": s.get("status") == "OK" and bool(s.get("window")),
             "replaced_attempts": len(failed), "window": [kk(s, "window", "from"), kk(s, "window", "to")]}
        if s.get("kind") == "stream":
            v["reached_playing"] = bool(kk(s, "launch", "stream", "ok"))
            v["controller_pauses"] = None if _gr(s, "recovery") is None else len(_gr(s, "recovery", "controller_pauses"))
            v["client_pauses_reported"] = None if _gr(s, "recovery") is None else len(_gr(s, "recovery", "client_pauses"))
        if w == "E1-PS1-1080P":
            v["frac_1920x1080"] = kk(s, "key", "status_poll", "frac_1920x1080")
            v["rung_injection"] = s.get("rung_injection")
        if w == "E1-VOD":
            v["progress_ratio"] = kk(s, "key", "vod", "progress_ratio")
        val[f"{w}/run{s.get('run')}"] = v
    json.dump(val, open(os.path.join(HERE, "validity.json"), "w"), indent=1)
    out["validity"] = val
    ps = next((s for w, lab, s, _ in cols if w == "E1-PS1-STREAM" and lab == "E4" and s.get("status") == "OK"), None)
    if ps:
        rf = kk(ps, "teardown", "report_fields") or {}
        mins = (rf.get("duration_ms") or 0) / 60000
        d = {"spikes_20ms_per_min": round(rf["decoder.spike_20_ms"] / mins, 1) if mins and "decoder.spike_20_ms" in rf else None,
             "stale_drops_per_min": round(rf["decoder.stale_output_drops"] / mins, 2) if mins and "decoder.stale_output_drops" in rf else None,
             "rendered_fps": kk(ps, "key", "heartbeat", "rendered_fps"),
             "video_loss_per_min": kk(ps, "key", "heartbeat", "video_loss_per_min")}
        d["holds"] = {"spikes < 200": d["spikes_20ms_per_min"] is not None and d["spikes_20ms_per_min"] < 200,
                      "stale < 20": d["stale_drops_per_min"] is not None and d["stale_drops_per_min"] < 20,
                      "rendered >= 59.5": d["rendered_fps"] is not None and d["rendered_fps"] >= 59.5,
                      "loss < 10 (reported, the night's)": d["video_loss_per_min"] is not None and d["video_loss_per_min"] < 10}
        out["dbase_ps1_stream"] = d

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
    md = ["# E4-S1 — the CONC aligned frame (E2 §3 method, amendment A1; reported)", "",
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
    open(os.path.join(HERE, "e4_s1_conc.md"), "w").write("\n".join(md) + "\n")
    out["conc"] = res


# ---------------------------------------------------------------- 3. SNES
def snes(out):
    res = {}
    md = ["# E4-S1 — the SNES row read by E2 §4 (reported; Snes9x)", ""]
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
    open(os.path.join(HERE, "e4_s1_snes.md"), "w").write("\n".join(md) + "\n")
    out["snes"] = res


# ---------------------------------------------------------------- 4. memory
def slope(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0


def memory(out):
    res = {}
    md = ["# E4-S1 — the memory row read by E2 §5 (reported)", "",
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
    open(os.path.join(HERE, "e4_s1_memory.md"), "w").write("\n".join(md) + "\n")
    out["memory"] = res


def main():
    out = {}
    cols = load_cols()
    table(out, cols)
    for fn in (drift, reference, checks):
        try:
            fn(out, cols)
        except Exception as exc:  # noqa: BLE001
            out[fn.__name__ + "_error"] = f"{type(exc).__name__}: {exc}"
    for fn in (conc, snes, memory):
        try:
            fn(out)
        except Exception as exc:  # noqa: BLE001 -- partial data while runs are pending
            out[fn.__name__ + "_error"] = f"{type(exc).__name__}: {exc}"
    json.dump(out, open(os.path.join(HERE, "e4_s1_analysis.json"), "w"), indent=1, default=str)
    print(json.dumps({k: (v if k.endswith("error") or k in ("dbase_ps1_stream", "heaviest") else "ok") for k, v in out.items()},
                     indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
