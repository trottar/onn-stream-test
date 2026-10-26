# B24 — the fast restart unlocked: design, written before any B24 code

Baseline HEAD 06c565e (G-A5 adopted: `PRIVYHUB_RESTART_FAST=1`, the eleventh line; the worker is B22's). Queue:
`handoffs/QUEUE_2026-10-26I.md` §B24. Rows: CL-B13 §2 (four Home returns). G-A6 not touched.

## 0. Settled

### (1) The old audio's stop: 2,088 ms once, 203-352 ms otherwise

- **The audio timing snapshot is the stop's last act** (`_write_linux_timing_snapshot`, after the joins and both
  `pactl` calls). Its file mtime is therefore the stop's end, on the host clock:

  | return | entry (`session_ended`) | the stop began (`released_ms`) | snapshot written (after entry) | **the stop ran** | `audio_stopped_ms` |
  | --- | --- | --- | --- | --- | --- |
  | 1 | 22:43:48.258 | 123 | 22:43:50.469 (+2,211) | **2,088 ms** | 2,210 |
  | 2 | 22:46:47.349 | 221 | 22:46:47.772 (+424) | 203 | 576 (the spawn's end; the join came after) |
  | 3 | 22:47:10.632 | 471 | 22:47:11.453 (+821) | 350 | 824 |
  | 4 | 22:47:40.229 | 421 | 22:47:41.002 (+773) | 352 | 769 |

- **The code's bounds inside the stop** (`NativeAudioStreamer._stop_linux_locked`), in order:
  1. the stop event set; **the sender's join ≤ 1.0 s**. The Opus sender (`audio_codec.run_opus_sender`) waits on that
     event between frames, so it leaves in ≤ 10 ms;
  2. **the capture's `_kill_process`: SIGTERM, `wait(timeout=2)`, then SIGKILL**;
  3. the reader's join ≤ 1.0 s. The reader blocks in `os.read` on the capture's pipe and leaves at its EOF, i.e. once
     the capture is dead;
  4. `pactl move-sink-input` and `pactl unload-module`, each `timeout=3.0`;
  5. the timing snapshot.
- **The one 2-s bound that a 2,088-ms stop fits is the capture's `wait(timeout=2)` expiring** (2,000 + ~88 ms of the
  rest):
  - the sender cannot take 1 s;
  - the reader's 1 s can only run while the capture lives;
  - `pactl` would show 3 s.
  - So at return 1 the capture (ffmpeg on the sink's monitor) did not exit on SIGTERM within 2 s and was SIGKILLed.
  - **No kept row records the kill:** `native_pulseaudio.log` has no timestamps or exit lines. Hence a new row
    (§1.4: the capture's return code).
  - Why it hung once is not in the files. A plausible cause, not tested: a monitor read blocked on an idle,
    suspended sink while the game was held paused.
- **Bounded?** Yes, by the code: ≤ ~1 + 2 (+ the kill's reap) + 1 + 3 + 3 ≈ 10 s worst case; 0.2-0.35 s typical;
  2.1 s once.

### (2) Does the new session's ready need anything the old audio's stop does?

- **The ready** (`native-stream-ready`) needs `status()` active (the new encoder and relay running), then the resume.
  It reads nothing of the audio.
- **The new encoder** needs only the capture released (the old encoder's exit). The audio is separate processes and
  sockets.
- **`AUDIO_CODEC.prepare`** sets the streamer's Opus session for the next sender. The old sender holds its own
  `session` reference (`run_opus_sender(streamer, streamer._audio_codec_opus, …)`, read once at its start), and it
  has left within ≤ 10 ms of the stop's first act. **So `prepare` after the new spawn is safe once the old stop has
  begun.**
- **The new audio** (`_session_io.start`) does need the old stop: the same streamer, its sink module and capture;
  `start` begins with `audio.stop()`.
- **The client:**
  - B22 starts the rebuilt audio receiver at the ready's return;
  - the receiver binds at `start()` and **waits up to 3,000 ms for its first real PCM before it plays**
    (`STARTUP_REAL_PCM_TIMEOUT_MS`), counting no underrun meanwhile;
  - the old sender is silent from the stop's first act.
  - So a new audio that starts after the ready (within 3 s) is heard from its first packet. Only the old stream would
    harm it, and it has stopped.
- **Answer: the ready needs only the new encoder's check and `prepare`.** The old audio's tail and the new audio's
  start can follow the ready, with no client change.

### (3) The old encoder between the kill and its exit (123 / 221 / 471 / 421 ms)

- `_kill_managed_process`: SIGTERM, `wait(timeout=5)`. ffmpeg on SIGTERM stops its input, flushes the encoder and the
  RTP muxer, and exits.
- **The FEC relay is stopped only after that exit** (B22's order: kill → wait → relay stop). So every packet the dying
  encoder flushes is forwarded to the onn. Its last frame reached the relay's rows at +0.075 / +0.168 / **+0.351 /
  +0.388** s.
- The 471 / 421 ms at returns 3-4 (23 s and 30 s after the previous start) are the graceful exit's own time. The
  per-second log cannot split the flush from the exit.

## 1. The design: `PRIVYHUB_RESTART_FAST_UNLOCK=1`, inside the adopted `PRIVYHUB_RESTART_FAST=1`

New `companion/restart_fast_unlock.py`: `RestartFastUnlock(RestartFast)`, the adopted class with its worker replaced.
`plugins/games.py` imports it only when both flags read `1`, and builds it in place of `RestartFast`. The request half
(eligibility, the read-only preflight, the snapshot, the lock hand-off, the response, the `restart_fast` row) is
inherited unchanged. **`restart_fast.py` is not edited.**

**The worker, under the manager's lock (taken before the response, as G-A5):**
1. **the old audio's stop starts first**, on its own thread: `_session_io.stop_stream()`. Its first act stops the old
   sender. The old capture process is noted before, for (§1.4);
2. **the relay stops** (`_fec_relay.stop()`, today's field reset for it): the old encoder's frames stop being
   forwarded at the kill, whatever it still flushes (`relay_stopped_ms`). That is the answer to "stop forwarding at
   the kill, or make the kill stop it sending": the relay. It is independent of how ffmpeg exits, and its port is
   closed before the old encoder can flush into a new relay;
3. **the old encoder:**
   - SIGTERM, then the capture target (xdotool) selected for the new encoder while it exits;
   - **a 100-ms grace, then SIGKILL**, then its reap (`released_ms`). The flushed frames go nowhere now, so the
     graceful exit buys nothing; CL-B13's exits took 123-471 ms. Today's code already SIGKILLs at 5 s;
4. today's other field resets (as G-A5's worker);
5. **the new encoder** as G-A5's `_spawn_locked` makes it (the same log header, the relay's start, `START_RUNG`, the
   argv line, `Popen`), with the target from step 3 (`spawned_ms`). One encoder at a time on the capture: the `Popen`
   only after the old one's reap;
6. `AUDIO_CODEC.prepare` (a refusal fails the restart as G-A5);
7. **today's startup check, 0.75 s from the `Popen`, at least one check** (`checked_ms`);
8. **the lock released** (`unlocked_ms`). **The ready's `status()` answers here.** Row `restart_fast_done` (lock /
   relay_stopped / released / spawned / checked / unlocked).
- Any exception before 8: today's `_stop_locked()` and `restart_fast_failed`, as G-A5, then the lock released.

**After the lock, on the same worker thread:**
1. **the old capture bounded:** a watchdog SIGKILLs the old capture if it still lives **300 ms** after the stop began.
   SIGTERM is not waited on for 2 s; the stop's `wait` then returns at once;
2. **the old audio's stop joined, cap 10 s** (the code's own bounds). Then:
   - row **`restart_fast_audio_stop`**: `restart_fast_audio_stop_ms` (the stop's duration),
     `restart_fast_audio_stop_end_ms` (after the entry), the capture's return code (`capture_returncode`; −9 =
     killed), `capture_killed_at_bound` (the watchdog fired), `joined` (within the cap);
3. **the new audio:**
   - under the lock, a check that the session is still this restart's (the spawned encoder alive);
   - then today's redundancy and `_session_io.start()` outside the lock (its own lock serializes it against any
     stop);
   - then under the lock again: if the session changed meanwhile (a stop or another start), `stop_stream()` undoes it;
   - row `restart_fast_audio` (`started` / `skipped` and why, `new_audio_ms`).

**The config row:** `restart_fast_unlock_config` (`kill_grace_s` 0.1, `capture_bound_s` 0.3, `audio_join_cap_s` 10)
beside G-A5's `restart_fast_config`.

**Absent = the adopted G-A5 behaviour, byte for byte:**
- `restart_fast_unlock` is imported only when both flags read `1`;
- `plugins/games.py`'s B24 items are `_restart_fast_unlock = None`, the import `if`, and the wire's `if
  _restart_fast_unlock is not None:` (which rebinds `self._restart_fast` and logs the config row);
- proof: the module's AST with them removed = HEAD's; `restart_fast.py` byte-identical to HEAD (sha256);
- B22's 13 tests unedited and green.

## 2. The target rows (hashed here)

| row | bound | how it is met |
| --- | --- | --- |
| **R1** the picture back (new activity → `session_started`) | **≤ 2.0 s at every return, including one with a 2.2-s old-audio stop** | the ready at the check's end. Return 1's numbers would give ≈ entry + 0.11 (released) + ~0.35 (spawn) + 0.75 + ~0.13 (the ready's resume) ≈ entry + 1.35, + its 0.55 s new activity → entry ≈ **1.9 s** |
| **R2** the old encoder's last frame forwarded | **≤ entry + 0.3 s** | the relay stopped before the kill (≈ entry + the lock + a few ms) |
| **R3** the lock held | **≤ the check's end** (`unlocked_ms` − `checked_ms` ≤ 20 ms) | released at 8 |
| **R4** two encoders' frames forwarded in one second after the kill | **none** | the relay closed from the kill until the new encoder's start, which is after the old one's reap |
| **R5** `session_ended` → the old report → `session_started` | **in order** | B22's client release still waits for the report; the ready ≥ the check's end |
| R6 | the old audio's stop logged after the ready (`restart_fast_audio_stop`), the new audio started (`restart_fast_audio` `started`), the first 2-s interval after `session_started` ≤ 15 underruns | the tail; the client's 3-s start-up wait |

## 3. Tests (`tests/restart_fast_unlock/`, new; B22's harness)

A real `NativeStreamManager` on a temp root, B22's fake processes / relay / session I/O (imported from
`tests/restart_fast`, unedited). Extended here:
- **a tracing lock** (holder, acquire and release times);
- **a frame generator:** every 16 ms each live encoder's frame is forwarded if the relay runs. It models the real
  hazard: a dying encoder forwards into any running relay;
- **a fake old capture** whose SIGTERM exit takes 2.0 s.

The tests:
- **a slow old-audio stop** (the capture's 2.0-s SIGTERM + 88 ms, as return 1):
  - the ready's `status()` returns at the check's end (≤ `checked_ms` + 50) and before the audio stop's end;
  - the watchdog kills the capture at 300 ms; `restart_fast_audio_stop` logged after the ready, with
    `capture_killed_at_bound` true, `capture_returncode` −9;
  - the new audio started after the stop;
- **a slow stop the watchdog cannot shorten** (a 2.2-s fake `pactl` stall, no capture): the ready still at the
  check's end; `restart_fast_audio_stop_ms` ≈ 2,200 logged after it;
- **a slow old-encoder exit** (450 ms after SIGTERM):
  - no old frame forwarded after entry + 0.3 s (after the relay's stop);
  - the SIGKILL at the 100-ms grace (`released_ms` ≈ 100-150);
  - no second in which both encoders' frames were forwarded after the kill;
  - one live encoder at a time;
- **the lock:** held by the worker from before the response to `unlocked_ms`; `unlocked_ms` − `checked_ms` ≤ 20;
  never held across the audio tail except the two short session checks;
- **the order:** `session_ended` → `restart_fast` → the response → the old report (+70 ms) → `restart_fast_done` →
  `session_started` → `restart_fast_audio_stop` → `restart_fast_audio`;
- a stop arriving during the tail: the new audio skipped or undone;
- failures as G-A5 (`restart_fast_failed`, the lock released);
- **absent:** with `PRIVYHUB_RESTART_FAST` alone, the plugin's `_restart_fast` is the adopted `RestartFast` (not the
  subclass); the unlock flag alone (without `RESTART_FAST`) imports nothing; `0` / `yes` / empty → nothing;
- **B22's 13 (`tests/restart_fast`) unedited and green; every suite under `tests/` green.**

## 4. Files

`companion/restart_fast_unlock.py` (new), `companion/plugins/games.py`, `tests/restart_fast_unlock/` (new). No
client change, so no APK: `6bddafc0…` (CONFIRMED) is the client for CL-B14. Record
`evidence/B24_RESTART_FAST_UNLOCK_2026-10-26.md` + `b24_2026-10-26/`; `patches/B24_RESTART_FAST_UNLOCK.md`.
