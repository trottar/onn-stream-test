---
memory_schema: 1
as_of: 2026-09-23
status: D-BASE-R3c2 — RUNTIME VALIDATED; checks 0-6 all PASS. A recovery save resumes into a fresh core loaded while RUNNING (option A) and plays; a live session's tile is Resume; the prompt appears only with no live session; discard / copy / cross-title behave as decided
---

# D-BASE-R3c2 — recovery resumes into a fresh, running core

Task: `handoffs/D-BASE-R3C2_TASK.md`, second in
`handoffs/OVERNIGHT_2026-09-23B_QUEUE.md` (authorized by the user
2026-09-22, unattended). Patch: `patches/D-BASE-R3C2_RECOVERY_FLOW.md`.
Evidence: `d_base_r3c2_2026-09-23/`, SHA-256 in `r3c2_sha256.txt`.
Decisions implemented: `decisions/D-BASE-R3C_RECOVERY_NEVER_INTO_LIVE_CORE.md`
and option A (both the user's, 2026-09-22).

## Classification

**RUNTIME VALIDATED — checks 0-6 all PASS.** Defect `R3b-D1` (the tile
routed into a stale session) and defect `R3b-D2` (a mid-FMV recovery save
looping) are both closed on the production path.

## What was installed

Companion `emulator_manager.py` (`load_recovery_state_running`) and
`plugins/games.py` (tile fields, cross-title stop in `launch`, the new
`recovery-resume` and `recovery-copy`); client `MainActivity.kt` (tile
states, prompt before launch, no poll-driven prompt). APK
`21e3d089f2e17fa9ba6753fa4aadfa729fc1f6990a1268c13464a44cd70d9dcb`,
device hash equal. Companion restarted (8765 free, `DISPLAY=:0`),
pid 160925. Pre/post hashes: `pre_patch_sha256.txt`,
`post_patch_sha256.txt`.

The resume sequence: end any live session → the normal `launch` (paused
handoff) → `resume()` → 1.0 s → `LOAD_STATE_SLOT 0` into the **running**
core, RetroArch's `[State] Loading state` line required → `pause()` →
delete `.state.recovery`, `.png` and the index. Failure keeps the three
files and ends the fresh session.

## Raw numbers first — the seven checks

Harness: `r3c2_helpers.py` (restore the copy; check 0) and
`r3c2_checks.py` (checks 1-6, driving the real launcher through
uiautomator: GAMES → CONTINUE PLAYING → the title's tile → the dialog's
buttons by text); log `r3c2_run.log`; one JSON per check. The recovery
copy (`d_base_r3c_2026-09-22/recovery_copy/`) was restored into place
before each prompt check, hash-verified each time (`hash OK` in the log),
and was **intact at the end** (`recovery_copy_sha256.txt` and the index
hash both verify).

| # | check | measured | verdict |
| --- | --- | --- | --- |
| 0 | fresh running load plays (no client) | `recovery-resume` 200: new pid 161028, paused, `[State] Loading … 16777240 bytes` (source `05BD85C7…8040`), files discarded. Unpaused, 30 s `framemd5`: **607 distinct**, 20-21/s from second 1 (arm R 615; the loop was 22). Snapshots: the save's own scene, then the FMV moved on | **PASS** |
| 1 | live session → Resume | stream opened by RESUME PLAYING, 30 s, BACK (`active`, paused, pid 162140). Tile buttons **Resume, Options** (no Launch). Tap Resume: stream in 5.9 s, **same pid 162140**, one RetroArch log for the whole check and **no `[State] Loading`**; report `first_clean_idr_ms` **632**, max gap 115, 58.1 fps | **PASS** |
| 2 | no session + recovery → prompt → resume | Tile: Launch on Companion, Options. Prompt shown with all five options + Not now. Resume from recovery save: stream in 8.2 s, **new pid 162852**, `[State] Loading` in its log; 60 s of `native_frame_sizes`: **61 of 61 distinct IDR sizes, spread 46,889 B** (41,460-88,349; the loop read 3,686 B, a frozen window 0); report 67.2 s, 59.69 fps, max gap 81, lost 19, 0 resyncs. The three files gone. Second launch: the normal "Start Tekken 3" dialog (Start Fresh / Load Save), **no prompt** | **PASS** |
| 3 | discard | prompt → Discard: the three files gone; stream in 7.3 s; one RetroArch log, **no `[State] Loading`** (plain launch); report clean (0 lost, 80 ms max gap) | **PASS** |
| 4 | copy to slot | slot 1 empty before. Prompt → Copy to slot 1: `Tekken 3 (USA).state1` **SHA-256 `05bd85c7…abbd8040`** = the recovery file; the three recovery files gone; **no `[State] Loading`** (plain launch); report clean. The validation's slot write was then undone: slot file removed and `privyhub_state_slots.json` restored (`02b1c2ff…` before and after) | **PASS** |
| 5 | cross-title | Tekken 3 live and paused (pid 163974). Crash Bandicoot's tile → Launch → Start Fresh: the old pid **gone**; its RetroArch log ends `[SRAM] Saved successfully …` twice (the `SAVE_FILES` flush) then `Unloading game`; new pid 164172 runs Crash Bandicoot (164177 is the AppImage's own child, the usual pair); stream in 8.7 s | **PASS** |
| 6 | gameplay save through the running path | arm G's method: attract fight after 140 s, `SAVE_STATE_SLOT 0` (`af4d8cb9…fab5`), session stopped, staged as `.state.recovery` + `.png` + index. Prompt → Resume from recovery save: `[State] Loading` logged; host `framemd5` of the window during the stream: **1,630 distinct**, 60/s in every moving second (arm G 1,640; the same held card at 18-21 s); report 59.32 fps, 0 lost; the three files gone. The slot-0 scratch was then restored to its pre-check bytes | **PASS** |

The recovery prompt's **only** trigger is now the tile, before a launch,
with no live session. Loaded into a running core, a mid-FMV save (checks
0, 2) and a gameplay save (check 6) both play.

## Deviations, recorded

- **Copy-to-slot launches first.** The handoff said "copies without
  launching". The slot bookkeeping (`_record_state_slot_index`,
  occupied-slot confirmation, cheat-profile isolation) is keyed on the
  live session's identity, so the copy runs inside a plain session of the
  recovery's title, which is where the flow ends anyway (check 4: plain
  launch).
- **A 1.0 s settle** between `resume()` and the load. Arm R loaded 20 s
  after boot; checks 0 and 2 show 1 s after boot plays the same.
- **Check 1's first attempt was aborted by the harness**: its title
  pattern also matched the launcher's NOW PLAYING label and tapped the
  bar, which opened the stream (that report,
  `native_decoder_20260923_042019_648.json`, is kept and is not a check
  result). Anchored to the tile's text ("… - PlayStation") and re-run.

## State at the end

No game active; no recovery file in the states directory
(`save_available: false`); the slot-0 scratch and the slot index as they
were; `recovery_copy/` intact; the new companion (pid 160925) left
running and the TV on the launcher, as the queue asks.

## Privacy

UI dumps were parsed in memory and the launcher's status line (which
shows an address) was dropped; no address, endpoint or identifier in any
file here.
