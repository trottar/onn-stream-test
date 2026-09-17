# D-125 — EPG non-blocking background warmer

**Date:** 2026-09-17

**Type:** Linux companion production performance fix

## Production file

- `companion/plugins/epg.py`

## Behavior

Normal guide cache misses/stale reads no longer run `npm run grab` on the HTTP
request thread.

They enqueue one deduplicated background refresh and return immediately.

Fresh cached guide behavior is unchanged.

Explicit forced refresh remains synchronous.

A bounded POST `prefetch` action is added for subsequent Android page-level
warming.

## Runtime validation

Probe:

`tools/probes/d125_epg_background_warmer_probe.py`

Target:

`D125_NONBLOCKING_GUIDE_MISS_AND_BACKGROUND_WARMER_VALIDATED`

No APK build/install is required for D-125.
