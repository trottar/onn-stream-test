# Repository memory maintenance — 2026-09-17

## Purpose

Convert active project memory from append-only patch chronology into a compact
repository-native bootstrap.

## Scope

Documentation/tooling only.

No Android, companion, playback, networking, storage, Games, or EPG runtime
behavior changes.

## Architecture

- `CURRENT.md` is the single authoritative resumable state.
- `MEMORY.md` contains durable knowledge rather than chronology.
- `CURRENT_HANDOFF.md` is handoff-only.
- `MAINTENANCE.md` defines soft/hard and semantic triggers.
- `tools/check_memory_health.py` reports threshold/structure health.
- history/evidence/investigations/patch records preserve detail.

The exact pre-maintenance active-memory state remains available in Git commit
`0206017cfd8f0fc57decb7a5e9e8632e6a4f6cdd`.

## Product state recorded

D-126 is accepted from runtime evidence. The next product work item remains
D-127 incorrect-guide durable intent/recheck.

## Validation

Installer:

- validates exact predecessor HEAD and blobs;
- backs up every touched tracked file;
- compiles and self-tests the memory-health utility;
- runs the health check after rewriting active memory;
- regenerates `docs/memory/manifest.json`;
- runs `git diff --check`;
- rolls back exact predecessor bytes on deterministic failure.
