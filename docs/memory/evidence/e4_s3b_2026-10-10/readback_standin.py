#!/usr/bin/env python3
"""E4-S3B: the driver's 60-s constraint read-back (its readback_thread, the same fields), run stand-alone for step
mem:1G while the driver was stopped to fix its control lookup (ladder_fix.md). Ends when the suite PID exits."""
import importlib.util, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("e1_suite", os.path.join(HERE, "../../../../tools/e1_suite.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
pid, label = int(sys.argv[1]), sys.argv[2]
with open(os.path.join(HERE, "runs", "constraint_readback.jsonl"), "a") as fh:
    while os.path.exists(f"/proc/{pid}"):
        time.sleep(60)
        p = m.unit_props()
        fh.write(json.dumps({"at_utc": m.utc(), "step": label, "game_active": m.games_status().get("active"),
                             **{k: p.get(k) for k in ("MemoryMax", "MemorySwapMax", "CPUQuotaPerSecUSec", "memory.max",
                                                      "memory.swap.max", "cpu.max", "dropin_present")},
                             "source": "readback_standin.py"}) + "\n")
        fh.flush()
