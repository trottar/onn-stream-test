# B57 — design, written before any B57 code (the PS2 multitap relaunch through PINE; the import ignore line)

Queue: `handoffs/QUEUE_2026-11-08U.md` §B57. Baseline `d618a20a` (IMPORT-1 committed; the tree clean). Built in
`/tmp/b_q13u_b57` (companion/, tools/, tests/, PrivyHub/ only); the tree gets the diff at the end, uncommitted.

## 0. Settled

**B54's relaunch for PS1 (RetroArch), as built** (`companion/relaunch_ports.py`):
pause → `save_relaunch_state` (SAVE_STATE_SLOT 0 copied to `<stem>.state.relaunch`, verified; a failure = refused,
nothing touched) → the encoder stopped → the core stopped → the launch with the new ports → resume → a 1.0-s settle →
`load_recovery_state_running(source=<the relaunch save>)` (`[State] Loading` required) → pause → the encoder started for
the remembered client on the new window → `relaunch_ports` row (`state: loaded`, `steps_ms`, `total_ms`,
`within_budget`) and a `ports_set` row `source: relaunch`. A failed new launch → the previous ports (the same load);
both failing → the session ends (the error is the answer). A failed load → `state: restarted`.

**Where PS2 diverges today:** `kind == "pcsx2"` skips the save (`reason: ps2_no_relaunch_state`), so after the launch
the title runs from its boot: `state: restarted`. `save_relaunch_state` raises `PS2_NO_STATES` on PCSX2;
`load_recovery_state_running` on PCSX2 goes to B55's slot-8 path and ignores `source`.

**The slots (PCSX2's own 1-10; PrivyHub's user slots are 1-3):** 9 = B55's hold / stall scratch, 8 = B55's give-up save,
**7 = the relaunch (new, `ps2_session.RELAUNCH_SLOT`)**. None collides: the slot-9 save can fire on a stall signal
while the relaunch's gate is up, and the slot-8 save at a give-up; neither touches slot 7, and the relaunch touches
neither. The file is PCSX2's `data/games/ps2/sstates/<serial> (<crc>).07.p2s` (and its `.07.p2s.backup`, PCSX2's
BackupSavestate); overwritten at the title's next relaunch; no slot index is written (as PS1's relaunch save), so the
Game State list never shows it.

**The budget** (B54's 15 s from the join to play; the row's `steps_ms` are what A reads):

