---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 0206017cfd8f0fc57decb7a5e9e8632e6a4f6cdd
---

# Agent Operating Rules

## Authority

Treat `/home/privyhub/Projects/onn-stream-test` as authoritative between
checkpoints. GitHub is reference/history unless a clean synchronized checkpoint
has been validated.

Prefer current local source and the newest specific runtime evidence over
summaries. Never let stale documentation override newer validated state.

## Startup

For substantial work:

1. read `CURRENT.md`;
2. read only CURRENT-linked records relevant to the active task;
3. consult `MEMORY.md` selectively for durable architecture/rules;
4. consult handoffs, history, investigations, patches, and evidence only when
   needed.

Follow `MAINTENANCE.md`. Do not eagerly load the full memory hierarchy.

## Development method

Use:

**one narrow hypothesis -> one targeted diagnostic/probe -> fresh evidence ->
inspect evidence -> one coherent patch**

Inspect exact current source before modifying it. Establish the expected
pre-state, make one logical change, validate installed/generated output, and
avoid unrelated cleanup.

Do not reopen resolved or explicitly deferred investigations without new
evidence. Raw measurements outrank classifiers when they disagree.

## Durable memory

- `CURRENT.md` — single active objective, current state, exact next action.
- `MEMORY.md` — long-lived rules and validated facts, not chronology.
- `YYYY-MM-DD.md` / `memory/` — detailed dated history.
- `handoffs/CURRENT_HANDOFF.md` — small transfer note only.
- `architecture/` — subsystem architecture.
- `decisions/` — decisions and status.
- `evidence/` — runtime/E2E proof.
- `investigations/` — active/closed/deferred investigation detail.
- `patches/` — patch/install history.
- `roadmap/` — current development position.
- `history/` — superseded deep-memory reference.
- `MAINTENANCE.md` — memory lifecycle and health policy.

Every meaningful patch ZIP must include the relevant durable-memory changes and
set `durable_memory_updated: true`.

## Stable subsystem boundary

Do not disturb validated video, audio, controller, Save/Load, pause/resume,
TV-state sync, VOD storage, or other stable paths for unrelated work.

A compile/build is not runtime validation.

## Privacy

Never ask the user to provide or paste IP addresses. Do not place private
network addresses, ADB endpoints, device identifiers, credentials, or secrets in
shareable diagnostics or durable memory.

## Commands

Current Linux companion launch:

`python3 ./companion/privyhub_service.py`

Keep commands narrow and copy/paste friendly.

## Patch discipline

Follow `patches/PATCH_PROTOCOL.md`.

Before modification:

1. inspect exact current state;
2. verify expected predecessor state/hash;
3. reject wrong state before writing.

Where applicable, installers must back up changed files, preserve line endings,
validate generated output, compile changed Python, run applicable real builds,
run `git diff --check`, and restore exact predecessor bytes on deterministic
failure.

Result classes remain explicit:

- `INSTALLED SUCCESSFULLY`
- `FAILED BEFORE MODIFICATION`
- `ROLLED BACK`

Checkpoint with an exact reviewed staging allowlist. Never use broad
`git add .` to choose checkpoint scope.
