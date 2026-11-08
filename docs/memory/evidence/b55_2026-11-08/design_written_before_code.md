# B55 — PS2 recovery through PINE save states: the slot-9 save, the hold's return, the stall resume, the give-up save (design, hashed before code)

Queue: `handoffs/QUEUE_2026-11-08T.md` §B55; the user's "Yes" (PS2 hold / stall through saved states). Baseline
`0eb115d9`; built in `/tmp/b_q12t_b55` on the baseline (independent of B54's copy: B54's PS2 relaunch keeps its
recorded `restarted` path — §3). **Inside `PRIVYHUB_PS2=1`: every change is on a branch reached only when the session's
launch kind is `pcsx2`, which only the flag allows. Absent = today byte for byte.**

## 0. Settled (the code and the HOME-5 / HOME-6 records read in place; PCSX2 not started)

**The four behaviours B49 turned off, and the one path they share.** On this hub the link-recovery umbrella
(`PRIVYHUB_LINK_RECOVERY=1`) implies `PRIVYHUB_INPUT_HOLD_REWIND=1` = B12's `state` mode, so:
- **the slot-9 save** (`rewind_cores.Cores.save`): a scratch save at a controller silence of 400 ms (B9, `kind
  silence`) and at the client's stall signal (B12, `kind stall`);
- **the hold's return** (B32's screen loss: the client's stall signal pauses the game on the host, "as at a link
  stall"; the return → `stall_end` or B16's fast ready) and **the stall resume** (a link stall's return): both end in
  `hold_rewind.Rewinder.rewind` → `Cores.release`, which loads slot 9 before the recovery's own resume. B2's input
  hold release takes the same call;
- **the link give-up save** (`save_recovery_state` at `GIVE_UP_MS` 120 s, the game paused): the recovery prompt's file.

