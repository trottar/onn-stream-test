---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: fa79d4f5feba6797a6993a6fcdcdaff673812da3
---

# Agent Operating Rules

## Authority and startup

Treat `L:\Projects\onn-stream-test` as authoritative between checkpoints.
GitHub is reference/history unless a clean synchronized checkpoint has been
validated.

At the start of substantial work, read:

- `CURRENT.md`
- `MEMORY.md`
- `handoffs/CURRENT_HANDOFF.md`
- relevant architecture, decisions, evidence, investigations, patches and roadmap files.

Prefer current local source and newest specific runtime evidence over older
summaries. `history/` is superseded deep memory and must never override current
state.

## Development method

Use:

**one narrow hypothesis -> one targeted diagnostic/probe -> fresh evidence ->
inspect evidence -> one coherent patch**

Inspect exact current source/context before modifying it. Establish the expected
pre-state, make one logical change, validate actual generated/installed output,
and avoid unrelated cleanup.

Do not reopen resolved or explicitly deferred investigations without new
evidence.

## Durable memory

Maintain `docs/memory/` continuously.

- `CURRENT.md` — active state and next step.
- `MEMORY.md` — curated current durable facts/rules.
- `memory/YYYY-MM-DD.md` — detailed dated history.
- `handoffs/CURRENT_HANDOFF.md` — new-chat handoff.
- `decisions/` — decisions/status.
- `evidence/` — runtime/E2E validation.
- `investigations/` — active/closed/deferred work.
- `patches/` — patch/install history and protocol.
- `architecture/` — subsystem architecture.
- `roadmap/` — development position.
- `history/` — superseded deep-memory snapshots/reference only.

Keep `MEMORY.md` curated rather than append-only. Preserve superseded history in
the appropriate dated/evidence/decision/history file instead of deleting it.

Every meaningful patch ZIP must include relevant durable-memory updates and set
`durable_memory_updated: true`.

## Stable-subsystem boundary

Do not disturb known-good video, audio, controller, Save/Load, pause/resume,
TV/IPTV, metadata/artwork, cheat/mod isolation, A8 mapping, diagnostics or
teardown behavior for unrelated work.

Phase A and Phase B are complete. Current technical work is Phase C / C1 explicit
stream profiles. The C1 inventory is complete; the next technical classification
is `C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`.

The first C1 production patch must be behavior-preserving static profile
extraction. No GUI selector, adaptive controller or generalized framework in the
first patch.

## Runtime evidence

Distinguish source correctness from runtime validation. A development patch is
not complete because it compiles.

For game-stream failures, use existing logs/decoders/telemetry before adding new
instrumentation. Reason from measured packets, SPS/PPS, IDR, queued/rendered
frames, stale drops and capture state rather than inferring from “black screen.”

Raw measurements outrank classifiers when they disagree.

Never claim a validation ran if it did not run.

## Privacy

Never ask the user to provide or paste IP addresses. Do not echo user network
addresses. Use placeholders/redaction.

Network-bearing target data and private ADB connection details stay outside the
repository and shareable diagnostics.

## Commands

Use Windows PowerShell for runnable project commands.

Keep commands narrow and copy/paste friendly. For a patch delivery, provide one
complete PowerShell block instead of making the user reconstruct commands from
multiple snippets.

Android build/install:

`.\tools\build_install_onn.ps1; cd L:\Projects\onn-stream-test`

Companion:

`python .\companion\privyhub_service.py`

## Packaging and validation

Follow `patches/PATCH_PROTOCOL.md`.

Before modification:

1. inspect exact current local state;
2. verify expected predecessor state/hash;
3. reject wrong state before writing.

Where applicable, an installer must:

- back up changed files under `archive/patch_backups`;
- preserve line endings/BOM;
- validate actual installed/generated output;
- compile changed Python;
- run Android/Kotlin compilation for Android changes;
- run other required real builds;
- run scoped `git diff --check`;
- restore exact predecessor bytes if validation fails;
- support idempotent reinstall when practical;
- update durable memory.

Result classes must remain explicit:

- `INSTALLED SUCCESSFULLY`
- `FAILED BEFORE MODIFICATION`
- `ROLLED BACK`

On Windows, Git LF/CRLF advisory text is non-failing when the Git command returns
exit code 0. Nonzero remains failure.

Do not combine install and push before independently validating installed state.

Checkpoint with an exact reviewed staging allowlist. Never use broad `git add .`
to choose checkpoint scope.

## Current guardrail

Docs/memory cleanup is active before C1 production implementation.

Part 1 is checkpointed with the completed C1 inventory preserved in Git.

Part 2 curates `MEMORY.md` / `AGENTS.md` and introduces the `history/` deep-memory
layer. Part 3 normalizes decisions/investigations. Part 4 refreshes top-level
project docs and ledgers.

Do not start C1 production code until the focused docs/memory cleanup reaches its
intended checkpoint.
