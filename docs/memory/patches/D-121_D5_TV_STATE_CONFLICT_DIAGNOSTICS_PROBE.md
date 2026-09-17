# D-121 — D5.4 TV-state conflict diagnostics probe

**Date:** 2026-09-17

**Type:** diagnostic-only

## Purpose

Validate the existing stale-revision protection and D-120 conflict
observability using the real Android mutation/push path.

## Added

- `tools/probes/d121_tv_state_conflict_diagnostics_probe.py`;
- D-120 runtime acceptance evidence;
- D-121 investigation / active-state memory.

## Production scope

No Android production change.

No companion production change.

No APK build or install.

No companion restart.

## Runtime mutation

Linux temporarily advances by one revision with only a country display-name
marker.

The user toggles one Favorite locally while the onn revision is stale.

Linux is then restored to the original user-state content at a later monotonic
revision and the normal TV Refresh path restores the onn.
