# B7 — the client's stall signal (the downlink-only drop): design (written and hashed before any B7 code)

Queue `handoffs/QUEUE_2026-10-22C.md` item B7, session B. Predecessors: B6's companion files (in the tree,
uncommitted), B5's `NativeStreamActivity.kt`, HEAD's `NativeControllerSender.kt` / `AvcLowLatencyDecoder.kt`
(`predecessors/`).

## 0. From the code and the bench

- **Cell 7 (`@down`):** the controller stream never stopped. The game ran on with the player's input and **no picture
  for ~2.2-2.6 s**, until the client's `native-stream-desync` (`client_output_silence`, sent at 1 s of output silence
  over HTTP) paused it.
- **The client knows its output gap at any moment:** `AvcLowLatencyDecoder.lastOutputAgeMs()` (ms since the last
  rendered frame). The 500-ms metrics tick reads it for the gate. Desync fires at `DESYNC_MS = 1,000`.
- **The floor for S, from the client's frame timing:**
  - 60 fps = a frame every 16.7 ms;
  - the decoder calls output stale at 60 ms (`DEFAULT_STALE_OUTPUT_MS`);
  - the gate counts a tick clean only with the max output gap ≤ 120 ms (`STABILIZATION_MAX_OUTPUT_GAP_MS`).
  - **So S must exceed 120 ms; the queue's 150 (9 frames) is the floor.**
- **But clean sessions do have gaps of 150-400 ms:**
  - the client reports' top-16 output-gap events, BENCH-R1 cell 8: 14 of 16 ≥ 150, 5 ≥ 200, 2 ≥ 300, max 395;
  - cell 2: 16 / 2 / 0, max 272;
  - UX-R2's sessions: max 109-534.
  - The top-16 list is saturated, so ≥ 14 per ~11.5 min is a lower bound.
  - **A host that pauses at 150 would pause ≥ 14 times per session on the clean LAN.** That is B6's lesson again.
- **So the client sends at S (the floor, 150 by default) and the host decides when to act.**
  - `PRIVYHUB_STALL_SIGNAL=1` acts at 150 (the queue's default); `=<ms>` (150-2000) acts at that age. A can tune it
    without reinstalling.
  - BENCH-R2 should run 150 and 400 on the `none` cell. At ≥ 400 the clean reports on file show 0-2 per session.
- **The client's recovery gate** (≥ 1 s of output silence): a **full-screen black overlay** until 3 clean 500-ms
  ticks pass (B6 §2). While it stands the player sees nothing, even with frames decoding. **So "stalled" for the
  signal = output age ≥ S, OR the client in its recovery gate.**

## 1. The datagram (client → host, the controller socket, 24 bytes, little-endian)

```
"PHS1" | u8 kind (1 = stall, 2 = stall_end) | u8 flags (bit 0 = in the recovery gate) | u16 0 | u32 seq
       | i64 rendered frames (the last displayed frame's id) | u32 output_age_ms (age at send)
```

- Sent by the controller sender's own loop (every ~8 ms; one socket, already connected to the host):
  - while stalled, one `stall` every 50 ms (**20 / s**);
  - when gameplay is shown again (output fresh and not in the gate), **one `stall_end`**.
- Only once the session has passed its startup gate. Before the first frame, nothing.
- **The host maps the last displayed frame to its clock** as `receive time − output_age_ms` (the one-way delay on a LAN
  is a few ms and is taken as 0; stated). `rendered frames` is logged as the id.
- **Absent** (`debug.privyhub.stall_signal` empty or invalid) = no monitor, no datagram. The sender's loop is today's.
  - `1` → S = 150; `120 < n ≤ 2000` → S = n.
  - **The host absent = today:** a 24-byte datagram fails the 36-byte size check and is counted in `bad_packets`,
    exactly as any unknown datagram is today.

## 2. The host (`PRIVYHUB_STALL_SIGNAL=1|<ms>`; new module `companion/stall_signal.py`; one owner: the recovery)

- **The receive loop:** one guarded statement before the size check, `if self._stall_signal is not None and
  self._stall_signal.on_datagram(data, now): continue`.
  - It parses (never blocks) and hands events to one worker thread, like B2's dispatcher.
  - B1's uplink gate runs before it, so a `@both` blackout drops these too.
  - A stall datagram is not a controller packet: it resets no silence timer and releases no hold.
- **`stall` with `output_age_ms` ≥ the host's threshold T, state `PLAYING`:**
  - `_enter_recovery(trigger="client_stall")`: v2's own transition, `EmulatorManager.pause()`, one `desync_pause`
    row (`trigger: client_stall`, `client_frame`, `age_ms`).
  - **The pause lands ~1-2 frames after the first stall arrives.** `pause()` reads `GET_STATUS` first (≤ 1 frame),
    then the toggle lands at the next poll. The queue's "within one frame" would need a raw `PAUSE_TOGGLE`, which
    B2's rule forbids. Stated.
  - **The onset for B4:** the client's last displayed frame on the host clock. If B4's rewinder is wired, it gets a
    pending hold (onset, the confirmed pause, the episode key) through a new `Rewinder.set_pending`, the same
    counter as B4 (less its 4-frame lag).
- **`stall` while a hold stands** (`input_hold`, the `@both` case after the return): **the pause converts to
  `client_stall`.**
  - One `input_hold_to_client_stall` row. No second pause, `_state_since` unchanged, so B4's pending hold (the
    uplink's onset, earlier and truer) stays.
  - The hold's own release then finds the reason changed and does nothing (B2's own check).
