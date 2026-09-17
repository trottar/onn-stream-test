# D-125 — EPG non-blocking background warmer

**Status:** production patch / runtime validation required

## Evidence

D-124 measured cached guide reads at roughly 1–2 ms and one uncached guide
acquisition at 19.08 seconds.

Representative SQLite work was below 1 ms.

## Narrow change

Normal `GET /plugins/epg/guide` must not synchronously execute the upstream grab
path on a cache miss or stale cache.

D-125:

1. preserves fresh-cache immediate reads;
2. returns stale cache immediately when available;
3. queues missing/stale refresh work to one deduplicated background worker;
4. returns an immediate empty/pending response for an uncached normal read;
5. keeps explicit forced refresh synchronous for diagnostics/manual refresh;
6. adds bounded POST `prefetch` support for later Android page-level warming;
7. exposes background queue state in EPG status;
8. shuts the queue down without blocking companion teardown.

No playback, TV-state, VOD, or Android production change.

## Scope boundary

D-125 intentionally does not yet add:

- Favorites/page prefetch calls from Android;
- persistent incorrect-guide user intent;
- the paged guide-style category UI.

Those remain immediate follow-up work after the non-blocking Linux seam passes.
