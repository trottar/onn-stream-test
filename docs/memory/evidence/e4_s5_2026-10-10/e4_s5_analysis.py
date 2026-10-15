#!/usr/bin/env python3
"""E4-S5 §2-§3 -- the sessions and the flagged runs, as pre-registered (e4_s5_preregistration.txt). Read-only.
-> e4_s5_table.md, e4_s5_verdict.json, validity.json. The per-window classifier is offline.py's (e4_s5_offline.py,
imported from this directory); capture and dup+drop are segment-aware (as E4-S2)."""
import glob
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
spec = importlib.util.spec_from_file_location("offline", os.path.join(HERE, "e4_s5_offline.py"))
O = importlib.util.module_from_spec(spec)
spec.loader.exec_module(O)
REF_HOST = 7.4     # E4-S1 SNES-STREAM host CPU


def k(s, *p):
    for x in p:
        s = s.get(x) if isinstance(s, dict) else None
    return s


def segcap(rd, s):
    t0, t1 = s["window"]["from"], s["window"]["to"]
    rows = [r for r in O.jl(os.path.join(rd, "encoder.jsonl")) if r.get("records") and t0 <= r["at_utc"] <= t1]
    fr = dt = dd = 0.0
    for a, b in zip(rows, rows[1:]):
        d = O.ep(b["at_utc"]) - O.ep(a["at_utc"])
        if b["frame"] < a["frame"] or d > 3 or b["dup"] < a["dup"] or b["drop"] < a["drop"]:
            continue
        fr += b["frame"] - a["frame"]
        dt += d
        dd += (b["dup"] - a["dup"]) + (b["drop"] - a["drop"])
    return (round(fr / dt, 3) if dt else None, round(dd / (dt / 60), 3) if dt else None)


def ra_verbose(s):
    """The RetroArch session log for the run: verbose lines about refresh / timing / swap / sync."""
    log = O.ra_log(O.ep(s["gap"]["to"]))
    p = os.path.join(REPO, "logs/games", log.get("log") or "-")
    if not os.path.exists(p):
        return {"log_found": False}
    txt = open(p, errors="replace").read()
    pat = re.compile(r"refresh|swap|vsync|frame ?time|estimat|sync|monitor|Hz", re.I)
    lines = [l.strip()[:200] for l in txt.splitlines() if pat.search(l) and "[Input]" not in l]
    return {"log_found": True, "lines_total": len(txt.splitlines()), "debug_lines": sum(1 for l in txt.splitlines() if "[DEBUG]" in l),
            "timing_lines": lines[:25]}


def sidecar(path):
    rows = O.jl(path)
    enc = [r for r in rows if r.get("event") == "encoder_start"]
    fm = [r for r in rows if r.get("event") == "framemd5"]
    return enc, fm


def session(rd, enc_rows, fm_rows):
    s = json.load(open(os.path.join(rd, "summary.json")))
    if s.get("status") != "OK":
        return {"run": os.path.relpath(rd, HERE), "status": s.get("status")}
    w = O.window(rd, O.encoder_sessions())
    cap, dd = segcap(rd, s)
    t0, t1 = O.ep(s["gap"]["from"]), O.ep(s["window"]["to"])
    en = [r for r in enc_rows if t0 <= O.ep(r["at_utc"]) <= t1]
    fm = [r for r in fm_rows if t0 <= O.ep(r["from_utc"]) <= t1]
    return {"run": os.path.relpath(rd, HERE), "status": "OK", "class": w["class"], "fault_s": w["fault_s"],
            "capture_fps": cap, "dupdrop_per_min": dd, "drops_per_s": w["drops_per_s"],
            "input_tbr": [r.get("input_tbr") for r in en], "output_fps": [r.get("output_fps") for r in en],
            "output_r_arg": [r.get("output_r_arg") for r in en],
            "window_distinct_fps": [r.get("distinct_mean") for r in fm], "window_distinct_min_max": [(r.get("distinct_min"), r.get("distinct_max")) for r in fm],
            "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"), "retroarch_fps": k(s, "key", "retroarch", "frames_per_s"),
            "host_cpu": k(s, "host", "host", "cpu.mean_pct", "mean"), "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"),
            "resyncs": k(s, "key", "heartbeat", "stream_resyncs"), "socket_w": k(s, "host", "host", "gpu.socket_power_w", "mean"),
            "flags_absent_after": k(s, "teardown", "flags_absent"), "retroarch_log": ra_verbose(s)}


