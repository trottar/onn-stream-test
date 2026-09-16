---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# TV, IPTV, and Media Architecture

<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:TV_MEDIA:BEGIN -->
## External VOD runtime validation and next storage boundary

The temporary external-drive-backed VOD path is runtime validated through the
normal onn client, including Continue Watching.

The compatibility chain currently works through a VOD directory symlink, with
D-092 allowing scanner-generated dynamic source health to match scanner
discovery.

Product architecture must not depend on that symlink. The next storage boundary
should select a media root explicitly and make that same root authoritative for
both catalog scanning and HTTP serving.

The selection mechanism must preserve the repo-local `media/` default and fail
cleanly when an explicitly selected external root is unavailable.
<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:TV_MEDIA:END -->

<!-- PRIVYHUB_D092_DYNAMIC_VOD_SYMLINK_HEALTH:TV_MEDIA:BEGIN -->
## Dynamic VOD health and external-storage symlinks

During D5, a temporary directory symlink beneath `media/vod` exposed a mismatch
between catalog discovery and source-start health validation.

The scanner owns dynamic source creation. D-092 therefore permits only those
scanner-generated sources to traverse a symlink outside the project tree, and
only when the lexical playback path is safe and resolves to the exact scanner
recorded file.

Static catalog sources do not gain general external-path access.

This preserves a narrow fail-closed boundary while Prototype-1 uses temporary
external storage. A first-class configurable bulk-media root is still the
long-term D5 architecture.
<!-- PRIVYHUB_D092_DYNAMIC_VOD_SYMLINK_HEALTH:TV_MEDIA:END -->

<!-- PRIVYHUB_D091_D5_MEDIA_BASELINE:TV_MEDIA:BEGIN -->
## D5 Prototype-1 external VOD measurement

A directory symlink under the project VOD tree can currently expose the
Prototype-1 external movie disk to the existing scanner and range server. A
representative movie was discovered and served successfully with HTTP Range 206.

This proves host compatibility only. The symlink is not the desired permanent
storage abstraction because the companion still defines `MEDIA_ROOT` as the
project `media/` directory.

D5 should make the bulk-media root explicit/configurable while keeping small
PrivyHub state local and preserving stable library identity across storage
migration.
<!-- PRIVYHUB_D091_D5_MEDIA_BASELINE:TV_MEDIA:END -->

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
