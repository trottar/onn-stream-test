---
memory_schema: 2
as_of: 2026-09-17
---

# Deep Memory / Superseded History

This directory preserves superseded snapshots/reference that remain useful for
historical reconstruction but are not authoritative current state.

## Trust order

When history conflicts with current material, prefer:

1. current local source and fresh runtime evidence;
2. newest specific evidence/decision/architecture records;
3. `CURRENT.md`;
4. durable rules in `MEMORY.md`;
5. dated/patch history;
6. this directory.

Do not copy an old guardrail, roadmap phase, baseline commit, classifier result,
or investigation status back into current memory without checking newer
evidence.

## 2026-09-17 bootstrap maintenance

Immediately before the memory-maintenance rewrite, the exact active-memory state
is preserved naturally in Git commit:

`0206017cfd8f0fc57decb7a5e9e8632e6a4f6cdd`

That checkpoint contains the pre-maintenance `CURRENT.md`, `MEMORY.md`,
`CURRENT_HANDOFF.md`, active investigation index, and roadmap status. Do not copy
those large files into a second archive merely to shorten the live bootstrap.

Specific technical detail remains additionally preserved in dated memory,
evidence, investigations, patch records, architecture, and decisions.
