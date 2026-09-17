# D-112 — D5 Program Guide newline polish

**Date:** 2026-09-16

**Type:** Android presentation polish

## Purpose

Remove literal `\n` artifacts from the runtime-validated Program Guide.

## Root cause

`MainActivity.showTvProgramGuide()` currently appends:

```kotlin
append("\\n")
```

That Kotlin string contains a literal backslash followed by `n`.

The intended separator is an actual newline:

```kotlin
append("\n")
```

## Production scope

Changed:

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`

Only the programme-row separator inside Program Guide is changed.

## Intentionally unchanged

- `TvEpgRepository.kt`;
- Linux EPG plugin/toolchain/cache;
- guide identity/mapping;
- companion networking;
- TV catalog/providers;
- playback;
- TV-state synchronization;
- VOD;
- Games/controllers/video/audio.

## Validation

Installer requires the exact D-111 checkpoint and exact predecessor blobs,
backs up every changed file, runs `git diff --check`, runs the real Android
`:app:assembleDebug` build, validates the generated APK, and restores exact
pre-patch bytes if validation fails.

Runtime check is visual:
open the already-working `10 Bold` Program Guide and confirm programme rows use
real line breaks with no visible `\n` separators.