**PINE's measured times (HOME-5 / HOME-6):** the save's file complete **0.5 s** after the request (both times); the
load **0.9 s** to a confirmed picture (both times), of which the load itself — PINE 0x0A to PCSX2's `Loaded state from
slot N.` — took **≤ 0.31 s** (HOME-6 C12'': `ELF Loading:` at t 4.68 and `Loaded state from slot 1.` at t 4.99 in the
per-launch log, a span that also holds B52's pause and the PINE round trip); the rest is B52's check, the game running.

**The budgets and the judgement:**

| behaviour | its budget | PINE | verdict |
| --- | --- | --- | --- |
| **the slot-9 save** | B9: the acknowledgement ≤ `SAVE_ACK_S` 100 ms; B12: the state's instant ~150 ms (8-14 frames) after the onset | PINE answers in milliseconds; PCSX2 takes the snapshot on its CPU thread at the next event check (≤ 1 frame while running, at once while paused) and writes the 0.5-s zip in its own thread afterwards | **FITS** — the file's completion is checked at the load, not at the save |
| **the hold's return / the stall resume** (one path) | B16's R1 / R2 (hashed): resumed **≤ 1.0 s after the return**; the fast ready takes ≤ 0.55 s of it → **the load's share ≤ 0.45 s** | the load ≤ 0.31 s; B52's picture confirmation (~0.6 s more) needs the game running anyway | **FITS with the confirmation after the resume:** the load and its log line block (bounded 0.45 s); the recovery's resume follows at once; the picture is checked while the game plays. Run as B52 does it (load, check, then resume) it is 0.55 + 0.9 = 1.45 s and would **not** fit — disclosed |
| **the link give-up save** | none tight: the game is paused and the player gone; the next event is `END_MS` (30 min) | 0.5 s | **FITS** |
| **the rewind** (RetroArch's `REWIND`) | — | PCSX2 has none | **stays off** |

**Reserved PCSX2 slots** (inside PCSX2's own 1-10; PrivyHub's user slots are 1-3): **slot 9** = the scratch (as
RetroArch's slot 9: one save at a time, `silence` or `stall`), **slot 8** = the give-up save. The files are PCSX2's
own, `data/games/ps2/sstates/<serial> (<crc>).0N.p2s`; with `BackupSavestate` kept (B52), PCSX2 also keeps one
`.p2s.backup` per slot (disclosed). The B33 rule stands: a return under 1 s with no loss resumes without a load (by
then the slot-9 file — 0.4 s + 0.5 s — is complete in every case that loads).

## 1. The code (each branch on `_launch_kind == "pcsx2"`)

- **`Cores.save`, PS2:** instead of `saves_skipped_ps2` (B49): the folder's state files read (`state_files`), then
  PINE 0x09 slot 9 under the emulator's lock; `last_save` as RetroArch's (`ok` = PINE OK) plus `p2s_before`; the row
  `state_saved` (or `state_save_failed`) with `slot` 9, `kind`, `ps2_states: "pine"`; the game log `PS2 state save:
  slot 9 pine 0x09 ok (<kind>)`.
- **`Rewinder.rewind`, PS2:** B49's `rewind_skipped` / `ps2_mode` row is now written only when B9's object is not in
  `state` mode (the rewind method: none in PCSX2, `reason: "ps2: no rewind in PCSX2"`). In `state` mode the PS2 release
  goes to `Cores.release` like every core.
- **`Cores.release`, PS2 branch** (after B33's decision and the onset match, unchanged):
  1. the slot-9 file new since `p2s_before` and complete (`wait_state_file`, bounded by the share: 0.45 s); not →
     `rewind_skipped`, `reason: "the PS2 state file is not complete"` (the resume proceeds, no load);
  2. PCSX2 paused (the pause the stall / hold owns; `ensure_pine_pause`); PINE 0x0A slot 9; the log line waited
     ≤ 0.45 s; PINE not OK → `rewind_failed`, `reason: "PINE load not acknowledged"`;
  3. the row `input_release` with `method: "state"`, `slot` 9, `ps2_states: "pine"`, `load_ms`, `line: true|false`,
     `verification: "picture_after_resume"`; the game log `PS2 state load: slot 9 pine 0x0a ok; <ms> ms`;
  4. **the verifier** (a daemon thread): waits ≤ 2 s for PINE to read running (the recovery's resume), then B52's
     `check_picture` (≤ 5 s, the pre-load picture as `pre`); writes `ps2_states` `{"check": "picture", "verdict":
     ok|static|fault, "s": …}` and the game log line; **static / fault → the PS1-shaped error of this path: a
     `rewind_failed` row** (`reason: "the game did not resume from the save (picture <verdict>)"`), as a RetroArch load
     that fails at the release is a `rewind_failed` row and the resume stands (B4). The game is left as it is.
- **`save_recovery_state`, PS2** (instead of B49's `skipped`): PINE 0x09 slot 8 (PCSX2 paused, as the give-up finds
  it), the file waited (`SAVE_BOUND_S`), the recovery index written as PS1's (`state_file` = the slot-8 file,
  `saved_at`, `game_id`, `game_title`, `game_key`); the game log `PS2 recovery save: slot 8 pine 0x09 ok; file complete
  <s>s`. `gave_up_saved` then carries `ps2_states: "pine"` (B49's `ps2_mode` / `save_skipped` keys appear only if the
  skip ever returns — it no longer does).
- **The prompt's paths for a PS2 recovery save:**
  - **Resume** (`load_recovery_state_running`, the fresh launch running): B52's ELF hold, PINE 0x0A slot 8 (PCSX2
    paused for it), the log line, resume, `check_picture` (blocking here: the launch has no tight budget); ok → the PS1
    payload; static / fault → `EmulatorError("The game did not resume from the save")` → the flow's "Recovery resume
    failed; the recovery save is kept";
  - **Copy to a slot** (`copy_recovery_state_to_slot`): the slot-8 file copied to the user slot's PCSX2 name
    (`.0N.p2s` beside it), sha256-verified, the slot index written (`_record_state_slot_index`), PS1's
    occupied-slot rule;
  - **Discard:** unchanged (it removes the indexed file — the slot-8 file — and clears the index).
  - `load_recovery_state` (the paused variant, unused by the R3c2 flow) stays refused for PS2.
- **The start's `ps2_session` row:** `ps2_states: "pine"`, `pine: [state_save_slot9, hold_return_load,
  stall_resume_load, recovery_save]`, `off: [rewind]` (B51's `savestates: "pine"` kept).
  `ps2_session.OFF_BEHAVIOURS` → `("rewind",)`; `PINE_BEHAVIOURS` new; constants `SCRATCH_SLOT` 9, `RECOVERY_SLOT` 8,
  `RELEASE_SHARE_S` 0.45.

## 2. Tests (`tests/ps2_session/test_b55.py`, B51's PINE socket double, B52's fake window; < 10 s)

- **the hold's save:** `Cores.save` on a PS2 session sends `[6][0x09][9]`, `state_saved` with `ps2_states: "pine"`;
- **the hold's load:** `Cores.release` sends `[6][0x0A][9]`, the `input_release` row with `ps2_states: "pine"`; the
  verifier writes `picture ok` after the resume;
- **the stall resume's load:** a `kind: "stall"` save and a stall pending → the same load (via `client_ready_stall`);
- **a failed picture** (static, and a `TLB Miss`) → the `rewind_failed` row with the PS1-shaped reason;
- **the file not complete** → `rewind_skipped`, no load sent;
- **the give-up save:** slot 8, the recovery index; the prompt's Resume (picture ok → payload; static → the error),
  Copy (the `.0N.p2s`, the index), Discard;
- **the start row:** `ps2_states: "pine"`, `off: ["rewind"]`;
- **absent → today:** a RetroArch session never takes a PS2 branch (B49 / B50 / B51's absent tests stay green); B49's
  skip-row tests move to the new meaning (disclosed).

## 3. Not in this item

- **B54's PS2 relaunch** stays `restarted` (B54 is built on the baseline, B55 likewise); routing it through slot 8 /
  9 is a two-line follow-up once both are on the tree — listed for the next queue.
