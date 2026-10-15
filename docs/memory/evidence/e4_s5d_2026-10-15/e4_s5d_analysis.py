#!/usr/bin/env python3
"""E4-S5D §2 -- the two confirmation runs on the five-line adopted state, read against e4_s5d_preregistration.txt.
Read-only over runs/ and logs/games/native_video_alpha.log (from the byte offset taken before the SNES run).
Capture and dup+drop are segment-aware, E4-S5's segcap (e4_s5_analysis.py) unchanged; the encoder starts' probed
input tbr, output fps and the presence of -r 60 in the 'encoder argv:' line, per encoder block in the run's span.
-> e4_s5d_table.md, e4_s5d_verdict.json, validity.json."""
import json
import os
import re
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
LOG = os.path.join(REPO, "logs/games/native_video_alpha.log")
REF_HOST = 7.4     # E4-S1 SNES-STREAM host CPU; E1's band +/- 2 points
ep = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def k(s, *p):
    for x in p:
        s = s.get(x) if isinstance(s, dict) else None
    return s


def jl(p):
    out = []
    for l in open(p, errors="replace"):
        try:
            out.append(json.loads(l))
        except ValueError:
            pass
    return out


def segcap(rd, s):
    """E4-S5's segcap, verbatim in effect: frames / s and (dup + drop) / min over the window, a counter reset or a
    > 3-s hole skipping its pair."""
    t0, t1 = s["window"]["from"], s["window"]["to"]
    rows = [r for r in jl(os.path.join(rd, "encoder.jsonl")) if r.get("records") and t0 <= r["at_utc"] <= t1]
    fr = dt = dd = 0.0
    for a, b in zip(rows, rows[1:]):
        d = ep(b["at_utc"]) - ep(a["at_utc"])
        if b["frame"] < a["frame"] or d > 3 or b["dup"] < a["dup"] or b["drop"] < a["drop"]:
            continue
        fr += b["frame"] - a["frame"]
        dt += d
        dd += (b["dup"] - a["dup"]) + (b["drop"] - a["drop"])
    return (round(fr / dt, 3) if dt else None, round(dd / (dt / 60), 3) if dt else None)


def encoder_blocks():
    off = int(open(os.path.join(HERE, "alpha_log_offset_snes.txt")).read().split()[0])
    with open(LOG, "rb") as fh:
        fh.seek(off)
        raw = fh.read().decode("utf-8", "replace")
    out = []
    for b in raw.split("Starting PrivyHub Linux native-video backend")[1:]:
        m = re.search(r"start: (\d+\.\d+)", b)
        argv = re.search(r"encoder argv: ([^\n]*)", b)
        inp = re.search(r"Stream #0:0: Video: rawvideo[^\n]*", b)
        outl = re.search(r"Stream #0:0: Video: h264[^\n]*", b)
        t = re.search(r"Window title: RetroArch (\S+)", b)
        a = argv.group(1).split() if argv else []
        r_arg = a[a.index("-r") + 1] if "-r" in a else None
        out.append({"start": float(m.group(1)) if m else None, "core": t.group(1) if t else None,
                    "argv_found": bool(argv), "output_r_arg": r_arg,
                    "r_before_an": bool(r_arg) and a.index("-r") + 2 == (a.index("-an") if "-an" in a else -1),
                    "input_tbr": (re.search(r"([\d.k]+) tbr", inp.group(0)).group(1) if inp and re.search(r"([\d.k]+) tbr", inp.group(0)) else None),
                    "output_fps": (re.search(r"([\d.]+) fps", outl.group(0)).group(1) if outl and re.search(r"([\d.]+) fps", outl.group(0)) else None)})
    return out


