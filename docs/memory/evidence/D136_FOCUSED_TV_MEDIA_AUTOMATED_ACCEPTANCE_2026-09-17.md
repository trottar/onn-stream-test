# D-136 — Focused TV/media automated regression acceptance

**Date:** 2026-09-17

Classification:

`D136_FOCUSED_TV_MEDIA_AUTOMATED_REGRESSION_VALIDATED`

Sub-gates:

- D-122: `D122_D5_TV_MEDIA_AUTOMATED_REGRESSION_BASELINE_VALIDATED`
- D-133: `D133_EPG_STATUS_ACCURACY_RUNTIME_VALIDATED`
- D-135: `D135_FAVORITES_QUEUE_CONTENTION_REMOVED`

Recent accepted performance/state values:

- Favorites total: 1,599 ms
- Favorites executor queue wait: 2 ms
- Linux TV-state sync complete: true
- Linux TV-state reconciliation complete: true
- one-column full-width guide: true
- mislabeled guide-gap rows: 0

Problems: none.

This automated acceptance does not prove visible/audio playback. The remaining
D5 gate is the established manual onn smoke: one Live TV playback, guide/Favorites
navigation, and one VOD playback.
