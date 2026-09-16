# D-105 — D5 EPG upstream source availability evidence — 2026-09-16

**Status:** runtime evidence / architectural correction

## Fresh runtime evidence

After D-104R2 was installed, committed, pushed, and the onn APK was updated,
D-103 still reported:

- `guides.json` fetch succeeded;
- 180,681 entries were returned;
- only 2 entries had a supported XML/GZIP source;
- only 2 unique mappings were accepted;
- the onn EPG database contained the same 2 mappings;
- the onn EPG database contained 0 programmes;
- those 2 mappings had no exact or case-insensitive intersection with the
  3,286 nonblank channel IDs in the onn TV database.

## Upstream corroboration

The current official IPTV-org `epg/GUIDES.md` lists one green public worker
covering 2 channels. The other listed workers are red and report 0 channels.

The current IPTV-org API documentation describes `guides.json` as guide
metadata containing channel/site identity plus a `sources` array. The 180,681
top-level rows therefore must not be interpreted as 180,681 currently hosted
downloadable guide feeds.

## Correction

The earlier D-103 classification
`D103_MAPPING_SOURCE_SCHEMA_OR_FORMAT_DIVERGENCE` was too broad.

The decisive current boundary is:

`D105_UPSTREAM_PUBLIC_EPG_SOURCE_AVAILABILITY`

D-104R2's XML-preferred/GZIP-fallback support is compatible and may remain,
but it did not repair the current EPG outage and does not constitute D5.3
runtime acceptance.

## Next narrow diagnostic

D-105 measures guide-metadata coverage against the effective onn catalog
*before* the `sources[]` availability filter. It reports exact channel coverage,
English coverage, source-backed coverage, and the guide sites responsible for
the largest matched channel sets.

No onn database is modified.
