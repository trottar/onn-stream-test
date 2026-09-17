# D-130 — TV-entry latency runtime evidence

**Date:** 2026-09-17

Classification:

`D130_TV_ENTRY_STATE_SYNC_DOMINANT`

Measured runtime values from `logs/tv/d130_tv_entry_latency_probe.txt`:

- `total_entry_ms: 24525`
- `ensure_catalog_ms: 7`
- `state_sync_ms: 24214`
- `post_sync_catalog_ms: 3`
- `ui_render_ms: 291`
- `initial_catalog_cached: true`
- `state_sync_action: pulled`
- `state_sync_local_changed: true`

Conclusion: the top-level TV entry delay is not catalog loading. The cached
catalog path is effectively immediate; the blocking Linux TV-state round trip
owns about 98.7% of the measured entry latency. This evidence authorizes a
narrow scheduling change while preserving the D5.4 authority contract.
