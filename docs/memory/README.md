---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 0206017cfd8f0fc57decb7a5e9e8632e6a4f6cdd
---

# PrivyHub Durable Memory

This repository-native memory system keeps project continuity independent of
chat or model state.

## Authority order

When sources disagree:

1. current local source and fresh runtime evidence;
2. the newest specific evidence/decision/architecture record;
3. `CURRENT.md`;
4. durable rules in `MEMORY.md`;
5. dated history and patch records;
6. superseded `history/` snapshots and older summaries.

Do not silently merge contradictory states.

## Responsibilities

- `AGENTS.md` — operating rules and narrow startup sequence.
- `CURRENT.md` — single authoritative resumable state.
- `MEMORY.md` — durable rules, invariants, and repeatedly useful validated facts.
- `MAINTENANCE.md` — maintenance triggers, thresholds, and cleanup procedure.
- `COMMUNICATION.md` — cross-session update protocol.
- `handoffs/CURRENT_HANDOFF.md` — small handoff-only note.
- dated memory — chronology.
- `architecture/` — subsystem boundaries.
- `decisions/` — decisions/status.
- `evidence/` — runtime proof.
- `investigations/` — diagnostic detail.
- `patches/` — patch/checkpoint history.
- `roadmap/` — current roadmap position.
- `history/` — superseded snapshots/reference only.

## Startup

Read `AGENTS.md`, then `CURRENT.md`. Retrieve only the records that CURRENT
points to for the active task. Consult `MEMORY.md` selectively.

Do not load the whole hierarchy at startup.

## Maintenance

Run `tools/check_memory_health.py` when maintenance is triggered or before a
major handoff/checkpoint.

See `MAINTENANCE.md`.

## ZIP invariant

Every meaningful future PrivyHub ZIP update includes the memory files changed by
that work and sets `durable_memory_updated: true`.
