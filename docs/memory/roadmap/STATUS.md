---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Authoritative Roadmap Status — 2026-09-10

## Phase A — Emulator Completion

- A1 Controller/analog: COMPLETE / runtime validated.
- A2 Save/Load: COMPLETE / runtime validated.
- A3 Pause/Resume: COMPLETE / runtime validated.
- A4 Host coexistence/audio lifecycle: COMPLETE / runtime validated.
- A5 Direct launch UX: COMPLETE / runtime validated.
- A6 Organization/metadata/art: COMPLETE / runtime validated.
- A7 Cheats/mods: COMPLETE / runtime validated.
- A8 Input mapping/profiles: COMPLETE / runtime validated for original P1/P2 scope.
- Four-player controller extension: **CURRENT** — transport/ViGEm, real Android P1-P4 assignment, RetroArch ports 1-4, and A8 P1-P4 profile/editor/session mapping are runtime validated. Gameplay regression is active: 1P and 2P are complete; representative real 4P gameplay is next.
- A9 Full emulator regression/checkpoint: PENDING after four-player acceptance.

## Phase B — Clean Baseline

Not started. Remove Sunshine/Moonlight comprehensively, prove native Games independently, checkpoint.

## Phase C — Streaming Architecture

Not started. Make quality profiles explicit, test 1080p60, generalize proven native streaming to other live/application sources.

## Phase D — Resource Testing / Linux

Not started formally. Establish representative workloads, benchmark the Windows reference, test inexpensive Linux-capable tiers, develop capability scaling, and replay the saved UDP acceptance suite.

## Immediate sequence

`25e9a14 -> [DONE] four-player base slots -> [DONE] real Android P1-P4 assignment -> [DONE] RetroArch ports 1-4 -> [DONE] A8 P3/P4 profile/editor -> [DONE] 1P regression -> [DONE] 2P regression -> representative 4P gameplay -> A9 full emulator regression/checkpoint -> close Phase A -> Phase B`.

This file supersedes stale status in older top-level roadmap documents until they are intentionally reconciled.

## 2026-09-10 four-player gameplay boundary

Four-player host routing is runtime validated in Crash Bash. Gameplay exposure is blocked at the PS1 multitap/core-options layer; core-options/storage audit is active. A9 remains next after the representative 4P gameplay gate passes.

## PS1 4P blocker refinement

The four-player blocker is now narrowed to Beetle PSX HW session topology. Core-option storage is known and multitap is explicitly disabled. Source-context audit is next; A9 remains pending behind representative 4P gameplay.

## 2026-09-10 four-player closure update

1P and 2P post-extension regressions are complete. Four real host routes and RetroArch ports 1-4 are complete. The remaining representative 4P blocker is the PS1 emulated accessory topology; exact audit found Beetle multitap disabled. A game-specific Port-1 multitap development patch is next for runtime validation. A9 begins immediately after representative 4P gameplay passes.

## Immediate rollback gate

Before continuing representative 4P gameplay or A9, complete the exact rollback comparison for the first PS1 multitap patch. After rollback: restart companion, launch a normal game with four charged controllers, rerun the four-controller Android assignment probe, and inspect whether P1-P4 again map cleanly to slots 1-4. A revised multitap implementation is blocked on that result.

## Immediate sequence after rollback comparison

Re-enable Crash Bash game-specific Port-1 multitap -> substitute a different physical controller -> rerun real Android four-controller assignment during an active game session -> if assignment passes, rerun representative Crash Bash 4P gameplay -> A9. If assignment still fails specifically at the fourth physical device, instrument the Android InputDevice/session boundary before changing emulator code.

## Phase A final gate — A9 ACTIVE

Four-player extension is COMPLETE/runtime validated, including game-specific PS1 multitap and representative Crash Bash four-player gameplay. A9 is now the only Phase A gate: full emulator regression across NES/SNES/Genesis/ordinary PS1, lifecycle and 2P/analog checks, cheat/mod/input-profile continuity, repository audit, then clean checkpoint commit/push.

## A9 reopened product gate: general PS1 4-player flag

First A9 runtime pass exposed CTR P3/P4 greyed because multitap was configured only for Crash Bash. Before Phase A closure, generalize PS1 multitap into a per-game On/Off setting (Port 1 only, max four players) with advisory metadata recommendations. Then rerun targeted CTR/ordinary-PS1 checks and correct the NES/Genesis A9 log-identification misses before the final A9 checkpoint.

## Remaining Phase A PS1 topology gate

Implement and runtime-validate the manual PS1 Multitap On/Off flag. CTR is the second representative title after Crash Bash. When CTR P3/P4 exposure and independent P1-P4 control pass, return to A9 and correct/re-run the separate NES/Genesis log-identification checks before the Phase A checkpoint.

## Tooling blocker before CTR runtime validation

CTR Multitap On/Off runtime validation is temporarily blocked by persistent wireless ADB reconnection failure in the Android build/install helper. Resolve the build-tool recovery path first; do not change emulator/controller production logic for this failure.

## ADB tooling blocker update

The first recovery audit was invalid due to its own `sdk.dir` parser defect.
Corrected audit v2 is the immediate diagnostic gate. Do not alter the
multitap/Phase-A production path until the ADB recovery state is measured.

## Tooling blocker: wireless ADB recovery

Runtime-validate the hardened build/install script, then continue the installed
PS1 Multitap On/Off CTR test. Phase A remains open until CTR validation and the
corrected A9 NES/Genesis checks pass.

## ADB tooling status

Persistent wireless ADB recovery: **COMPLETE / runtime validated**.
Next active Phase A gate: PS1 Multitap On/Off CTR runtime validation, followed
by correction/rerun of A9 NES/Genesis probe identification and Phase A checkpoint.

## PS1 Multitap On/Off status

**COMPLETE / runtime validated.** Crash Bash and CTR both demonstrate Port-1
four-player exposure with Port 2 disabled and independent P1-P4 control.

## Phase A final gate

Only A9 NES/Genesis machine-identification closure remains. All other first-run
A9 stages passed. Use corrected A9 finish mode to rerun NES and Genesis plus a
fresh repository audit. A confirmed finish result advances directly to the
Phase A checkpoint commit/push.

## A9 coverage semantics

Phase A checkpointing may proceed with an explicit no-fixture skip for emulator
families that have zero current library entries. Such families are **not**
runtime validated and must be exercised when content is later added.

Current runtime coverage is strong for SNES and PS1. NES and Genesis are
configured/supported paths but have no current local runtime fixture.

## Phase A — Emulator Completion

**Status: COMPLETE / checkpoint ready (2026-09-10).**

Runtime-validated available-library scope includes SNES and extensive PS1
coverage, including four-controller routing and manual Port-1-only multitap on
Crash Bash and CTR. A9 available-library regression completed successfully.

Declared coverage gaps:
- NES: supported/configured, zero current local fixture, not runtime validated;
- Genesis: supported/configured, zero current local fixture, not runtime
  validated.

These gaps do not block the Phase A checkpoint and should be closed when actual
content is later added.

Next: complete final repository commit/push, then advance to the next roadmap
phase. Do not continue emulator feature development absent a new requirement or
regression.
