---
memory_schema: 2
as_of: 2026-09-17
---

# Chat and Memory Communication Protocol

## Start of substantial work

Read:

1. `AGENTS.md`;
2. `CURRENT.md`;
3. only CURRENT-linked records relevant to the task.

Consult `MEMORY.md` selectively. Read handoffs/history only when needed.

## During work

Put detailed chronology in the dated memory log. Put proof in `evidence/` or the
relevant investigation. Put durable conclusions in `MEMORY.md` only when they
are expected to matter beyond the current task.

Do not append completed patch narratives to active-state files.

## End of meaningful work

Update:

- dated history;
- `CURRENT.md` if objective/state/next action changed;
- relevant evidence/investigation/roadmap/decision records;
- `MEMORY.md` only for durable knowledge;
- `CURRENT_HANDOFF.md` only as a compact transfer note.

Follow `MAINTENANCE.md` when thresholds or semantic triggers fire.

## Patch behavior

Memory changes travel with the same patch that establishes the code or evidence
change. Package manifests set `durable_memory_updated: true`.
