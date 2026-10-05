#!/usr/bin/env python3
"""C5-CLOSE -- the user's three looks of 2026-10-04/05 (local evening; 02:28-04:15Z), read-only, from the logs:
per companion session the controller's start row (top / inject), every inject / refused / transition row, the
samples by (level, stream kbps), recovery's session rows, and the look's session-file rows. Addresses never read."""
import glob, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
G = REPO / "logs" / "games"
T0, T1 = "2026-10-05T02:20", "2026-10-05T04:16"
def rows(paths):
    out = {}
    for p in paths:
        for l in open(p, errors="replace"):
            try:
                r = json.loads(l)
            except Exception:
                continue
            a = r.get("at_utc") or ""
            if T0 <= a < T1:
                out[(a, r.get("event"), r.get("session_elapsed_ms"))] = r
    return [out[k] for k in sorted(out)]
abr = rows([G / "adaptive_bitrate_shadow.jsonl"] + sorted(glob.glob(str(G / "stream_log_archive" / "adaptive_bitrate_shadow*"))))
rec = rows([G / "native_stream_recovery.log"])
look = rows([G / "ps1_look_sessions.jsonl"])
print(f"window {T0}Z .. {T1}Z")
print("\n== recovery session rows")
for r in rec:
    if r.get("event") in ("session_started", "session_ended", "desync_pause", "resumed", "gave_up_saved"):
        print(" ", r["at_utc"][:19], r["event"], r.get("state"))
print("\n== the look's session file (ps1_look_sessions.jsonl)")
for r in look:
    print(" ", r["at_utc"][:19], r.get("event"), "preset", r.get("preset"), "removed", r.get("removed"))
print("\n== controller: starts, injections, refusals, transitions; samples per segment by (level, stream kbps)")
seg = {}
def flush():
    if seg:
        print("     samples:", dict(sorted(seg.items())))
        seg.clear()
for r in abr:
    ev = r.get("event")
    if ev == "controller_start":
        flush()
        print(" ", r["at_utc"][:19], "controller_start", "top", r.get("top"), "inject", r.get("inject_enabled"))
    elif ev in ("inject", "refused", "transition"):
        print(" ", r["at_utc"][:19], ev, r.get("class"), r.get("from_kbps"), "->", r.get("to_kbps"), r.get("reason"),
              "elapsed_ms", r.get("session_elapsed_ms", r.get("at_elapsed_ms")), "injected", r.get("injected"))
    elif ev == "sample":
        k = (r.get("level_kbps"), r.get("stream_kbps"))
        seg[k] = seg.get(k, 0) + 1
flush()
