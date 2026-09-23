---
memory_schema: 1
as_of: 2026-09-22
status: DECIDED 2026-09-22 by the user (the rule, then option A); IMPLEMENTED and RUNTIME VALIDATED 2026-09-23 by D-BASE-R3c2
---

# Decision — a recovery state never loads into a live core

## The decision (user, 2026-09-22)

- A recovery state is **never loaded into a running core**.
- When a live game session exists (paused because the player left the
  stream screen, or otherwise), the launcher tile for that title reads
  **Resume**, and tapping it resumes that session with **no state load**.
- The recovery prompt (resume from recovery save / copy to a slot /
  discard) appears **only when no live session exists** and a
  `.state.recovery` file does. "Resume from recovery save" then **ends any
  stale session, launches a fresh RetroArch and loads the state into it**,
  and deletes the recovery file once that succeeds.
- `native-stream-stop` keeps its meaning — end the stream, pause the game,
  keep the session. That is a feature; the bug was `recovery-resume`
  acting on a live core.

Source: `evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md` (the two
post-N150 defects, one cause) and the user's instruction recorded in
`handoffs/D-BASE-R3C_TASK.md`.

## What R3c found before implementing it

`evidence/D_BASE_R3C_RECOVERY_SEMANTICS_2026-09-22.md`, Part 1: a fresh
core **also loops** when the N150 recovery save (taken mid-FMV) is loaded
**paused** — which is how today's `load_recovery_state` must load. Loaded
into a **running** core it plays; a gameplay state loaded paused plays. So
this decision fixes defect 1 (the stale session) but not defect 2 (the
loop).

## Open — the user's to decide

How a fresh-core recovery load avoids the loop: **A** load recovery saves
into a running core (relaxes the paused precondition for the recovery
path only — a Save/Load change), **B** keep the paused load and accept
that a cutscene give-up comes back looping, or **C** do not save during
FMV. Options and evidence in the R3c record. Nothing is implemented until
this is chosen.

## The second decision — option A (user, 2026-09-22), implemented

**Resume-from-recovery loads into a fresh core while it is running**:
launch fresh → unpause → `LOAD_STATE_SLOT 0` → pause for the stream
handoff → delete the recovery save. The paused-load precondition is
relaxed **for the recovery path only** (`load_recovery_state_running`);
the ordinary Save/Load path is untouched. Implemented and RUNTIME
VALIDATED by `D-BASE-R3c2` (`evidence/D_BASE_R3C2_RECOVERY_FLOW_2026-09-23.md`,
checks 0-6), with one recorded deviation: copy-to-slot runs inside a plain
session of the title, because the slot bookkeeping is keyed on the live
session.
