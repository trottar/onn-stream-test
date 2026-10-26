---
memory_schema: 1
as_of: 2026-10-26
baseline_commit: 06c565e (G-A5 adopted beside it, uncommitted by A; B24 uncommitted)
---

# B24 — the fast restart unlocked: the ready at the new encoder's check, the old audio after it, the old encoder's frames stopped at the kill

**Classification: SETTLED + BUILT** behind **`PRIVYHUB_RESTART_FAST_UNLOCK=1`**, inside the adopted
`PRIVYHUB_RESTART_FAST=1` (G-A5).
- **Tests:** `tests/restart_fast_unlock` 10 green (three runs); B22's 13 (`tests/restart_fast`) unedited and green;
  every suite under `tests/` green; two mutations caught.
- **Proof:** absent = the adopted G-A5 behaviour. `plugins/games.py`'s AST = HEAD's with B24's 3 items removed;
  `restart_fast.py` byte-identical. **PROVEN.**
- No client change, so no APK: **`6bddafc0…a927` (CONFIRMED) is the client.** G-A6 not touched.
- NOT ADOPTED; no live run; nothing committed.

Design `b24_2026-10-26/design_written_before_code.md`, sha256 `23500f09…a35d4e`, hashed **03:32:18Z, before any B24
code**. Preconditions checked first: G-A5's record present; only the companion and `privyhub-link-n1` active.

## 0. Settled

### (1) The old audio's stop: 2,088 ms at return 1

- **The audio timing snapshot is the stop's last act.** Its file mtime is the stop's end:

  | return | the stop began (`released_ms`) | ended (after entry) | **the stop ran** |
  | --- | --- | --- | --- |
  | 1 | 123 | 2,211 | **2,088 ms** |
  | 2 | 221 | 424 | 203 |
  | 3 | 471 | 821 | 350 |
  | 4 | 421 | 773 | 352 |

- **The bounds in the code** (`_stop_linux_locked`):
  - the sender's join ≤ 1 s. The Opus sender waits on the stop event between frames and leaves in ≤ 10 ms;
  - **the capture: SIGTERM, `wait(timeout=2)`, SIGKILL;**
  - the reader's join ≤ 1 s. It leaves at the capture's EOF;
  - two `pactl` calls, ≤ 3 s each.
- **2,088 ms fits only the capture's 2-s wait expiring** (+ ~88 ms of the rest). At return 1 the audio capture did not
  exit on SIGTERM within 2 s and was SIGKILLed.
  - No kept row records the kill (the audio log has no timestamps). B24 now logs the capture's return code.
  - Why it hung is not in the files. Not tested: a monitor read blocked on an idle, suspended sink while the game
    was held.
- **Bounded:** ≈ 10 s worst case by the code; 0.2-0.35 s typical.

### (2) What the new ready needs

- **Only the new encoder's check and `prepare`.** The ready reads `status()` active, then resumes; it needs nothing of
  the audio.
- `prepare` is safe once the old stop has begun: the old sender holds its own session reference and has left within
  10 ms.
- The new audio does need the old stop (the same streamer, sink module and capture).
- **The client waits up to 3,000 ms for its first real audio packet** (`STARTUP_REAL_PCM_TIMEOUT_MS`) and counts no
  underrun meanwhile. So a new audio that starts after the ready is heard from its first packet: **no client change.**

### (3) The old encoder between the kill and its exit (123 / 221 / 471 / 421 ms)

- SIGTERM: ffmpeg stops its input, flushes the encoder and the RTP muxer, and exits.
- **G-A5 stops the FEC relay only after that exit**, so every flushed packet was forwarded. Hence the last frame at
  +0.35 / +0.39 s at returns 3-4.

## 1. Built (`b24.diff`)

**`companion/restart_fast_unlock.py` (new): `RestartFastUnlock(RestartFast)`,** the adopted class with its worker
replaced. The request half is inherited unchanged; `restart_fast.py` is not edited. `plugins/games.py` builds it in
place of `RestartFast` only when both flags read `1`, and logs `restart_fast_unlock_config` (`kill_grace_s` 0.1,
`capture_bound_s` 0.3, `audio_join_cap_s` 10, `startup_check_s` 0.75).

**The worker, under the manager's lock (taken before the response, as G-A5):**
1. the old audio's stop started first, on its own thread (its first act silences the old sender); a watchdog thread
   beside it;
2. **the relay stopped:** the old encoder's frames stop being forwarded here, whatever it flushes (`relay_stopped_ms`);
3. **the old encoder SIGTERMed;** the capture target selected meanwhile; **SIGKILL after a 100-ms grace**; reaped
   (`released_ms`). Its flushed frames go nowhere, so the graceful exit buys nothing;
4. G-A5's field resets;
5. **the new encoder** as G-A5's `_spawn_locked` makes it, with that target (`spawned_ms`). The `Popen` only after the
   old one's reap: one encoder on the capture;
6. `prepare`;
7. today's 0.75-s check, at least once (`checked_ms`);
8. **the lock released** (`unlocked_ms`). The ready's `status()` answers here. Row `restart_fast_done`.

**Beside it and after:**
- **the watchdog:** the old capture SIGKILLed if it still lives 300 ms after the stop began. Its SIGTERM `wait` is 2 s;
- **the old audio's stop joined** (cap 10 s), then row **`restart_fast_audio_stop`**: `restart_fast_audio_stop_ms`,
  `_end_ms` (after entry), `capture_returncode` (−9 = killed), `capture_killed_at_bound`, `joined`;
- **the new audio:** the session checked under the lock, `_session_io.start()` outside it, then checked again (a
  stop or another start meanwhile → `stop_stream()`). Row `restart_fast_audio` (`started`, `new_audio_ms`, `why`).
