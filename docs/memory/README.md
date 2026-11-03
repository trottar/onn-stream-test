---
memory_schema: 1
as_of: 2026-11-03
---

# PrivyHub Durable Memory

This repository-native memory system keeps project continuity independent of chat or model state.

## Authority order

When sources disagree:

1. current local source and fresh runtime evidence;
2. the newest specific evidence/decision/architecture record;
3. `CURRENT.md`;
4. durable rules in `MEMORY.md`;
5. dated history and patch records;
6. superseded `history/` snapshots and older summaries.

Do not silently merge contradictory states.

## What is here

**Files:**

- `AGENTS.md`: the operating rules and the narrow startup sequence (required by the health check).
- `COMMUNICATION.md`: the cross-session update protocol.
- `CURRENT.md`: the single authoritative resumable state: the objective, the work item, the verified state (the
  fourteen adopted lines), the next action. Its headings are fixed by the health check.
- `LEARNINGS.md`: durable lessons.
- `MAINTENANCE.md`: the maintenance triggers, size thresholds and cleanup procedure.
- `MEMORY.md`: durable rules, invariants and repeatedly useful validated facts.
- `README.md`: this file.
- `REPOSITORY_POLICY.md`: what is committed and what stays local.
- `TOOLS.md`: the proven tools and entry points, the drop-ins and their off switches.
- `USER.md`: the collaboration preferences.

**Directories:**

- `architecture/`: the subsystem boundaries, one file per subsystem (adaptive bitrate, controllers, diagnostics, the
  E1 workload suite, games, the native source contract, network, remote access, streaming, stream telemetry, system,
  TV media, TV-state sync).
- `archive/`: what was archived on 2026-11-03, moved unchanged. It is indexed by `archive/INDEX.md`. It has these
  subdirectories:
  - `current/`: CURRENT.md's history;
  - `docs/`: five retired docs pages and KNOWN_ISSUES' closed sections;
  - `memory/`: the daily logs, the closed investigations, TOOLS' history and the other retired memory files;
  - `prompts/`;
  - `scratch/`;
  - `windows-scripts/`.
- `chats/`: empty since 2026-11-03. `CHAT_INDEX.md` is in `archive/memory/chats/`.
- `decisions/`: the decision records, plus `DECISION_LOG.md`.
- `evidence/`: the runtime proof, one record per item, each with its harness directory. It also holds `reads/` (the
  output of `tools/diag_read.py`) and `snapshots/`. **Records are never moved or edited.**
- `handoffs/`: the task handoffs, the small `CURRENT_HANDOFF.md` (required by the health check) and
  `SESSION_B_STATUS.txt`. `handoffs/README.md` gives the status of every handoff.
- `history/`: superseded snapshots and sections moved out verbatim, for reference only ([`history/README.md`](history/README.md)).
- `investigations/`: the investigation detail still kept in place, for example `BASELINE_STREAM_HEALTH.md` and
  `LINK_DROP_RECOVERY_DESIGN.md`. `ACTIVE.md` is now a short index that holds no live state; `CLOSED.md` and
  `DEFERRED.md` are the other lists.
- `patches/`: the patch notes. `PATCH_INDEX.md` lists every note; `PATCH_PROTOCOL.md` is the patch protocol from the
  ZIP era.
- `repository/`: `CODE_MAP.md` (where the code is) and `DEBT.md`.
- `roadmap/`: empty since 2026-11-03. `STATUS.md` and `D5_MEDIA_SERVER_SUBSTEPS.md` are in `archive/memory/roadmap/`,
  and the roadmap is `docs/ROADMAP.md`.
- `templates/`: `MEMORY_UPDATE.md`.

Git keeps no empty directory, so `chats/` and `roadmap/` exist only on disk.

## Startup

Read `AGENTS.md`, then `CURRENT.md`. Retrieve only the records that CURRENT points to for the active task. Consult
`MEMORY.md` selectively.

Do not load the whole hierarchy at startup.

## Front matter

Memory files start with this front matter:
- `memory_schema: 1`;
- `as_of`, the date the content is true for;
- optionally `status` and `baseline_commit`.

Files still marked `memory_schema: 2` are from the 2026-09-17 ZIP era. They are normalized to 1 when they are next
rewritten. Records are not retrofitted (`MAINTENANCE.md`, "Front matter (memory_schema)").

## Maintenance

Run `python3 tools/check_memory_health.py` when maintenance is triggered or before a major handoff or checkpoint. It
checks:
- that the required files exist;
- the size limits of `CURRENT.md`, `MEMORY.md` and `handoffs/CURRENT_HANDOFF.md`;
- `CURRENT.md`'s headings.

See `MAINTENANCE.md`. Changes are delivered as git commits. The user commits.
