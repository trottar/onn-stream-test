#!/usr/bin/env python3
"""B36: the always-on diagnostics keeper (`privyhub-diag`) -- B30's trip log-keeper made permanent, read-only on the hub.

    python3 tools/diag_keeper.py [--root ~/privyhub_diag] [--copy-s 300] [--sample-s 60] [--once]

- every --copy-s: B30's copies (G4-S4's logs in logs/games/ following rotation, the hub's wan_sessions /
  session_audit / impairment rows, B35's vod_client / vod_range rows, each game log, the new decoder reports and audio
  timing files, the companion's journal), redacted, into the UTC day's dir <root>/<YYYY-MM-DD>/raw/<log>/<NNNNNN>_<UTC><ext>
  (never an existing name), with <day>/manifest.sha256 growing;
- every --sample-s: the overlay and session samples into <day>/samples/*.jsonl, and the recovery log's new rows: each
  `session_ended` schedules that session's summary row 90 s later into <root>/sessions.jsonl (diag_read's reader over
  the live logs; G4-S4's columns, the slot map, the restarts and their triggers);
- retention, the ONE deletion this tool makes: at the start and at each UTC date change, a dir directly under the
  root named YYYY-MM-DD (a real dir, not a symlink) whose date is more than 30 days before today is removed whole;
  one row per removal in <root>/retention.jsonl. Nothing else is deleted;
- <root>/status.txt (one line), <root>/STOP (touch to end), <root>/state.json (the tails' positions, so a restart of
  this unit resumes). No cap: it runs until STOP or the unit stops. No stream, no restart, no adb, no game; it holds
  no file open between steps. The root may not be inside the repo.
Reuses B30's redactor, tails and readers (tools/trip_log_keeper.py must stay in the tree).
Design: docs/memory/evidence/b36_2026-10-31/design_written_before_code.md (hashed before this code).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trip_log_keeper as tlk  # noqa: E402
import diag_read  # noqa: E402

REPO = tlk.REPO
DIAG_ROOT = Path.home() / "privyhub_diag"
EXTRA_TOP_TAILS = ["vod_client.jsonl", "vod_range.jsonl"]       # B35's rows
RETAIN_DAYS = 30
SUMMARY_DELAY_S = 90.0
SUMMARY_LOOKBACK_H = 6
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def day_of(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")


def retention(root: Path, now: float, days: int = RETAIN_DAYS) -> list[dict[str, Any]]:
    """Remove whole day-dirs older than `days` directly under root. Returns one row per removal."""
    root = Path(root)
    today = datetime.fromtimestamp(now, timezone.utc).date()
    out = []
    if not root.is_dir():
        return out
    for name in sorted(os.listdir(root)):
        p = root / name
        if not DAY.match(name) or p.is_symlink() or not p.is_dir():
            continue
        try:
            d = datetime.strptime(name, "%Y-%m-%d").date()
        except ValueError:
            continue
        if d < today - timedelta(days=days):
            n = sum(1 for x in p.rglob("*") if x.is_file())
            shutil.rmtree(p)
            out.append({"at_utc": tlk.utc(now), "removed": name, "files": n, "rule": f"older than {days} days"})
    if out:
        with open(root / "retention.jsonl", "a") as fh:
            for r in out:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
    return out


def live_summary(logs_root: Path, root: Path, end_utc: str) -> dict[str, Any]:
    """The sessions.jsonl row for the session whose end is `end_utc`, from the live logs (read-only)."""
    end = diag_read.ts(end_utc)
    logs = diag_read.Logs()
    logs.add_live(logs_root, root)
    an = diag_read.Analysis(logs, end - timedelta(hours=SUMMARY_LOOKBACK_H), end + timedelta(seconds=SUMMARY_DELAY_S + 60))
    for s in an.sessions:
        if s["end"] is not None and abs((s["end"] - end).total_seconds()) < 1.0:
            return an.session_row(s)
    return {"end_utc": end_utc, "error": "session not found"}


class DiagKeeper(tlk.Keeper):
    def __init__(self, root: Path, logs_root: Path = REPO / "logs", summary: Callable[[str], dict[str, Any]] | None = None,
                 **kw: Any) -> None:
        self.root = Path(root).expanduser().resolve()
        if self.root == REPO or REPO in self.root.parents:
            raise SystemExit(f"the diag root may not be inside the repo: {self.root}")
        self.root.mkdir(parents=True, exist_ok=True)
        super().__init__(self.root, float("inf"), 0.0, logs_root=logs_root, **kw)
        self._summary = summary if summary is not None else (lambda end: live_summary(self.logs, self.root, end))
        self.day = ""
        self._roll(self.clock())
        self.rec_tail: tlk.Tail | None = None
        self.pending: list[tuple[float, str]] = []
        self.summaries = 0
        self.removed = 0
        self.term = False                                       # SIGTERM (the unit stopping): end with a final copy

    # -- the day-dir -----------------------------------------------------------------------------------------------
    def _roll(self, now: float) -> bool:
        d = day_of(now)
        if d == self.day:
            return False
        self.day = d
        self.out = self.root / d
        self.raw, self.samples = self.out / "raw", self.out / "samples"
        self.out.mkdir(parents=True, exist_ok=True)
        return True

    def stop_file(self) -> Path:
        return self.root / "STOP"

    def why_end(self) -> str | None:
        if self.term:
            return "SIGTERM"
        return "STOP" if self.stop_file().exists() else None

    def _status(self) -> None:
        line = (f"{tlk.utc(self.clock())} | {self.phase} | copies {self.copies}, last {self.last_copy} | samples "
                f"{self.samples_n}, last {self.last_sample} | sessions {self.summaries} | day {self.day} | "
                f"retention {RETAIN_DAYS} d, removed {self.removed} | stop: touch {self.stop_file()}\n")
        tmp = self.root / "status.txt.new"
        tmp.write_text(line)
        tmp.replace(self.root / "status.txt")

    # -- the positions across a restart of this unit ------------------------------------------------------------------
    def _save_state(self) -> None:
        st = {"tails": {k: {"ino": t.ino, "off": t.off} for k, t in self.tails.items()},
              "seen": {k: sorted(v) for k, v in self.seen.items()}, "jsince": self.jsince,
              "pending": self.pending,
              "rec": {"ino": self.rec_tail.ino, "off": self.rec_tail.off} if self.rec_tail else None}
        tmp = self.root / "state.json.new"
        tmp.write_text(json.dumps(st, sort_keys=True))
        tmp.replace(self.root / "state.json")

    def begin(self) -> None:
        super().begin()
        for n in EXTRA_TOP_TAILS:
            self.tails[n] = tlk.Tail(self.logs / n, None)
        self.rec_tail = tlk.Tail(self.games / "native_stream_recovery.log", self.arch)
        try:
            st = json.loads((self.root / "state.json").read_text())
        except (OSError, ValueError):
            return
        for k, v in (st.get("tails") or {}).items():
            t = self.tails.get(k)
            if t is None and k.startswith("games/") and tlk.GAME_LOG.match(k[len("games/"):]):
                t = self.tails[k] = tlk.Tail(self.games / k[len("games/"):], None)
            if t is not None and v.get("ino") is not None and t.ino == v["ino"] and v.get("off", 0) <= self._size(t):
                t.off = v["off"]                               # the same file: resume where the last run stopped
        for k, v in (st.get("seen") or {}).items():
            self.seen.setdefault(k, set()).update(v)
        if st.get("jsince"):
            self.jsince = min(int(st["jsince"]), self.jsince or int(st["jsince"]))
        r = st.get("rec") or {}
        if r.get("ino") is not None and self.rec_tail.ino == r["ino"] and r.get("off", 0) <= self._size(self.rec_tail):
            self.rec_tail.off = r["off"]
        self.pending = [tuple(x) for x in st.get("pending") or []]

    @staticmethod
    def _size(t: tlk.Tail) -> int:
        try:
            return t.live.stat().st_size
        except OSError:
            return 0

    # -- the steps ------------------------------------------------------------------------------------------------------
    def copy(self, final: bool = False) -> dict[str, Any]:
        row = super().copy(final)
        self._save_state()
        return row

    def sample(self) -> None:
        super().sample()
        self.watch()

    def watch(self) -> None:
        """New recovery rows: each session_ended schedules its summary; due summaries are written."""
        now = self.clock()
        if self.rec_tail is not None:
            try:
                data, _ = self.rec_tail.step()
            except OSError:
                data = b""
            for r in diag_read.rows(data):
                if r.get("event") == "session_ended" and r.get("at_utc"):
                    self.pending.append((now + SUMMARY_DELAY_S, r["at_utc"]))
        due = [p for p in self.pending if p[0] <= now]
        self.pending = [p for p in self.pending if p[0] > now]
        for _, end in due:
            try:
                row = dict(self._summary(end))
            except Exception as exc:
                row = {"end_utc": end, "error": type(exc).__name__}
            row = {"written_at_utc": tlk.utc(now), **row}
            text, _ = self.redactor.apply(json.dumps(row, sort_keys=True, default=str))
            with open(self.root / "sessions.jsonl", "a") as fh:
                fh.write(text + "\n")
            self.summaries += 1
        if due:
            self._save_state()

    def run(self, once: bool = False) -> str:
        self.removed += len(retention(self.root, self.clock()))
        self.begin()
        self.phase = "running"
        next_copy, next_sample = self.clock() + self.copy_s, self.clock()
        why = None
        while True:
            why = self.why_end()
            if why:
                break
            now = self.clock()
            if self._roll(now):
                self.removed += len(retention(self.root, now))
            if now >= next_sample:
                self.sample()
                next_sample = now + self.sample_s
            if now >= next_copy:
                self.copy()
                next_copy = now + self.copy_s
            self._status()
            if once:
                why = "once"
                break
            self.sleep(max(0.5, min(next_copy, next_sample) - self.clock()))
        self._roll(self.clock())
        self.copy(final=True)
        self.phase = f"done ({why})"
        self._status()
        return why


UNIT_TEXT = """[Unit]
Description=PrivyHub diagnostics keeper (B36; read-only copies of the hub's logs into ~/privyhub_diag, 30-day retention)
After=privyhub-companion.service

[Service]
Type=simple
WorkingDirectory=%h/Projects/onn-stream-test
ExecStart=/usr/bin/python3 -B %h/Projects/onn-stream-test/tools/diag_keeper.py
Restart=on-failure
RestartSec=30
Nice=10

[Install]
WantedBy=default.target
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=DIAG_ROOT)
    ap.add_argument("--copy-s", type=float, default=300.0)
    ap.add_argument("--sample-s", type=float, default=60.0)
    ap.add_argument("--once", action="store_true", help="one sample and one copy, then stop (a check)")
    ap.add_argument("--unit", action="store_true", help="print the user unit's text and exit")
    a = ap.parse_args(argv)
    if a.unit:
        print(UNIT_TEXT, end="")
        return 0
    holder: list[DiagKeeper] = []

    def nap(s: float) -> None:                                   # sleeps in 1-s pieces so a SIGTERM ends it promptly
        end = time.time() + s
        while time.time() < end and not (holder and holder[0].term):
            time.sleep(min(1.0, max(0.0, end - time.time())))

    k = DiagKeeper(a.root, copy_s=a.copy_s, sample_s=a.sample_s, sleep=nap)
    holder.append(k)
    signal.signal(signal.SIGTERM, lambda *_: setattr(k, "term", True))
    why = k.run(once=a.once)
    print(f"diag keeper: done ({why}); {k.copies} copies, {k.samples_n} samples, {k.summaries} sessions; {k.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
