#!/usr/bin/env python3
"""CL-B7 (from cl_b6_analysis.py's one(); only RUNS and the tail changed). Was: CL-B6: the A/B repeated after the onn power-cycle (run 1 Opus as adopted, run 2 PCM by override) against cl_b6_preregistration.txt §4, beside CL-B5 A/B/L and G-A2 (host gates as CL-B3's: status OK, RetroArch
>= 59.9, capture 60 +/- 0.1, dup+drop <= 0.2/min via E4-S5D's segcap, flags_absent after), A and B
paired on one evening (same title, same seven lines, the new APK). Reported, not gated: the audio sender's datagrams/s (status_poll), the LAN
interface's tx rate (the sampler's /proc/net/dev), the client's audio block (the session report), host / per-process
CPU, the video figures. Read-only. -> cl_b5_verdict.json, validity.json."""
import importlib.util, json, os, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
spec = importlib.util.spec_from_file_location("s5d", os.path.join(HERE, "../e4_s5d_2026-10-15/e4_s5d_analysis.py"))
S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
RUNS = {
    "CL-B6 1 opus": os.path.join(HERE, "../cl_b6_2026-10-19/runs/E1-PS1-STREAM/run1"),
    "CL-B6 2 pcm": os.path.join(HERE, "../cl_b6_2026-10-19/runs/E1-PS1-STREAM_flag/run1"),
    "CL-B7 1 pcm": os.path.join(HERE, "runs/pcm/E1-PS1-STREAM_flag/run1"),
    "CL-B7 2 opus today": os.path.join(HERE, "runs/opus_today/E1-PS1-STREAM/run1"),
    "CL-B7 3 opus lean": os.path.join(HERE, "runs/opus_lean/E1-PS1-STREAM/run1"),
}
ARM = {"CL-B7 1 pcm": "pcm", "CL-B7 2 opus today": "opus_today", "CL-B7 3 opus lean": "opus_lean"}
PROCS = ("companion", "retroarch", "encoder", "xorg")

def jl(p):
    for line in open(p):
        try: yield json.loads(line)
        except ValueError: pass

def inwin(t, w):
    return w["from"] <= t <= w["to"]

