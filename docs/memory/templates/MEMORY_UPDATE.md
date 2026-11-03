# Memory Update Checklist

- Put the chronology in the task's `evidence/` record (the dated logs ended 2026-10-10).
- Update `CURRENT.md` only when active objective/state/blocker/next action changes.
- Keep exactly one authoritative next action in `CURRENT.md`.
- Update `MEMORY.md` only for durable cross-phase facts/rules.
- Put proof in `evidence/`, not in active memory.
- Put investigation detail in `investigations/`.
- Update roadmap/decision/architecture records only when their state changes.
- Keep `CURRENT_HANDOFF.md` small and handoff-specific.
- Run `tools/check_memory_health.py --repo <repo>` when maintenance triggers.
- Follow `MAINTENANCE.md` before beginning another major work item after a hard
  threshold or semantic trigger.
- Leave changed memory files in the working tree with the work, for the user's commit.
- Write the task's `git status` to `logs/<task>_git_status.txt`.
- Do not claim runtime validation from source inspection or compilation alone.
