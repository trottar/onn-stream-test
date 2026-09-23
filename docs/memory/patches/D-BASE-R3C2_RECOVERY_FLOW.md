---
memory_schema: 1
as_of: 2026-09-23
baseline_commit: ee2f89f
durable_memory_updated: true
---

# D-BASE-R3c2 — recovery resumes into a fresh, running core

## Purpose

The user's two decisions of 2026-09-22
(`decisions/D-BASE-R3C_RECOVERY_NEVER_INTO_LIVE_CORE.md`): a recovery state
never loads into a live core; and **option A** — resume-from-recovery
launches fresh, **unpauses, loads into the running core, then pauses** for
the stream handoff, because a mid-FMV save loaded paused loops
(`evidence/D_BASE_R3C_RECOVERY_SEMANTICS_2026-09-22.md`). Built and
installed directly under the overnight authorization
(`handoffs/OVERNIGHT_2026-09-23B_QUEUE.md`), not as a ZIP.

## Changed scope

**`companion/games/emulator_manager.py`**
`f5b2d805…d25a5` → `c5d98052…708474`.
- New `load_recovery_state_running()`: same staging as
  `load_recovery_state` (`<stem>.state.recovery` → slot-0 scratch,
  SHA-256 verified), the precondition **inverted** (the core must be
  `PLAYING`, not paused), `LOAD_STATE_SLOT 0`, and **RetroArch's own
  `[State] Loading state` line required** within 2 s (`Failed to load
  state` still fails it). Probe event `load_state_link_drop_recovery_running`.
- `load_recovery_state` (paused) and the player Save/Load path are
  **unchanged**.

**`companion/plugins/games.py`**
`c7c753a9…aa034` → `60184e35…bd73d` (includes `P8`'s knob, already there).
- `details` (the tile data) gains `live_session` {game_id, title, paused}
  or null, `recovery_available` (a recovery save exists **for this id**),
  `recovery_saved_at`.
- `launch`: a live session of a **different** title is ended first through
  the normal `stop` path (`recovery.session_ended()`, `emulator.stop()`
  with its `SAVE_FILES`, `end_game_session()`); the same title is left
  alone (its tile is Resume).
- `recovery-resume`: end any live session → the normal `launch` action
  (controller preflight, paused handoff) for the recovery's `game_id` →
  `emulator.resume()` → 1.0 s → `load_recovery_state_running()` →
  `emulator.pause()` → `discard_recovery_state()` (file, `.png`, index).
  On failure the recovery save is **kept**, the fresh session is ended,
  and the error goes to the client.
- `recovery-copy`: the slot bookkeeping is keyed on the live session's
  identity, so the copy runs **inside a plain session of the recovery's
  title** (launched if none is live), through the unchanged verified
  `copy_recovery_state_to_slot`, then the recovery save is discarded. The
  handoff asked for "without launching"; the flow ends in a plain launch
  either way.
- `recovery-discard` unchanged.

**`PrivyHub/app/src/main/java/MainActivity.kt`**
`a727f515…c44e9` → `2e31feb4…c464`.
- Game tile dialog: `live_session` for this id → positive button
  **Resume** (opens the stream; no prompt, no load). No live session and
  `recovery_available` → **Launch on Companion** raises the recovery
  prompt before any launch. Otherwise the normal launch dialog.
- The status poll **no longer raises the prompt** (`maybeShowRecoveryPrompt`
  and `recoveryPromptShownFor` removed).
- Prompt choices all end in a launch: Resume / Copy → the companion
  launches, the client opens the stream; Discard → the client's plain
  launch. `requestRecoveryAction` takes an `onSuccess`.
- `NativeStreamActivity.kt` and `NativeAudioReceiver.kt` unchanged (`P8`
  build v2's passive ring kept).

## Validation performed

`py_compile` both Python files; `git diff --check` clean;
`./gradlew :app:assembleDebug` BUILD SUCCESSFUL; APK
`21e3d089f2e17fa9ba6753fa4aadfa729fc1f6990a1268c13464a44cd70d9dcb`
installed, device hash equal; companion restarted (8765 free,
`DISPLAY=:0`). Runtime: `evidence/D_BASE_R3C2_RECOVERY_FLOW_2026-09-23.md`.
