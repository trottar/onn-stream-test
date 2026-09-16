# D-107 — D5 EPG feed-aware identity result — 2026-09-16

**Status:** runtime-validated diagnostic result

D-107 completed successfully against the current onn TV database and current
IPTV-org guide metadata.

## Guide identity model

- guide rows: 180,681;
- unique canonical `channel[@feed]` IDs: 13,555;
- unique English canonical IDs: 6,936;
- unique bare channels: 11,723;
- guide rows with nonblank feed: 31,321;
- guide rows with blank feed: 230;
- currently hosted source-backed canonical IDs: 2.

## Built-in IPTV-org English playlist

- unique `tvg-id` values: 2,974;
- feed-bearing IDs: 2,973;
- channel-only IDs: 1;
- D-106-style bare-channel exact matches: 0;
- feed-aware exact canonical matches: 1,195;
- English exact canonical matches: 1,019;
- exact canonical coverage: 40.1816%;
- feed-bearing exact coverage: 40.1951%;
- base channel has some guide metadata: 1,450;
- blank-feed fallback candidates: 3;
- different-feed-only candidates: 252.

## Current onn catalog

- 3,169 meaningful IDs;
- 117 synthetic IDs;
- 1,220 feed-aware exact canonical guide matches;
- exact canonical coverage: 38.4979%;
- 1,564 IDs have guide metadata at the base-channel level.

Provider split:

- `iptv_org`: 3,017 meaningful IDs, 1,218 canonical matches, 40.3712%;
- `free_tv`: 153 meaningful IDs, 4 canonical matches, 2.6144%;
- `freecasthub`: 1 meaningful ID, 0 canonical matches.

Top guide sites for built-in exact canonical matches included:

- `i.mjh.nz`: 618;
- `pluto.tv`: 316;
- `plex.tv`: 283;
- `tvtv.us`: 191;
- `xumo.tv`: 147;
- `tvpassport.com`: 108.

## Classification

`D107_FEED_AWARE_CANONICAL_COVERAGE_PARTIAL`

The raw measurement is more important than the label:
guide metadata coverage is materially useful for the built-in provider, while
the public hosted-guide layer remains effectively unavailable.

Therefore the next boundary is local programme acquisition, not another Android
identity/parser change.
