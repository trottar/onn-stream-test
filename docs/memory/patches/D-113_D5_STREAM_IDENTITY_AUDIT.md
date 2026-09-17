# D-113 — D5 stream identity audit

**Date:** 2026-09-16

**Type:** diagnostic-only

## Purpose

Audit feed-ID/display-name consistency after a working EPG exposed a
stream-content mismatch.

## Changes

- add `tools/probes/d113_stream_identity_audit.py`;
- record current 10 Bold upstream source/issue evidence;
- add D-113 investigation;
- update current/handoff/roadmap/architecture/daily memory.

## Intentionally unchanged

- Android production code;
- companion production code;
- Linux EPG plugin/cache/toolchain;
- onn TV/EPG databases;
- TV catalog data;
- playback health;
- VOD;
- Games/controllers/video/audio.

## Runtime outputs

- `logs/tv/d113_stream_identity_audit.json`
- `logs/tv/d113_stream_identity_audit.txt`

No database or cache is modified by the probe.
