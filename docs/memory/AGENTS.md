---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Agent Operating Rules

## Development method

Use one narrow hypothesis, one targeted diagnostic/probe, fresh evidence, then one coherent patch. Do not stack speculative production changes. Prefer durable instrumentation over repeated ad-hoc commands.

The local working tree is authoritative between checkpoints. GitHub is history/reference unless the user explicitly establishes a clean synchronized checkpoint.

Inspect exact current source before modifying it. Establish the expected pre-state, make one logical change, validate the actual generated/installed output, and avoid unrelated cleanup.

## Stable-subsystem boundary

Do not disturb known-good video, audio, controller, Save/Load, pause/resume, TV/IPTV, metadata/artwork, cheat/mod isolation, or A8 mapping behavior for unrelated work. Reopen a closed investigation only when fresh evidence requires it.

## Runtime evidence

Distinguish source correctness from runtime validation. A development patch is not complete merely because it compiles. Hardware/session behavior must pass the relevant E2E acceptance sequence before a feature is called runtime validated.

Never claim a validation ran if it did not run.

## Privacy

Never ask the user to provide or paste IP addresses. Do not echo user network addresses. Use placeholders/redaction. Prefer privacy-safe summaries over raw packet captures when summaries answer the question.

## Commands

Keep commands narrow and copy/paste friendly. Avoid large unrelated command lists. Admin PowerShell should normally be a one-line command when practical.

## Packaging

Follow `patches/PATCH_PROTOCOL.md`. A failed installer must clearly classify itself as `FAILED BEFORE MODIFICATION` or `ROLLED BACK`; success is `INSTALLED SUCCESSFULLY`. The user should never have to infer whether project bytes changed.

## Current guardrail

The baseline `25e9a14` is the immutable pre-four-player checkpoint. A8 is complete. Four-player controller extension comes before A9. Do not begin A9 or unrelated Phase B/C/D work until four-player support has been staged and runtime validated.
