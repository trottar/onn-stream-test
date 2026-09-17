# D-133 — EPG status accuracy

**Date:** 2026-09-17

Purpose: stop presenting ordinary schedule gaps as unavailable guide coverage.

Production:
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`

Diagnostic:
- `tools/probes/d133_epg_status_accuracy_probe.py`

Unchanged: EPG acquisition/mappings, D-125/D-126 background behavior, D-127
incorrect-guide state, D-129 geometry, D-131 entry scheduling, TV-state authority,
playback, Favorites, Hide, VOD, Games, audio/video/controllers.

Runtime target: `D133_EPG_STATUS_ACCURACY_RUNTIME_VALIDATED`.

<!-- PRIVYHUB_D133_RUNTIME_RESULT:BEGIN -->
## Runtime result — accepted 2026-09-17

`D133_EPG_STATUS_ACCURACY_RUNTIME_VALIDATED`

4/4 visible guide rows remained full-width; 2 had current programmes; 1 had
`No current listing` plus `Next:`; 0 had the old unavailable+next contradiction;
1 genuine unavailable row remained.

**Status: runtime accepted.**
<!-- PRIVYHUB_D133_RUNTIME_RESULT:END -->
