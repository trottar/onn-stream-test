#!/usr/bin/env python3
"""B36: the one-line read -- per-session and per-10-min tables, every restart / rewind / pause with its cause, and the
+-60-s per-second view, from the diagnostics keeper's copies (read-only).

    python3 tools/diag_read.py "last night"
    python3 tools/diag_read.py today
    python3 tools/diag_read.py "2026-10-30 21:00..05:00"            (UTC; an end not after the start is the next day)
    python3 tools/diag_read.py "2026-10-30 21:00..2026-10-31 06:10"
    python3 tools/diag_read.py trip                                 (the trip keeper's dir, its whole span)
        [--source DIR ...] [--live] [--root ~/privyhub_diag] [--around HH:MM:SS ...] [--around-saves] [--out FILE]

Writes one Markdown file under docs/memory/evidence/reads/ (never an existing name) and prints its path.
The logic is TRIP-R2's trip_r2_read.py (docs/memory/evidence/trip_r2_2026-10-31/scripts/), copied and parameterised:
UX-R3's hitch definition, unchanged -- a UTC second is a hitch second if
  R  the heartbeat interval ending in it rendered < 50 fps;
  C  a host control gap >= 250 ms starts in it (not the user's own exit);
  G  an output gap >= 200 ms is recorded in it (the ladder sample's output_gap_ms, or a client-report top-16 gap
     placed by the client's elapsed clock);
  L  the heartbeat interval ending in it lost >= 30 packets after FEC.
Sources are opened for reading only. Titles appear as class + short tag only.
Design: docs/memory/evidence/b36_2026-10-31/design_written_before_code.md (hashed before this code).
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
TRIP_DIR = REPO / "docs/memory/evidence/trip_2026-10-30"
READS = REPO / "docs/memory/evidence/reads"
DIAG_ROOT = Path.home() / "privyhub_diag"
EPOCH = datetime(1970, 1, 1)
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GAME_LOG = re.compile(r"^(\d{8})-(\d{6})-game_([a-z0-9]+)_([0-9a-f]{4})[0-9a-f]*\.log$")
# B50: a PS2 session's game log (B49: no id or title in its name); its sessions read system `ps2`, core `pcsx2`
PS2_LOG = re.compile(r"^(\d{8})-(\d{6})-ps2\.log$")
PS2_CORE = "pcsx2"


def is_game_log(name: str) -> bool:
    return bool(GAME_LOG.match(name) or PS2_LOG.match(name))


# B53: PCSX2's own log per launch (`<UTC launch>-pcsx2.log`, live under data/games/ps2/logs/, the keeper's raw/ps2logs__*)
PCSX2_LOG = re.compile(r"^(\d{8}T\d{6}Z)-pcsx2\.log$")
PCSX2_LINE = re.compile(r"^\[\s*(\d+(?:\.\d+)?)\]\s?(.*)$")
PCSX2_COUNTS = {
    "read_errors": re.compile(r"Read Abort|CDVD read err|READ ERROR|Read Bad Parameter|Read when CD Error"),
    "invalid_binding": re.compile(r"Invalid binding:"),
    "card_formatted": re.compile(r"McdSlot \d+ \[File\].*\[8 MB, Formatted\]"),
    "card_unformatted": re.compile(r"McdSlot \d+ \[File\].*UNFORMATTED"),
    "tlb_miss": re.compile(r"TLB Miss"),
    "state_saved": re.compile(r"Saved state to slot \d+"),
    "state_loaded": re.compile(r"Loaded state from slot \d+"),
    "elf": re.compile(r"ELF Loading:"),
}


def pcsx2_events(name: str, data: bytes) -> list[tuple[datetime, str]]:
    """(UTC, kind) for each counted line of one per-launch PCSX2 log (the name's time + the line's seconds)."""
    m = PCSX2_LOG.match(name)
    if not m:
        return []
    t0 = datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ")
    out = []
    for line in data.decode("utf-8", "replace").splitlines():
        lm = PCSX2_LINE.match(line)
        if not lm:
            continue
        for kind, rx in PCSX2_COUNTS.items():
            if rx.search(lm.group(2)):
                out.append((t0 + timedelta(seconds=float(lm.group(1))), kind))
    return out

# the trip's known titles (game id prefix -> class + tag); others read "<SYSTEM> <4-hex>"
TAGS = {"04ff": "PS1 platformer", "ee3b": "SNES action-adventure", "2ef9": "PS1 first-person RPG",
        "3699": "PS1 football (Blitz)", "7bf5": "PS1 brawler", "6d53": "PS1 kart racer", "33df": "PS1 golf",
        "9f2b": "PS1 hockey A", "e2cd": "PS1 hockey B"}
CORES = {"snes": "snes9x", "ps1": "beetle-psx-hw"}

# the log names (as in logs/games/ or logs/) the reader uses
LOGS = {"rec": "native_stream_recovery.log", "lad": "adaptive_bitrate_shadow.jsonl", "hb": "native_stream_heartbeat.log",
        "gaps": "native_stream_ctrl_gaps.log", "fsz": "native_frame_sizes.jsonl", "host": "host_resource_samples.jsonl",
        "wan": "wan_sessions.jsonl", "vod_client": "vod_client.jsonl", "vod_range": "vod_range.jsonl"}

# ---------------------------------------------------------------- time


def ts(s: str) -> datetime:
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).replace(tzinfo=None)


def sec(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S")


def hms(t: datetime) -> str:
    return t.strftime("%H:%M:%S")


def unix(t: datetime) -> float:
    return (t - EPOCH).total_seconds()


def local_to_utc(naive: datetime, tz: tzinfo | None) -> datetime:
    """A naive local time -> naive UTC (tz None: the hub's own zone, with its DST rules for that date)."""
    aware = naive.astimezone(timezone.utc) if tz is None else naive.replace(tzinfo=tz).astimezone(timezone.utc)
    return aware.replace(tzinfo=None)


def utc_to_local(t: datetime, tz: tzinfo | None) -> datetime:
    aware = t.replace(tzinfo=timezone.utc)
    return (aware.astimezone() if tz is None else aware.astimezone(tz)).replace(tzinfo=None)


def parse_range(text: str, now: datetime, tz: tzinfo | None = None) -> tuple[str, datetime | None, datetime | None]:
    """(label, start UTC, end UTC); `trip` gives (trip, None, None): the span comes from the trip dir."""
    s = " ".join(text.strip().lower().split())
    if s == "trip":
        return "trip", None, None
    if s == "today":
        loc = utc_to_local(now, tz)
        return "today", local_to_utc(loc.replace(hour=0, minute=0, second=0, microsecond=0), tz), now
    if s == "last night":
        loc = utc_to_local(now, tz).replace(hour=0, minute=0, second=0, microsecond=0)
        return ("last-night", local_to_utc(loc - timedelta(days=1) + timedelta(hours=17), tz),
                local_to_utc(loc + timedelta(hours=8), tz))
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})[ t](\d{1,2}:\d{2}(?::\d{2})?)\s*\.\.\s*(?:(\d{4}-\d{2}-\d{2})[ t])?(\d{1,2}:\d{2}(?::\d{2})?)", s)
    if not m:
        raise ValueError(f"not a range: {text!r} (last night | today | trip | YYYY-MM-DD HH:MM..[YYYY-MM-DD ]HH:MM)")

    def at(d: str, hm: str) -> datetime:
        return datetime.strptime(f"{d} {hm}" + (":00" if hm.count(":") == 1 else ""), "%Y-%m-%d %H:%M:%S")

    a = at(m.group(1), m.group(2))
    b = at(m.group(3) or m.group(1), m.group(4))
    if not m.group(3) and b <= a:
        b += timedelta(days=1)
    if b <= a:
        raise ValueError("the end is not after the start")
    return f"{a.strftime('%Y%m%dT%H%M')}-{b.strftime('%Y%m%dT%H%M')}", a, b

