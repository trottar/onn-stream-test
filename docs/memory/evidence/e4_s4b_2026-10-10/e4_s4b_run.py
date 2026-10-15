#!/usr/bin/env python3
"""E4-S4B -- grab deferral on a clean link, run as pre-registered (e4_s4b_preregistration.txt §1-§2):

1. THE CLEAN-LINK GATE: E1-PS1-STREAM x1, no flag, 20 min (runs/E1-PS1-STREAM/run<n>). Clean = video loss/min < 10 AND
   rendered >= 59.5 AND resyncs <= 10. Not clean -> idle 30 min -> the next control; at most 4 controls. None clean ->
   gate.json INCONCLUSIVE (link), no flagged run, stop.
2. After the first clean control (THE control): the pre-run guide read (tools/e1_suite.py guide_read, 60 s after the
   control's teardown) -> pre_guide.json; then ONE suite invocation: E1-CONC x2 with PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1
   (unconstrained; runs/E1-CONC_flag/run1, run2), E1-CONC x1 with the flag at CPUQuota=150% (runs/E1-CONC_flag_cpu150/
   run1). The flag lives in the runner's e3_flag.conf, the constraint in e4_constraint.conf, each for its runs only.
   Each CONC teardown waits for the deferred queue to drain and records it (the runner's own code).
Logs to run_console.log; gate.json records every control attempt."""
import importlib.util
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
SUITE = os.path.join(REPO, "tools/e1_suite.py")
PRE = os.path.join(HERE, "e4_s4b_preregistration.txt")
OUT = os.path.join(HERE, "runs")
FLAG = "PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1"
MAX_CONTROLS, IDLE_S = 4, 1800


def log(*a):
    line = f"[e4s4b {time.strftime('%H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(os.path.join(HERE, "run_console.log"), "a") as fh:
        fh.write(line + "\n")


def suite(plan):
    with open(os.path.join(HERE, "runs_console.log"), "a") as fh:
        return subprocess.run([sys.executable, SUITE, "run", "--out", OUT, "--prereg", PRE, "--e2", "--window", "1200",
                               "--gap", "120", "--plan", plan], stdout=fh, stderr=subprocess.STDOUT, cwd=REPO).returncode


def k(s, *p):
    for x in p:
        s = s.get(x) if isinstance(s, dict) else None
    return s


def clean(s):
    loss, rend, res = (k(s, "key", "heartbeat", x) for x in ("video_loss_per_min", "rendered_fps", "stream_resyncs"))
    ok = (s or {}).get("status") == "OK" and None not in (loss, rend, res) and loss < 10 and rend >= 59.5 and res <= 10
    return ok, {"status": (s or {}).get("status"), "video_loss_per_min": loss, "rendered_fps": rend, "resyncs": res}


def main():
    gate_p = os.path.join(HERE, "gate.json")
    gate = json.load(open(gate_p)) if os.path.exists(gate_p) else {"attempts": [], "clean_control": None}
    log("start; controls so far", len(gate["attempts"]))
    while gate["clean_control"] is None and len(gate["attempts"]) < MAX_CONTROLS:
        if gate["attempts"]:
            log(f"control {len(gate['attempts'])} not clean: idle {IDLE_S} s")
            time.sleep(IDLE_S)
        n = len(gate["attempts"]) + 1
        log(f"control {n}")
        suite("E1-PS1-STREAM:1:120")
        sp = os.path.join(OUT, "E1-PS1-STREAM", f"run{n}", "summary.json")
        s = json.load(open(sp)) if os.path.exists(sp) else None
        ok, fig = clean(s)
        gate["attempts"].append({"n": n, "summary": os.path.relpath(sp, HERE), "clean": ok, **fig,
                                 "window": (s or {}).get("window")})
        if ok:
            gate["clean_control"] = n
        json.dump(gate, open(gate_p, "w"), indent=1)
        log(f"control {n}: {'CLEAN' if ok else 'not clean'} {fig}")
    if gate["clean_control"] is None:
        gate["verdict"] = "INCONCLUSIVE (link): no clean control in four; no flagged run"
        json.dump(gate, open(gate_p, "w"), indent=1)
        log(gate["verdict"])
        return 0
    if not os.path.exists(os.path.join(HERE, "pre_guide.json")):
        time.sleep(60)
        spec = importlib.util.spec_from_file_location("e1_suite", SUITE)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        g = m.guide_read()
        g["at_utc"] = m.utc()
        json.dump(g, open(os.path.join(HERE, "pre_guide.json"), "w"), indent=1)
        log("pre-run guide read", g)
    log("the flagged runs: E1-CONC x2 with the flag, E1-CONC x1 with the flag at CPUQuota=150%")
    suite(f"E1-CONC:2:120:{FLAG},E1-CONC:1:120:{FLAG}:CPUQuota=150%")
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
