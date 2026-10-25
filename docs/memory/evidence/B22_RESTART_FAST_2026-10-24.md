---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 13ccff5 (+ B21; the client = `20e3e339…`'s sources, CONFIRMED; B22 uncommitted)
---

# B22 — the picture after a Home return: the host's start answered before its teardown, the client released at the new stream's first fresh frame

**Classification: SETTLED + BUILT.**
- **Flags:** `PRIVYHUB_RESTART_FAST=1` (host). The client half is inside the existing `restart_guard` (default on),
  armed only by the host's response key.
- **Tests:**
  - host `tests/restart_fast` 13 green (a real `NativeStreamManager` with a slow fake teardown: **response 0.6-1 ms**
    of 300; no two encoders on the capture; the rows in order); `tests/guard_end` 2 green;
  - JVM **146 / 146** (`RestartFastTest` 10 new; B11 / B15 / B17 / B19 suites unchanged);
  - two mutations caught.
- **Proof:** host AST = the predecessor with B22's 4 items removed. Client: 72 added code lines in 12 hunks, each
  null-safe on `restartFast`, a read, or reached only with the key; 1 changed line equal to today's without it.
  **PROVEN.**
- **APK** (B5 … B19 + B22) **`6bddafc0…a927`**, pinned, **NOT installed.**
- NOT ADOPTED; no live run; nothing committed.

Design `b22_2026-10-24/design_written_before_code.md`, sha256 `c1fd8901…7fd82c3`, hashed **18:00:24Z (2026-10-25),
before any B22 code**.

## 0. Settled (CL-B12 cell 1's rows and the code)

### (1) The host's start, entry → response 2.19 / 2.00 s

The relay's per-second frame log gives each encoder's phase (its IDR is the second's largest frame), host clock:

| step | press 1 | press 2 |
| --- | --- | --- |
| the start's entry (`session_ended`) | 28.813 | 29.620 |
| the old encoder's last frame | ~29.60 (**+0.79**) | ~30.39 (**+0.77**) |
| the new encoder's first frame | ~30.15 (+1.34) | ~30.77 (+1.15) |
| the response | 31.004 (+2.19) | 31.619 (+2.00) |

**Read with the code** (`_start_linux_locked`), the 2.0-2.2 s are:
- **~0.78 s: the old audio's teardown** (`_session_io.stop_stream()`: the sender's join, the capture's terminate +
  wait, the reader's join, two `pactl` calls).
  - It runs **before** the encoder is touched. `_stop_locked()` orders telemetry (a no-op on Linux), audio, then the
    encoder.
  - So the capture (x11grab, inside the encoder's ffmpeg) is held for that long.
- **0.38-0.55 s:** the encoder's exit, the relay's restart, xdotool, the new `Popen`, the VAAPI init;
- **~0.85 s:** a fixed 0.75-s startup check, then the new audio's start.

**Can it be off the response's path? Yes.** At a guarded restart the response's fields are the running session's (the
same profile, window, client). Reusing the encoder was not taken: the restart is what sends the new decoder its IDR
and in-band SPS / PPS, and the host cannot force an IDR otherwise (B10).

### (2) The client's `session_started` 8.8 s / 4.2 s after the response

- **The start-up gate** (`updateStabilization`, every 500-ms tick) needs:
  - the host metadata, receiver, decoder, no IDR wait, and host audio + controller active;
  - **then a baseline tick + 6 consecutive clean ticks.** A clean tick has a new frame, no drop, no overflow, queue 0,
    ≥ 45 fps, output gap ≤ 120 ms, rx → decode ≤ 150 ms. Any other tick resets the count to 0.
  - **So response → ready ≥ ~3.5-4.0 s by construction.**
- **Press 2's 4.15 s is that minimum** (no reset). **Press 1's 8.78 s is ≥ 1 reset:**
  - its queued-minus-rendered rose 18 → 21 between the 35.571 and 37.625 heartbeats; press 2's stayed flat at 29;
  - the session counted `queue_overflow_drops` 9 and `max_codec_ms` 854;
  - **the failed condition was not logged** (now it is, §1).
- **What the client did** (the new sessions' reports; session clock from `startSession`):

  | row | press 1 | press 2 |
  | --- | --- | --- |
  | the old encoder's frames decoded (the new receiver hears it until its kill) | from 858 ms | from 445 ms |
  | `ssrc_change` (the new encoder) | 1,531 | 1,213 |
  | its first IDR | 1,775 (243 ms; 1 IDR rejected, 14 P dropped) | 1,227 (14 ms, FEC-recovered) |
  | the decoder at the switch | **an 854-ms codec stall** (output gap 820) | a 577-ms output gap, no stall |
  | the response | ~2,486 | ~2,000 |
  | the audio's first write (started at the response) | 2,720 | 2,190 |
  | `session_started` | ~11,270 | ~6,150 |

- **The picture was back ~2.0 s / ~1.3 s after `startSession`**, before the host's response. The game then waited
  behind the overlay on the gate. **The difference between the presses is the gate's reset, plus press 1's slower
  switch.** The decoder configuration, the surface and the audio are the same in both.
- **The clock, disclosed.** On the host's clock the new activity is ≈ `startSession` − `create_to_start_ms` ≈ 28.24 /
  29.5 (the events log is the onn's, ~0.5 s behind). **CL-B12's 12.0 / 6.8 s are ≈ 11.5 / 6.3 s on one clock.**

## 1. Built (`b22.diff`)

**Host, `companion/restart_fast.py` (new), behind `PRIVYHUB_RESTART_FAST=1`:**
- **Eligible:** `guard_end=1`, Linux, an old encoder running; else today's start.
- **At the request:**
  - today's validation;
  - the preflight, read only. The audio codec's refusal is checked without `prepare`, which would swap the Opus
    session under the old audio;
  - a `status()` snapshot;
  - a worker thread takes the manager's lock;
  - **then the response:** the snapshot + `"restart_fast": {"armed": true, "old_stream_active": true}`, plus today's
    keys. One recovery row `restart_fast` (`response_ms`, `lock_ms`).
- **The worker, under the lock:**
  1. **the old encoder killed first** (terminate, wait): the capture released (`released_ms`);
  2. the old audio's stop on its own thread, beside the new encoder;
  3. today's field resets (the relay stopped);
  4. **the new encoder as today's start makes it** (the capture target, the same log header, the relay, `START_RUNG`,
     the argv line, `Popen`), only after the old one's `wait` returned (`spawned_ms`);
  5. the old audio joined (`audio_stopped_ms`), then today's `AUDIO_CODEC.prepare`;
  6. **today's 0.75-s check from the `Popen`, at least one check** (`checked_ms`);
  7. the new audio (`done_ms`).
  - One row `restart_fast_done`, or on any exception today's `_stop_locked()` and `restart_fast_failed` (the error's
    type and ≤ 200 characters).
- **The ready's `status()` waits on the same lock.** No resume before the new encoder and audio are up; no other
  start, stop or encoder restart in between.
- A `restart_fast_config` row at the wire (`startup_check_s` 0.75, `lock_wait_s` 2.0).
- **`plugins/games.py`:** the import, the wire, and at the start `if _restart_fast is not None and guard_end and
  …eligible(…): payload = self._restart_fast.start(…) else: <today's start>`. `native_stream.py` unchanged.

**Client, inside `restart_guard`, armed only by the key (`RestartFast.kt` new, `NativeStreamActivity.kt`):**
- **The release at the new stream's first fresh frame.** A 50-ms tick from the response releases (today's ready
  POST) at the first tick with all of:
  - the host metadata;
  - **the switch seen:** `ssrcChanges` above its value at the start's POST;
  - **a frame rendered after the switch;**
  - no IDR wait;
  - the output ≤ 100 ms old. Press 1's 854-ms stall is waited out, not released into;
  - **the old report's post finished**, or 1,000 ms since the response.
  - Today's 6-tick gate keeps running beside it as the fallback.
- **The rebuilt audio receiver starts at the ready's return** (released or refused), no longer at the response. The
  host's new audio is up by then and the old one gone. The receiver binds its socket only at `start()`, so it never
  hears the old stream. The game is paused until then, so nothing audible is lost.
- **The report** (only when armed):
  - `restart_fast_released_by` `fast` / `gate`;
  - `_response_to_switch_ms`, `_switch_to_release_ms`, `_response_to_release_ms`, `_report_wait_ms`;
  - **`_gate_resets` and `_gate_last_reset`**: the gate's failed condition (`no_new_frame` / `dropped` / `overflow` /
    `queue` / `fps` / `gap` / `rx_decode`), (2)'s unlogged reason.
