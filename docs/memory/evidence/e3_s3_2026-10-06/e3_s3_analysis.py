#!/usr/bin/env python3
"""E3-S3 -- the bar as pre-registered (e3_s3_preregistration.txt). Read-only. -> e3_s3_table.md/.json, e3_s3_verdict.json"""
import collections
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
E2R = os.path.join(REPO, "docs/memory/evidence/e2_s1_2026-10-05/runs")
RUNS = os.path.join(HERE, "runs", "E1-META_flag")


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def main():
    subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_table.py"), os.path.join(HERE, "e3_s3_table.md"),
                    f"META r1 (flag)={RUNS}/run1", f"META r2 (flag)={RUNS}/run2", f"E2 META={E2R}/E1-META/run1"],
                   check=True, stdout=subprocess.DEVNULL)
    t = json.load(open(os.path.join(HERE, "e3_s3_table.json")))
    e2 = t["E2 META"]["epg_cost"]["cpu_s_per_grab_window_avg"]
    bar = round(0.7 * e2, 2)
    ch = jl(os.path.join(HERE, "children_cpu.jsonl")) if os.path.exists(os.path.join(HERE, "children_cpu.jsonl")) else []
    g = json.load(open(os.path.join(HERE, "guide_read_after.json")))
    out = {"e2_cpu_s_per_grab": e2, "bar_cpu_s_per_grab": bar}
    for r in ("run1", "run2"):
        s = json.load(open(os.path.join(RUNS, r, "summary.json")))
        w0, w1 = s["window"]["from"], s["window"]["to"]
        x = t[f"META {r[:1]}{r[-1]} (flag)".replace("r", "r", 1)] if False else t["META r%s (flag)" % r[-1]]
        grabs = [e for e in jl(os.path.join(RUNS, r, "epg.jsonl"))
                 if e["kind"] == "grab" and w0 <= e["start_utc"] and e["end_utc"] <= w1]
        per_ch = collections.Counter(e["channel"] for e in grabs if e["ok"])
        failed = sum(1 for e in grabs if not e["ok"])
        cw = [c for c in ch if w0[:19] <= c["at_utc"][:19] <= w1[:19] and "children_cpu_s" in c]
        same_pid = [c for c in cw if c["pid"] == cw[0]["pid"]] if cw else []
        exact = (round((same_pid[-1]["children_cpu_s"] - same_pid[0]["children_cpu_s"]) / max(1, len(grabs)), 2)
                 if len(same_pid) > 1 else None)
        cpu = x["epg_cost"]["cpu_s_per_grab_window_avg"]
        pk = x["epg_cost"]["peak_pss_mb_median"]
        out[r] = {"a_cpu_s_per_grab": cpu, "a": cpu <= bar, "b_peak_pss_mb_median": pk, "b": pk is not None and pk <= 660,
                  "c_failed": failed, "c_per_channel": dict(per_ch), "c": failed == 0 and len(per_ch) == 6 and min(per_ch.values()) >= 34,
                  "reported": {"grabs": len(grabs), "grab_s_median": s["key"]["epg"]["grab_s_median"],
                               "host_cpu": s["host"]["host"]["cpu.mean_pct"]["mean"],
                               "companion_pss_last_mb": x["companion_mem"].get("pss_last_mb"),
                               "exact_children_cpu_s_per_grab": exact,
                               "exact_samples": len(same_pid)}}
    out["d_guide"] = {"channels_serving": g["channels_serving"], "programmes_total": g["programmes_total"], "before": 342,
                      "holds": g["channels_serving"] == 6 and 325 <= g["programmes_total"] <= 359}
    ok = all(out[r][k] for r in ("run1", "run2") for k in "abc") and out["d_guide"]["holds"]
    out["verdict"] = "ACCEPTED" if ok else "REJECTED"
    json.dump(out, open(os.path.join(HERE, "e3_s3_verdict.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    sys.exit(main())
