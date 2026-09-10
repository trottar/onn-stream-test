---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Chat and Memory Communication Protocol

## Purpose

A chat should be able to start by reading a small, stable set of repository files rather than reconstructing months of discussion. Conversely, meaningful chat conclusions should be committed back into repository memory rather than living only in conversation history.

## Start-of-chat load order

Read `MEMORY.md`, `CURRENT.md`, `USER.md`, and `AGENTS.md` first. Then open the subsystem/decision/evidence files relevant to the task. Use `handoffs/CURRENT_HANDOFF.md` when a compact transfer summary is needed.

## During work

Record durable discoveries in the dated `memory/YYYY-MM-DD.md` file. Do not promote a hypothesis into `MEMORY.md` until evidence supports it. When a decision changes, update its status in `decisions/DECISION_LOG.md` rather than leaving two apparently-current statements.

## End of meaningful work

Update the dated log, `CURRENT.md`, roadmap/evidence/decision files as applicable, and `handoffs/CURRENT_HANDOFF.md`. Curate `MEMORY.md` only when a fact is likely to matter across future phases.

## ZIP behavior

The memory changes belonging to a patch travel in the same ZIP. This makes the patch itself a communication checkpoint: code/data changes, validation state, and the explanation of why the change exists remain together.
