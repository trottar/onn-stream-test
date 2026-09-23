---
memory_schema: 1
as_of: 2026-09-22
status: TASK HANDOFF — D-BASE-R3c Part 2, the recovery-flow change under the user's decisions of 2026-09-22 (never into a live core; and option A — recovery saves load into a RUNNING fresh core); companion + client change, adb-driven validation; authorized by the user 2026-09-22 for an unattended run
---

# D-BASE-R3c Part 2 — recovery resumes into a fresh, running core

**The user's decisions, both 2026-09-22, verbatim in substance.**

1. (`decisions/D-BASE-R3C_RECOVERY_NEVER_INTO_LIVE_CORE.md`) A recovery
   state is never loaded into a running session. Live session → the tile
   is **Resume**, no prompt, no load. No live session + `.state.recovery`
   → the three-option prompt before launch. `native-stream-stop` keeps its
   meaning.
2. **Option A** from `evidence/D_BASE_R3C_RECOVERY_SEMANTICS_2026-09-22.md`:
   resume-from-recovery **launches fresh, unpauses, loads the state into
   the running core (`LOAD_STATE_SLOT 0` as arm R did), then pauses for
   the stream handoff**. The paused-load precondition is relaxed **for the
   recovery path only**; the ordinary Save/Load path (`AGENTS.md`: stable)
   is untouched.

Read first: the R3c record (arms P/Q loop, R plays, G plays — the numbers
this change must reproduce), `evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`,
`investigations/LINK_DROP_RECOVERY_DESIGN.md`, `companion/plugins/games.py`
(`native-stream-stop`, `recovery-resume`, `recovery-discard`,
`copy-to-slot` if present, the tile data), `companion/games/emulator_manager.py`
(`load_recovery_state` and its paused check, launch, pause/resume, the
RetroArch command port), `PrivyHub/app/src/main/java/.../MainActivity.kt`
(tile, prompt), `evidence/d_base_r3c_2026-09-22/r3c_probe.py` (the exact
launch → unpause → load → grab sequence that played), `TOOLS.md`.

**The recovery save to test with:** `evidence/d_base_r3c_2026-09-22/recovery_copy/`
holds the N150 save, its `.png` and `privyhub_recovery_save.json`
(SHA-256s in `recovery_copy_sha256.txt`). Restore the three files into
place before each check that needs a prompt (paths in the R3c record);
verify the hash after copying. **The E30 save was discarded by the user;
this copy is the only one.** Leave `recovery_copy/` untouched at the end.

## The change — one coherent change, nothing else

- **Companion `recovery-resume`:** if any live session exists, end it
  cleanly first (the normal stop path with the manager's save-files
  flush). Then launch the requested title fresh, wait for the window,
  **unpause**, issue the state load into the running core through the
  manager (a new `load_recovery_state_running()` or a `running=True`
  argument — the existing paused-only entry point stays as it is for
  Save/Load), confirm RetroArch's `[State] Loading` line or the command
  reply, then **pause** so the stream handoff finds the same paused
  session a normal launch leaves. On success (state loaded, core paused,
  session live) delete `.state.recovery`, its `.png` and the index entry;
  on any failure keep them and return the error to the client.
- **`recovery-discard`** deletes the three; **`copy-to-slot`** copies the
  file into the chosen slot without launching, then deletes the recovery
  file (state that in the record).
- **Tile data:** `live_session: {title, paused}` and
  `recovery_available: bool` per title.
- **Client tile:** live session for this title → primary action
  **Resume** (open the stream, no prompt, no load). No live session and
  `recovery_available` → the prompt before launch. Neither → plain launch.
  Live session for a *different* title → launch normally; the companion
  ends the other session first.
- **No change** to the recovery state machine or its constants, the
  encoder, the stream, `native-stream-stop`, or the Save/Load path.

Inspect exact current source and record pre-patch hashes; compile
Python; `git diff --check`; Android build and install per `TOOLS.md`
(record the APK hash; note the P8 diagnostic client build v2 is what is
installed today and this build replaces it — keep P8's ring, it is
passive); restart the companion (D-068) with 8765 checked free and
`DISPLAY=:0`.

## Validation — adb-driven per TOOLS.md, the onn on and paired (port 5555)

0. **Fresh-core running load plays (the probe, repeated on the new path).**
   Restore the recovery copy. Through the new `recovery-resume` only (no
   client): the session comes up paused with the state loaded; then
   unpause and run 30 s `x11grab → framemd5` on the managed window as
   `r3c_probe.py` did. Reading: distinct frames **in the hundreds** with
   per-second uniques at the FMV rate (arm R: 615, 20-21/s) — **not 22**.
   If it loops, stop: DEVELOPMENT-ONLY, the change left installed, the
   record says exactly which step differs from arm R.
1. **Live session → Resume.** Launch the reference title, open the stream,
   30 s attract mode, BACK (session stays, paused). Tile reads Resume;
   tapping reopens the stream on the **same RetroArch pid**, no
   `[State] Loading` line in that session's RetroArch log, output within
   3 s.
2. **No live session + recovery file → prompt → fresh running load.** Stop
   the session; restore the copy. Launch from the launcher: prompt appears
   (uiautomator dump); choose resume-from-recovery: a **new** pid, the
   `[State] Loading` line, stream opens, and the picture moves — 60 s of
   `native_frame_sizes.jsonl` with IDR spread in the gameplay/FMV band and
   the onn's report clean; the three recovery files gone afterwards; a
   second launch shows no prompt.
3. **Discard.** Restore, launch, choose discard: the three files gone, plain
   launch (no `[State] Loading`).
4. **Copy to slot.** Restore, launch, choose copy-to-slot: the slot file's
   SHA-256 equals `05bd85c7…abbd8040`; plain launch; recovery file deleted
   after the copy.
5. **Cross-title.** Live paused session of the reference title; launch a
   different title: the old session ends cleanly (no orphan pid, save files
   flushed), the new one launches.
6. **Gameplay save through the running path** (option A's own check):
   as arm G, run to the attract fight, `SAVE_STATE_SLOT 0`, stop the
   session, stage that file as `.state.recovery` (plus index), and go
   through check 2 again: it must play at 60 fps (arm G: 1,640 distinct).
   Restore the recovery copy afterwards.

RUNTIME VALIDATED only if 0-6 all pass; otherwise DEVELOPMENT-ONLY with
the failing check named, the change left installed, `CURRENT.md` saying
so. Teardown per `TOOLS.md`; `recovery_copy/` intact (hash-checked); no
recovery file left in the states directory; companion idle.

## Record and memory

`evidence/D_BASE_R3C2_RECOVERY_FLOW_<date>.md` (raw first, then the seven
checks) with artifacts and SHA-256s under `evidence/d_base_r3c2_<date>/`;
patch record and `PATCH_INDEX.md`; the decision record updated with option
A as the user's choice; `investigations/LINK_DROP_RECOVERY_DESIGN.md`
(the resume sequence: launch → unpause → load → pause); `CURRENT.md`
(fixed headings, `python3 tools/check_memory_health.py` healthy — trim);
`MEMORY.md` (the rule and the sequence, two lines); `handoffs/
CURRENT_HANDOFF.md`; `investigations/ACTIVE.md`; `KNOWN_ISSUES.md` (the
two R3b post-run defects closed or narrowed); `TOOLS.md` (tile states, what
RESUME PLAYING means now, the installed APK); the dated memory file. Never
retry a failing action more than twice; INDETERMINATE with the exact
command otherwise. No addresses, ADB endpoints or device identifiers in
any memory or evidence file. Nothing committed.
