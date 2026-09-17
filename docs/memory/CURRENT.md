---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D-128
maintenance_status: healthy
baseline_commit: 020d86a0c0792653e2ce4d976244098981419648
---

# Current Project State

## Active Objective

Finish the bounded D5 TV/EPG usability work without reopening validated media,
TV-state, Games, or transport subsystems.

## Current Work Item

**D-128 — guide-style paged Favorites/category presentation.**

D-127 is runtime accepted. D-128 is an Android presentation-only development
patch that turns existing paged TV rows into compact guide rows using already
cached guide data.

## Verified State

- D5 external/removable VOD: **COMPLETE / runtime validated**.
- D5 Live TV catalog/categories/playback: **runtime validated**.
- Linux EPG acquisition plus Android EPG consumption/cache: **runtime validated**.
- D5.4 Linux-authoritative durable TV-state sync: **COMPLETE / runtime validated**.
- D-125 non-blocking EPG miss handling: **runtime validated**.
- D-126 Favorites/visible-page prefetch: **runtime validated**.
- D-127 incorrect-guide durable intent: **runtime validated** with
  `D127_INCORRECT_GUIDE_DURABILITY_CONFIRMED`.

## Current Repository / Patch State

Expected D-128 predecessor checkpoint:

`020d86a0c0792653e2ce4d976244098981419648`

D-128 rev1 failed the Kotlin compile gate because it duplicated the existing `formatTvGuideTime(Long)` member and was fully rolled back. Rev2 corrected that transform, but its delivery wrapper used persistent `set -euo pipefail` plus `exit 1`; on failure it terminated the interactive Bash session before installation completed, so the D-128 probe was never installed. Rev3 passed the Android build but its generated `CURRENT.md` omitted two headings required by `tools/check_memory_health.py`; the memory-health gate therefore failed and the installer rolled back. Rev4 keeps the corrected Android transform, shell-safe delivery pattern, and exact memory-health heading contract.

D-128 production scope is only `MainActivity.kt`. It reads the existing cached
`TvGuideSummary` already populated/warmed by D-125/D-126 and displays current and
next programme time ranges in shared TV rows. D-127 marked-incorrect channels
continue to suppress trusted guide presentation.

**Status: DEVELOPMENT PATCH / RUNTIME VALIDATION NEXT.**

## Next Action

After APK installation:

1. run the D-128 probe with `--prepare`;
2. open TV and then Favorites on the onn;
3. confirm visible guide-backed rows show current and next programme time ranges;
4. run the probe with `--verify` and inspect
   `logs/tv/d128_guide_style_ui_probe.txt`.

Target:

`D128_GUIDE_STYLE_FAVORITES_RUNTIME_VALIDATED`

## Success Criteria

- Favorites/category pages remain paged and navigable.
- Cached guide-backed rows show `Now:` with start/end time and title.
- Cached guide-backed rows show `Next:` with start/end time and title when known.
- D-127 marked-incorrect channels do not show trusted Now/Next programme data.
- Rendering performs no guide acquisition or channel-state mutation.
- D-125/D-126 prefetch, playback, Favorites, Hide and TV-state sync remain unchanged.

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

- `investigations/D128_GUIDE_STYLE_CATEGORY_PRESENTATION.md`
- `evidence/D127_INCORRECT_GUIDE_RUNTIME_ACCEPTANCE_2026-09-17.md`
- `architecture/TV_STATE_SYNC.md`
- `roadmap/STATUS.md`
- `2026-09-17.md`

## After D-128

1. correct/expand EPG coverage/status presentation;
2. focused TV/media regression;
3. checkpoint/close bounded D5 TV work.
