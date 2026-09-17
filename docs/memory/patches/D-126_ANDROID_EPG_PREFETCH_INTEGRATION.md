# D-126 — Android EPG prefetch integration

**Date:** 2026-09-17

**Type:** Android production performance integration

## Production files

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/TvEpgRepository.kt`
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`

## Behavior

D-125 is runtime accepted.

D-126 connects normal TV navigation to its prefetch seam:

- TV home queues stale/missing Favorites;
- result pages queue stale/missing visible channels;
- prefetch is bounded/fail-soft;
- Android EPG meta records the last successful prefetch request.

## Build gate

Installer runs:

`sh ./gradlew :app:assembleDebug --no-daemon`

and restores exact predecessor bytes if the build or validation fails.

## Runtime probe

`tools/probes/d126_android_epg_prefetch_probe.py`

Target:

`D126_ANDROID_TV_ENTRY_AND_PAGE_PREFETCH_VALIDATED`
