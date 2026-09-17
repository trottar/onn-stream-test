# D-135 — TV-state executor isolation

**Date:** 2026-09-17

## Purpose

Remove measured navigation queue contention without weakening Linux TV-state
authority or making state operations concurrent.

## Production

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`

## Behavior

A dedicated single-thread executor owns TV-state push/pull/reconciliation.
General catalog/page navigation stays on `networkExecutor`.

## Diagnostic

- `tools/probes/d135_tv_state_executor_isolation_probe.py`

The probe verifies Favorites queue wait/total load and waits for the unchanged
Linux state pull to complete and reconcile.

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
