#!/usr/bin/env python3
"""E3-S7B, reported only (not gated): the aligned frame of tonight's E3-R2 CONC runs (today's grab, unpaced; those runs
carried PRIVYHUB_RECOVERY_TRIGGER=v2, which touches no grab and fired nothing) against this task's control, by
e2_analysis.py's CONC alignment as e3_s7b_analysis.py uses it. Read-only over E3-R2's runs. -> aligned_r2_conc.json"""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("a", os.path.join(HERE, "e3_s7b_analysis.py"))
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
M.HERE = os.path.join(HERE, "aligned_r2_conc_view")
os.makedirs(M.HERE, exist_ok=True)
r2 = os.path.join(HERE, "..", "e3_r2_2026-10-08", "runs", "E1-CONC_flag")
for n in (1, 2):
    p = os.path.join(M.HERE, f"r2run{n}")
    if not os.path.islink(p):
        os.symlink(os.path.relpath(os.path.join(r2, f"run{n}"), M.HERE), p)
p = os.path.join(M.HERE, "ctl")
if not os.path.islink(p):
    os.symlink(os.path.relpath(os.path.join(HERE, "runs", "E1-PS1-STREAM", "run1"), M.HERE), p)
al = M.aligned(["r2run1", "r2run2"], "ctl")
out = {"baseline_loss_per_s": al["baseline"]["stats"]["loss"][0]}
for i in (1, 2):
    a = al[f"E1-CONC/run{i}"]["aligned"]["loss"]
    out[f"R2 CONC r{i} (today's grab)"] = {"aligned_loss_0_10": a, "loss_0_2_mean": round(sum(a[:3]) / 3, 3)}
json.dump(out, open(os.path.join(HERE, "aligned_r2_conc.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
