# PrivyHub documentation

This directory contains project architecture, operations, diagnostics, roadmap,
and durable development memory.

## Current authority

Use this order:

1. current local source and fresh runtime evidence;
2. newest specific evidence/decision/architecture records;
3. `memory/CURRENT.md`;
4. durable rules in `memory/MEMORY.md`;
5. dated/patch history;
6. superseded `memory/history/` reference.

## Startup

Substantial work starts with:

- `memory/AGENTS.md`;
- `memory/CURRENT.md`;
- only the records CURRENT links for the active task.

Do not eagerly load all historical memory.

## Memory architecture

- `memory/CURRENT.md` — one active objective and one next action.
- `memory/MEMORY.md` — long-lived rules and validated facts.
- `memory/MAINTENANCE.md` — memory health/cleanup policy.
- `memory/handoffs/` — compact handoff notes.
- `memory/evidence/` — runtime proof.
- `memory/investigations/` — investigation detail.
- `memory/decisions/` — decision records.
- `memory/architecture/` — subsystem architecture.
- `memory/patches/` — patch/checkpoint history.
- `memory/roadmap/` — current roadmap state.
- dated files / `memory/history/` — chronology and superseded reference.

## Main project documents

- `ROADMAP.md`
- `PROJECT_STATUS.md`
- `KNOWN_ISSUES.md`
- `DIAGNOSTICS.md`
- `A4_AUDIO_RECOVERY.md`
- `A8_INPUT_PROFILES.md`

When any older top-level document conflicts with newer validated state, prefer
the newer source/evidence and current repository memory.

Do not place private network addresses, credentials, device identifiers, or
user media/content identifiers in shareable documentation.
