# D-107 — D5 EPG feed-aware identity diagnostic

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
