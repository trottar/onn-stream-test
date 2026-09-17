---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D-136
maintenance_status: healthy
baseline_commit: 7d2d5a17d3b568161fccb00cdaeefd22798dca5c
---

# Current Project State

## Active Objective

Finish bounded D5 TV/media regression and closeout without reopening validated
subsystems absent new evidence.

## Current Work Item

**D-136 — focused TV/media regression gate.**

D-135 is runtime accepted with
`D135_FAVORITES_QUEUE_CONTENTION_REMOVED`.

Measured D-135 result:
- Favorites total: 1,599 ms;
- executor queue wait: 2 ms;
- named stage sum: 1,595 ms;
- residual: 4 ms;
- Linux TV-state sync still completed and reconciled;
- Favorites became ready before the ~24.7-second state pull completed.

The >15-second Favorites regression is therefore resolved without weakening the
Linux-authority contract.

## Verified State

- Live TV guide UX through D-133: **runtime validated**.
- D-131 first TV render: **runtime validated**.
- D-135 executor isolation/Favorites performance: **runtime validated**.
- D-134 classifier error is superseded by raw timing evidence.

## Current Repository / Patch State

Expected D-136 predecessor:

`7d2d5a17d3b568161fccb00cdaeefd22798dca5c`

D-136 changes no production code. It reuses the established D-122 automated
TV/media regression baseline and additionally requires the accepted D-133 guide
status result and D-135 executor-isolation result.

**Status: REGRESSION GATE / AUTOMATED + SHORT MANUAL SMOKE NEXT.**

## Next Action

1. install/commit/push D-136;
2. run the D-136 automated probe;
3. if automated baseline passes, manually smoke:
   - one Live TV channel playback;
   - TV guide/Favorites navigation;
   - one VOD playback;
4. if all are clean, record D5 bounded TV/media closeout.

## Success Criteria

- D-122 automated media baseline still passes;
- D-133 one-column/status acceptance remains valid;
- D-135 Favorites queue wait/latency and state reconciliation remain valid;
- manual Live TV playback is normal;
- guide/navigation is normal;
- manual VOD playback is normal;
- no production changes are required.

## Do Not Reopen Without New Evidence

- D5.4 TV-state authority semantics.
- D-125/D-126 EPG background behavior.
- D-127 incorrect-guide state.
- D-129/D-133 guide geometry/status.
- D-131/D-135 executor scheduling.
- External VOD architecture.
- Linux Games lifecycle.
- Deferred UDP work.

## Relevant References

- `evidence/D135_TV_STATE_EXECUTOR_ISOLATION_RUNTIME_ACCEPTANCE_2026-09-17.md`
- `investigations/D136_FOCUSED_TV_MEDIA_REGRESSION.md`
- `patches/D-136_FOCUSED_TV_MEDIA_REGRESSION.md`
- `tools/probes/d122_d5_tv_media_regression_probe.py`
- `roadmap/D5_MEDIA_SERVER_SUBSTEPS.md`
- `roadmap/STATUS.md`
- `2026-09-17.md`
