# D-106 — D5 EPG provider / identity diagnostic

**Status:** diagnostic-only / runtime evidence next

## Question

Is D-105's low 89/3,286 guide-metadata overlap caused by:

1. genuinely sparse guide metadata for the built-in IPTV-org English playlist;
2. synthetic `tv_stream_*` identities inflating the catalog denominator; or
3. provider identity dilution from managed/custom playlists?

## Important source behavior

`TvRepository.parsePlaylist()` stores `tvg-id` as `channel_id`. When `tvg-id`
is blank, it falls back to the generated stable stream ID.

Elsewhere, `meaningfulChannelId()` explicitly excludes IDs beginning with
`tv_stream_`, so nonblank IDs are not equivalent to EPG-matchable identities.

Managed providers also attempt to resolve their identity back to the built-in
IPTV-org catalog before storage.

## Probe

`tools/probes/d106_epg_provider_identity_probe.py`

It measures:

- current IPTV-org English playlist `tvg-id` completeness;
- guide metadata coverage of that built-in playlist independent of onn state;
- onn unique meaningful versus synthetic channel IDs;
- provider-by-provider meaningful/synthetic identity counts;
- provider-by-provider exact guide metadata coverage;
- provider overlap with the current built-in English playlist.

No production state is modified.

## Decision boundary

If the built-in English playlist itself has sparse guide metadata coverage,
upstream metadata is the dominant limitation.

If built-in coverage is materially higher than merged-catalog coverage, inspect
provider identity reconciliation next.

If synthetic identities dominate the denominator, correct diagnostics/modeling
before making EPG architecture decisions.
