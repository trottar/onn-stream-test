#!/usr/bin/env python3
"""G4-P2 §2: what G4-S1's run 1 / run 2 files hold for gate 3. Read-only.

    PYTHONDONTWRITEBYTECODE=1 python3 docs/memory/evidence/g4_p2_2026-10-17/g4_s1_gate3_read.py

Per run: the sampler's mode (sampler_meta.json), title.txt (titles, titles with the FPS
counter), encoder.jsonl (present or not), the host samples' process CPU (sampler_summary.json:
the window means G4-S1 reported), and the patched remote row's own gate-3 reader
(`e1_remote.gate3_figures` over the run directory) -- what the fixed row would read from these
files.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tools"))
import e1_remote as R  # noqa: E402
import e1_sampler  # noqa: E402

RUNS = REPO / "docs/memory/evidence/g4_s1_2026-10-16/runs/E1-PS1-STREAM-REMOTE"
out = {}
for run in ("run1", "run2"):
    rd = RUNS / run
    s = json.loads((rd / "summary.json").read_text())
    meta = json.loads((rd / "sampler_meta.json").read_text())
    titles = [l for l in (rd / "title.txt").read_text(errors="replace").splitlines() if l and not l.startswith("#")]
    with_fps = [l for l in titles if re.search(r"FPS:\s*[\d.]+.*Frames:\s*\d+", l)]
    t0, t1 = s["window"]["from"], s["window"]["to"]
    host = {"retroarch": e1_sampler.ra_fps(str(rd / "title.txt"), R._ep(t0), R._ep(t1))}
    procs = {}
    summ = json.loads((rd / "sampler_summary.json").read_text())
    for k, v in (summ.get("host") or {}).items():
        if k.startswith("procs.") and k.endswith(".cpu_pct") and isinstance(v, dict):
            procs[k] = v.get("mean")
    first = json.loads(next(l for l in (rd / "samples.jsonl").open() if l.strip()))
    out[run] = {
        "sampler_e2": meta.get("e2"), "sampler_title": meta.get("title"),
        "title_lines": len(titles), "titles_with_fps_counter": len(with_fps),
        "encoder_jsonl_present": (rd / "encoder.jsonl").exists(),
        "samples_process_keys": sorted((first.get("procs") or {}).keys()),
        "window_cpu_pct_means": procs,
        "fixed_row_reads": R.gate3_figures(rd, host, t0, t1),
    }
print(json.dumps(out, indent=1))
