#!/usr/bin/env python3
"""C5-CLOSE-A -- the user's repeated Look 3 (2026-10-05 05:01-05:06Z), read-only from the logs: the controller rows
(rotated + live, by time), per-level C2 samples, the recovery rows, the encoder's Output #0 / sized-transition lines in
native_video_alpha.log, and the decoder report stored at BACK. Addresses are masked; nothing is written."""
import glob, json, re, statistics as st
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]; G = REPO / "logs" / "games"
T0, T1 = "2026-10-05T05:01:00", "2026-10-05T05:06:00"
REPORT = G / "decoder_sessions" / "native_decoder_20261005_050544_758.json"
rows = {}
for p in [G / "adaptive_bitrate_shadow.jsonl"] + sorted(glob.glob(str(G / "stream_log_archive" / "adaptive_bitrate_shadow*"))):
    for l in open(p, errors="replace"):
        try: r = json.loads(l)
        except Exception: continue
        if T0 <= (r.get("at_utc") or "") < T1:
            rows[(r["at_utc"], r.get("event"), r.get("session_elapsed_ms"))] = r
R = [rows[k] for k in sorted(rows)]
print("== controller rows (not samples / states)")
for r in R:
    if r.get("event") not in ("sample", "state"):
        print(" ", r["at_utc"][:23], r["event"], {k: r.get(k) for k in ("top", "inject_enabled", "class", "from_kbps", "to_kbps",
              "reason", "injected", "session_elapsed_ms", "from_size", "to_size", "actuation_ms") if r.get(k) is not None})
SESSION_END = "2026-10-05T05:05:34"   # recovery session_ended (the companion restart that ended the stream)
print("== C2 samples per stream level, inside the session (to its end at 05:05:34Z)")
for lvl in (7000, 12600):
    S = [r for r in R if r.get("event") == "sample" and r.get("stream_kbps") == lvl and r["at_utc"] < SESSION_END]
    if not S: continue
    fps = [r["fps"] for r in S if isinstance(r.get("fps"), (int, float))]
    lost = sum(r["lost_packets_delta"] for r in S if isinstance(r.get("lost_packets_delta"), (int, float)))
    gap = [r["output_gap_ms"] for r in S if isinstance(r.get("output_gap_ms"), (int, float))]
    mins = len(S) * 2 / 60
    print(f"  {lvl}: {len(S)} reports {S[0]['at_utc'][11:19]}-{S[-1]['at_utc'][11:19]} (~{mins:.2f} min); fps median {st.median(fps):.2f} "
          f"min {min(fps):.2f}; lost_packets_delta {lost} (~{lost / mins:.1f}/min); largest per-report gap {max(gap)} ms; "
          f"unclean {sum(1 for r in S if r.get('clean') is False)}; dispositions "
          f"{dict((d, sum(1 for r in S if r.get('disposition') == d)) for d in sorted({r.get('disposition') for r in S}))}")
print("== recovery rows")
for l in open(G / "native_stream_recovery.log", errors="replace"):
    try: r = json.loads(l)
    except Exception: continue
    if T0 <= r.get("at_utc", "") < T1 and r.get("event") in ("session_started", "session_ended", "desync_pause", "resumed", "gave_up_saved"):
        print(" ", r["at_utc"][:19], r["event"], r.get("state"))
print("== encoder (native_video_alpha.log, the last three Output #0 blocks and the sized-transition lines)")
d = open(G / "native_video_alpha.log", "rb").read().decode("utf-8", "replace")
for i in [m.start() for m in re.finditer(r"Output #0", d)][-3:]:
    for l in d[i:i + 900].replace("\r", "\n").split("\n"):
        if re.search(r"Stream #0:0: Video", l): print("  ", l.strip()[:120])
for m in list(re.finditer(r"C5-M5 Linux sized level transition[^\r\n]*", d))[-2:]: print("  ", m.group(0)[:120])
print("   last progress:", d[-300:].replace("\r", "\n").strip().split("\n")[-1][:110])
print("== decoder report", REPORT.name)
rep = json.load(open(REPORT))["report"]; v, dec = rep["video"], rep["decoder"]
print(f"  duration {rep['duration_ms']} ms; video frames {v['frames']}, lost {v['lost_packets']}, ssrc_changes {v['ssrc_changes']}, "
      f"sequence_resyncs {v['sequence_resyncs']}; decoder rendered {dec['rendered_frames']}, stale drops {dec['stale_output_drops']}, "
      f"spikes >=20/50/80/250 ms {dec['spike_20_ms']}/{dec['spike_50_ms']}/{dec['spike_80_ms']}/{dec['spike_250_ms']} "
      f"({dec['spike_20_ms'] / (rep['duration_ms'] / 60000):.1f}/min over the report), max_codec_ms {dec['max_codec_ms']}, "
      f"max_output_gap_ms {dec['max_output_gap_ms']}; audio underruns {rep['audio']['underruns']}")
print("  slow events by gap (elapsed_ms, codec_ms, ..., output_gap_ms):")
for e in sorted(rep["slow_events_top_gap"], key=lambda e: -e[-1])[:4]: print("   ", e)
print("  the report carries no decoded-size field (paused_frame_* is the pause thumbnail)")
