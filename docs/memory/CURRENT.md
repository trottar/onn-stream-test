---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D-131
maintenance_status: healthy
baseline_commit: 6da5c4506128b2518370de0f46e7b719bd967850
---

# Current Project State

## Active Objective

Finish the bounded D5 TV/EPG usability work without reopening validated media,
TV-state, Games, or transport subsystems.

## Current Work Item

**D-131 — non-blocking top-level TV-state synchronization.**

D-130 measured top-level TV entry at 24,525 ms. The cached catalog check took
7 ms and UI render took 291 ms; synchronous Linux TV-state synchronization alone
took 24,214 ms and dominated the entry path.

D-131 preserves the same Linux-authoritative pull/import contract but renders the
cached TV home before the state round trip. Reconciliation happens after the
background pull completes.

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
- D-130 latency measurement: **runtime measured** with
  `D130_TV_ENTRY_STATE_SYNC_DOMINANT`.

## Current Repository / Patch State

Expected D-131 predecessor checkpoint:

`6da5c4506128b2518370de0f46e7b719bd967850`

D-131 production scope is only `MainActivity.kt`:

- local/cached `ensureCatalog()` still runs first;
- the TV home renders immediately after that local catalog gate;
- D-126 Favorites prefetch begins without waiting for TV-state sync;
- the existing `synchronizeTvStateNow()` still performs the same Linux pull/import;
- when the pull changes durable state, the post-sync catalog pass and TV UI
  reconciliation still occur;
- Linux authority, revisions, conflicts, schemas and push behavior are unchanged.

**Status: DEVELOPMENT PATCH / RUNTIME VALIDATION NEXT.**

## Next Action

1. install/build/push/APK-install D-131;
2. run the D-131 probe with `--prepare`;
3. open TV once from the top-level PrivyHub screen;
4. the TV home should appear quickly; run `--verify` and let the probe observe the
   eventual background state-sync completion;
5. inspect `logs/tv/d131_tv_entry_nonblocking_probe.txt`.

Target:

`D131_TV_ENTRY_NONBLOCKING_SYNC_VALIDATED`

## Success Criteria

- first TV-home render completes within 2,000 ms in the measured cached-catalog case;
- Linux TV-state synchronization still completes and reports its normal action;
- synchronization reconciliation completes after the first render;
- local-state changes are still imported under the existing D5.4 authority contract;
- D-129 guide UI, D-126 prefetch, playback, Favorites and Hide remain unchanged;
- no network address or device identifier is written to the probe report.

## Do Not Reopen Without New Evidence

- D5.4 TV-state seed/push/pull/conflict correctness.
- D-125 non-blocking Linux EPG request boundary.
- D-126 Favorites/visible-page prefetch seam.
- D-127 incorrect-guide durable-state contract.
- D-129 one-column guide presentation.
- External VOD hotplug/storage architecture.
- Linux Games controller/multitap/video/audio lifecycle.
- Deferred Opal/Siflower UDP reverse-engineering branch.

## Relevant References

- `evidence/D130_TV_ENTRY_LATENCY_RUNTIME_EVIDENCE_2026-09-17.md`
- `investigations/D130_TV_ENTRY_LATENCY.md`
- `investigations/D131_NONBLOCKING_TV_ENTRY_STATE_SYNC.md`
- `patches/D-131_NONBLOCKING_TV_ENTRY_STATE_SYNC.md`
- `architecture/TV_STATE_SYNC.md`
- `roadmap/STATUS.md`
- `2026-09-17.md`
