---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 555cc4f
durable_memory_updated: true
---

# C3.L0R1 — CURRENT.md structure correction and memory-health gate

## Purpose

Correct the `docs/memory/CURRENT.md` section structure so
`tools/check_memory_health.py` passes, and make that checker an
installer-enforced validation gate so the same miss cannot recur silently.

Durable memory only. No production source change.

## Expected predecessor

`555cc4f` — the `C3.L0` commit.

## Failure this revision corrects

`C3.L0` installed successfully and pushed, then post-install
`check_memory_health.py` reported `maintenance_required` because the rewritten
`CURRENT.md` did not carry the seven exact headings the checker requires.

Accurate attribution: the 182-byte predecessor `CURRENT.md` had no `##` headings
at all and was already failing the same check at `310596dd`. `C3.L0` inherited
the failure rather than introducing it, but presented memory reconciliation as
part of its purpose and did not fix it.

Root cause: the file was rewritten without first reading the repository's own
validator. The project instruction to inspect existing tools before creating
anything new was applied to probes and diagnostics but not to validators.

Contributing cause: `MAINTENANCE.md` already listed the health check as step 9
of the maintenance procedure. It was documented and still skipped, because
nothing executed it.

## Changed scope

Replaced:

- `docs/memory/CURRENT.md` — rewritten against the required headings;
- `docs/memory/MAINTENANCE.md` — records the exact required headings and makes
  the health check an installer-enforced gate;
- `docs/memory/LEARNINGS.md` — records both lessons;
- `docs/memory/2026-09-18.md` — records the failure and correction.

Added:

- `docs/memory/patches/C3-L0R1_CURRENT_STRUCTURE_AND_HEALTH_GATE.md`.

Generated and validated:

- `docs/memory/patches/PATCH_INDEX.md`.

## Intentionally unchanged scope

- all companion and Android production source;
- all diagnostics and probes;
- `.gitignore`, including the confirmed `_patches/`/`_probes/` coverage gap;
- the Linux host-telemetry gap;
- every `C3.L0` audit conclusion, including
  `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`,
  `architecture/ADAPTIVE_BITRATE.md`, `roadmap/STATUS.md`,
  `investigations/ACTIVE.md`, `handoffs/CURRENT_HANDOFF.md`,
  `docs/KNOWN_ISSUES.md` and
  `evidence/C1_C2_LINUX_REVALIDATION_2026-09-18.md`.

## New installer behavior

Post-write validation now runs `tools/check_memory_health.py --repo <repo>` and
treats a non-zero exit as a validation failure, triggering exact-byte rollback.

A missing checker is reported as a warning rather than a failure, because an
absent tool is a different problem from a reported unhealthy state. A present
checker that reports a problem fails closed.

## Confirmed by the C3.L0 run, no action taken

`git status --short` showed `?? _patches/` and `?? _probes/`, confirming the
`.gitignore` coverage gap predicted by the `C3.L0` audit and already recorded in
`docs/KNOWN_ISSUES.md`. Both remain untracked and unpushed.

## Validation performed

- installer Python compile;
- installer self-test on a fixture reproducing the `C3.L0` installed state,
  covering correct install, wrong-state rejection before modification,
  idempotent reinstall, generated-index correctness, memory-health gate pass,
  memory-health gate failure forcing rollback, and forced-validation-failure
  rollback with exact-byte restoration;
- `CURRENT.md` heading structure asserted directly: all seven required headings
  present exactly once;
- payload SHA-256 manifest verified against installed output;
- predecessor SHA-256 verification for every replaced file;
- LF line endings and trailing newline preserved;
- `git diff --check` and ZIP integrity executed by the delivery block.

No runtime or E2E validation applies.

## Result

`INSTALLED SUCCESSFULLY` on the run recorded in `docs/memory/2026-09-18.md`.

## Next

`C3.L1` — Linux encoder-only restart continuity probe.
