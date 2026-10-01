#!/usr/bin/env python3
"""C5-M4A V5 -- the 20-min hold scored as pre-registered (c5_m4a_preregistration.txt).

    c5_m4a_score.py <runs dir>        (run c5_m4_host_table.py <runs dir> first; it writes the R1/R2 json)

Met if ALL of: R1 (RetroArch fps >= 59.88, no 256-frame interval > 256/60 s + 12 ms), R2 (capture fps median
>= 59.5, dup+drop <= 0.5 %), the capture window 1920x1080, spikes >= 20 ms < 200/min, rendered fps >= 59.5,
stale drops < 20/min, audio underruns < 5/min. Reported, not gated: loss/min and max gap (LINK-L1 is MIXED),
the per-second largest frame p50/p90, cap hits s/min, >= 80-packet frames/min (beside C5-M4's b_4x), and the
controller's transitions (0 expected). A link-drop recovery pause in the hold is listed from the recovery log.
"""
import json, os, sys

R = sys.argv[1]
OUT = os.path.dirname(os.path.abspath(R))
tag = os.path.basename(os.path.abspath(R))
ht = json.load(open(os.path.join(OUT, f"c5_m4_host_table_{tag}.json")))
B4X = json.load(open(os.path.join(OUT, "..", "c5_m4_2026-10-01", "c5_m4_host_table_runs.json")))["b_4x"]
rows = []
for hold, r in ht.items():
    rep = json.load(open(os.path.join(R, f"report_{hold}.json")))["report"]
    m = rep["duration_ms"] / 60000.0
    aund = (rep["audio"].get("underruns") or 0) / m
    dl = [json.loads(l) for l in open(os.path.join(R, f"decision_log_{hold}.jsonl")) if l.strip()]
    trans = sum(1 for d in dl if d.get("event") == "transition")
    idx = [l.split() for l in open(os.path.join(R, "index.txt")) if l.startswith(hold + " ")][0]
    t0, t1 = idx[4], idx[5]
    rec = []
    for l in open("/home/privyhub/Projects/onn-stream-test/logs/games/native_stream_recovery.log", errors="replace"):
        try:
            d = json.loads(l)
        except Exception:
            continue
        if t0 <= d.get("at_utc", "")[:19] + "Z" <= t1 and d.get("event") not in ("session_started", "session_ended"):
            rec.append((d.get("at_utc"), d.get("event")))
    gates = {
        "R1 RetroArch holds 60": r.get("r1"),
        "R2 capture holds 60": r.get("r2"),
        "capture window 1920x1080": r.get("capture") == "1920x1080",
        "spikes < 200/min": r["spikes"] < 200,
        "rendered fps >= 59.5": r["fps"] >= 59.5,
        "stale < 20/min": r["stale"] < 20,
        "audio underruns < 5/min": aund < 5,
    }
    met = all(gates.values())
    lines = [f"C5-M4A V5 -- {hold} ({r['min']} min), scored as pre-registered", ""]
    lines += [f"  {k:<28} {'MET' if v else 'MISSED'}" for k, v in gates.items()]
    lines += ["", f"  V5: {'MET' if met else 'NOT MET'}", "",
              f"  RetroArch fps {r.get('ra_fps')}, longest 256-frame interval {r.get('interval_max_ms')} ms "
              f"({r.get('long_intervals')} over the bar); capture fps median {r.get('enc_fps_median')}, dup+drop {r.get('dup_drop')}",
              f"  client: fps {r['fps']}, spikes {r['spikes']}/min, stale {r['stale']}/min, audio underruns {aund:.2f}/min",
              f"  reported: loss {r['vloss']}/min, max gap {r['maxgap']} ms, {r['mbps']} Mbit/s",
              f"  per-s largest frame p50/p90/max {r['frmax_p50']}/{r['frmax_p90']}/{r['frmax_max']} B, cap hits "
              f"{r['caphit_s_min']} s/min, >= 80-pkt {r['ge80_min']}/min  "
              f"(C5-M4 b_4x, 5 min: {B4X['frmax_p50']}/{B4X['frmax_p90']}/{B4X['frmax_max']}, {B4X['caphit_s_min']} s/min, {B4X['ge80_min']}/min)",
              f"  host: GPU {r['gpu_mean']:.1f} % (p95 {r['gpu_p95']}), CPU {r['cpu_mean']:.1f} %, Tctl max {r['tctl_max']} C, "
              f"RetroArch {r.get('t2_ra_cpu') or 0:.1f} % / encoder {r.get('t2_enc_cpu') or 0:.1f} % of a core (T2)",
              f"  controller transitions in the hold: {trans} (0 expected); events {json.dumps(r['abr_events'])}",
              f"  link-drop recovery events in the hold: {rec if rec else 'none'}"]
    text = "\n".join(lines) + "\n"
    print(text)
    rows.append({"hold": hold, "gates": gates, "met": met, "audio_underruns_per_min": round(aund, 2),
                 "transitions": trans, "recovery_events": rec})
open(os.path.join(OUT, "c5_m4a_v5_score.txt"), "w").write(text)
json.dump(rows, open(os.path.join(OUT, "c5_m4a_v5_score.json"), "w"), indent=1)
