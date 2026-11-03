# D-107 — D5 EPG feed-aware identity diagnostic

<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:D107_RESULT:BEGIN -->
## Result — 2026-09-16

D-107 completed successfully.

Built-in IPTV-org:
- 3,017 meaningful IDs;
- 1,218 feed-aware exact canonical guide matches;
- 40.3712% exact canonical coverage;
- 1,475 IDs with some base-channel guide metadata.

Whole onn catalog:
- 3,169 meaningful IDs;
- 1,220 exact canonical guide matches;
- 38.4979% exact canonical coverage;
- 1,564 IDs with base-channel guide metadata.

The earlier bare-channel zero-overlap result is conclusively superseded.

Public source-backed guide availability remains only 2 canonical IDs.

Decision:
move to a bounded local-acquisition viability probe rather than another Android
matching/parser patch.
<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:D107_RESULT:END -->

**Status:** diagnostic-only / runtime evidence next

## Narrow question

How much of the built-in IPTV-org English playlist and current onn catalog
matches `guides.json` when the upstream feed-aware identity contract is applied?

## Upstream identity contract

IPTV-org stream IDs may be:

- `<channel_id>`
- `<channel_id>@<feed_id>`

The API represents those components separately in stream and guide records as
`channel` and `feed`.

D-106 compared full playlist `tvg-id` values against only guide `channel`, which
made its built-in zero-overlap classification invalid.

## Probe

`tools/probes/d107_epg_feed_identity_probe.py`

The probe is read-only and measures:

- guide canonical identity `channel@feed` when feed is nonblank;
- guide bare channel identity separately;
- feed-bearing versus channel-only playlist IDs;
- D-106-style raw bare-channel overlap for comparison;
- exact feed-aware canonical overlap;
- English canonical overlap;
- base-channel presence even when exact feed differs;
- controlled blank-feed fallback candidates;
- provider-specific onn canonical coverage;
- top guide sites among exact canonical matches.

Raw measurements outrank the classifier.

## Decision boundary

If feed-aware built-in metadata coverage is substantial, investigate a
Linux-local EPG acquisition/cache path because public hosted sources remain
minimal.

If feed-aware coverage is still genuinely low, investigate alternative guide
metadata/source strategy before implementing local acquisition.

No Android production change belongs in D-107.
