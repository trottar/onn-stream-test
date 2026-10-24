#!/usr/bin/env python3
"""G-A3: the confirmation window (from LINK-R1's link_r1_window.py, without its sampler or a drop-in). Runs one
E1-SNES-STREAM through the suite's own CLI (run --only E1-SNES-STREAM --runs 1 --window 600 --gap 120 --e2 --prereg
<this dir's>), reads the environ back every 15 s (the nine adopted lines expected throughout), and copies the run's five
logs over its span (BENCH-R3's driver's logs_copy, addresses masked). The reading is g_a3_read.py's.
    python3 -B g_a3_window.py
"""
import importlib.util
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE.parent
REPO = HERE.parents[3]
spec = importlib.util.spec_from_file_location("bench_r3_driver", EV / "bench_r3_2026-10-22/bench_r3_driver.py")
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)          # module level only defines (main() runs under __main__ alone)
E1 = D.E1
FLAG = "PRIVYHUB_LINK_REPORT=1"
OUT = HERE / "runs"
STOP = threading.Event()
ENV = {"reads": 0, "max_lines": 0, "nine_with_flag": 0, "lines_at_nine": None}


def log(*a):
    line = f"{D.utc()} " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(HERE / "window_console.txt", "a") as fh:
        fh.write(line + "\n")


def environ_watch():
    while not STOP.is_set():
        try:
            env = E1.environ_flags(E1.mainpid()) or []
        except Exception:       # noqa: BLE001 -- a read failure is a missed read, not fatal
            env = []
        ENV["reads"] += 1
        ENV["max_lines"] = max(ENV["max_lines"], len(env))
        if len(env) == 9 and FLAG in env and sorted(env) == E1.ADOPTED:
            ENV["nine_with_flag"] += 1
            ENV["lines_at_nine"] = ENV["lines_at_nine"] or sorted(env)
        STOP.wait(15)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pf = E1.preflight()
    log("preflight ok", pf.get("ok"), "environ", len(pf.get("environ") or []), "game", pf.get("game_active"))
    if not pf.get("ok"):
        log("refusing: the preflight is not ok")
        return 2
    t0 = time.time()
    th = threading.Thread(target=environ_watch, daemon=True)
    th.start()
    with open(OUT / "suite_console.log", "a") as fh:
        rc = subprocess.run([sys.executable, str(REPO / "tools/e1_suite.py"), "run", "--out", str(OUT), "--prereg",
                             str(HERE / "g_a3_preregistration.txt"), "--only", "E1-SNES-STREAM", "--runs", "1", "--window",
                             "600", "--gap", "120", "--e2"], stdout=fh, stderr=subprocess.STDOUT, cwd=str(REPO)).returncode
    t1 = time.time()
    STOP.set()
    log("the suite exited", rc)
    rd = D.latest_run(OUT / "E1-SNES-STREAM")
    s = D.load_json(rd / "summary.json") if rd else None
    f = D.figures(s, rd) if s else {}
    copied = D.logs_copy(t0, t1, OUT / "logs_run1")
    final = D.load_json(OUT / "final_state.json") or {}
    rec = {"t0": D.utc(t0), "t1": D.utc(t1), "suite_rc": rc, "run_dir": rd.name if rd else None, "environ_watch": ENV,
           "logs_copied": copied, "final_flags_absent": final.get("flags_absent"), "final_environ_lines": len(final.get("environ") or []),
           "figures": {k: v for k, v in f.items() if k not in ("report_fields", "pauses")},
           "post_check": json.loads(subprocess.run(
               [sys.executable, str(REPO / "tools/e3_state.py")], capture_output=True, text=True).stdout or "{}")}
    (HERE / "window_result.json").write_text(json.dumps(rec, indent=1) + "\n")
    log("done:", json.dumps({k: rec[k] for k in ("suite_rc", "run_dir", "environ_watch", "final_flags_absent", "final_environ_lines")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