def run(wid):
    rd = os.path.join(HERE, "runs", wid, "run1")
    s = json.load(open(os.path.join(rd, "summary.json")))
    if s.get("status") != "OK":
        return {"run": f"runs/{wid}/run1", "status": s.get("status")}
    cap, dd = segcap(rd, s)
    t0, t1 = ep(s["gap"]["to"]) - 5, ep(s["window"]["to"]) + 5
    en = [b for b in encoder_blocks() if b["start"] and t0 <= b["start"] <= t1]
    return {"run": f"runs/{wid}/run1", "status": "OK", "window": s["window"], "capture_fps": cap, "dupdrop_per_min": dd,
            "encoder_starts": en, "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"),
            "retroarch_fps": k(s, "key", "retroarch", "frames_per_s"), "host_cpu": k(s, "host", "host", "cpu.mean_pct", "mean"),
            "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"), "resyncs": k(s, "key", "heartbeat", "stream_resyncs"),
            "socket_w": k(s, "host", "host", "gpu.socket_power_w", "mean"), "preflight_ok": k(s, "preflight", "ok"),
            "preflight_environ": k(s, "preflight", "environ"), "flags_absent_after": k(s, "teardown", "flags_absent")}


def main():
    have = [w for w in ("E1-SNES-STREAM", "E1-PS1-STREAM") if os.path.exists(os.path.join(HERE, "runs", w, "run1", "summary.json"))]
    res = {w: run(w) for w in have}
    json.dump({w: r.get("status") for w, r in res.items()}, open(os.path.join(HERE, "validity.json"), "w"), indent=1)
    gates = {}
    sn = res.get("E1-SNES-STREAM")
    if sn and sn["status"] == "OK":
        en = sn["encoder_starts"]
        gates["E1-SNES-STREAM"] = {
            "argv_r60_every_start": bool(en) and all(e["output_r_arg"] == "60" for e in en),
            "capture_60_pm_0.1": sn["capture_fps"] is not None and abs(sn["capture_fps"] - 60) <= 0.1,
            "dupdrop_le_0.2": sn["dupdrop_per_min"] is not None and sn["dupdrop_per_min"] <= 0.2,
            "retroarch_ge_59.9": (sn["retroarch_fps"] or 0) >= 59.9,
            "host_cpu_pm_2_of_7.4": sn["host_cpu"] is not None and abs(sn["host_cpu"] - REF_HOST) <= 2}
    ps = res.get("E1-PS1-STREAM")
    if ps and ps["status"] == "OK":
        gates["E1-PS1-STREAM"] = {"capture_60_pm_0.1": ps["capture_fps"] is not None and abs(ps["capture_fps"] - 60) <= 0.1,
                                  "dupdrop_le_0.2": ps["dupdrop_per_min"] is not None and ps["dupdrop_per_min"] <= 0.2}
    failed = sorted(f"{w}:{c}" for w, g in gates.items() for c, v in g.items() if not v)
    incomplete = [w for w in ("E1-SNES-STREAM", "E1-PS1-STREAM") if w not in gates]
    verdict = ("FAILED (" + ", ".join(failed) + ")" if failed else
               ("INCOMPLETE (" + ", ".join(incomplete) + " not run / not OK)" if incomplete else "CONFIRMED"))
    json.dump({"runs": res, "gates": gates, "verdict": verdict}, open(os.path.join(HERE, "e4_s5d_verdict.json"), "w"), indent=1)
    md = ["# E4-S5D — the confirmation runs on the five-line adopted state", "",
          "| run | capture fps | dup+drop /min | encoder starts: input tbr → output fps (-r) | RetroArch | host CPU % | rendered* | loss/min* | resyncs* |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for w, x in res.items():
        if x["status"] != "OK":
            md.append(f"| {w} | {x['status']} | | | | | | | |")
            continue
        es = "; ".join(f"{e['input_tbr']} → {e['output_fps']} (-r {e['output_r_arg']})" for e in x["encoder_starts"]) or "none found"
        md.append(f"| {w} | {x['capture_fps']} | {x['dupdrop_per_min']} | {es} | {x['retroarch_fps']} | {x['host_cpu']} | "
                  f"{x['rendered_fps']} | {x['loss_per_min']} | {x['resyncs']} |")
    md += ["", "\\* the link: reported, not gated.", "", "## Gates", ""]
    for w, g in gates.items():
        md.append(f"- **{w}**: " + ", ".join(f"{c} {'✓' if v else '✗'}" for c, v in g.items()))
    md += ["", f"**{verdict}**"]
    open(os.path.join(HERE, "e4_s5d_table.md"), "w").write("\n".join(md) + "\n")
    print(json.dumps({"verdict": verdict, "gates": gates}, indent=1))


if __name__ == "__main__":
    main()
