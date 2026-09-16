# D-105 — D5 EPG local-source viability

<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:D105_CORRECTION:BEGIN -->
## Feed-identity correction after D-106

D-105's public-source result remains valid: current hosted guide-source
availability is effectively absent for the onn catalog.

Its 89/3,286 metadata-overlap figure is representation-incomplete for built-in
IPTV-org streams because current playlist IDs may include `@feed` while the
probe compared them only to guide `channel`.

Do not use the D-105 exact-overlap percentage as final metadata coverage.

D-107 supersedes that coverage calculation with feed-aware canonical identity.
<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:D105_CORRECTION:END -->

<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:D105_RESULT:BEGIN -->
## Result — 2026-09-16

D-105 completed successfully.

Classification:
`D105_METADATA_MATCHES_BUT_PUBLIC_SOURCES_UNAVAILABLE`.

Measured:
- 180,681 guide rows / 11,723 unique guide IDs;
- 3,286 unique nonblank onn TV channel IDs;
- 89 exact metadata matches (2.7085%);
- 86 English exact matches (2.6172%);
- 0 source-backed matched channels;
- 1 green public guide worker covering 2 channels.

Decision:
do not build Linux-local EPG acquisition yet. First separate meaningful channel
IDs from generated `tv_stream_*` IDs and partition metadata coverage by provider.

D-106 owns the next diagnostic.
<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:D105_RESULT:END -->

**Status:** diagnostic-only / runtime evidence next

## Question

Do the 180,681 IPTV-org guide metadata rows cover a useful portion of the
effective onn TV catalog even though current public hosted guide sources cover
only two channels?

## Probe

`tools/probes/d105_epg_local_source_viability_probe.py`

The probe:

- fetches current IPTV-org `guides.json`;
- reads a temporary, read-only snapshot of the onn TV database when ADB
  `run-as` is available;
- falls back to the English IPTV-org playlist only if the onn snapshot is
  unavailable;
- measures exact guide-metadata-to-catalog identity coverage before source
  availability filtering;
- measures English-language coverage separately;
- measures how many matched channels currently have a usable XML/GZIP source;
- ranks guide sites by unique matched catalog channels;
- reads the current public IPTV-org guide-worker status;
- writes fresh JSON and text evidence under `logs/tv/`;
- does not modify the onn database or production behavior.

## Decision boundary

If metadata/catalog intersection is substantial while public-source
intersection is absent or minimal, investigate Linux-local EPG acquisition and
caching using the existing IPTV-org EPG tooling.

If metadata/catalog intersection itself is weak, do not add a local grabber
yet; diagnose identity/provider coverage first.
