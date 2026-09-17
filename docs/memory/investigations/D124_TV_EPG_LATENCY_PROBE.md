# D-124 — TV/EPG latency probe

**Status:** diagnostic-only / runtime evidence pending

## Hypothesis

The observed Live TV / guide slowness is caused primarily by EPG acquisition or
cache-miss behavior rather than the already-stable TV-state synchronization
path.

D-124 measures this before any guide UI or loading change.

## Probe boundary

No APK change.

No Android production instrumentation yet.

The probe reuses the accepted D-116 ADB snapshot mechanism and reads:

- `privyhub_tv.db`;
- `privyhub_epg.db`.

It also times normal, non-forced Linux companion EPG requests for at most three
representative channels.

## Raw measurements

The probe records:

- companion `/status` latency;
- companion `/plugins/epg/status` latency;
- ADB TV/EPG DB snapshot duration;
- visible/favorite stream counts;
- fallback `guide_mappings` count;
- total programme rows;
- distinct channels with programme rows;
- channels with active/current-future programme rows;
- favorite-channel programme-cache coverage;
- representative deduplicated Favorites count/page SQLite query timings;
- representative cached EPG query timing;
- up to three normal companion guide-request timings;
- guide response cached/stale/programme-count fields when present.

## Important limitation

SQLite queries are executed against read-only onn snapshots on Linux.

Those timings can expose expensive query shapes or cache-coverage problems, but
they are not Android CPU/view-render measurements.

If DB/API stages are fast while user-visible loading remains slow, the correct
next diagnostic is targeted Android-side instrumentation around category
construction, guide loading, persistence, and render callbacks.

## Classification

Possible primary classifications:

- `D124_COMPANION_GUIDE_FETCH_LATENCY_OBSERVED`;
- `D124_ANDROID_EPG_CACHE_COVERAGE_GAP`;
- `D124_REPRESENTATIVE_SQLITE_QUERY_EXPENSIVE`;
- `D124_EXTERNAL_TIMING_DOES_NOT_EXPLAIN_UI_LATENCY`.

Do not make a production optimization until the runtime report is inspected.
