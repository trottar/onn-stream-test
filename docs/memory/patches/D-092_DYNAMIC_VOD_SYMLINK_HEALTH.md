---
memory_schema: 1
as_of: 2026-09-16
patch: D-092_DYNAMIC_VOD_SYMLINK_HEALTH
durable_memory_updated: true
---

# D-092 dynamic VOD symlink health

Purpose:
make dynamic VOD source-start health consistent with scanner discovery for the
temporary external-storage symlink, without granting static sources arbitrary
external filesystem access.

Production:
- `companion/privyhub_service.py`

Diagnostic:
- `tools/probes/d092_dynamic_vod_source_start_probe.py`

Behavior changed:
only `_dynamic == True` scanner-generated VOD may pass source-start health when
its safe lexical media path traverses a symlink to external storage and resolves
to the exact scanner-recorded target.

Unchanged:
- static VOD containment;
- range server;
- Android app;
- external drive/symlink;
- browser/camera runners;
- Games;
- IPTV;
- Phase-C transport.
