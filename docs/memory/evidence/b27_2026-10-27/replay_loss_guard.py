#!/usr/bin/env python3
"""B27: B10's loss-guard rule replayed over every client report since CL-B10 (read-only). Design: design_written_before_code.md.
The reports carry no per-drop timeline, so per session this is a bound from the counters (a report with the guard's own
keys is read as it is):
  D = sequence_gap_au_drops + incomplete_au_drops (an over-count: some may sit in a resync's wait)
  E <= min(D, idr_frames + 1)              episodes (drops inside one GOP are one)
  held: upper E x (G - 1), estimate E x 7.64 (BENCH-R3 E-on: 3,010 held / 394 episodes), lower 0
  longest hold <= min(max_frames_between_idr - 1, 36) frames (36 = the 600-ms cap at 60 fps); 0 if D = 0
  flagged: D > 0 and that bound >= 30 frames (a possible hold > 0.5 s)
    python3 -B replay_loss_guard.py <decoder_sessions dir> <out dir>"""
import glob, json, sys
from pathlib import Path

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
SINCE = "2026-10-23T18:42:13"            # CL-B10's first cell
OFFSITE = ("2026-10-24T19:15", "2026-10-25T17:40")   # G4-S4's span, before the onn came home
PER_EPISODE = 3010 / 394
CAP_FRAMES = 36
FRAME_MS = 1000.0 / 60.0

rows = []
for f in sorted(glob.glob(str(SRC / "native_decoder_*.json"))):
    try:
        d = json.load(open(f))
    except Exception as exc:
        rows.append({"file": Path(f).name, "error": type(exc).__name__})
        continue
    at = d.get("received_at_utc") or ""
    if at < SINCE:
        continue
    r = d.get("report") or {}
    v = r.get("video") or {}
    g = int(r.get("encoder_gop_frames") or 15)
    dr = int(v.get("sequence_gap_au_drops") or 0) + int(v.get("incomplete_au_drops") or 0)
    idr = int(v.get("idr_frames") or 0)
    m = int(v.get("max_frames_between_idr") or 0)
    e = min(dr, idr + 1)
    longest = 0 if dr == 0 else min(max(m - 1, 0), CAP_FRAMES)
    own = {k: r[k] for k in ("loss_guard_mode", "frames_after_dropped_reference", "loss_guard_episodes",
                             "loss_guard_frames_held", "loss_guard_timeouts", "loss_guard_max_wait_ms") if k in r}
    rows.append({
        "file": Path(f).name, "received_at_utc": at,
        "where": "off-site (G4-S4)" if OFFSITE[0] <= at < OFFSITE[1] else "LAN",
        "duration_s": round((r.get("duration_ms") or 0) / 1000.0, 1), "frames": int(v.get("frames") or 0),
        "gop": g, "sequence_gap_au_drops": int(v.get("sequence_gap_au_drops") or 0),
        "incomplete_au_drops": int(v.get("incomplete_au_drops") or 0), "drops": dr, "idr_frames": idr,
        "max_frames_between_idr": m, "sequence_resyncs": int(v.get("sequence_resyncs") or 0),
        "ssrc_changes": int(v.get("ssrc_changes") or 0),
        "non_idr_aus_dropped_waiting_for_idr": int(v.get("non_idr_aus_dropped_waiting_for_idr") or 0),
        "episodes_upper": e, "held_upper": e * (g - 1), "held_estimate": round(e * PER_EPISODE),
        "longest_hold_frames_upper": longest, "longest_hold_ms_upper": round(longest * FRAME_MS),
        "possible_hold_over_0_5_s": dr > 0 and longest >= 30,
        "own_guard_keys": own,
    })

ok = [x for x in rows if "error" not in x]
tot = {}
for where in ("LAN", "off-site (G4-S4)"):
    s = [x for x in ok if x["where"] == where]
    tot[where] = {"sessions": len(s), "streaming_min": round(sum(x["duration_s"] for x in s) / 60.0, 1),
                  "sessions_with_drops": sum(1 for x in s if x["drops"] > 0), "drops": sum(x["drops"] for x in s),
                  "held_upper": sum(x["held_upper"] for x in s), "held_estimate": sum(x["held_estimate"] for x in s),
                  "longest_hold_ms_upper": max((x["longest_hold_ms_upper"] for x in s), default=0),
                  "possible_hold_over_0_5_s": [x["file"] for x in s if x["possible_hold_over_0_5_s"]]}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "replay_output.json").write_text(json.dumps({"since": SINCE, "offsite_span": OFFSITE, "per_episode": PER_EPISODE,
                                                    "totals": tot, "sessions": rows}, indent=1) + "\n")
L = ["# B27 — B10's rule over every client report since CL-B10 (bounds from the counters; read-only)", "",
     f"Reports received since {SINCE}Z: {len(ok)} (+{len(rows) - len(ok)} unreadable). Off-site = G4-S4's span "
     f"{OFFSITE[0]}Z-{OFFSITE[1]}Z.", "",
     "| received (UTC) | where | s | drops (gap + incomplete) | IDRs | max between IDRs | episodes ≤ | held ≤ / est. | longest hold ≤ | > 0.5 s possible |",
     "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
for x in ok:
    L.append(f"| {x['received_at_utc'][:19]} | {x['where']} | {x['duration_s']} | {x['drops']} "
             f"({x['sequence_gap_au_drops']} + {x['incomplete_au_drops']}) | {x['idr_frames']} | "
             f"{x['max_frames_between_idr']} | {x['episodes_upper']} | {x['held_upper']} / {x['held_estimate']} | "
             f"{x['longest_hold_frames_upper']} fr ({x['longest_hold_ms_upper']} ms) | "
             f"{'**yes**' if x['possible_hold_over_0_5_s'] else 'no'}{' (own keys: ' + json.dumps(x['own_guard_keys']) + ')' if x['own_guard_keys'] else ''} |")
L += ["", "| totals | sessions | streaming min | with drops | drops | held ≤ | held est. | longest hold ≤ | > 0.5 s possible |",
      "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
for k, t in tot.items():
    L.append(f"| {k} | {t['sessions']} | {t['streaming_min']} | {t['sessions_with_drops']} | {t['drops']} | "
             f"{t['held_upper']} | {t['held_estimate']} | {t['longest_hold_ms_upper']} ms | "
             f"{len(t['possible_hold_over_0_5_s'])} {t['possible_hold_over_0_5_s']} |")
(OUT / "replay_table.md").write_text("\n".join(L) + "\n")
print("\n".join(L[-4:]))
