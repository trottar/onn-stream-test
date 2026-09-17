# D-126 — Android EPG prefetch integration

**Status:** development patch / runtime validation required

## Purpose

Use the D-125 Linux prefetch seam from normal Android TV navigation so likely
guide data begins warming before the user explicitly opens Program Guide.

## Behavior

- entering TV queues stale/missing Favorites guide identities;
- opening any paged TV result queues stale/missing identities for the visible
  page;
- Android local guide data is checked first so fresh local guide rows are not
  needlessly submitted;
- prefetch POST timeout is bounded to two seconds and is fail-soft;
- successful prefetch calls write Android EPG diagnostic meta:
  - `companion_epg_last_prefetch_at_ms`;
  - `companion_epg_last_prefetch_requested`;
  - `companion_epg_last_prefetch_queued`.

The current category rendering remains unchanged. Existing cached `Now:` rows
continue to render through `getCachedGuide()`.

## Scope boundary

D-126 does not yet implement:

- durable `incorrect guide` user intent;
- guide correction/recheck policy;
- Program Guide/category visual redesign.

Those remain next after D-126 proves the warm-ahead request reaches Linux from
normal Android navigation.
