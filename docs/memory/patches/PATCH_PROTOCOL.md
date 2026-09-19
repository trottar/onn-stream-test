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

## Two tiers, and how to choose

**Tier 1 — ordinary change the build validates.** Source edits, memory-only
updates, anything where a compiler or the memory-health checker will catch a
mistake. Deliver: payload, per-file predecessor SHA-256, a plain installer that
writes and verifies, and the copy/paste block. Nothing else. No self-test, no
fixture, no sandbox pre-validation. This is the default and covers almost
everything.

**Tier 2 — structural change with no compile-time check.** Files moving,
renaming or being deleted across the tree, where nothing downstream would notice
a mistake. Here a fixture-based self-test earns its cost, because the failure
mode is silent. `ANDROID-FLAT` and `STREAMLINE` are the only two examples in
this repository's history.

If unsure, it is Tier 1.

## Do not re-prove the gates

The installer's gates run on the user's machine and roll back on failure. Do not
compile against hand-written stubs, do not mock the Android framework, do not
run the installer against synthetic repositories to demonstrate that it works.
State plainly what was and was not validated, and let the real gates decide.

## Validation

Validate deterministic transformers/probes, fixture install, idempotence, wrong-state rejection, rollback behavior where practical, ZIP integrity, exact contents, generated hashes, Python compile, Kotlin/Android compile when Android changes, and other real builds required by changed components.

Never report a check as passed if it did not execute.

## Memory invariant

Every meaningful ZIP must include the `docs/memory` files affected by that work. Update the dated session log and any changed `CURRENT`, decision, evidence, roadmap, or handoff files. The package manifest must include:

`durable_memory_updated: true`

The memory files are part of the patch, not after-the-fact prose.
