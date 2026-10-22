---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 0f4b551 (B2 / B4 / B6 / B7 committed in it; B8 uncommitted beside it)
---

# B8 — the hold / stall ownership at the link's return: the pre-hold frames carried, the resume at the return

**Classification: BUILT** behind `PRIVYHUB_INPUT_HOLD_B8=1` (active only with `PRIVYHUB_INPUT_HOLD`,
`PRIVYHUB_INPUT_HOLD_B6=1` and `PRIVYHUB_STALL_SIGNAL` wired).
- 14 tests with the fake core and fake client (3 runs green). B2 19 / B4 22 / B6 16 / B7 12 unchanged and green.
- Flag absent = BENCH-R2's files: whole-module AST identical with the B8 items removed, 4 / 4 files.
- NOT ADOPTED; no live run; nothing committed.

Design `b8_2026-10-22/design_written_before_code.md`, sha256 `5bbfe71d…f5e1`, hashed **18:52:37Z, before any B8 code**.

## 0. What b1's rows said (read before designing)

BENCH-R2's recovery log, the first b1 blackout:
1. `desync_pause input_hold`, age 955 ms. B4's pending = (the silence's onset, the confirmed pause).
2. `input_hold_handover → client_stall` at the return, **age 4,040 ms**: the client's last displayed frame was ~70 ms
   (~4 frames) *before* the uplink silence's onset. B4's pending survives the handover (same `_state_since`).
3. `resumed` with **no via**, 1.9 s after the return: the client's gate `ready`. **That path has no rewind**, so the
   hold's pending was left with a stale key.
4. A gate-bit `client_stall` (age 6 ms) arrived after that ready, and paused the core again. B7's `set_pending`
   replaced the pending with this second pause's own.
5. `stall_end` rewound only that second pause: requested 1-4.

So the ~57 pre-hold frames were lost at step 3, and the 2-4-s resume was the gate (step 3) plus a second stall pause
(steps 4-5). The design names this; the test `test_b7_alone_reproduces_bench_r2_b1` replays it with B8 absent
(requested ≤ 12, two pauses).

## 1. What was built (`b8.diff`)

