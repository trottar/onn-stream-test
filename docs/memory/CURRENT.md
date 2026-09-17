---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D-132
maintenance_status: healthy
baseline_commit: 0c9d1aee1f4d9d65c2ee15729a52fbbb32861dd8
---

# Current Project State

## Active Objective

Finish the bounded D5 TV/EPG usability work without reopening validated media,
TV-state, Games, or transport subsystems.

## Current Work Item

**D-132 — Favorites EPG coverage/status classification.**

D-131 is runtime accepted with
`D131_TV_ENTRY_NONBLOCKING_SYNC_VALIDATED`. First TV-home render measured 330 ms
while the unchanged Linux-authoritative pull continued for 24,050 ms and
reconciled at 25,073 ms.

The remaining bounded TV/EPG question is guide coverage/status presentation.
D-132 is diagnostic-only: classify why visible Favorites do or do not currently
have trusted programme data before changing UI status labels or acquisition
behavior.

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

## Current Repository / Patch State

Expected D-132 predecessor checkpoint:

`0c9d1aee1f4d9d65c2ee15729a52fbbb32861dd8`

D-132 changes no Android or companion production code. It adds a diagnostic probe
that snapshots the onn TV/EPG databases and, only for visible Favorites lacking a
current Android programme, checks the existing local companion guide endpoint.

**Status: DIAGNOSTIC PATCH / RUNTIME MEASUREMENT NEXT.**

## Next Action

1. install/commit/push D-132;
2. run `tools/probes/d132_favorites_epg_coverage_probe.py --repo .`;
3. inspect `logs/tv/d132_favorites_epg_coverage_probe.txt`;
4. choose the next production change only from the measured gap classes.

## Success Criteria

- every visible Favorite is classified into a concrete guide state;
- Android current/future/stale cache state is measured directly;
- missing Android current data is compared against the existing Linux companion
  guide endpoint where the channel identity is EPG-matchable;
- marked-incorrect and synthetic/unmatchable channels are separated from ordinary
  missing guide coverage;
- no production behavior changes;
- no network address or device identifier is written to the report.

## Do Not Reopen Without New Evidence

- D5.4 TV-state seed/push/pull/conflict correctness.
- D-125 non-blocking Linux EPG request boundary.
- D-126 Favorites/visible-page prefetch seam.
- D-127 incorrect-guide durable-state contract.
- D-129 one-column guide presentation.
- D-131 non-blocking TV-entry scheduling.
- External VOD hotplug/storage architecture.
- Linux Games controller/multitap/video/audio lifecycle.
- Deferred Opal/Siflower UDP reverse-engineering branch.

## Relevant References

- `evidence/D131_NONBLOCKING_TV_ENTRY_RUNTIME_ACCEPTANCE_2026-09-17.md`
- `investigations/D132_FAVORITES_EPG_COVERAGE.md`
- `patches/D-132_FAVORITES_EPG_COVERAGE_PROBE.md`
- `architecture/TV_STATE_SYNC.md`
- `roadmap/STATUS.md`
- `2026-09-17.md`
