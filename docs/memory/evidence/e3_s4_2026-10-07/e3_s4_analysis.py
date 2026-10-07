#!/usr/bin/env python3
"""E3-S4 -- the bar as pre-registered (e3_s4_preregistration.txt). Read-only.
-> e3_s4_table.md/.json (tools/e3_table.py: the two flagged runs beside E2's two bsnes runs), repeat/ (e1_suite.py's
   compare, unchanged, pointed at the flagged runs) and e3_s4_verdict.json"""
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
E2R = os.path.join(REPO, "docs/memory/evidence/e2_s1_2026-10-05/runs")
R = os.path.join(HERE, "runs")


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def k(s, *p):
    for x in p:
        s = (s or {}).get(x) if isinstance(s, dict) else None
    return s


def main():
    E2 = load("e2a", "docs/memory/evidence/e2_s1_2026-10-05/e2_analysis.py")
    SU = load("e1s", "tools/e1_suite.py")
    cols = [("snes9x r1", f"{R}/E1-SNES-STREAM_flag/run1"), ("snes9x r2", f"{R}/E1-SNES-STREAM_flag/run2"),
            ("E2 bsnes r1", f"{E2R}/E1-SNES-STREAM/run1"), ("E2 bsnes r2", f"{E2R}/E1-SNES-STREAM/run2")]
    subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_table.py"), os.path.join(HERE, "e3_s4_table.md")]
                   + [f"{a}={b}" for a, b in cols], check=True, stdout=subprocess.DEVNULL)
    t = json.load(open(os.path.join(HERE, "e3_s4_table.json")))
    rows = dict((n, f) for n, f in E2.TABLE)
    S = {a: json.load(open(os.path.join(b, "summary.json"))) for a, b in cols}
    # E1's repeatability on the flagged pair: e1_suite.compare, unchanged, on a view whose E1-SNES-STREAM is the flag dir
    view = os.path.join(HERE, "repeat")
    os.makedirs(view, exist_ok=True)
    link = os.path.join(view, "E1-SNES-STREAM")
    if os.path.islink(link):
        os.unlink(link)
    os.symlink(os.path.relpath(os.path.join(R, "E1-SNES-STREAM_flag"), view), link)
    rep = SU.compare(__import__("pathlib").Path(view))["E1-SNES-STREAM"]
    e2_dd = max(rows["encoder dup + drop per min"](S[a]) for a in ("E2 bsnes r1", "E2 bsnes r2"))
    out = {}
    for a in ("snes9x r1", "snes9x r2"):
        s = S[a]
        x = {"retroarch_cpu": k(s, "host", "host", "procs.retroarch.cpu_pct", "mean"),
             "host_cpu": k(s, "host", "host", "cpu.mean_pct", "mean"),
             "retroarch_fps": rows["RetroArch fps"](s), "capture_fps": rows["encoder capture fps"](s),
             "rendered_fps": rows["rendered fps (heartbeat)"](s), "dup_drop_per_min": rows["encoder dup + drop per min"](s),
             "retroarch_threads": t[a].get("retroarch_threads"),
             "psi_cpu": k(s, "host", "host", "psi_ms_per_s.cpu_some", "mean"),
             "socket_w": k(s, "host", "host", "gpu.socket_power_w", "mean"),
             "video_loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"),
             "underruns": k(s, "key", "heartbeat", "audio_underruns"),
             "report": k(s, "teardown", "report_fields")}
        x["c_retroarch_cpu"] = x["retroarch_cpu"] is not None and x["retroarch_cpu"] <= 150
        x["c_host_cpu"] = x["host_cpu"] <= 20
        x["c_fps"] = (x["retroarch_fps"] is not None and x["retroarch_fps"] >= 59.9 and x["capture_fps"] is not None
                      and abs(x["capture_fps"] - 60) <= 0.5 and x["rendered_fps"] >= 59.5)
        x["c_dup_drop"] = x["dup_drop_per_min"] is not None and x["dup_drop_per_min"] <= 0.2
        out[a] = x
    out["repeatable"] = {"verdict": rep["verdict"], "failed": rep.get("failed"), "rows": rep.get("rows")}
    out["e2_dup_drop_max"] = e2_dd
    ok = all(out[a][c] for a in ("snes9x r1", "snes9x r2") for c in ("c_retroarch_cpu", "c_host_cpu", "c_fps", "c_dup_drop")) \
        and rep["verdict"] == "REPEATABLE"
    out["verdict"] = "ACCEPTED" if ok else "REJECTED"
    json.dump(out, open(os.path.join(HERE, "e3_s4_verdict.json"), "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
