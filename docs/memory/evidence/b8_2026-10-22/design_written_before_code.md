# B8 — the hold / stall ownership at the link's return: design, written before any B8 code

Baseline HEAD 0f4b551 (B2 / B4 / B6 / B7 committed in it). Queue: `handoffs/QUEUE_2026-10-22D.md` §B8. Data:
`BENCH_R2_LOCK_HOLD_STALL_CELLS_2026-10-23.md` §3 b1 / b2, §9, and its `logs_bench/native_stream_recovery.log`.

## 0. What the b1 rows say happened (read from the log before designing)

First blackout (15:24:52Z), in order:
1. `desync_pause input_hold`, age 954.7 ms — the hold paused; B4's pending = (hold onset, the confirmed pause).
2. `input_hold_handover → client_stall`, **age 4,040 ms**, held 3,099 ms — at the link's return the first stall
   datagram arrived with the client's output age ≈ the blackout: the client's last displayed frame was
   (receive − 4.04 s), ~70 ms *before* the hold's onset (the uplink silence). B4's pending stays (same `_state_since`).
3. `resumed` with **no via** (15:24:58.451, 1.9 s after the return) — `note_stream_ready`, the client's gate `ready`.
   That path has no rewind. The hold's pending is left behind with a stale key (dropped at the next rewind).
4. `client_stall in_gate age 6` → `desync_pause client_stall` — the client still sent gate-bit stalls after its own
   ready: a new pause on a fresh `_state_since`; B7's `set_pending` replaced the hold's pending with this pause's own.
5. `rewind_failed req 2` / `input_release … via stall_end` — only this second pause's 1-4 frames were requested.