# ---------------------------------------------------------------- the sources (read-only)


def rows(data: bytes) -> list[dict[str, Any]]:
    out = []
    for line in data.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                out.append(r)
    return out


class Logs:
    """Every log's text joined in order, from keeper-shaped dirs, TRIP-R2's copies/ shape, or the live logs/."""

    def __init__(self) -> None:
        self.data: dict[str, bytes] = defaultdict(bytes)
        self.reports: list[dict[str, Any]] = []
        self.game_logs: list[str] = []          # game log file names (they carry the launch time and the title)
        self.pcsx2_logs: dict[str, bytes] = defaultdict(bytes)   # B53: per-launch PCSX2 logs, by file name
        self.overlay: list[dict[str, Any]] = []
        self.sources: list[str] = []

    # -- a keeper dir (B30's trip dir, or one of diag_keeper's day-dirs): raw/<key>/<NNNNNN>_<UTC><ext>
    def add_keeper_dir(self, d: Path) -> None:
        d = Path(d)
        raw = d / "raw"
        self.sources.append(f"keeper dir {d.name}")
        names = {v: k for k, v in LOGS.items()}
        if raw.is_dir():
            for sub in sorted(os.listdir(raw)):
                p = raw / sub
                if not p.is_dir():
                    continue
                base = sub[len("games__"):] if sub.startswith("games__") else sub
                files = sorted(f for f in os.listdir(p) if (p / f).is_file())
                # B53: the keeper's copies of PCSX2's per-launch logs
                if sub.startswith("ps2logs__") and PCSX2_LOG.match(sub[len("ps2logs__"):]):
                    for f in files:
                        self.pcsx2_logs[sub[len("ps2logs__"):]] += (p / f).read_bytes()
                    continue
                if base == "decoder_sessions":
                    for f in files:
                        self._report((p / f).read_bytes())
                elif is_game_log(base):
                    if base not in self.game_logs:
                        self.game_logs.append(base)
                elif base in names:
                    for f in files:
                        self.data[base] += (p / f).read_bytes()
        ov = d / "samples" / "overlay.jsonl"
        if ov.is_file():
            self.overlay += rows(ov.read_bytes())

    # -- TRIP-R2's copies/ shape (the joined logs; game_logs/; decoder_sessions/)
    def add_copies_dir(self, d: Path) -> None:
        d = Path(d)
        self.sources.append(f"copies dir {d.name}")
        for name in LOGS.values():
            if (d / name).is_file():
                self.data[name] += (d / name).read_bytes()
        for f in sorted(glob.glob(str(d / "decoder_sessions" / "*.json"))):
            self._report(Path(f).read_bytes())
        for f in sorted(os.listdir(d / "game_logs")) if (d / "game_logs").is_dir() else []:
            if is_game_log(f) and f not in self.game_logs:
                self.game_logs.append(f)
        if (d / "overlay.jsonl").is_file():
            self.overlay += rows((d / "overlay.jsonl").read_bytes())

    # -- the live logs (what the keeper's per-session summary reads)
    def add_live(self, logs_root: Path, diag_root: Path | None = None) -> None:
        logs_root = Path(logs_root)
        games, arch = logs_root / "games", logs_root / "games" / "stream_log_archive"
        self.sources.append("live logs")
        for name in LOGS.values():
            top = name in ("wan_sessions.jsonl", "vod_client.jsonl", "vod_range.jsonl")
            for p in ([] if top else [arch / f"{name}.{i}" for i in (3, 2, 1)]) + [(logs_root if top else games) / name]:
                try:
                    self.data[name] += p.read_bytes()
                except OSError:
                    continue
        # B53: PCSX2's per-launch logs beside the repo's logs (data/games/ps2/logs/)
        p2 = logs_root.parent / "data" / "games" / "ps2" / "logs"
        for f in sorted(os.listdir(p2)) if p2.is_dir() else []:
            if PCSX2_LOG.match(f):
                try:
                    self.pcsx2_logs[f] = (p2 / f).read_bytes()
                except OSError:
                    continue
        d = games / "decoder_sessions"
        for f in sorted(os.listdir(d)) if d.is_dir() else []:
            try:
                self._report((d / f).read_bytes())
            except OSError:
                continue
        for f in sorted(os.listdir(games)) if games.is_dir() else []:
            if is_game_log(f) and f not in self.game_logs:
                self.game_logs.append(f)
        if diag_root is not None and Path(diag_root).is_dir():
            for day in sorted(os.listdir(diag_root)):
                ov = Path(diag_root) / day / "samples" / "overlay.jsonl"
                if DAY.match(day) and ov.is_file():
                    self.overlay += rows(ov.read_bytes())

    def _report(self, data: bytes) -> None:
        try:
            d = json.loads(data.decode("utf-8", errors="replace"))
        except ValueError:
            return
        if isinstance(d, dict) and d.get("received_at_utc") and isinstance(d.get("report"), dict):
            self.reports.append(d)

    def get(self, key: str) -> list[dict[str, Any]]:
        return rows(self.data.get(LOGS[key], b""))


