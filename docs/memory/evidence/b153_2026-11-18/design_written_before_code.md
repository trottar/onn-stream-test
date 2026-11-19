# B153 / B155 — the planned switch's length; one row for the session's two keys (design, written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-18BA.md` §B153, §B155. Baseline `d7a99b62`. Behind `PRIVYHUB_PARTY=1` (and
`PRIVYHUB_H7=1`); absent = today byte for byte. The users' own sessions (every stream start that is not a party mini
game's planned switch) byte for byte today with the flags set.

## B153 — settled (the sitting's logs, the code; `settle/`)

**What a planned switch is**, in order (`PartyMinigames._switch_stream` → `NativeStreamManager.start` →
`_start_linux_locked`): the arms (B143 audio, B144 band); `start()`'s checks; **`_stop_locked()`**: the telemetry
(nothing on Linux), **`session_io.stop_stream()` → `NativeAudioStreamer._stop_linux_locked()`** (the stop event; the
sender joined; **`_kill_process(capture)`: SIGTERM, wait ≤ 2 s, then SIGKILL**; the reader joined; the sink-input moved
back, the null sink unloaded, the timing snapshot written), then **`_kill_managed_process(encoder)`: SIGTERM, wait ≤
5 s**, the FEC relay stopped; the band's arm taken; the window found (`xdotool`, ≤ 2 s); the log header; the relay
started; the encoder spawned; **the start check: 0.75 s from the spawn**; then the audio's redundancy and
**`session_io.start()`** (the controller, the audio: null sink, the title's sink-input moved, the capture `ffmpeg -f
pulse … -f s16le pipe:1`, its reader and sender); `status()`; the row.

**The two kinds, all 20 (the self-proof's 2 and the sitting's 18; `settle/switch_parts.txt`, ms from the switch's
start t0 = `time_unix` − `seconds`):**

| | t0 → the old sound stopped (the audio timing snapshot's mtime) | → the old encoder's last frame | → the new encoder's first frame (x11grab `start`) | → the row |
| --- | --- | --- | --- | --- |
| 12 short (1.655-1.978 s) | 39-423 | 154-234 | 503-563 | 857-874 |
| 8 long (3.480-3.605 s) | **2005-2010** | 93-231 | 483-545 | 870-875 |

**Everything after the old sound's stop is the same in both kinds; the long kind's whole extra is the audio stop, and
all eight end at 2.005-2.010 s: the capture's 2-s wait running out, then SIGKILL.** One short and one long, the
sitting's consecutive pair (`settle/log_lines_one_short_one_long.txt`): switch 15 (to the title, 1.852 s, t0
…873.841): sound stopped +0.322, the board's encoder's last frame +0.479 (`time=00:01:14.55` from `start:
…799.770`, "Exiting normally, received signal 15."), the title's first frame +0.982 (`start: …874.823`), the row
+1.852. Switch 16 (to the board, 3.480 s, t0 …888.751): sound stopped **+2.008**, the title's encoder's last frame
+2.102 (`time=00:00:16.03`), the board's first frame +2.605 (`start: …891.356`), the row +3.480.

**Why the capture does not go at SIGTERM.** The stop sets the stop event first; the reader thread leaves its loop
after its next read, so **nothing drains the capture's stdout pipe any more**. ffmpeg 7.1 notices SIGTERM only when its
main loop wakes (every 0.5 s, its stats period), then flushes. 64 KiB of pipe at 48 kHz stereo s16 (192 kB/s) fills
in ~0.34 s: when the notice comes later than that, its last write blocks on the full pipe (the handler restarts the
write) and it never exits: the 2-s wait runs out, SIGKILL. **Reproduced on the hub with the real ffmpeg** (no audio
device: lavfi silence at the real rate standing in for the pulse monitor, the same output; `settle/exp1.py`): today's
order 30 stops → **8 killed at 2006-2008 ms**, the rest 115-417 ms (the sitting: 8 of 20, 2005-2010 / 39-423); the
reader draining until the exit (`exp1_drain.py`) 20 → 0 killed (65-567 ms); SIGKILL at once 10 → 6-7 ms. **The eight
share one cause; it is a race on every stop, not the window, the direction or the title.** The short kind's own
spread (39-423 ms) is the same 0.5-s notice; the encoder's 93-234 ms after it is its own SIGTERM notice.

**The users' own starts and stops go through the same `_stop_locked` (the onn's start, RESUME, the recovery's
restarts, the stop route): the same race is there today.** This queue does not touch it (below: what is left).

## B153 — the design (a party's planned switch only)

A new arm on the stream, as B144's band: **`NativeStreamManager.party_switch_next(pid)`**, set by `_switch_stream`
for the switch's pid just before `ns.start` and cleared in its `finally` (`_arm_fast`; a stream without the method:
nothing). `_start_linux_locked` takes it once (`_take_party_switch(process_id)`: True only when armed for this
process; cleared either way) **before `_stop_locked`**. Only when it is True:

1. **The old sound stopped at once**: `_stop_locked(fast=True)` → `session_io.stop_stream(now=True)` →
   `NativeAudioStreamer.stop(now=True)` → `_stop_linux_locked(now=True)`: the capture is **SIGKILLed** (then waited,
   ≤ 2 s) instead of SIGTERM + 2 s. The capture writes raw PCM to our own pipe; there is nothing to finish. The rest
   of the audio stop as today (the sender's join and its B143 record, the reader, the sink back, the snapshot).
2. **The old encoder stopped at once**: `_kill_managed_process_now(encoder)`: SIGKILL, then waited (≤ 5 s). Its
   output is RTP to our own loopback relay; the new encoder's first frame is a key frame.
3. **The new sound started before the encoder's check**: right after the encoder's spawn, the redundancy and
   `session_io.start()` (which never raises: audio errors are kept in its status, as today), then the 0.75-s check
   runs to the same deadline (from the spawn), **and one more poll of the encoder and the relay after it** (so the
   check is never skipped when the audio start takes longer than 0.75 s). If the encoder died, `_stop_locked()` (as
   today) stops the new sound too and the start fails as today. After the check nothing more is started.

Not armed (every other start: the onn's own, RESUME, the recovery's restarts, the fast restart, a stop): **the code
path is today's line for line** — `_stop_locked()` with no argument, `stop_stream()` with no argument, the same
SIGTERM waits, the audio after the check. With the flags absent nothing arms it.

**Not done, and why:** keeping the old sound until the new is up (two captures and two senders at once: one
`NativeAudioStreamer` holds one run; B143's sequence continuity is per run) — the early start gets most of it with no
new state. Shortening the 0.75-s check: it is the start's only proof the encoder came up; kept.

**Expected on the hub** (from the parts above): the switch's length = the pre-stop work and the sound's stop
(~40 ms: the 39-ms switch had both notices near 0) + the encoder's kill (~10 ms) + the window, relay, spawn (part of
today's 483-563 ms) + the 0.75-s check + `status()` → **expected 1.0-1.4 s; bound: every planned switch ≤ 1.6 s**
(today 1.655-1.978 and 3.480-3.605). **The gap of no sound** (the onn's `audio_max_arrival_gap_ms` at the switch;
today 1459-1759 / 3284-3410, ≈ the length − 0.2 s): the old sender stops at the stop event (t0 + a few ms); the new
sender's first datagram comes after the stop (~50 ms), the window and the spawn, and the audio's own set-up (pactl,
the capture's start, its first data) → **expected 0.4-0.8 s; bound ≤ 1.2 s**.

**Tests (`tests/b153_party_switch_length/`)**, B114's harness, a new `b153` mode (B143's set-up: the real routes, the
real `_switch_stream`, the real `_start_linux_locked` on G8-S2's stubbed manager, the real `NativeAudioStreamer` with
Opus to a loopback socket) **with the capture the real ffmpeg 7.1 stand-in** (lavfi silence at the real rate, the
same s16le pipe — disclosed; no pulse, no device, no title) and B114's made-up title: a held start, **ten practices
in a row (twenty planned switches, both ways)**, a real go and its end (two more). Shown: every planned switch's
`seconds` ≤ the harness bound (no window search, no VAAPI: **≤ 1.0 s**) and its sound gap (last old datagram → first
new) **≤ 0.5 s**; the capture SIGKILLed at every planned switch, never at a users' start; B143's continuity kept (the
sequence goes on). **HEAD's code, the same scenario:** the long kind shown — at least one switch with the sound's stop
≥ 1.9 s (expected ~1 in 3). **A users' start with the flags set:** the board's own start and a RESUME-shaped start
(not armed; another pid armed): the calls on G8-S2's recorders and the audio's datagrams byte for byte HEAD's; the
capture stopped by SIGTERM as today. **The flags absent:** the routes as HEAD's (B114's flags-absent test). B143's and
B115's suites green.

## B155 — one row for the session's two keys (design)

Settled: `PARTY_SESSION_SETTINGS` (two keys) are set on the emulator for one launch (`launch()` in
`_start_steps`); `_prepare_retroarch_session_config` writes them into `data/games/retroarch/config/
privyhub-session.cfg` (a temporary file renamed over it) only when that attribute is set; every launch rewrites the
file. **In the party layer only** (the emulator manager unchanged): `launch()` stats the file before the launch and,
after the launch returns, reads it back; **`keys_written` = the file was written by this launch (its inode or mtime
changed) and each of the two keys has exactly one assignment, `key = "value"` with the value set.** The
`minigame_launch` row (both forms: with and without a cheat setup) carries `"keys_written": true|false`. A users'
launch writes no `minigame_launch` row (and its config is today's). Tests (`tests/b155_party_keys_written/`, B114's
harness): true at a party launch; a file written without the keys → false (the read is real); a users' launch: no row,
its config without the keys, byte for byte HEAD's; the flags absent → today.

**Files:** `companion/native_stream.py`, `companion/native_session_io.py`, `companion/party_minigame.py`;
`tests/b114_party_minigame_hang/b114_scenario.py` (the `b153` and `b155` modes), the two new test dirs.
