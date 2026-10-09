#!/usr/bin/env python3
"""E3-S7B -- the bar as pre-registered (e3_s7b_preregistration.txt; E3-S7's bar, unchanged). Read-only. Adapted from
E3-S7's e3_s7_analysis.py (copied here, not run there). Applies E3-A2's validity rule first, re-implemented here (a run
whose recovery state leaves PLAYING in its window is invalid; its replacement in runs_retry<n>/ takes its place).
-> e3_s7b_table.md/.json, aligned_ctl/, validity.json, loss_vs_cycle.md, e3_s7b_verdict.json"""
import glob
import importlib.util
import json
import os
import statistics
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
EV = os.path.join(REPO, "docs/memory/evidence")
E2R = os.path.join(EV, "e2_s1_2026-10-05/runs")
CH6 = ["ComedyCentral.us@East", "CNBCUK.uk@SD", "10Bold.au@Sydney", "FoxSports1.us@HD", "NBC.us@East", "FilmBox.nl@Netherlands"]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def k(s, *p):
    for x in p:
        s = (s or {}).get(x) if isinstance(s, dict) else None
    return s


def events():
    seen = set()
    for f in sorted(glob.glob(os.path.join(REPO, "logs/games/stream_log_archive/native_stream_recovery.log*"))) + \
            [os.path.join(REPO, "logs/games/native_stream_recovery.log.1"), os.path.join(REPO, "logs/games/native_stream_recovery.log")]:
        try:
            lines = open(f, errors="replace").read().splitlines()
        except OSError:
            continue
        for l in lines:
            if l in seen:
                continue
            seen.add(l)
            try:
                yield json.loads(l)
            except ValueError:
                pass


def validity():
    ev = list(events())
    out = {}
    for sp in sorted(glob.glob(os.path.join(HERE, "runs*", "*", "run*", "summary.json"))):
        s = json.load(open(sp))
        if s.get("kind") != "stream" or not s.get("window"):
            continue
        t0, t1 = s["window"]["from"], s["window"]["to"]
        bad = [(r.get("at_utc"), r.get("event"), r.get("trigger")) for r in ev if t0 <= (r.get("at_utc") or "") <= t1
               and (r.get("event") == "desync_pause" or str(r.get("event", "")).startswith("gave_up")
                    or str(r.get("state", "")).startswith("PAUSED"))]
        out[os.path.relpath(os.path.dirname(sp), HERE)] = {"window": [t0, t1], "valid": not bad, "events": bad}
    json.dump(out, open(os.path.join(HERE, "validity.json"), "w"), indent=1)
    return out


def pick(val, row, n):
    """the judged run for <row> number n: runs/<row>/run<n> if valid, else the first valid replacement."""
    for d in ["runs"] + [f"runs_retry{i}" for i in (1, 2)]:
        rel = f"{d}/{row}/run{n if d == 'runs' else 1}"
        if rel in val and val[rel]["valid"]:
            return rel
    return None


def aligned(conc_rels, ctl_rel):
    A = load("e2a", "docs/memory/evidence/e2_s1_2026-10-05/e2_analysis.py")
    view = os.path.join(HERE, "aligned_ctl")
    os.makedirs(os.path.join(view, "E1-CONC"), exist_ok=True)
    for i, rel in enumerate(conc_rels, 1):
        p = os.path.join(view, "E1-CONC", f"run{i}")
        if os.path.islink(p):
            os.unlink(p)
        os.symlink(os.path.relpath(os.path.join(HERE, rel), os.path.dirname(p)), p)
    p = os.path.join(view, "E1-PS1-STREAM")
    os.makedirs(p, exist_ok=True)
    q = os.path.join(p, "run1")
    if os.path.islink(q):
        os.unlink(q)
    os.symlink(os.path.relpath(os.path.join(HERE, ctl_rel), p), q)
    A.R, A.HERE = view, view
    out = {}
    A.conc(out)
    return out["conc"]


