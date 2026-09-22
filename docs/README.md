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
- `memory/handoffs/` — compact handoff notes, plus **task handoffs**: a
  self-contained brief written by the user's assistant, run start-to-finish
  by Claude Code, and recorded in `memory/evidence/` with its own harness
  directory and SHA-256s.
- `memory/evidence/` — runtime proof, one record per investigation item.
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

## Newest evidence records (2026-09-20 to 2026-09-22)

The `D-BASE` baseline-stream-health chain, newest first. Each is one file
under `memory/evidence/` with its harness beside it:

- `D_BASE_S3_CAP_SOAK_2026-09-22.md` — three hours on the adopted frame
  cap; the residual loss correlates with nothing.
- `D_BASE_P7_STARVATION_COUNTER_2026-09-22.md` — what
  `prolonged_starvation_events` counts: audio arrival jitter, not loss.
- `D_BASE_P6A_CAP_ADOPTED_2026-09-22.md` — the 90 KB frame cap becomes a
  profile default.
- `H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md` — the host's display,
  session and boot path, read before the monitor is removed.
- `D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md` — the intervention that
  established the cause.
- `D_BASE_P5_WHICH_QUEUE_2026-09-21.md` — which queue drops the burst.
- `O1_OPAL_AIR_VIEW_2026-09-21.md` — the router's read-only view of the
  air.
- `D_BASE_S2_*`, `D_BASE_S1_*`, `D_BASE_T1_*`, `B2_HOST_ON_OPAL_*`,
  `D_BASE_P4_*`, `D_BASE_P3_*`, `D_BASE_R5_*` — soaks, thermals, topology
  and instruments.
- `GROUP_A_*_2026-09-20.md`, `D_BASE_R2/R3/R3A/R4_*`, `D_BASE_P1/P2/P2A_*`
  — the host-side causes, recovery and the earlier instruments.

Classification for each is in `memory/evidence/RUNTIME_VALIDATION.md`.

When any older top-level document conflicts with newer validated state, prefer
the newer source/evidence and current repository memory.

Do not place private network addresses, credentials, device identifiers, or
user media/content identifiers in shareable documentation.
