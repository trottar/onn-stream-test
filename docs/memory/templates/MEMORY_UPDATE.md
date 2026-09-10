# Memory Update Checklist

- Update the dated `memory/YYYY-MM-DD.md` session log.
- Update `CURRENT.md` if current task/checkpoint/blocker changed.
- Update `MEMORY.md` only for durable cross-session facts.
- Update `decisions/DECISION_LOG.md` when a decision is made/superseded/deferred.
- Update `evidence/RUNTIME_VALIDATION.md` only when validation status actually changes.
- Update the relevant architecture/investigation/debt/roadmap file when scope changes.
- Rewrite `handoffs/CURRENT_HANDOFF.md` so a new chat starts from the correct state.
- Include changed memory files in the same ZIP as the work.
- Set `durable_memory_updated: true` in the package manifest.
- Do not claim runtime validation from source inspection or compilation alone.