So the ~57 pre-hold frames were lost at step 3 (a resume path without the rewind), and the 2-4-s resume is the client's
gate (step 3) plus a second stall pause (steps 4-5). b2 (no stall pair) resumed at B2's own `input_release`, 1.1 s
after the return, with the pre-hold frames requested (58-59; failed on PSX HW for B4's reason, not this one).

## 1. The flag

`PRIVYHUB_INPUT_HOLD_B8=1`, new module `companion/hold_ownership.py`. Active only when the hold is valid
(`PRIVYHUB_INPUT_HOLD`), B6 is on (`PRIVYHUB_INPUT_HOLD_B6=1`, wired) and the stall signal is valid
(`PRIVYHUB_STALL_SIGNAL`, wired): the case b1 measured. Otherwise one `input_hold_b8_config ignored` row and nothing
else. **Absent = BENCH-R2's code byte for byte:** the plugin imports the module only with the flag set; every hook in
an existing file is one statement guarded by `… _input_hold_b8 is not None` (or `"b8" in pending` inside B4's rewind,
which only B8 ever writes), proven by the whole-module AST with those statements removed against the predecessors.
B2 / B4 / B6 / B7 suites run unchanged.

## 2. One owner; what the owner remembers

The owner stays recovery v2's `LinkDropRecovery` (state, `_last_desync_reason`, `_state_since`). B8 is memory and
three decisions, called from the owner's own methods and B7's worker:

- **The episode:** `note_hold` (after B6's, in `note_input_hold`): when the pause stands as the hold's, B8 records the
  key (`_state_since`) and `pre_hold_frames` = B4's `counter_before` of the hold's pending (None without B4).
- **The handover carries it** (`note_stall`, at the end of B7's stall branch): when the pause is this episode's and its
  reason is now `client_stall`, the client's last displayed frame on the host clock (receive − age, the LAN's one-way
  delay 0, as B7) is compared with the hold's onset. B4's pending onset becomes the earlier of the two; the rewind
  then requests `pre_hold_frames` + `stall_frames` (the frames between the client's last displayed frame and the
  silence's onset, ≥ 0), within the cap. One `input_hold_carry` row (pre_hold_frames, stall_frames, client_frame,
  age_ms). The pending's key is unchanged (the handover keeps `_state_since`), so whichever resume path runs first
  consumes it once.
- **The return:** `note_return` at the top of `note_input_release` (the first controller packet back, before B7's
  60-ms wait): `return_at` = now for this episode's pause (reason `input_hold` or `client_stall`).

## 3. The resume at the return (b2's 1.1 s as the target for b1)

- **R-B8** (`maybe_resume`, from the monitor after B6's): the pause is this episode's, its reason `client_stall`
  (handed over), `return_at` is set, and the newest heartbeat was received after `return_at` with the client's output
  age 0-300 ms (B6's R1 test, `OUTPUT_FRESH_MS`) → B4's rewind (`via hold_return_stall`), `resume_game()`, PLAYING,
  `resumed via hold_return_stall` (`packets_back_to_resume_ms`, `output_age_ms`). It does **not** wait for a second
  stall, the client's gate, or `stall_end`. So the resume lands at the first fresh report after the return
  (heartbeat 1-2 s + the 250-ms monitor tick).
- **If the reason is still `input_hold`** at the return (no stall within B7's 60 ms), B2's own release resumes as
  today (b2's path); B8 only marks the episode returned.
- **The client's ready while the episode's stall pause stands** (the gate first, b1's step 3): B8 resumes it itself
  with the rewind (`via client_ready_hold`), at the top of `note_gameplay_released`, so no resume path of a hold
  episode drops the pre-hold frames. `{"recovered": True, "from_state": "hold_stall"}` — not a session.
- **`stall_end` before the fresh heartbeat:** B7's own resume (`via stall_end`) with the same carried pending. Fine:
  whichever is first resumes, the pending is consumed once.

## 4. After the return: no second pause from the client's gate

- After a hold episode's resume (any path above, or B2's release), until the episode ends, a stall with the gate bit
  and an output age below B7's threshold is the client's own "Reconnecting" overlay over fresh output, not a drop:
  **ignored** (one `stall_gate_after_return` row per episode with the count at its end). A stall with age ≥ the
  threshold still acts as B7 (a new drop: its own pause, its own rewind).
- **`stall_end` after the resume:** a logged no-op `stall_end_late` (client_frame); it ends the episode.
- The episode also ends at a new hold, or 20 s after the resume (the client's gate times out at 15 s).

## 5. Unchanged

- **The client's ready after the resume** (`client_ready_after_hold`): B6's window, set by B8's resume exactly as B6's
  own `maybe_resume` sets it (`_ready_window_until = now + 20 s`); B6 logs it as written.
- **The rate limit:** B6's cap counts holds released by input (reason `input_hold` at the release); a handed-over hold
  resumed by B8 is not counted, as today. B2's 50-ms minimum unchanged.
- **@down (stall only, c1):** no hold episode, B8 does nothing; B7's pause / rewind / resume as BENCH-R2 measured.
- **B4's cap with B8** (no `_CAP` given): B6's default + 10 (the client's frames before the silence's onset: b1's 70 ms
  ≈ 4 frames, + margin) = 72 at H 950, ≤ 120; the buffer sized for it (snes9x 823,536 B × 74 → 59 MiB).

## 6. Tests (fake core, fake client, real LinkDropRecovery, real B2 dispatcher, real B4 Rewinder with a fake NCI)

1. Flag: absent → nothing; requires hold + B6 + stall (ignored rows otherwise); the plugin import guard.
2. **@both:** hold → handover (stall age 4,040) → the first controller packet back → a fresh heartbeat → **one resume**
   (`via hold_return_stall`) at the first fresh heartbeat after the return, before any `stall_end` or ready; **one
   rewind, requested = pre-hold + stall frames** (counted from the fake clocks); no second pause from the gate-bit
   stalls that follow; the later `stall_end` → `stall_end_late`, no resume; the client's ready → `client_ready_after_hold`.
3. The gate's ready first → the B8 resume with the rewind, no session.
4. **@down:** stall only → B7's rows exactly (pause client_stall, its own rewind, `resumed via stall_end`), no B8 row.
5. **The late `stall_end`:** after the B8 resume → `stall_end_late`, the core's resume count unchanged.
6. A stall with age ≥ threshold after the return → B7's new pause (not ignored).
7. **The rate limit unchanged:** six released holds disarm as B6; handed-over holds resumed by B8 do not count.
8. B4's cap with B8 (72) and the config buffer.
9. B2 / B4 / B6 / B7 suites unchanged and green; the flag-absent proof (whole-module AST).
