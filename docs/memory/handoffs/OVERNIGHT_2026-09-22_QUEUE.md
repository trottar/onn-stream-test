---
memory_schema: 1
as_of: 2026-09-22
status: OVERNIGHT QUEUE — four handoffs in order, unattended; the user is asleep and will read the records in the morning; authorized by the user 2026-09-22
---

# Overnight queue, 2026-09-22

Run these in order, one at a time, each recorded in `docs/memory/` before the next starts. Ask nothing; there is nobody to answer. Every task carries its own read-first list, its own classification rule and its own memory list — this file only sets the order and the gates.

| # | handoff | needs | gate | approx. |
| --- | --- | --- | --- | --- |
| 0 | `D-BASE-P6A_TASK.md` | one 20-min session + 60 s check | already running, or run first if its record is absent | 45 min |
| 1 | `D-BASE-S3_TASK.md` | one 180-min session, instruments only | P6a recorded (any classification); the profile in force must be the P6a profile with `any_override: false` | 3 h 20 min |
| 2 | `D-BASE-P7_TASK.md` | one client build, one 20-min session | S3 recorded; teardown clean | 1 h 15 min |
| 3 | `H2_PREP_TASK.md` | read-only host inventory, rewrite of `D-BASE-H2_TASK.md` | none — run it even if 1 or 2 stopped early | 25 min |
| 4 | `M1_DOCS_RECONCILE_TASK.md` | documentation only, no commit | after 3, so it can cite P7 and H2-PREP | 40 min |

**Rules across the night.**

- **One session at a time.** Teardown per TOOLS.md between tasks: game stopped, banner gone, no orphaned RetroArch; the companion is restarted for P7's build and left running on the default profile at the end.
- **The adopted profile stays adopted.** No task tonight changes an encoder flag. S3 and P7 confirm `any_override: false` before their holds. If P6a classified DEVELOPMENT-ONLY, S3 and P7 still run on it and say so in their records — do not revert.
- **If a session dies**, record what the logs show (recovery log, decoder session, heartbeat tail), classify INDETERMINATE for that task and move to the next task on the list. Never retry a failing action more than twice.
- **Tasks 3 and 4 do not depend on the stream.** If task 1 or 2 cannot run, still do 3 and 4.
- **Nothing is committed to git.** M1 writes a checkpoint proposal; the commit is the user's.
- **Privacy as always:** no addresses, MACs, SSIDs, serials, credentials or device identifiers in any memory or evidence file; the Opal is read-only over `ssh opal` and only if `BatchMode` succeeds in one try.
- **At the end**, `docs/memory/CURRENT.md` must list, in order, each task's classification and record file in one line each, and the Next Action must read: `H1` SSH console (user), `H2` headless cutover when the plug is installed (user's word), `R3b` by hand, then whatever `S3`/`P7` left open. `python3 tools/check_memory_health.py` healthy.
