#!/usr/bin/env python3
"""E3-S5 -- the bar as pre-registered (e3_s5_preregistration.txt). Read-only. -> e3_s5_table.md/.json, e3_s5_verdict.json"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
E2R = os.path.join(REPO, "docs/memory/evidence/e2_s1_2026-10-05/runs")
R = os.path.join(HERE, "runs")


def k(s, *p):
    for x in p:
        s = (s or {}).get(x) if isinstance(s, dict) else None
    return s


def main():
    cols = [("control", f"{R}/E1-PS1-STREAM/run1"), ("flag r1", f"{R}/E1-PS1-STREAM_flag/run1"),
            ("flag r2", f"{R}/E1-PS1-STREAM_flag/run2"), ("E2 PS1-STREAM", f"{E2R}/E1-PS1-STREAM/run1")]
    subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_table.py"), os.path.join(HERE, "e3_s5_table.md")]
                   + [f"{a}={b}" for a, b in cols], check=True, stdout=subprocess.DEVNULL)
    t = json.load(open(os.path.join(HERE, "e3_s5_table.json")))
    S = {a: json.load(open(os.path.join(b, "summary.json"))) for a, b in cols}
    hb = lambda a, x: k(S[a], "key", "heartbeat", x)
    ctl_loss, ctl_ur = hb("control", "video_loss_per_min"), hb("control", "audio_underruns")
    out = {}
    for a in ("control", "flag r1", "flag r2"):
        rf = k(S[a], "teardown", "report_fields") or {}
        mins = (rf.get("duration_ms") or 0) / 60000
        out[a] = {"sender_cpu": t[a]["threads"].get("audio_sender_cpu"),
                  "companion_cpu": k(S[a], "host", "host", "procs.companion.cpu_pct", "mean"),
                  "underruns": hb(a, "audio_underruns"), "rendered_fps": hb(a, "rendered_fps"),
                  "retroarch_fps": k(S[a], "key", "retroarch", "frames_per_s"), "loss_per_min": hb(a, "video_loss_per_min"),
                  "spikes20_per_min": round(rf["decoder.spike_20_ms"] / mins, 1) if mins and "decoder.spike_20_ms" in rf else None,
                  "stale_per_min": round(rf["decoder.stale_output_drops"] / mins, 2) if mins and "decoder.stale_output_drops" in rf else None,
                  "report_max_gap_ms": rf.get("decoder.max_output_gap_ms"),
                  "c2_gap_max_ms": k(S[a], "key", "telemetry", "output_gap_ms_max"),
                  "c2_r2d_median_ms": k(S[a], "key", "telemetry", "receive_to_decode_ms_median"),
                  "relay_cpu": t[a]["threads"].get("relay_cpu"),
                  "host_cpu": k(S[a], "host", "host", "cpu.mean_pct", "mean"),
                  "socket_w": k(S[a], "host", "host", "gpu.socket_power_w", "mean"),
                  "sender_syscall": t[a]["threads"].get("audio_sender_syscall")}
    loss_gated = ctl_loss is not None and ctl_loss < 10
    for a in ("flag r1", "flag r2"):
        x = out[a]
        x["a"] = x["sender_cpu"] is not None and x["sender_cpu"] <= 4 and x["companion_cpu"] <= 17
        x["b"] = x["underruns"] is not None and x["underruns"] <= ctl_ur + 5 and x["underruns"] <= 20
        x["c"] = (x["rendered_fps"] >= 59.5 and abs(x["retroarch_fps"] - 60) <= 0.5 and x["loss_per_min"] <= 3 * ctl_loss)
        x["d"] = (x["spikes20_per_min"] is not None and x["spikes20_per_min"] < 200 and x["stale_per_min"] < 20
                  and (x["loss_per_min"] < 10 if loss_gated else True))
    e2 = S["E2 PS1-STREAM"]
    e = (abs(out["control"]["host_cpu"] - k(e2, "host", "host", "cpu.mean_pct", "mean")) <= 2
         and abs(out["control"]["rendered_fps"] - k(e2, "key", "heartbeat", "rendered_fps")) <= 0.5)
    out["e_comparable"] = {"control_cpu": out["control"]["host_cpu"], "e2_cpu": k(e2, "host", "host", "cpu.mean_pct", "mean"),
                           "control_fps": out["control"]["rendered_fps"], "e2_fps": k(e2, "key", "heartbeat", "rendered_fps"),
                           "holds": e}
    out["loss_row_gated"] = loss_gated
    allok = all(out[a][c] for a in ("flag r1", "flag r2") for c in "abcd")
    out["verdict"] = "INCONCLUSIVE" if not e else ("ACCEPTED" if allok else "REJECTED")
    out["verdict_abcd_alone"] = "all hold" if allok else "some fail"
    json.dump(out, open(os.path.join(HERE, "e3_s5_verdict.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    sys.exit(main())
