#!/usr/bin/env python3
"""C3-L3A-R4: every mark of rerun session 4 against the slow events in its
stored decoder report, over the 5 s before the mark (R2B's mark_check.py,
unchanged method, this session's inputs). Reads only.

The report's slow-event buffer SATURATED again (128 of 128), in two rings
(`AvcLowLatencyDecoder.recordSlowEvent`): events inside the 2 s cycle window
after a discontinuity go to the MARKED ring (64), all others to the RECENT
ring (64). So, per source:
  marked ring  - cycle-window events, retained from its first row onward;
  recent ring  - off-transition events, retained only from its first row;
                 before that, an off-transition event was evicted: a mark
                 there with nothing in 5 s reads "unknown", not "none";
  top-gap list - the 16 largest output gaps of the whole session, never
                 evicted: any gap not in it is <= the list's smallest.
Inputs (here): runs/20260928_122028.json, 20260928_122028_state.json,
native_decoder_20260928_163654_864.json (byte copy of the stored report).
Also locates the session's largest output gap on the decoder axis.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
run = json.loads((HERE / "runs" / "20260928_122028.json").read_text())
state = json.loads((HERE / "20260928_122028_state.json").read_text())
report = json.loads((HERE / "native_decoder_20260928_163654_864.json").read_text())["report"]
fires = [t["fired_at_s"] for t in state["transitions"]]
decoys = [d["at_s"] for d in state["events"] if d["kind"] == "decoy"]
BEFORE_S = 5.0

offset = run["decoder"]["view"]["alignment"]["offset_s"]
cols = report["slow_event_columns"]
E, G = cols.index("elapsed_ms"), cols.index("output_gap_ms")
C = cols.index("codec_ms")
rows = report["slow_events_ge_50_ms"]
n_marked = report["slow_event_retained_marked"]
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
for r in top:
    if not in_cycle(r[E] / 1000.0):
        t = r[E] / 1000.0
        prev = max([s for s in ssrc_dec if s <= t], default=None)
        print(f"  off-transition top-gap row: decoder {t:.3f} s = probe {t - offset:.3f} s, "
              f"gap {r[G]} ms, codec {r[C]}, {t - prev:.2f} s after the previous ssrc_change")
print()
print(f"{'mark s':>8} {'dec s':>8}  {'source':<9} {'gap ms':>6} {'codec':>5} {'s before':>8}"
      f"  {'lag fire':>8} {'lag decoy':>9}")
behind_gap = 0
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
        if worst[G] >= 100 and in_cycle(worst[E] / 1000.0):
            behind_gap += 1
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
print(f"marks behind a measured restart gap (>= 100 ms, in a cycle window, <= 5 s before): {behind_gap}")

gaps = sorted(r[G] for r in recent)
print(f"recent ring ({len(recent)} off-transition events, decoder {recent_from:.1f}-"
      f"{max(r[E] for r in recent) / 1000.0:.1f} s): output_gap_ms >= 50: "
      f"{sum(1 for g in gaps if g >= 50)}, max {gaps[-1]}; the rest are latency events")

print()
worst = max(top, key=lambda r: r[G])
t = worst[E] / 1000.0
prev_i = max(i for i, s in enumerate(ssrc_dec) if s <= t)
idr = report["first_idr_after_discontinuity"]
print(f"session max output gap {worst[G]} ms at decoder {t:.3f} s = probe {t - offset:.3f} s, "
      f"codec_ms {worst[C]}; {1000 * (t - ssrc_dec[prev_i]):.0f} ms after ssrc_change #{prev_i + 1} "
      f"of {len(ssrc_dec)} (decoder {ssrc_dec[prev_i]:.3f} s)")
print(f"  first_idr_after_discontinuity row for that change: {idr[prev_i] if prev_i < len(idr) else '-'}")
print(f"  video.max_output_gap_ms {report['video'].get('max_output_gap_ms')}, "
      f"decoder block max_output_gap_ms {report.get('decoder', {}).get('max_output_gap_ms')}")
