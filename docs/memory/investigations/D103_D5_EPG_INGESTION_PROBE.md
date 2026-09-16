# D-103 — D5.2 EPG ingestion diagnostic

<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:D103_RESULT:BEGIN -->
## Result — 2026-09-16

D-103 completed successfully and identified the first divergence before XMLTV
programme parsing.

Measured:
- guide fetch: success;
- guide entries: 180,681;
- entries accepted by the XML-only source gate: 2;
- unique accepted mappings: 2;
- onn cached mapping rows: 2;
- onn cached programme rows: 0;
- onn TV streams: 3,356;
- onn distinct nonblank channel IDs: 3,286;
- accepted-guide to onn-catalog intersection: 0.

Classification:
`D103_MAPPING_SOURCE_SCHEMA_OR_FORMAT_DIVERGENCE`.

Source inspection then confirmed current IPTV-org EPG workers support compressed
XML/GZIP output in addition to XML and JSON. D-104 owns the narrow compatibility
repair. D-103 remains the runtime evidence probe and is updated to model
XML-preferred/GZIP-fallback source selection.
<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:D103_RESULT:END -->


**Status:** diagnostic-only / runtime evidence next
**Date:** 2026-09-16

## Narrow question

Why does the accepted Live TV catalog contain 3,356 streams while the onn reports
only 2 EPG mappings and 0 cached programmes?

## Probe contract

`tools/probes/d103_epg_ingestion_probe.py` is read-only with respect to PrivyHub
production state. It:

1. fetches the same `guides.json` used by `TvEpgRepository`;
2. reproduces the current Android mapping parser gates exactly;
3. fetches the same IPTV-org English playlist used by `TvRepository`;
4. measures exact channel-ID intersection;
5. when exactly one authorized ADB device is available, takes temporary read-only
   snapshots of `privyhub_epg.db` and `privyhub_tv.db` through `run-as`;
6. compares upstream mappings, onn cached mappings, and onn catalog IDs;
7. samples a bounded number of mapped XMLTV sources and measures exact
   channel/site programme matches;
8. writes fresh JSON and text evidence under `logs/tv/`.

The probe does not clear caches, refresh the app database, change providers,
modify Android code, or require an IP address.

## Evidence rule

Trust the raw stage measurements over the classifier. The classifier is only a
routing aid for the next single fix.

## Output

- `logs/tv/d103_epg_ingestion_probe.json`
- `logs/tv/d103_epg_ingestion_probe.txt`

Return the text log first. Inspect the JSON only if the text summary identifies a
boundary that needs the detailed counters.
