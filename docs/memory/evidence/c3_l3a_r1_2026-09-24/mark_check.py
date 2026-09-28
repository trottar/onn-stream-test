#!/usr/bin/env python3
"""C3-L3A-R1: every mark against the slow events (>= 50 ms) retained in the
decoder session that covers it, over the 5 s before the mark. Offsets come
from the regenerated run file (each session aligned on its own fires).
Reads only; run from the repository root with this directory's copies."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
run = json.loads((HERE / "after_fix" / "20260924_115810.json").read_text())
state = json.loads((HERE / "c3_l3a_gameplay_acceptance_state.json").read_text())
fires = [t["fired_at_s"] for t in state["transitions"]]
decoys = [d["at_s"] for d in state["events"] if d["kind"] == "decoy"]
BEFORE_S = 5.0

sessions = []
for part in run["decoder"]["sessions"]:
    payload = json.loads((HERE / Path(part["path"]).name).read_text())
    report = payload["report"]
    cols = report["slow_event_columns"]
    rows = [dict(zip(cols, r)) for r in report["slow_events_ge_50_ms"]]
    offset = part["view"]["alignment"]["offset_s"]
    span = part["view"]["session_probe_span_s"]
    sessions.append((part["session"], offset, span, rows))
    print(f"session {part['session']}: offset {offset:+.3f} s (decoder = probe + offset), "
          f"probe span {span[0]:.3f} .. {span[1]:.3f}, slow events retained {len(rows)}")

print()
print(f"{'mark s':>8} sess {'dec s':>8}  worst gap in {BEFORE_S:g} s before: gap ms  codec ms  s before mark"
      "   lag fire  lag decoy")
for m in state["marks"]:
    at = m["elapsed_s"]
    sess = [s for s in sessions if s[2][0] <= at <= s[2][1]]
    fire = max([f for f in fires if f <= at], default=None)
    decoy = max([d for d in decoys if d <= at], default=None)
    tail = (f"{'-' if fire is None else f'{at - fire:.2f}':>9}  "
            f"{'-' if decoy is None else f'{at - decoy:.2f}':>9}")
    if not sess:
        print(f"{at:8.3f}  -  no session covers this mark  {tail}")
        continue
    number, offset, _, rows = sess[0]
    dec = at + offset
    inside = [r for r in rows if dec - BEFORE_S <= r["elapsed_ms"] / 1000.0 <= dec]
    if not inside:
        print(f"{at:8.3f}  {number}  {dec:8.3f}  none                                    {tail}")
        continue
    worst = max(inside, key=lambda r: r["output_gap_ms"])
    print(f"{at:8.3f}  {number}  {dec:8.3f}  {worst['output_gap_ms']:>6}  {worst['codec_ms']:>8}  "
          f"{dec - worst['elapsed_ms'] / 1000.0:13.2f}  {len(inside):>3} ev  {tail}")
