# D-113 — 10 Bold upstream stream-identity evidence — 2026-09-16

**Status:** external/current evidence; catalog-wide runtime audit next

A user-visible mismatch was observed after D-111/D-112:

- PrivyHub search entry: `10 Bold Adelaide`;
- video content observed: a children's channel;
- EPG content: 10 Bold schedule, including *The Young and the Restless*.

## Current IPTV-org stream row

Current `iptv-org/iptv` source inspection at commit
`48cc00e50b4aa06ec6124c1e2b11982d0869eb1f` shows:

- `tvg-id="10Bold.au@Sydney"`;
- title `10 Bold Adelaide (1080p)`;
- the stream URL whose SHA-256 is:
  `3abb5a9b35973ed3ddf6f49b8b56e01d982deecc1d9ab380ea4ad53105de8500`.

This is internally contradictory before playback is considered:
the canonical feed ID is `Sydney` while the title says `Adelaide`.

## Upstream issue evidence

IPTV-org issue:

`https://github.com/iptv-org/iptv/issues/23224`

reports that the same stream URL actually carries **Rocky Mountain PBS Kids**
rather than 10 Bold.

The issue was closed as not planned because the submitted legacy channel ID was
invalid; that closure is not evidence that the stream content was corrected.

## Architectural meaning

The D-111 EPG path can be technically correct while still showing a schedule
that does not match video when the upstream stream itself is mislabeled.

Therefore keep these dimensions separate:

1. EPG acquisition/cache/transport correctness;
2. catalog channel/feed metadata consistency;
3. actual stream-content identity.

D-113 audits dimension 2 across the current onn built-in catalog before any
automatic suppression/identity-trust policy is added.
