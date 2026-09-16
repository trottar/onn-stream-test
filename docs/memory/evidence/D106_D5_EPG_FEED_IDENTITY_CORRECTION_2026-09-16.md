# D-106 — D5 EPG feed-identity correction — 2026-09-16

**Status:** diagnostic correction / D-107 evidence next

## D-106 raw result

D-106 successfully measured the onn provider/identity distribution:

- 3,356 stream rows;
- 3,286 unique nonblank IDs;
- 3,169 meaningful IDs;
- 117 synthetic `tv_stream_*` IDs;
- built-in `iptv_org`: 3,017 meaningful unique IDs and 2,973 overlaps with the
  current English playlist;
- `free_tv`: 153 meaningful unique IDs;
- `freecasthub`: 1 meaningful unique ID and 107 synthetic IDs.

Those raw measurements remain valid.

## Classification correction

D-106 classified the built-in guide metadata as sparse because it compared
playlist `tvg-id` values directly with the guide API's bare `channel` field.

Current IPTV-org contracts show that this comparison is incomplete:

- playlist stream IDs may be `<channel_id>` or `<channel_id>@<feed_id>`;
- API stream records expose `channel` and `feed` separately;
- API guide records expose `channel` and `feed` separately.

Therefore a playlist ID such as `BBCOne.uk@EastMidlandsHD` must be compared with
the guide pair:

- `channel = BBCOne.uk`
- `feed = EastMidlandsHD`

using canonical identity `BBCOne.uk@EastMidlandsHD`.

The D-106 classification
`D106_BUILTIN_GUIDE_METADATA_COVERAGE_SPARSE`
is superseded and must not drive architecture decisions.

## Still-valid evidence

The current public hosted-source limitation remains valid: current IPTV-org
public guide workers expose source-backed data for only two channels.

D-107 recomputes metadata coverage with feed-aware canonical identities before
any production EPG change.
