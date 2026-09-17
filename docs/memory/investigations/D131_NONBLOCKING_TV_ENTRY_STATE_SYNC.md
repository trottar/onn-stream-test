# D-131 — Non-blocking top-level TV-state synchronization

**Date:** 2026-09-17

**Status:** development patch / runtime validation required

## Evidence

D-130 measured `D130_TV_ENTRY_STATE_SYNC_DOMINANT`:

- total entry 24,525 ms;
- cached catalog 7 ms;
- synchronous TV-state sync 24,214 ms;
- post-sync catalog 3 ms;
- UI render 291 ms.

## Hypothesis

The Linux-authoritative sync operation is valid but is scheduled on the wrong
side of the first-render boundary. Rendering the already-valid local cache first
should remove the user-visible delay without weakening durable authority.

## Production change

`MainActivity.openTvHome()`:

1. runs the existing catalog gate;
2. renders TV home immediately;
3. starts the existing Favorites warm-ahead;
4. performs the unchanged Linux TV-state sync;
5. if the pull changes local durable state, reruns the existing catalog gate;
6. reconciles the TV home/result page afterward.

No sync schema, revision, conflict or import logic changes.

## Runtime target

`D131_TV_ENTRY_NONBLOCKING_SYNC_VALIDATED`

The probe requires a first render within 2 seconds and eventual observation of
both state-sync completion and UI reconciliation.