def keeper_dirs_for(root: Path, a: datetime, b: datetime) -> list[Path]:
    """The diag root's day-dirs that overlap [a, b] (+-1 day: a chunk is named by its copy time)."""
    out = []
    if Path(root).is_dir():
        for day in sorted(os.listdir(root)):
            if not DAY.match(day) or not (Path(root) / day).is_dir():
                continue
            d = datetime.strptime(day, "%Y-%m-%d")
            if a - timedelta(days=1) <= d <= b + timedelta(days=1):
                out.append(Path(root) / day)
    return out

# ---------------------------------------------------------------- the analysis (TRIP-R2's, parameterised)


class Analysis:
    def __init__(self, logs: Logs, t0: datetime, t1: datetime, tz: tzinfo | None = None,
                 tags: dict[str, str] | None = None) -> None:
        self.t0, self.t1, self.tz = t0, t1, tz
        self.tags = TAGS if tags is None else tags
        w = self.inwin
        self.rec = [r for r in logs.get("rec") if r.get("at_utc") and w(ts(r["at_utc"]))]
        self.lad = [r for r in logs.get("lad") if r.get("at_utc") and w(ts(r["at_utc"]))]
        self.hb = [r for r in logs.get("hb") if r.get("received_at_utc") and w(ts(r["received_at_utc"]))]
        self.gaps = [r for r in logs.get("gaps") if r.get("start_utc") and w(ts(r["start_utc"]))]
        self.fsz = {r["at_utc"][:19]: r for r in logs.get("fsz") if r.get("at_utc") and w(ts(r["at_utc"]))}
        self.ovl = [r for r in logs.overlay if r.get("at_utc") and w(ts(r["at_utc"]))]
        self.wan = logs.get("wan")
        self.vod_client = [r for r in logs.get("vod_client") if self._t(r) and w(self._t(r))]
        self.vod_range = [r for r in logs.get("vod_range") if self._t(r) and w(self._t(r))]
        self.reports = sorted((d for d in logs.reports if w(ts(d["received_at_utc"]))),
                              key=lambda d: d["received_at_utc"])
        self.launches = []
        for f in sorted(logs.game_logs):
            m = GAME_LOG.match(f)
            if m is None:                                   # B50: a PS2 launch
                m2 = PS2_LOG.match(f)
                if m2 is None:
                    continue
                t = local_to_utc(datetime.strptime(m2.group(1) + m2.group(2), "%Y%m%d%H%M%S"), tz)
                self.launches.append((t, "PS2", PS2_CORE))
                continue
            t = local_to_utc(datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S"), tz)
            tag = self.tags.get(m.group(4), f"{m.group(3).upper()} {m.group(4)}")
            self.launches.append((t, tag, CORES.get(m.group(3), m.group(3))))
        self.sources = list(logs.sources)
        # B53: PCSX2's per-launch logs: the launch times and every counted line (UTC)
        self.pcsx2_launches = sorted(datetime.strptime(PCSX2_LOG.match(n).group(1), "%Y%m%dT%H%M%SZ")
                                     for n in logs.pcsx2_logs)
        self.pcsx2 = sorted(ev for n, data in logs.pcsx2_logs.items() for ev in pcsx2_events(n, data))
        self._sessions()
        self._seconds()

    @staticmethod
    def _t(r: dict[str, Any]) -> datetime | None:
        for k in ("at_utc", "received_at_utc", "start_utc"):
            if r.get(k):
                try:
                    return ts(r[k])
                except ValueError:
                    return None
        return None

    def inwin(self, t: datetime) -> bool:
        return self.t0 <= t < self.t1

    def title_at(self, t: datetime) -> tuple[str, str]:
        cur = None
        for lt, tag, core in self.launches:
            if lt <= t + timedelta(seconds=60):
                cur = (tag, core)
        return cur or ("?", "?")

    # -- client sessions (the recovery log)
    def _sessions(self) -> None:
        self.sessions: list[dict[str, Any]] = []
        cur = None
        last_cfg = None
        ps2_at = None                                       # B50: the newest `ps2_session` row (the stream's start)
        for r in self.rec:
            t, ev = ts(r["at_utc"]), r.get("event")
            if ev == "ps2_session":
                ps2_at = t
            if ev == "remote_config":
                last_cfg = r
            elif ev == "session_started":
                cur = {"start": t, "class": (last_cfg or {}).get("class"), "events": [], "end": None, "end_kind": None}
                # B50: the title's system node: a PS2 stream start just before this release makes it a PS2 session
                if ps2_at is not None and timedelta(0) <= t - ps2_at <= timedelta(seconds=120):
                    cur["ps2"] = True
                ps2_at = None
                self.sessions.append(cur)
            elif cur is not None:
                cur["events"].append(r)
                if ev == "session_end_bye":
                    cur["bye"] = True
                if ev == "session_ended" and cur["end"] is None:
                    cur["end"] = t
                if ev == "restart_fast" and cur.get("end_kind") is None and cur["end"] and (t - cur["end"]).total_seconds() < 2:
                    cur["end_kind"] = "client restart (restart_fast)"
                if ev == "gave_up_saved":
                    cur["end_kind"] = "link loss: gave up, saved"
                    cur["end"] = cur["end"] or t
                if ev == "ended_after_link_loss":
                    cur["end"] = cur["end"] or t
        for s in self.sessions:
            if s["end_kind"] is None:
                s["end_kind"] = "user exit (bye)" if s.get("bye") else ("open" if s["end"] is None else "?")
            s["tag"], s["core"] = self.title_at(s["start"])
            if s.get("ps2"):                                # B50: the session's own row wins over the launch order
                s["tag"], s["core"] = "PS2", PS2_CORE
        self.restarts = [r for r in self.rec if r.get("event") == "restart_fast"]
        self.transitions = [r for r in self.lad if r.get("event") == "transition"]
        # B32-host writes `in_place` on the step's `transition_done` row (adaptive_bitrate_live), not on `transition`:
        # carry it onto the transition it closes (the first done row within 10 s after it)
        dones = [r for r in self.lad if r.get("event") == "transition_done" and "in_place" in r]
        for tr in self.transitions:
            if "in_place" not in tr:
                d = next((d for d in dones if timedelta(0) <= ts(d["at_utc"]) - ts(tr["at_utc"]) <= timedelta(seconds=10)), None)
                if d is not None:
                    tr["in_place"] = d["in_place"]
        self.stalls = [r for r in self.rec if r.get("event") == "client_stall"]
        self.segs: list[list[dict[str, Any]]] = []
        for r in self.hb:
            if "sequence" not in r or "elapsed_ms" not in r:
                continue
            if not self.segs or r["sequence"] <= self.segs[-1][-1]["sequence"]:
                self.segs.append([])
            self.segs[-1].append(r)

    def seg_for(self, s: dict[str, Any]) -> list[dict[str, Any]]:
        best = None
        for g in self.segs:
            a, b = ts(g[0]["received_at_utc"]), ts(g[-1]["received_at_utc"])
            if a <= (s["end"] or a) and b >= s["start"] - timedelta(seconds=10):
                ov = (min(b, s["end"] or b) - max(a, s["start"])).total_seconds()
                if best is None or ov > best[0]:
                    best = (ov, g)
        return best[1] if best else []

    @staticmethod
    def offset(g: list[dict[str, Any]]) -> float | None:
        """UTC - client elapsed, the median over the segment."""
        return statistics.median([unix(ts(r["received_at_utc"])) - r["elapsed_ms"] / 1000 for r in g]) if g else None

    def report_for(self, s: dict[str, Any]) -> dict[str, Any] | None:
        best = None
        for d in self.reports:
            rt = ts(d["received_at_utc"])
            if s["end"] and abs((rt - s["end"]).total_seconds()) < 5:
                best = d
        return best

    def rtt_for(self, s: dict[str, Any]) -> tuple[Any, Any]:
        """The WAN row closed between this session's end and the next session's start (G5-S1's close)."""
        if not s["end"]:
            return None, None
        i = self.sessions.index(s)
        a = unix(s["end"]) - 30
        nxt = self.sessions[i + 1]["start"] if i + 1 < len(self.sessions) else s["end"] + timedelta(hours=2)
        b = unix(nxt) + 5
        for r in self.wan:
            if a <= (r.get("closed_unix_s") or 0) <= b:
                v = ((r.get("measures") or {}).get("rtt_ms") or {}).get("value") or {}
                return v.get("p50"), v.get("p95")
        return None, None

    # -- per-second evidence
    def _seconds(self) -> None:
        hitch: dict[str, set[str]] = defaultdict(set)
        row: dict[str, dict[str, Any]] = defaultdict(dict)
        for g in self.segs:
            prev = None
            for r in g:
                k = sec(ts(r["received_at_utc"]))
                if prev is not None:
                    dt = (r["elapsed_ms"] - prev["elapsed_ms"]) / 1000
                    if dt > 0:
                        def d(f: str) -> int:
                            return (r.get(f) or 0) - (prev.get(f) or 0)
                        fps = d("rendered_frames") / dt
                        lost = d("lost_packets")
                        row[k].update(fps=round(fps, 1), lost=lost, rssi=r.get("link_rssi_dbm"),
                                      underruns=d("audio_underruns"), starv=d("audio_prolonged_starvation_events"),
                                      resync=d("stream_resyncs"), out_age=r.get("last_output_age_ms"))
                        if r.get("pad_slots"):
                            row[k]["pad_slots"] = r["pad_slots"]
                        if fps < 50:
                            hitch[k].add("R")
                        if lost >= 30:
                            hitch[k].add("L")
                prev = r
        self.bye_times = [ts(r["at_utc"]) for r in self.rec if r.get("event") == "session_end_bye"]
        for gp in self.gaps:
            a, b = ts(gp["start_utc"]), ts(gp.get("end_utc") or gp["start_utc"])
            user = any(a - timedelta(seconds=1) <= bt <= b for bt in self.bye_times)
            k = sec(a)
            row[k]["ctrl_gap_ms"] = max(row[k].get("ctrl_gap_ms", 0), gp.get("gap_ms") or 0)
            row[k]["ctrl_gap_user"] = user
            if not user:
                hitch[k].add("C")
        for r in self.lad:
            k = r["at_utc"][:19]
            if r.get("event") == "sample":
                row[k].update(rung=r.get("stream_kbps"), lstate=r.get("state"), ogap=r.get("output_gap_ms"),
                              wfi=r.get("waiting_for_idr"))
                if (r.get("output_gap_ms") or 0) >= 200:
                    hitch[k].add("G")
            elif r.get("event") in ("transition", "session_ended_reset"):
                row[k].setdefault("ladder_ev", []).append(
                    r["event"] + (f" {r.get('from_kbps')}->{r.get('to_kbps')}" + (" in place" if r.get("in_place") else "")
                                  if r["event"] == "transition" else ""))
        for r in self.rec:
            k = r["at_utc"][:19]
            row[k].setdefault("rec", []).append(r.get("event", "?") + (f"({r.get('trigger')})" if r.get("trigger") else "")
                                                + (f"[{r.get('why')}]" if r.get("why") else ""))
        self.report_gaps: list[tuple[datetime, Any, dict[str, Any]]] = []
        self.report_disc: list[tuple[datetime, Any, dict[str, Any]]] = []
        for s in self.sessions:
            d = self.report_for(s)
            off = self.offset(self.seg_for(s))
            if not d or off is None:
                continue
            rp = d["report"]
            for x in rp.get("slow_events_top_gap", []) or []:
                t = EPOCH + timedelta(seconds=off + x[0] / 1000)
                self.report_gaps.append((t, x[6], s))
                if x[6] >= 200:
                    hitch[sec(t)].add("G")
                    row[sec(t)]["report_gap_ms"] = max(row[sec(t)].get("report_gap_ms", 0), x[6])
            for x in rp.get("stream_discontinuities", []) or []:
                t = EPOCH + timedelta(seconds=off + x["elapsed_ms"] / 1000)
                self.report_disc.append((t, x.get("type"), s))
                row[sec(t)]["disc"] = x.get("type")
        self.hitch, self.row = hitch, row

    # -- counts for [a, b)
    def summarize(self, a: datetime, b: datetime) -> dict[str, Any]:
        hitch, row = self.hitch, self.row
        out: dict[str, Any] = {}
        hs = [k for k in hitch if a <= ts(k) < b]
        out["hitch_s"] = len(hs)
        out["hitch_by"] = {c: sum(1 for k in hs if c in hitch[k]) for c in "RCGL"}
        gs = [g for g in self.gaps if a <= ts(g["start_utc"]) < b]
        out["silences"] = sum(1 for g in gs if not any(ts(g["start_utc"]) - timedelta(seconds=1) <= bt <= ts(g.get("end_utc") or g["start_utc"])
                                                       for bt in self.bye_times))
        out["silences_user"] = len(gs) - out["silences"]
        out["max_silence_ms"] = max([g.get("gap_ms") or 0 for g in gs], default=0)
        lost = und = starv = res = 0
        fpsl: list[float] = []
        rssi: list[int] = []
        for k, v in row.items():
            if a <= ts(k) < b and "fps" in v:
                lost += v["lost"]; und += v["underruns"]; starv += v["starv"]; res += v["resync"]
                fpsl.append(v["fps"])
                if v.get("rssi") is not None:
                    rssi.append(v["rssi"])
        out.update(lost=lost, underruns=und, starvation=starv, resyncs=res,
                   fps_med=round(statistics.median(fpsl), 1) if fpsl else None,
                   fps_min=round(min(fpsl), 1) if fpsl else None,
                   rssi=f"{min(rssi)}..{max(rssi)}" if rssi else "")
        out["stream_s"] = len({k for k, v in row.items() if a <= ts(k) < b and "fps" in v}) * 2
        trs = [r for r in self.transitions if a <= ts(r["at_utc"]) < b]
        out["transitions"] = [f"{hms(ts(r['at_utc']))} {r.get('from_kbps')}->{r.get('to_kbps')}" + (" in place" if r.get("in_place") else "")
                              for r in trs]
        out["stalls"] = [f"{hms(ts(r['at_utc']))} {r.get('age_ms')}ms" for r in self.stalls if a <= ts(r["at_utc"]) < b]
        out["restarts"] = [hms(ts(r["at_utc"])) for r in self.restarts if a <= ts(r["at_utc"]) < b]
        ev = [r for r in self.rec if a <= ts(r["at_utc"]) < b]
        out["pauses"] = [f"{hms(ts(r['at_utc']))} {r.get('trigger')}" for r in ev if r.get("event") == "desync_pause"]
        out["holds"] = sum(1 for r in ev if str(r.get("event", "")).startswith("input_hold"))
        out["rewinds"] = [f"{hms(ts(r['at_utc']))} {r.get('method')}" + (f" ({r['why']})" if r.get("why") else "")
                          for r in ev if r.get("event") == "input_release"]
        out["surface_lost"] = [r for r in ev if r.get("event") == "surface_lost"]
        out["pad_slots"] = [r for r in ev if r.get("event") == "pad_slots"]
        out["byes"] = sum(1 for r in ev if r.get("event") == "session_end_bye")
        out["resets"] = sum(1 for r in self.lad if r.get("event") == "session_ended_reset" and a <= ts(r["at_utc"]) < b)
        rungs = sorted({v["rung"] for k, v in row.items() if a <= ts(k) < b and v.get("rung")})
        out["rungs"] = "/".join(map(str, rungs))
        return out

    # -- one session as a sessions.jsonl row (G4-S4's columns + B34's slots + the restarts and their triggers)
    def pcsx2_counts(self, s: dict[str, Any]) -> dict[str, int] | None:
        """B53: the counted PCSX2 lines from the previous session's end (or this launch) to this session's end."""
        launches = [t for t in self.pcsx2_launches if t <= s["start"] and s["start"] - t <= timedelta(hours=6)]
        if not launches:
            return None
        launch = launches[-1]
        ends = [x["end"] for x in self.sessions if x["end"] is not None and launch <= x["end"] < s["start"]]
        lo = max(ends) if ends else launch
        hi = (s["end"] or s["start"]) + timedelta(seconds=5)
        out = {k: 0 for k in PCSX2_COUNTS}
        for t, kind in self.pcsx2:
            if lo <= t < hi:
                out[kind] += 1
        return out

    @staticmethod
    def ps1_reference(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """B50: the PS1 sessions a comparison may use as its reference (a PS2 session never)."""
        return [r for r in rows if r.get("core") == CORES["ps1"] and r.get("system") != "ps2"]

    def session_row(self, s: dict[str, Any]) -> dict[str, Any]:
        end = s["end"] or s["start"]
        m = self.summarize(s["start"], end + timedelta(seconds=1))
        L = (end - s["start"]).total_seconds()
        p50, p95 = self.rtt_for(s)
        slot_map = None
        for r in reversed(m["pad_slots"]):
            slot_map = r.get("slots") or r.get("map") or r.get("pad_slots")
            break
        if slot_map is None:
            for k in sorted(self.row, reverse=True):
                if s["start"] <= ts(k) <= end and self.row[k].get("pad_slots"):
                    slot_map = self.row[k]["pad_slots"]
                    break
        players = (len(slot_map) if isinstance(slot_map, (dict, list)) else None) if slot_map is not None else None
        samples = [r for r in self.lad if r.get("event") == "sample" and s["start"] <= ts(r["at_utc"]) <= end]
        per10 = (L / 600.0) if L > 0 else None
        restarts = [self.restart_detail(r) for r in self.restarts
                    if s["start"] <= ts(r["at_utc"]) <= end + timedelta(seconds=2)]
        return {
            "start_utc": sec(s["start"]) + "Z", "end_utc": (sec(s["end"]) + "Z") if s["end"] else None,
            "length_s": int(L), "core": s["core"], "title": s["tag"], "players": players, "slot_map": slot_map,
            "path_class": s["class"], "rung_history": m["transitions"], "rungs": m["rungs"],
            "start_rung": samples[0].get("stream_kbps") if samples else None,
            "lost_post_fec": m["lost"], "rtt_p50_ms": p50, "rtt_p95_ms": p95,
            "rendered_fps_med": m["fps_med"], "rendered_fps_min": m["fps_min"], "resyncs": m["resyncs"],
            "pauses": m["pauses"], "holds": m["holds"], "stalls": m["stalls"], "rewinds": m["rewinds"],
            "restarts": restarts,
            # the client reports the cause of the restart that STARTED a session in that session's own report
            "restart_cause": (self.report_for(s) or {}).get("report", {}).get("restart_cause"),
            "surface_lost": [{k: v for k, v in r.items() if k != "schema"} for r in m["surface_lost"]],
            "end_kind": s["end_kind"], "resets": m["resets"],
            "hitch_s": m["hitch_s"], "hitch_by": m["hitch_by"],
            "hitch_s_per_10min": round(m["hitch_s"] / per10, 1) if per10 else None,
            # B50: a PS2 session says its system (other sessions' rows as before)
            **({"system": "ps2"} if s["core"] == PS2_CORE else {}),
            # B53: PCSX2's own log lines for this session, when its launch's log exists (no key otherwise)
            **({"pcsx2_log": c} if s["core"] == PS2_CORE and (c := self.pcsx2_counts(s)) is not None else {}),
            "silences": m["silences"], "silences_user": m["silences_user"],
            "silences_per_10min": round(m["silences"] / per10, 1) if per10 else None,
            "max_silence_ms": round(m["max_silence_ms"]), "underruns": m["underruns"], "starvation": m["starvation"],
            "rssi": m["rssi"],
        }

    # -- a client restart and its cause
    def restart_detail(self, r: dict[str, Any]) -> dict[str, Any]:
        tt = ts(r["at_utc"])
        sess = next((i for i, s in enumerate(self.sessions, 1)
                     if s["end"] and 0 <= (tt - s["end"]).total_seconds() < 2), None)
        if sess is None:
            sess = next((i for i, s in enumerate(self.sessions, 1) if s["start"] <= tt <= (s["end"] or tt)), None)
        before = [x for x in self.lad if x.get("event") == "sample" and x.get("stream_kbps") and ts(x["at_utc"]) < tt]
        after = [x for x in self.lad if x.get("event") == "sample" and x.get("stream_kbps") and ts(x["at_utc"]) > tt]
        ups = [x for x in self.transitions if ts(x["at_utc"]) <= tt and (x.get("to_kbps") or 0) > (x.get("from_kbps") or 0)]
        last_up = ups[-1] if ups else None
        in_sess = None
        if last_up is not None and sess is not None:
            in_sess = ts(last_up["at_utc"]) >= self.sessions[sess - 1]["start"]
        # the client reports a restart's cause in the report of the session it started (posted at that session's end)
        nxt_s = next((s for s in self.sessions if s["start"] >= tt - timedelta(seconds=1)), None)
        rep = self.report_for(nxt_s) if nxt_s is not None else None
        cause = rep["report"].get("restart_cause") if rep else None
        lost = [x for x in self.rec if x.get("event") == "surface_lost"
                and -15 <= (ts(x["at_utc"]) - tt).total_seconds() <= 5]
        sil = [g for g in self.gaps if -20 <= (ts(g["start_utc"]) - tt).total_seconds() <= 0
               and not any(ts(g["start_utc"]) - timedelta(seconds=1) <= bt <= ts(g.get("end_utc") or g["start_utc"]) for bt in self.bye_times)]
        st = [x for x in self.stalls if -20 <= (ts(x["at_utc"]) - tt).total_seconds() <= 0]
        title = self.sessions[sess - 1]["tag"] if sess else self.title_at(tt)[0]
        return {
            "at_utc": sec(tt) + "Z", "session": sess, "title": title,
            "rung_before": before[-1]["stream_kbps"] if before else None,
            "rung_after": after[0]["stream_kbps"] if after else None,
            "last_stepup_dt_s": round((tt - ts(last_up["at_utc"])).total_seconds()) if last_up else None,
            "last_stepup_in_session": in_sess,
            "trigger": (cause or {}).get("trigger"), "paused_ms": (cause or {}).get("paused_before_loss_ms"),
            "away_ms": (cause or {}).get("away_ms"), "create_to_start_ms": (cause or {}).get("create_to_start_ms"),
            "surface_lost": [{k: v for k, v in x.items() if k not in ("schema", "at_utc")} for x in lost],
            "silences_before_ms": [round(g.get("gap_ms") or 0) for g in sil],
            "stalls_before_ms": [x.get("age_ms") for x in st],
        }

# ---------------------------------------------------------------- the Markdown


def md_table(head: list[str], body: Iterable[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"]
    for r in body:
        out.append("| " + " | ".join("" if x is None else str(x).replace("|", "/") for x in r) + " |")
    return out


def seconds_view(an: Analysis, center: datetime, label: str) -> list[str]:
    out = [f"### ±60 s around {label} {sec(center)}Z", ""]
    body = []
    for k in sorted(an.row):
        kt = ts(k)
        if center - timedelta(seconds=60) <= kt <= center + timedelta(seconds=60):
            v = an.row[k]
            f = an.fsz.get(k, {})
            if not any(x in v for x in ("rec", "ladder_ev", "ctrl_gap_ms", "fps", "disc", "report_gap_ms", "rung")):
                continue
            body.append([hms(kt), "".join(sorted(an.hitch.get(k, ()))), v.get("fps", ""), v.get("lost", ""),
                         v.get("out_age", ""), round(v["ctrl_gap_ms"]) if "ctrl_gap_ms" in v else "",
                         "user" if v.get("ctrl_gap_user") else "", v.get("rung", ""), v.get("ogap", ""),
                         v.get("report_gap_ms", ""), v.get("disc", ""), f.get("frames", ""),
                         "; ".join(v.get("ladder_ev", [])), ", ".join(v.get("rec", []))])
    out += md_table(["UTC", "hitch", "fps", "lost", "out age ms", "ctrl gap ms", "", "rung", "output gap ms",
                     "report gap ms", "disc", "tx frames", "ladder", "recovery"], body) if body else ["(no rows)"]
    return out + [""]


def render(an: Analysis, label: str, around: list[datetime], around_saves: bool) -> str:
    L = [f"# diag read — {label}", "",
         f"Range (UTC): {sec(an.t0)}Z → {sec(an.t1)}Z. Sources: {'; '.join(an.sources) or 'none'}. "
         f"Generated by tools/diag_read.py (read-only). Hitch: UX-R3's (R/C/G/L). Titles as class + tag.", ""]
    L += ["## Sessions", ""]
    body = []
    for i, s in enumerate(an.sessions, 1):
        r = an.session_row(s)
        body.append([i, hms(s["start"]), hms(s["end"] or s["start"]), f"{r['length_s'] // 60}:{r['length_s'] % 60:02d}",
                     r["title"], r["core"], (r["path_class"] or "").replace("remote-", ""),
                     r["players"] if r["players"] is not None else "—",
                     json.dumps(r["slot_map"], sort_keys=True) if r["slot_map"] is not None else "—",
                     ", ".join(r["rung_history"]) or "—", r["end_kind"],
                     ", ".join(f"{hms(ts(x['at_utc']))} {x['trigger'] or '?'}" for x in r["restarts"]) or "—",
                     r["lost_post_fec"], f"{r['rendered_fps_med']} ({r['rendered_fps_min']})", r["resyncs"],
                     ", ".join(r["stalls"]) or "—", ", ".join(r["pauses"]) or "—", r["holds"], ", ".join(r["rewinds"]) or "—",
                     f"{r['hitch_s']} ({'/'.join(str(r['hitch_by'][c]) for c in 'RCGL')})", r["hitch_s_per_10min"],
                     f"{r['silences']} ({r['silences_user']})", r["silences_per_10min"], r["underruns"], r["starvation"],
                     r["rssi"], f"{r['rtt_p50_ms']}/{r['rtt_p95_ms']}" if r["rtt_p50_ms"] is not None else ""])
    L += md_table(["#", "start", "end", "length", "title", "core", "path", "players", "slot map", "rungs (transitions)",
                   "end", "restarts (trigger)", "loss post-FEC", "fps med (min)", "resyncs", "stalls", "pauses", "holds",
                   "rewinds (method, why)", "hitch s (R/C/G/L)", "hitch s / 10 min", "silences (user)",
                   "silences / 10 min", "underruns", "starvation", "RSSI", "RTT p50/p95"], body) if body else ["(no sessions)"]
    L += ["", "## Per 10 min", ""]
    body = []
    t = an.t0.replace(minute=an.t0.minute - an.t0.minute % 10, second=0, microsecond=0)
    while t < an.t1:
        b = t + timedelta(minutes=10)
        m = an.summarize(t, b)
        started = sum(1 for s in an.sessions if t <= s["start"] < b)
        if m["stream_s"] or started or m["restarts"]:
            body.append([t.strftime("%m-%d %H:%M"), f"~{m['stream_s']}", started, len(m["restarts"]), m["byes"],
                         len(m["transitions"]), len(m["stalls"]), len(m["pauses"]), len(m["rewinds"]),
                         f"{m['hitch_s']} ({'/'.join(str(m['hitch_by'][c]) for c in 'RCGL')})", m["silences"],
                         round(m["max_silence_ms"]), m["lost"], f"{m['fps_med']} ({m['fps_min']})", m["underruns"],
                         m["starvation"], m["rungs"], m["rssi"]])
        t = b
    L += md_table(["10 min from", "stream s", "sessions started", "client restarts", "user exits", "transitions",
                   "stalls", "pauses", "rewinds", "hitch s (R/C/G/L)", "silences", "max silence ms", "loss",
                   "fps med (min)", "underruns", "starvation", "rungs", "RSSI"], body) if body else ["(no stream)"]
    L += ["", "## Every client restart, with its cause", ""]
    body = []
    for r in an.restarts:
        d = an.restart_detail(r)
        body.append([hms(ts(d["at_utc"])), d["session"] if d["session"] else "(none PLAYING)", d["title"],
                     f"{d['rung_before']} → {d['rung_after']}",
                     (f"{d['last_stepup_dt_s']} s" + ("" if d["last_stepup_in_session"] else " (earlier session)"))
                     if d["last_stepup_dt_s"] is not None else "—",
                     d["trigger"] or "(no report)", d["paused_ms"], d["away_ms"],
                     ", ".join(str(x) for x in d["silences_before_ms"]) or "—",
                     ", ".join(str(x) for x in d["stalls_before_ms"]) or "—",
                     "; ".join(json.dumps(x, sort_keys=True) for x in d["surface_lost"]) or "—"])
    L += md_table(["restart", "session", "title", "rung before → after", "last step-up Δt", "client's trigger",
                   "paused ms", "away ms", "uplink silences in the 20 s before (ms)", "stalls in the 20 s before (ms)",
                   "surface_lost (B32)"], body) if body else ["(none)"]
    L += ["", "## Every rewind, pause, hold and stall", ""]
    body = []
    for r in an.rec:
        ev = r.get("event")
        if ev in ("input_release", "desync_pause", "client_stall", "state_saved", "resumed", "gave_up_saved") or \
                str(ev).startswith("input_hold"):
            cause = {"input_release": f"via {r.get('via')}, method {r.get('method')}" + (f", why {r.get('why')}" if r.get("why") else "")
                                      + (f", net {r.get('net_unattended_frames')} frames" if r.get("net_unattended_frames") is not None else ""),
                     "desync_pause": f"trigger {r.get('trigger')}, age {r.get('age_ms')} ms",
                     "client_stall": f"age {r.get('age_ms')} ms",
                     "state_saved": f"kind {r.get('kind')}, slot {r.get('slot')}"}.get(ev, r.get("trigger") or r.get("via") or "")
            body.append([hms(ts(r["at_utc"])), ev, cause])
    L += md_table(["UTC", "event", "cause"], body) if body else ["(none)"]
    L += ["", "## Ladder transitions", ""]
    L += md_table(["UTC", "from → to", "in place (B32)", "path class"],
                  [[hms(ts(r["at_utc"])), f"{r.get('from_kbps')} → {r.get('to_kbps')}", "yes" if r.get("in_place") else "no",
                    r.get("path_class", "")] for r in an.transitions]) if an.transitions else ["(none)"]
    pads = [r for r in an.rec if r.get("event") == "pad_slots"]
    L += ["", "## Pad slots (B34)", ""]
    L += md_table(["UTC", "slot map"], [[hms(ts(r["at_utc"])), json.dumps(r.get("slots") or r.get("map") or r.get("pad_slots"), sort_keys=True)]
                                        for r in pads]) if pads else ["(no pad_slots rows: the client sent none)"]
    # B53: PCSX2's own log per PS2 session (only when one exists)
    p2 = [(s, an.session_row(s)) for s in an.sessions if s["core"] == PS2_CORE]
    p2 = [(s, r) for s, r in p2 if "pcsx2_log" in r]
    if p2:
        L += ["", "## PCSX2 logs (B53)", ""]
        L += md_table(["start", "end"] + list(PCSX2_COUNTS), [[hms(s["start"]), hms(s["end"] or s["start"])]
                                                            + [r["pcsx2_log"][k] for k in PCSX2_COUNTS] for s, r in p2])
    L += ["", "## VOD (B35)", ""]
    if an.vod_client:
        L += md_table(["UTC", "event", "detail"], [[hms(Analysis._t(r)), r.get("event"),
                                                    json.dumps({k: v for k, v in r.items() if k not in ("event", "at_utc", "schema")}, sort_keys=True)]
                                                   for r in an.vod_client])
    else:
        L += ["(no VOD client rows)"]
    if an.vod_range:
        closes: dict[str, int] = defaultdict(int)
        for r in an.vod_range:
            closes[str(r.get("closed") or r.get("close") or r.get("how") or "?")] += 1
        L += ["", f"Range log: {len(an.vod_range)} requests, {sum(int(r.get('bytes') or 0) for r in an.vod_range)} bytes; "
                  f"closes: {', '.join(f'{k} {v}' for k, v in sorted(closes.items()))}."]
    L += ["", "## Per-second views (±60 s)", ""]
    centers = [(ts(r["at_utc"]), "restart") for r in an.restarts] + [(ts(r["at_utc"]), "stall") for r in an.stalls]
    if around_saves:
        centers += [(ts(r["at_utc"]), "state_saved") for r in an.rec if r.get("event") == "state_saved"]
    centers += [(t, "the time") for t in around]
    for c, lab in sorted(centers):
        L += seconds_view(an, c, lab)
    return "\n".join(L) + "\n"

# ---------------------------------------------------------------- main


def trip_span(trip_dir: Path) -> tuple[datetime, datetime]:
    ts_all = [ts(r["at_utc"]) for r in rows((trip_dir / "samples" / "overlay.jsonl").read_bytes()) if r.get("at_utc")]
    return min(ts_all), max(ts_all) + timedelta(seconds=60)


def build(range_text: str, now: datetime, sources: list[Path] | None = None, live: bool = False,
          root: Path = DIAG_ROOT, tz: tzinfo | None = None, logs_root: Path = REPO / "logs",
          trip_dir: Path = TRIP_DIR) -> tuple[str, Analysis]:
    label, a, b = parse_range(range_text, now, tz)
    logs = Logs()
    if label == "trip":
        a, b = trip_span(trip_dir)
        if not sources:
            sources = [trip_dir]
    for s in sources or []:
        s = Path(s)
        if (s / "raw").is_dir() or (s / "samples").is_dir():
            logs.add_keeper_dir(s)
        else:
            logs.add_copies_dir(s)
    if live:
        logs.add_live(logs_root, root)
    if not sources and not live:
        for d in keeper_dirs_for(root, a, b):
            logs.add_keeper_dir(d)
    return label, Analysis(logs, a, b, tz)


def parse_at(s: str, an: Analysis) -> datetime:
    s = s.strip().replace("Z", "")
    if "T" in s or " " in s:
        return ts(s.replace(" ", "T"))
    t = datetime.strptime(s if s.count(":") == 2 else s + ":00", "%H:%M:%S").time()
    d = datetime.combine(an.t0.date(), t)
    return d if d >= an.t0 else d + timedelta(days=1)


def new_path(d: Path, stem: str) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    p, n = d / f"{stem}.md", 1
    while p.exists():
        p, n = d / f"{stem}_{n}.md", n + 1
    return p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("range", nargs="+", help='last night | today | trip | "YYYY-MM-DD HH:MM..HH:MM" (UTC)')
    ap.add_argument("--source", action="append", type=Path, default=[], help="a keeper dir or a copies/ dir (repeatable)")
    ap.add_argument("--live", action="store_true", help="read logs/ directly")
    ap.add_argument("--root", type=Path, default=DIAG_ROOT)
    ap.add_argument("--trip-dir", type=Path, default=TRIP_DIR, help="the trip keeper's dir (for `trip`)")
    ap.add_argument("--around", action="append", default=[], help="HH:MM:SS or YYYY-MM-DDTHH:MM:SS (UTC), repeatable")
    ap.add_argument("--around-saves", action="store_true", help="a per-second view around every state_saved row")
    ap.add_argument("--out", type=Path, help="the Markdown file (never overwritten)")
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    label, an = build(" ".join(a.range), now, a.source, a.live, a.root, trip_dir=a.trip_dir)
    around = [parse_at(x, an) for x in a.around]
    text = render(an, label, around, a.around_saves)
    if a.out:
        if a.out.exists():
            ap.error(f"{a.out} exists; not overwritten")
        a.out.parent.mkdir(parents=True, exist_ok=True)
        out = a.out
    else:
        out = new_path(READS, f"diag_{label}_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}")
    with open(out, "x") as fh:
        fh.write(text)
    print(f"diag read: {len(an.sessions)} sessions, {len(an.restarts)} restarts, {len(an.stalls)} stalls -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
