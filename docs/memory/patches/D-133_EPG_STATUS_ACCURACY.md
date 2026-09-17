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
