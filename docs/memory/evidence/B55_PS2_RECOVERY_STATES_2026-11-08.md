---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 0eb115d9 (B55 built in /tmp/b_q12t_b55 on the baseline; applied to the tree with queue T's combined diff, uncommitted)
---

# B55 — PS2 recovery through PINE save states: the slot-9 save, the hold's return, the stall resume, the give-up save

**Classification: SETTLED + BUILT** inside `PRIVYHUB_PS2=1` (each change is on a branch reached only in a PCSX2
session). The user's "Yes" (PS2 hold / stall through saved states).
- **Tests:** `tests/ps2_session` **93** green ×3 (79 + B55's 14). Three B49 skip tests moved to B55's meaning
  (disclosed). Every host suite as the baseline copy.
- **Mutations:** 8 caught, none survived (`b55_2026-11-08/tests_mutations.txt`; the three import errors listed in
  every line belong to the mutation copy, which has no `tools/`, and are not mutation results).
- **Proof:** absent = today, PROVEN (`b55_2026-11-08/proof_flag_absent.md`).
- NOT ADOPTED (live with the adopted `PRIVYHUB_PS2=1` at the next companion restart); no live run; PCSX2 not started;
  nothing committed.

Design `b55_2026-11-08/design_written_before_code.md`, sha256 `d5f6fb6a…875d4e`, hashed **18:28:52Z, before any B55
code**.

## 0. Settled: the four behaviours against PINE's measured times

**One path for the hold's return and the stall resume.**
- The link-recovery umbrella implies `PRIVYHUB_INPUT_HOLD_REWIND=1` (B12's `state` mode). So:
  - B32's screen loss pauses the game through the client's stall signal, "as at a link stall";
  - a link stall goes the same way;
  - both resume through `Rewinder.rewind` → `Cores.release`, which loads the slot-9 save before the recovery's own
    resume;
  - B2's input-hold release takes the same call.
- The slot-9 save is taken at a 400-ms controller silence (`kind silence`) or at the client's stall signal
  (`kind stall`).

**PINE's times (HOME-5 / HOME-6):**
- **save:** the file is complete **0.5 s** after the request;
- **load:** **0.9 s** to a confirmed picture. The load itself (PINE 0x0A to PCSX2's `Loaded state from slot N.`) took
  **≤ 0.31 s** at HOME-6 C12''; the rest is B52's check, which runs with the game going.

| behaviour | its budget | verdict |
| --- | --- | --- |
| **the slot-9 save** | B9: the ack ≤ 100 ms; B12: the state ~150 ms after the onset | **LIVE.** PINE answers in milliseconds, and PCSX2 takes the snapshot at its CPU thread's next event (≤ 1 frame). The 0.5-s file write follows in its own thread, and its completion is checked at the load. |
| **the hold's return / the stall resume** | B16's R1 / R2 (hashed): resumed **≤ 1.0 s after the return**; the fast ready uses ≤ 0.55 s of it, so **the load's share is ≤ 0.45 s** | **LIVE, with the picture confirmed after the resume.** The load and its log line block (bounded 0.45 s; ≤ 0.31 s measured); the recovery resumes at once; B52's picture check then runs while the game plays. **Run as B52 does it (load, check, then resume) it would be 0.55 + 0.9 = 1.45 s and would not fit** (disclosed). |
| **the link give-up save** | none tight (the game is paused and the player gone) | **LIVE** (slot 8), with the recovery prompt's Resume / Copy / Discard for PS2. |
| **the rewind** | — | **stays off** (PCSX2 has none). |

- **Reserved PCSX2 slots** (inside PCSX2's own 1-10; PrivyHub's user slots are 1-3): **9** = the scratch, **8** = the
  give-up save.
- The files are PCSX2's own, `data/games/ps2/sstates/<serial> (<crc>).0N.p2s`. PCSX2 also keeps one `.p2s.backup` per
  slot (`BackupSavestate`, kept by B52).
- B33 stands: a return under 1 s with no loss resumes without a load. By then (0.4 s + 0.5 s) the slot-9 file is
  complete in every case that loads.

## 1. Built (`b55_2026-11-08/b55.diff`, 8 files)

- **`rewind_cores.Cores.save`, PS2:** PINE 0x09 slot 9 under the emulator's lock (B49's `saves_skipped_ps2` gone).
  - The row is `state_saved` / `state_save_failed` with `slot` 9, `core` `pcsx2`, `kind`, `ps2_states: "pine"`.
  - The game log: `PS2 state save: slot 9 pine 0x09 ok (<kind>)`.
- **`rewind_cores.Cores.release`, PS2 branch** (after B33 and the onset match, unchanged):
  1. the slot-9 file new and complete (≤ 0.45 s), else `rewind_skipped` "the PS2 state file is not complete";
  2. PCSX2 paused; PINE 0x0A slot 9; the log line (≤ 0.45 s). A PINE failure is a `rewind_failed` row;
  3. the `input_release` row with `ps2_states: "pine"`, `load_ms`, `line`, `verification: "picture_after_resume"`;
     the game log `PS2 state load: slot 9 pine 0x0a ok; <ms> ms`;
  4. **a verifier thread** waits ≤ 2 s for PCSX2 running (the recovery's resume), then runs B52's `check_picture`.
     - It writes `ps2_states` `{check: picture, verdict, s}` and `PS2 state load: slot 9 picture <verdict> <s>s`.
     - **static / fault → the PS1-shaped error of this path: a `rewind_failed` row** "the game did not resume from
       the save (picture …)". As with a RetroArch load that fails at the release, the resume stands.
- **`hold_rewind.Rewinder.rewind`:** B49's PS2 `rewind_skipped` row ("ps2: no rewind in PCSX2") only when B9 is not in
  `state` mode; in `state` mode the PS2 release goes to `Cores.release`.
- **`emulator_manager.py`:**
  - `save_recovery_state` → `_pcsx2_save_recovery_state`: slot 8, the file waited, PS1's recovery index;
  - `load_recovery_state_running` → B52's ELF hold, PINE 0x0A slot 8, the picture (blocking), left running;
    static → "The game did not resume from the save";
  - `copy_recovery_state_to_slot` → the slot-8 file copied to the user slot's `.0N.p2s`, verified, the slot index;
  - Discard is unchanged (index-based); the paused `load_recovery_state` stays refused.
- **`link_drop_recovery`:** `gave_up_saved` carries `ps2_states: "pine"`.
- **`plugins/games.py`:** the start's `ps2_session` row has `ps2_states: "pine"`, `pine: [state_save_slot9,
  hold_return_load, stall_resume_load, recovery_save]`, `off: [rewind]`.
- **`ps2_session.py`:** `PINE_BEHAVIOURS`, `OFF_BEHAVIOURS = ("rewind",)`, `SCRATCH_SLOT` 9, `RECOVERY_SLOT` 8,
  `RELEASE_SHARE_S` 0.45, `VERIFY_RUNNING_S` 2.0.

## 2. Tests (`tests/ps2_session/test_b55.py`, 14; B51's PINE socket double, B52's fake window)

- **The hold's save:** `[6][0x09][9]` with PCSX2 running, the row, the file, the log line; a PINE failure → the failed
  row.
- **The hold's load:**
  - `[6][0x0A][9]`; the `input_release` row with `ps2_states: "pine"`, `load_ms` ≤ 450;
  - the game left paused for the recovery's resume;
  - after the resume, the verifier → `picture ok`, no `rewind_failed`.
- **The stall resume:** a `kind: stall` save matched within 100 ms → the same load (`client_ready_stall`).
- **A failed picture:** static → `rewind_failed` "…(picture static)"; a `TLB Miss` → "…(picture fault)".
- **An incomplete file** → `rewind_skipped`, no load sent.
- **Through the Rewinder** (B9 in `state` mode) → the PINE load, no skip row.
- **The give-up save:** slot 8, the index; the `gave_up_saved` row.
- **The prompt:** Resume (slot 8, picture ok, left running), Resume with a static picture → PS1's error, Copy to slot 2
  (the bytes, the slot detail), Discard (the slot-8 file gone, the copy kept).
- **A RetroArch session:** the NCI's `SAVE_STATE_SLOT 9`, no `ps2_states`.
- B49's three skip tests moved to B55's meaning (disclosed): the rewind-method row's reason; the slot-9 save never
  through the NCI; the recovery paths routed to PINE with the paused load still refused. The start row test checks
  `ps2_states` / `pine` / `off: ["rewind"]`.

## 3. For A (HOME-7 C18)

- **The hold's return:** Home on the onn, count to 2, back.
- **Expected in the recovery log:**
  - `state_saved` `slot 9 … ps2_states pine kind stall`;
  - at the return, `input_release` `ps2_states pine … load_ms <450`, then `ps2_states` `verdict ok`;
  - `resumed via client_ready_stall` (or `stall_end`).
- **Expected in the game log:** `PS2 state save: slot 9 pine 0x09 ok (stall)`, `PS2 state load: slot 9 pine 0x0a ok;
  <ms> ms`, `PS2 state load: slot 9 picture ok <s>s`.
- **On the TV:** the game where it was.
- **The time:** the `resumed` row's time minus the client's return (the rows' times), against R1's 1.0 s.
- **The stall resume** is the same path (a link stall is not provoked at HOME-7; it is read if one happens).

## 4. Files

`b55_2026-11-08/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
- the design + `design.sha256` + `design_hashed_at.txt`;
- `b55.diff` (`git apply --check` OK);
- `proof_flag_absent.md`;
- `tests_ps2_session_x3.txt`, `tests_host_b55.txt`, `tests_host_baseline.txt`, `tests_mutations.txt`;
- `redact_check.txt`, `manifest.sha256`.

Patch note: `patches/B55_PS2_RECOVERY_STATES.md`.
