---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D-133
maintenance_status: healthy
baseline_commit: 85cfc89e6327c156df4d9d6fa3bbf7f6b3ac577b
---

# Current Project State

## Active Objective

Finish the bounded D5 TV/EPG usability work without reopening validated media,
TV-state, Games, or transport subsystems.

## Current Work Item

**D-133 — accurate schedule-gap versus unavailable guide status.**

D-132 classified all 21 visible Favorites: 11 have a current programme, 5 have
future/companion schedule data but no programme covering the current moment, and
5 have no known guide coverage.

The current renderer labels every no-current-programme case as
`Guide data unavailable`, even when `Next:` data exists. D-133 corrects only that
presentation distinction.

## Verified State

- D5 external/removable VOD: **COMPLETE / runtime validated**.
- D5 Live TV catalog/categories/playback: **runtime validated**.
- Linux EPG acquisition plus Android EPG consumption/cache: **runtime validated**.
- D5.4 Linux-authoritative durable TV-state sync: **COMPLETE / runtime validated**.
- D-125 non-blocking EPG miss handling: **runtime validated**.
- D-126 Favorites/visible-page prefetch: **runtime validated**.
- D-127 incorrect-guide durable intent: **runtime validated**.
- D-128 compact tile treatment: **superseded after runtime failure**.
- D-129 single-column full-width TV guide: **runtime validated**.
- D-130 latency diagnostic: **runtime measured / closed**.
- D-131 non-blocking TV-entry state sync: **runtime validated**.
- D-132 Favorites EPG coverage diagnostic: **runtime measured / closed** with
  `D132_FAVORITES_GUIDE_GAPS_CLASSIFIED`.

## Current Repository / Patch State

Expected D-133 predecessor checkpoint:

`85cfc89e6327c156df4d9d6fa3bbf7f6b3ac577b`

D-133 production scope is one rendering branch in `MainActivity.kt`:
current -> existing `Now:`; upcoming but no current -> `No current listing`
plus existing `Next:`; no current/upcoming -> `Guide data unavailable`.

**Status: DEVELOPMENT PATCH / RUNTIME VALIDATION NEXT.**

## Next Action

1. install/build/push/APK-install D-133;
2. open TV -> Favorites at the top of the list;
3. verify a schedule-gap row shows `No current listing` plus `Next:`;
4. run `tools/probes/d133_epg_status_accuracy_probe.py --verify`.

Target: `D133_EPG_STATUS_ACCURACY_RUNTIME_VALIDATED`

## Success Criteria

- schedule-gap rows are not mislabeled as unavailable guide coverage;
- schedule-gap rows retain their existing `Next:` programme/time;
- true no-coverage rows continue to say `Guide data unavailable`;
- D-129 one-column/full-width layout remains intact;
- acquisition, mappings, TV-state, playback, Favorites and Hide semantics do not change;
- no network address or device identifier is written to the probe report.

## Do Not Reopen Without New Evidence

- D5.4 TV-state seed/push/pull/conflict correctness.
- D-125 non-blocking Linux EPG request boundary.
- D-126 Favorites/visible-page prefetch seam.
- D-127 incorrect-guide durable-state contract.
- D-129 one-column guide presentation.
- D-131 non-blocking TV-entry scheduling.
- D-132 measured coverage classes unless contradicted by new evidence.
- External VOD hotplug/storage architecture.
- Linux Games controller/multitap/video/audio lifecycle.
- Deferred Opal/Siflower UDP reverse-engineering branch.

## Relevant References

- `evidence/D132_FAVORITES_EPG_COVERAGE_RUNTIME_EVIDENCE_2026-09-17.md`
- `investigations/D132_FAVORITES_EPG_COVERAGE.md`
- `investigations/D133_EPG_STATUS_ACCURACY.md`
- `patches/D-133_EPG_STATUS_ACCURACY.md`
- `roadmap/STATUS.md`
- `2026-09-17.md`
