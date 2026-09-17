---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D-130
maintenance_status: healthy
baseline_commit: bfc62a6c5b815ecbd9427af0117d5c22906e2998
---

# Current Project State

## Active Objective

Finish the bounded D5 TV/EPG usability work without reopening validated media,
TV-state, Games, or transport subsystems.

## Current Work Item

**D-130 — top-level TV-entry latency stage probe.**

D-129 is runtime accepted with
`D129_SINGLE_COLUMN_TV_GUIDE_RUNTIME_VALIDATED`: four visible TV guide rows were
full-width and one-column, three carried current-programme data, and one
explicitly reported unavailable guide data.

The remaining observed Live TV issue is the few-second `Loading TV catalog...`
entry delay. D-130 is diagnostic-only and measures the existing `openTvHome()`
sequence before any synchronization or catalog policy is changed.

## Verified State

- D5 external/removable VOD: **COMPLETE / runtime validated**.
- D5 Live TV catalog/categories/playback: **runtime validated**.
- Linux EPG acquisition plus Android EPG consumption/cache: **runtime validated**.
- D5.4 Linux-authoritative durable TV-state sync: **COMPLETE / runtime validated**.
- D-125 non-blocking EPG miss handling: **runtime validated**.
- D-126 Favorites/visible-page prefetch: **runtime validated**.
- D-127 incorrect-guide durable intent: **runtime validated**.
- D-128 compact text-on-tiles UI: **superseded after runtime failure**.
- D-129 single-column full-width TV guide: **runtime validated**.

## Current Repository / Patch State

Expected D-130 predecessor checkpoint:

`bfc62a6c5b815ecbd9427af0117d5c22906e2998`

Current top-level TV-entry sequence is:

1. `TvRepository.ensureCatalog()`;
2. synchronous `synchronizeTvStateNow()` Linux-authority request/import;
3. when sync reports local state changed, a second `ensureCatalog()`;
4. build/render the TV home page;
5. only after UI render, Favorites guide prefetch work continues.

D-130 adds timestamp-only log markers around stages 1-4 and a probe that parses
the latest complete entry session. It changes no catalog, sync, playback, EPG,
Favorites, Hide, or guide behavior.

**Status: DIAGNOSTIC PATCH / RUNTIME MEASUREMENT NEXT.**

## Next Action

1. install/build/push/APK-install D-130;
2. let the probe clear logcat with `--prepare`;
3. from the top-level PrivyHub screen, open TV once and wait for the TV home page;
4. run `tools/probes/d130_tv_entry_latency_probe.py --verify`;
5. inspect `logs/tv/d130_tv_entry_latency_probe.txt` and patch only the measured
   dominant stage.

## Success Criteria

- Probe records raw milliseconds for initial catalog check, Linux TV-state sync,
  optional post-sync catalog pass, UI render, and total entry time.
- Probe records whether the catalog was cached and whether sync reported local
  state changed.
- No network address or ADB/device identifier is written to the report.
- Diagnostic instrumentation does not change TV behavior.
- The next production fix is chosen from measured evidence rather than inference.

## Do Not Reopen Without New Evidence

- D5.4 TV-state authority/conflict correctness.
- D-125 non-blocking Linux EPG request boundary.
- D-126 Favorites/visible-page prefetch seam.
- D-127 incorrect-guide durable-state contract.
- D-129 one-column guide presentation.
- External VOD hotplug/storage architecture.
- Linux Games controller/multitap/video/audio lifecycle.
- Deferred Opal/Siflower UDP reverse-engineering branch.

## Relevant References

- `evidence/D129_SINGLE_COLUMN_TV_GUIDE_RUNTIME_ACCEPTANCE_2026-09-17.md`
- `investigations/D130_TV_ENTRY_LATENCY.md`
- `patches/D-130_TV_ENTRY_LATENCY_PROBE.md`
- `architecture/TV_STATE_SYNC.md`
- `roadmap/STATUS.md`
- `2026-09-17.md`
