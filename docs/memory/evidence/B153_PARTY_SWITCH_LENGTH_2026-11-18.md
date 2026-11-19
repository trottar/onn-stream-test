---
memory_schema: 1
as_of: 2026-11-18
status: BUILT (session B, queue BA) — the planned switch's length and its gap of no sound, behind PRIVYHUB_PARTY=1 (and PRIVYHUB_H7=1); with B155 (the minigame_launch row's "keys_written"). Settled from the sitting's logs: the eight long switches (3.48-3.61 s) were the old sound's stop running a 2-s wait out — the audio capture's ffmpeg, SIGTERMed after the reader had stopped draining its pipe, blocked on the full pipe until SIGKILL at 2.0 s (all eight at 2.005-2.010 s; reproduced with the real ffmpeg, 8 of 30). Built: a party's planned switch kills the old capture and encoder at once and starts the new sound before the encoder's 0.75-s check; every other start is today's. Nothing adopted; nothing committed
---

# B153 — the planned switch's length (and B155 — one row for the session's two keys)

Queue: `handoffs/QUEUE_2026-11-18BA.md` §B153, §B155. The directory is `b153_2026-11-18/`: the design + `.sha256`
(hashed 20:15:17Z, before any code), `settle/` (the parts of all 20 switches, one short and one long switch's log
lines, the stand-in experiment and its result), `b153.diff` (applies on `d7a99b62`), `b155.diff` (applies on top of
it), the harness's two analyses (`scenario_mine.json`, `scenario_head.json`), the runs (`tests_x3.txt`,
`tests_recent.txt`, `tests_others.txt`, `tests_mutations.txt`), `scripts/`, the checks, `manifest.sha256`. Patches:
`patches/B153_PARTY_SWITCH_LENGTH.md`, `patches/B155_PARTY_KEYS_WRITTEN.md`. No stream, no client, nothing started on
the onn; the app not changed; the board's repo not touched.

## Settled — why some switches take twice as long

**A planned switch, step by step** (`PartyMinigames._switch_stream` → `NativeStreamManager.start` →
`_start_linux_locked`): the arms; `start()`'s checks; `_stop_locked()`: **the old sound's stop**
(`NativeAudioStreamer._stop_linux_locked`: the stop event — the sender stops and **the reader stops draining the
capture's pipe** —, the sender joined, **the capture SIGTERMed and waited ≤ 2 s, then SIGKILLed**, the reader joined,
the sink-input moved back, the null sink unloaded, the timing snapshot written), then **the old encoder SIGTERMed**
(waited ≤ 5 s), the relay stopped; the window found; the relay started; the new encoder spawned; **the 0.75-s check**;
then **the new sound** (`session_io.start`: null sink, the sink-input moved, the capture, its reader and sender);
`status()`; the row.

**What each of the 20 was made of** (ms from its start t0 = `time_unix` − `seconds`; `settle/switch_parts.txt`, from
the party rows, the audio timing snapshots' mtimes and the video log's encoder blocks):

| | the old sound stopped | → the old encoder's last frame | → the new encoder's first frame | → the row |
| --- | --- | --- | --- | --- |
| 12 short (1.655-1.978 s) | 39-423 | 154-234 | 503-563 | 857-874 |
| 8 long (3.480-3.605 s) | **2005-2010** | 93-231 | 483-545 | 870-875 |

