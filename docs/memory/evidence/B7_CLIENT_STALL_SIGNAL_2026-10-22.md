---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 144e5c7 (+ B5 / B6 in the tree, uncommitted; B7's predecessors are those files)
---

# B7 — the client's stall signal: a picture-only drop pauses the game, and it resumes when the player can see again

**Classification: BUILT** behind `debug.privyhub.stall_signal=<1|ms>` (client) and `PRIVYHUB_STALL_SIGNAL=<1|ms>`
(host).
- **Host:** 12 tests with a fake client through the real receive loop, 3 runs green. B2 / B4 / B6's tests are
  unchanged and green. Flag absent = B6's files (whole-module AST identical, 4 files).
- **Client:** 6 JVM tests (91 / 91 with B5's). Property absent = B5's client (only added lines, all in the allowed
  forms).
- **The APK (B5 + B7) `cb0935c8…1080`** built offline and pinned, **NOT installed**.
- NOT ADOPTED; no live run; nothing committed.

Design `b7_2026-10-22/design_written_before_code.md`, sha256 `71ab1635…c890`, hashed **05:45:07Z, before any B7
code**.

## 0. What the data said first: S and the host's threshold

- **The floor, from the client's frame timing:**
  - a frame every 16.7 ms;
  - output stale at 60 ms (`DEFAULT_STALE_OUTPUT_MS`);
  - the gate's clean bound 120 ms (`STABILIZATION_MAX_OUTPUT_GAP_MS`).
  - **S must exceed 120: the queue's 150 is the floor.**
- **But the clean LAN has output gaps of 150-400 ms.** The client reports' retained top-16 gaps:
  - BENCH-R1 cell 8: 14 ≥ 150, 5 ≥ 200, 2 ≥ 300, max 395;
  - cell 2: 16 / 2 / 0, max 272;
  - UX-R2's sessions: max 109-534.
  - The list is saturated, so these are lower bounds.
  - **A host pausing at 150 would pause ≥ 14 times per 11.5-min session.**
- **So the client sends at S (150 by default) and the host decides:**
  - `PRIVYHUB_STALL_SIGNAL=1` acts at 150 (the queue's default); `=<ms>` (150-2000) acts later;
  - tunable without reinstalling;
  - BENCH-R2 runs 150 and 400.

## 1. What was built (`b7.diff`)

**Client** (`StallSignal.kt` new; `NativeControllerSender.kt` +9, `NativeStreamActivity.kt` +21,
`AvcLowLatencyDecoder.kt` +3):
- The controller sender's own 8-ms loop calls an optional `stallTick`, which sends on the controller socket a 24-byte
  `PHS1` datagram: kind, flags (bit 0 = in the recovery gate), seq, the last displayed frame's id (the rendered
  count), the output's age.
- **"Stalled" = output age ≥ S, or the client inside its recovery gate** (the full-screen black "Reconnecting"
  overlay, B6 §2): what the player cannot see. A `stall` goes out every 50 ms (20 / s), then one `stall_end` when
  gameplay is shown.
- Nothing is sent before the first frame or the startup gate.
- The report gains `stall_signal_ms` / `_stalls_sent` / `_ends_sent`, flag on only.

**Host** (`companion/stall_signal.py` new; `native_session_io.py` +11, `games/link_drop_recovery.py` +10,
`hold_rewind.py` +5, `plugins/games.py` +9):
- **The receive loop:** one guarded statement before the 36-byte size check parses and queues (it never blocks). A
  stall datagram is never a controller packet. **Absent: it is a bad packet, as any unknown datagram today** (tested).
- **Stall, age ≥ T (or the gate bit), while `PLAYING`:**
  - `_enter_recovery(trigger="client_stall")`: v2's own transition, `EmulatorManager.pause()`;
  - the rows: one `desync_pause` + one `client_stall` (the client's frame id, the age);
  - B4's rewinder gets the onset = the client's last displayed frame on the host clock (receive − age; the LAN's
    one-way delay taken as 0), through a new `Rewinder.set_pending`.
  - **The pause lands ~1-2 frames after the first stall.** `pause()` reads status first. The queue's "within one
    frame" would need a raw `PAUSE_TOGGLE`, which B2's rule forbids.
- **Stall while a hold stands** (the `@both` return): **B2's own handover** (`input_hold_handover`, trigger
  `client_stall`).
  - The design's `input_hold_to_client_stall` row became B2's own row: one owner, one row. Disclosed.
  - The pause, the episode and B4's earlier onset stay.
- **The race:** with B7 on, `note_input_release` waits ≤ 60 ms for a stall before releasing, because the first
  controller packet back beats the next stall datagram. **+≤ 60 ms on every true hold's release.**
- **Release** (reason `client_stall`):
  - on `stall_end`, or 300 ms with no stall (a lost `stall_end`);
  - B4's rewind first, then `resume_game()`, then `resumed via stall_end` / `stall_quiet`.
  - **The core resumes when the client shows gameplay, not behind its black overlay.**
- **A client ready within 20 s of a stall resume:** `recovered` (`client_ready_after_stall`), not a new session.
  - If the ready lands first, the gate's path resumes (without B4's rewind) and the later `stall_end` is a no-op
    (`stall_end_after_gate`).
  - A client desync during a stall pause is ignored (the stall owns it).

## 2. The two cases

- **`@down` (cell 7):** the stall datagrams arrive.
  - The core pauses at ~T + 1-2 frames after the client's last displayed frame, **instead of running ~2.2-2.6 s
    without a picture**.
  - It resumes with B4's rewind to that frame when the client shows gameplay.
  - Tested: the onset within ±30 ms of the client's last frame, then pause, rewind, resume.
- **`@both`:** the stall datagrams cannot arrive while dark, and the uplink hold (B2 / B6) pauses.
  - At the return the client is still stalled or in its gate. Its stall arrives within ~50 ms and takes the hold over.
  - The release waits for `stall_end`.
  - **This closes B6's latent interaction** (the game run behind the black overlay, then the session restarted).
  - Tested through B1's real uplink gate: one pause, the handover, no `input_release`, `resumed via stall_end` at the
    client's gate end, with the rewind first.

## 3. Tests

- **Host, `tests/stall_signal`: 12 OK** (3 runs; from the tree):
  - the parse;
  - `@down` (pause, the onset ±30 ms, `stall_end` with the rewind; below T nothing; a lost `stall_end` resumes
    after 300 ms);
  - `@both` (the handover; without a stall, B2's release after the short wait, held ≈ 1,000 ms);
  - a ready after a stall resume is not a session;
  - the ready first, then `stall_end`: one resume;
  - a desync during a stall pause is ignored;
  - B4's `set_pending` (the counter less 4);
  - flag absent: no import, and a stall datagram is a bad packet;
  - the hook shapes.
  - *Fixed during testing, disclosed:*
    - `stall_end_after_gate` was logged for episodes the host never acted on (now only after a stall pause or
      takeover);
    - the harness sent several `stall_end`s and counted its own end-of-run silence. Both fixed in the test.
- **Client, `StallSignalTest` 6:**
  - the flag;
  - the 24-byte encoding;
  - nothing before the first frame / the startup gate;
  - 9 stalls over a 500-ms stall in the 8-ms loop (~20 / s, not 62), then exactly one `stall_end`;
  - the gate keeps the stall with fresh frames;
  - a new episode.
  - The suite is **91 / 91** (78 + 7 + 6).
- **The rest:** B6 16, B2 19, B4 22, impairment 29, and the regression set (`tests_regression.txt`), all OK.
  C3-F1's pre-existing error, and the golden fixture the copy lacks.
- **Proofs:**
  - `proof_flag_absent_host.md`: **4 identical**;
  - `proof_flag_absent_client.md`: **0 lines changed** (21 / 9 / 3 added, all in the allowed forms).

## 4. The APK (`apk_sha256.txt`, `build_console.txt`, `tests_apk.txt`)

**`cb0935c8cadd5ee65a3f52f390d0994899de27ebaa5c207b547e57185e761080`**, 9,757,709 B, carries B5 + B7.
- Both properties appear in `classes3.dex`.
- Built offline in `/tmp/b_q22c/PrivyHub` with `--no-configuration-cache` (B5's incident), only the companion active.
  **0 tree files newer than the marker.**
- Same signer as the installed `93d29b4a…` (digests compared, not printed).
- **NOT installed.**

## 5. For BENCH-R2 (session A)

- **Install** `cb0935c8…` (`adb install -r`, after preserving `93d29b4a…`); read it back.
- `setprop debug.privyhub.stall_signal 1`.
- **`@down`:** `PRIVYHUB_IMPAIRMENT=blackout-4s@down,every=120s,seed=1` + `PRIVYHUB_STALL_SIGNAL=1` (+
  `PRIVYHUB_INPUT_HOLD=1`, `PRIVYHUB_INPUT_HOLD_REWIND=1` for the rewind).
  - Expected per blackout: one `desync_pause client_stall` within ~0.2 s of the client's last frame, then
    `resumed via stall_end` when the client shows gameplay. No game running without a picture.
- **`none` with everything on, `PRIVYHUB_STALL_SIGNAL=1` vs `=400`:** stall pauses per 10 min. Expected many at 150
  (the reports above), few at 400.
- **`@both` with B1b's gate + hold + B6 + rewind + stall:** the handover rows, the resume at `stall_end`, no
  `session_started`.

## 6. Files

**`b7_2026-10-22/`:**
- `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ `predecessor_note.txt`),
  `predecessor_sha256.txt`, `after_sha256.txt`;
- `design_written_before_code.md`, `design.sha256`, `design_hashed_at.txt`;
- `b7.diff`;
- `proof_flag_absent_host.py` / `.md`, `proof_flag_absent_client.py` / `.md`;
- `tests_stall_signal.txt`, `tests_regression.txt`;
- `build_started_at.txt`, `build_console.txt`, `tests_apk.txt`, `apk_sha256.txt`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

**Elsewhere:** `companion/stall_signal.py` (new), `native_session_io.py`, `games/link_drop_recovery.py`,
`hold_rewind.py`, `plugins/games.py`, `tests/stall_signal/test_stall_signal.py` (new);
`PrivyHub/app/src/main/java/streaming/StallSignal.kt` (new), `NativeStreamActivity.kt`, `NativeControllerSender.kt`,
`AvcLowLatencyDecoder.kt`, `PrivyHub/app/src/test/java/streaming/StallSignalTest.kt` (new);
`patches/B7_CLIENT_STALL_SIGNAL.md`; `logs/b7_git_status.txt`.

The rules held:
- no stream, no restart, no adb, no sudo, no nft;
- the Opal untouched;
- gradle offline with only the companion active;
- nothing fetched, nothing deleted;
- nothing of A's touched.
