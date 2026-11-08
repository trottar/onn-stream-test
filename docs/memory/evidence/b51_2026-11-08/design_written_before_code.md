# B51 — PS2 saving like PS1: PrivyHub's SAVE / LOAD through PINE (design, written and hashed before any B51 code)

Queue: `handoffs/QUEUE_2026-11-08R.md` §B51. HOME-4+ C12: the user saves only with PrivyHub's SAVE button, and for
PS2 it answered B49's refusal. Baseline `c497a196`; built in `/tmp/b_q10r_b51`. **Everything is inside
`PRIVYHUB_PS2=1`; absent = today byte for byte** (a `ps2` session cannot exist without it).

## 0. Settled

**S1. PINE on PCSX2 2.8.2**, read from the AppImage's own binary (its `.symtab` names `PINEServer::MainLoop` and the
two state lambdas; `pine_opcodes.txt`; nothing run). The binary holds no header file.
- **The opcode** is the byte after the 4-byte little-endian size; a 16-entry jump table at `0x17ead0`:
  - **0x09 → the block that builds `$_0` → `VMManager::SaveStateToSlot(slot, true, <error OSD>)`;**
  - **0x0A → `$_1` → `VMManager::LoadStateFromSlot(slot, …)`;**
  - 0x0F → the status B49 / B50 already use.
