# PrivyHub documentation

This directory holds the project's architecture, operations, diagnostics, roadmap and durable development memory.
What PrivyHub is, and how to run it, is in the repository [`README.md`](../README.md).

## Current authority

Use this order:

1. current local source and fresh runtime evidence;
2. newest specific evidence/decision/architecture records;
3. `memory/CURRENT.md`;
4. durable rules in `memory/MEMORY.md`;
5. dated/patch history;
6. superseded `memory/history/` reference.

When an older document conflicts with newer validated state, prefer the newer source or evidence and the current
repository memory.

## Startup

Substantial work starts with:

- `memory/AGENTS.md`;
- `memory/CURRENT.md`;
- only the records CURRENT links for the active task.

Do not eagerly load all historical memory.

## The docs map

| Page | What it holds |
|---|---|
| [`ROADMAP.md`](ROADMAP.md) | the roadmap (Linux-first, with the remote foundation): the phases, their gates and status |
| [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) | open and deferred issues and debt, with an open-items index |
| [`REMOTE_TRUST.md`](REMOTE_TRUST.md) | the remote trust model (G0): the topologies, the threat model, the overlay boundary, session identity, and one section per adopted G line with its off switch |
| [`CAPABILITY_MODEL.md`](CAPABILITY_MODEL.md) | the capability model (E5): the capability classes and their thresholds |
| [`WAN_ADAPTATION_RULES.md`](WAN_ADAPTATION_RULES.md) | the WAN adaptation rules R1-R5 (G5); `PRIVYHUB_WAN_ADAPTATION` itself is not adopted |
| [`DIAGNOSTICS.md`](DIAGNOSTICS.md) | the diagnostics today: the `privyhub-diag` keeper, `diag_read.py` / `diag_check.py`, the companion's self-test and support bundle, then the UDP transport probes and their acceptance tests |
| [`A8_INPUT_PROFILES.md`](A8_INPUT_PROFILES.md) | the named controller input profiles (A8) |
| [`RUNBOOK.md`](RUNBOOK.md) | the user's steps: at home, away from home, if it breaks, going home, the one-line reads |
| [`investigations/`](investigations/) | `2026-09-07-udp-transport.md`, the Windows-era synthetic-UDP study (the issue is still paused) |
| [`memory/`](memory/) | the durable memory: the state, the rules, the records ([`memory/README.md`](memory/README.md)) |

## Memory in brief

- `memory/CURRENT.md`: the active objective and the next action.
- `memory/MEMORY.md`: long-lived rules and validated facts.
- `memory/evidence/`: runtime proof, one record per item, with its harness directory. Records are never moved.
- `memory/handoffs/`: task handoffs. `memory/handoffs/README.md` gives the status of every one.
- `memory/patches/`: patch notes, indexed by `memory/patches/PATCH_INDEX.md`.
- `memory/archive/`: what was archived on 2026-11-03, indexed by `memory/archive/INDEX.md`.
- `memory/history/`: superseded snapshots and moved sections (reference only).

## Archived pages (2026-11-03)

These five pages moved, unchanged, to `memory/archive/docs/`:

- `A4_AUDIO_RECOVERY.md` → [`memory/archive/docs/A4_AUDIO_RECOVERY.md`](memory/archive/docs/A4_AUDIO_RECOVERY.md):
  the Windows A4 audio lifecycle fix (WASAPI); done.
- `DEBUGGING_HARNESS.md` → [`memory/archive/docs/DEBUGGING_HARNESS.md`](memory/archive/docs/DEBUGGING_HARNESS.md):
  the one-command PowerShell harness (the script no longer exists). Today's equivalents are the `privyhub-diag` keeper,
  `tools/diag_read.py` / `tools/diag_check.py` and the support bundle; see [`DIAGNOSTICS.md`](DIAGNOSTICS.md).
- `DEBUGGING_MEMORY.md` → [`memory/archive/docs/DEBUGGING_MEMORY.md`](memory/archive/docs/DEBUGGING_MEMORY.md): the
  Windows-era durable rules; the current rules are in `memory/MEMORY.md`.
- `PROJECT_STATUS.md` → [`memory/archive/docs/PROJECT_STATUS.md`](memory/archive/docs/PROJECT_STATUS.md): the status
  as of 2026-09-28. The current state is `memory/CURRENT.md` and `ROADMAP.md` §0.
- `REPOSITORY_AUDIT_2026-09-07.md` →
  [`memory/archive/docs/REPOSITORY_AUDIT_2026-09-07.md`](memory/archive/docs/REPOSITORY_AUDIT_2026-09-07.md): the
  pre-push repository audit; done.

The closed sections of `KNOWN_ISSUES.md` moved verbatim to `memory/archive/docs/KNOWN_ISSUES_CLOSED_2026-11-02.md`.
The full list of moves is `memory/archive/INDEX.md`.

## Sharing rule

Do not place private network addresses, credentials, device identifiers, or user media/content identifiers in
shareable documentation. Use placeholders.
