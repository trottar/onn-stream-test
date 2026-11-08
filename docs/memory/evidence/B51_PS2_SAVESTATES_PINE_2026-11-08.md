---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: c497a196 (the tree clean; B51 built in /tmp/b_q10r_b51 and applied to the tree, uncommitted)
---

# B51 — PS2 saving like PS1: PrivyHub's SAVE / LOAD through PINE (inside `PRIVYHUB_PS2=1`)

**Classification: SETTLED + BUILT.**
- **Tests:** `tests/ps2_session` 65 green ×3 (1.9 s); every host suite as the baseline copy.
- **Mutations:** 6 caught.
- **Proof:** absent = today, hunk by hunk (`b51_2026-11-08/proof_flag_absent.md`).
- NOT ADOPTED; PCSX2 **not started** (its binary disassembled from the AppImage in `/tmp`); no BIOS read; nothing
  written to the drive; nothing committed.

Design `b51_2026-11-08/design_written_before_code.md`, sha256 `0f2026b8…0032`, hashed **08:44:47Z, before any B51
code**. Precondition: only the companion and `privyhub-diag` active; the tree clean (HEAD `c497a196`).
- **Seen at the start and not touched:** `b49-ps2.conf` is in the companion's drop-ins (16 `PRIVYHUB_` lines), the bench
  flag on at the user's decision after HOME-4+ (`dropins_at_start.txt`).
- The running companion has B50's code. B51 goes live at the next restart (A's HOME-5 stage 1).

## 1. Settled

1. **PINE on PCSX2 2.8.2**, read from its binary (`pine_binary_reading.md`, `pine_opcodes.txt`):
   - **save state = opcode 0x09, load state = 0x0A** (status 0x0F); the request is `[u32 6][u8 op][u8 slot]`;
   - the reply is `[u32 5][u8 0x00]` OK or `0xFF` failure;
   - accepted only with the VM running / paused;
   - **the OK means queued** (`QueuedConnection` to the emulator thread), and the save zips on a further thread, so
     the file completes after the reply;
   - **the file** is `{serial} ({crc:08X}).{slot:02d}.p2s` in `data/games/ps2/sstates/`, the old one kept as
     `.p2s.backup`;
   - PCSX2 logs `Saved state to slot N.` / `Loaded state from slot N.`
2. **The PS1 path:**
   - the onn's Game State → `POST save-state` / `load-state?slot=N` (1-3) → RetroArch slot 0 + copy / stage + load;
   - **the PS1 slot index** feeds the Game State list, "Saved States" and the tiles;
   - success → `Saved Slot N - <date> - <size>`; failure → the "Game State" dialog;
   - **a load requires the game paused.**
   - **Every failure on this API is HTTP 503 `{"ok": false, "error": …}`, PS1 included.** So the user's "the PS1 error
     shape" and "never 503" cannot both hold. B kept the PS1 shape and real failure texts; the "not available" refusal
     is never given for the buttons. Disclosed for the user.
3. **What goes through PINE:**
   - **the SAVE / LOAD buttons: yes;**
   - **the hold's rewind / state load, the slot-9 save and the stall resume's load: kept off.** PINE's save completes
     asynchronously at a time B cannot measure without running PCSX2, so fitting their budgets is unshown; disclosed.
     C13 does not run;
   - **the rewind:** none in PCSX2, off;
   - **the link give-up save:** off (not asked).

## 2. Built (`b51.diff`, 5 files)

- **`ps2_session.py`:**
  - `MSG_SAVE_STATE` / `MSG_LOAD_STATE` / `MSG_STATUS`, `PINE_OK` / `PINE_FAIL`, `SAVE_BOUND_S = 10`,
    `LOAD_CONFIRM_S = 3`;
  - `pine_call`, `state_files` (mtime ns, size, inode: PCSX2 writes a new file and keeps a backup), `pcsx2_log_path`;
  - `Session.pine_path`, `ensure_pine_pause` (a SIGSTOP-paused PCSX2 cannot answer: SIGCONT, then its hotkey pause
    confirmed by PINE; else re-frozen and refused), `state_message`, `wait_state_file` (steady size, whole zip),
    `wait_log_line`.
