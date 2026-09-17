# D-117 — D5.4 Linux-authority pull probe

**Date:** 2026-09-17

**Type:** diagnostic-only

## Purpose

Validate the remaining direction of the D5.4 synchronization contract:
initialized/newer Linux authority -> onn.

## Added

- `tools/probes/d117_linux_authority_pull_probe.py`;
- D-116 runtime acceptance evidence;
- D-117 investigation and durable-memory status updates.

## Intentionally unchanged

- Android production code;
- companion production code;
- TV/EPG databases by the installer;
- EPG/catalog/playback behavior;
- runtime health/recency;
- VOD;
- Games/controllers/video/audio.

## Runtime behavior

The probe temporarily changes only the Linux `country_name` display string,
leaves `country_code` unchanged, verifies the onn pull, restores the original
Linux user-state content, then verifies the onn restores.

The test's two Linux writes intentionally advance the monotonic server revision.
