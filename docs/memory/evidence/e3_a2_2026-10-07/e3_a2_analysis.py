#!/usr/bin/env python3
"""E3-A2 -- the two adoptions' bar as pre-registered (e3_a2_preregistration.txt). Read-only.
-> e3_a2_table.md/.json (tools/e3_table.py beside E2 and the E3-S5C / E3-S4 / E3-S6A runs), loss_per_minute.txt,
   e3_a2_verdict.json. The addendum (e3_a2_preregistration_addendum.txt): runs that validity.json (e3_a2_validity.py)
   marks invalid are reported, not judged; the replacement runs_retry1/ PS1-STREAM run takes PS1 r1's place."""
import importlib.util
import json
import os
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
EV = os.path.join(REPO, "docs/memory/evidence")
E2R = os.path.join(EV, "e2_s1_2026-10-05/runs")
R = os.path.join(HERE, "runs")


def k(s, *p):
    for x in p:
        s = (s or {}).get(x) if isinstance(s, dict) else None
    return s


def main():
    spec = importlib.util.spec_from_file_location("e2a", os.path.join(EV, "e2_s1_2026-10-05/e2_analysis.py"))
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    rows = dict(A.TABLE)
    cols = [("PS1 r1", f"{R}/E1-PS1-STREAM/run1"), ("PS1 r2", f"{R}/E1-PS1-STREAM/run2"),
            ("SNES", f"{R}/E1-SNES-STREAM/run1"), ("META", f"{R}/E1-META/run1"),
            ("PS1 r1 replacement", f"{HERE}/runs_retry1/E1-PS1-STREAM/run1"),
            ("S5C F2", f"{EV}/e3_s5c_2026-10-07/runs/E1-PS1-STREAM_flag/run2"),
            ("S5C C2", f"{EV}/e3_s5c_2026-10-07/runs/E1-PS1-STREAM/run2"),
            ("S4 r1", f"{EV}/e3_s4_2026-10-07/runs/E1-SNES-STREAM_flag/run1"),
            ("S6A META", f"{EV}/e3_s6a_2026-10-07/runs/E1-META/run1"),
            ("E2 PS1-STREAM", f"{E2R}/E1-PS1-STREAM/run1"), ("E2 SNES r1", f"{E2R}/E1-SNES-STREAM/run1"),
            ("E2 META", f"{E2R}/E1-META/run1")]
    subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_table.py"), os.path.join(HERE, "e3_a2_table.md")]
                   + [f"{a}={b}" for a, b in cols], check=True, stdout=subprocess.DEVNULL)
    t = json.load(open(os.path.join(HERE, "e3_a2_table.json")))
    S = {a: json.load(open(os.path.join(b, "summary.json"))) for a, b in cols[:5]}
    V = json.load(open(os.path.join(HERE, "validity.json")))
    valid = {"PS1 r1": V["runs/E1-PS1-STREAM/run1"]["valid"], "PS1 r2": V["runs/E1-PS1-STREAM/run2"]["valid"],
             "SNES": V["runs/E1-SNES-STREAM/run1"]["valid"],
             "PS1 r1 replacement": V["runs_retry1/E1-PS1-STREAM/run1"]["valid"]}
    out, mins = {}, {}
    for a in ("PS1 r1", "PS1 r2", "SNES", "PS1 r1 replacement"):
        s = S[a]
        rf = k(s, "teardown", "report_fields") or {}
        m = (rf.get("duration_ms") or 0) / 60000
        t0, t1 = A.t(s["window"]["from"]), A.t(s["window"]["to"])
        L = A.hb_loss_series(t0, t1)
        mins[a] = [round(sum(v for sec, v in L.items() if t0 + 60 * i <= sec < t0 + 60 * (i + 1)), 1) for i in range(20)]
        x = {"sender_cpu": t[a]["threads"].get("audio_sender_cpu"),
             "companion_cpu": k(s, "host", "host", "procs.companion.cpu_pct", "mean"),
             "host_cpu": k(s, "host", "host", "cpu.mean_pct", "mean"),
             "underruns": k(s, "key", "heartbeat", "audio_underruns"),
             "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"),
             "retroarch_fps": rows["RetroArch fps"](s), "capture_fps": rows["encoder capture fps"](s),
             "retroarch_cpu": k(s, "host", "host", "procs.retroarch.cpu_pct", "mean"),
             "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"),
             "minute_median": statistics.median(mins[a]), "minutes_gt_100": sum(1 for v in mins[a] if v > 100),
             "spikes20_per_min": round(rf["decoder.spike_20_ms"] / m, 1) if m and "decoder.spike_20_ms" in rf else None,
             "stale_per_min": round(rf["decoder.stale_output_drops"] / m, 2) if m and "decoder.stale_output_drops" in rf else None,
             "socket_w": k(s, "host", "host", "gpu.socket_power_w", "mean"),
             "c2_gap_max_ms": k(s, "key", "telemetry", "output_gap_ms_max"),
             "report_max_gap_ms": rf.get("decoder.max_output_gap_ms")}
        x["f1"] = x["sender_cpu"] is not None and x["sender_cpu"] <= 8 and x["companion_cpu"] <= 20
        out[a] = x
    for a in ("PS1 r1", "PS1 r2", "PS1 r1 replacement"):
        x = out[a]
        x["valid"] = valid[a]
        x["f2"] = x["underruns"] <= 20
        x["f3"] = x["rendered_fps"] >= 59.5 and abs(x["host_cpu"] - 11.69) <= 2 and abs(x["rendered_fps"] - 59.81) <= 0.5
        x["f4"] = x["spikes20_per_min"] is not None and x["spikes20_per_min"] < 200 and x["stale_per_min"] < 20
    x = out["SNES"]
    title = open(os.path.join(R, "E1-SNES-STREAM/run1/title.txt")).read()
    x["title_first"] = next((l.split("= ", 1)[1] for l in title.splitlines() if "WM_NAME" in l), None)
    x["retroarch_threads"] = t["SNES"].get("retroarch_threads")
    x["s1"] = x["retroarch_cpu"] is not None and x["retroarch_cpu"] <= 150
    x["s2"] = x["host_cpu"] <= 20
    x["s3"] = (x["retroarch_fps"] is not None and x["retroarch_fps"] >= 59.9 and x["capture_fps"] is not None
               and abs(x["capture_fps"] - 60) <= 0.5 and x["rendered_fps"] >= 59.5)
    x["s4"] = "Snes9x" in title and "bsnes" not in title
    g = json.load(open(os.path.join(HERE, "guide_read_after.json")))
    mm, e = t["META"]["companion_mem"], S["META"]["key"]["epg"]
    out["META"] = {"pss_end_mb": mm["pss_last_mb"], "m1": mm["pss_last_mb"] <= 60,
                   "grabs": [e["grabs_ok"], e["grabs_failed"], e["grab_s_median"]],
                   "m2": e["grabs_failed"] == 0 and e["grabs_ok"] >= 205,
                   "guide": [g["channels_serving"], g["programmes_total"]],
                   "m3": g["channels_serving"] == 6 and 271 <= g["programmes_total"] <= 299,
                   "companion_cpu": k(S["META"], "host", "host", "procs.companion.cpu_pct", "mean"),
                   "host_cpu": k(S["META"], "host", "host", "cpu.mean_pct", "mean"),
                   "socket_w": k(S["META"], "host", "host", "gpu.socket_power_w", "mean"),
                   "last15_pct": mm["last15_growth_pct"]}
    judged = [a for a in ("PS1 r2", "PS1 r1 replacement") if valid[a]]     # the addendum: r1 invalid, replaced
    out["judged_ps1_runs"] = judged
    out["SNES"]["valid"] = valid["SNES"]
    fs = [f"{a}.{c}" for a in judged for c in ("f1", "f2", "f3", "f4") if not out[a][c]]
    fs += [] if len(judged) == 2 else ["fewer than two valid PS1-STREAM runs"]
    out["not_judged"] = {"PS1 r1": [c for c in ("f1", "f2", "f3", "f4") if not out["PS1 r1"][c]]}
    fs += ["SNES.f1"] if not out["SNES"]["f1"] else []
    ss = [f"SNES.{c}" for c in ("s1", "s2", "s3", "s4") if not out["SNES"][c]]
    ms = [f"META.{c}" for c in ("m1", "m2", "m3") if not out["META"][c]]
    out["frame_spin"] = {"failing": fs, "verdict": "ADOPTION STANDS" if not fs else "ADOPTION REVERTED"}
    out["snes9x"] = {"failing": ss, "verdict": "ADOPTION STANDS" if not ss else "ADOPTION REVERTED"}
    out["index_with_others"] = {"failing": ms, "verdict": "HOLDS" if not ms else "FAILS (the user's call)"}
    json.dump(out, open(os.path.join(HERE, "e3_a2_verdict.json"), "w"), indent=1, default=str)
    with open(os.path.join(HERE, "loss_per_minute.txt"), "w") as fh:
        fh.write("lost video packets per minute of each 20-min window (heartbeat), E3-A2, in run order\n")
        for a in ("PS1 r1", "PS1 r2", "SNES", "PS1 r1 replacement"):
            fh.write(f"{a}: {mins[a]}  minutes > 100: {out[a]['minutes_gt_100']}; median {out[a]['minute_median']}\n")
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