- **The race at a `@both` return:** the first controller packet back (430 / s) beats the next stall datagram
  (20 / s).
  - With B7 on, `note_input_release` first waits ≤ 60 ms (> one stall interval) in the hold's worker for a stall.
  - If one arrives, the conversion above applies and the release is skipped. If not, B2's release as today.
  - The cost: +≤ 60 ms on every true hold's release, with B7 on.
- **Release, reason `client_stall`:**
  - on `stall_end`, or, if `stall_end` is lost, on 300 ms with no stall datagram while the episode is the stall's (the
    client sends 20 / s while stalled);
  - B4's rewind (`via stall_end`) first, then `resume_game()`, then `resumed via stall_end`.
  - Since the client sends `stall_end` only when it shows gameplay (output fresh and its gate passed), **the core
    resumes exactly when the player can see it again.**
  - Fallbacks: the client's ready (`note_stream_ready`) and v2's give-up save, as today.
- **A client ready within 20 s of a stall resume** while `PLAYING`: `recovered` (B6's R3, for B7's own resumes), one
  `client_ready_after_stall` row. Not a new session, so no ladder reset.
  - The race: the client sends `stall_end` (UDP) and its ready (HTTP) at the gate's release. Usually `stall_end`
    lands first.
  - If the ready lands first, the gate path resumes (without B4's rewind) and the later `stall_end` is a no-op, one
    `stall_end_after_gate` row.
- **A client desync during a `client_stall` pause** (`client_output_silence` at 1 s): ignored, as any trigger during a
  non-hold pause is today. The stall owns the episode.

## 3. The two cases, stated

- **`@down` (the uplink alive):**
  - the stall datagrams arrive; the core pauses ~(T + 1-2 frames) after the client's last frame;
  - it resumes when the client shows gameplay again, with B4's rewind to the last displayed frame;
  - **cell 7's fix: unattended play without a picture ≈ T + 2 frames instead of ~2.2-2.6 s, and with the rewind ≈ 0.**
- **`@both`:**
  - the stall datagrams cannot arrive while dark, and the uplink hold (B2 / B6) pauses;
  - at the return the client is still stalled or in its gate, so its stall datagrams arrive within ~50 ms, the hold
    converts to `client_stall`, and the release waits for `stall_end`;
  - **this closes B6's latent interaction** (the game run behind the black overlay, then the session restarted).

## 4. Tests

**Host** (`tests/stall_signal/`; a fake client sending real datagrams through the real receive loop and the real
recovery; B2 / B4 / B6 tests unchanged):
1. the parse and the flag table;
2. `@down`: stall ≥ T pauses (`client_stall`, the row, `client_frame`), and the rewind's pending onset = receive −
   age; `stall_end` resumes, rewind first; below T nothing;
3. the lost `stall_end`: resume after 300 ms of no stall;
4. the conversion: a hold, then a stall: one pause, one row, the hold's release ignored, `stall_end` resumes;
5. the race: a release with a stall within 60 ms is deferred; without one, B2's release (+ the wait);
6. a ready after a stall resume: `recovered`; a ready first, then `stall_end`: one resume, the row;
7. flag absent: no import; a 24-byte datagram is a bad packet as today; the AST proof.

**Client** (`StallSignalTest`, JVM, fake clock):
1. the flag (`1` → 150, `400`, ≤ 120 / garbage off);
2. the encoding (24 bytes, the fields);
3. no datagram before the first frame or the startup gate;
4. age ≥ S gives a `stall` every 50 ms (20 / s), not every 8-ms loop;
5. the gate held gives stall continues with flag bit 0 though frames are fresh;
6. fresh and released gives exactly one `stall_end`;
7. a new episode afterwards.

The APK carries B5 + B7, built offline (`--no-configuration-cache`, the tree checked untouched), pinned, NOT installed.
