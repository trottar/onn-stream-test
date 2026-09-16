---
memory_schema: 1
as_of: 2026-09-16
patch: D-099_NONBLOCKING_VOD_PRESENCE
durable_memory_updated: true
---

# D-099 nonblocking VOD presence

Production changes:
- `companion/privyhub_service.py`
- `companion/range_server.py`
- `companion/storage_presence.py`

Adds nonblocking local backing-device presence checks; avoids configurable VOD `resolve()` calls that can activate automount; keeps range server online with VOD absent; returns absent `/vod` requests quickly. Raw storage identifiers are not logged.
