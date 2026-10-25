# B22 — the picture after a Home return: design, written before any B22 code

Baseline HEAD 13ccff5 + B21 (uncommitted). Queue: `handoffs/QUEUE_2026-10-24H.md` §B22. Rows: CL-B12 §4 cell 1
(`cl_b12_2026-10-24/runs/1_snes_5ghz_two_home_presses/`: the recovery log, heartbeats, the relay's per-second frame
log `native_frame_sizes.jsonl`, the journal) and the new sessions' client reports
(`logs/games/decoder_sessions/native_decoder_20261024_171831_675.json` = press 1's new session, posted at press 2;
`…_172343_666.json` = press 2's new session; read only).

## 0. Settled

### (1) The host's start, entry → response 2.19 / 2.00 s

Read from the code (`plugins/games.py` `native-stream-start`; `native_stream.py` `start` → `_start_linux_locked`), in
order, all inside the request and the manager's lock:
1. `guard_end`'s bookkeeping (`session_ended`, the ladder's end), `emulator.status()`, `note_stream_start`: cheap.
2. the preflight (ffmpeg / DISPLAY / xdotool / render node / the RetroArch pid), `AUDIO_CODEC.prepare`: cheap.
3. **`_stop_locked()`**:
   - `_host_telemetry.stop()`: a no-op on Linux (the telemetry is started on the Windows path only);
   - **`_session_io.stop_stream()` = the old audio's teardown, BEFORE the encoder is touched:** the sender's join
     (≤ 1 s), the audio capture's terminate + wait, the reader's join (≤ 1 s), two `pactl` calls, a timing snapshot;
   - **then** the encoder's terminate + `wait(timeout=5)` (on Linux the encoder is also the capture: x11grab in the same
     ffmpeg), the FEC relay's stop (thread joins ≤ 1 s each).
4. the new capture target (xdotool), the log header, the relay's start, the encoder's `Popen`;
5. **a fixed 0.75-s startup check** (`deadline = now + 0.75`, polling every 50 ms that the encoder and the relay live);
6. the audio redundancy, `_session_io.start()` (the controller ensured, the new audio started), `status()`.

The relay's per-second frame log (one row per second and per relay; the first frame of each encoder is its IDR, so the
encoder's phase is the `max_bytes_at_utc` sub-second) puts numbers on it, host clock:

| step | press 1 | press 2 |
| --- | --- | --- |
| the start's entry (`session_ended`) | 28.813 | 29.620 |
| the old encoder's last frame (36 / 14 frames into its last second, phase .013 / .158) | ~29.60 (+0.79) | ~30.39 (+0.77) |
| the new encoder's first frame (its phase .155 / .77-.79; 52 / 15 frames in its first second) | ~30.15 (+1.34) | ~30.77 (+1.15) |
| the response (journal; CL-B12) | 31.004 (+2.19) | 31.619 (+2.00) |

- **Entry → the old encoder's end, ~0.78 s:** the encoder is killed only after the old audio's teardown. That
  teardown is what holds the capture.
- **→ the new encoder's first frame, 0.38-0.55 s:** the encoder's exit, the relay's restart, xdotool, `Popen`, the
  VAAPI init.
- **→ the response, 0.85 s:** the fixed 0.75-s check, then the audio's start.
- So the teardown is ~0.8 s of the 2.0-2.2, not all of it. The rest is the new encoder's start (~0.45) and the fixed
  check plus the audio (~0.85).

**Can the teardown leave the response's path? Yes.** Nothing the client needs from the response depends on the new
encoder:
- the client reads `active`, `alpha_version`, `capture_backend`, `gop_frames`, the bitrate, the FEC fields,
  `capture_target` (display text only), `audio.active`, `controller.active`, `audio_cushion`, `audio_redundancy`,
  `heartbeat_interval_ms`, `stall_resume`, `guard_end`;
- at a guarded restart they are the running session's values (the same profile, window and client). A `status()`
  snapshot taken before the teardown carries them.

