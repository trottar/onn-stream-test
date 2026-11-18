---
memory_schema: 1
as_of: 2026-11-18
status: BUILT (session B, queue AX) — the sound across a party's planned switch, behind PRIVYHUB_PARTY=1 (and PRIVYHUB_H7=1). Cause settled from the code: the hub's audio sender began every stream at sequence 0 (PHA1 has no SSRC or marker), and the app drops a frame that is behind what it has played (OpusReorder LATE) until the new count passes it; only a new receiver (a new client session, or the app's own restart, B11) starts over. The rule replayed on PP-H3c's twelve streams predicts every silent stretch within one heartbeat row (max error 2.0 s). Built: a planned switch arms the audio streamer, and the new process's sender continues the last run's sequence and timestamp; the users' own starts begin at 0 as today. Hub only; the app not changed. Tests through the real routes: 2 and 5 (+1) planned switches, every one heard at the first datagram (bound 50 ms, measured 0 ms), no LATE frame; HEAD's code: 7 of 8 switches silent end to end, one silent 3.08 s. Nothing adopted; nothing committed
---

# B143 — the sound across a planned switch

Queue: `handoffs/QUEUE_2026-11-18AX.md` §B143. The directory is `b143_2026-11-18/`: the design + `.sha256` (hashed
04:15:58Z, before any code), `replay_rule.py` + `replay_rule_result.jsonl` (the settle), `b143.diff`, the scenario's
two analyses (`scenario_mine.json`, `scenario_head.json`), the runs (`tests_x3.txt`, `tests_recent.txt`,
`tests_others.txt`, `tests_mutations.txt`), `scripts/`, the checks, `manifest.sha256`. Patch:
`patches/B143_PARTY_AUDIO_ACROSS_SWITCH.md`. No stream, no client, nothing started on the onn; the app not changed.

## Settled (from the code; the app read only)

- **What the hub's sender starts over at every `native_stream.start`:** the stream's start stops the old audio
  (`_stop_locked` → `session_io.stop_stream`) and starts a new sender thread. With the hub's `PRIVYHUB_AUDIO_CODEC=opus`
  that is `audio_codec.run_opus_sender`: **sequence 0, timestamp 0, a new Opus encoder**. The PHA1 header is magic,
  version, channels, a 16-bit sequence, a 32-bit timestamp, frames — **no SSRC, no marker, no session field.**
- **What the app does with audio behind what it has played:** `NativeAudioReceiver` reads the sequence and skips the
  timestamp (line 1204); `OpusReorder.offer` (`OpusFraming.kt` 101-135) drops a frame more than half the 16-bit space
  behind `next` as **LATE** (line 110) and never moves `next` for it; a frame 64-32767 ahead is a JUMP, taken at once.
  The PCM path the same (line 1302).
- **What makes it accept a new beginning:** a new receiver (`next = -1`). **Home / RESUME** is a new client session,
  so the app builds a new `NativeAudioReceiver`. The app's own restart rebuilds it too (B11, `NativeStreamActivity`
  line 983: "the host restarted its audio at sequence 0: a fresh receiver"), but **only for a restart the app itself
  asked for.** The app is not told about a planned switch, so it keeps its receiver.
- **The rule replayed on the sitting** (`replay_rule.py` on the onn's heartbeat rows 03:36-03:54Z and the party rows):
  within a client session, a stream's first min(L, M) / 100 s are silent, where M is the furthest frame played and L
  the stream's own frames. **12 streams, predicted against observed within one heartbeat row (max error 2.0 s; rows
  every 2 s):**

| client session / stream | length | predicted silent | observed silent (until) |
| --- | --- | --- | --- |
| 1 / the board | 44.4 s | 0 | 0 |
| 1 / the self-proof's title | 1.4 s | 1.4 s | 1.4 s |
| 1 / the board back | 110.7 s | 44.4 s | 45.4 s (03:38:35) |
| 1 / the first real match | 119.0 s | 110.7 s | 110.9 s (03:41:34) |
| 2 (RESUME) / the match | 97.3 s | 0 | 0 |
| 2 / the board back | 99.3 s | 97.3 s | 99.3 s (to its end) |
| 2 / practice 1 · the board · practice 2 · the board | 80.1 · 78.1 · 90.4 · 20.3 s | all of each | all of each |
| 2 / the second real match | 122.8 s | 99.3 s | 99.4 s (03:51:28) |
| 2 / the board to the END | 57.4 s | all | all |

  **On a board night every mini game is shorter than the board stretch before it, so every one would be silent.**

