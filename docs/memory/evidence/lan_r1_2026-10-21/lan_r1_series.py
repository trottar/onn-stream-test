#!/usr/bin/env python3
"""LAN-R1: the per-report series, from the copies in inputs/ only (read-only; no stream, no host load).

Each live ladder `sample` row (what the controller read, 2-s cadence) is joined to the nearest client heartbeat
within 1.5 s and 1,500 ms of elapsed (the same report, or the same 2-s interval when the two sends are offset), and the heartbeat's cumulative counters are turned
into per-report deltas within one client session:

    lost        the ladder's `lost_packets_delta` (post-FEC; what the controller reads live)
    hb_lost     heartbeat lost_packets delta (post-FEC, incl. the jump of a resync)
    hb_resync_lost  heartbeat lost_packets_in_resyncs delta
    fec_rec     fec_recovered_packets delta
    unrec       fec_unrecoverable_groups delta
    resyncs     stream_resyncs delta
    underruns / concealed   audio deltas (context only)

Spans: the two evenings and every clean window named by the task, from their records.
"""
from __future__ import annotations

import bisect
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
INP = HERE / "inputs"

LADDER_FILES = (sorted((INP / "ux_r2" / "stream_log_archive").glob("adaptive_bitrate_shadow.jsonl.*"))
                + [INP / "ux_r2" / "adaptive_bitrate_shadow.jsonl", INP / "ux_r1" / "adaptive_bitrate_shadow.jsonl"])
HEARTBEAT_FILES = [INP / "archive" / "native_stream_heartbeat.log.3", INP / "archive" / "native_stream_heartbeat.log.2",
                   INP / "archive" / "native_stream_heartbeat.log.1", INP / "ux_r1" / "native_stream_heartbeat.log",
                   INP / "ux_r2" / "native_stream_heartbeat.log"]
RECOVERY_FILES = [INP / "ux_r1" / "native_stream_recovery.log", INP / "ux_r2" / "native_stream_recovery.log"]

# (name, kind, start, end) -- UTC; windows from each record (the e1 suite's 600-s window)
SPANS = [
    ("UX-R1 Sunday (2026-10-20)", "evening", "2026-10-20T04:19:00", "2026-10-20T05:23:00"),
    ("UX-R2 last night (2026-10-21)", "evening", "2026-10-21T04:42:00", "2026-10-21T05:27:00"),
    ("CL-B5 A pcm", "clean", "2026-10-18T23:31:04", "2026-10-18T23:41:04"),
    ("CL-B5 B opus", "clean", "2026-10-18T23:48:24", "2026-10-18T23:58:24"),
    ("CL-B5 L opus", "clean", "2026-10-19T00:18:05", "2026-10-19T00:28:05"),
    ("CL-B6 1 opus", "clean", "2026-10-19T02:37:42", "2026-10-19T02:47:42"),
    ("CL-B6 2 pcm", "clean", "2026-10-19T02:55:02", "2026-10-19T03:05:02"),
    ("CL-B7 pcm", "clean", "2026-10-19T17:01:34", "2026-10-19T17:11:34"),
    ("CL-B7 opus today", "clean", "2026-10-19T17:19:12", "2026-10-19T17:29:12"),
    ("CL-B7 opus lean", "clean", "2026-10-19T17:37:00", "2026-10-19T17:47:00"),
    ("G4-S3 (remote, 4000; no LAN part)", "clean_remote", "2026-10-19T13:54:00", "2026-10-19T14:04:00"),
]
# G8-S1's shim cells at a 7000 start (the run's telemetry span; ladder and heartbeat from the archives)
G8_SPANS = [
    ("G8-S1 03 loss-1 off", "g8", "2026-10-16T20:42:58", "2026-10-16T20:57:06"),
    ("G8-S1 04 loss-1 on", "g8", "2026-10-16T20:57:14", "2026-10-16T21:11:31"),
    ("G8-S1 05 loss-5 off", "g8", "2026-10-16T21:11:40", "2026-10-16T21:25:45"),
    ("G8-S1 06 loss-5 on", "g8", "2026-10-17T00:29:30", "2026-10-17T00:44:01"),
    ("G8-S1 07 burst-50x20 off", "g8", "2026-10-17T00:44:09", "2026-10-17T00:58:27"),
    ("G8-S1 08 burst-50x20 on", "g8", "2026-10-17T00:58:35", "2026-10-17T01:12:51"),
    ("G8-S1 21 delay-50+loss-1 off", "g8", "2026-10-17T04:01:53", "2026-10-17T04:15:59"),
    ("G8-S1 22 delay-50+loss-1 on", "g8", "2026-10-17T04:16:08", "2026-10-17T04:30:28"),
]


def ts(t: str) -> float:
    t = t.rstrip("Z")
    fmt = "%Y-%m-%dT%H:%M:%S.%f" if "." in t else "%Y-%m-%dT%H:%M:%S"
    return datetime.strptime(t, fmt).replace(tzinfo=timezone.utc).timestamp()


