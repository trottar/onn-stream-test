# D-129 — Single-column TV guide

**Date:** 2026-09-17

**Status:** runtime accepted

## Hypothesis

The D-128 failure was architectural, not a missing-text bug: TV result pages were
still rendered through the generic three-column source grid. Changing the TV
result rendering seam to one column, plus loading already-warmed companion guide
data into the Android cache before render, produced the requested guide without
disturbing acquisition or playback.

## Production change

### MainActivity.kt

- detects TV result pages from `tvResultPages`;
- sets `sourceGrid.columnCount = 1` only for those pages and restores 3 elsewhere;
- expands TV result controls to the full grid width;
- identifies guide rows to the diagnostic probe via a non-sensitive content
  description;
- presents channel/current/next programme data as one vertical row;
- explicitly displays guide-unavailable and guide-marked-incorrect states;
- prefetches then hydrates companion guide cache before first result render.

### TvEpgRepository.kt

Adds bounded `hydrateCompanionGuides()` which calls only the existing companion
`/plugins/epg/guide` seam. It stores returned programmes in the Android EPG cache
but never invokes the legacy direct-upstream fallback.

## Boundaries

Unchanged: Linux D-125 warmer, D-126 prefetch contract, D-127 trust state,
TV-state authority, playback, Favorites/Hide semantics, VOD, Games,
video/audio/controllers.

## Runtime acceptance

Classification:

`D129_SINGLE_COLUMN_TV_GUIDE_RUNTIME_VALIDATED`

Measured visible Favorites state:

- guide rows: 4;
- full-width rows: 4;
- one-column: true;
- rows with current programme: 3;
- explicit guide-unavailable rows: 1;
- visible marked-incorrect rows: 0.

Canonical evidence:
`docs/memory/evidence/D129_SINGLE_COLUMN_TV_GUIDE_RUNTIME_ACCEPTANCE_2026-09-17.md`.
