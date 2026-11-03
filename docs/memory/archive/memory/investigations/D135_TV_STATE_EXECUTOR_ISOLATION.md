# D-135 — TV-state executor isolation

**Date:** 2026-09-17

**Status:** development patch / runtime validation required

## Evidence

D-134 total Favorites load was 24,382 ms while all named stages summed to only
1,530 ms. The 22,852 ms residual occurs before/in between the named stages.

`MainActivity` has a single-thread `networkExecutor`. D-131 renders TV home early
but then continues the ~24-second `synchronizeTvStateNow()` on that same executor.
`openTvPage()` submits Favorites work to the same queue.

## Change

- add one dedicated single-thread `tvStateSyncExecutor`;
- route `scheduleTvStatePush()` through it;
- move D-131 background pull/import/reconciliation into it;
- keep catalog/page/navigation work on `networkExecutor`;
- preserve all existing D-131 sync/reconcile markers and authority semantics;
- add a direct Favorites executor-start/queue-wait marker.

TV-state pushes and pulls therefore remain serialized with one another, rather
than becoming concurrent.

## Runtime target

`D135_FAVORITES_QUEUE_CONTENTION_REMOVED`

<!-- PRIVYHUB_D135_RUNTIME_RESULT:BEGIN -->
## Runtime result — accepted 2026-09-17

`D135_FAVORITES_QUEUE_CONTENTION_REMOVED`

Favorites total 1,599 ms; queue wait 2 ms; named-stage sum 1,595 ms; residual
4 ms. Linux TV-state synchronization still completed (`pulled`) and reconciled,
with Favorites ready before state-sync completion.

**Status: runtime accepted.**
<!-- PRIVYHUB_D135_RUNTIME_RESULT:END -->
