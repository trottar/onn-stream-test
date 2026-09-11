---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: fa79d4f5feba6797a6993a6fcdcdaff673812da3
---

# Deep Memory / Superseded History

This directory preserves superseded durable-memory snapshots that remain useful
for historical reconstruction but are no longer authoritative for current
development state.

## Trust rule

Files in `history/` are reference only.

When a history snapshot conflicts with newer information, prefer:

1. current local source and fresh runtime evidence;
2. current specific evidence/decision/architecture records;
3. `CURRENT.md`, `CURRENT_HANDOFF.md` and current `MEMORY.md`;
4. dated history and patch records;
5. this directory.

Do not copy an old guardrail, roadmap phase, baseline commit, classifier result
or investigation status back into current memory without checking newer evidence.

## What belongs here

Use `history/` for a coherent superseded snapshot whose full historical context
is worth retaining but would make live `MEMORY.md` misleading or append-only.

Do not move detailed runtime evidence, dated session logs, decisions, patch
history or investigation records here merely to shorten current memory. Those
already have dedicated durable homes.

## Initial snapshot

`MEMORY_SUPERSEDED_THROUGH_2026-09-11.md` is an exact byte-for-byte copy of the
pre-Part-2 `MEMORY.md`.

It preserves the accumulated Phase A/Phase B/C1 chronology, including
intermediate findings and superseded roadmap/guardrail state, while the live
`MEMORY.md` is curated to current durable facts and rules.