**The lines for one short and one long** (`settle/log_lines_one_short_one_long.txt`, the sitting's consecutive pair):
switch 15, to the title, 1.852 s (t0 19:41:13.841Z): the board's audio snapshot written +0.322 s; the board's encoder's
last frame +0.479 (`frame= 4473 … time=00:01:14.55` from `start: 1795030799.770199`, "Exiting normally, received
signal 15."); the title's first frame +0.982 (`Duration: N/A, start: 1795030874.822839`); the row +1.852. Switch 16, to
the board, 3.480 s (t0 19:41:28.751Z): the title's audio snapshot **+2.008 s**; its encoder's last frame +2.102
(`frame=  962 … time=00:00:16.03`); the board's first frame +2.605 (`start: 1795030891.355916`); the row +3.480.

**The cause, one for all eight:** the long kind's whole extra is the old sound's stop, and all eight end 2.005-2.010 s
after the switch began: `_kill_process`'s 2-s wait running out. ffmpeg 7.1 acts on SIGTERM only when its main loop wakes
(every 0.5 s); by then the reader has stopped draining (it leaves at the stop event), and 64 KiB of pipe at 192 kB/s
fills in ~0.34 s — a later notice blocks its last write on the full pipe, and only SIGKILL ends it. **Not the window,
the direction or the title: a race on every stop** (to the title 3 long of 10, to the board 5 of 10). **Reproduced on
the hub with the real ffmpeg** (`settle/exp1.py`: lavfi silence at the real rate for the pulse monitor, the same pipe;
no audio device): today's order 8 of 30 killed at 2006-2008 ms, the rest 115-417 ms; draining until the exit 0 of 20;
SIGKILL at once 6-7 ms. The short kind's own spread (39-423 ms) is the same 0.5-s notice; the encoder's 93-234 ms is
its own. **B24 met the same wait** in the users' fast restart (CL-B13: 2,088 ms) and bounded it there at 0.3 s (that
path is what RESUME takes: at 19:35:13Z its capture was SIGKILLed at the bound, 402 ms); the party's planned switch
calls `ns.start` directly and never had that bound.

## Built (`b153.diff`)

- `companion/native_stream.py`: **`party_switch_next(pid)`** / `_take_party_switch(process_id)` (B144's pattern: taken
  once per Linux start, True only for the armed process, cleared either way). When taken: `_stop_locked(fast=True)` —
  `session_io.stop_stream(now=True)` and **`_kill_managed_process_now`** (the old encoder SIGKILLed, then waited);
  **the new sound started right after the encoder's spawn** (`_start_session_io_locked`, the same calls as before,
  moved), the 0.75-s check to the same deadline **and one poll after it**. Not taken: the same calls as HEAD, in the
  same order (`_stop_locked()`, `stop_stream()`, SIGTERM waits, the sound after the check).
- `companion/native_session_io.py`: `stop_stream(now)` → `NativeAudioStreamer.stop(now)` →
  `_stop_linux_locked(now)`: **`_kill_process_now`** (the capture SIGKILLed, then waited ≤ 2 s) only when `now`.
- `companion/party_minigame.py`: `_switch_stream` arms it for the switch's pid beside B143's arm and disarms it in its
  `finally` (`_arm_fast`; a stream without the method: nothing). Every planned switch goes through it.

