# D-113 — D5 stream identity audit result — 2026-09-16

**Status:** runtime validated diagnostic result

Classification:

`D113_CONFIRMED_UPSTREAM_STREAM_IDENTITY_CONTRADICTION`

## Current upstream/API measurements

- IPTV-org `feeds.json`: 44,704 rows;
- IPTV-org `streams.json`: 17,181 rows;
- onn built-in IPTV-org streams: 3,071;
- feed-bearing built-in rows: 3,070;
- rows whose feed exists in official feed metadata: 3,070;
- rows whose current stream URL exactly matches the official API: 3,013;
- feed-name contradiction heuristic hits: 9.

The heuristic hit rate is approximately 0.29% of the built-in stream rows.

## Confirmed 10 Bold defect

Current onn/upstream row:

- display name: `10 Bold Adelaide (1080p)`;
- canonical identity: `10Bold.au@Sydney`;
- assigned feed: `Sydney`;
- display name explicitly names a different known feed: `Adelaide`;
- current official API reports the same contradictory canonical ID/title pair;
- the URL hash matches the previously identified upstream bad source;
- the Linux EPG cache correctly contains a Sydney 10 Bold guide.

User-observed video content was a children's channel rather than 10 Bold.
Existing upstream issue evidence reports the same URL as Rocky Mountain PBS Kids.

Therefore the guide mismatch is explained by bad stream identity, not by an EPG
transport/cache failure.

## Scope of the heuristic

The remaining eight heuristic hits are not all reliable proof of wrong content.
Several are ambiguous token/name cases such as:

- `East` / `West` / `Central`;
- regional BBC names whose assigned feed adds an HD suffix or a broader regional
  label.

Therefore the raw D-113 heuristic is not sufficiently precise to drive generic
automatic hiding, playback failure, or EPG suppression.

## Disposition

- preserve D-111/D-112 EPG acquisition/cache/UI acceptance;
- keep transport health separate from semantic channel identity;
- do not add a generic automatic `identity_suspect` rule from D-113 alone;
- do not hardcode the current 10 Bold URL into production architecture;
- use the existing user `Hide` action for confirmed bad sources when desired;
- treat `manual_hidden` as durable user intent in D5.4 state synchronization;
- revisit automated semantic-identity confidence only with stronger,
  representative evidence.

D-113 is closed at its current scope.
