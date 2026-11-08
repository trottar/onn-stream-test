#!/usr/bin/env python3
"""B49: H3's P2 metric -- unique frames per second from a 60-fps x11grab capture, with the two artefacts H3-P1 found
taken out of the minimum (`evidence/H3_P1_PS2_PROBE_2026-11-07.md` §P2):

- **static / black seconds** (fades, loading screens: the picture does not change, so no emulator can make unique
  frames): a second where >= 90 % of the frames are near-black (Y mean <= 24), or with <= 2 unique frames, is
  excluded from the minimum (counted and listed);
- **the 59.94-Hz beat** (a 59.94-Hz picture captured at 60 Hz repeats one frame every ~17 s): **at most one** isolated
  single repeat per second (a frame equal to the one before while the frames around it differ) is counted as unique
  in the corrected figure. More repeats in a second are real (a 30-fps drop is all single repeats), so they stay.
  Capture an NTSC title at its own rate (`-framerate 60000/1001`) so the beat does not arise in the first place.

The input is ffmpeg's `showinfo` log of the capture **with every frame** (no mpdecimate), e.g.

    ffmpeg -f x11grab -framerate 60000/1001 -window_id <wid> -t 60 -i :0 -vf format=yuv420p,showinfo -f null - 2> showinfo.txt

(`format=yuv420p` first: x11grab's packed `bgr0` carries a padding byte, so its mean is not a luma; the tool refuses
any frame that is not YUV or gray.)

The tool reads only the file given and prints numbers (no path, no title):

    python3 tools/ps2_p2_frames.py showinfo.txt [--pcsx2-fps 59.93] [--json out.json]

A's pre-registered bars (QUEUE_2026-11-08P): median >= 59 and corrected minimum >= 55 (`pass` in the output).
Design: `docs/memory/evidence/b49_2026-11-08/design_written_before_code.md` §5.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

BLACK_Y = 24.0
BLACK_SHARE = 0.9
STATIC_UNIQUE = 2
BAR_MEDIAN = 59
BAR_MIN = 55

_LINE = re.compile(r"pts_time:\s*([\d.]+).*?fmt:(\w+).*?checksum:\s*([0-9A-Fa-f]+).*?mean:\s*\[\s*([\d.]+)")


def parse(text: str) -> list[tuple[float, str, float]]:
    """(pts_time, checksum, Y mean) per frame, in order. A frame that is not YUV / gray refuses (ValueError)."""
    out = []
    for m in map(_LINE.search, text.splitlines()):
        if not m:
            continue
        if not m.group(2).startswith(("yuv", "gray")):
            raise ValueError(f"frames are {m.group(2)}: capture with -vf format=yuv420p,showinfo")
        out.append((float(m.group(1)), m.group(3).upper(), float(m.group(4))))
    return out


def analyze(frames: list[tuple[float, str, float]], pcsx2_fps: float | None = None) -> dict:
    if not frames:
        return {"frames": 0, "error": "no frames"}
    t0 = frames[0][0]
    n = len(frames)
    repeat = [i > 0 and frames[i][1] == frames[i - 1][1] for i in range(n)]
    single = [repeat[i] and (i == 0 or not repeat[i - 1]) and (i + 1 >= n or not repeat[i + 1]) for i in range(n)]
    seconds: dict[int, dict] = {}
    for i, (t, _, y) in enumerate(frames):
        s = seconds.setdefault(int(t - t0), {"frames": 0, "unique": 0, "corrected": 0, "black": 0})
        s["frames"] += 1
        if not repeat[i]:
            s["unique"] += 1
            s["corrected"] += 1
        elif single[i] and not s.get("forgiven"):
            s["corrected"] += 1          # one isolated repeat per second at most (the beat)
            s["forgiven"] = True
        if y <= BLACK_Y:
            s["black"] += 1
    last = max(seconds)
    full = {k: v for k, v in seconds.items() if k < last} or seconds   # the partial last second dropped
    excluded = sorted(k for k, v in full.items()
                      if v["black"] >= BLACK_SHARE * v["frames"] or v["unique"] <= STATIC_UNIQUE)
    kept = [v["corrected"] for k, v in full.items() if k not in excluded]
    median = statistics.median(v["unique"] for v in full.values())
    out = {
        "frames": n,
        "seconds": len(full),
        "median_fps": median,
        "raw_min_fps": min(v["unique"] for v in full.values()),
        "corrected_min_fps": min(kept) if kept else None,
        "median_fps_kept_seconds": statistics.median(kept) if kept else None,
        "excluded_static_or_black_seconds": len(excluded),
        "excluded_at_s": excluded[:30],
        "single_repeats": sum(single),
        "pcsx2_fps": pcsx2_fps,
        "bars": {"median_ge": BAR_MEDIAN, "corrected_min_ge": BAR_MIN},
    }
    out["pass"] = bool(median >= BAR_MEDIAN and kept and min(kept) >= BAR_MIN)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("showinfo", type=Path)
    ap.add_argument("--pcsx2-fps", type=float, default=None, help="PCSX2's own counter, read by A from its overlay")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    result = analyze(parse(a.showinfo.read_text(errors="replace")), a.pcsx2_fps)
    text = json.dumps(result, indent=1)
    if a.json:
        a.json.write_text(text + "\n")
    print(text)
    return 0 if result.get("frames") else 2


if __name__ == "__main__":
    sys.exit(main())
