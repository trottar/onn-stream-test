# D-130 — Top-level TV-entry latency

**Date:** 2026-09-17

**Status:** diagnostic active

## Observation

After D-129 runtime acceptance, Favorites/category result pages are responsive,
but entering TV from the top-level PrivyHub screen still leaves
`Loading TV catalog...` visible for several seconds.

## Source boundary

Current `openTvHome()` waits for all of the following before rendering TV home:

1. `TvRepository.ensureCatalog()`;
2. `synchronizeTvStateNow()`;
3. if sync reports `localStateChanged`, a second `ensureCatalog()`;
4. `buildTvHomeNode()` + `renderCurrentPage()`.

Favorites guide prefetch happens after that render and therefore is not part of
the observed loading message interval.

The initialized TV-state sync path currently calls `applyEnvelope()` on every
entry and reports `localStateChanged = true`. That may make the second catalog
pass routine even when the Linux revision did not change, but this remains a
hypothesis until measured.

## Diagnostic

Add low-overhead `Log.i` stage markers with one monotonic session ID and raw
elapsed milliseconds. Probe clears logcat before the run and parses the latest
complete session after one top-level TV entry.

No production behavior, timeout, authority, cache, playback, or EPG policy is
changed by D-130.
