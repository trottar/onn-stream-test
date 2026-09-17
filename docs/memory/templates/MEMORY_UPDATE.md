# Memory Update Checklist

- Update dated history with detailed chronology.
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
- Include changed memory files in the same ZIP as the work.
- Set `durable_memory_updated: true` in the package manifest.
- Do not claim runtime validation from source inspection or compilation alone.
