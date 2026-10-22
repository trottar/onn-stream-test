#!/usr/bin/env python3
"""B2: "unattended frames" -- host frames emitted while no controller packet had arrived for >= 250 ms.

The number the fast input hold (PRIVYHUB_INPUT_HOLD) exists to cut. Defined in
`docs/memory/evidence/b2_2026-10-22/design_written_before_code.md` §7. Read-only; it reads only the directory given.

    python3 tools/unattended_frames.py --logs <dir with native_stream_ctrl_gaps.log and native_frame_sizes.jsonl>
        --span 2026-10-21T04:42:00 2026-10-21T05:27:00 [--window death 2026-10-21T04:54:50 2026-10-21T04:55:05]
        [--hold-ms 250,500,1000] [--json out.json]

- The control-gap log (E3-R2) holds every controller gap > 250 ms (start / end). A gap's unattended span is
  [start + 250 ms, end]; its frames are the frame-size log's per-second `frames`, prorated by the overlap.
- Episodes ("per blackout"): gaps less than 500 ms apart (the gap log's own burst rule) are one episode.
- Per 10 min: unattended frames / streaming seconds (seconds with frames > 0 in the span) x 600.
- Held episodes per H: the episodes with at least one single gap >= H, per 10 min (what an input hold of H would
  pause, the false holds of a clean link included).
- **Two counts.** `unattended_frames` is the queue's definition as written (every host frame in those spans). But the
  encoder keeps emitting the frozen picture at the full rate while the core is paused (measured: Sunday's recovery
  pause 05:10:03-05:10:08Z, 60 frames/s), so that count cannot show a pause. **`unattended_frames_core_running`**
  also subtracts the spans in which recovery had the core paused (`native_stream_recovery.log`: a `desync_pause` to
  the next `resumed` / `session_ended` / `session_started`): the frames the game advanced without the player. This
  is the number the input hold exists to cut.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
from datetime import datetime, timezone
from pathlib import Path

THRESHOLD_S = 0.25
EPISODE_JOIN_S = 0.5


def ts(t: str) -> float:
    t = t.rstrip("Z")
    fmt = "%Y-%m-%dT%H:%M:%S.%f" if "." in t else "%Y-%m-%dT%H:%M:%S"
    return datetime.strptime(t, fmt).replace(tzinfo=timezone.utc).timestamp()


def utc(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def jl(paths):
    for p in paths:
        try:
            lines = Path(p).read_text(errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                yield json.loads(line)
            except Exception:
                pass


def load(logs: Path, a: float, b: float):
    gaps = {}
    for r in jl(sorted(glob.glob(str(logs / "native_stream_ctrl_gaps.log*")))
                + sorted(glob.glob(str(logs / "stream_log_archive" / "native_stream_ctrl_gaps.log*")))):
        if r.get("start_utc") and r.get("end_utc"):
            s, e = ts(r["start_utc"]), ts(r["end_utc"])
            if e > a and s < b:
                gaps[(r["start_utc"], r["end_utc"])] = (s, e)
    frames = {}
    for r in jl(sorted(glob.glob(str(logs / "native_frame_sizes.jsonl*")))
                + sorted(glob.glob(str(logs / "stream_log_archive" / "native_frame_sizes.jsonl*")))):
        if r.get("at_utc") and isinstance(r.get("frames"), (int, float)):
            t = math.floor(ts(r["at_utc"]))
            if a - 1 <= t < b:
                frames[t] = int(r["frames"])
    return sorted(gaps.values()), frames


def paused_spans(logs: Path, a: float, b: float) -> list[tuple[float, float]]:
    """Recovery's paused spans: a desync_pause to the next resumed / session_ended / session_started."""
    rows = {}
    for r in jl(sorted(glob.glob(str(logs / "native_stream_recovery.log*")))
                + sorted(glob.glob(str(logs / "stream_log_archive" / "native_stream_recovery*")))):
        if r.get("at_utc") and r.get("event"):
            rows[(r["at_utc"], r["event"])] = (ts(r["at_utc"]), r["event"])
    out, start = [], None
    for t, ev in sorted(rows.values()):
        if ev == "desync_pause" and start is None:
            start = t
        elif ev in ("resumed", "session_ended", "session_started") and start is not None:
            if t > a and start < b:
                out.append((start, t))
            start = None
    if start is not None and start < b:
        out.append((start, b))
    return out


