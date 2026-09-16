---
memory_schema: 1
as_of: 2026-09-16
patch: D-098_ABSENT_VOD_CATALOG_RESILIENCE
durable_memory_updated: true
---

# D-098 absent VOD catalog resilience

Production:
`companion/privyhub_service.py`

Change:
- catch dynamic-root filesystem OSError during initial availability checks;
- catch filesystem OSError around the complete recursive dynamic scan;
- return an empty dynamic result rather than propagating the storage error;
- publish no partial dynamic-source index from a failed scan.

This protects:
- `GET /sources` while removable VOD is absent;
- dynamic-source lookup for stale Continue Watching/source IDs;
- mid-scan physical removal.

Unchanged:
- Android client;
- systemd/fstab mount architecture;
- Range server;
- Games;
- live media;
- controller/streaming paths.
