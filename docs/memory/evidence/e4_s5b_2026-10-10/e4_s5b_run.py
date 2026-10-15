#!/usr/bin/env python3
"""E4-S5B -- the run, as pre-registered (e4_s5b_preregistration.txt §1-§3):

1. live session 1: tools/e1_suite.py E1-SNES-STREAM x1, no flag, --window 4500 (75 min) -> runs_bench/; when its window
   opens, e4_s5b_bench.py --per-arm 24 beside it (48 interleaved 60-s sessions, ~52 min) -> bench/bench.jsonl;
2. if arm B holds < 3 bad-probe sessions: live session 2 (the same) with the bench's next 24 per arm (--start-index 48);
3. E1-PS1-STREAM x1 at 20 min WITH PRIVYHUB_SNES_CAPTURE_FIX=output_rate (the runner's e3_flag.conf) -> runs_ps1/.
Every step logs to run_console.log. The flag lives only in the bench process's environment (arm B) and in the PS1
run's drop-in; it is absent at every teardown (the runner's own checks)."""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
SUITE = os.path.join(REPO, "tools/e1_suite.py")
PRE = os.path.join(HERE, "e4_s5b_preregistration.txt")
BENCH = os.path.join(HERE, "e4_s5b_bench.py")
FLAG = "PRIVYHUB_SNES_CAPTURE_FIX=output_rate"


def log(*a):
    line = f"[e4s5b {time.strftime('%H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(os.path.join(HERE, "run_console.log"), "a") as fh:
        fh.write(line + "\n")


def suite(out, plan, window):
    return subprocess.Popen([sys.executable, SUITE, "run", "--out", out, "--prereg", PRE, "--e2", "--window", str(window),
                             "--gap", "120", "--plan", plan],
                            stdout=open(os.path.join(HERE, os.path.basename(out) + "_console.log"), "a"),
                            stderr=subprocess.STDOUT, cwd=REPO)


def windows_opened(out):
    try:
        return sum(1 for l in open(os.path.join(out, "suite.log")) if ": window " in l)
    except OSError:
        return 0


def live_with_bench(out, start_index):
    before = windows_opened(out)
    p = suite(out, "E1-SNES-STREAM:1:120", 4500)
    while p.poll() is None and windows_opened(out) == before:
        time.sleep(5)
    if p.poll() is not None:
        log("the live session ended before its window opened; no bench")
        return False
    log(f"live window open; bench --per-arm 24 --start-index {start_index}")
    b = subprocess.run([sys.executable, BENCH, os.path.join(HERE, "bench"), "--per-arm", "24", "--start-index",
                        str(start_index)], stdout=open(os.path.join(HERE, "bench_console.log"), "a"),
                       stderr=subprocess.STDOUT, cwd=REPO)
    log(f"bench exit {b.returncode}; waiting for the live session's window and teardown")
    p.wait()
    log("live session done")
    return b.returncode == 0


def bad_in_b():
    n = 0
    for l in open(os.path.join(HERE, "bench", "bench.jsonl")):
        r = json.loads(l)
        if r.get("event") == "session" and r.get("arm") == "B" and r.get("input_tbr") not in (None, "60"):
            n += 1
    return n


def main():
    log("start")
    ok = live_with_bench(os.path.join(HERE, "runs_bench"), 0)
    nb = bad_in_b() if os.path.exists(os.path.join(HERE, "bench", "bench.jsonl")) else 0
    log(f"after 24 per arm: arm B bad probes {nb}")
    if ok and nb < 3:
        log("fewer than 3 bad probes in B: the extension (live session 2, 24 more per arm)")
        live_with_bench(os.path.join(HERE, "runs_bench"), 48)
        log(f"after 48 per arm: arm B bad probes {bad_in_b()}")
    log("PS1-STREAM x1 with the flag")
    suite(os.path.join(HERE, "runs_ps1"), f"E1-PS1-STREAM:1:120:{FLAG}", 1200).wait()
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
