# D-116 — D5.4 Android TV-state synchronization

**Date:** 2026-09-17

**Type:** Android production integration

## Production files

Changed:

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/TvRepository.kt`
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`

Added:

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/TvStateSyncClient.kt`

## Behavior

- first TV entry seeds an uninitialized Linux authority;
- later TV entry pulls initialized Linux durable state;
- durable onn mutations push revisioned state;
- language/country participate in sync;
- runtime health/recency remains local;
- companion failure does not block local TV use;
- revision conflicts fail closed.

## Validation gates

Installer verifies exact D-115 predecessor state, backs up changed files,
compiles the runtime probe, runs probe self-test, runs `git diff --check`, runs
the real Android `:app:assembleDebug`, verifies the APK, and restores exact
pre-patch bytes if validation fails.

Runtime test is performed after APK installation.