def main():
    val = validity()
    ctl = pick(val, "E1-PS1-STREAM", 1)
    concs = [pick(val, "E1-CONC_flag", n) for n in (1, 2)]
    cols = [("control", ctl), ("CONC paced r1", concs[0]), ("CONC paced r2", concs[1])]
    S7 = f"{EV}/e3_s7_2026-10-08/runs/E1-CONC_flag"
    cols = [(a, os.path.join(HERE, b)) for a, b in cols if b]
    cols += [("S7 CONC 4000 r1", f"{S7}/run1"), ("S7 CONC 4000 r2", f"{S7}/run2"),
             ("S6A CONC (index, today's grab)", f"{EV}/e3_s6a_2026-10-07/runs/E1-CONC/run1"),
             ("E2 PS1-STREAM", f"{E2R}/E1-PS1-STREAM/run1"), ("E2 CONC r1", f"{E2R}/E1-CONC/run1")]
    subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_table.py"), os.path.join(HERE, "e3_s7b_table.md")]
                   + [f"{a}={b}" for a, b in cols], check=True, stdout=subprocess.DEVNULL)
    t = json.load(open(os.path.join(HERE, "e3_s7b_table.json")))
    out = {"task1_flag": "ABSENT in every run (E3-R2 REJECTED)", "delay_ms": 1500, "judged": {"control": ctl, "conc": concs},
           "validity": val}
    if not ctl or not all(concs):
        out["verdict"] = "REJECTED (broke the row: no valid run after two replacements)"
        json.dump(out, open(os.path.join(HERE, "e3_s7b_verdict.json"), "w"), indent=1, default=str)
        print(json.dumps(out, indent=1, default=str))
        return
    S = {a: json.load(open(os.path.join(b, "summary.json"))) for a, b in cols}
    c, e2 = S["control"], S["E2 PS1-STREAM"]
    cpu, fps = k(c, "host", "host", "cpu.mean_pct", "mean"), k(c, "key", "heartbeat", "rendered_fps")
    comp = abs(cpu - 11.69) <= 2 and abs(fps - 59.81) <= 0.5
    al = aligned(concs, ctl)
    base = al["baseline"]["stats"]["loss"][0]
    ctl_loss = k(c, "key", "heartbeat", "video_loss_per_min")
    g = json.load(open(os.path.join(HERE, "guide_read_after.json")))
    out["control"] = {"host_cpu": cpu, "rendered_fps": fps, "loss_per_min": ctl_loss, "baseline_loss_per_s": round(base, 4),
                      "underruns": k(c, "key", "heartbeat", "audio_underruns"), "comparable": comp}
    for i, name in enumerate(("CONC paced r1", "CONC paced r2"), 1):
        s = S[name]
        hb, ep = s["key"]["heartbeat"], s["key"]["epg"]
        rd = os.path.dirname(os.path.join(HERE, concs[i - 1], "summary.json"))
        t0, t1 = s["window"]["from"], s["window"]["to"]
        grabs = [json.loads(l) for l in open(os.path.join(rd, "epg.jsonl"))]
        grabs = [x for x in grabs if x.get("kind") == "grab" and t0 <= x["start_utc"] and x["end_utc"] <= t1]
        per = Counter(x["channel"] for x in grabs if x.get("ok"))
        a = al[f"E1-CONC/run{i}"]["aligned"]["loss"]
        m02 = statistics.mean([x for x in a[:3] if x is not None])
        x = {"loss_per_min": hb["video_loss_per_min"], "rendered_fps": hb["rendered_fps"], "resyncs": hb["stream_resyncs"],
             "underruns": hb["audio_underruns"], "aligned_loss_0_10": a,
             "aligned_busiest_0_10": al[f"E1-CONC/run{i}"]["aligned"].get("busiest"), "loss_0_2_mean": round(m02, 3),
             "grabs_ok_failed_median": [ep["grabs_ok"], ep["grabs_failed"], ep["grab_s_median"]],
             "refreshes_per_channel": {ch: per.get(ch, 0) for ch in CH6},
             "companion_cpu": k(s, "host", "host", "procs.companion.cpu_pct", "mean"),
             "companion_pss_end_mb": t[name]["companion_mem"]["pss_last_mb"], "epg_cost": t[name]["epg_cost"],
             "host_cpu": k(s, "host", "host", "cpu.mean_pct", "mean")}
        x["a"] = x["loss_per_min"] <= 100 and x["loss_per_min"] <= 3 * ctl_loss
        x["b"] = x["rendered_fps"] >= 59.5 and x["resyncs"] <= 10
        x["c"] = m02 <= 3 * base
        x["d"] = ep["grabs_failed"] == 0 and all(per.get(ch, 0) >= 20 for ch in CH6) and ep["grab_s_median"] <= 11.8
        out[name] = x
    out["e_guide"] = {"channels": g["channels_serving"], "programmes": g["programmes_total"],
                      "holds": g["channels_serving"] == 6 and 305 <= g["programmes_total"] <= 337}
    # reported: loss vs cycle speed across today (S6A) / 1,500 (this task) / 4,000 (S7)
    rows = []
    for lab in ("S6A CONC (index, today's grab)", "CONC paced r1", "CONC paced r2", "S7 CONC 4000 r1", "S7 CONC 4000 r2"):
        s2 = S[lab]
        ep, hb2 = s2["key"]["epg"], s2["key"]["heartbeat"]
        rows.append(f"| {lab} | {hb2['video_loss_per_min']} | {hb2['rendered_fps']} | {hb2['stream_resyncs']} | "
                    f"{ep['grabs_ok']} | {round(ep['grabs_ok'] / 6, 1)} | {ep['grab_s_median']} |")
    open(os.path.join(HERE, "loss_vs_cycle.md"), "w").write(
        "| CONC run (delay) | loss/min | rendered fps | resyncs | grabs ok | refreshes per channel (mean) | median grab s |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n" + "\n".join(rows) + "\n")
    ok = all(out[n][cl] for n in ("CONC paced r1", "CONC paced r2") for cl in "abcd") and out["e_guide"]["holds"]
    out["comparability"] = comp
    out["verdict"] = "INCONCLUSIVE" if not comp else ("ACCEPTED" if ok else "REJECTED")
    json.dump(out, open(os.path.join(HERE, "e3_s7b_verdict.json"), "w"), indent=1, default=str)
    print(json.dumps({kk: v for kk, v in out.items() if kk != "validity"}, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
