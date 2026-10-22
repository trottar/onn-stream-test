---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: aa884a3 (B1's edits in the tree, uncommitted; B2's predecessors for native_session_io.py / plugins/games.py are B1's files)
---

# B2 — the fast input hold (the game freezes with the player instead of running on without them)

**Classification: BUILT behind `PRIVYHUB_INPUT_HOLD`; unit-tested with a fake clock and the real receive loop; flag
absent = today (AST-identical hooked functions, not imported, the recovery suite green); `tools/unattended_frames.py`
written and run as the baseline; NOT ADOPTED; no live run; nothing committed.**

Queue `handoffs/QUEUE_2026-10-22B.md` item B2, session B. Design `b2_2026-10-22/design_written_before_code.md`, sha256
`37549c7d…aebc`, hashed **00:50:33Z, before any B2 code edit**.

## 0. Settled first, from the code: the client sends its controller state continuously

`NativeControllerSender.kt`, `sendLoop()`:
- `while (running)`: for **each of the 4 players, unconditionally**, one 36-byte `PHI1` packet with the whole state;
  then `Thread.sleep(8)`. There is no change test.
- That is ≈ 430 packets / s with or without input, and the host's `_receive_loop` comment says the same.
- **A silence is the link (or the client), not a still player, so B2 went ahead.** No "every-tick sender" task was
  needed.

## 1. What was built

**The flag:** `PRIVYHUB_INPUT_HOLD=<H ms>`:
- 100-4000 = H; `1` / `on` = **250**;
- absent = today;
- `0`, out of range or anything else = ignored, one `input_hold_config` row (a valid value also writes its row once).

**One owner: recovery v2's own state machine** (`companion/games/link_drop_recovery.py`, +85 lines):
- **`note_input_hold(age_ms)`** is `_enter_recovery(trigger="input_hold")`, v2's own transition. It acts only from
  `PLAYING`, pauses through `EmulatorManager.pause()` (which reads RetroArch's state and confirms `PAUSED`; never a
  raw `PAUSE_TOGGLE`), and writes **one `desync_pause` row with `trigger: input_hold`**.
- **`note_input_release(held_ms)`** acts only while the pause is still the hold's own. It resumes through
  `EmulatorManager.resume()` and logs `resumed`, `via: input_release`, `held_ms`.
  - If the resume fails, it hands over to `controller_silence`, so v2's controller-return exit applies, and logs
    `input_release_failed`.
- **The handover** (one guarded statement in `_enter_recovery`):
  - A different trigger during a hold (v2's `controller_silence` at 5.35 s, or the client's `client_output_silence`
    / desync) takes the pause over. The reason changes, v2's exit state is cleared, and one `input_hold_handover`
    row is written.
  - There is **no second `pause_game` call and no second pause row.** `GIVE_UP_MS` counts from the one pause.
  - v2's exit, its encoder restart and the client's ready gate then apply as today, and `input_release` no longer
    acts.
- The client's ready gate (`note_stream_ready`) resumes a hold as it resumes any `PAUSED_RECOVERING`.

**The detector** (`companion/input_hold.py`, new, 157 lines; `native_session_io.py` +15 over B1):
- A class attribute `NativeControllerBridge._input_hold = None`, a setter, and two guarded statements in
  `_receive_loop`: in the timeout branch `on_quiet(now, last_any_packet_at)`, and on each accepted packet
  `on_packet(now)`.
- **The loop never blocks:** events go to one worker thread (`HoldDispatcher`), which calls the recovery methods in
  order. Detection is H to H + 50 ms (the loop's wake).
- With B1's uplink blackout, the dropped packets drive the same timeout branch, so the bench exercises exactly this
  path.

**The rate limits:**
- **minimum hold 50 ms** (≥ 2 frames: a release waits until the pause has stood 50 ms; pause / resume themselves wait
  for RetroArch's confirmed state);
- **at most 6 holds in any rolling 60 s.** Past the cap, no hold, one `input_hold_cap` row per window; v2's 5.35-s
  trigger still protects;
- **the user's own pause wins:** no hold if the emulator is already paused; one `input_hold_skipped_paused` row per
  episode.

**The wiring** (`plugins/games.py` +9 over B1): a guarded module-level import and one guarded call in the plugin's
`__init__`, after v2's wiring.

## 2. What it costs the player (stated, from the code; not measured)

- **Without input for up to H + ≤ 50 ms** (≈ 18 frames at 250) before the freeze, instead of the outage's length
  (UX-R3: ~4 s), plus `EmulatorManager.pause()`'s RetroArch round trip.
- **The picture during a hold:** the encoder captures the RetroArch window with `x11grab` at a fixed `-framerate`
  and encodes VBR (`-b:v` / `-maxrate` / `-bufsize`, no filler; `native_stream.py`).
  - A paused RetroArch keeps its last frame on screen, so **the stream keeps sending that frozen picture** as small
    P-frames plus the periodic IDR (`-g`).
  - On a dead link the client sees nothing until it returns, then the frozen, current frame.
  - **Measured since, from the record:** during Sunday's recovery pause (05:10:03-05:10:08Z, `desync_pause` →
    `resumed`) the host's frame-size log shows **60 frames / s** (49 in the encoder-restart second). The stream does
    keep flowing on a paused core.
- **On release:** `EmulatorManager.resume()`'s round trip, a few frames.
- **False holds on a clean link:** every host-side controller gap ≥ H is a pause / resume pair. The baseline (§4)
  gives last night's rate.

## 3. Tests (`tests_input_hold.txt`, `tests_regression.txt`)

**`tests/input_hold`: 19 OK.**
- The flag table.
- **The detector (fake clock):** < H nothing; ≥ H exactly one hold; repeated quiet still one; the first packet one
  release with `held_ms`; never before a first packet; the cap (6 in 60 s, then 2 capped, one `cap` row, holds again
  after the window).
- **The recovery machine (fake callbacks):**
  - a hold then a release (`pause`, `resume`; `desync_pause input_hold`, `resumed input_release`);
  - **v2's 5.35-s silence during a hold: one `pause` call, one `desync_pause` row, one handover; the release
    ignored; v2's controller-return exit resumes once**;
  - the client's desync hands over;
  - the ready gate resumes a hold;
  - a failed resume hands over to `controller_silence`;
  - no hold unless `PLAYING`;
  - without the hold, today's behaviour (a desync during a v2 pause ignored).
- **The dispatcher:** the 50-ms minimum hold; the user's pause wins (no call, one skipped row); the cap row.
- **The hooks:** 2 + 1 guarded statements, the guarded import; a fresh process with no flag imports no `input_hold`.
- **The real receive loop with B1's 1-s uplink blackout:** one `desync_pause input_hold` with `age_ms` 250-320, and
  one `resumed` with `held_ms` ≈ 1,000.
- **The reader** (`tools/unattended_frames.py`) on synthetic logs: the episodes, the raw count and the core-running
  count.

**The regression set, in the copy, B1 and B2 in place, all OK:**
- impairment 29; **the recovery suite (E3-R2's) 17**;
- overlay 17, session_identity 88, audio_codec 20, encoder_rc 16, wan_adaptation 23, wan_telemetry 18,
  remote_ladder 26, remote_cap 16, start_rung 17, lan_loss_rule 21;
- adaptive_bitrate_shadow 21, native_source_contract 7, c5_m1 14;
- adaptive_bitrate_live 126 (its golden test from the tree, as in B1).

C3-F1's 1 error is pre-existing.

**Flag absent** (`proof_flag_absent.py` → `proof_flag_absent.md`): the function holding each B2 statement, those
statements removed, against the predecessors:

| file | function | |
| --- | --- | --- |
| `native_session_io.py` | `_receive_loop` | **identical** (new: `set_input_hold`, the class attribute) |
| `plugins/games.py` | `__init__` | **identical** |
| `games/link_drop_recovery.py` | `_enter_recovery` | **identical** (new: `note_input_hold`, `note_input_release`, `INPUT_HOLD`) |

**One fix found by the tests, disclosed:** B1's test helper stubbed `_neutralize(player)`, but the receive loop's exit
calls `_neutralize()` with no player. The helper's thread raised at the end of a run. The stub now takes an optional
player. B1's proof was re-run with it.

## 4. The measure: "unattended frames" (`tools/unattended_frames.py`; the baseline `unattended_ux_r1.json`, `unattended_ux_r2.json`)

- **Definition:** host frames emitted while no controller packet had arrived for ≥ 250 ms.
- **How it is computed:**
  - each control-gap row's span from start + 250 ms to end, against the frame-size log's frames per second, prorated;
  - **episodes** are gaps less than 500 ms apart;
  - **per 10 min** is over the seconds that carried frames;
  - **held episodes per H** are the episodes with one gap ≥ H.
- It reads only the directory it is given. This baseline ran over UX-R1's and UX-R2's preserved copies, read only.
- **Two counts, disclosed as a correction to the queue's wording.**
  - `unattended_frames` is the definition as written: every host frame in those spans.
  - **The encoder keeps sending the frozen picture at the full rate while the core is paused** (§2, measured), so
    that count cannot show a pause.
  - **`unattended_frames_core_running`** also subtracts recovery's paused spans (`desync_pause` → `resumed` /
    `session_ended` / `session_started`, from the recovery log in the same directory): the frames the game advanced
    without the player. **This is the number the hold exists to cut, and the one BENCH-R1 should read.**

| | **Sunday (UX-R1), 04:19-05:23** | **Last night (UX-R2), 04:42-05:27** |
| --- | ---: | ---: |
| streaming seconds | 3,506 | 2,389 |
| controller gaps > 250 ms / episodes | 289 / 147 | 36 / 23 |
| unattended frames, raw (per 10 min) | 4,110 (703) | 564 (142) |
| **unattended frames, core running (per 10 min)** | **3,999 (684)** (the two recovery pauses subtracted) | **564 (142)** (no recovery pause) |
| episodes an H of 250 / 500 / 1,000 would hold, per 10 min | 25.2 / 11.5 / 4.1 | 5.8 / 1.8 / 0.5 |

**The named windows:**
- **the death (R2, 04:54:55-04:54:59Z): 83.8 unattended frames.** Five gaps of 967 / 350 / 341 / 546 / 442 ms, which
  is 2.65 s silent.
  - With H 250, the hold pauses 250 ms into each gap, and the first packet of each return releases it. Five short
    pauses, each ~0.25 s late, instead of ~84 frames run without the player.
- **R2 04:56-05:03Z** (UX-R3's second-death window): 6.6 frames. Three gaps of 276-297 ms; each would be a hold of
  ~30-50 ms.
- **Sunday's bursts:** 05:06 → 714.6 (52 gaps), 05:10-05:11 → 544.6 (48), 05:20-05:21 → 1,065.9 (79).
  - **The cap (6 holds in 60 s) would hold only the first 6 episodes of such a minute.** After that the game runs on
    until v2's 5.35 s. The cap is set for "a flapping link cannot pause / resume faster than the core can follow".
    Whether 6 is too low for Sunday's room is for the bench and the user.
  The step 04:56-05:05 → 271.7 (39 gaps, many of 434-991 ms).

**Read with care:**
- The largest episodes include the user's own actions, which the measure counts too:
  - R2's 05:08:58 (11.95 s) is the user's Zelda pause;
  - R1's 04:26 / 04:35 / 04:36 (6.5-9.3 s) are Load States restarting the client session.
- They are host frames emitted with no input, whatever the cause. In those seconds the frame rate itself fell, so the
  counts are frames actually emitted.
- The bench (B1's blackout) has no such confound.

## 5. For BENCH-R1 (session A)

- **The cells:** B1's `blackout-4s@both,every=120s` with **`PRIVYHUB_INPUT_HOLD=250`** on vs absent, and
  `blackout-4s@down,every=120s` with the hold on (the A/B of the missing input).
- **Read:**
  - the recovery log's `desync_pause input_hold` / `resumed input_release` / `input_hold_handover` / `input_hold_cap`
    rows;
  - `tools/unattended_frames.py` over the cell's logs, **per blackout, the `core_running` count**. Expected
    ~ (4 − 0.25) s × 60 ≈ 225 frames without the hold. With it, ~0-5: the frames between 250 ms of silence and the
    pause landing. The raw count will barely move, because the frozen picture keeps streaming.
  - **Cell 8 (`none` with the hold, the false-hold check):** last night's real link had 3 controller gaps of
    276-297 ms in 04:56-05:03, and 5.8 held episodes per 10 min at H 250 over the evening (start-up and a user
    pause included). A bench with the TV idle may show some. Whether a 250-ms gap on an idle LAN is "the hold is
    wrong" or "the link is not clean" is for the reading.
  - the user's or driver's view of the frozen frame.
- **Not tested here:** RetroArch's pause / resume round trip under a 4-s blackout, and the client's view of the frozen
  picture.

## 6. Files

**`b2_2026-10-22/`:**
- `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ `predecessor_note.txt`),
  `predecessor_sha256.txt`, `after_sha256.txt`;
- `design_written_before_code.md`, `design.sha256`, `design_hashed_at.txt`;
- `b2.diff`, `diffstat.txt`;
- `proof_flag_absent.py`, `proof_flag_absent.md`;
- `tests_input_hold.txt`, `tests_regression.txt`;
- `unattended_ux_r1.json`, `unattended_ux_r2.json`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

**Elsewhere:**
- `companion/input_hold.py` (new), `companion/games/link_drop_recovery.py`, `companion/native_session_io.py`,
  `companion/plugins/games.py`;
- `tests/input_hold/test_input_hold.py` (new), `tools/unattended_frames.py` (new);
- `tests/impairment/test_blackout.py` (the stub fix);
- `patches/B2_INPUT_HOLD.md`;
- `logs/b2_git_status.txt`.

No stream, no companion restart, no adb, no sudo, no nft, the Opal untouched, nothing fetched, nothing deleted.
`systemctl --user` showed no `privyhub-*` unit but the companion before each run. Nothing of A's touched.
