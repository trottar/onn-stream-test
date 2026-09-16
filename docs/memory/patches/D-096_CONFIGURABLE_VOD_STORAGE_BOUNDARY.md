---
memory_schema: 1
as_of: 2026-09-16
patch: D-096_CONFIGURABLE_VOD_STORAGE_BOUNDARY
durable_memory_updated: true
---

# D-096 configurable VOD storage boundary

Production:
- `companion/privyhub_service.py`
- `companion/range_server.py`

Operational tooling:
- `tools/storage/configure_vod_storage.py`
- `tools/probes/d096_storage_boundary_probe.py`

Behavior:
- optional machine-local `data/storage.json` selects physical VOD root;
- project `media/vod` remains default;
- logical `/vod` identity remains stable;
- internal live/HLS root remains project-local;
- Range server maps `/vod` independently;
- API exposes configured/mode/available for VOD storage;
- helper creates stable UUID-based `/mnt/privyhub-media` automount and removes
  old desktop-path symlink only after successful validation.

Privacy:
- raw filesystem UUID remains machine-local and is not logged in PrivyHub
  probe/receipt output.

Unchanged:
- Android client;
- Games;
- browser/camera runners;
- IPTV provider;
- Phase-C streaming/controller paths.