def main():
    e1, f1 = sidecar(os.path.join(HERE, "runs_sessions", "sidecar.jsonl"))
    e2, f2 = sidecar(os.path.join(HERE, "runs_flag", "sidecar.jsonl"))
    ses = [session(rd, e1, f1) for rd in sorted(glob.glob(os.path.join(HERE, "runs_sessions", "E1-SNES-STREAM", "run*")))]
    flg = [session(rd, e2, f2) for rd in sorted(glob.glob(os.path.join(HERE, "runs_flag", "E1-SNES-STREAM_flag", "run*")))]
    json.dump({"sessions": [x.get("status") for x in ses], "flag": [x.get("status") for x in flg]},
              open(os.path.join(HERE, "validity.json"), "w"), indent=1)
    # §2's statements: (i) fault iff tbr 59; (ii) the window ~60 distinct frames/s in every session
    st_i = all((x["class"].startswith("FAULT")) == ("59" in x["input_tbr"]) for x in ses if x["status"] == "OK")
    st_ii = all(all(v is not None and abs(v - 60) <= 1 for v in x["window_distinct_fps"]) and x["window_distinct_fps"]
                for x in ses if x["status"] == "OK")
    out = {"sessions": ses, "flagged": flg, "statement_i_fault_iff_tbr59": st_i, "statement_ii_window_60": st_ii,
           "faulty_sessions": sum(1 for x in ses if x.get("class", "").startswith("FAULT"))}
    ok = len(flg) == 2 and all(x["status"] == "OK" for x in flg)
    if ok:
        cl = {x["run"]: {"capture_60_pm_0.1": x["capture_fps"] is not None and abs(x["capture_fps"] - 60) <= 0.1,
                         "dupdrop_le_0.2": x["dupdrop_per_min"] is not None and x["dupdrop_per_min"] <= 0.2,
                         "rendered_ge_59.5": (x["rendered_fps"] or 0) >= 59.5, "retroarch_ge_59.9": (x["retroarch_fps"] or 0) >= 59.9,
                         "host_cpu_pm_2": x["host_cpu"] is not None and abs(x["host_cpu"] - REF_HOST) <= 2,
                         "output_r_60": x["output_r_arg"] == ["60"] * len(x["output_r_arg"]) and bool(x["output_r_arg"])}
              for x in flg}
        out["bar"] = cl
        failed = sorted({c for r in cl.values() for c, v in r.items() if not v})
        out["verdict"] = "ACCEPTED" if not failed else "REJECTED (" + ", ".join(failed) + ")"
    else:
        out["verdict"] = "INCONCLUSIVE (a flagged run did not complete)"
    json.dump(out, open(os.path.join(HERE, "e4_s5_verdict.json"), "w"), indent=1, default=str)
    md = ["# E4-S5 — the sessions and the flagged runs", "",
          "| run | class | capture fps / dup+drop per min | input tbr → output fps (-r) | window distinct fps (min-max) | rendered | RetroArch | host CPU | loss/min |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for x in ses + flg:
        if x["status"] != "OK":
            md.append(f"| {x['run']} | {x['status']} | | | | | | | |")
            continue
        md.append(f"| {x['run']} | **{x['class']}** | {x['capture_fps']} / {x['dupdrop_per_min']} | "
                  f"{', '.join(f'{a} → {b} ({c})' for a, b, c in zip(x['input_tbr'], x['output_fps'], x['output_r_arg']))} | "
                  f"{x['window_distinct_fps']} {x['window_distinct_min_max']} | {x['rendered_fps']} | {x['retroarch_fps']} | "
                  f"{round(x['host_cpu'], 2) if x['host_cpu'] else None} | {x['loss_per_min']} |")
    md += ["", f"Statement (i), the fault iff the probe reads 59: {st_i}; (ii), the window at ~60 distinct frames/s: {st_ii}.",
           f"Faulty sessions in §2: {out['faulty_sessions']} of {len(ses)}.", "", f"**§3 verdict: {out['verdict']}**", "",
           "RetroArch's verbose log (first session), timing-related lines:", "", "```"]
    if ses and ses[0].get("retroarch_log"):
        rl = ses[0]["retroarch_log"]
        md += [f"lines {rl.get('lines_total')}, [DEBUG] lines {rl.get('debug_lines')}"] + (rl.get("timing_lines") or [])
    md.append("```")
    open(os.path.join(HERE, "e4_s5_table.md"), "w").write("\n".join(md) + "\n")
    print(json.dumps({kk: out[kk] for kk in ("statement_i_fault_iff_tbr59", "statement_ii_window_60", "faulty_sessions", "verdict")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