def one(label, rd):
    s = json.load(open(os.path.join(rd, "summary.json")))
    w = s["window"]; k = S.k
    cap, dd = S.segcap(rd, s)
    h = json.load(open(os.path.join(rd, "sampler_summary.json")))["host"]
    tx = [r["net"]["eno1"]["tx_kBps"] for r in jl(os.path.join(rd, "samples.jsonl"))
          if inwin(r.get("at_utc", ""), w) and "eno1" in (r.get("net") or {})]
    txp = [r["net"]["eno1"]["tx_pps"] for r in jl(os.path.join(rd, "samples.jsonl"))
           if inwin(r.get("at_utc", ""), w) and "eno1" in (r.get("net") or {})]
    rungs = sorted({int(r["bitrate_kbps"]) for r in jl(os.path.join(rd, "status_poll.jsonl"))
                    if isinstance(r.get("bitrate_kbps"), (int, float)) and inwin(r.get("at_utc", ""), w)})
    rep = json.load(open(os.path.join(REPO, "logs/games/decoder_sessions", s["teardown"]["report"])))["report"]
    a = rep["audio"]; dur_min = rep.get("duration_ms", 0) / 60000 or None
    x = {"label": label, "status": s["status"], "window": [w["from"], w["to"]], "report": s["teardown"]["report"],
         "capture_fps": cap, "dupdrop_per_min": dd, "retroarch_fps": k(s, "key", "retroarch", "frames_per_s"),
         "host_cpu_pct": k(s, "host", "host", "cpu.mean_pct", "mean"),
         "procs_cpu_pct_of_core": {p: round(h[f"procs.{p}.cpu_pct"]["mean"], 2) for p in PROCS if f"procs.{p}.cpu_pct" in h},
         "rung_kbps": rungs, "eno1_tx_kbit_s_mean": round(statistics.mean(tx) * 1024 * 8 / 1000, 1) if tx else None,  # the sampler's tx_kBps is KiB/s (G4-W1)
         "eno1_tx_pps_mean": round(statistics.mean(txp), 1) if txp else None,
         "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"), "video_loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"), "heartbeat_audio_underruns": k(s, "key", "heartbeat", "audio_underruns"), "output_gap_ms_max": k(s, "key", "telemetry", "output_gap_ms_max"), "gaps_over_1s": k(s, "key", "gaps", "over_1s"), "gaps_max_ms": k(s, "key", "gaps", "max_ms"),
         "resyncs": k(s, "key", "heartbeat", "stream_resyncs"), "flags_absent_after": k(s, "teardown", "flags_absent"),
         "report_duration_min": round(dur_min, 2) if dur_min else None,
         "audio": {"codec": a.get("codec", "pcm (field absent)"), "rx_unique": a["packets"], "lost_net": a["lost_packets"],
                   "lost_unit_ms": 10 if a.get("codec") == "opus" else 5,
                   "audio_ms_lost_per_min": round(a["lost_packets"] * (10 if a.get("codec") == "opus" else 5) / dur_min, 2),
                   "sequence_holes_per_min": round(a["lost_packets"] / dur_min, 2),
                   "recovered_by_duplicate": a["recovered_by_duplicate"], "underruns": a["underruns"],
                   "arrival_holes_gt15ms": a["arrival_holes"]["total"],
                   "arrival_holes_per_min": round(a["arrival_holes"]["total"] / dur_min, 1),
                   "avg_queue_residence_ms": round(a["avg_queue_residence_ms"], 2), "max_queue_residence_ms": a["max_queue_residence_ms"],
                   "stale_drops": a["stale_drops"], "concealed_underruns": a["concealed_underruns"],
                   "concealed_loss_packets": a["concealed_loss_packets"], "prolonged_starvation_events": a["prolonged_starvation_events"],
                   "opus": a.get("opus")},
         "video_report": {kk: rep.get("decoder", {}).get(kk) for kk in ("spike_20_ms", "spike_50_ms", "max_output_gap_ms")}}
    x["gates"] = {"status_ok": s["status"] == "OK", "retroarch_ge_59.9": (x["retroarch_fps"] or 0) >= 59.9,
                  "capture_60_pm_0.1": cap is not None and abs(cap - 60) <= 0.1,
                  "dupdrop_le_0.2": dd is not None and dd <= 0.2, "flags_absent_after": bool(x["flags_absent_after"])}
    return x


import datetime, re, subprocess
def ep(s):
    return datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp()
def hb_codecs(w):
    j = subprocess.run(["journalctl", "--user", "-u", "privyhub-companion", "-o", "cat", "--no-pager", "--since", f"@{int(ep(w[0]))}",
                        "--until", f"@{int(ep(w[1]))}"], capture_output=True, text=True, timeout=120).stdout
    c = re.findall(r"audio_codec=([a-z]+)", j)
    return {x: c.count(x) for x in sorted(set(c))}
res = {lab: one(lab, rd) for lab, rd in RUNS.items()}
for lab, x in res.items():
    x["spikes_20_per_min"] = round(x["video_report"]["spike_20_ms"] / x["report_duration_min"], 1)
    x["spikes_50_per_min"] = round(x["video_report"]["spike_50_ms"] / x["report_duration_min"], 2)
    x["heartbeat_audio_codec_in_window"] = hb_codecs(x["window"])
    o = x["audio"].get("opus") or {}
    x["opus_decode_mode_key"] = ("decode_mode" in o, o.get("decode_mode"))
onn6 = [json.loads(l) for l in open(os.path.join(HERE, "../cl_b6_2026-10-19/onn_reads.jsonl"))]
res["CL-B6 1 opus"]["onn"] = {r["label"]: r for r in onn6 if r["label"] in ("before_run1", "run1_150s")}
res["CL-B6 2 pcm"]["onn"] = {r["label"]: r for r in onn6 if r["label"] in ("before_run2", "run2_150s")}
onn = [json.loads(l) for l in open(os.path.join(HERE, "onn_reads.jsonl"))]
thr = [json.loads(l) for l in open(os.path.join(HERE, "onn_threads.jsonl"))]
for lab, arm in ARM.items():
    res[lab]["onn"] = {r["label"]: r for r in onn if r["label"].startswith(arm + "_")}
    res[lab]["threads"] = {r["label"]: r for r in thr if r["label"].startswith(arm + "_")}
