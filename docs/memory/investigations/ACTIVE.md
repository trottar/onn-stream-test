---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Active Investigations

## A9 emulator-focused regression/checkpoint

Status: ACTIVE.

All A1-A8 work plus the four-player extension and representative Crash Bash 4P gameplay are runtime validated. Run one final regression across NES, SNES, Genesis, and an ordinary non-Crash-Bash PS1 title; recheck 2P/analog, direct launch, pause/resume, frozen preview, Save/Load, End, host coexistence, one cheat session, one mod session, one custom A8 input profile, and repository diff hygiene.

If the A9 runtime probe passes, inspect the repository audit it records, update final durable evidence, and create/push the clean Phase A checkpoint.

The earlier controller dropout is not active software work. It persisted once with multitap removed and did not reproduce with a replacement controller. Reopen only if representative controllers reproduce the failure.

## PS1 multitap library generalization

Status: ACTIVE. Crash Bash Port-1 multitap is validated; CTR demonstrates that one hard-coded game override is insufficient for a larger library. Target: per-game On/Off selector, Port 1 only, Port 2 always disabled, advisory checker from existing `max_players` metadata, no automatic activation. Exact source/candidate audit precedes production change.

## A9 NES/Genesis fresh-log identification

Status: ACTIVE but secondary. First A9 run marked NES and Genesis `<unknown>` despite user-confirmed normal direct launch/gameplay/analog/coexistence/End. Treat as probe-detection issue unless runtime evidence contradicts it. Fix/re-run after the PS1 multitap product gap is closed.

## Active: PS1 library-wide multitap usability

Current metadata cannot identify known four-player PS1 titles, so the checker is deferred. Production work is limited to a manual On/Off flag with Port 1 only. CTR is the next representative runtime validation. A9 remains pending after this product gap and the separate NES/Genesis probe-identification misses.

## Active: persistent wireless ADB target disappearance

Observed 2026-09-10 while installing the PS1 Multitap On/Off Android build: `build_install_onn.ps1` built the APK but failed at `[2/4]` because `adb devices` contained no online physical target. This failure has occurred before. Narrow hypothesis: the build tool lacks recovery for a previously paired Android TV whose `_adb-tls-connect._tcp` service is discoverable but not yet attached to the ADB server. Diagnostic-only audit captures exact local build-script hash/context, ADB version/server mDNS state, service-type counts, and device-state counts with all serials/endpoints redacted.

## ADB recovery audit v1 probe defect

The v1 diagnostic did not answer the wireless-ADB question because it failed
while locating ADB. Root cause is internal to the probe's double-escaped
`sdk.dir` regex. Corrected audit v2 is required before changing
`build_install_onn.ps1`. Persistent tooling hypothesis remains unchanged:
the build script currently lacks bounded mDNS/reconnect recovery when the ONN
transport drops from `adb devices`.

## Wireless ADB recovery — production patch active

The server-restart comparison still showed no mDNS TLS service and no transport.
Persistent recovery is therefore implemented in the build/install tool rather
than left as a manual setup step. Runtime validation of the patched script is
the active gate.

## Wireless ADB recovery investigation — CLOSED

Post-patch runtime classification `ADB_TARGET_ALREADY_ONLINE` with one online
transport and recovered mDNS service. The build/install recovery path is
validated. Reopen only on a new failure of the patched recovery logic.

## PS1 multitap library generalization — CLOSED

CTR runtime validation passed with manual Multitap On. Port 1 enabled, Port 2
disabled, all four controllers independent. Manual On/Off is sufficient for the
current four-player product ceiling. Metadata recommendation remains deferred
until metadata quality improves.

## A9 NES/Genesis fresh-log identification — ACTIVE / final Phase A gate

First A9 run already passed all other substantive stages. Fix only the
identification logic: when live status lacks usable game id/system/title, locate
the newest fresh RetroArch log whose `System:` line matches the expected family,
parse Game ID/Title/System from that log, and apply the existing XInput/fallback
checks. Rerun NES and Genesis only via finish mode.

## A9 NES/Genesis identity investigation — CLOSED AS INVALID TEST SETUP

The repeated `<unknown>` measurements did not come from launched NES/Genesis
sessions. The user clarified no games for those systems are currently installed
and the prompts were answered without launches. Therefore the prior identity
investigation was based on an invalid test setup, not a production failure.

Replacement: coverage-aware A9 finalizer. Zero library entries are skipped and
not claimed runtime validated.

## Phase A A9 — CLOSED / CHECKPOINT READY

Coverage-aware A9 returned
`PHASE_A_A9_CHECKPOINT_READY_WITH_NO_FIXTURE_SKIPS`.
All available-library regression requirements passed. NES and Genesis have no
local fixtures and remain declared unvalidated runtime coverage gaps.

No active emulator investigation remains for the Phase A checkpoint.
