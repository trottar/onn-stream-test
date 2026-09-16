---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# TV, IPTV, and Media Architecture

The TV/IPTV subsystem is mature and should remain stable during Games/controller work. It includes persistent catalog state, paging, hidden channels, favorites, recents, search, EPG, fullscreen/channel-surfing behavior, grouping/order/overrides, provider handling, backup behavior, and preview UX.

The companion also supports local live/browser/camera sources and dynamically scanned VOD/media content. Control and media planes are separate.

These systems are part of the broader PrivyHub goal but are not dependencies to modify for the four-player Games extension.

<!-- PRIVYHUB_D089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT:TV_MEDIA:BEGIN -->
## Bulk-media storage boundary for Linux Prototype 1

The Linux Prototype 1 should separate small PrivyHub operational state from bulk
media capacity.

Current deployment intent:

```text
internal system disk
    -> PrivyHub code/runtime
    -> catalog/configuration
    -> metadata/cache where practical

external hard drive
    -> bulk VOD/movie files
```

This is not a requirement that future PrivyHub installations use removable
storage. The media library must remain storage-backend/path portable so later
server-like storage can replace the temporary external disk.

D5 must specifically verify how the existing dynamic-media scanner and range
server behave when the configured bulk-media root is external and when that
storage is temporarily unavailable. Absence of the storage root must not be
silently treated as authoritative deletion of user media.

No mount path or filesystem is standardized by this decision.
<!-- PRIVYHUB_D089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT:TV_MEDIA:END -->
