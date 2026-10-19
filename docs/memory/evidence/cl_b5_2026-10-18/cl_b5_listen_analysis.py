#!/usr/bin/env python3
"""CL-B5 run L (Opus, the listen) beside A (PCM); not paired, 35 min apart: PS1-STREAM runs against cl_b5_preregistration.txt §5 (host gates as CL-B3's: status OK, RetroArch
>= 59.9, capture 60 +/- 0.1, dup+drop <= 0.2/min via E4-S5D's segcap, flags_absent after), A and B
paired on one evening (same title, same seven lines, the new APK). Reported, not gated: the audio sender's datagrams/s (status_poll), the LAN
interface's tx rate (the sampler's /proc/net/dev), the client's audio block (the session report), host / per-process
CPU, the video figures. Read-only. -> cl_b5_listen_verdict.json, validity.json."""
import importlib.util, json, os, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
spec = importlib.util.spec_from_file_location("s5d", os.path.join(HERE, "../e4_s5d_2026-10-15/e4_s5d_analysis.py"))
S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
RUNS = {"L opus": os.path.join(HERE, "runs_listen/E1-PS1-STREAM_flag/run1"),
        "A pcm": os.path.join(HERE, "runs/E1-PS1-STREAM/run1")}  # L beside A (not paired: 35 min later)
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

res = {lab: one(lab, rd) for lab, rd in RUNS.items()}
o = res["L opus"]
failed = [f"{lab}:{g}" for lab, x in res.items() for g, v in x["gates"].items() if not v]
poll = [r for r in jl(os.path.join(RUNS["L opus"], "status_poll.jsonl"))]
verdict = {"verdict": "ALL HOST GATES HOLD" if not failed else "FAILED (" + ", ".join(failed) + ")", "runs": res,
           "eno1_tx_kbit_s_L_minus_A": round(o["eno1_tx_kbit_s_mean"] - res["A pcm"]["eno1_tx_kbit_s_mean"], 1),
           "eno1_tx_pps_L_minus_A": round(o["eno1_tx_pps_mean"] - res["A pcm"]["eno1_tx_pps_mean"], 1),
           # on eno1 (Ethernet: +14 B per frame): PCM 400 x (976+28+14) B, Opus 200 x (176+28+14) B
           "predicted_saving_kbit_s_ip": round(3212.8 - 326.4, 1),
           "predicted_saving_kbit_s_eno1": round((400 * 1018 - 200 * 218) * 8 / 1000, 1), "predicted_pps_saving": 200}
json.dump(verdict, open(os.path.join(HERE, "cl_b5_listen_verdict.json"), "w"), indent=1)
json.dump({k: v["status"] for k, v in res.items()}, open(os.path.join(HERE, "validity_listen.json"), "w"), indent=1)
print(json.dumps(verdict, indent=1))
