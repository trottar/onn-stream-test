#!/usr/bin/env python3
"""BENCH-R1 (copied from g8_s5_suite_call.py; only the pre-registration name changed): one E1-PS1-STREAM run with its per-run drop-in, through tools/e1_suite.py's own run_suite (unedited).

Why a wrapper: the suite's CLI --plan splits on "," (plan items) and "+" (drop-in KEY=VALs), and G8-P1's flag value
carries both (`delay-50+loss-1@post-fec,seed=1`). So the plan row is built here as the CLI would build it --
["E1-PS1-STREAM", 1, <gap>, [KEY=VAL, ...]] -- and handed to run_suite. The suite's own pre-registration rule is kept:
the pre-registration must match its .sha256, or nothing runs.

    g8_s5_suite_call.py <out_dir> <window_s> <gap_s> KEY=VAL [KEY=VAL ...]
"""
import hashlib
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PRE = HERE / "bench_r1_preregistration.txt"


def main(argv):
    out, window, gap, kvs = Path(argv[0]), int(argv[1]), int(argv[2]), argv[3:]
    want = PRE.with_suffix(".sha256").read_text().split()[0] if PRE.with_suffix(".sha256").exists() else None
    if hashlib.sha256(PRE.read_bytes()).hexdigest() != want:
        print("refusing: the pre-registration does not match its hash")
        return 2
    if not kvs or not all(kv.startswith("PRIVYHUB_") and "=" in kv for kv in kvs):
        print("refusing: the drop-in must be PRIVYHUB_KEY=VAL entries", kvs)
        return 2
    spec = importlib.util.spec_from_file_location("e1_suite", REPO / "tools/e1_suite.py")
    e1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e1)
    e1.run_suite(out, None, 1, window, gap, [["E1-PS1-STREAM", 1, gap, list(kvs)]], True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