**Reusing the encoder** (the same client within N s) was considered and not taken:
- the stream's restart is what re-sends the IDR and the in-band SPS / PPS that a new client instance's decoder needs
  (the new activity has a new decoder);
- the host cannot force an IDR without a restart (B10);
- the audio sequence restart is the boundary B11 / B17 order around.

### (2) The client's `session_started` 8.8 s (press 1) / 4.2 s (press 2) after the response

The client's start-up gate (`updateStabilization`, every 500-ms metrics tick) releases only after:
- the host metadata (the response), the receiver, the decoder, no IDR wait, the host's audio and controller active;
- **then one baseline tick and `STABILIZATION_CLEAN_TICKS` = 6 consecutive clean ticks.** A clean tick has: a new
  frame rendered, no decoder drop, no queue overflow, queue depth 0, ≥ 45 fps, output gap ≤ 120 ms, rx → decode
  ≤ 150 ms. Any other tick resets the count to 0.
- **So response → ready is ≥ ~3.5-4.0 s by construction:** the response's next tick, + the baseline, + 6 × 500 ms,
  + the ready's POST.
- **Press 2's 4.15 s is that minimum:** no reset.
- **Press 1's 8.78 s is ~9 ticks more: at least one reset.**
  - The gate's per-tick reason is not logged.
  - The kept rows show press 1's queued-minus-rendered rising 18 → 21 between the 35.571 and 37.625 heartbeats. Press
    2's is flat (29, 29) after its start.
  - Press 1's session counted `queue_overflow_drops` 9 and `max_codec_ms` 854 against press 2's 7 / 150, over a
    shorter session.
  - A single reset at ~36.3 s fits the 39.79 ready. Which condition failed cannot be pinned from the kept rows.

**What the client did in those seconds** (session clock; t0 = `startSession`, ~28.52 / ~29.62 host):

| row | press 1 | press 2 |
| --- | --- | --- |
| the old stream's frames decoded (the new receiver hears the old encoder until its kill) | from 858 ms | from 445 ms |
| `ssrc_change` (the new encoder) | 1,531 | 1,213 |
| the first IDR after it (resync) | 1,775 (243 ms; 1 IDR rejected, 14 P dropped) | 1,227 (14 ms, FEC-recovered) |
| the decoder at the switch | **one 854-ms codec stall** (rx → decode 854, output gap 820, at 1,976) | an output gap of 577 ms at 1,250, no codec stall |
| the response (`hostMetadataComplete`) | ~2,486 | ~2,000 |
| the audio's first write (B11's rebuilt receiver, started at the response) | 2,720 | 2,190 |
| the ready (`session_started`) | ~11,270 | ~6,150 |

- **The picture was back at ~2.0 s (press 1) / ~1.3 s (press 2) after `startSession`**: the new stream's first
  decoded frames, 0.3-0.5 s before the host's response. The game stayed paused behind the start-up overlay for 3.5-9 s
  more, waiting on the gate.
- **The difference is the gate** (a reset in press 1), plus press 1's slower switch (a rejected IDR and the 854-ms
  codec stall). The configuration, the surface and the audio hold are the same in both: one decoder each, created from
  the old stream's SPS / PPS; the audio started at the response in both.
- **The clock, disclosed.** The events log is the onn's clock. The new activity reads 0.69-0.72 s before the host's
  entry there, against `create_to_start_ms` 280 / 96 on the client.
  - On the host's clock, `startSession` (t0) is heartbeat 1's receipt less its `elapsed_ms`: ≤ 28.52 / ≤ 29.62. The
    start's POST follows it at once (the same function hands to the session thread, which takes the pending and
    posts).
  - So the new activity is ≈ t0 − `create_to_start_ms` ≈ **28.24 / 29.5** (host clock), and the entry came 0.57 /
    ~0.12 s after it. Press 1's first POST took ~0.3 s to reach the host.
  - **CL-B12's 12.0 / 6.8 s (new activity → `session_started`) are ≈ 11.5 / 6.3 s on one clock.**

