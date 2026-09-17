# D-115 — D5 Linux TV-state authority

**Date:** 2026-09-16

**Type:** companion production seam / runtime validation required

## Purpose

Establish the versioned Linux durable TV user-state authority before Android
synchronization.

## Production changes

- `companion/plugins/tv_state.py`
- `companion/plugins/__init__.py`
- `companion/privyhub_service.py`

## Service change

Generic plugin POST routing supports an optional JSON-body handler with a
4 MiB request cap.

Plugins without that handler retain the existing POST behavior.

## State contract

Persisted under ignored `data/tv_state/state.json`.

Durable fields only:

- preferences;
- managed/custom providers;
- favorite/manual-hidden state;
- channel overrides;
- favorite groups/order;
- protect-auto-hide.

Runtime health/recents are excluded.

## Diagnostic

Adds:

`tools/probes/d115_tv_state_authority_probe.py`

The runtime probe restores exact predecessor state after testing.

## Intentionally unchanged

- Android production code;
- Android TV/EPG SQLite databases;
- Linux EPG plugin/cache;
- TV catalog/playback;
- TV runtime health semantics;
- VOD;
- Games/controllers/video/audio.

## Next

After runtime validation, D-116 connects Android to this authority.
