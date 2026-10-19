#!/usr/bin/env python3
"""CL-B6: take the onn readings at the pre-registered moments, following the suite's console log: before run 1 (at
start), 150 s into run 1's window, before run 2 (at its idle gap, after its restart), 150 s into run 2's window."""
import datetime, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
LOG, OUT = HERE / "runs_console.log", HERE / "onn_reads.jsonl"
def read(label):
    r = subprocess.run([sys.executable, str(HERE / "cl_b6_onn_read.py"), label], capture_output=True, text=True, timeout=90)
    with OUT.open("a") as f:
        f.write(r.stdout if r.stdout.strip() else '{"label": "%s", "error": "no output"}\n' % label)
def utc(s):
    return datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp()
read("before_run1")
seen_windows = seen_gaps = 0
while True:
    text = LOG.read_text() if LOG.exists() else ""
    lines = text.splitlines()
    gaps = [l for l in lines if "idle gap" in l]
    wins = [l for l in lines if ": window " in l]
    if len(gaps) >= 2 and seen_gaps < 2:
        seen_gaps = 2
        read("before_run2")
    if len(wins) > seen_windows:
        seen_windows += 1
        start = utc(wins[-1].split(": window ")[1])
        time.sleep(max(0, start + 150 - time.time()))
        read(f"run{seen_windows}_150s")
    if "suite done" in text or "rc=" in text or seen_windows >= 2:
        break
    time.sleep(2)
