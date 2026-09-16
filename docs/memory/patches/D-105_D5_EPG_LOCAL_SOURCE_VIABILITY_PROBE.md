# D-105 — D5 EPG local-source viability probe

**Date:** 2026-09-16

**Type:** diagnostic-only development patch

## Purpose

Correct the D5 EPG investigation after D-104R2 runtime evidence showed that
XML/GZIP support does not increase the two currently source-backed guide
mappings.

## Changes

- adds `tools/probes/d105_epg_local_source_viability_probe.py`;
- records the current upstream public-source availability evidence;
- updates durable memory so 180,681 guide metadata rows are not mistaken for
  180,681 downloadable guide feeds;
- records D-104R2 as compatible but not runtime-accepted;
- leaves all Android, companion, VOD, Games, controller, streaming, and TV
  production code unchanged.

## Output

- `logs/tv/d105_epg_local_source_viability_probe.json`
- `logs/tv/d105_epg_local_source_viability_probe.txt`

## Runtime status

Probe package only. D5.3 remains active and not accepted.
