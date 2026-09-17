# D-111 — D5 Android companion EPG integration

**Date:** 2026-09-16

**Type:** Android production integration / runtime validation required

## Purpose

Connect the existing Android guide repository to D-110's validated Linux EPG
service while preserving onn SQLite/offline behavior.

## Production change

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/TvEpgRepository.kt`

## Diagnostic change

- `tools/probes/d111_android_companion_epg_probe.py`

## Durable memory

Records:

- D-110 Linux EPG runtime acceptance;
- companion-first Android EPG decision;
- D-111 active/runtime-pending state.

## Intentionally unchanged

- MainActivity TV UI;
- TvRepository catalog/providers;
- companion production code;
- Linux EPG service implementation;
- TV-state synchronization;
- VOD;
- Games/controllers/video/audio.

## Build gate

Installer runs:

`sh ./gradlew :app:assembleDebug --no-daemon`

and rolls back tracked source/memory changes if the build fails.