- **Not changed:** the decoder (the switch stall is not addressed), the surface, the receiver, B16's recovery fast
  ready, B17's order.

## 2. Tests

**Host (`tests_restart_fast_host.txt`, `host_fake_timeline.txt`).** A real `NativeStreamManager` on a temp root; fake
encoders on a per-window registry; the old encoder exits 1.0 s after its terminate, the old audio's stop takes 0.7 s,
the spawn 0.3 s; `plugins/games.py` loaded alone (B17's harness):
- **the handler's response in 0.6-1 ms** (the fakes are instant; bound 300 ms). It carries `restart_fast` armed,
  `guard_end` and today's keys;
- **the ready's `status()` waits for the worker** (> 1.5 s after the response);
- **no two encoders on the capture** (`max_live` {w1: 1});
- **the order:**
  - `session_ended` → `restart_fast` → the response → the old report (+70 ms) → `restart_fast_done` →
    `session_started`;
  - the kill → the exit → the new `Popen`; the old audio's stop began before the spawn and ended after it;
  - `prepare` after the old audio; the check ≥ 700 ms from the spawn;
- the check runs once even when the old audio took 1.2 s (past its deadline);
- **failures:**
  - a new encoder dying in the check → `restart_fast_failed`, the stream ended;
  - the capture target gone → `restart_fast_failed`, the old audio still stopped, `status()` inactive;
  - a codec refusal → refused in the request, nothing touched;
- a `status()` poll during the worker waits;
- **not eligible** (no `guard_end`, no encoder, not Linux), the flag absent / `0` / `yes` / empty → today's
  `start()`, no key;
- absent: nothing imported. `tests/guard_end` 2 green.
- **Mutations** (`tests_mutations.txt`, scratch copies):
  - spawning before the old encoder's exit fails `{'w1': 2} != {'w1': 1}`;
  - answering after the worker fails at **2.06 s** (today's figure with these fakes).

**The timeline with the fakes** (from the entry):

| ms | row |
| --- | --- |
| 0.7 | `restart_fast` / the response |
| 70.8 | the old report |
| 1,000.7 | the old encoder exited |
| 1,301.6 | the new encoder spawned |
| 1,701.3 | the old audio stopped |
| 2,052.1 | the new audio, `restart_fast_done` |
| 2,052.4 | `session_started` |

**Client (JVM, `tests_jvm.txt`, `tests_restart_fast_jvm.xml`), `RestartFastTest`, 10:**
- **the decision table.** No release before the response, without the metadata, on the old encoder's frames (no
  switch), with nothing rendered after the switch, while waiting for an IDR, or on a stale output (101 ms, −1). Then
  one release, named `fast`, with its timings;
- **the real `RtpH264Receiver` on loopback:** SSRC A's frames before and after the response → no release; SSRC B's
  P-frames → `ssrcChanges` 1, the IDR wait; B's IDR → **the release at the first tick after its frame**;
- **the report wait:** released 50 ms after the report is done; **capped at 1,000 ms after the response**;
- the gate's release named `gate`, its resets and last reason counted;
- the audio taken once;
- **B17's harness with the key** (300 ms per post): the start, the report, the ready, in order; the rebuilt receiver
  started **after the ready**, not at the response; `restart_cause` `via_start`, `host_ended_session`,
  `old_report_posted`;
- **without the key:** B17's order, the receiver at the response;
- `restart_guard 0` → no guard.
- **B11's 8, B15's 8, B17's 5, B19's 4: unchanged and green; 146 / 146.**

**Every host suite** (`tests_regression_after_b22.txt`, in the copy): the same outcomes as this queue's baseline plus `tests/restart_fast`: **27 `tests/` suites green**; the four `tools/` tests fail in the copy as at the baseline (fixtures under `docs/`).

## 3. The APK (`apk_sha256.txt`, `build_console.txt`)

- **`6bddafc0ac58999e200842ff482349408aefed87fa61f0a88f4f7fa19218a927`**, 9,638,278 B: B5 + B7 + B10 + B11 + B13 +
  B14 + B15 + B16 + B17 + B18 + B19 + **B22**.
- Built offline in `/tmp/b_q24h/PrivyHub` (`bash ./gradlew :app:testDebugUnitTest --rerun :app:assembleDebug
  --offline --no-configuration-cache`, 46 s) beside the companion and `privyhub-link-n1`. **0 tree `PrivyHub/` files
  newer than the build marker.**
- Same signer as `20e3e339…` (digest lines compared, not printed); `apksigner verify` OK. 944 entries as
  `20e3e339…`; **only `classes3.dex` differs** (377,988 → 389,044 B).
- **NOT installed.** `20e3e339…` stays CONFIRMED on the onn. A copy is at `/tmp/b_q24h_scratch/apk/app-debug.apk`.
- **With today's host (no `PRIVYHUB_RESTART_FAST`) this APK behaves as `20e3e339…`:** no key, no arm.

## 4. The target, and what CL-B13 measures

**The picture back ≤ 3 s after the new activity on a LAN** (new activity → `session_started`). Expected from §0's
rows, **not measured here:**
- **press 2's shape:** entry +0.12; response ≤ +0.42; the new encoder's first frame ≈ entry + 0.5 (the kill at once)
  → +0.6; its first decoded frame and the release ≈ +0.9; the ready waits for the worker (≈ entry + 1.3-1.5) →
  **`session_started` ≈ +1.5-1.7 s**;
- **press 1's shape** (entry +0.57, the 854-ms stall) ≈ **+2.4-2.6 s**.

**Rows for CL-B13, per return:**
- `restart_fast` `response_ms` ≤ 300 and its `at_utc` − `session_ended`'s ≤ 300 ms;
- `restart_fast_done` (`released_ms`, `spawned_ms`, `checked_ms`, `done_ms`);
- the journal: the start's response before the old report;
- the relay's frame log: the old encoder's last frame ≤ entry + 0.3, never two encoders' frames in one second beyond
  the switch;
- the client report: `restart_fast_released_by` `fast`, `_response_to_release_ms`, `_gate_resets`;
- **new activity → `session_started` ≤ 3.0 s** (the events read, less the clock offset; or `startSession` from
  heartbeat 1 less `create_to_start_ms`);
- the first 2-s interval after `session_started` ≤ 15 underruns.

## 5. Files

- **`b22_2026-10-24/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b22.diff`, `proof_flag_absent.py` / `.md`;
  - `tests_restart_fast_host.txt`, `host_fake_timeline.txt`, `tests_mutations.txt`, `tests_jvm.txt`,
    `tests_restart_fast_jvm.xml`, `tests_regression_after_b22.txt`;
  - `apk_sha256.txt`, `build_console.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `companion/restart_fast.py` (new), `companion/plugins/games.py`, `tests/restart_fast/` (new);
  - `RestartFast.kt` (new), `NativeStreamActivity.kt`, `RestartFastTest.kt` (new);
  - `patches/B22_RESTART_FAST.md`, `logs/b22_git_status.txt`.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of
  `privyhub-link-n1` touched; nothing fetched, deleted, adopted, installed or committed.