def running_frames_in(frames: dict, s: float, e: float, paused: list[tuple[float, float]]) -> float:
    """Frames in [s, e] outside the paused spans."""
    n, cur = 0.0, s
    for ps, pe in sorted(paused):
        if pe <= cur or ps >= e:
            continue
        if ps > cur:
            n += frames_in(frames, cur, ps)
        cur = max(cur, pe)
    if cur < e:
        n += frames_in(frames, cur, e)
    return n


def frames_in(frames: dict, s: float, e: float) -> float:
    n = 0.0
    sec = math.floor(s)
    while sec < e:
        lo, hi = max(s, sec), min(e, sec + 1)
        if hi > lo:
            n += frames.get(sec, 0) * (hi - lo)
        sec += 1
    return n


def episodes(gaps):
    out = []
    for s, e in gaps:
        if out and s - out[-1]["end"] < EPISODE_JOIN_S:
            out[-1]["end"] = max(out[-1]["end"], e)
            out[-1]["gaps"].append((s, e))
        else:
            out.append({"start": s, "end": e, "gaps": [(s, e)]})
    return out


def measure(logs: Path, a: float, b: float, windows=(), holds=(250, 500, 1000)) -> dict:
    gaps, frames = load(logs, a, b)
    paused = paused_spans(logs, a, b)
    stream_s = sum(1 for t, f in frames.items() if a <= t < b and f > 0)
    eps = episodes(gaps)
    for ep in eps:
        ep["unattended_frames"] = round(sum(frames_in(frames, max(s + THRESHOLD_S, a), min(e, b))
                                            for s, e in ep["gaps"] if e - s >= THRESHOLD_S), 1)
        ep["unattended_frames_core_running"] = round(sum(
            running_frames_in(frames, max(s + THRESHOLD_S, a), min(e, b), paused)
            for s, e in ep["gaps"] if e - s >= THRESHOLD_S), 1)
        ep["longest_gap_ms"] = round(max(e - s for s, e in ep["gaps"]) * 1000.0)
        ep["silent_ms"] = round(sum(e - s for s, e in ep["gaps"]) * 1000.0)
    total = sum(ep["unattended_frames"] for ep in eps)
    running = sum(ep["unattended_frames_core_running"] for ep in eps)
    per10 = (lambda x: round(x * 600.0 / stream_s, 2) if stream_s else None)
    res = {"span": [utc(a), utc(b)], "streaming_s": stream_s, "gaps": len(gaps), "episodes": len(eps),
           "unattended_frames": round(total, 1), "unattended_frames_per_10min": per10(total),
           "unattended_frames_core_running": round(running, 1),
           "unattended_frames_core_running_per_10min": per10(running),
           "recovery_paused_spans": [[utc(x), round(y - x, 2)] for x, y in paused],
           "episodes_per_10min": per10(len(eps)),
           "held_episodes_per_10min": {str(h): per10(sum(1 for ep in eps if ep["longest_gap_ms"] >= h)) for h in holds},
           "held_episodes": {str(h): sum(1 for ep in eps if ep["longest_gap_ms"] >= h) for h in holds},
           "top_episodes": [{"start": utc(ep["start"]), "end": utc(ep["end"]), "gaps": len(ep["gaps"]),
                             "silent_ms": ep["silent_ms"], "longest_gap_ms": ep["longest_gap_ms"],
                             "unattended_frames": ep["unattended_frames"],
                             "unattended_frames_core_running": ep["unattended_frames_core_running"]}
                            for ep in sorted(eps, key=lambda x: -x["unattended_frames"])[:10]],
           "windows": {}}
    for name, wa, wb in windows:
        n = sum(frames_in(frames, max(s + THRESHOLD_S, wa), min(e, wb)) for s, e in gaps if e - s >= THRESHOLD_S)
        nr = sum(running_frames_in(frames, max(s + THRESHOLD_S, wa), min(e, wb), paused)
                 for s, e in gaps if e - s >= THRESHOLD_S)
        res["windows"][name] = {"span": [utc(wa), utc(wb)], "unattended_frames": round(n, 1),
                                "unattended_frames_core_running": round(nr, 1),
                                "gaps": [[utc(s), round((e - s) * 1000)] for s, e in gaps if e > wa and s < wb]}
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", required=True, type=Path)
    ap.add_argument("--span", nargs=2, required=True)
    ap.add_argument("--window", nargs=3, action="append", default=[])
    ap.add_argument("--hold-ms", default="250,500,1000")
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    res = measure(a.logs, ts(a.span[0]), ts(a.span[1]), [(n, ts(x), ts(y)) for n, x, y in a.window],
                  tuple(int(x) for x in a.hold_ms.split(",")))
    print(json.dumps(res, indent=1))
    if a.json:
        a.json.write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