## Built (`b143.diff`)

- `companion/native_session_io.py` (`NativeAudioStreamer`): each sender run records where it stopped, `(next sequence,
  next timestamp)`. Only the run that is still the current one writes it (a token per run). **`party_continue_next(pid)`**
  arms the next start for that process; `_audio_start_counters(process_id)` runs once per Linux start, after the old
  run is stopped, and gives the recorded pair when armed for that pid, else `(0, 0)`. The arm and the record are cleared
  either way. Both sender loops start from `_audio_start` and record at their end.
- `companion/audio_codec.py` (`run_opus_sender`): the same start and record (`getattr` defaults, so any streamer
  without them is today's).
- `companion/party_minigame.py`: `_switch_stream` arms the audio for the switch's pid just before `ns.start` and
  disarms it in its `finally` (`_arm_switch`). Every planned switch goes through it: the way in, a practice's way back,
  the end's way back. The layer's docstring has lines for B143-B145.
- **Unchanged:** the users' own starts (the onn's `native-stream-start`, RESUME, the recovery's restarts, the fast
  restart) are never armed, so they begin at 0 as today. The video's switch (B115), the encoder's command, the relay,
  the controller and the planned-switch window are all untouched.

**What the switch costs in the sound:** the old sound stops when the switch begins and the new one starts with the new
sender's first datagram. That gap belongs to the switch itself and the fix does not change it. In the harness it was
**~770 ms at every switch** (the start's own 0.75-s video check plus the audio set-up, `gap_ms` in
`scenario_mine.json`). On the hub it is bounded by the switch's own time: 1.71-3.60 s in the sitting
(`minigame_stream` `seconds`), with the new sender's first datagram ~0.25 s before the row. **The fix adds 0 ms.** In
the modelled app the new process's first frame is released at the datagram that brings it, then played at the next 5-ms
poll.

## Tests (`tests/b143_party_audio_switch/`, 5; B114's scenario, its new `b143` mode)

| test | shown |
| --- | --- |
| the scenario | a fresh board (the onn's own start: `[0, 0]`); a held start, a real go, the end (**2 planned switches**); a held start, a practice left by Start, a practice left by time, a real go, the end (**5 + the end's way back**); every real start went through (no error, no worker died) |
| every switch heard at once | 8 / 8 switches: **the sequence continued** (first new = last old + 1), **the first frame released ≤ 50 ms after the new stream's first datagram (0 ms at every switch)**, every new frame released, **0 LATE** (2107 in order) |
| HEAD's code (the mutation) | the same scenario on the baseline's companion: every new stream at 0; **7 of 8 switches silent end to end, one silent 3.08 s**, 1790 LATE |
| the model | `receiver_model.py` (the app's receive path and `OpusReorder`, ported line for line, the lines cited): in order, a duplicate, a lost frame given up after k, LATE, a JUMP; a stream at 0 after 300 frames plays only past 300 |
| a users' start | the Opus and the PCM sender, two starts each (with an arm for another process set): **byte for byte HEAD's datagrams**, each starting at sequence 0, timestamp 0 |

In the scenario, behind the stream stub's own start: the real `NativeStreamManager._start_linux_locked` (G8-S2's stubbed
manager, nothing spawned) and the real `NativeAudioStreamer` (Opus as the hub runs it; `pactl` answered by stubs; the
capture a made-up process writing silence at the real rate) send to a UDP socket on loopback. **Disclosed:** the fake
title's pid has no `/proc` entry, so that one path is aliased as alive for the stream's and the audio's own checks;
libopus is found once with the real `Popen` (the harness replaces it for its fake RetroArch); the layer's
`_switch_stream` is the real one, reached through the real routes.

**The flags absent → today:** B114's `FlagsAbsentAreToday` (the real routes on HEAD's code against mine) in
`tests_others.txt`. **The client contract's tests** and **the audio codec's suite** are green there too.