- **`EmulatorManager.save_state` / `load_state`:** a `pcsx2` session → `_pcsx2_save_state` / `_pcsx2_load_state`
  (B49's refusal removed for these two only).
  - **The save:** the slot normalized, the hand-over, a snapshot, PINE 0x09 + slot. Not OK → "PCSX2 did not
    acknowledge the save state". Then the slot's file complete ≤ 10 s, else "PrivyHub could not verify the saved PS2
    state". **`_record_state_slot_index`** (the PS1 index), then the PS1 payload: `action` `save_state`, `slot`,
    `accepted` / `confirmed` true, `replaced_existing`, `control` `pcsx2_pine_save_state`, `slot_detail`,
    `state_file`. Game log: `PS2 save: slot N pine 0x09 ok; file complete <s>s`.
  - **The load:** PS1's preconditions and messages ("Load State requires the game to be paused", "No save state exists
    in Slot N", the 0-byte case), the hand-over, PINE 0x0A + slot ("PCSX2 did not acknowledge the load state"). Then
    PCSX2's log line ≤ 3 s → `confirmed` / `verification` `pcsx2_log`, else `visual_required` (PS1's two values),
    `paused` true. Game log: `PS2 load: slot N pine 0x0a ok; confirmed|visual`.
  - **The bound:** 10 s, named from an expected ~1-s write of a ~45-MB zstd state on the hub's disk (≥ 10×). **No write
    time was measured** (B cannot start PCSX2). HOME-5 logs the real one, and a later revision sets the bound to 5× it.
- **`plugins/games.py`:** the `ps2_session` row has `savestates: "pine"` (the old `save_states: "off"` removed,
  disclosed); `off` keeps the four automatic behaviours.
- **Tests:**
  - `tests/ps2_session/test_b51.py` (new, 11) uses a real Unix-socket PINE double: it records every request and writes
    the `.p2s` with PCSX2's backup rename, or PCSX2's log line;
  - `test_ps2_session.py` moved three B49 / B50 expectations to B51's meaning (disclosed).

## 3. Tests

- **The codes:** 0x09 / 0x0A / 0x0F, OK 0x00 / fail 0xFF, against the binary's table.
- **SAVE:** the exact request `[6][0x09][2]` → the PS1 payload, the PS1 index's slot detail (`exists`, size, time),
  the Game State list `{1: empty, 2: saved, 3: empty}`, `replaced_existing` on a second save, the game log line.
- **The failures** (PINE `0xFF`, no answer, no file) → the PS1-shaped `EmulatorError` with real texts, never "not
  available".
- **A SIGSTOP-paused session** → SIGCONT → the hotkey pause → the save. With no PINE after SIGCONT → re-frozen,
  refused, no message sent.
- **LOAD:** `[6][0x0A][3]` → `confirmed` / `pcsx2_log`, `paused`; with no log line `visual_required`; PS1's messages
  for an empty slot, not paused, and a PINE failure; a relaunched session still lists and loads the slot.
- **PS1 untouched:** a RetroArch session never takes the branch. **Absent:** B49 / B50's absent tests.
- **Regression:** every `tests/` suite as the baseline copy; from the tree after the apply, the touched suites OK.

## 4. Docs-only fixes (insertions)

- **C10's off check** (an errata section in the B47 record): with `vod_retry` `0` the full-screen player shows only
  the paused picture; "Playback error - marked recently failed" is behind it, ~32 s after the drop.
- **C9's row** (an errata section in the B46 record): the release rule is per pad, slot 0 or 1.
- Both are also in `KNOWN_ISSUES.md`.

## 5. Files

`b51_2026-11-08/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`, `dropins_at_start.txt`,
  `units_before_apply.txt`, `applied_to_tree_at.txt`;
- the design + `.sha256` + `design_hashed_at.txt`;
- `pine_binary_reading.md`, `pine_opcodes.txt`;
- `predecessors/` + `predecessor_sha256.txt`, `after_sha256.txt`;
- `b51.diff`;
- `proof_flag_absent.md`;
- `tests_ps2_session_x3.txt`, `tests_mutations.txt`, `tests_host_b51.txt`, `tests_host_baseline.txt`,
  `tests_tree_after_apply.txt`;
- `redact_check.txt`, `manifest.sha256`.

Patch note: `patches/B51_PS2_SAVESTATES_PINE.md`.
