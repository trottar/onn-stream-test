#!/usr/bin/env python3
"""E4-S5C -- the run, as pre-registered (e4_s5c_preregistration.txt §1): E4-S5B's driver (e4_s5b_run.py) without the
PS1 run, the extension rule widened to either arm.

1. live session 1: tools/e1_suite.py E1-SNES-STREAM x1, no flag, --window 4500 (75 min) -> runs_bench/; when its window
   opens, e4_s5c_bench.py --per-arm 24 beside it (48 interleaved 60-s sessions) -> bench/bench.jsonl;
2. if EITHER arm holds < 3 bad-probe sessions: live session 2 (the same) with the bench's next 24 per arm
   (--start-index 48).
Every step logs to run_console.log. The flag lives only in the bench process's environment (arm B) at build time; the
companion runs with no flag (the runner's own flags_absent checks)."""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
SUITE = os.path.join(REPO, "tools/e1_suite.py")
PRE = os.path.join(HERE, "e4_s5c_preregistration.txt")
BENCH = os.path.join(HERE, "e4_s5c_bench.py")


def log(*a):
    line = f"[e4s5c {time.strftime('%H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
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


def bad(arm):
    n = 0
    for l in open(os.path.join(HERE, "bench", "bench.jsonl")):
        r = json.loads(l)
        if r.get("event") == "session" and r.get("arm") == arm and r.get("input_tbr") not in (None, "60"):
            n += 1
    return n


def main():
    log("start")
    ok = live_with_bench(os.path.join(HERE, "runs_bench"), 0)
    have = os.path.exists(os.path.join(HERE, "bench", "bench.jsonl"))
    na, nb = (bad("A"), bad("B")) if have else (0, 0)
    log(f"after 24 per arm: bad probes A {na}, B {nb}")
    if ok and (na < 3 or nb < 3):
        log("an arm holds fewer than 3 bad probes: the extension (live session 2, 24 more per arm)")
        live_with_bench(os.path.join(HERE, "runs_bench"), 48)
        log(f"after 48 per arm: bad probes A {bad('A')}, B {bad('B')}")
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
