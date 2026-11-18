#!/usr/bin/env python3
"""B143 (settle): the app's rule replayed on PP-H3c's second sitting (2026-11-18T03:36-03:54Z).

The rule (the app's `OpusReorder.offer`, PrivyHub/.../streaming/OpusFraming.kt lines 101-110): a frame whose sequence
is behind the receiver's `next` by more than half the 16-bit space is LATE and dropped; `next` moves only with a frame
that is played. The hub's sender starts every stream at sequence 0 (companion/audio_codec.py `run_opus_sender`:
`sequence = 0`), 100 frames a second (10-ms Opus frames, the hub's default). A new client session (a new receiver)
starts with `next` = -1 and takes the first frame it gets. So within one client session a stream's first
min(L, M) seconds are silent, M = the furthest point the receiver has played (in frames), L the stream's length; then
`next` = max(M, L). (If M >= 32769 the new stream's 0 reads as ahead by 64..32767: a JUMP, taken at once.)

Inputs (read only): the onn's heartbeat rows (logs/games/native_stream_heartbeat.log) and the sitting's party rows
(evidence/pph3c2_2026-11-18/part2/party_rows.txt). The streams: each client session's first stream from the session's
own start (the first heartbeat row's time minus its elapsed_ms); each planned switch (`minigame_stream` switched true):
the old stream ends at the switch's start (row time - seconds: `_stop_locked` runs first), the new one begins when its
sender starts (row time - 0.25 s: the start waits for 20 datagrams, 0.2 s, then answers). Home (`minigame_taken` home)
ends a stream. Observed silent: rows with audio_queue_depth 0 and audio_underruns rising since the row before.
Prints one line per stream: predicted silent stretch and its end, the observed end, the error. Numbers only."""
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
FPS = 100
DAY = "2026-11-18"
LO, HI = f"{DAY}T03:36:00", f"{DAY}T03:54:00"


def ts(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def hhmmss(t):
    return t.strftime("%H:%M:%S")


rows = []
for line in (REPO / "logs/games/native_stream_heartbeat.log").read_text().splitlines():
    try:
        r = json.loads(line)
    except ValueError:
        continue
    at = r.get("received_at_utc", "")
    if LO <= at[:19] <= HI:
        rows.append(r)
sessions = []          # [start, [rows]]
for r in rows:
    if r["sequence"] == 1 or not sessions:
        sessions.append([ts(r["received_at_utc"]) - timedelta(milliseconds=r["elapsed_ms"]), []])
    sessions[-1][1].append(r)

party = []
for line in (REPO / "docs/memory/evidence/pph3c2_2026-11-18/part2/party_rows.txt").read_text().splitlines():
    m = re.match(r"(\d\d:\d\d:\d\d\.\d+)Z (\w+) (\{.*\})$", line)
    if m:
        party.append((ts(f"{DAY}T{m.group(1)}Z"), m.group(2), json.loads(m.group(3))))
switches = [(t - timedelta(seconds=f["seconds"]), t - timedelta(seconds=0.25)) for t, step, f in party
            if step == "minigame_stream" and f.get("switched") is True]
homes = [t for t, step, f in party if step == "minigame_taken" and f.get("what") == "home"]

# the streams of each client session: (begin, end)
out = []
for i, (s0, srows) in enumerate(sessions):
    s_end = ts(srows[-1]["received_at_utc"])
    cuts = sorted([(a, b) for a, b in switches if s0 < a < s_end] + [(h, None) for h in homes if s0 < h < s_end])
    begin, streams = s0, []
    for a, b in cuts:
        streams.append((begin, a))
        if b is None:
            begin = None
            break
        begin = b
    if begin is not None:
        streams.append((begin, s_end))
    # observed silent rows of this session
    silent = []
    prev = None
    for r in srows:
        t = ts(r["received_at_utc"])
        if prev is not None:
            silent.append((t, r["audio_queue_depth"] == 0 and r["audio_underruns"] > prev["audio_underruns"]))
        prev = r
    M = -1
    for k, (b, e) in enumerate(streams):
        L = (e - b).total_seconds() * FPS
        if M < 0:
            pred_s = 0.0
            M = L
        elif 1 <= M % 65536 <= 32768:
            pred_s = min(L, M) / FPS
            M = max(M, L)
        else:
            pred_s, M = 0.0, L
        pred_end = b + timedelta(seconds=pred_s)
        # observed: the last silent row in this stream's span that belongs to a run starting at its begin
        obs_end = None
        in_span = [(t, s) for t, s in silent if b < t <= e + timedelta(seconds=1)]
        if in_span and in_span[0][1]:
            run_end = None
            for t, s in in_span:
                if not s:
                    run_end = t
                    break
            obs_end = run_end if run_end is not None else e
        obs_s = (obs_end - b).total_seconds() if obs_end else 0.0
        err = obs_s - pred_s
        out.append({"session": i + 1, "stream": k, "begin": hhmmss(b), "end": hhmmss(e), "length_s": round(L / FPS, 1),
                    "predicted_silent_s": round(pred_s, 1), "predicted_until": hhmmss(pred_end),
                    "observed_silent_s": round(obs_s, 1), "observed_until": hhmmss(obs_end) if obs_end else "-",
                    "error_s": round(err, 1)})
for o in out:
    print(json.dumps(o))
errs = [abs(o["error_s"]) for o in out]
print(json.dumps({"streams": len(out), "max_abs_error_s": max(errs), "heartbeat_rows": len(rows),
                  "row_interval_s": 2}))
