---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# TV, IPTV, and Media Architecture

<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:TV_MEDIA:BEGIN -->
## Linux EPG acquisition/cache service boundary

D-109 established that the current upstream grabber can generate real programme
data from multiple guide sites.

D-110's development architecture is:

```text
upstream guide metadata + site definitions
        |
persistent rebuildable Linux EPG toolchain
        |
Linux programme cache
        |
existing companion /plugins API
        |
future Android EPG adapter
        |
onn local SQLite/UI cache
```

Properties:
- companion startup does not bootstrap EPG;
- EPG runtime lives under ignored `data/epg`;
- Node/npm is not installed system-wide;
- official portable runtime checksum and upstream commit are pinned;
- exact `channel[@feed]` identity is preserved;
- programme acquisition is serialized and bounded;
- positive results are cached;
- stale cache may survive refresh failure;
- no Android dependency on the upstream grabber implementation.

The ~446 MB reference toolchain footprint is acceptable only as a Prototype-1
development seam. Resource slimming or a smaller native acquisition adapter
remains open for cheap future Linux targets.
<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:TV_MEDIA:END -->

<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:TV_MEDIA:BEGIN -->
## EPG reference grabber dependency boundary

The current IPTV-org reference EPG grabber requires Node/npm, but the Prototype-1
Linux appliance does not currently have Node/npm installed.

Do not infer from a successful reference-grabber experiment that Node must become
a permanent PrivyHub production dependency.

D-109 uses a verified portable runtime only to answer acquisition viability.

If local acquisition is viable, production design must separately evaluate:
- resource footprint;
- scheduling/caching model;
- dependency isolation;
- update strategy;
- whether to retain the upstream Node tooling or implement a smaller native
  acquisition adapter.
<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:TV_MEDIA:END -->

<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:TV_MEDIA:BEGIN -->
## EPG acquisition boundary after D-107

The TV catalog and guide metadata identity layers must remain separate from
programme acquisition.

Current measured built-in IPTV-org state:
- exact feed-aware metadata coverage: 40.3712%;
- public hosted guide-source coverage: effectively 2 canonical IDs.

A Linux-local acquisition/cache path is now a plausible architecture candidate,
but it is not yet accepted.

D-108 tests the upstream EPG grabber only as a disposable reference
implementation. Passing D-108 does not require PrivyHub production to retain
Node/npm or the upstream repository as a permanent dependency.

Production architecture should be chosen only after measuring real programme
yield and resource/toolchain cost.
<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:TV_MEDIA:END -->

<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:TV_MEDIA:BEGIN -->
## Feed-aware TV / EPG identity

Current IPTV-org stream identity is feed-aware.

Canonical identity is:
- `channel` when no feed is present;
- `channel@feed` when a feed is present.

The playlist may carry this as one `tvg-id` string, while API stream and guide
records expose `channel` and `feed` separately.

PrivyHub diagnostics and future EPG mapping must preserve this distinction.

This is an exact structural identity rule, not fuzzy matching.

D-107 measures the impact before any production schema or mapping change.
<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:TV_MEDIA:END -->

<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:TV_MEDIA:BEGIN -->
## EPG source-format compatibility boundary

The Android TV EPG model remains XMLTV-based.

Guide-source ingestion may receive:
- plain XML;
- GZIP-compressed XML;
- other upstream formats such as JSON.

D5's compatibility boundary is intentionally narrow:
`guide mapping -> prefer XML / fallback GZIP -> magic-byte decompression -> existing XMLTV parser`.

The mapping database does not need a new source-format column because content
compression is determined from the fetched bytes. A parser-source version stored
in EPG meta invalidates only the refresh gate, not the SQLite schema.

JSON ingestion and non-exact channel matching remain separate future concerns
that require their own evidence before implementation.
<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:TV_MEDIA:END -->


<!-- PRIVYHUB_D101R1_BROWSER_CAMERA_C6_RECLASSIFICATION:TV_MEDIA:BEGIN -->
## Browser/camera native source architecture placement

The accepted future architecture for browser/app and camera/live streaming is
the C6 generalized native source pipeline:

`source/capture -> profile/encoder -> transport/FEC -> client decoder`

This allows reuse of:
- lifecycle/readiness;
- stream profiles/capability gates;
- telemetry/adaptation;
- transport/FEC;
- client decoder;
- diagnostics.

Browser input may later extend the client/session input contract to forward
keyboard/mouse events from client-attached HID devices.