def tgroups(t):
    """150-s per-thread means by name group (names are the kernel's 15-char comm)."""
    if not t or "threads" not in t:
        return None
    g = {}
    for x in t["threads"]:
        g[x["name"]] = {"category": x["category"], "count": x["count"], "mean": x["cpu_mean"], "max": x["cpu_max"]}
    return {"total": t.get("privyhub_threads_total"), "by_category": t.get("privyhub_by_category"), "names": g,
            "processes": t.get("processes"), "onn_busy": t.get("onn_busy_pct_of_capacity_mean"), "flag": t.get("opus_decode_flag"),
            "uptime_s": t.get("uptime_s")}
tab = {lab: tgroups(res[lab]["threads"].get(arm + "_150s")) for lab, arm in ARM.items()}
def delta(a, b):
    if not (tab[a] and tab[b]):
        return None
    names = sorted(set(tab[a]["names"]) | set(tab[b]["names"]))
    d = {n: round(tab[a]["names"].get(n, {}).get("mean", 0) - tab[b]["names"].get(n, {}).get("mean", 0), 2) for n in names}
    cats = sorted(set(tab[a]["by_category"]) | set(tab[b]["by_category"]))
    pr = sorted(set(tab[a]["processes"]) | set(tab[b]["processes"]))
    return {"threads_total": round(tab[a]["total"] - tab[b]["total"], 2),
            "by_category": {c: round(tab[a]["by_category"].get(c, 0) - tab[b]["by_category"].get(c, 0), 2) for c in cats},
            "by_name_nonzero": {n: v for n, v in d.items() if abs(v) >= 0.3},
            "processes": {p: round(tab[a]["processes"].get(p, {}).get("cpu_mean", 0) - tab[b]["processes"].get(p, {}).get("cpu_mean", 0), 2) for p in pr}}
mine = list(ARM)
failed = [f"{lab}:{g}" for lab in mine for g, v in res[lab]["gates"].items() if not v]
out = {"verdict": "ALL HOST GATES HOLD" if not failed else "FAILED (" + ", ".join(failed) + ")", "runs": res, "threads_150s": tab,
       "delta_opus_today_minus_pcm": delta("CL-B7 2 opus today", "CL-B7 1 pcm"),
       "delta_lean_minus_today": delta("CL-B7 3 opus lean", "CL-B7 2 opus today"),
       "eno1_tx_kbit_s_opus_today_minus_pcm": round(res["CL-B7 2 opus today"]["eno1_tx_kbit_s_mean"] - res["CL-B7 1 pcm"]["eno1_tx_kbit_s_mean"], 1)}
json.dump(out, open(os.path.join(HERE, "cl_b7_verdict.json"), "w"), indent=1, default=str)
print(out["verdict"], "eno1 opus-pcm", out["eno1_tx_kbit_s_opus_today_minus_pcm"])
for lab, x in res.items():
    a = x["audio"]; o = a.get("opus") or {}
    print(f"{lab:19s} ra {x['retroarch_fps']} cap {x['capture_fps']} dd {x['dupdrop_per_min']} fa {x['flags_absent_after']} | codec {a['codec']} hb {x['heartbeat_audio_codec_in_window']} dm {x['opus_decode_mode_key']} | und {a['underruns']}/{x['heartbeat_audio_underruns']} lostms {a['lost_net']*a['lost_unit_ms']} q {o.get('decode_queue_depth_max')}/{o.get('decode_queue_wait_max_us')} dec {o.get('decode_avg_us')} | sp20 {x['spikes_20_per_min']} sp50 {x['spikes_50_per_min']} gap {x['video_report']['max_output_gap_ms']} ctrl>1s {x['gaps_over_1s']}/{x['gaps_max_ms']} vloss {x['video_loss_per_min']} rend {x['rendered_fps']} | eno1 {x['eno1_tx_kbit_s_mean']} host {x['host_cpu_pct']}")
print("threads", json.dumps(tab, default=str)[:3000])
print("d today-pcm", json.dumps(out["delta_opus_today_minus_pcm"]))
print("d lean-today", json.dumps(out["delta_lean_minus_today"]))
