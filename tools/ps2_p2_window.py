#!/usr/bin/env python3
"""B50: when to take H3's P2 capture in a streamed PS2 session (H3-P2's P7f overlapped the user's Back).

The rule (QUEUE_2026-11-08Q §B50.6): the 60-s capture starts **>= 60 s after the last `session_started`** and has **no
pause within 90 s of it** (no pause in [start - 90 s, start + 60 s + 90 s]). Minute 3 of the session (its first
`session_started` + 180 s) is preferred when it is valid. If no valid start comes before minute 9, the plan falls back
to minute 3, marked `fallback`.

The pauses are the recovery log's `session_ended` rows (the onn's Back) and the PS2 game log's `PS2 pause:` lines (its
UTC prefix). The starts are the recovery log's `session_started` rows. The tool reads only the two files given and
prints times and seconds (no path or title):

    python3 tools/ps2_p2_window.py plan  --recovery logs/games/native_stream_recovery.log --ps2-log <the session's -ps2.log> [--now <UTC>]
    python3 tools/ps2_p2_window.py check --recovery ... --ps2-log ... --start <UTC of the capture's start>

`plan` prints `wait_s` (0 = start now) and the planned start; A starts the capture then. `check`, after the capture,
says whether the window is valid with the pauses seen since (a Back during or within 90 s after it → retake later).
Design: `docs/memory/evidence/b50_2026-11-08/design_written_before_code.md` §S6.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

AFTER_START_S = 60
PAUSE_GUARD_S = 90
CAPTURE_S = 60
PREFERRED_S = 180
LAST_PREFERRED_S = 540
_PS2_PAUSE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z) PS2 pause:")


def ts(s: str) -> datetime:
    s = s.strip().replace("Z", "+00:00")
    t = datetime.fromisoformat(s)
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def read_events(recovery: Path, ps2_log: Path | None) -> tuple[list[datetime], list[datetime]]:
    starts, pauses = [], []
    for line in recovery.read_text(errors="replace").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if not isinstance(r, dict) or not r.get("at_utc"):
            continue
        if r.get("event") == "session_started":
            starts.append(ts(r["at_utc"]))
        elif r.get("event") == "session_ended":
            pauses.append(ts(r["at_utc"]))
    if ps2_log is not None and ps2_log.is_file():
        for line in ps2_log.read_text(errors="replace").splitlines():
            m = _PS2_PAUSE.match(line)
            if m:
                pauses.append(ts(m.group(1)))
    return sorted(starts), sorted(pauses)


def valid(t: datetime, starts: list[datetime], pauses: list[datetime]) -> bool:
    before = [s for s in starts if s <= t]
    if not before or (t - before[-1]).total_seconds() < AFTER_START_S:
        return False
    lo, hi = t - timedelta(seconds=PAUSE_GUARD_S), t + timedelta(seconds=CAPTURE_S + PAUSE_GUARD_S)
    return not any(lo < p < hi for p in pauses)            # exactly 90 s away is not "within"


def plan(starts: list[datetime], pauses: list[datetime], now: datetime) -> dict:
    """The earliest valid start >= now (minute 3 preferred), else minute 3 as the fallback."""
    if not starts:
        return {"error": "no session_started yet"}
    first = starts[0]
    minute3 = first + timedelta(seconds=PREFERRED_S)
    t = max(now, minute3)
    t = t.replace(microsecond=0)
    limit = first + timedelta(seconds=LAST_PREFERRED_S)
    while t <= limit:
        if valid(t, starts, pauses):
            return {"start_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "wait_s": max(0, int((t - now).total_seconds())),
                    "fallback": False}
        t += timedelta(seconds=1)
    return {"start_utc": minute3.strftime("%Y-%m-%dT%H:%M:%SZ"), "wait_s": max(0, int((minute3 - now).total_seconds())),
            "fallback": True}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", choices=("plan", "check"))
    ap.add_argument("--recovery", type=Path, required=True)
    ap.add_argument("--ps2-log", type=Path, default=None)
    ap.add_argument("--now", default=None)
    ap.add_argument("--start", default=None)
    a = ap.parse_args(argv)
    starts, pauses = read_events(a.recovery, a.ps2_log)
    if a.mode == "plan":
        now = ts(a.now) if a.now else datetime.now(timezone.utc)
        out = plan(starts, pauses, now)
    else:
        if not a.start:
            ap.error("check needs --start")
        t = ts(a.start)
        out = {"start_utc": a.start, "valid": valid(t, starts, pauses),
               "pauses_near": sum(1 for p in pauses
                                  if t - timedelta(seconds=PAUSE_GUARD_S) < p < t + timedelta(seconds=CAPTURE_S + PAUSE_GUARD_S))}
    print(json.dumps(out))
    return 0 if "error" not in out else 2


if __name__ == "__main__":
    sys.exit(main())