## 1. The design, host: `PRIVYHUB_RESTART_FAST=1`

New `companion/restart_fast.py`, imported by `plugins/games.py` only when the flag reads exactly `1`.

**Eligible** (else today's start, unchanged):
- the request carries `guard_end=1` (a guarded client restart; B17);
- the host is Linux;
- an old encoder is running (`_process` alive). Then a teardown exists, and the response's metadata is the running
  session's.

**At the request** (`RestartFast.start`, in the handler's thread, after today's bookkeeping and pause check):
1. today's validation (`_validated_ipv4`, `_validated_port`) and `host_resource_sampling.start` (idempotent);
2. today's preflight, read only: ffmpeg, DISPLAY, xdotool, the render node, the RetroArch pid alive. **The audio
   codec's refusal is checked read-only** (`AUDIO_CODEC.active` and opus not declared by the client → today's refusal
   text). Its `prepare` is NOT called here: it replaces the streamer's Opus session, which the old audio still uses. A
   failure raises today's `NativeStreamError` before anything is touched;
3. `snapshot = manager.status()` (the running session);
4. **the worker thread starts, takes the manager's lock, signals it holds it** (the request waits ≤ 2 s for that
   signal; a timeout logs `restart_fast_lock_wait` and the request goes on to wait for the lock the same way today's
   start would). **No other start, stop, encoder restart, ladder transition or `status()` can run between the response
   and the worker's end: the ready's `status()` waits on the same lock.**
5. **the response:** the snapshot + `"restart_fast": {"armed": true, "old_stream_active": true}`. The handler then adds
   today's keys (`game_session`, `paused`, `stabilization_required`, `heartbeat_interval_ms`, `stall_resume`,
   `guard_end`). One recovery row: `restart_fast` (`response_ms` from `RestartFast.start`'s entry).

**The worker** (under the lock; timings from the request's entry, monotonic):
1. **the old encoder first:** `_kill_managed_process(_process)` and `_capture_process` (terminate, `wait(timeout=5)`,
   kill). **The capture is released when the process has exited** → `released_ms`;
2. the rest of the old teardown **beside the new encoder**: `_session_io.stop_stream()` (the old audio) on its own
   thread, started now. `_host_telemetry.stop()` (a no-op on Linux) runs first, in today's order;
3. today's `_stop_locked()` field resets (relay stopped; `_process` / `_capture_process` / `_encoder_command` /
   `_client_port` None; the bitrate, width and height back to the profile's; `_last_capture_target`; the log handle
   closed);
4. **the new encoder, as today's start does it:** the capture target (xdotool), the same log header, the relay's start,
   `START_RUNG`'s kwargs, `_build_linux_ffmpeg_command`, the `encoder argv:` line, `Popen` → `spawned_ms`. **One
   encoder at a time on the capture:** the new `Popen` comes only after the old process's `wait` returned;
5. the old audio's thread joined → `audio_stopped_ms`; `AUDIO_CODEC.prepare` (today's call, now after the old audio
   stopped; a refusal fails the restart as below);
6. **today's startup check, 0.75 s from the `Popen`.** At least one check runs even if the audio's stop took longer
   than 0.75 s (today's loop runs zero checks once past its deadline; here one runs);
7. today's audio redundancy, `_session_io.start()` → `done_ms`; one recovery row `restart_fast_done` with the five
   timings;
8. **any exception:** today's `_stop_locked()` (the stream ends), one row `restart_fast_failed` (the error's type and
   ≤ 200 characters, no address). The client's gate then waits as today: no new stream, the ready refused by
   `status()` inactive ("Native stream is not active; gameplay remains paused"), the 15-s stability timeout.

**Unchanged:**
- today's start (every non-eligible request, and every request without the flag);
- the stop; the recovery's encoder restarts;
- the ready's handler: its `status()` now simply waits for the worker. **That is the safety net: no resume before the
  new encoder and the new audio are up.**

