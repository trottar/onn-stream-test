---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Patch and ZIP Protocol

## Before modification

Inspect the exact local source, establish exact expected pre-state/hashes, and make one coherent change. Do not reconstruct an expected local state from Git when a successful local receipt records authoritative installed bytes.

## Installer behavior

Where applicable, a patch installer must reject wrong-state input before modification, back up changed files under `archive/patch_backups`, preserve line endings/BOM, validate actual installed/generated output, run syntax/compile/build steps, run `git diff --check`, and restore exact pre-patch bytes if post-write validation fails.

Result classes must be explicit:

- `INSTALLED SUCCESSFULLY`
- `FAILED BEFORE MODIFICATION`
- `ROLLED BACK`

Target actual Windows PowerShell compatibility. Parse PowerShell scripts before execution. Avoid newer .NET APIs unless target availability is proven. Use absolute paths for staging/process work where possible. User-facing blocks must be syntactically complete when pasted as one block; do not provide a detached `finally` cleanup section.

## Validation

Validate deterministic transformers/probes, fixture install, idempotence, wrong-state rejection, rollback behavior where practical, ZIP integrity, exact contents, generated hashes, Python compile, Kotlin/Android compile when Android changes, and other real builds required by changed components.

Never report a check as passed if it did not execute.

## Memory invariant

Every meaningful ZIP must include the `docs/memory` files affected by that work. Update the dated session log and any changed `CURRENT`, decision, evidence, roadmap, or handoff files. The package manifest must include:

`durable_memory_updated: true`

The memory files are part of the patch, not after-the-fact prose.