**Expected on the hub** (the design's): **the switch 1.0-1.4 s, bound ≤ 1.6 s** (today 1.655-1.978 / 3.480-3.605);
**the gap of no sound 0.4-0.8 s, bound ≤ 1.2 s** (the onn's `audio_max_arrival_gap_ms`; today 1459-1759 /
3284-3410). From the parts: ~40 ms of stop, ~10 ms of kill, the window, relay and spawn (part of today's 483-563 ms),
the 0.75-s check; the new sound's first datagram after the spawn and the audio's own set-up, inside the check.

**What is left in the users' start path (not touched):** the users' stream stop (`native-stream-stop`, `stop`), the
end of a game session and any start that is not the fast restart still stop the capture with SIGTERM and the 2-s wait,
and the sound still starts after the 0.75-s check; the fast restart (RESUME, the onn's restarts) has B24's 0.3-s bound.

## Tests

| suite | shown |
| --- | --- |
| `b153_party_switch_length` (6) | B114's harness, `b153` mode — the real routes, `_switch_stream`, `_start_linux_locked` on G8-S2's stubbed manager, `NativeAudioStreamer` (Opus to loopback) **with the capture the real ffmpeg** (lavfi silence at the real rate — disclosed: a stand-in for the pulse monitor, no device, no title): a fresh board, a users' restart, then **ten practices left by Select (twenty planned switches), a real go and its end (22)**: every row ≤ 1.5 s (the stub's own 0.6 s + the real start ≤ 0.9 s): **1.364-1.367 s, the real start 0.763-0.766 s**; the sound's gap ≤ 300 ms: **19.5-29.8 ms**; the sequence continued at every one (B143); the capture and encoder killed at once at every planned switch (7.3-7.9 ms), **SIGTERM at the users' restart (315 ms) as today**. **HEAD's code, the same 22:** rows 1.625-1.977 s and **five at 3.561-3.563 s**; the capture's stops 64-416 ms and **five at 2000.2-2000.6 ms** (the hub: 39-423 / 2005-2010); gaps 832-2776 ms. **A users' start on G8-S2's recorders** (another pid armed on mine): every call, the argv and the payload the same as HEAD's |
| `b155_party_keys_written` (4) | below |
| B143 (5), B115 (6) | green |

**Runs:** B153, B155, B143, B115 **three times each, all OK** (`tests_x3.txt`; 0 temp dirs left); the recent suites once,
all OK (B151, B148, B147, B145, B144, B141, B140, B139, B137, B134, B133, start_rung, encoder_rc — `tests_recent.txt`;
B148's and B139's one skip each: the board's repo not named, the hub's kept pictures not in the work copy); the earlier
suites once, all OK (`tests_others.txt`: B114 with its flags-absent test against its baseline, B108, B110, B112, B127,
B124 …; B111 2 skipped — no board's repo named) but **`art_systems` 1 error in the work copy: its docs test reads
`docs/CHEATS.md`, which the work copy does not hold; against the repo 120 / 120 OK** (`art_repo.txt`). The older suites'
own temp dirs (153, as in queue AZ) stay in my main-disk scratch. **Mutations** (`tests_mutations.txt`): **6 / 6 caught** — the arm removed (bound, gap, kills), the capture's SIGTERM kept (bound, gap, kills), the sound after the check (bound, gap), any pid taken (kills, the users' start on the recorders), B155's keys not read and the field from the arm (the keyless launch). Disclosed: the sound-after-the-check mutation's first replacement did not compile (an error at set-up, not a catch); fixed and run again, caught.

## B155 — one row for the session's two keys (`b155.diff`)

**Settled:** B139's `PARTY_SESSION_SETTINGS` are set on the emulator for one launch and written by
`_prepare_retroarch_session_config` into the session config (`privyhub-session.cfg`, a temporary file renamed over it);
every launch rewrites the file, so PP-H4's C read it at only three of seven launches. **Built (the party layer only; the
emulator manager unchanged):** `launch()` stamps the file (inode, mtime) before the launch and reads it back after;
**`"keys_written": true`** on the `minigame_launch` row (with and without a cheat setup) when this launch wrote it and
each key has exactly one assignment `key = "false"`; else false. **Tests (4):** a party launch → true (the file's two
lines); a launch whose write is made keyless after the fact → false (the read is real, not the arm); a users' launch of
the same title → no minigame row, no field, its config without the keys; the flags absent → B114's `today` routes the
same on HEAD's code and mine, the users' launch config byte for byte HEAD's.

## Disclosed

The harness's capture is the real ffmpeg reading lavfi silence (no pulse server, no device, no title). The stand-in
experiment ran the same program on the hub (no device). B111's Godot parts skipped (the board's repo not named — this
queue does not touch it). My scratch: the `/tmp/b_q38ba` work copy (companion/, tools/, tests/, PrivyHub/'s `app/src`);
a first scratch folder of mine under `/tmp` (the experiment scripts) was moved to the main disk within minutes so the
`/tmp/b_` copy holds the sources only.