`companion/hold_ownership.py` (new, 228 lines). Guarded one-statement hooks: `link_drop_recovery.py` +14,
`stall_signal.py` +11, `hold_rewind.py` +7, `plugins/games.py` +12. One owner stays recovery v2's state machine; B8 is
its memory:
- **The episode:** a hold's pause (`note_hold`, after B6's). Its key is the owner's `_state_since`.
- **The handover carries the rewind** (`note_stall`, at the end of B7's stall branch). The stall's receive time − its
  age = the client's last displayed frame on the host clock. B4's pending onset moves to it when earlier. The rewind
  then requests **`pre_hold_frames` + `stall_frames`** (both in the rewind row and one `input_hold_carry` row).
- **The return** (`note_return`, at the top of `note_input_release`: the first controller packet back, before B7's
  60-ms wait) arms the resume.
- **The resume at the return** (`maybe_resume`, from the monitor after B6's R1): the first heartbeat after the
  return that shows the client's output 0-300 ms old. Then B4's rewind, `resume_game()`, `resumed via
  hold_return_stall` (`packets_back_to_resume_ms`, `output_age_ms`). **No wait for a second stall, the client's gate
  or `stall_end`.**
- **The gate's ready first** (the plugin's ready action, before its own status read and resume, the core still
  paused so B4's method applies): the same rewind and resume, `via client_ready_hold`. *Design change, disclosed:* the
  design put this hook at the top of `note_gameplay_released`. Reading the plugin showed the ready action resumes the
  emulator *before* that call, and B4's REWIND + PAUSE_TOGGLE on a running core would pause it. So the hook moved one
  call earlier, into the ready action. The ready itself is then B6's `client_ready_after_hold` (not a session).
- **After the resume:** a gate-bit stall with an output age below B7's threshold is the client's "Reconnecting"
  overlay over fresh output. It is **ignored** (one `stall_gate_after_return` row; the count goes in the end row).
  - A stall with a stale output (≥ the threshold) is a new drop and acts as B7.
  - **`stall_end` is a logged no-op `stall_end_late`.** It ends the episode. A new hold or 20 s also end it.
- **`stall_end` before the fresh heartbeat:** B7's own resume, with the same carried pending (consumed once).
- **Unchanged:**
  - B6's `client_ready_after_hold` window: set by B8's resume exactly as B6's own resume sets it.
  - B6's cap rule: a handed-over hold is not a released one.
  - `@down` (no hold): B7 exactly.
- **B4's cap with B8** (no `_CAP` given): B6's default + 10 = **72** at H 950. The launch config's buffer is sized for
  it (snes9x 59 MiB, against B6's 53).

## 2. What BENCH-R3 should see per `@both` blackout (snes9x)

1. One hold at ~0.95-1.05 s.
2. At the return, `input_hold_handover → client_stall` and one `input_hold_carry` (pre ≈ 57-60, stall ≈ 4).
3. **`resumed via hold_return_stall` at the first fresh heartbeat after the return.** The client's heartbeat is every
   2 s, so 0.1-2.3 s after the return; b2's 1.1 s is the target.
4. One rewind row (`via hold_return_stall`) with `requested_frames` = pre + stall (≤ 72).
5. Then `stall_gate_after_return`, `stall_end_late`, `client_ready_after_hold`. **No second `desync_pause`**, no
   `session_started`.
6. `tools/unattended_frames.py --net` ≈ 0 per blackout, if snes9x's rewind confirms (PLAYING after).

## 3. Tests (`tests_input_hold_b8.txt`, `tests_regression.txt`)

**`tests/input_hold_b8`: 14 OK, 3 runs.** The real recovery, B2's real dispatcher, B4's real `Rewinder` (a fake NCI),
B6's real tuning, B7's real `StallSignal`, one fake clock:
- the flag (absent; hold + B6 + stall required; ignored rows), the wire, the cap 72 and the buffer;
- **`@both`:**
  - the first after-return heartbeat with a stale output does not resume; the first fresh one does;
  - **one resume, one rewind: requested 63 = pre-hold 59 (1,050 ms − B4's 4) + stall 4 (70 ms)**;
  - gate stalls are ignored;
  - `stall_end_late`; `client_ready_after_hold`; no session; B6's released count 0;
- the gate's ready first (with the rewind); `stall_end` before the heartbeat (B7's resume, requested 63);
- a stale-output stall after the return pauses again; no stall at the return (B2's release, then gate stalls
  ignored); the episode expires;
- **`@down`:** the event list with B8 on equals B8 off;
- **the rate limit:** six released holds disarm (B6); eight handed-over holds resumed by B8 do not;
- FlagAbsent: a fresh process imports nothing, the class attribute is None; the hook shapes;
- *B7 alone* reproduces BENCH-R2's b1 (two pauses, the second's own frames only).

**Regression:** every suite under `tests/` green from the copy.
- `input_hold_rewind`'s 2 skips are its predecessor-file tests (env not given), as before.
- The four `tools/` tests that read `docs/memory` fixtures fail identically on an untouched HEAD copy
  (`tests_tools_at_head_copy.txt`). They are the copy's environment.

**Proof** `proof_flag_absent_host.md`: **ALL IDENTICAL**:
- link_drop_recovery 4 items removed, stall_signal 3, hold_rewind 2, plugins/games 4;
- `hold_ownership` is never imported with the flag absent.

## 4. Files

- **`b8_2026-10-22/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/`, `predecessor_sha256.txt`,
    `predecessor_note.txt`, `after_sha256.txt`;
  - `design_written_before_code.md`, `design.sha256`, `design_hashed_at.txt`;
  - `b8.diff`, `proof_flag_absent_host.py` / `.md`;
  - `tests_input_hold_b8.txt`, `tests_regression.txt`, `tests_tools_at_head_copy.txt`;
  - `redact_check.py`, `redact_check.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `companion/hold_ownership.py` (new), `games/link_drop_recovery.py`, `stall_signal.py`, `hold_rewind.py`,
    `plugins/games.py`, `tests/input_hold_b8/` (new);
  - `docs/memory/patches/B8_HOLD_STALL_OWNERSHIP.md`, `logs/b8_git_status.txt`.
- **The rules held:**
  - no stream, no restart, no adb, no sudo, no nft;
  - the Opal untouched;
  - nothing fetched, nothing deleted, nothing of A's touched, nothing committed.
