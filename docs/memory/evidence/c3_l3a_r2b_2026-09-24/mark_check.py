#!/usr/bin/env python3
"""C3-L3A-R2B: every mark of rerun session 2 against the slow events in the
rebuilt decoder report, over the 5 s before the mark (R1's mark_check.py,
one session). Reads only.

The report's slow-event buffer SATURATED, and it is two rings
(`AvcLowLatencyDecoder.recordSlowEvent`): events inside the 2 s cycle window
after a discontinuity go to the MARKED ring (64), all others to the RECENT
ring (64). So, per source:
  marked ring  - cycle-window events, retained from its first row onward;
  recent ring  - off-transition events, retained only from its first row;
                 before that, an off-transition event was evicted: a mark
                 there with nothing in 5 s reads "unknown", not "none";
  top-gap list - the 16 largest output gaps of the whole session, never
                 evicted: any gap not in it is <= the list's smallest.
Inputs: after_decoder/20260924_130016.json (here); the state copy and the
wrapped report in ../c3_l3a_r2_2026-09-24/.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R2 = HERE.parent / "c3_l3a_r2_2026-09-24"
run = json.loads((HERE / "after_decoder" / "20260924_130016.json").read_text())
state = json.loads((R2 / "20260924_130016_state.json").read_text())
report = json.loads((R2 / "native_decoder_20260924_171642_rebuilt.json").read_text())["report"]
fires = [t["fired_at_s"] for t in state["transitions"]]
decoys = [d["at_s"] for d in state["events"] if d["kind"] == "decoy"]
BEFORE_S = 5.0

offset = run["decoder"]["view"]["alignment"]["offset_s"]
cols = report["slow_event_columns"]
E, G = cols.index("elapsed_ms"), cols.index("output_gap_ms")
C = cols.index("codec_ms")
rows = report["slow_events_ge_50_ms"]
n_marked = report["slow_event_retained_marked"]
# Merged chronologically, so split the rings by the cycle windows themselves.
ssrc_dec = [d["elapsed_ms"] / 1000.0 for d in report["stream_discontinuities"]]
in_cycle = lambda t: any(0.0 <= t - s <= 2.0 for s in ssrc_dec)  # noqa: E731
marked = [r for r in rows if in_cycle(r[E] / 1000.0)]
recent = [r for r in rows if not in_cycle(r[E] / 1000.0)]
top = report["slow_events_top_gap"]
top_floor = min(r[G] for r in top)
marked_from = min(r[E] for r in marked) / 1000.0
recent_from = min(r[E] for r in recent) / 1000.0
print(f"offset {offset:+.3f} s (decoder = probe + offset)")
print(f"rows {len(rows)}: in a cycle window {len(marked)} (report: marked {n_marked}), "
      f"outside {len(recent)} (report: recent {report['slow_event_retained_recent']})")
print(f"marked ring from decoder {marked_from:.3f} s = probe {marked_from - offset:.3f} s")
print(f"recent ring from decoder {recent_from:.3f} s = probe {recent_from - offset:.3f} s"
      f" (off-transition events before this were evicted)")
print(f"top-gap list: {len(top)} rows, smallest {top_floor} ms; every gap not listed is <= {top_floor} ms")
top_at_ssrc = sum(1 for r in top if in_cycle(r[E] / 1000.0))
print(f"top-gap rows inside a cycle window (i.e. at a transition): {top_at_ssrc} of {len(top)}")
print()
print(f"{'mark s':>8} {'dec s':>8}  {'source':<9} {'gap ms':>6} {'codec':>5} {'s before':>8}"
      f"  {'lag fire':>8} {'lag decoy':>9}")
for m in state["marks"]:
    at = m["elapsed_s"]
    dec = at + offset
    fire = max([f for f in fires if f <= at], default=None)
    decoy = max([d for d in decoys if d <= at], default=None)
    tail = (f"  {'-' if fire is None else f'{at - fire:.2f}':>8} "
            f"{'-' if decoy is None else f'{at - decoy:.2f}':>9}")
    lo = dec - BEFORE_S
    cand = [("top-gap", r) for r in top if lo <= r[E] / 1000.0 <= dec]
    cand += [("marked", r) for r in marked if lo <= r[E] / 1000.0 <= dec]
    cand += [("recent", r) for r in recent if lo <= r[E] / 1000.0 <= dec]
    if cand:
        src, worst = max(cand, key=lambda c: c[1][G])
        print(f"{at:8.3f} {dec:8.3f}  {src:<9} {worst[G]:>6} {worst[C]:>5} "
              f"{dec - worst[E] / 1000.0:8.2f}{tail}")
        continue
    cycle_here = any(lo <= s <= dec for s in ssrc_dec)
    if dec < recent_from:
        what = f"unknown <= {top_floor}"
        if cycle_here and lo < marked_from:
            what += " (cycle window before marked ring)"
    else:
        what = "none (covered)"
    print(f"{at:8.3f} {dec:8.3f}  {what}{tail}")

print()
gaps = sorted(r[G] for r in recent)
print(f"recent ring ({len(recent)} off-transition events, decoder {recent_from:.1f}-"
      f"{max(r[E] for r in recent) / 1000.0:.1f} s): output_gap_ms >= 50: "
      f"{sum(1 for g in gaps if g >= 50)}, max {gaps[-1]}; the rest are latency events")
