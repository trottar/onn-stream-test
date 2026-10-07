#!/usr/bin/env python3
"""E3-S6 -- the two verdicts as pre-registered (e3_s6_preregistration.txt). Read-only.
-> e3_s6_table.md/.json, aligned_ctl/e2_conc.md (e2_analysis.py's CONC section, unchanged, baseline = the control),
   aligned_e2/e2_conc.md (baseline = E2's PS1-STREAM, reported), e3_s6_verdict.json"""
import importlib.util
import json
import os
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
E2R = os.path.join(REPO, "docs/memory/evidence/e2_s1_2026-10-05/runs")
R = os.path.join(HERE, "runs")


def load_e2():
    spec = importlib.util.spec_from_file_location("e2a", os.path.join(REPO, "docs/memory/evidence/e2_s1_2026-10-05/e2_analysis.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def aligned(name, baseline_dir):
    view = os.path.join(HERE, name)
    os.makedirs(view, exist_ok=True)
    for link, target in (("E1-CONC", os.path.join(R, "E1-CONC_flag")), ("E1-PS1-STREAM", baseline_dir)):
        p = os.path.join(view, link)
        if os.path.islink(p):
            os.unlink(p)
        os.symlink(os.path.relpath(target, view), p)
    m = load_e2()
    m.R, m.HERE = view, view
    out = {}
    m.conc(out)
    return out["conc"]


def k(s, *p):
    for x in p:
        s = (s or {}).get(x) if isinstance(s, dict) else None
    return s


def main():
    cols = [("control", f"{R}/E1-PS1-STREAM/run1"), ("META r1", f"{R}/E1-META_flag/run1"), ("META r2", f"{R}/E1-META_flag/run2"),
            ("CONC r1", f"{R}/E1-CONC_flag/run1"), ("CONC r2", f"{R}/E1-CONC_flag/run2"),
            ("E2 PS1-STREAM", f"{E2R}/E1-PS1-STREAM/run1"), ("E2 META", f"{E2R}/E1-META/run1"),
            ("E2 CONC r1", f"{E2R}/E1-CONC/run1"), ("E2 CONC r2", f"{E2R}/E1-CONC/run2")]
    subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_table.py"), os.path.join(HERE, "e3_s6_table.md")]
                   + [f"{a}={b}" for a, b in cols], check=True, stdout=subprocess.DEVNULL)
    t = json.load(open(os.path.join(HERE, "e3_s6_table.json")))
    S = {a: json.load(open(os.path.join(b, "summary.json"))) for a, b in cols}
    g = json.load(open(os.path.join(HERE, "guide_read_after.json")))
    out = {"memory": {}, "stream": {}}
    for r in ("META r1", "META r2"):
        m = t[r]["companion_mem"]
        e = S[r]["key"]["epg"]
        cpu = k(S[r], "host", "host", "cpu.mean_pct", "mean")
        out["memory"][r] = {"pss_end_mb": m["pss_last_mb"], "last15_pct": m["last15_growth_pct"],
                            "a": m["pss_last_mb"] <= 60 and not m["keeps_growing"],
                            "grabs": [e["grabs_ok"], e["grabs_failed"], e["grab_s_median"]],
                            "b": e["grabs_failed"] == 0 and e["grabs_ok"] >= 205 and e["grab_s_median"] <= 6.8,
                            "host_cpu": cpu, "d": cpu <= 11.8,
                            "anon_first_last": [m["anon_first_mb"], m["anon_last_mb"]], "pss_max_mb": m["pss_max_mb"],
                            "companion_cpu": k(S[r], "host", "host", "procs.companion.cpu_pct", "mean")}
    out["memory"]["c_guide"] = {"channels_serving": g["channels_serving"], "programmes_total": g["programmes_total"],
                                "before": 343, "candidates_identical_in_smoke": True,
                                "holds": g["channels_serving"] == 6 and 326 <= g["programmes_total"] <= 360}
    mok = all(out["memory"][r][c] for r in ("META r1", "META r2") for c in "abd") and out["memory"]["c_guide"]["holds"]
    out["memory"]["verdict"] = "ACCEPTED" if mok else "REJECTED"
    ctl, e2 = S["control"], S["E2 PS1-STREAM"]
    comp = (abs(k(ctl, "host", "host", "cpu.mean_pct", "mean") - k(e2, "host", "host", "cpu.mean_pct", "mean")) <= 2
            and abs(k(ctl, "key", "heartbeat", "rendered_fps") - k(e2, "key", "heartbeat", "rendered_fps")) <= 0.5)
    al = aligned("aligned_ctl", os.path.join(R, "E1-PS1-STREAM"))
    al_e2 = aligned("aligned_e2", os.path.join(E2R, "E1-PS1-STREAM"))
    base_loss = al["baseline"]["stats"]["loss"][0]
    ctl_loss = k(ctl, "key", "heartbeat", "video_loss_per_min")
    for r, key in (("CONC r1", "E1-CONC/run1"), ("CONC r2", "E1-CONC/run2")):
        hb = S[r]["key"]["heartbeat"]
        a = al[key]["aligned"]["loss"]
        m02 = statistics.mean([x for x in a[:3] if x is not None])
        out["stream"][r] = {"loss_per_min": hb["video_loss_per_min"], "e": hb["video_loss_per_min"] <= 100 and hb["video_loss_per_min"] <= 3 * ctl_loss,
                            "rendered_fps": hb["rendered_fps"], "resyncs": hb["stream_resyncs"],
                            "f": hb["rendered_fps"] >= 59.5 and hb["stream_resyncs"] <= 10,
                            "aligned_loss_0_10": a, "aligned_busiest_0_10": al[key]["aligned"].get("busiest"),
                            "loss_0_2_mean": round(m02, 3), "g_limit": round(3 * base_loss, 3), "g": m02 <= 3 * base_loss,
                            "underruns": hb["audio_underruns"],
                            "grabs": [S[r]["key"]["epg"]["grabs_ok"], S[r]["key"]["epg"]["grabs_failed"], S[r]["key"]["epg"]["grab_s_median"]],
                            "companion_pss_end_mb": t[r]["companion_mem"]["pss_last_mb"]}
    out["stream"]["control"] = {"loss_per_min": ctl_loss, "rendered_fps": k(ctl, "key", "heartbeat", "rendered_fps"),
                                "host_cpu": k(ctl, "host", "host", "cpu.mean_pct", "mean"), "baseline_loss_per_s": round(base_loss, 4)}
    out["stream"]["comparability"] = comp
    sok = all(out["stream"][r][c] for r in ("CONC r1", "CONC r2") for c in "efg")
    out["stream"]["verdict"] = "INCONCLUSIVE" if not comp else ("ACCEPTED" if sok else "REJECTED")
    out["aligned_vs_e2_baseline"] = {r: v.get("aligned", {}).get("loss") for r, v in al_e2.items() if r != "baseline"}
    json.dump(out, open(os.path.join(HERE, "e3_s6_verdict.json"), "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