- **The request:** `[u32 size = 6][u8 opcode][u8 slot]`. The slot is one byte. PrivyHub's slots 1-3 map to PCSX2's
  slots 1-3 (PCSX2's own hotkeys cover 1-10).
- **Valid only while the VM state is 2-4** (running, paused, or between), else the reply is a failure.
- **The reply:** `[u32 5][u8 0x00]` OK, or `[u32 5][u8 0xFF]` failure (the shared error path).
- **Not synchronous.** The OK means queued: the block calls `QMetaObject::invokeMethod(g_emu_thread, …,
  QueuedConnection)`. The save's second argument `true` zips the state on a separate thread
  (`ZipSaveStateOnThread`), so **the file is complete some time after the reply**.
- **The file:** in the ini's `Savestates` folder (`data/games/ps2/sstates/`, B49), named `{serial} ({crc:08X}).{slot:02d}.p2s`;
  the previous one is kept as `….p2s.backup` (`BackupSavestate`). PCSX2's log says `Saved state to slot {}.` /
  `Loaded state from slot {}.` (those strings are in the binary).

**S2. PrivyHub's PS1 path, end to end.**
- **The onn:** the game's Game State menu (`MainActivity`, the game paused after Back) → `POST
  /plugins/games/save-state?slot=N` or `load-state?slot=N` (with `&replace=true` for a profile slot).
- **The companion:** `EmulatorManager.save_state` / `load_state`, slots 1-3. A save takes RetroArch's slot 0 and
  copies it to `<stem>.stateN`; the load stages slot 0 and sends `LOAD_STATE_SLOT 0`, and **requires the game paused**
  ("Load State requires the game to be paused").
- **Both record the PS1 slot index** (`data/games/retroarch/privyhub_state_slots.json`, keyed by `system::path`), and
  `_save_state_slot_detail` reads it back. That gives the onn's Game State list (`save_state_slot_details` in every
  `status()`), the "Saved States" view and the tiles.
- **Success:** HTTP 200 and `status()` plus `action` (`save_state` / `load_state`), `slot`, `accepted`, `confirmed`,
  `replaced_existing` (save), `paused` / `verification` (load), `control`, `slot_detail`, `state_file`. The onn shows
  `Saved Slot N - <date> - <size>` / `Loaded …` from `slot_detail`.
- **Failure:** `EmulatorError` → `RuntimeError` → **HTTP 503 `{"ok": false, "error": "<message>"}` for every system** (the
  control API's POST mapping, `privyhub_service.py`). The onn shows its "Game State" dialog `HTTP 503: …`.
  - So the 503 the user saw was B49's *refusal* text, not a PS2-only code. **"The PS1 error shape" and "never 503"
    cannot both hold.** The design follows the user's stated requirement, "exactly as PS1": a PINE failure answers
    HTTP 503 `{"ok": false, "error": …}` with a real failure message in PS1's words, and **never the "not available"
    refusal**. Disclosed for the user.
- **The automatic uses:**
  - the hold / stall's scratch slot 9 (`rewind_cores`: `SAVE_STATE_SLOT 9` at a 400-ms silence or a stall,
    `LOAD_STATE_SLOT 9` at the release under B33's loss rule) and the hold's `REWIND` (`hold_rewind`);
  - the link give-up save (`save_recovery_state`, slot 0 + copy).

**S3. What can go through PINE now.**
- **The SAVE / LOAD buttons: yes** (this item).
- **The hold's return and the stall resume: kept off.** Their budget is a load within the release. PINE's save
  completes asynchronously at an unmeasured time, and B cannot run PCSX2 to measure it, so whether it fits is unknown.
  Disclosed. HOME-5 measures the button save's write time (the game log), which decides a later item. **C13 does not
  run.**
- **The rewind: not available in PCSX2. It stays off,** disclosed.
- **The link give-up save:** kept off (not asked).

## 1. The design

- **`ps2_session`:**
  - `MSG_SAVE_STATE = 0x09`, `MSG_LOAD_STATE = 0x0A`, `MSG_STATUS = 0x0F`, `PINE_OK = 0x00`;
  - `pine_call(path, opcode, payload, timeout)` → the result byte, or None with no answer;
  - `Session` gains `pine_path` (default B49's socket path) and `state(op, slot)`;
  - `ensure_pine_pause()`: a SIGSTOP-paused PCSX2 cannot answer PINE, so SIGCONT, then the hotkey pause confirmed by
    PINE; else an error.
- **`EmulatorManager.save_state` for a `pcsx2` session** (replacing B49's refusal):
  1. the slot normalized (1-3); `ensure_pine_pause()` when paused by SIGSTOP;
  2. a snapshot of `data/games/ps2/sstates/*.p2s` (name → mtime, size);
  3. PINE `0x09` + slot; not OK → `EmulatorError("PCSX2 did not acknowledge the save state")`;
  4. wait ≤ **`SAVE_BOUND_S = 10 s`** for the file ending `.{slot:02d}.p2s` that is new or changed: its size the same
     on two polls 0.25 s apart, and a readable zip. Not by the bound → `EmulatorError("PrivyHub could not verify the
     saved PS2 state")`.
     - **The bound:** no write time could be measured (B cannot start PCSX2). A PS2 state (~45 MB raw, zstd) is
       expected to write in about 1 s on the hub's disk, so 10 s is ≥ 10×. HOME-5 logs the real time, and a later
       revision sets the bound to 5× the measured time.
  5. `_record_state_slot_index(slot, file)`: **the PS1 index**, so the slot detail, the Game State list and "Saved
     States" read the PS2 save exactly as a PS1 one;
  6. the PS1 payload (`control: "pcsx2_pine_save_state"`, `pine_response: "ok"`); the game log
     `PS2 save: slot N pine 0x09 ok; file complete <s>s`.
- **`load_state` for a `pcsx2` session:**
  1. the PS1 preconditions: an active session, the game paused, the slot detail existing (PS1's messages: "No save
     state exists in Slot N" …);
  2. `ensure_pine_pause()`; PINE `0x0A` + slot; not OK → `EmulatorError("PCSX2 did not acknowledge the load state")`;
  3. confirmation: `Loaded state from slot N.` in PCSX2's own log within **3 s** → `confirmed: true`,
     `verification: "pcsx2_log"`; else `confirmed: false`, `verification: "visual_required"` (PS1's two values);
  4. `paused: true`; the PS1 payload (`control: "pcsx2_pine_load_state"`); the game log
     `PS2 load: slot N pine 0x0a ok; <confirmed|visual>`.
- **Files:** in `data/games/ps2/sstates/` on the hub (B49's ini); never the drive.
- **The `ps2_session` row:** `savestates: "pine"` replaces `save_states: "off"`; `off` keeps the four automatic
  behaviours (S3). Disclosed.
- **Kept:** the six B49 refusals for the recovery save / load / copy (not the buttons) and the `ps2_mode` skips.

## 2. Tests (`tests/ps2_session`, < 10 s)

- **The codes:** `MSG_SAVE_STATE == 0x09`, `MSG_LOAD_STATE == 0x0A`, `MSG_STATUS == 0x0F`, asserted against the binary's
  reading (`pine_opcodes.txt`).
- **A PINE socket double** (a Unix socket thread that records each request and answers as configured, writing a fake
  `.p2s` zip like PCSX2):
  - SAVE on a fake `ps2` session → the request `[6][0x09][slot]` → the PS1-shaped payload, the index written, the slot
    detail `exists`, the game log line;
  - LOAD → `[6][0x0A][slot]` → the PS1-shaped payload, `confirmed` from a fake PCSX2 log line, `visual_required`
    without it;
  - a PINE `0xFF` / no answer / no file → `EmulatorError` (HTTP 503 `{"ok": false, "error"}` as PS1), never the
    refusal text;
  - LOAD of an empty slot → PS1's message; LOAD while not paused → PS1's message;
  - a SIGSTOP-paused session → SIGCONT, then the hotkey confirmed, then the save;
  - the slot list from fake files (`status()`'s `save_state_slot_details`);
  - the row's `savestates: "pine"`.
- **A PS1 session's `save_state` / `load_state` / slot detail untouched:** the methods' RetroArch body is unchanged; a
  `retroarch` session never takes the branch.
- **Absent → today:** B49 / B50's absent tests.

**Docs only:** C10's off-check description and C9's row, as insertions.
