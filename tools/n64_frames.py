#!/usr/bin/env python3
"""B59: the N64 frame metric -- distinct frames per second against the title's own internal rate, and the hitch rate.

The stream carries 60 frames a second whatever an N64 title draws (x11grab at a fixed 60, `-r 60`), so UX-R3's R rule
(rendered < 50 fps) never fires on a title that draws 20 or 30 frames, and it does not see the title's own slowdowns.
This tool reads the title's drawn frames from a capture of the RetroArch window:

- **distinct frames per second** (a frame differing from the one before), static / black seconds excluded as H3's P2
  (`ps2_p2_frames`: >= 90 % near-black, or <= 2 distinct);
- **the internal rate:** the most common distinct count of the kept seconds, snapped to 20 / 30 / 60 (or
  `--internal-fps`); at 60 one isolated repeat per second is forgiven (the 59.94-Hz beat), as P2's;
- **a hitch second:** a kept second with distinct frames < 5/6 of the internal rate (UX-R3's 50-of-60, scaled:
  < 50 at 60, < 25 at 30, < 17 at 20); **the hitch rate** per 10 min, to set beside the stream's UX-R3 hitch rate
  (`tools/diag_read.py`) and a PS1 session's.

The input is ffmpeg's `showinfo` log of the capture with every frame, YUV first:

    ffmpeg -f x11grab -framerate 60 -window_id <wid> -t 600 -i :0 -vf format=yuv420p,showinfo -f null - 2> showinfo.txt

    python3 tools/n64_frames.py showinfo.txt [--internal-fps 30] [--json out.json]

Prints numbers only (no path, no title). Design: docs/memory/evidence/b59_2026-11-08/design_written_before_code.md.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ps2_p2_frames as _p2  # noqa: E402  (the showinfo parser and the static / black rule)

RATES = (20, 30, 60)
HITCH_SHARE = 5 / 6


def snap(n: float) -> int:
    return min(RATES, key=lambda r: (abs(r - n), -r))


def analyze(frames: list[tuple[float, str, float]], internal_fps: int | None = None) -> dict:
    if not frames:
        return {"frames": 0, "error": "no frames"}
    t0 = frames[0][0]
    n = len(frames)
    repeat = [i > 0 and frames[i][1] == frames[i - 1][1] for i in range(n)]
    single = [repeat[i] and (i == 0 or not repeat[i - 1]) and (i + 1 >= n or not repeat[i + 1]) for i in range(n)]
    seconds: dict[int, dict] = {}
    for i, (t, _, y) in enumerate(frames):
        s = seconds.setdefault(int(t - t0), {"frames": 0, "distinct": 0, "singles": 0, "black": 0})
        s["frames"] += 1
        if not repeat[i]:
            s["distinct"] += 1
        elif single[i]:
            s["singles"] += 1
        if y <= _p2.BLACK_Y:
            s["black"] += 1
    last = max(seconds)
    full = {k: v for k, v in seconds.items() if k < last} or seconds   # the partial last second dropped
    excluded = sorted(k for k, v in full.items()
                      if v["black"] >= _p2.BLACK_SHARE * v["frames"] or v["distinct"] <= _p2.STATIC_UNIQUE)
    kept = {k: v for k, v in full.items() if k not in excluded}
    if not kept:
        return {"frames": n, "seconds": len(full), "error": "every second static or black",
                "excluded_static_or_black_seconds": len(excluded)}
    mode = Counter(v["distinct"] for v in kept.values()).most_common(1)[0][0]
    rate = int(internal_fps) if internal_fps else snap(mode)
    # the 59.94-Hz beat: one isolated repeat per second counted as distinct, at 60 only
    counted = {k: v["distinct"] + (1 if rate == 60 and v["singles"] else 0) for k, v in kept.items()}
    bar = rate * HITCH_SHARE
    hitches = sorted(k for k, c in counted.items() if c < bar)
    minutes = len(kept) / 60.0
    return {
        "frames": n,
        "seconds": len(full),
        "kept_seconds": len(kept),
        "excluded_static_or_black_seconds": len(excluded),
        "internal_fps": rate,
        "internal_fps_source": "given" if internal_fps else "mode",
        "distinct_mode": mode,
        "median_distinct_fps": statistics.median(counted.values()),
        "min_distinct_fps": min(counted.values()),
        "hitch_bar_lt": round(bar, 2),
        "hitch_seconds": len(hitches),
        "hitch_at_s": hitches[:30],
        "hitch_per_10min": round(len(hitches) / minutes * 10, 2) if minutes else None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("showinfo", type=Path)
    ap.add_argument("--internal-fps", type=int, choices=RATES, default=None)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    result = analyze(_p2.parse(a.showinfo.read_text(errors="replace")), a.internal_fps)
    text = json.dumps(result, indent=1)
    if a.json:
        a.json.write_text(text + "\n")
    print(text)
    return 0 if result.get("frames") and "error" not in result else 2


if __name__ == "__main__":
    sys.exit(main())
