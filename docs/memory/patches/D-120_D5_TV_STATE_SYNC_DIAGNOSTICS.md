# D-120 — D5.4 TV-state sync diagnostics

**Date:** 2026-09-17

**Type:** Android production observability polish

## Production files

Changed:

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/TvStateSyncClient.kt`
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`

## Behavior

Adds persisted last-success and last-conflict metadata for the existing
TV-state synchronization contract.

Adds TV-state revision / last-sync / last-conflict information to:

TV Settings -> Catalog / EPG Status

No sync policy, merge semantics, Linux service, EPG, catalog, or playback logic
changes.

## Validation

Installer gates on exact D-119 predecessor state, compiles the probe, runs probe
self-test, runs `git diff --check`, builds `:app:assembleDebug`, verifies the
APK, and rolls back exact tracked predecessor bytes on deterministic failure.

Runtime validation is read-only after the new APK is installed.
