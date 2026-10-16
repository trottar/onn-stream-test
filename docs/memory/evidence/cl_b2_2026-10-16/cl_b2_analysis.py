#!/usr/bin/env python3
"""CL-B2: the three PS1-STREAM runs (R1 setting off / flag absent, R2 paired + flag on, R3 both off) against
cl_b2_preregistration.txt's host-side gates (E4-S1 PS1-STREAM's): status OK, RetroArch >= 59.9, capture 60.0 +/- 0.1 and
dup+drop <= 0.2/min (E4-S5D's segcap, imported), host CPU within +/- 2 points of 10.9 %, flags_absent after. Loss and
rendered reported. Read-only. -> cl_b2_table.md, cl_b2_verdict.json, validity.json."""
import glob
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("s5d", os.path.join(HERE, "../e4_s5d_2026-10-15/e4_s5d_analysis.py"))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
REF_HOST = 10.9     # E4-S1 PS1-STREAM host CPU
LABEL = {"E1-PS1-STREAM": "R1/R3 (setting off, flag absent)", "E1-PS1-STREAM_flag": "R2 (paired, identity_v2 on, host flag on)"}


def one(rd):
    s = json.load(open(os.path.join(rd, "summary.json")))
    rel = os.path.relpath(rd, HERE)
    if s.get("status") != "OK":
        return {"run": rel, "status": s.get("status")}
    cap, dd = S.segcap(rd, s)
    k = S.k
    x = {"run": rel, "status": "OK", "window": s["window"], "capture_fps": cap, "dupdrop_per_min": dd,
         "retroarch_fps": k(s, "key", "retroarch", "frames_per_s"), "host_cpu": k(s, "host", "host", "cpu.mean_pct", "mean"),
         "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"), "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"),
         "resyncs": k(s, "key", "heartbeat", "stream_resyncs"), "flags_absent_after": k(s, "teardown", "flags_absent"),
         "dropin": s.get("dropin") or k(s, "restart", "environ")}
    x["gates"] = {"retroarch_ge_59.9": (x["retroarch_fps"] or 0) >= 59.9,
                  "capture_60_pm_0.1": cap is not None and abs(cap - 60) <= 0.1,
                  "dupdrop_le_0.2": dd is not None and dd <= 0.2,
                  "host_cpu_pm_2_of_10.9": x["host_cpu"] is not None and abs(x["host_cpu"] - REF_HOST) <= 2,
                  "flags_absent_after": bool(x["flags_absent_after"])}
    return x


def main():
    rds = sorted(glob.glob(os.path.join(HERE, "runs", "E1-PS1-STREAM*", "run*")), key=lambda d: json.load(open(os.path.join(d, "summary.json")))["started_utc"])
    res = [one(d) for d in rds if os.path.exists(os.path.join(d, "summary.json"))]
    json.dump({r["run"]: r["status"] for r in res}, open(os.path.join(HERE, "validity.json"), "w"), indent=1)
    failed = [f"{r['run']}:{g}" for r in res for g, v in (r.get("gates") or {}).items() if not v] + \
             [f"{r['run']}:status" for r in res if r["status"] != "OK"]
    verdict = "ALL HOST GATES HOLD" if not failed else "FAILED (" + ", ".join(failed) + ")"
    json.dump({"runs": res, "verdict": verdict}, open(os.path.join(HERE, "cl_b2_verdict.json"), "w"), indent=1)
    md = ["# CL-B2 — the PS1-STREAM runs", "",
          "| run | window (UTC) | capture fps | dup+drop /min | RetroArch | host CPU % | flags_absent after | rendered* | loss/min* | resyncs* |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        if r["status"] != "OK":
            md.append(f"| {r['run']} | {r['status']} | | | | | | | | |")
            continue
        w = r["window"]
        md.append(f"| {r['run']} | {w['from'][11:16]}-{w['to'][11:16]} | {r['capture_fps']} | {r['dupdrop_per_min']} | {r['retroarch_fps']} | "
                  f"{r['host_cpu']} | {r['flags_absent_after']} | {r['rendered_fps']} | {r['loss_per_min']} | {r['resyncs']} |")
    md += ["", "\\* the link: reported, not gated.", "", f"**{verdict}**"]
    open(os.path.join(HERE, "cl_b2_table.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
