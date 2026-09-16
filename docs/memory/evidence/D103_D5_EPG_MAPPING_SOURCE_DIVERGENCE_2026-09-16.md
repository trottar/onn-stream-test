# D-103 D5.2 EPG mapping-source evidence — 2026-09-16

## Runtime result

Classification:

`D103_MAPPING_SOURCE_SCHEMA_OR_FORMAT_DIVERGENCE`

Measured from the Linux D-103 probe with read-only onn SQLite snapshots:

- guide fetch succeeded;
- upstream guide entries: 180,681;
- entries with a source accepted by the current XML-only parser: 2;
- accepted unique mappings: 2;
- IPTV-org English playlist nonblank `tvg-id` values: 2,974;
- onn TV stream rows: 3,356;
- onn TV distinct nonblank channel IDs: 3,286;
- accepted guide mappings intersecting onn catalog IDs: 0;
- onn EPG mapping rows: 2;
- onn EPG programme rows: 0.

The onn mapping cache exactly matches the parser's 2-row result. This rules out
a simple stale-cache-only explanation for the observed state.

XML programme sampling could not run because neither accepted mapping intersected
the onn catalog.

## Source-level interpretation

The production parser accepts only source format `XML`. Current IPTV-org EPG
infrastructure supports compressed XML/GZIP output as well as other source
formats.

The first production repair is therefore source-format compatibility, not fuzzy
channel matching.

D-104 owns that repair and preserves exact channel/site identity until fresh
post-fix evidence identifies any later matching boundary.
