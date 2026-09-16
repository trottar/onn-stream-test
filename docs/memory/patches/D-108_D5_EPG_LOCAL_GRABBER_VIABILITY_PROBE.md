# D-108 — D5 EPG local-grabber viability probe

**Date:** 2026-09-16

**Type:** diagnostic-only development patch

## Purpose

Record the D-107 runtime result and test whether Linux-local guide acquisition
is viable for representative exact channel matches.

## Upstream reference

Pinned `iptv-org/epg` commit:

`78e94adb76841a63d94a53e80dbd0d52bb7c2c5c`

## Changes

- adds `tools/probes/d108_epg_local_grabber_viability_probe.py`;
- records the D-107 feed-aware coverage result;
- adds the D-108 local-grabber investigation;
- updates current/handoff/roadmap/architecture/daily durable memory.

## Intentionally unchanged

- Android production code;
- companion production code;
- D-104R2 XML/GZIP compatibility;
- TV playback/catalog behavior;
- TV-state synchronization implementation;
- VOD;
- Games/controllers/video/audio;
- host Node/npm/git installation.

## Runtime output

- `logs/tv/d108_epg_local_grabber_viability_probe.json`
- `logs/tv/d108_epg_local_grabber_viability_probe.txt`
