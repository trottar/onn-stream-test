# D-119 — D5.4 TV-entry sync-trigger probe

**Date:** 2026-09-17

**Type:** diagnostic-only

## Purpose

Measure whether a true top-level TV entry runs the existing synchronization
path reliably, without using Refresh.

## Added

- `tools/probes/d119_tv_entry_sync_trigger_probe.py`;
- D-119 investigation record;
- active-state / handoff / roadmap updates.

## Intentionally unchanged

- Android production code;
- companion production code;
- Linux TV-state schema/authority;
- TV/EPG SQLite databases by the installer;
- playback, catalog, EPG, health, VOD, games, controllers, video, and audio.

## Runtime mutation

The probe temporarily changes only Linux `preferences.country_name`, preserving
`country_code`.

Linux user-state content is restored during verify when safe. Final cleanup uses
the already-validated TV Refresh pull path.