**The config row:** `restart_fast_config` (`startup_check_s` 0.75, `lock_wait_s` 2.0) at the plugin's wire.

**Expected (from §0's rows, not measured here):**
- response ≤ 300 ms after the entry (the bookkeeping + a `status()` snapshot; tested with fakes);
- the old encoder killed at ~entry + 0.05 instead of + 0.78;
- the new encoder's first frame ~entry + 0.45-0.6;
- the worker's end (the ready can complete) ~entry + 1.3-1.5: + the 0.75-s check, the old audio's stop overlapped
  with it, + the new audio's start.

## 2. The design, client: inside the existing `restart_guard` (default on), armed only by the host's key

`debug.privyhub.restart_guard` stays as B19 left it (on unless `0`). The new behaviour needs **both**:
- a guarded start (`restart != null`);
- the response's `"restart_fast": {"armed": true}`, sent only by a host with `PRIVYHUB_RESTART_FAST=1` on an eligible
  start.

Absent either → today. New `RestartFast.kt` (pure logic, JVM-testable) + the activity's wiring:
1. **The release at the new stream's first fresh frame**, not after 6 clean ticks. A 50-ms tick (B16's form), armed
   at the response, releases (today's `requestGameplayRelease`, the ready POST) at the first tick with all of:
   - the host metadata complete;
   - **the switch seen:** the receiver's `ssrcChanges` above its value just before the start's POST (when the host says
     `old_stream_active`). The old stream's frames are not the new encoder's;
   - the receiver not waiting for an IDR;
   - **a frame rendered after the switch:** the decoder's count above its value at the first tick that saw the switch;
   - the last output ≤ 100 ms old (B16's `freshMs`): press 1's 854-ms codec stall is waited out, not released into;
   - **the old report's post finished** (success or failure), or 1,000 ms since the response. That keeps ended →
     report → started in order on the host.
   - Today's gate keeps running beside it. **If the tick never fires (no switch seen, e.g. no old packet ever
     arrived), today's 6-tick release still comes.**
2. **The audio waits for the release.** B11's rebuilt receiver is created and configured at the response as today,
   but started when the ready's POST returns (released or not), no longer at the response.
   - Until then the host's old audio may still be sending: under the fast restart the old audio stops beside the new
     encoder, after the response.
   - The new audio starts in the worker, which the ready's `status()` waits on. **So at the ready's return the host's
     new audio is up and the old is gone. The receiver binds its socket at `start()` (`receiveLoop`), so it never
     hears the old stream.**
   - The game is paused until that release, so nothing audible is lost.
   - The failure path (a refused ready, `failStabilization`) starts it too.
3. **The report** (top-level keys, only when armed):
   - `restart_fast_released_by` `fast` / `gate`;
   - `restart_fast_response_to_switch_ms`, `restart_fast_switch_to_release_ms`, `restart_fast_response_to_release_ms`;
   - `restart_fast_report_wait_ms`;
   - `restart_fast_gate_resets` and `restart_fast_gate_last_reset`: today's gate's resets while armed, with the
     failed condition's name (`no_new_frame` / `dropped` / `overflow` / `queue` / `fps` / `gap` / `rx_decode`). This
     is (2)'s unlogged reason, for CL-B13.

**Not changed:** the decoder (press 1's 854-ms stall at the switch is not addressed: the release waits it out), the
surface, the receiver, B16's recovery fast ready, B17's order (the start first, the report after), the audio
receiver's own start-up hold.

## 3. The target, and the budget it rests on

**The picture back ≤ 3 s after the new activity on a LAN**, read as CL-B12 did: new activity → `session_started` (the
game running under a live picture). Expected on press 2's rows (host clock):
- the new activity ≈ 29.5;
- the start's entry 29.62 (+0.12); the response ≤ +0.42;
- the new encoder's first frame ≈ entry + 0.5 (the kill at once; today's 0.38-0.55 s to the new frame) → +0.63;
- its IDR and first decoded frame + 0.05-0.25 → ≈ +0.9; the tick's release ≤ +0.95;
- the ready's `status()` waits for the worker (≈ entry + 1.3-1.5) → **`session_started` ≈ +1.5-1.7.**

On press 1's (entry 0.57 s after the activity, the 854-ms stall) ≈ +2.4-2.6. **≤ 3 s in both, by ~0.5 s;** measured
only by CL-B13.

## 4. Absent = today, byte for byte

- **Host:**
  - `restart_fast` imported only when `PRIVYHUB_RESTART_FAST` reads `1`;
  - `plugins/games.py`'s B22 items are `_restart_fast = None`, the import `if`, the wire's `if _restart_fast is not
    None:` and the start's `if _restart_fast is not None and guard_end and …: … else: <today's start>`;
  - proof: the module's AST with those items removed (an `if` with that test replaced by its `else` body) = the
    predecessor's. `native_stream.py` unchanged.
- **Client:**
  - every added line runs only under `restartFast != null`, which is set only when the guard took a pending and the
    host's response carries the key;
  - the one changed line (the rebuilt audio's start at the response) is the same as today when `restartFast` is null;
  - proof: the added / changed lines listed, each identical to today without the key.
  - `restart_guard 0` → no guard → no key read.

## 5. Tests

- **Host, `tests/restart_fast/` (new), a real `NativeStreamManager` on a temp root** with fake processes (terminate /
  wait / poll on an injected clock), a fake relay, a fake session I/O, the capture target and `Popen` patched:
  - **a slow teardown** (the old encoder exits 1.0 s after its terminate, the old audio's stop 0.7 s, the new
    `Popen`'s spawn 0.3 s):
    - the handler (`plugins/games.py` loaded alone, B17's harness) returns **≤ 300 ms**, carrying `restart_fast`
      armed, `guard_end` and today's keys;
    - a concurrent `status()` (the ready) **waits until the worker's end**;
  - **no two encoders on the capture:** at the new `Popen` the old process has exited (a registry of live fake
    processes per window);
  - the old audio's stop runs after the kill and before the end; `prepare` after the old audio stopped; the startup
    check ran at least once;
  - **the rows in order:**
    - the fake host's client posts the start, the old report 70 ms after the response, and the ready at the switch;
    - the recovery and journal events read `session_ended` → `restart_fast` → the report → `restart_fast_done` →
      `session_started` (the ready's `status()` after the worker);
  - **failure:** `_select_capture_target` raising → `_stop_locked`, `restart_fast_failed`, `status()` inactive;
  - **not eligible** (no `guard_end`, no running encoder, the flag absent / `0`) → today's `start` called, no key;
  - absent → the module not imported; `tests/guard_end` and `tests/remote_ladder` green.
- **Client, JVM (`RestartFastTest`, B15 / B17's harness and B16's loopback receiver):**
  - the decision table (no switch / waiting for an IDR / no frame after the switch / stale output / the report pending
    → no release; then a release once);
  - **the real `RtpH264Receiver` on loopback:** SSRC A's frames, then SSRC B's IDR → `ssrcChanges` +1, no release on
    A's frames, the release at the first tick after B's IDR frame;
  - the report wait capped at 1,000 ms;
  - the audio: with the key the rebuilt receiver is started at the ready's return, not at the response; without the
    key at the response (B17's order, unchanged);
  - B17's slow fake host + the key: the start first, the report, the release after the report;
  - absent key / guard `0` → today's (B11 / B15 / B17 / B19 suites unchanged and green).
- **The APK** (B5 … B19 + B22) built offline in the copy with `--no-configuration-cache`, pinned, NOT installed.

## 6. Files

- **Host:** `companion/restart_fast.py` (new), `companion/plugins/games.py`, `tests/restart_fast/` (new).
- **Client:** `RestartFast.kt` (new), `NativeStreamActivity.kt`, `RestartFastTest.kt` (new).
- Record `evidence/B22_RESTART_FAST_2026-10-24.md` + `b22_2026-10-24/`; `patches/B22_RESTART_FAST.md`.
