# D-107 — D5 EPG feed-aware identity probe

**Date:** 2026-09-16

**Type:** diagnostic-only development patch

## Purpose

Correct D-106's identity comparison before making another EPG architecture or
production-code decision.

## Changes

- adds `tools/probes/d107_epg_feed_identity_probe.py`;
- records D-106's valid raw provider measurements while superseding its sparse
  built-in-metadata classification;
- records the upstream `<channel>@<feed>` identity contract;
- updates D5.3 durable memory and roadmap state.

## Intentionally unchanged

- Android production code;
- D-104R2 XML/GZIP compatibility;
- companion production code;
- TV playback/catalog behavior;
- TV-state sync implementation;
- VOD;
- Games/controllers/video/audio.

## Runtime output

- `logs/tv/d107_epg_feed_identity_probe.json`
- `logs/tv/d107_epg_feed_identity_probe.txt`
