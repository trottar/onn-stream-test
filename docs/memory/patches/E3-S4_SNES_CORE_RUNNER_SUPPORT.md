---
memory_schema: 1
as_of: 2026-10-06
baseline_commit: d9fdbdd
durable_memory_updated: true
---

# E3-S4: runner support for a lighter SNES core (tools only); the companion change prepared, NOT APPLIED

## Purpose

E3's fourth item (`handoffs/E3-S4_SNES_LIGHTER_CORE_TASK.md`, record
`evidence/E3_S4_SNES_LIGHTER_CORE_2026-10-06.md`) is **NOT RUN**: no
lighter core is installed, and the fetch was refused by the session's
permission policy.

## Change

**`tools/e1_suite.py`** (measurement tool):

- `SNES_CORENAMES` (snes9x → "Snes9x", snes9x2010 → "Snes9x 2010",
  snes9x2005_plus → "Snes9x 2005 Plus").
- A plan row carrying `PRIVYHUB_SNES_CORE=<core>` moves the game's
  counter override to that corename's config directory.
- The override's directory is created if missing.

**Not applied:**
`evidence/e3_s4_2026-10-06/e3_s4_snes_core_PROPOSED_NOT_APPLIED.diff`
(`companion/games/emulator_manager.py`, `_resolve_game`,
`PRIVYHUB_SNES_CORE`).

## Validation

`e1_suite.py --self-test`. No run.

## Rollback

Revert the two hunks in `tools/e1_suite.py`.
