# D-103 — D5.2 EPG ingestion diagnostic

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
