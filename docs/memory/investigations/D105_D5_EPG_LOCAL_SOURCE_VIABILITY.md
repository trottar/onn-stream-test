# D-105 — D5 EPG local-source viability

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