def jl(p: Path) -> list[dict]:
    out = []
    if p.exists():
        for line in p.read_text(errors="replace").splitlines():
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def ladder_rows() -> list[dict]:
    rows = {}
    for p in LADDER_FILES:
        for r in jl(p):
            if r.get("mode") == "live" and r.get("at_utc"):
                rows[(r["at_utc"], r.get("event"), r.get("session_elapsed_ms"))] = r
    return sorted(rows.values(), key=lambda r: r["at_utc"])


def recovery_rows() -> list[dict]:
    rows = {}
    for p in RECOVERY_FILES:
        for r in jl(p):
            if r.get("at_utc") and r.get("event"):
                rows[(r["at_utc"], r["event"])] = r
    return sorted(rows.values(), key=lambda r: r["at_utc"])


HB_KEYS = {"hb_lost": "lost_packets", "hb_resync_lost": "lost_packets_in_resyncs", "fec_rec": "fec_recovered_packets",
           "unrec": "fec_unrecoverable_groups", "resyncs": "stream_resyncs", "underruns": "audio_underruns",
           "concealed": "audio_concealed_underruns"}


def heartbeat_deltas() -> list[tuple[float, int, dict]]:
    """[(t, elapsed_ms, deltas)], time-sorted, for every heartbeat with a predecessor in the same client session."""
    rows = {}
    for p in HEARTBEAT_FILES:
        for r in jl(p):
            if r.get("received_at_utc") and isinstance(r.get("elapsed_ms"), (int, float)):
                rows[(r["received_at_utc"], r["elapsed_ms"])] = r
    seq = sorted(rows.values(), key=lambda r: r["received_at_utc"])
    out: list[tuple[float, int, dict]] = []
    prev = None
    for r in seq:
        t = ts(r["received_at_utc"])
        if prev is not None and r["elapsed_ms"] > prev["elapsed_ms"] and t - ts(prev["received_at_utc"]) < 30:
            d = {}
            for k, src in HB_KEYS.items():
                a, b = r.get(src), prev.get(src)
                d[k] = (a - b) if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a >= b else None
            out.append((t, int(r["elapsed_ms"]), d))
        prev = r
    return out


def series(span: tuple[str, str, str, str], rows: list[dict] | None = None, hb=None) -> list[dict]:
    _, _, a, b = span
    rows = rows if rows is not None else ladder_rows()
    hb = hb if hb is not None else heartbeat_deltas()
    ta, tb = ts(a), ts(b)
    hb_t = [x[0] for x in hb]
    out = []
    for r in rows:
        if r.get("event") != "sample":
            continue
        t = ts(r["at_utc"])
        if not ta <= t < tb:
            continue
        el = r.get("session_elapsed_ms")
        d = None
        if isinstance(el, (int, float)):
            # the same client report has the same elapsed; when the two sends are offset (seen 04:55-05:08 on
            # 10-21, ~0.5 s) the nearest heartbeat within 1.5 s and 1,500 ms of elapsed covers the same interval
            i = bisect.bisect_left(hb_t, t)
            best = None
            for j in (i - 1, i, i + 1):
                if 0 <= j < len(hb):
                    th, he, dd = hb[j]
                    if abs(th - t) <= 1.5 and abs(he - el) <= 1500 and (best is None or abs(th - t) < best[0]):
                        best = (abs(th - t), dd)
            d = best[1] if best else None
        out.append({"at_utc": r["at_utc"], "t": t, "elapsed_ms": el, "disposition": r.get("disposition"),
                    "fps": r.get("fps"), "queue": r.get("queue_depth"), "gap": r.get("output_gap_ms"),
                    "lost": r.get("lost_packets_delta"), "waiting_for_idr": r.get("waiting_for_idr"),
                    "level": r.get("level_kbps"), "state": r.get("state"), "reason": r.get("reason"),
                    "joined": d is not None, **(d or {k: None for k in HB_KEYS})})
    return out


if __name__ == "__main__":
    rows, hb = ladder_rows(), heartbeat_deltas()
    for sp in SPANS + G8_SPANS:
        s = series(sp, rows, hb)
        n = len(s)
        j = sum(x["joined"] for x in s)
        tot = lambda k: sum(x[k] or 0 for x in s)
        mins = (s[-1]["t"] - s[0]["t"]) / 60 if s else 0
        print(f"{sp[0]:36s} samples {n:4d} joined {j:4d} min {mins:5.1f} | ladder lost {tot('lost'):6d} "
              f"hb lost {tot('hb_lost'):6d} (in resyncs {tot('hb_resync_lost'):5d}) fec_rec {tot('fec_rec'):5d} "
              f"unrec {tot('unrec'):4d} resyncs {tot('resyncs'):3d}")
