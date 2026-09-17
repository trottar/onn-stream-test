# D-126 — Android EPG prefetch integration

**Status:** COMPLETE / RUNTIME VALIDATED

## Purpose

Use the D-125 Linux prefetch seam from normal Android TV navigation so likely
guide data begins warming before the user explicitly opens Program Guide.

## Runtime acceptance — 2026-09-17

Classification:

`D126_ANDROID_TV_ENTRY_AND_PAGE_PREFETCH_VALIDATED`

Measured Android EPG prefetch metadata:

- baseline timestamp: 0;
- newer prefetch observed: true;
- requested: 21;
- queued: 21;
- requested-positive: true;
- queued-positive: true.

User observation during the same run:

- entering TV still showed `Loading TV catalog...` for a few seconds;
- Favorites loaded immediately.

Interpretation:

The Android -> Linux prefetch integration is functioning. The top-level TV-entry
delay is a separate catalog/state-entry path and is not evidence that the D-125
EPG cache-miss fix failed.

## Accepted behavior

- TV entry queues stale/missing Favorites guide identities.
- Paged TV results queue stale/missing visible identities.
- Fresh Android guide data is filtered before submission.
- Prefetch is bounded/fail-soft.
- Successful calls record EPG diagnostic meta.

## Closed scope

D-126 does not implement incorrect-guide durable intent or the guide-style UI.
Those remain subsequent work.
