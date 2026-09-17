# D-130 — TV-entry latency stage probe

**Date:** 2026-09-17

**Type:** diagnostic-only Android observability patch

## Purpose

Measure the stage that owns the remaining top-level `Loading TV catalog...`
latency before making a production change.

## Changed runtime source

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`
  - adds monotonic `D130_TV_ENTRY` timing markers around catalog, sync,
    post-sync catalog and UI-ready stages.

## Diagnostic

- `tools/probes/d130_tv_entry_latency_probe.py`
  - clears logcat during `--prepare`;
  - parses the latest complete timing session during `--verify`;
  - writes raw stage measurements and a bounded classifier;
  - writes no network address or device identifier.

## Boundaries

No catalog/sync semantics, timeouts, EPG behavior, playback, Favorites, Hide,
VOD, Games, audio/video/controller behavior changes.
