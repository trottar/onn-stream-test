# D-114 — TV stream identity policy after D-113

**Date:** 2026-09-16

**Status:** accepted development policy

## Decision

Do not infer or enforce a generic semantic-identity failure state from D-113's
feed-name heuristic.

D-113 found 9 heuristic contradictions among 3,071 built-in IPTV-org stream
rows, but several are naming ambiguities rather than demonstrated wrong-content
streams.

The confirmed `10 Bold Adelaide` case is handled as a source-specific integrity
defect:

- advertised canonical ID is `10Bold.au@Sydney`;
- title says Adelaide;
- user-observed video is not 10 Bold;
- upstream evidence reports the URL as another channel.

PrivyHub will not rewrite that stream to Sydney or Adelaide, because neither
would describe the observed content.

## Operational policy

For a source the user confirms is semantically wrong:

- use the existing manual `Hide` action when desired;
- do not record a playback/transport failure merely because content identity is
  wrong;
- do not trust EPG semantic correctness for that stream solely because its
  canonical ID has a valid guide;
- do not hardcode third-party URL deny lists into the product architecture from
  one current upstream defect.

## Architecture rule

Keep these dimensions independent:

1. stream transport/playback health;
2. catalog/feed metadata consistency;
3. semantic content identity confidence;
4. EPG acquisition/cache correctness.

An automated `identity_suspect` layer remains a possible later TV-quality
feature, but requires higher-confidence evidence than simple display-name/feed
token disagreement.

## D5.4 consequence

`manual_hidden` is already part of the accepted durable TV user-state contract.

D5.4 must therefore preserve and synchronize a user's decision to hide a known
bad source through the Linux-authoritative state model.

The D-113 policy checkpoint does not require an Android or companion production
change.
