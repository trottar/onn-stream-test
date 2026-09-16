# D-106 — D5 EPG provider / identity probe

**Date:** 2026-09-16

**Type:** diagnostic-only development patch

## Purpose

Follow D-105's 2.7% exact guide-metadata coverage with one narrower identity
diagnostic before selecting a production EPG architecture.

## Changes

- adds `tools/probes/d106_epg_provider_identity_probe.py`;
- records the completed D-105 runtime result;
- updates durable memory to distinguish nonblank channel IDs from meaningful
  EPG identities;
- records D5.3 as active and diagnostic-only.

## Intentionally unchanged

- Android production code;
- D-104R2 XML/GZIP compatibility;
- companion production code;
- TV playback/catalog behavior;
- VOD;
- Games/controllers/video/audio.

## Runtime output

- `logs/tv/d106_epg_provider_identity_probe.json`
- `logs/tv/d106_epg_provider_identity_probe.txt`
