# D-113 — D5 stream identity integrity audit

<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:D113_RESULT:BEGIN -->
## Runtime result / disposition — 2026-09-16

D-113 passed with:

`D113_CONFIRMED_UPSTREAM_STREAM_IDENTITY_CONTRADICTION`

Measured:
- 3,071 built-in IPTV-org rows;
- 3,070 feed-bearing rows;
- 3,013 exact official API URL matches;
- 9 feed-name contradiction heuristic hits.

The 10 Bold trigger is confirmed:
- `10 Bold Adelaide (1080p)`;
- `10Bold.au@Sydney`;
- official API preserves the same contradiction;
- known bad URL hash matches;
- user-observed video does not contain 10 Bold content.

The remaining hits include ambiguous name/feed cases, so the classifier is not
precise enough for generic automatic suppression.

Disposition:
- close D-113 at current scope;
- no production identity-suspect heuristic;
- no hardcoded URL deny list;
- manual Hide is the current safe user action;
- preserve manual-hidden state in D5.4 synchronization.

See `decisions/D114_STREAM_IDENTITY_POLICY.md`.
<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:D113_RESULT:END -->

**Status:** diagnostic-only / runtime evidence next

## Trigger

D-111 established a working companion-backed Program Guide.

After D-112 readability polish, `10 Bold Adelaide` displayed video content that
did not match the 10 Bold guide.

Current upstream source evidence shows the catalog entry itself is contradictory:

- canonical ID says `10Bold.au@Sydney`;
- title says `10 Bold Adelaide`;
- an existing upstream issue reports the same stream URL actually carries Rocky
  Mountain PBS Kids.

## Narrow question

Is this feed-ID/display-name contradiction isolated to this stream, or does the
current onn built-in IPTV-org catalog contain a broader class of contradictory
feed identities?

## Probe

`tools/probes/d113_stream_identity_audit.py`

The probe is read-only.

It:

1. snapshots the onn `privyhub_tv.db` through authorized ADB `run-as`;
2. reads only built-in `iptv_org` stream rows;
3. fetches current official IPTV-org `feeds.json`;
4. fetches current official IPTV-org `streams.json`;
5. checks feed-bearing canonical IDs against official feed names/alt names;
6. flags only explicit contradictions where the display name names a *different*
   known feed while not naming the assigned feed;
7. compares stream URLs to current official API stream rows by SHA-256;
8. reports the current Linux EPG cache metadata for `10Bold.au` rows;
9. writes fresh JSON/text evidence.

The probe does not infer video content from pixels/audio.

## Why no production fix yet

The specific 10 Bold source is clearly suspect, but a general rule should not be
added from one example.

D-113 measures the breadth of feed-name contradictions first.

Potential follow-up, depending on evidence:

- isolated upstream defect -> targeted source quarantine/manual override path;
- multiple contradictions -> generic `identity_suspect` catalog state and EPG
  suppression until stream identity is trusted;
- no metadata contradictions beyond 10 Bold -> do not burden the full catalog
  with an aggressive heuristic.

Playback health and semantic identity must remain separate concepts:
a stream can be technically healthy while broadcasting the wrong channel.
