# D-124 — TV/EPG latency probe

**Date:** 2026-09-17

**Type:** diagnostic-only

## Purpose

Measure the external/database stages that could explain slow Live TV/guide
loading before adding Android instrumentation or redesigning the guide UI.

## Added

- `tools/probes/d124_tv_epg_latency_probe.py`;
- D-124 investigation;
- current/handoff/roadmap memory updates.

## Production scope

No Android production code change.

No companion production code change.

No APK build/install.

No companion restart.

The probe is read-only. Normal companion guide GETs may populate the companion's
existing runtime/cache state exactly as ordinary guide access would; no force
refresh is requested.
