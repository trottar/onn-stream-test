#!/usr/bin/env python3
"""CL-B3: the PS1-STREAM runs (R1 on the seven-line state, identity_v2 on; W the same with the per-run drop-in
PRIVYHUB_WAN_TELEMETRY=1) against cl_b3_preregistration.txt's host-side gates (CL-B2's): status OK, RetroArch >= 59.9,
capture 60.0 +/- 0.1 and dup+drop <= 0.2/min (E4-S5D's segcap, imported), flags_absent after. HOST CPU IS REPORTED, NOT
GATED, beside the ladder's rung range (status_poll bitrate_kbps), the ladder's acted decisions and the per-process split
(the CL-B2 bar lesson). Loss and rendered reported. W's cost: companion CPU (% of one core) and PSS, W minus R1.
Read-only. -> cl_b3_table.md, cl_b3_verdict.json, validity.json."""
import glob
import importlib.util
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("s5d", os.path.join(HERE, "../e4_s5d_2026-10-15/e4_s5d_analysis.py"))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
PROCS = ("companion", "retroarch", "encoder", "xorg")
LABEL = {"E1-PS1-STREAM": "R1", "E1-PS1-STREAM_flag": "W"}


def rungs(rd):
    c = Counter()
    for line in open(os.path.join(rd, "status_poll.jsonl")):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r.get("bitrate_kbps"), (int, float)):
            c[int(r["bitrate_kbps"])] += 1
    acts = []
    for line in open(os.path.join(rd, "decisions.jsonl")):
        r = json.loads(line)
        if r.get("acted"):
            acts.append({"at_utc": r.get("at_utc"), "event": r.get("event"), "from_kbps": r.get("from_kbps"),
                         "to_kbps": r.get("to_kbps")})
    return c, acts


def one(rd):
    s = json.load(open(os.path.join(rd, "summary.json")))
    rel = os.path.relpath(rd, HERE)
    if s.get("status") != "OK":
        return {"run": rel, "status": s.get("status")}
    cap, dd = S.segcap(rd, s)
    k = S.k
    h = json.load(open(os.path.join(rd, "sampler_summary.json")))["host"]
    c, acts = rungs(rd)
    x = {"run": rel, "label": LABEL.get(rel.split(os.sep)[1], rel), "status": "OK", "window": s["window"],
         "capture_fps": cap, "dupdrop_per_min": dd,
         "retroarch_fps": k(s, "key", "retroarch", "frames_per_s"), "host_cpu": k(s, "host", "host", "cpu.mean_pct", "mean"),
         "procs_cpu_pct_of_core": {p: h[f"procs.{p}.cpu_pct"]["mean"] for p in PROCS if f"procs.{p}.cpu_pct" in h},
         "companion_pss_kb": h.get("procs.companion.pss_kb", {}).get("mean"),
         "rung_kbps_range": [min(c), max(c)] if c else None, "rung_kbps_polls": {str(r): n for r, n in sorted(c.items())},
         "ladder_acted": acts,
         "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"), "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"),
         "resyncs": k(s, "key", "heartbeat", "stream_resyncs"), "flags_absent_after": k(s, "teardown", "flags_absent"),
         "dropin": s.get("dropin") or k(s, "restart", "environ")}
    x["gates"] = {"retroarch_ge_59.9": (x["retroarch_fps"] or 0) >= 59.9,
                  "capture_60_pm_0.1": cap is not None and abs(cap - 60) <= 0.1,
                  "dupdrop_le_0.2": dd is not None and dd <= 0.2,
                  "flags_absent_after": bool(x["flags_absent_after"])}
    return x


def main():
    rds = sorted(glob.glob(os.path.join(HERE, "runs", "E1-PS1-STREAM*", "run*")),
                 key=lambda d: json.load(open(os.path.join(d, "summary.json")))["started_utc"])
    res = [one(d) for d in rds if os.path.exists(os.path.join(d, "summary.json"))]
    json.dump({r["run"]: r["status"] for r in res}, open(os.path.join(HERE, "validity.json"), "w"), indent=1)
    failed = [f"{r['run']}:{g}" for r in res for g, v in (r.get("gates") or {}).items() if not v] + \
             [f"{r['run']}:status" for r in res if r["status"] != "OK"]
    verdict = "ALL HOST GATES HOLD" if not failed else "FAILED (" + ", ".join(failed) + ")"
    by = {r.get("label"): r for r in res if r["status"] == "OK"}
    cost = None
    if "R1" in by and "W" in by:
        a, b = by["R1"], by["W"]
        dcpu = round(b["procs_cpu_pct_of_core"]["companion"] - a["procs_cpu_pct_of_core"]["companion"], 3)
        dpss = round(((b["companion_pss_kb"] or 0) - (a["companion_pss_kb"] or 0)) / 1024, 3)
        cost = {"companion_cpu_point_of_core_W_minus_R1": dcpu, "companion_pss_mb_W_minus_R1": dpss,
                "le_0.5_point": dcpu <= 0.5, "le_2_mb": dpss <= 2,
                "note": "two runs, not paired arms; read beside the rung ranges"}
    json.dump({"runs": res, "verdict": verdict, "wan_cost": cost}, open(os.path.join(HERE, "cl_b3_verdict.json"), "w"), indent=1)
    md = ["# CL-B3 — the PS1-STREAM runs", "",
          "| run | window (UTC) | capture fps | dup+drop /min | RetroArch | host CPU %† | rung kbps (polls) | ladder acted | companion / RetroArch / encoder % of a core | flags_absent after | rendered* | loss/min* | resyncs* |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        if r["status"] != "OK":
            md.append(f"| {r['run']} | {r['status']} |" + " |" * 11)
            continue
        w, p = r["window"], r["procs_cpu_pct_of_core"]
        md.append(f"| {r['label']} `{r['run']}` | {w['from'][11:16]}-{w['to'][11:16]} | {r['capture_fps']} | {r['dupdrop_per_min']} | "
                  f"{r['retroarch_fps']} | {r['host_cpu']} | {r['rung_kbps_range']} {r['rung_kbps_polls']} | {len(r['ladder_acted'])} | "
                  f"{p.get('companion')} / {p.get('retroarch')} / {p.get('encoder')} | {r['flags_absent_after']} | {r['rendered_fps']} | "
                  f"{r['loss_per_min']} | {r['resyncs']} |")
    md += ["", "† reported, not gated (the CL-B2 bar lesson). \\* the link: reported, not gated.", ""]
    if cost:
        md += [f"W's cost (companion, W − R1): {cost['companion_cpu_point_of_core_W_minus_R1']} point of a core, "
               f"{cost['companion_pss_mb_W_minus_R1']} MB PSS (≤ 0.5 / ≤ 2: {cost['le_0.5_point']} / {cost['le_2_mb']}).", ""]
    md += [f"**{verdict}**"]
    open(os.path.join(HERE, "cl_b3_table.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