| step | expected | from |
| --- | --- | --- |
| pause (hotkey, PINE-confirmed) | ~0.1-0.2 s | B49 / HOME-5 |
| **save: PINE 0x09 slot 7 + B52's file-complete check** | **~0.5 s** | HOME-5 / HOME-6 (the file complete 0.5 s after the request) |
| stream stop | ~0.2 s | B54 |
| stop: SIGTERM (≤ 5 s, then SIGKILL ≤ 2 s) | ~1 s | B49 (bound 7 s) |
| launch with `MultitapPort1` per the count (window, sink-input) + **the hold to the ELF** (B52's pre-check) | **~6-9 s** together (H3-P2's boot to the game running; HOME-6: `ELF Loading:` at t 4.68 in PCSX2's log) | H3-P2, HOME-6 |
| **load: PINE 0x0A slot 7 + `Loaded state from slot 7.`** | **≤ 0.31 s** | HOME-6 C12'' |
| **B52's picture check** (3 distinct frames, not black, PINE running, no TLB Miss) | ~0.6 s (0.9 s load-to-picture in all) | HOME-6 |
| pause, stream start | ~0.1 + ~0.8 s | B54 |

**Expected total ~9.5-13 s, inside 15 s** (less margin than PS1's ~6-10 s; the boot dominates). The worst bounds
(window 30 s, sink-input 45 s, ELF 30 s, picture 5 s) can pass 15 s; then `within_budget: false` is recorded and the
game still comes back — the budget is read, not enforced (as B54).

## 1. The design, inside `PRIVYHUB_PS2=1`

Every change is on a branch reached only in a PCSX2 session (`_launch_kind == "pcsx2"`), which exists only with
`PRIVYHUB_PS2=1` (B49: without it the plugin never imports `ps2_session`, `SYSTEMS` has no `ps2`, no PS2 launch). **So
absent = today byte for byte**, and a RetroArch relaunch is untouched in either case.

1. `ps2_session.RELAUNCH_SLOT = 7` (beside `SCRATCH_SLOT` 9, `RECOVERY_SLOT` 8).
2. **`EmulatorManager.save_relaunch_state()`, PCSX2 branch** → `_pcsx2_save_relaunch_state()`:
   B51 / B55's shape — `ensure_pine_pause`, the sstates folder's listing before, PINE 0x09 slot 7, **B52's
   file-complete check** (`wait_state_file`: new / changed, size steady over two polls, a whole zip; `SAVE_BOUND_S`).
   - PINE fail / no answer → `EmulatorError("PCSX2 did not acknowledge the save state")`, log
     `PS2 relaunch save: slot 7 pine 0x09 fail|no answer`;
   - file not complete → `EmulatorError("PrivyHub could not verify the relaunch savestate")`;
   - ok → log `PS2 relaunch save: slot 7 pine 0x09 ok; file complete <s>s`; returns `{ok, action:
     save_relaunch_state, state_path: <the .07.p2s>, size_bytes, slot: 7, ps2_states: "pine"}`. No index.
3. **`load_recovery_state_running(source=…)`, PCSX2 branch:** `source` given → B55's running load with the slot read
   from it (it must be this session's `.07.p2s`, else `EmulatorError("The relaunch save is not this session's PS2
   state")`); `source` None → B55's slot-8 path exactly. The running load is B55's: hold until the ELF is up (B52's
   pre-check: `elf_started` or `wait_elf` ≤ 30 s) → PINE 0x0A slot 7 → `Loaded state from slot 7.` → resume → **B52's
   picture check** → left running. Log `PS2 relaunch load: slot 7 pine 0x0a ok; picture <verdict> <s>s`.
   - The picture `static` / `fault` → `EmulatorError("The game did not resume from the save")` carrying
     `ps2_picture = <verdict>` (the state was loaded and the game did not run from it);
   - the ELF not up, PINE fail → `EmulatorError` without `ps2_picture` (no state was loaded: the game is its fresh
     boot).
4. **`relaunch_ports.run`, `kind == "pcsx2"`** (RetroArch's branch unchanged):
   1. pause (if not paused);
   2. **save** (`step "save"`): `emulator.save_relaunch_state()`. **A failure is not a refusal on PS2:** the title
      restarts without the state, today's behaviour — `row.reason = "ps2_relaunch_save_failed"`, `row.save_error`;
   3. stream stop; **stop** (SIGTERM, B49's `_pcsx2_stop`);
   4. **launch** with `players_chosen=target` → `MultitapPort1` per the count (B46 / B49's plan); the previous-ports
      fallback and the ended path exactly as B54;
   5. with a state: **resume** (PCSX2 boots on) → **load** (`load_recovery_state_running(source=<.07.p2s>)`: the ELF
      hold, PINE 0x0A slot 7, B52's picture check) → `state: loaded`. **No 1.0-s settle on PS2** (the ELF hold is the
      settle);
   6. **the load fails:**
      - with `ps2_picture` (static / fault: the loaded state did not run) → **the title restarts without the state**:
        `stop_clean` + `launch_clean` (the landed ports) → `state: restarted`, `reason: "ps2_relaunch_picture_<v>"`,
        `load_error`. A clean launch failing → the previous ports, then the ended path (as B54's launch);
      - without it (the ELF not up, PINE fail) → the game is its fresh boot already: `state: restarted`,
        `reason: "ps2_relaunch_load_failed"`, `load_error`;
   7. pause; stream start; the rows as B54 (`relaunch_ports` with `state`, `kind: pcsx2`, `steps_ms`, `total_ms`,
      `within_budget`, `ps2_states: "pine"`, `slot: 7` when a save was made; `ports_set` `source: relaunch`).
   - **Never a dead session:** every failure lands on a running title (restarted), except both launches failing,
     which is B54's ended path unchanged.
5. **The response:** `relaunch.state` `loaded` / `restarted` (+ `reason` when restarted on PS2). No client change
   (the client shows "Setting up 4 players…" for either and reads `state` only into its row).

## 2. Tests (no PCSX2, no BIOS, no title; B51's PINE double, B52's fake window / log)

`tests/relaunch_ports/test_b57.py` (and B54's PS2 test moved to B57's meaning, disclosed):
- **the full sequence** on the real `EmulatorManager` with the PINE double and the fake capture (stop / launch faked as
  a new PCSX2 whose log gains `ELF Loading:` once resumed): pause → PINE `[6][0x09][7]` → the `.07.p2s` complete →
  stream stop → stop → launch(4) → resume → the ELF hold → PINE `[6][0x0A][7]` → picture ok → pause → stream start;
  `state: loaded`, `ports_set` 4 / multitap / `relaunch`, the row's `slot` 7, `ps2_states` pine, `within_budget`; the
  game-log lines; **slots 8 / 9 untouched**; no slot index written;
- **a save failure** (PINE fail; the file not complete) → no refusal, `state: restarted`, `reason
  ps2_relaunch_save_failed`, no 0x0A sent;
- **a picture fault** (static; a TLB Miss) → `stop_clean` / `launch_clean`, `state: restarted`, `reason
  ps2_relaunch_picture_static|fault`, the session running;
- **the ELF never up** → `restarted`, `ps2_relaunch_load_failed`, no clean relaunch;
- **PS1 untouched:** B54's RetroArch sequence and rows exactly (B54's suite unchanged and green);
- **absent → today:** with `em._ps2` None (the flag absent) no PS2 session exists; `save_relaunch_state` on a
  non-PCSX2 manager is B54's; the source-less `load_recovery_state_running` on PCSX2 is B55's slot-8 path.
- B55 / B51 / B52's suites unchanged and green.

## 3. The ignore line

`.gitignore` gets `PrivyHub-Import/` (a hand-copied stick folder anywhere in the repo). `data/import/` is already
ignored by `data/`; checked with `git check-ignore -v` in the tree for both (`PrivyHub-Import/games/ps1/x.chd`,
`data/import/plans/x.json`).

## 4. Record

`evidence/B57_PS2_RELAUNCH_STATE_2026-11-08.md` + `b57_2026-11-08/` (design + hash, diff, proof absent, tests ×3,
mutations, host suites against the baseline copy, `git_check_ignore.txt`, `redact_check.txt`, `manifest.sha256`);
`patches/B57_PS2_RELAUNCH_STATE.md`.
