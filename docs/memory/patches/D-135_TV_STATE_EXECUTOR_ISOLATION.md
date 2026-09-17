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
