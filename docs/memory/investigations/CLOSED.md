---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: db59209578fc628fc602e707f5f7cd9091949edc
---

# Closed Investigations

## A4 audio/host lifecycle

Runtime validated: TV game audio works, local duplicate audio is suppressed, controlled shutdown restores session state, and plugin shutdown reuses the normal Games stop path. Do not reopen absent regression evidence.

## A8 mapping assignment boundary

Resolved: physical controller semantics remain canonical through PHI1/ViGEm; A8 session mapping applies later in RetroArch bindings. Controller preflight ordering was corrected so XInput devices exist before RetroArch initializes.

## A6 artwork transient

A temporary cover-art disappearance after repeated APK reinstall activity repopulated without persistent regression. Do not touch artwork unless repeatable in normal launches.

## Cheat/mod isolation

Resolved and runtime validated: normal save/state namespaces are protected; cheat/mod profiles use isolated namespaces; deterministic IPS derived content is verified.

## Part 3 normalization — resolved work migrated from ACTIVE

The pre-Part-3 `ACTIVE.md` contained accumulated investigation chronology from
completed Phase A and Phase B work. Its exact bytes are preserved at:

`docs/memory/history/ACTIVE_INVESTIGATIONS_SUPERSEDED_THROUGH_2026-09-11.md`

The following work is closed and must not be treated as active unless fresh
contradictory evidence appears:

- Phase A A9 regression/checkpoint;
- PS1 library-wide manual Port-1-only Multitap On/Off generalization and CTR
  validation;
- NES/Genesis A9 identity issue, closed as invalid no-fixture test setup;
- persistent wireless ADB recovery and post-patch validation;
- Phase B B1.1-B1.13 diagnostics/health/client-feedback/classifier/GUI/retention
  work;
- B1/B2 completion-gap and source-context audits;
- B2 Diagnostics action-feedback polish;
- B3/B3.1 Sunshine/Moonlight dependency inventory and active-edge trace;
- B4.1-B4.8 server/Android legacy-edge removal, orphan audit, code cleanup,
  physical artifact cleanup, device package verification/removal and final
  package-state verification;
- B5 native-only regression and classifier correction;
- B6 clean-native repository audit/checkpoint;
- C1.1 explicit stream-parameter inventory.

C1.1 completed with `C1_INVENTORY_COMPLETE`. The next technical work is schema
design, not another inventory run.

Historical intermediate states, including development-patch/runtime-pending
labels that were true at the time, remain reference history only.
