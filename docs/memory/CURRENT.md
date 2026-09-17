---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D-129
maintenance_status: healthy
baseline_commit: 821796701d534e5cee127f43edf85342e1f7998c
---

# Current Project State

## Active Objective

Finish the bounded D5 TV/EPG usability work without reopening validated media,
TV-state, Games, or transport subsystems.

## Current Work Item

**D-129 — true single-column TV guide result presentation.**

D-128 installed and built, but runtime validation failed with
`D128_GUIDE_STYLE_ROWS_NOT_OBSERVED`. The Favorites screen still used the generic
three-column fixed-width source-button grid, so adding Now/Next text did not
produce the requested TV-guide experience.

D-129 moves the correction to the actual rendering seam: TV result pages use a
dedicated one-column full-width row layout while non-TV pages keep the existing
three-column tile UI.

## Verified State

- D5 external/removable VOD: **COMPLETE / runtime validated**.
- D5 Live TV catalog/categories/playback: **runtime validated**.
- Linux EPG acquisition plus Android EPG consumption/cache: **runtime validated**.
- D5.4 Linux-authoritative durable TV-state sync: **COMPLETE / runtime validated**.
- D-125 non-blocking EPG miss handling: **runtime validated**.
- D-126 Favorites/visible-page prefetch: **runtime validated**.
- D-127 incorrect-guide durable intent: **runtime validated**.
- D-128 Android build/install: **development-only; runtime UI target failed**.

## Current Repository / Patch State

Expected D-129 predecessor checkpoint:

`821796701d534e5cee127f43edf85342e1f7998c`

D-129 production scope:

- `MainActivity.kt`: TV result pages switch the shared `GridLayout` to one column,
  TV channel controls expand to full-width guide rows, non-TV pages restore three
  columns, and rows explicitly show current/next guide data or an unavailable /
  incorrect-guide state;
- `TvEpgRepository.kt`: adds a bounded companion-only hydration pass so Android
  can copy already-warmed companion guide data into its local EPG cache before
  the result page is rendered. It does not invoke the legacy upstream fallback.

**Status: DEVELOPMENT PATCH / RUNTIME VALIDATION NEXT.**

## Next Action

1. install/build/push/APK-install D-129;
2. open TV -> Favorites;
3. confirm channel/program entries are one full-width vertical list, not a
   three-column tile grid;
4. run `tools/probes/d129_single_column_tv_guide_probe.py --verify` and inspect
   `logs/tv/d129_single_column_tv_guide_probe.txt`.

Target:

`D129_SINGLE_COLUMN_TV_GUIDE_RUNTIME_VALIDATED`

If the layout validates but no programme data is available, the probe reports
`D129_SINGLE_COLUMN_TV_GUIDE_LAYOUT_VALIDATED_NO_PROGRAMMES`; that is evidence for
the separate EPG coverage/status follow-up, not a reason to return to tiles.

## Success Criteria

- TV Favorites/category result pages render one full-width row per channel in a
  single vertical column.
- Guide-backed rows show current programme time/title and next programme when
  available.
- Missing guide data is represented explicitly rather than silently leaving a
  generic channel tile.
- D-127 marked-incorrect channels remain visibly marked and do not present guide
  data as trusted.
- Non-TV catalog/VOD/Games pages retain the existing three-column presentation.
- Hydration is companion-only, bounded, off the UI thread, and does not restore
  synchronous upstream EPG acquisition.
- Playback, Favorites, Hide and TV-state synchronization remain unchanged.

## Do Not Reopen Without New Evidence

- D5.4 TV-state seed/push/pull/conflict contract.
- D-125 non-blocking Linux EPG request boundary.
- D-126 Favorites/visible-page prefetch seam.
- D-127 incorrect-guide durable-state contract.
- External VOD hotplug/storage architecture.
- Linux Games controller/multitap/video/audio lifecycle.
- Deferred Opal/Siflower UDP reverse-engineering branch.
- ADB recovery unless ADB actually becomes a blocker.

## Relevant References

- `evidence/D128_GUIDE_STYLE_RUNTIME_FAILURE_2026-09-17.md`
- `investigations/D128_GUIDE_STYLE_CATEGORY_PRESENTATION.md`
- `investigations/D129_SINGLE_COLUMN_TV_GUIDE.md`
- `patches/D-129_SINGLE_COLUMN_TV_GUIDE.md`
- `roadmap/STATUS.md`
- `2026-09-17.md`

## After D-129

1. correct/expand EPG coverage/status presentation;
2. focused TV/media regression;
3. checkpoint/close bounded D5 TV work.