Camera streaming-source infrastructure is C6; smart-home camera/device
orchestration remains Phase I.
<!-- PRIVYHUB_D101R1_BROWSER_CAMERA_C6_RECLASSIFICATION:TV_MEDIA:END -->

<!-- PRIVYHUB_D100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE:TV_MEDIA:BEGIN -->
## External VOD removable-storage architecture — accepted

Runtime-validated architecture:

```text
logical /vod namespace + stable IDs
        |
configurable VOD root
        |
nonblocking backing-device presence boundary
        |
UUID/system-managed removable storage
```

Accepted behavior:
- disk absent: control/media services stay available; dynamic VOD is empty;
- stale saved source: controlled failure;
- disk inserted: normal access activates/reuses the system mount;
- next catalog refresh repopulates the same logical IDs;
- Continue Watching survives the physical storage transition.

Final physical E2E passed repeated unplug/reinsert cycles without Linux desktop
or file-manager interaction.
<!-- PRIVYHUB_D100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE:TV_MEDIA:END -->

<!-- PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1:TV_MEDIA:BEGIN -->
## Nonblocking removable-VOD presence boundary

Configured local removable storage separates device presence from filesystem access. Device absent -> fast `/dev/disk/...` check -> unavailable, no mount-path touch. Device present -> normal access may activate systemd automount. Range server remains online without VOD so internal media is independent of removable storage.
<!-- PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1:TV_MEDIA:END -->

<!-- PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1:TV_MEDIA:BEGIN -->
## Removable VOD absent-state contract

The logical `/vod` namespace may point at removable physical storage.

When that storage is absent or disappears during a scan:
- filesystem `OSError` is treated as storage unavailability;
- dynamic VOD children are omitted for that request;
- no partial scan is published;
- the control API remains online;
- saved/stale source IDs fail through a controlled response;
- reinsertion plus a subsequent rescan restores the same logical IDs.

This keeps removable storage failure isolated from unrelated PrivyHub
subsystems.
<!-- PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1:TV_MEDIA:END -->

<!-- PRIVYHUB_D097_VOD_APPLIANCE_MODE:TV_MEDIA:BEGIN -->
## Removable VOD appliance operating model

Prototype-1 bulk VOD storage is treated as removable appliance media.

Normal mode:
- UUID-backed `/mnt/privyhub-media`;
- systemd `x-systemd.automount`;
- `nofail`;
- read-only filesystem;
- logical `/vod/...` namespace independent of physical storage;
- automount remains active even when disk is absent.

This allows a headless/server workflow:
`stop playback -> unplug -> later reinsert -> client access triggers recovery`.

Writable media ingestion is intentionally not part of normal serving mode.
Future direct rip/copy workflows should temporarily enter controlled writable
maintenance mode and expose safe-disconnect through PrivyHub rather than SSH.
<!-- PRIVYHUB_D097_VOD_APPLIANCE_MODE:TV_MEDIA:END -->

<!-- PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE:TV_MEDIA:BEGIN -->
## Configurable physical VOD root

D-096 separates internal runtime media from bulk VOD storage.

Logical namespace:
- `/live/...` -> internal project `media/live`;
- `/vod/...` -> configured physical VOD root, defaulting to project `media/vod`.

Machine-local configuration:
`data/storage.json` is ignored by Git and may contain an absolute `vod_root`.
No external-disk path or UUID is tracked in the repository.

Linux Prototype-1 mount:
- stable mountpoint: `/mnt/privyhub-media`;
- filesystem selected by UUID discovered locally by the setup helper;
- systemd automount + `nofail`;
- no dependence on user-session `/media/...` mounts.

This shape is intentionally portable to later dedicated server/storage: the
logical VOD namespace and media identity do not depend on the physical storage
path.
<!-- PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE:TV_MEDIA:END -->

<!-- PRIVYHUB_D094_EXTERNAL_STORAGE_REMOUNT:TV_MEDIA:BEGIN -->
## External media mount ownership

The external-drive test demonstrated that Linux desktop automount may be lazy:
physical reconnection alone did not recreate the mounted filesystem path, while
opening the drive in the file manager did.

PrivyHub itself recovered correctly after the mount appeared.

Architecture:
- OS/service layer: deterministic mount ownership at a stable path;
- PrivyHub: configured bulk-media root + availability reporting;
- scanner/range server: consume that root consistently;
- client semantics: unavailable storage is not the same as an empty library.

The final design should remain portable to later dedicated local/server storage
and must not encode a removable-drive label or desktop-session mount path.
<!-- PRIVYHUB_D094_EXTERNAL_STORAGE_REMOUNT:TV_MEDIA:END -->

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
