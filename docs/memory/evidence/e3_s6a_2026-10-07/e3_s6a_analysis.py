#!/usr/bin/env python3
"""E3-S6A -- the adoption's bar as pre-registered (e3_s6a_preregistration.txt). Read-only.
-> e3_s6a_table.md/.json (tools/e3_table.py beside E3-S6's runs and E2's), aligned/e2_conc.md (e2_analysis.py's CONC
   section, unchanged, pointed at this run's CONC with this run's PS1-STREAM as baseline; reported), e3_s6a_verdict.json"""
import importlib.util
import json
import os
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
E2R = os.path.join(REPO, "docs/memory/evidence/e2_s1_2026-10-05/runs")
S6R = os.path.join(REPO, "docs/memory/evidence/e3_s6_2026-10-07/runs")
R = os.path.join(HERE, "runs")


def k(s, *p):
    for x in p:
        s = (s or {}).get(x) if isinstance(s, dict) else None
    return s


def aligned():
    spec = importlib.util.spec_from_file_location("e2a", os.path.join(REPO, "docs/memory/evidence/e2_s1_2026-10-05/e2_analysis.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    view = os.path.join(HERE, "aligned")
    os.makedirs(view, exist_ok=True)
    for link, target in (("E1-CONC", os.path.join(R, "E1-CONC")), ("E1-PS1-STREAM", os.path.join(R, "E1-PS1-STREAM"))):
        p = os.path.join(view, link)
        if os.path.islink(p):
            os.unlink(p)
        os.symlink(os.path.relpath(target, view), p)
    m.R, m.HERE = view, view
    out = {}
    m.conc(out)
    return out["conc"]


def main():
    cols = [("PS1-STREAM", f"{R}/E1-PS1-STREAM/run1"), ("META", f"{R}/E1-META/run1"), ("CONC", f"{R}/E1-CONC/run1"),
            ("S6 control", f"{S6R}/E1-PS1-STREAM/run1"), ("S6 META r1", f"{S6R}/E1-META_flag/run1"),
            ("S6 CONC r1", f"{S6R}/E1-CONC_flag/run1"), ("S6 CONC r2", f"{S6R}/E1-CONC_flag/run2"),
            ("E2 PS1-STREAM", f"{E2R}/E1-PS1-STREAM/run1"), ("E2 META", f"{E2R}/E1-META/run1"),
            ("E2 CONC r1", f"{E2R}/E1-CONC/run1"), ("E2 CONC r2", f"{E2R}/E1-CONC/run2")]
    subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_table.py"), os.path.join(HERE, "e3_s6a_table.md")]
                   + [f"{a}={b}" for a, b in cols], check=True, stdout=subprocess.DEVNULL)
    t = json.load(open(os.path.join(HERE, "e3_s6a_table.json")))
    S = {a: json.load(open(os.path.join(b, "summary.json"))) for a, b in cols}
    g = json.load(open(os.path.join(HERE, "guide_read_after.json")))
    out = {}
    m, e = t["META"]["companion_mem"], S["META"]["key"]["epg"]
    cpu = k(S["META"], "host", "host", "cpu.mean_pct", "mean")
    out["META"] = {"pss_end_mb": m["pss_last_mb"], "last15_pct": m["last15_growth_pct"],
                   "m1": m["pss_last_mb"] <= 60 and m["last15_growth_pct"] is not None and m["last15_growth_pct"] <= 5,
                   "grabs": [e["grabs_ok"], e["grabs_failed"], e["grab_s_median"]],
                   "m2": e["grabs_failed"] == 0 and e["grabs_ok"] >= 205 and e["grab_s_median"] <= 6.8,
                   "guide": [g["channels_serving"], g["programmes_total"]],
                   "m3": g["channels_serving"] == 6 and 327 <= g["programmes_total"] <= 361,
                   "host_cpu": cpu, "m4": cpu <= 11.8,
                   "companion_cpu": k(S["META"], "host", "host", "procs.companion.cpu_pct", "mean"),
                   "pss_max_mb": m["pss_max_mb"]}
    c, ec = t["CONC"]["companion_mem"], S["CONC"]["key"]["epg"]
    hb = S["CONC"]["key"]["heartbeat"]
    al = aligned()
    a = al["E1-CONC/run1"]["aligned"]["loss"]
    out["CONC"] = {"pss_end_mb": c["pss_last_mb"], "c1": c["pss_last_mb"] <= 60,
                   "grabs": [ec["grabs_ok"], ec["grabs_failed"], ec["grab_s_median"]], "c2": ec["grabs_failed"] == 0,
                   "reported": {"loss_per_min": hb["video_loss_per_min"], "rendered_fps": hb["rendered_fps"],
                                "resyncs": hb["stream_resyncs"], "underruns": hb["audio_underruns"],
                                "aligned_loss_0_10": a, "aligned_busiest_0_10": al["E1-CONC/run1"]["aligned"].get("busiest"),
                                "loss_0_2_mean": round(statistics.mean([x for x in a[:3] if x is not None]), 3),
                                "baseline_loss_per_s": round(al["baseline"]["stats"]["loss"][0], 4),
                                "companion_cpu": k(S["CONC"], "host", "host", "procs.companion.cpu_pct", "mean"),
                                "host_cpu": k(S["CONC"], "host", "host", "cpu.mean_pct", "mean")}}
    p = S["PS1-STREAM"]
    pc, pf = k(p, "host", "host", "cpu.mean_pct", "mean"), k(p, "key", "heartbeat", "rendered_fps")
    out["PS1-STREAM"] = {"host_cpu": pc, "rendered_fps": pf, "p1": abs(pc - 11.69) <= 2 and abs(pf - 59.81) <= 0.5,
                         "companion_cpu": k(p, "host", "host", "procs.companion.cpu_pct", "mean"),
                         "companion_pss_first_last_mb": [t["PS1-STREAM"]["companion_mem"]["pss_first_mb"],
                                                         t["PS1-STREAM"]["companion_mem"]["pss_last_mb"]],
                         "loss_per_min": k(p, "key", "heartbeat", "video_loss_per_min"),
                         "underruns": k(p, "key", "heartbeat", "audio_underruns")}
    fails = [f"{r}.{c}" for r, cl in (("META", "m1 m2 m3 m4"), ("CONC", "c1 c2"), ("PS1-STREAM", "p1"))
             for c in cl.split() if not out[r][c]]
    out["failing_clauses"] = fails
    out["verdict"] = "ADOPTION STANDS" if not fails else "ADOPTION REVERTED"
    json.dump(out, open(os.path.join(HERE, "e3_s6a_verdict.json"), "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
