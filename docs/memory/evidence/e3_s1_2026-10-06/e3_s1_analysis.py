#!/usr/bin/env python3
"""E3-S1 -- the analysis as pre-registered (e3_s1_preregistration.txt). Read-only on the runs.

    e3_s1_analysis.py   -> e3_s1_table.md/.json (tools/e3_table.py), aligned_ctl/e2_conc.md (baseline = tonight's
                           control), aligned_e2/e2_conc.md (baseline = E2's E1-PS1-STREAM), e3_s1_verdict.json

The aligned frame is e2_analysis.py's conc() unchanged, pointed at a view directory whose E1-CONC is
runs/E1-CONC_flag and whose E1-PS1-STREAM is the chosen baseline (symlinks).
"""
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
RUNS = os.path.join(HERE, "runs")
E2R = os.path.join(REPO, "docs/memory/evidence/e2_s1_2026-10-05/runs")


def load_e2():
    spec = importlib.util.spec_from_file_location("e2a", os.path.join(REPO, "docs/memory/evidence/e2_s1_2026-10-05/e2_analysis.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def aligned(name, baseline_dir):
    view = os.path.join(HERE, name)
    os.makedirs(view, exist_ok=True)
    for link, target in (("E1-CONC", os.path.join(RUNS, "E1-CONC_flag")), ("E1-PS1-STREAM", baseline_dir)):
        p = os.path.join(view, link)
        if os.path.islink(p):
            os.unlink(p)
        os.symlink(os.path.relpath(target, view), p)
    m = load_e2()
    m.R, m.HERE = view, view
    out = {}
    m.conc(out)
    return out["conc"]


def key(s, *path):
    x = s
    for k in path:
        x = (x or {}).get(k) if isinstance(x, dict) else None
    return x


def main():
    sj = lambda *p: json.load(open(os.path.join(RUNS, *p, "summary.json")))
    ctl = sj("E1-PS1-STREAM", "run1")
    c1, c2 = sj("E1-CONC_flag", "run1"), sj("E1-CONC_flag", "run2")
    meta = sj("E1-META_flag", "run1")
    e2 = lambda w, r: json.load(open(os.path.join(E2R, w, f"run{r}", "summary.json")))
    subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_table.py"), os.path.join(HERE, "e3_s1_table.md"),
                    f"control PS1-STREAM={RUNS}/E1-PS1-STREAM/run1", f"CONC r1 (flag)={RUNS}/E1-CONC_flag/run1",
                    f"CONC r2 (flag)={RUNS}/E1-CONC_flag/run2", f"META (flag)={RUNS}/E1-META_flag/run1",
                    f"E2 PS1-STREAM={E2R}/E1-PS1-STREAM/run1", f"E2 CONC r1={E2R}/E1-CONC/run1",
                    f"E2 CONC r2={E2R}/E1-CONC/run2", f"E2 META={E2R}/E1-META/run1"],
                   check=True, stdout=subprocess.DEVNULL)
    hb = lambda s, k: key(s, "key", "heartbeat", k)
    ep = lambda s, k: key(s, "key", "epg", k)
    ctl_loss = hb(ctl, "video_loss_per_min")
    v = {}
    v["a_loss"] = {"conc_r1": hb(c1, "video_loss_per_min"), "conc_r2": hb(c2, "video_loss_per_min"),
                   "control": ctl_loss, "limit": min(100.0, 3 * ctl_loss) if ctl_loss is not None else 100.0}
    v["a_loss"]["holds"] = all(x is not None and x <= 100 and x <= 3 * ctl_loss for x in (v["a_loss"]["conc_r1"], v["a_loss"]["conc_r2"]))
    v["b_fps"] = {"conc_r1": hb(c1, "rendered_fps"), "conc_r2": hb(c2, "rendered_fps")}
    v["b_fps"]["holds"] = all(x is not None and x >= 59.5 for x in (v["b_fps"]["conc_r1"], v["b_fps"]["conc_r2"]))
    v["c_resyncs"] = {"conc_r1": hb(c1, "stream_resyncs"), "conc_r2": hb(c2, "stream_resyncs")}
    v["c_resyncs"]["holds"] = all(x is not None and x <= 10 for x in (v["c_resyncs"]["conc_r1"], v["c_resyncs"]["conc_r2"]))
    g = {}
    for nm, s, need_ok, med in (("meta", meta, 205, 7.8), ("conc_r1", c1, 187, 8.8), ("conc_r2", c2, 187, 8.8)):
        g[nm] = {"ok": ep(s, "grabs_ok"), "failed": ep(s, "grabs_failed"), "median_s": ep(s, "grab_s_median"),
                 "need_ok": need_ok, "max_median_s": med}
        g[nm]["holds"] = (g[nm]["failed"] == 0 and (g[nm]["ok"] or 0) >= need_ok
                          and g[nm]["median_s"] is not None and g[nm]["median_s"] <= med)
    v["d_grabs"] = dict(g, holds=all(x["holds"] for x in g.values()))
    e2c = e2("E1-PS1-STREAM", 1)
    hc = lambda s: key(s, "host", "host", "cpu.mean_pct", "mean")
    v["e_comparable"] = {"control_cpu": hc(ctl), "e2_cpu": hc(e2c), "control_fps": hb(ctl, "rendered_fps"),
                         "e2_fps": hb(e2c, "rendered_fps")}
    v["e_comparable"]["holds"] = (abs(hc(ctl) - hc(e2c)) <= 2.0
                                  and abs(hb(ctl, "rendered_fps") - hb(e2c, "rendered_fps")) <= 0.5)
    if not v["e_comparable"]["holds"]:
        verdict = "INCONCLUSIVE"
    elif all(v[k]["holds"] for k in ("a_loss", "b_fps", "c_resyncs", "d_grabs")):
        verdict = "ACCEPTED"
    else:
        verdict = "REJECTED"
    v["verdict"] = verdict
    v["reported"] = {nm: {"busiest_core_per_second_p95": key(s, "host", "host", "cpu.max_pct", "p95"),
                          "audio_underruns": hb(s, "audio_underruns"),
                          "max_output_gap_ms": key(s, "key", "telemetry", "output_gap_ms_max"),
                          "decisions": key(s, "key", "decisions")}
                     for nm, s in (("control", ctl), ("conc_r1", c1), ("conc_r2", c2), ("meta", meta))}
    # the grabber's policy / nice as sampled: the epg category's threads (policy column) in the flagged runs
    pol = {}
    for nm in ("E1-CONC_flag/run1", "E1-CONC_flag/run2", "E1-META_flag/run1"):
        seen = {}
        for line in open(os.path.join(RUNS, nm, "threads.jsonl")):
            r = json.loads(line)
            for pid, tid, cpu, p, sc in (r.get("threads") or {}).get("epg") or []:
                seen[p] = seen.get(p, 0) + 1
        pol[nm] = seen
    v["reported"]["epg_thread_policy_counts"] = pol
    v["aligned_ctl"] = aligned("aligned_ctl", os.path.join(RUNS, "E1-PS1-STREAM"))
    v["aligned_e2"] = aligned("aligned_e2", os.path.join(E2R, "E1-PS1-STREAM"))
    json.dump(v, open(os.path.join(HERE, "e3_s1_verdict.json"), "w"), indent=1, default=str)
    print(json.dumps({k: (x.get("holds") if isinstance(x, dict) else x) for k, x in v.items()
                      if not k.startswith("aligned") and k != "reported"}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
