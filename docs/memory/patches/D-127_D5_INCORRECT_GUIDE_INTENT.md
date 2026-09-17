# D-127 — Durable incorrect-guide intent and deferred recheck

**Date:** 2026-09-17

**Type:** Android + Linux TV-state production change

**Status:** development patch / runtime validation pending

## Purpose

Add an explicit user action for distrusting bad guide data without changing
channel visibility or playback.

## Production files

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/TvDatabase.kt`
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/TvRepository.kt`
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/TvEpgRepository.kt`
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/TvStateSyncClient.kt`
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`
- `companion/plugins/tv_state.py`

## Behavior

- durable incorrect-guide intent is distinct from Hide;
- TV user-state moves to v2 with v1 import/migration support;
- rejected guide source is fingerprinted;
- marked channels remain visible/playable;
- guide presentation is suppressed while marked;
- marked channels become eligible for bounded background recheck after 24 hours;
- background recheck never clears intent;
- explicit Retry/Accept/Clear controls trust restoration; Retry itself never
  silently clears the mark.

## Validation gate

Installer:

- verifies exact predecessor HEAD and blob hashes;
- backs up changed files;
- applies deterministic transformations;
- compiles changed Python;
- runs the platform-appropriate Gradle wrapper for `:app:assembleDebug`;
- runs `git diff --check`;
- runs memory health validation;
- restores exact predecessor bytes on validation failure.

Runtime acceptance remains separate.
