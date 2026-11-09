#!/usr/bin/env python3
"""B69: the GameCube frame metric per segment -- a title can switch between 60 and 30 (H2-P1's T1: a 60-fps title
screen, a 30-fps attract demo), so one rate over a whole capture misreads both parts.

- **a capture** (ffmpeg `showinfo`, YUV first, as `n64_frames`): each second's distinct frames snapped to 30 / 60;
  runs of one rate >= `--min-segment` seconds (default 5) are the segments, the one second at each side of a change
  and the shorter runs dropped as transitions; **each segment is read by `n64_frames.analyze(..., internal_fps=rate)`**
  (its hitch bar: < 5/6 of the rate; static / black seconds excluded);
- **`--render render_times.txt`** (Dolphin's `LogRenderTimeToFile`: one interval in ms per presented frame): the same
  segments and bar on Dolphin's own presented frames per second, no capture needed;
- **`--vblank vblank_times.txt`** beside: Dolphin's emulated VIs per second, p50 / p95 / p99 and the intervals over
  34 / 100 ms (`--window START:END` in Dolphin's own seconds since its start, else the whole file).

    python3 tools/gc_frames.py [showinfo.txt] [--render render_times.txt] [--vblank vblank_times.txt] [--json out]

Prints numbers only (no path, no title). Design: docs/memory/evidence/b69_2026-11-09/design_written_before_code.md.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import n64_frames as _n64  # noqa: E402  (the per-segment reading)
import ps2_p2_frames as _p2  # noqa: E402  (the showinfo parser, the static / black rule)

RATES = (30, 60)
MIN_SEGMENT_S = 5
HITCH_SHARE = _n64.HITCH_SHARE


def snap(n: float) -> int:
    return min(RATES, key=lambda r: (abs(r - n), -r))


def segments(rates: dict[int, int | None], min_len: int = MIN_SEGMENT_S) -> tuple[list[tuple[int, int, int]], int]:
    """(start, end exclusive, rate) runs of one rate in consecutive seconds, one second trimmed at each side that
    borders another rate; runs shorter than `min_len` dropped. Returns (segments, seconds dropped)."""
    keys = sorted(rates)
    runs: list[list[int]] = []                      # [start, end exclusive, rate]
    for k in keys:
        r = rates[k]
        if r is None:
            continue
        if runs and runs[-1][1] == k and runs[-1][2] == r:
            runs[-1][1] = k + 1
        else:
            runs.append([k, k + 1, r])
    out = []
    used = 0
    for i, (a, b, r) in enumerate(runs):
        if i > 0 and runs[i - 1][1] == a:          # a change right before: its first second is a transition
            a += 1
        if i + 1 < len(runs) and runs[i + 1][0] == b:
            b -= 1
        if b - a >= min_len:
            out.append((a, b, r))
            used += b - a
    total = sum(1 for k in keys if rates[k] is not None)
    return out, total - used


def capture(frames: list[tuple[float, str, float]], min_len: int = MIN_SEGMENT_S) -> dict:
    if not frames:
        return {"frames": 0, "error": "no frames"}
    t0 = frames[0][0]
    secs: dict[int, dict] = {}
    for i, (t, h, y) in enumerate(frames):
        s = secs.setdefault(int(t - t0), {"frames": 0, "distinct": 0, "black": 0})
        s["frames"] += 1
        if i == 0 or h != frames[i - 1][1]:
            s["distinct"] += 1
        if y <= _p2.BLACK_Y:
            s["black"] += 1
    last = max(secs)
    rates: dict[int, int | None] = {}
    for k, v in secs.items():
        if k >= last:
            continue                                # the partial last second
        static = v["black"] >= _p2.BLACK_SHARE * v["frames"] or v["distinct"] <= _p2.STATIC_UNIQUE
        rates[k] = None if static else snap(v["distinct"])
    segs, dropped = segments(rates, min_len)
    out = []
    for a, b, r in segs:
        # the frames of seconds a..b inclusive: n64_frames drops the last (partial) second, so a..b-1 are read
        sub = [f for f in frames if a <= int(f[0] - t0) <= b]
        res = _n64.analyze(sub, internal_fps=r)
        out.append({"start_s": a, "end_s": b, "rate": r, **{k: res.get(k) for k in (
            "kept_seconds", "median_distinct_fps", "min_distinct_fps", "hitch_bar_lt", "hitch_seconds",
            "hitch_per_10min", "excluded_static_or_black_seconds")}})
    return {"frames": len(frames), "seconds": len(rates), "segments": out, "transition_or_short_seconds": dropped,
            **totals(out)}


def render(intervals_ms: list[float], min_len: int = MIN_SEGMENT_S) -> dict:
    """Dolphin's presented frames per second (cumulative intervals), segmented and barred as a capture."""
    if not intervals_ms:
        return {"presents": 0, "error": "no render times"}
    counts: dict[int, int] = {}
    t = 0.0
    for v in intervals_ms:
        t += v
        counts[int(t // 1000)] = counts.get(int(t // 1000), 0) + 1
    last = max(counts)
    rates: dict[int, int | None] = {}
    for k in range(0, last):                        # the partial last second dropped; an empty second is static
        n = counts.get(k, 0)
        rates[k] = None if n <= _p2.STATIC_UNIQUE else snap(n)
    segs, dropped = segments(rates, min_len)
    out = []
    for a, b, r in segs:
        vals = [counts.get(k, 0) for k in range(a, b)]
        bar = r * HITCH_SHARE
        hitches = [k for k in range(a, b) if counts.get(k, 0) < bar]
        minutes = len(vals) / 60.0
        out.append({"start_s": a, "end_s": b, "rate": r, "kept_seconds": len(vals),
                    "median_distinct_fps": statistics.median(vals), "min_distinct_fps": min(vals),
                    "hitch_bar_lt": round(bar, 2), "hitch_seconds": len(hitches),
                    "hitch_per_10min": round(len(hitches) / minutes * 10, 2) if minutes else None})
    return {"presents": len(intervals_ms), "seconds": len(rates), "segments": out,
            "transition_or_short_seconds": dropped, **totals(out)}


def totals(segs: list[dict]) -> dict:
    kept = sum(int(s.get("kept_seconds") or 0) for s in segs)
    hitch = sum(int(s.get("hitch_seconds") or 0) for s in segs)
    return {"kept_seconds_total": kept, "hitch_seconds_total": hitch,
            "hitch_per_10min_total": round(hitch / (kept / 60.0) * 10, 2) if kept else None}


def q(vals: list[float], p: float) -> float:
    s = sorted(vals)
    return round(s[min(len(s) - 1, int(p * len(s)))], 2)


def vblank(intervals_ms: list[float], window: tuple[float, float] | None = None) -> dict:
    """Dolphin's VI intervals: per second, p50 / p95 / p99, over 34 / 100 ms (in a window of its own seconds)."""
    t = 0.0
    vals = []
    for v in intervals_ms:
        t += v
        if window is None or window[0] * 1000 <= t <= window[1] * 1000:
            vals.append(v)
    if not vals:
        return {"n": 0}
    span = sum(vals) / 1000.0
    return {"n": len(vals), "span_s": round(span, 1), "per_s": round(len(vals) / span, 2) if span else None,
            "p50_ms": q(vals, .5), "p95_ms": q(vals, .95), "p99_ms": q(vals, .99), "max_ms": round(max(vals), 1),
            "gt_34ms": sum(v > 34 for v in vals), "gt_100ms": sum(v > 100 for v in vals)}


def numbers(path: Path) -> list[float]:
    out = []
    for tok in path.read_text(errors="replace").split():
        try:
            out.append(float(tok))
        except ValueError:
            pass
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("showinfo", type=Path, nargs="?")
    ap.add_argument("--render", type=Path, default=None)
    ap.add_argument("--vblank", type=Path, default=None)
    ap.add_argument("--window", default=None, help="START:END in Dolphin's seconds (the vblank summary)")
    ap.add_argument("--min-segment", type=int, default=MIN_SEGMENT_S)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    if a.showinfo is None and a.render is None:
        ap.error("a showinfo capture or --render is needed")
    result: dict = {}
    if a.showinfo is not None:
        result["capture"] = capture(_p2.parse(a.showinfo.read_text(errors="replace")), a.min_segment)
    if a.render is not None:
        result["dolphin_render"] = render(numbers(a.render), a.min_segment)
    if a.vblank is not None:
        w = tuple(float(x) for x in a.window.split(":")) if a.window else None
        result["dolphin_vblank"] = vblank(numbers(a.vblank), w)
    text = json.dumps(result, indent=1)
    if a.json:
        a.json.write_text(text + "\n")
    print(text)
    bad = any(isinstance(v, dict) and "error" in v for v in result.values())
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
