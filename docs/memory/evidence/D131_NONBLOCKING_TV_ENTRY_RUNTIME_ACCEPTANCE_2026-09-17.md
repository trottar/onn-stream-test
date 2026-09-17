# D-131 — Non-blocking TV-entry runtime acceptance

**Date:** 2026-09-17

Classification:

`D131_TV_ENTRY_NONBLOCKING_SYNC_VALIDATED`

Measured runtime values:

- `ui_ready_total_ms: 330`
- `ensure_catalog_ms: 19`
- `state_sync_ms: 24050`
- `state_sync_total_ms: 24754`
- `sync_reconciled_total_ms: 25073`
- `state_sync_action: pulled`
- `state_sync_local_changed: true`
- `ui_ready_before_sync_complete: True`

User-visible observation: TV entry now loads in roughly one or two seconds and
other Live TV behavior appears normal.

Conclusion: D-131 is runtime accepted. The local TV cache can render immediately
while the unchanged Linux-authoritative pull/import continues and reconciles
afterward. This preserves durable authority while removing remote latency from
the first-render critical path.
