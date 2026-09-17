# D-131 — Non-blocking TV-entry state sync

**Date:** 2026-09-17

## Purpose

Remove the measured 24-second Linux TV-state pull from the first TV-home render
critical path without changing the Linux-authoritative durable-state contract.

## Production file

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`

## Diagnostic

- `tools/probes/d131_tv_entry_nonblocking_probe.py`

## Safety / validation

The installer verifies the exact D-130 predecessor commit and clean tracked
state, backs up changed files, validates deterministic markers, compiles/runs the
probe self-test, runs the real Android debug build, `git diff --check`, memory
health, and restores exact predecessor bytes on deterministic failure.

## Installer history

- revision 01: failed **before modification** because `exact_prestate()` passed `check=False` to a `git()` wrapper that did not accept that keyword;
- revision 02: corrects the installer-only helper contract and adds a direct wrapper self-test. Production D-131 behavior is unchanged.

## Runtime acceptance

Prepare the probe, open TV once from top-level PrivyHub, then verify.

Target:

`D131_TV_ENTRY_NONBLOCKING_SYNC_VALIDATED`

<!-- PRIVYHUB_D131_RUNTIME_RESULT:BEGIN -->
## Runtime result — accepted 2026-09-17

`D131_TV_ENTRY_NONBLOCKING_SYNC_VALIDATED`

- first TV-home render: 330 ms;
- catalog: 19 ms;
- Linux TV-state sync: 24,050 ms;
- sync complete: 24,754 ms;
- reconciliation complete: 25,073 ms;
- action: `pulled`;
- local state changed: true;
- UI ready before state sync completed: true.

User reports the visible load is now roughly one or two seconds and other Live TV
behavior appears normal.

**Status: runtime accepted.**
<!-- PRIVYHUB_D131_RUNTIME_RESULT:END -->
