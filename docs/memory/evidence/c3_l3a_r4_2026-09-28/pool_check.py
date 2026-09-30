#!/usr/bin/env python3
"""C3-L3A-R4: recompute the pooled four-session table from the four run
files (logs/streaming/c3_l3a_runs/*.json, read in place) and compare every
cell with c3_l3a_aggregate.json (byte copy, here). Read-only.

Pooled rule (probe --aggregate): events, marked, marks, exposure summed;
chance-expected = the sum of each run's own chance-expected (each run's
exposure x its own chance rate), as the probe's pooling code does."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE.parents[3] / "logs" / "streaming" / "c3_l3a_runs"
agg = json.loads((HERE / "c3_l3a_aggregate.json").read_text())
runs = [json.loads(p.read_text()) for p in sorted(RUNS.glob("*.json"))]
print("runs:", [r["run_id"] for r in runs])
phase_a = sum(r["phase_a_s"] for r in runs)
marks = sum(r["total_marks"] for r in runs)
rate = marks / phase_a
print("(single pooled-rate alternative, for reference: exposure x",f"{rate:.4f}/s)")
print(f"phase A {phase_a:.3f} s (agg {agg['phase_a_s']}), marks {marks} (agg {agg['total_marks']}), "
      f"chance rate {rate:.4f}/s")
bad = 0
for w in ("2.5", "5.0", "8.0"):
    wk = w if w in runs[0]["scoring"] else w.rstrip("0").rstrip(".")
    ak = w if w in agg["scoring"] else w.rstrip("0").rstrip(".")
    print(f"W {w}")
    for cls in ("jump", "ramp", "decoy_jump_matched", "decoy_ramp_matched"):
        ev = sum(r["scoring"][wk]["classes"][cls]["events"] for r in runs)
        mk = sum(r["scoring"][wk]["classes"][cls]["marked"] for r in runs)
        ms = sum(r["scoring"][wk]["classes"][cls]["marks"] for r in runs)
        ex = sum(r["scoring"][wk]["classes"][cls]["exposure_s"] for r in runs)
        ce = round(sum(r["scoring"][wk]["classes"][cls]["chance_expected_marks"] for r in runs), 2)
        a = agg["scoring"][ak]["classes"][cls]
        same = (ev, mk, ms, round(ex, 1), ce) == (a["events"], a["marked"], a["marks"],
                                                    round(a["exposure_s"], 1), a["chance_expected_marks"])
        bad += not same
        print(f"  {cls:<20} {ev:>3} {mk:>3} {ms:>3} {ex:8.1f} {ce:6.2f}  agg match {same}")
    nw = sum(r["scoring"][wk]["not_in_any_sequence_window"] for r in runs)
    print(f"  not in any window {nw} (agg {agg['scoring'][ak]['not_in_any_sequence_window']})")
print("ALL CELLS MATCH" if bad == 0 else f"MISMATCHES: {bad}")