- **On a failure:** today's `_stop_locked()`, `restart_fast_failed`, the lock released; the old audio's stop still
  joined and logged; no new audio.

**Disclosed:**
- **The design said the stop's row is "logged after the ready".** With the capture bounded, the stop has usually
  ended inside the check's window, so the row is written at the lock's release, beside the ready. It comes after the
  ready only when a stop outlasts the check (tested with a 2.2-s stall). The ready never waits for it either way.
- **The first test run spawned a real `ffmpeg -window_id w1`, one per restart in the five tests that reach a spawn**: the new module's own `subprocess`
  reference was not yet patched in the test. Each printed its usage and exited (no input, no output), nothing was
  streamed, and none was left running. Patched since.

## 2. Tests (`tests_restart_fast_unlock.txt`, `host_fake_timeline_*.txt`, `tests_mutations.txt`)

B22's harness (imported as a module, unedited) plus a tracing lock, a frame generator (each live encoder's frame
forwarded every 16 ms while the relay runs) and slow fake audio stops.

- **Return 1's shape** (the old capture's SIGTERM exit 2.0 s, + 88 ms):
  - the response in 0.4 ms;
  - the watchdog's kill at 312 ms; the old audio stopped at 400 ms;
  - **the lock released and the ready at 1,160 ms** (G-A5's worker: ~2.2-2.4 s);
  - `restart_fast_audio_stop` (`_ms` 399.8, `capture_killed_at_bound` true), then the new audio started;
  - order `session_ended` → `restart_fast` → the response → the old report → `restart_fast_done` → the stop's row →
    the new audio.
- **A 2.2-s stall nothing can shorten** (no capture): the ready still at the check's end. `restart_fast_audio_stop_ms`
  > 2,100, logged > 0.5 s after the ready; the new audio after the ready.
- **A 450-ms encoder exit:**
  - the relay stopped at 0.8 ms, before the SIGTERM; **0 old frames forwarded after the kill**;
  - **the last old frame forwarded at −0.1 ms** (before the entry's own row); 47 new frames;
  - no second with both encoders' frames after the kill;
  - SIGKILL at the grace (`released_ms` 105); `max_live` 1; the old encoder's exit before the new spawn.
- **The lock:** the worker's main hold began before the response and ended ≤ `checked_ms` + 20 ms. The tail's other
  holds are the two session checks, each < 50 ms.
- **A stop during the tail** → the new audio skipped (`started` false); **a failure** → `restart_fast_failed`, the
  lock released, the stream inactive, the old audio's stop still logged.
- **Absent:**
  - `PRIVYHUB_RESTART_FAST` alone → the adopted `RestartFast`;
  - the unlock flag alone → nothing (no fast restart at all);
  - `0` / `yes` / empty → nothing;
  - fresh processes in four environs import nothing;
  - `restart_fast.py`'s sha256 = HEAD's.
- **Mutations:**
  - the relay stopped after the reap (G-A5's order) → the 450-ms test fails;
  - the tail under the lock → the 2-s capture, 2.2-s stall and stop-during-the-tail tests fail.
- **Every suite** (`tests_regression_after_b24.txt`, in the copy): the baseline's outcomes plus
  `tests/restart_fast_unlock`. The four `tools/` tests fail in the copy as at the baseline.

## 3. The rows, hashed, and what CL-B13's returns predict under B24

| row | bound |
| --- | --- |
| R1 the picture back (new activity → `session_started`) | ≤ 2.0 s at every return, including one with a 2.2-s old-audio stop |
| R2 the old encoder's last frame forwarded | ≤ entry + 0.3 s |
| R3 the lock held | ≤ the check's end (`unlocked_ms` − `checked_ms` ≤ 20) |
| R4 two encoders' frames in one second after the kill | none |
| R5 `session_ended` → the old report → `session_started` | in order |
| R6 `restart_fast_audio_stop` and `restart_fast_audio` `started`; the first 2-s interval ≤ 15 underruns | logged; met |

**CL-B13's four returns, re-timed with B24's order.** Assumed: the kill ~110 ms; the spawn as measured; the check
750 ms; the ready's resume as measured (109-130 ms). Not measured:

| return | released | spawned | check end | `session_started` after entry | new activity → entry | **picture back** |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ~110 | ~543 | ~1,293 | ~1,423 | 0.552 s | **~1.98 s** (CL-B13 3.12) |
| 2 | ~110 | ~465 | ~1,215 | ~1,338 | 0.059 | ~1.40 (1.74) |
| 3 | ~110 | ~463 | ~1,213 | ~1,322 | 0.084 | ~1.41 (2.00) |
| 4 | ~110 | ~451 | ~1,201 | ~1,318 | −0.107 | ~1.21 (1.76) |

- **Return 1 is tight against 2.0 s.** Its 0.55 s between the new activity and the start's entry (`create_to_start_ms`
  284 + the first POST's ~0.27 s) is outside the host.
- The capture target's xdotool time, now inside the kill's grace, comes off the spawn, which these numbers do not
  credit.

## 4. Files

- **`b24_2026-10-26/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b24.diff`, `proof_flag_absent.py` / `.md`;
  - `tests_restart_fast_unlock.txt`, `host_fake_timeline_slow_capture.txt` / `_slow_encoder_exit.txt`,
    `tests_mutations.txt`, `tests_regression_queue_i_baseline.txt`, `tests_regression_after_b24.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:** `companion/restart_fast_unlock.py` (new), `companion/plugins/games.py`, `tests/restart_fast_unlock/`
  (new); `patches/B24_RESTART_FAST_UNLOCK.md`; `logs/b24_git_status.txt`.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of
  `privyhub-link-n1` touched; nothing of A's touched (its uncommitted `tools/` and docs edits left as they are);
  nothing fetched, deleted, adopted or committed.
