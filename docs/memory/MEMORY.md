---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Curated Project Memory

<!-- PRIVYHUB_D117_PULL_VALIDATION:MEMORY:BEGIN -->
## D5.4 seed/push acceptance

D-116 runtime validated Linux/onn durable-state parity after:
- initial Linux seed from onn;
- a real manual-hidden user mutation;
- revision advancement to 2.

Canonical state hashes matched exactly.

Before closing D5.4, separately prove the pull direction with Linux intentionally
newer than the onn.

D-117 performs that test using only the country display name. Never change the
country code merely to create a sync test, because that would alter catalog
filter semantics.
<!-- PRIVYHUB_D117_PULL_VALIDATION:MEMORY:END -->

<!-- PRIVYHUB_D116_TV_STATE_SYNC:MEMORY:BEGIN -->
## TV durable-state synchronization boundary

D-115 validated Linux revisioned JSON authority.

D-116 client rules:
- seed Linux only when it is uninitialized;
- once initialized, Linux is authoritative on TV entry;
- push only durable user intent;
- use `server_revision` optimistic concurrency;
- stale writes must not overwrite Linux;
- local TV remains fail-soft/offline-capable.

Durable projection:
- language/country;
- managed/custom provider configuration;
- favorites;
- favorite groups/order;
- manual hidden;
- custom name/category/URL/referrer/user-agent;
- protect-auto-hide.

Never synchronize raw SQLite, EPG/cache data, playback-health counters,
last-watched timestamps, or auto-hidden runtime state as user preferences.
<!-- PRIVYHUB_D116_TV_STATE_SYNC:MEMORY:END -->

<!-- PRIVYHUB_D115_TV_STATE_AUTHORITY:MEMORY:BEGIN -->
## D5.4 TV-state authority rules

Do not mirror the Android version-2 TV backup directly onto Linux.

That backup mixes durable intent with runtime observations.

Linux-authoritative D5.4 state contains only:
- preferences;
- provider definitions/enabled state;
- favorite/manual-hidden state;
- channel profile overrides;
- favorite group/order;
- protect-auto-hide.

Runtime health/recency stays client/runtime data until explicit merge semantics
exist.

Linux owns a monotonic `server_revision`.
A write must carry the current `base_revision`.
Stale revisions never overwrite current state.
Identical state is idempotent and does not consume a revision.

State is versioned JSON under ignored `data/tv_state/`, never a copied SQLite
database.

An uninitialized Linux authority must be seeded from current onn durable state
before a later Android pull can become authoritative.
<!-- PRIVYHUB_D115_TV_STATE_AUTHORITY:MEMORY:END -->

<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:MEMORY:BEGIN -->
## Semantic stream-identity policy

D-113 measured 9 feed-name contradictions among 3,071 built-in IPTV-org streams,
but several were ambiguous naming/token cases.

Do not turn that heuristic into automatic hiding, transport failure, or EPG
suppression.

The confirmed 10 Bold case proves a narrower rule:
a technically healthy stream and a valid guide identity do not prove that the
video is semantically the advertised channel.

Keep separate:
- transport/playback health;
- feed/catalog metadata consistency;
- semantic content identity;
- EPG acquisition/cache correctness.

For user-confirmed bad sources, existing manual Hide is the safe current action.
Do not hardcode ephemeral third-party stream URLs as architectural product rules.

`manual_hidden` is durable user intent and must survive D5.4 Linux-authoritative
TV-state synchronization.
<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:MEMORY:END -->

<!-- PRIVYHUB_D113_D5_STREAM_IDENTITY:MEMORY:BEGIN -->
## Stream transport health is not stream identity health

A stream can:
- return valid media;
- accumulate playback successes;
- have a syntactically valid canonical channel/feed ID;
- have a functioning EPG;

and still broadcast the wrong channel.

Observed example:
the upstream row titled `10 Bold Adelaide` currently carries canonical ID
`10Bold.au@Sydney`, and an upstream issue reports its URL actually carries Rocky
Mountain PBS Kids.

Therefore never use successful playback alone as proof that EPG semantic
identity is trustworthy.

Keep separate:
1. transport/playback health;
2. channel/feed metadata consistency;
3. actual content identity;
4. EPG acquisition/cache correctness.

D-113 measures metadata consistency before a generic identity-suspect policy is
designed.
<!-- PRIVYHUB_D113_D5_STREAM_IDENTITY:MEMORY:END -->

<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:MEMORY:BEGIN -->
## D5.3 EPG runtime acceptance

D-111 completed the end-to-end EPG path and is accepted:

- Linux companion EPG acquisition/cache works;
- Android consumes `/plugins/epg/guide`;
- onn SQLite stores returned programmes;
- Program Guide renders schedule times and titles;
- playback remains independent of guide success.

Accepted runtime sample:
`10Bold.au@Sydney` with 65 cached programmes and a non-stale companion response.

The visible `\n` separators observed after acceptance are a
`MainActivity.showTvProgramGuide()` presentation bug, not an EPG data defect.

D-112 fixes that literal-newline rendering bug only.

Next architectural work after the polish is D5.4 TV durable-state ownership/sync.
<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:MEMORY:END -->

<!-- PRIVYHUB_D111_D5_ANDROID_COMPANION_EPG:MEMORY:BEGIN -->
## Android EPG cache / companion priority rule

After D-110 runtime acceptance, Android EPG refresh policy is:

1. use fresh nonempty onn SQLite guide data immediately;
2. otherwise prefer the Linux companion EPG endpoint;
3. persist successful companion programmes back into the same onn SQLite cache;
4. if Linux is unavailable, preserve stale/nonempty local data for normal
   navigation;
5. retain the older public hosted-guide acquisition path only as fallback.

Do not copy SQLite databases between Linux and Android.

Linux owns acquisition/cache generation; onn owns its local UI/offline cache.

Canonical identity remains exact `channel[@feed]`.

Playback must not depend on EPG success.

D-110's persistent reference-toolchain footprint is 626,714,586 bytes and
remains a future resource-optimization concern.
<!-- PRIVYHUB_D111_D5_ANDROID_COMPANION_EPG:MEMORY:END -->

<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:MEMORY:BEGIN -->
## Linux EPG acquisition/cache ownership rule

D-109 proved multi-site local EPG acquisition.

For D5, Linux now owns EPG acquisition/cache through the companion plugin API.
Android continues to own its local SQLite/UI cache until the Linux seam is
runtime validated.

Reference-grabber resource facts:
- initial setup: 77.42 seconds;
- disposable upstream tree: 445,831,397 bytes;
- representative uncached channel grabs: about 7-8 seconds.

Therefore:
- never reinstall/clone the upstream grabber for every guide request;
- keep toolchain state persistent but rebuildable under ignored `data/epg`;
- do not make Node/npm a system package dependency merely because the reference
  implementation uses Node;
- do not block normal companion startup on EPG bootstrap;
- cache positive programme results for normal guide navigation;
- preserve stale cached guide data when refresh fails;
- preserve exact `channel[@feed]` identity and keep fuzzy matching deferred.

A passing D-110 does not settle the final cheap-Linux dependency footprint.
Toolchain slimming/native acquisition remains an optimization question after
functional D5 acceptance.
<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:MEMORY:END -->

<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:MEMORY:BEGIN -->
## Diagnostic toolchain must not become appliance dependency by accident

A missing diagnostic dependency is not by itself a reason to install that
dependency permanently on the PrivyHub appliance.

D-108 found no host Node/npm, so it stopped before testing local EPG
acquisition.

For D-109, Node/npm is supplied as a checksum-verified portable official runtime
in a temporary directory. It exists only for the D-108 subprocess and is
deleted afterward.

This preserves the architectural distinction between:
- a reference/tooling implementation used to prove viability;
- the eventual PrivyHub production dependency model.

Passing a Node-based diagnostic does not commit PrivyHub production to Node.
<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:MEMORY:END -->

<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:MEMORY:BEGIN -->
## D5 EPG metadata-versus-acquisition boundary

D-107 established that feed-aware guide metadata is materially useful for the
built-in IPTV-org provider:

- 3,017 meaningful built-in IDs;
- 1,218 exact canonical guide matches (40.3712%);
- 1,475 IDs with some base-channel guide metadata.

This supersedes the earlier idea that guide metadata itself was broadly sparse.

A separate upstream limitation remains:
only 2 canonical IDs currently expose public hosted XML/GZIP guide sources.

Treat these as separate dimensions:
1. channel/feed metadata identity;
2. programme acquisition mechanism;
3. actual current/upcoming programme yield.

The next architectural decision must be based on measured local acquisition,
not on `guides.json` row count alone.
<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:MEMORY:END -->

<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:MEMORY:BEGIN -->
## IPTV-org channel/feed canonical identity rule

For current IPTV-org stream/guide data, identity can include a feed dimension.

Playlist stream IDs may be:
- `<channel_id>`;
- `<channel_id>@<feed_id>`.

API stream and guide records expose the same components separately as
`channel` and optional `feed`.

Canonical comparison rule:
- feed blank -> `channel`;
- feed nonblank -> `channel@feed`.

Never compare a composite playlist ID only against the guide's bare `channel`
field and interpret non-overlap as missing metadata.

D-106's provider/synthetic counts remain valid, but its
`D106_BUILTIN_GUIDE_METADATA_COVERAGE_SPARSE` classification is superseded.

Public guide-source availability is a separate dimension and remains minimal.
<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:MEMORY:END -->

<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:MEMORY:BEGIN -->
## TV channel identity quality rule

A nonblank `streams.channel_id` is not automatically a meaningful TV/EPG
identity.

`TvRepository.parsePlaylist()` uses the playlist `tvg-id` when available. If it
is blank, the repository falls back to the generated stable stream ID. Those
fallback IDs begin with `tv_stream_`.

`TvRepository.meaningfulChannelId()` explicitly treats `tv_stream_*` IDs as
non-meaningful channel identities.

Therefore EPG diagnostics must report meaningful and synthetic identities
separately rather than using all nonblank `channel_id` values as the denominator.

Provider identity also matters: non-built-in providers attempt to resolve to a
known built-in IPTV-org identity before their stream is stored.

D-106 establishes the provider/identity breakdown before further EPG design.
<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:MEMORY:END -->

<!-- PRIVYHUB_D105_D5_EPG_LOCAL_SOURCE_VIABILITY:MEMORY:BEGIN -->
## IPTV-org guide-row versus hosted-source rule

As of 2026-09-16, IPTV-org `guides.json` contains 180,681 guide metadata rows,
but current public hosted guide availability is drastically smaller. Official
`epg/GUIDES.md` lists one green worker covering 2 channels; the other listed
workers report 0.

Do not equate top-level `guides.json` row count with downloadable EPG coverage.

PrivyHub must distinguish:
- guide metadata identity: channel, feed, site, site ID, language;
- currently available hosted guide sources: `sources[]`;
- actual programme coverage after XMLTV acquisition.

D-104R2's XML/GZIP compatibility is safe to retain, but runtime evidence showed
it does not solve the present 2-mapping/0-programme condition.

Before choosing a production EPG architecture, measure metadata-to-catalog
coverage without the public-source filter. If coverage is useful, Linux-local
EPG acquisition/caching is the next architectural candidate.
<!-- PRIVYHUB_D105_D5_EPG_LOCAL_SOURCE_VIABILITY:MEMORY:END -->

<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:MEMORY:BEGIN -->
## D5 EPG source-format compatibility rule

D-103 established that the September 2026 IPTV-org guide feed is not failing at
network fetch: it returned 180,681 entries. PrivyHub reduced that feed to only
2 mappings because `TvEpgRepository` accepted only `sources[].format == XML`.

Current upstream EPG infrastructure may expose compressed XML as `GZIP`.
PrivyHub's D5 compatibility rule is:
- prefer a valid XML source when one is present;
- otherwise accept a valid GZIP source;
- identify compressed response bytes by gzip magic before XMLTV parsing;
- do not infer gzip solely from an HTTP header or filename;
- leave JSON source parsing deferred unless later evidence requires it;
- preserve exact channel/site ID matching until a separate diagnostic proves a
  matching defect.

Mapping parser/source-selection semantics have a version marker in EPG meta so
an old nonempty cache cannot suppress the first refresh after a parser upgrade.

The D-103 `2 mappings / 0 programmes` state is measured parser incompatibility,
not merely a stale-cache theory.
<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:MEMORY:END -->



<!-- PRIVYHUB_D102_D5_TV_SYNC_CHECKPOINT:MEMORY:BEGIN -->
## D5 TV durable rules

- Current onn Live TV catalog/categories/playback are runtime accepted on the
  Linux migration baseline.
- Current EPG is not accepted: fresh status showed 2 mappings and 0 cached
  programmes; the Program Guide UI works but has no actual guide data on tested
  channels.
- Diagnose the existing EPG ingestion path stage-by-stage before changing
  production matching/parser behavior.
- Linux is the durable authority target for TV user intent; onn keeps a local
  cache.
- Reuse/version the Android TV export/import model for synchronization. Never
  synchronize by copying `privyhub_tv.db` or `privyhub_epg.db`.
- Provider-derived catalogs and programme listings are rebuildable cache.
- Multi-client merge semantics for runtime health/recent-viewing observations
  must be explicit; do not blindly overwrite counters across clients.
- D5 restores the existing guide and establishes TV user-state sync. Full
  channel/guide redesign remains later media/TV work.
<!-- PRIVYHUB_D102_D5_TV_SYNC_CHECKPOINT:MEMORY:END -->

<!-- PRIVYHUB_D101R1_BROWSER_CAMERA_C6_RECLASSIFICATION:MEMORY:BEGIN -->
## Browser/camera roadmap ownership

Do not rebuild legacy browser/camera runners as temporary D5 Linux-specific
paths.

Roadmap ownership:
- D5: VOD + Live TV/EPG + diagnostics restored on Linux;
- after D8: return to remaining Phase C on Linux;
- C6: browser/app and camera/live streaming through generalized native source
  abstraction and shared profile/telemetry/transport/decoder infrastructure;
- optional browser keyboard/mouse forwarding from onn/client HID belongs with
  that C6 source/session work;
- Phase I: broader smart-home camera/device integration.

The current Linux host lacking a camera is not a D5 blocker.
<!-- PRIVYHUB_D101R1_BROWSER_CAMERA_C6_RECLASSIFICATION:MEMORY:END -->

### D-101R1 local-roadmap correction

The earlier D-101 attempt failed before modification because its
installer incorrectly required `ROADMAP.md` at the Linux repository
root. The roadmap file reviewed in chat was uploaded reference material;
the repo's durable roadmap state is maintained in
`docs/memory/roadmap/STATUS.md`.

D-101R1 records the same accepted reclassification entirely through the
actual durable-memory/decision files and does not create or require a
new root-level roadmap file.

<!-- PRIVYHUB_D100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE:MEMORY:BEGIN -->
## External VOD removable-storage contract — runtime validated

Validated Linux/onn product behavior:

- bulk VOD physical storage is configurable and independent of logical `/vod`;
- logical source IDs remain stable across physical storage migration/remount;
- the server may run indefinitely with removable VOD absent;
- absence must not crash or block the control API;
- VOD absence appears as an unavailable/empty dynamic library, not deletion;
- stale saved/Continue Watching source attempts fail cleanly;
- reinsertion requires no desktop/file-manager activation;
- normal client refresh/access automatically repopulates the library;
- Continue Watching identity survives unplug/reinsert;
- repeated unplug/reinsert transitions are supported.

Runtime acceptance sequence on 2026-09-16:
`connected -> unplug -> empty VOD -> reinsert -> Continue Watching/playback ->
unplug again -> empty VOD`, with successful onn refresh at every transition.

This storage seam is closed unless new evidence shows a regression.
<!-- PRIVYHUB_D100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE:MEMORY:END -->

<!-- PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1:MEMORY:BEGIN -->
## Do not dereference a missing systemd automount to test presence

For UUID/label/device-backed removable VOD, check backing-device presence first using the fstab mapping plus `/dev/disk/...`. If absent, return unavailable without `resolve()`, `exists()`, `stat()`, `open()`, or other access under the automount. If present, normal path access may activate the automount. Keep media-server startup independent of removable VOD. Never log raw device identifiers.
<!-- PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1:MEMORY:END -->

### Layered predecessor receipts must merge by actual installation chronology

When uncommitted development patches overlap files, merge expected post-state
using actual successful-receipt chronology, not arbitrary required/optional
grouping. The newest installed receipt is authoritative for an overlapping path.

<!-- PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1:MEMORY:BEGIN -->
## Removable storage OSError is library unavailability, never control-API failure

Linux automount/device states can make `Path.exists()`, `Path.is_dir()`,
`iterdir()`, stat calls, or path resolution raise `OSError` such as `ENODEV`
when removable storage is absent or disappears mid-scan.

Dynamic-media rule:
- catch filesystem `OSError` at the dynamic scanner boundary;
- return no dynamic children for that request;
- do not publish a partially built dynamic source index;
- keep `/sources` and the rest of the companion alive;
- stale saved source IDs may return controlled not-found/unavailable responses;
- when storage returns, a fresh scan restores the same logical IDs.

Do not interpret a missing removable library as authoritative library deletion.
<!-- PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1:MEMORY:END -->

<!-- PRIVYHUB_D097_VOD_APPLIANCE_MODE:MEMORY:BEGIN -->
## External VOD appliance mode: read-only normal operation, automount always active

For removable bulk VOD media on the Linux appliance:

- keep the UUID-based systemd automount active continuously, including while
  the disk is physically absent;
- mount the normal VOD library read-only;
- do not stop the automount as part of normal unplugging;
- do not depend on desktop `/media/<user>/<label>` mounts or file-manager
  activation;
- after reinsertion, normal VOD access triggers the mount and dynamic rescan.

User-facing normal workflow:
`stop playback -> unplug -> plug back later -> open/refresh VOD`.

Write/ingest operations are a distinct maintenance mode. If PrivyHub later
writes/rips directly to this storage, provide an explicit writable maintenance
workflow plus a client-accessible safe-disconnect action.
<!-- PRIVYHUB_D097_VOD_APPLIANCE_MODE:MEMORY:END -->

<!-- PRIVYHUB_D096R3_PROBE_LISTENER_LIFECYCLE:MEMORY:BEGIN -->
## Lifecycle acceptance should test listeners/process ownership, not raw bind reuse

For PrivyHub managed-process teardown, the meaningful acceptance boundary is:
- managed process exited;
- no matching PrivyHub process remains;
- no LISTEN socket remains on owned service ports.

A raw `bind()` test can remain false briefly after process exit because of TCP
socket state and therefore must not be used as the primary lifecycle classifier.

Also, classification return codes must compare the exact success token. Never
use a suffix test when the failure token contains that same suffix, as with
`NOT_CONFIRMED`.
<!-- PRIVYHUB_D096R3_PROBE_LISTENER_LIFECYCLE:MEMORY:END -->

<!-- PRIVYHUB_D096R2R1_PROBE_INSTALLER_PRESTATE:MEMORY:BEGIN -->
## Layered patch pre-state must validate the full uncommitted patch stack

When development patches are installed but intentionally not committed yet,
a follow-up patch cannot validate only its immediate predecessor receipt if
older installed patches still own legitimate tracked changes.

For a layered stack:
- union all still-active predecessor post-state paths;
- if multiple receipts contain the same path, the newest receipt is
  authoritative for that path;
- verify exact hashes against that merged expected state;
- allow no other tracked/staged modifications.

D-096R2R1 applies this to D-096 + D-096R1.
<!-- PRIVYHUB_D096R2R1_PROBE_INSTALLER_PRESTATE:MEMORY:END -->

<!-- PRIVYHUB_D096R1_STORAGE_DEVICE_DISCOVERY:MEMORY:BEGIN -->
## Do not infer backing block devices from automount pseudo-sources

On the Linux prototype, `findmnt -T <mounted-media-path>` can report a synthetic
systemd automount source such as `systemd-1`. That value is not a block device
and must not be passed to `blkid`.

For stable removable-storage identity:
1. access/stat a real file or directory on the mounted filesystem;
2. read its filesystem device number (`st_dev`);
3. convert to major:minor;
4. map major:minor to a real block device with `lsblk`;
5. use that `/dev/...` device for UUID lookup.

D-096R1 makes this the authoritative storage-device discovery rule.
<!-- PRIVYHUB_D096R1_STORAGE_DEVICE_DISCOVERY:MEMORY:END -->

<!-- PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE:MEMORY:BEGIN -->
## Bulk VOD physical storage is separate from the logical `/vod` namespace

D-096 establishes the storage abstraction needed by the Linux appliance.

Logical media identity:
- catalog paths remain `/vod/...`;
- generated dynamic VOD IDs remain based on logical relative paths;
- moving physical storage must not change source identity or Continue Watching
  ownership merely because the mount path changed.

Physical storage:
- default: project `media/vod`;
- optional local override: ignored `data/storage.json` with absolute `vod_root`;
- Linux appliance setup may mount a filesystem by stable UUID at
  `/mnt/privyhub-media` and point `vod_root` into that filesystem.

Serving:
- internal `media/live` remains under the project media root;
- Linux range server maps only `/vod/...` to the configured VOD physical root.

Availability:
- configured VOD root may be temporarily absent;
- companion startup must still succeed;
- API reports configured/mode/available explicitly;
- absent storage is an availability condition, not authoritative library
  deletion;
- dynamic rescanning repopulates the same logical IDs when storage returns.

Mount ownership:
- do not depend on `/media/<user>/<label>` or a file-manager click;
- use stable filesystem identity for appliance mounting;
- keep raw UUID machine-local; do not place it in tracked project files.
<!-- PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE:MEMORY:END -->

<!-- PRIVYHUB_D094_EXTERNAL_STORAGE_REMOUNT:MEMORY:BEGIN -->
## External storage: stable mount ownership is separate from PrivyHub rescanning

D5 runtime testing established that an external drive may be physically present
after reinsertion while still unmounted until the Linux desktop/file manager
activates it.

Once mounted, the existing VOD symlink becomes valid and PrivyHub dynamically
repopulates the library without a companion restart.

Durable rule:
- do not depend on `/media/<user>/<label>` desktop automount behavior;
- do not require opening the drive in a GUI;
- establish deterministic OS-level mount ownership for appliance operation;
- configure PrivyHub against a stable media-root path;
- represent configured-root unavailable separately from a genuinely empty media
  library;
- reuse the existing dynamic rescan path for automatic recovery after storage
  returns.

This narrows the D5 storage problem: scanner recovery is validated; stable mount
and explicit availability semantics remain.
<!-- PRIVYHUB_D094_EXTERNAL_STORAGE_REMOUNT:MEMORY:END -->

<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:MEMORY:BEGIN -->
## D5 external VOD runtime validated through normal onn UX

D-092 fixed the mismatch between dynamic VOD discovery and source-start health
for scanner-mediated symlinks to external storage.

Runtime validation on 2026-09-16 established:
- source-start HTTP 200 / ready true for the representative external movie;
- the movie plays normally on the onn;
- Continue Watching works.

Therefore the temporary external-drive VOD path is viable for Prototype 1.

Do not reinterpret this as the final storage architecture. The symlink remains
temporary. D5 still requires a configurable bulk-media root independent of the
repo/system disk, with stable content identity and clean handling of an
unavailable external root.

Checkpoint history:
- D-093 and D-093R1 both rolled back cleanly for installer-only documentation
  validation defects;
- D-093R2 is the authoritative runtime-validation checkpoint.

Do not reopen the D-092 source-start defect without contradictory runtime
evidence.
<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:MEMORY:END -->

<!-- PRIVYHUB_D092_DYNAMIC_VOD_SYMLINK_HEALTH:MEMORY:BEGIN -->
## Dynamic VOD discovery and source-start health must agree on scanner-mediated symlinks

D5 diagnosed a specific inconsistency:
the media-directory scanner can enumerate files beneath a symlinked directory and
the range server can serve the resulting lexical URL path, but pre-D-092
`_vod_is_healthy()` rejected the same source because `_filesystem_path` had
already been resolved outside project `MEDIA_ROOT`.

D-092 permits external resolution only for `_dynamic == True` sources generated
by the trusted scanner, and only when:
- the public playback path is lexically relative/safe beneath `MEDIA_ROOT`;
- no `..` component is present;
- the lexical path resolves to the exact scanner-recorded `_filesystem_path`.

Static/configured VOD continues to require resolved containment beneath
`MEDIA_ROOT`.

This is a narrow compatibility fix for the current temporary external-storage
arrangement, not the final configurable-media-root architecture.
<!-- PRIVYHUB_D092_DYNAMIC_VOD_SYMLINK_HEALTH:MEMORY:END -->

<!-- PRIVYHUB_D091_D5_MEDIA_BASELINE:MEMORY:BEGIN -->
## D5 external-VOD host path is healthy; symlink is diagnostic, not architecture

The Prototype-1 external movie disk is currently exposed under the project VOD
tree through a directory symlink.

Runtime measurement proved the full host path for a representative movie:
external filesystem -> symlink -> dynamic catalog -> direct Linux read ->
port-8000 HTTP Range, including a valid HTTP 206 response.

Therefore do not diagnose the current onn playback error as an external-drive
permission, exFAT-readability, symlink-resolution, catalog, or host Range-server
failure without contradictory evidence.

Architectural rule remains:
- do not make a symlink the product storage abstraction;
- D5 should provide a configurable bulk-media root independent of the project
  tree;
- preserve media/library identity across later migration to dedicated storage;
- temporary external-root absence must not mean authoritative library deletion.

Separate D5 portability seam:
browser and camera sources still use PowerShell runners and require Linux-native
runner work later in D5.
<!-- PRIVYHUB_D091_D5_MEDIA_BASELINE:MEMORY:END -->

<!-- PRIVYHUB_D090_D4_LINUX_GAMES_ACCEPTANCE:MEMORY:BEGIN -->
## D4 Linux Games parity accepted with explicit no-fixture gaps

On 2026-09-16 the final Linux Games normal-use regression passed for every
available representative path:

- SNES normal launch/gameplay/End;
- PS1 video/audio/controller, pause/frozen preview, Save/Load, resume, End;
- cheat profile;
- IPS mod profile;
- named A8 input profile;
- restart/recovery after repeated teardown;
- previously validated PS1 four-player/multitap behavior.

Classification:
`D4_FINAL_GAMES_REGRESSION_CONFIRMED_WITH_NO_FIXTURE_SKIPS`

Coverage rule remains authoritative:
zero installed fixtures means **skipped**, not runtime validated.

At D4 acceptance:
- NES: 0 local fixtures -> not Linux runtime validated;
- Genesis: 0 local fixtures -> not Linux runtime validated;
- SNES: runtime exercised and accepted;
- PS1: extensively runtime exercised and accepted.

Do not reopen validated D4 controller/multitap/lifecycle paths without new
contradictory evidence. Phase-D execution moves to D5 media/server restoration.
<!-- PRIVYHUB_D090_D4_LINUX_GAMES_ACCEPTANCE:MEMORY:END -->

<!-- PRIVYHUB_D089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT:MEMORY:BEGIN -->
## D5 bulk-media storage rule

For the current Linux Prototype 1, bulk VOD/movie files are expected to live
temporarily on an external hard drive because the internal system disk is small
relative to the media library.

Durable architecture rule:

- bulk media storage is a configurable storage root, not an intrinsic project
  directory;
- do not copy large VOD assets into PrivyHub runtime/project storage merely to
  make them available;
- keep small catalog, metadata, cache, configuration, and runtime state internal
  where practical;
- temporary external-storage absence must fail cleanly and must not by itself be
  interpreted as library deletion;
- preserve stable media/library identity across storage-path changes where
  practical;
- the external-drive deployment is temporary infrastructure, so D5 must not
  encode USB/removable-disk quirks into the long-term architecture.

The intended future transition is external disk -> dedicated server/storage
infrastructure without replacing the VOD/media model.
<!-- PRIVYHUB_D089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT:MEMORY:END -->

<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:MEMORY:BEGIN -->
## Linux PS1 multitap parity is runtime validated

On 2026-09-16 the user confirmed Crash Bash with Multitap On launches correctly,
Players 3/4 are available, and all four remotes independently control the four
players.

Durable interpretation:
- Linux reproduces the previously validated Windows Port-1 multitap behavior;
- D-087's XDG/user RetroArch Config-root adapter is correct;
- D-087R1's external-path metadata fix is correct;
- PS1 multitap is no longer an active Linux regression;
- lower PHI1/uinput/udev/A8 controller paths remain preserved and accepted.

Next Games work is broad normal-use D4 regression/acceptance, not another
multitap-specific patch.
<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:MEMORY:END -->

<!-- PRIVYHUB_D087R1_LINUX_PS1_MULTITAP_METADATA_PATH:MEMORY:BEGIN -->
## External RetroArch paths must not be forced repo-relative

Linux RetroArch's XDG/user Config tree is intentionally outside the PrivyHub
repository. Once an external path is selected and validated against its trusted
Config root, metadata/logging must not subsequently call
`relative_to(project_root)` on it.

PS1 multitap `options_file` metadata:
- Windows portable runtime: retain existing project-relative form;
- Linux: `retroarch-config/...`, relative to the trusted RetroArch Config root.

Do not encode a specific Linux home directory into product metadata.
<!-- PRIVYHUB_D087R1_LINUX_PS1_MULTITAP_METADATA_PATH:MEMORY:END -->

<!-- PRIVYHUB_D087_LINUX_PS1_MULTITAP_CONFIG_PATH:MEMORY:BEGIN -->
## RetroArch Config-directory portability rule

Do not assume RetroArch's `config/<core>/*.opt` tree is adjacent to the emulator
executable on every host.

- Windows portable runtime: `<retroarch executable dir>/config`
- Linux AppImage: `$XDG_CONFIG_HOME/retroarch/config` when set, otherwise
  `~/.config/retroarch/config`

PS1 multitap's content-specific `.opt` adapter must resolve this host Config
root before locating/copying `Beetle PSX HW.opt`.

A failure in this pre-launch materialization layer does not invalidate the
runtime-validated PHI1/uinput/udev/A8 controller path.
<!-- PRIVYHUB_D087_LINUX_PS1_MULTITAP_CONFIG_PATH:MEMORY:END -->

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:MEMORY:BEGIN -->
## Linux controller parity accepted; multiplayer remains separate

On 2026-09-16, after D-085, the user tested three different games using three
different input profiles and reported all three ran correctly.

Durable interpretation:

- Linux PHI1 -> uinput -> RetroArch udev gameplay input is runtime accepted for
  the tested single-game/profile paths.
- The D-085 `ABS_HAT0X/Y` -> RetroArch `h0*` correction is runtime validated.
- Default RetroArch autoconfig and named A8 profile application both have
  integrated gameplay evidence.
- D-084's platform-aware A8 adapter is retained, with D-085's Linux hat
  correction authoritative over D-084's initial D-pad table.
- Earlier D-076 host-side "configured" evidence must not be mistaken for
  gameplay acceptance; D-085 supplies the missing gameplay acceptance.

PS1 multitap/multiplayer is a separate active Linux regression. Windows Phase A
proved the intended behavior, including CTR Port-1 multitap and four independent
players. Linux must reproduce that behavior without changing the now-validated
single-player/default/A8 controller path.
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:MEMORY:END -->

<!-- PRIVYHUB_D085_LINUX_UDEV_HAT_MAPPING:MEMORY:BEGIN -->
## Linux RetroArch udev hat rule

Do not derive RetroArch `udev` autoconfig tokens directly from Linux
`/dev/input/js*` axis indexes.

The PrivyHub uinput D-pad is correctly emitted as `ABS_HAT0X/ABS_HAT0Y`.
For RetroArch's `udev` frontend those directions must be bound as:
`h0up`, `h0down`, `h0left`, `h0right`.

The prior `input_up_axis = "-7"` / `input_left_axis = "-6"` form came from the
Linux joystick API measurement and was a frontend-translation error.

Keep the validated non-hat Linux layout unchanged:
- left stick axes 0/1;
- LT/RT axes 2/5;
- right stick axes 3/4;
- canonical face/shoulder/select/start/thumb button mapping.

Validation-boundary rule: RetroArch reporting a controller "configured" proves
profile matching/enumeration, not that every gameplay binding in that profile is
correct. Linux controller parity requires actual onn gameplay validation.
<!-- PRIVYHUB_D085_LINUX_UDEV_HAT_MAPPING:MEMORY:END -->

<!-- PRIVYHUB_D084_LINUX_A8_PLATFORM_ADAPTER:MEMORY:BEGIN -->
## A8 portability rule — platform-neutral profiles, platform-specific RetroArch binds

A8 profile JSON is intentionally host-agnostic: sources such as `a`, `x`,
`right_stick_left`, and `l2` mean physical/canonical controller controls, not
RetroArch numeric button or axis indices.

The final A8 session adapter must translate those canonical tokens through the
active host controller frontend:

- Windows ViGEm/XInput uses the established A8 XInput tables.
- Linux PrivyHub uinput/udev uses the measured Linux joystick layout represented
  by `data/games/retroarch/autoconfig/udev/PrivyHub Virtual Gamepad P1.cfg`.

Never reuse Windows numeric XInput indices as Linux udev indices merely because
PHI1/XUSB semantics upstream are identical. D-076 preserved semantic transport,
not frontend numbering.

The immutable `Default` A8 profile still emits no explicit gameplay binds and
continues to rely on the host-specific RetroArch autoconfig.
<!-- PRIVYHUB_D084_LINUX_A8_PLATFORM_ADAPTER:MEMORY:END -->

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:MEMORY:BEGIN -->
## D4 Linux post-migration durable facts — 2026-09-16

### Persistent Linux controller prerequisites are resolved

`uinput` must be loaded persistently at boot, not merely configured by a udev
rule. The validated development host uses:

`/etc/modules-load.d/99-privyhub-uinput.conf`

with `uinput`, plus the project ownership rule for `/dev/uinput`. After reboot
the device ownership is correct and the PrivyHub user retains the required
realtime-priority allowance. Treat the older "persistent uinput / RT priority
still required" bullets as superseded by this evidence.

### Controller fault boundary

If buttons work and live Linux event monitoring shows changing `EV_ABS` values
for `ABS_X`/`ABS_Y`, do not return to Android transport, network transport,
uinput permissions, or analog-generation code by default. The current PS1
movement failure is isolated to RetroArch/core/session controller mode and
mapping behavior.

### rtw88 LPS is not the primary current stream cause

A run with ordinary LPS successfully disabled still produced severe socket
pressure (`SndbufErrors`, `RcvbufErrors`, and audio send errors). The repeated
rtw88 LPS fault is genuine but did not explain the stream failure by itself.
Do not productize LPS-off as the primary fix without new evidence.

### Temporary Windows router and ExpressVPN

The Windows PC is a development routing bridge, not the intended PrivyHub
network architecture. ExpressVPN has two independently observed effects:

1. its `expressvpn-pkf` binding on physical adapters can block forwarded
   Wi-Fi-to-Ethernet traffic;
2. even with those physical bindings disabled, an active VPN moves Windows'
   Internet route to the ExpressVPN interface, while Linux-forwarded Internet
   traffic does not successfully traverse that VPN path.

Local Linux-to-Windows reachability remains healthy in the second case. This is
a temporary-topology limitation, not a Linux/PrivyHub defect. Defer further
work; disconnect ExpressVPN when the Linux development host requires upstream
Internet.

### Android signing migration is separate from runtime behavior

`INSTALL_FAILED_UPDATE_INCOMPATIBLE` during Linux APK installation was traced to
different Android signing certificates between the already-installed package
and the Linux-built APK. Treat signing migration separately from game/runtime
debugging.

### Unresolved observations are not conclusions

A Linux hard freeze observed after a paused/stale game stream does not establish
a memory leak, GPU fault, or driver root cause without supporting kernel/runtime
evidence. Preserve the observation and reopen only if it recurs with measurable
evidence.

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:MEMORY:END -->

<!-- D4_LINUX_HANDOFF_FIX_01_MEMORY -->
## D4 Linux game handoff durable facts — 2026-09-15

- Linux Android build baseline is validated with the project unchanged before the D4 handoff patch.
- `load_state()` deliberately verifies RetroArch remains paused after loading during launch; a lost Android HTTP response can strand a correctly loaded session in the safe paused state.
- Require `host_window_policy.window_found` only when `host_window_policy.supported` is true.
- Retry only idempotent load-state transport failures, once; do not generalize to launch/save/end POSTs.
- User-visible game networking errors must redact literal IPv4 addresses.


<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15 -->

This file contains durable facts and rules, not chronological patch history.
Detailed history belongs in `memory/`, evidence in `evidence/`, and superseded
states in Git/history. Current local source and fresh runtime evidence always
outrank this summary.

## Mission and trust model

PrivyHub is a local-first, privacy-preserving, modular smart-home/media system.
The home Opal is the PrivyHub network/trust domain; the ordinary household
network is upstream connectivity, not the trusted device domain. The architecture
moves from the current inexpensive onn Android TV client and prototype host
toward inexpensive Linux-capable server hardware and additional trusted clients
without mandatory cloud, subscriptions, or proprietary infrastructure.

Local deterministic control is the baseline. Optional external AI providers are
future explicit integrations only, with data minimization and no silent fallback.

## Development position

- Phase A Games/emulation: **COMPLETE / PUSHED**.
- Phase B diagnostics/clean-native baseline: **COMPLETE / PUSHED**.
- Phase C adaptive streaming: **PAUSED AT WINDOWS PORTABILITY BOUNDARY**.
- Phase D Linux migration/native Linux baseline: **ACTIVE**.
- After D: resume unfinished C on Linux, then Phase E Linux
  characterization/optimization, Phase F media/VOD/Live TV, Phase G remote.

Windows Phase-C evidence remains useful input but is not a Linux product
constant. Automatic bitrate adaptation is not implemented.

## Games and emulator baseline

RetroArch is the managed frontend. Supported/configured families are NES,
SNES, Genesis, and PS1. PS1 has the strongest runtime coverage; SNES has runtime
coverage; NES and Genesis support/configuration must not be called runtime
validated without a representative local fixture.

Stable user-facing behaviors include:

- Save/Load and protected normal save/state namespaces;
- Pause/Resume/End lifecycle;
- isolated cheats/mod profiles;
- A8 controller profiles;
- four-player controller routing;
- PS1 manual Port-1-only Multitap On/Off;
- local metadata/art and direct game launch.

PrivyHub's PS1 local-player ceiling is four. Do not auto-enable multitap from
metadata.

User ROM/ISO/BIOS/firmware/keys remain outside Git and support bundles.

## Native stream contracts

The client-facing native stream remains H.264 over RTP-sized UDP with the
existing XOR FEC framing and Android hardware AVC decoding. The reference
profile is `native_game_720p60_reference`:

- 1280x720;
- 60 fps;
- 7000 kbps reference/max;
- GOP 15;
- B-frames 0;
- FEC group size 8.

Portable profile semantics are separate from backend-specific capture/encoder
policy, RTP payload type, packet size, ports, audio, controller protocol, and
telemetry cadence.

C2 `privyhub_stream_telemetry_v1` reuses the existing 2-second client-health path
and adds measurement-only receiver jitter, control-path RTT, signed decoder
queue-depth change, and sender/FEC pressure timing. Do not add a second hot-loop
sampler when existing instrumentation can answer the question.

## Windows Phase-C evidence

The Windows native path is:

`WGC -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`.

Validated fixed bitrate levels were 7000, 6000, and 5500 kbps; 5000 kbps was
runtime tested and rejected because focused play showed more steady-state visual
stutter. These values are Windows/test-environment evidence only.

The backend-neutral `video_only_restart` actuator is bidirectionally functional
but not acceptable for seamless automatic gameplay adaptation: the measured
restart interruption is roughly one second. Preserve it for diagnostics,
startup/manual recovery, fallback, or backends without a better mechanism.

Startup stabilization is runtime validated. Gameplay remains paused until fresh
receiver/decoder readiness evidence passes. Automatic adaptation freezes while
stabilizing or paused.

Unfinished Phase C must resume on Linux: low-interruption bitrate actuation and
automatic controller, adaptive FEC or explicit deferral, 1080p60
characterization, generalized source abstraction, and final Phase-C checkpoint.

## Linux host architecture — D073 through D078

The Linux reference prototype uses Debian 13 on Renoir `amdgpu`.

Durable Linux facts:

- VAAPI H.264 encoding works on the Renoir render node with stock Debian FFmpeg.
- Exact X11 window capture using `x11grab -window_id` works for real RetroArch
  gameplay. The target must remain mapped; minimizing/unmapping kills exact-window
  capture, while ordinary occlusion does not.
- The project-owned RetroArch 1.22.2 Linux AppImage and required FCEUmm, bsnes,
  BlastEm, and Beetle/Mednafen PSX HW Linux cores load successfully.
- Existing `EmulatorManager` readiness, launch, loopback control, save flush, and
  graceful shutdown work on Linux. Preserve that lifecycle/control surface.
- Linux native video is intentionally single-process:
  `owned X11 window -> FFmpeg x11grab -> VAAPI H.264 -> loopback RTP -> existing FEC relay`.
  Do not create a Linux WGC-equivalent raw-frame bridge.
- Linux process audio uses the EmulatorManager-owned RetroArch PID to identify
  one PulseAudio sink-input, move it to a dedicated temporary PrivyHub sink, and
  capture the monitor at 48 kHz stereo.
- PHA1 remains PCM S16LE stereo, 48 kHz, 240 frames/5 ms, with the existing
  16-byte v1 header.
- Under active RetroArch, the Linux PHA1 sender thread must obtain `SCHED_RR`
  priority 1 before emission. If that policy cannot be acquired, fail the Linux
  audio subpath rather than silently use the known-jittery fallback.
- Canonical PHI1/XUSB state remains host-independent. Linux converts it to four
  `evdev.UInput` gamepads; Windows retains ViGEm VX360.
- Linux uinput mapping and four project-owned RetroArch udev autoconfig profiles
  are validated. The generated Linux session config rewrites the portable
  project-relative autoconfig directory to its absolute project-owned path.
- D-077 adds trusted platform-aware runtime/core selection while preserving the
  Windows descriptor as the base mapping.
- D-078 makes companion media-server startup platform-aware: Windows keeps the
  PowerShell wrapper; Linux launches `companion/range_server.py` directly.

Temporary development ACL/RT-priority setup is not the production permission
model. Persistent service-scoped `/dev/uinput` access and `LimitRTPRIO=1` (or
equivalent) remain required. Never grant broad `CAP_SYS_NICE` to the general
Python interpreter.

## Integrated Linux/onn boundary

The first integrated Linux/onn PS1 run proved that the normal product path can:

- select the Linux runtime;
- launch managed RetroArch;
- load an existing save;
- create Linux virtual controllers;
- discover the exact managed X11 window;
- encode the intended native stream near 60 fps with VAAPI.

Therefore the current integrated failure is not evidence that RetroArch,
exact-window capture, or VAAPI encode is broken.

A separate Android compatibility bug prevents automatic stream entry on Linux:
`MainActivity` still requires the Windows-only
`host_window_policy.window_found`. Manual entry proves the Linux backend can
subsequently find the window. Treat this as a confirmed handoff bug ready for a
narrow fix.

The integrated PS1 run also reported missing `scph5501.bin`. Restore
user-provided BIOS content before final PS1 acceptance; it was not the transport
failure cause.

## Representative transport evidence

The old Prototype-1 UDP pathology has now been reproduced on the representative
Linux + home Opal + onn path while idle and in both directions.

Linux -> onn idle Test A:

- 3993 successful unique sends;
- zero unique loss;
- 2626 same-stamp duplicate Android arrivals;
- Android kernel arrival timing strongly bursty/gapped;
- only 7 Linux `SndbufErrors` and zero `RcvbufErrors`.

onn -> Linux idle Test B:

- 4000/4000 Android sends successful;
- 3894 unique Linux arrivals;
- 106 unique losses;
- 476 same-stamp duplicates;
- strong receive burst/gap transformation;
- Linux sender-buffer errors are not involved in this direction.

Durable conclusions:

- game/native-stream load is not required for the base pathology;
- a Linux-only sender implementation cannot explain the bidirectional result;
- production `SndbufErrors`/`RcvbufErrors` under game load amplify an already
  abnormal path but are not required for it;
- do not normalize large same-stamp duplicate delivery as ordinary Wi-Fi
  behavior;
- the unresolved region is shared network/radio/driver infrastructure until a
  lower-boundary measurement proves otherwise.

## Opal/router diagnostic disposition

Router-localization work established useful bounds but did not identify the
root duplicating component.

Validated evidence:

- Linux and onn are bridged through the home Opal wireless path.
- Ordinary `tcpdump`/AF_PACKET observations on both radio interfaces and on
  `br-lan` were completely blind during confirmed synthetic endpoint traffic.
- Disabling exposed OpenWrt software and hardware flow-offload flags did not fix
  transport and did not restore capture visibility; do not productize
  acceleration-off as a workaround.
- Proprietary Siflower FMAC/switch/HNAT components are present.

D083 and D083R1 are **invalid as networking evidence**. The first collected too
few counter samples and masked analyzer failure; the revision depended on
`nohup`, which the router does not provide. A smoke classifier also contradicted
raw `/proc/mounts`; raw evidence wins.

D082 is the last valid router-boundary result. The Opal/Siflower reverse-
engineering branch is paused. Do not continue by default. Re-enter only for a
bounded product-level measurement that can change a decision, or move the
transport discriminator to a different representative network/router.

## Diagnostics and evidence rules

Phase B diagnostics are stable and include health/resource status, Android
client feedback, corrected decoder/network classifier semantics, bounded event
history, Diagnostics/Self-Test UI, sanitized support bundles, and bounded manual
retention.

Rules:

- raw measurements outrank classifiers;
- stale-output shedding alone is informational unless decoder-local failure is
  present;
- do not infer success from `git status` when a dedicated receipt/probe exists;
- do not suppress startup stderr when process startup is the hypothesis;
- diagnostic runners fail closed on missing/insufficient evidence;
- do not turn an unproven diagnostic hypothesis into architecture.

## Repository and patch discipline

Commit source/configuration, durable engineering memory, reusable diagnostics,
and curated/sanitized evidence. Keep ROMs/ISOs, saves/states, emulator runtimes,
ordinary logs, patch backups, APK/build output, private ADB target cache, media
libraries, and raw network-bearing evidence out of Git.

Meaningful patches must verify predecessor state, reject wrong state before
modification, back up changed files, validate installed output, run applicable
compile/build checks plus `git diff --check`, and restore exact predecessor bytes
on post-write failure. Exit code is the authoritative command success signal;
warning text alone is not failure.

Every meaningful patch updates the affected durable-memory files and declares
`durable_memory_updated: true`.

## Privacy and network handling

Never ask the user to provide or paste IP addresses. Diagnostics may discover
addresses locally when required, but must not print or persist them in
shareable evidence. Overlay transport and future PrivyHub application
authorization are separate; source/request IP is not durable client identity.

## Deferred product work

- Linux/Opal transport root cause: paused after D083 closeout; re-entry condition
  is bounded product value or a different representative network path.
- Automatic C3 bitrate adaptation and C4 adaptive FEC: resume on Linux only.
- 1080p60 and generalized source abstraction: remaining Phase C on Linux.
- Media/VOD/Live TV polish: Phase F.
- Secure remote/portable-client foundation: Phase G; Tailscale is a first
  candidate, not a permanent dependency.
- Extended emulation/user-content import: Phase H.
- Broader home infrastructure: Phase I.
- Local intelligence/voice/privacy-aware AI: Phase J.

Maintainability debt remains in large files such as `MainActivity.kt`,
`emulator_manager.py`, and `games.py`. Avoid broad refactors while behavior is
stable.

<!-- PRIVYHUB_ADB_RECOVERY_PROBE_LINUX_PARITY_2026_09_15:MEMORY:BEGIN -->
## Wireless-ADB diagnostic parity rule

On Linux, `probe_adb_wireless_recovery.py` must follow the accepted D-053
bounded recovery semantics rather than only auditing mDNS/transport counts:
private cached target -> online transport -> mDNS connect -> reconnect offline ->
one ADB-server restart and bounded retry -> only then preserved-pairing Wireless
debugging Off/On. The private target may contain a network endpoint and must
never enter shareable logs, Git, or durable memory.

<!-- PRIVYHUB_ADB_RECOVERY_PROBE_LINUX_PARITY_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_2026_09_15:MEMORY:BEGIN -->
## Wireless-ADB endpoint-lifetime rule

Treat wireless-ADB pairing identity and `IP:port` endpoint as separate lifetimes.
The paired key may remain valid while the TLS listener restarts on a different
random port. A cached endpoint is therefore disposable. Recovery may reuse a
privately known host address, discover listening ports only on that one host,
and accept a new endpoint only after paired ADB authentication plus `get-state`
validation. Never expose or persist host/port values in shareable logs or durable
memory. mDNS remains useful but is not sufficient as the sole recovery path in
the representative environment.

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_V5_2026_09_15:MEMORY:BEGIN -->
## Wireless-ADB repair fallback rule

A successful manual `adb connect` after v4 failure proves that a recovery failure
must not be equated with lost pairing. Seed private endpoint host state whenever
ADB is online, learn the device's live `/proc/sys/net/ipv4/ip_local_port_range`,
and limit stale-port search to that one host/range. If bounded recovery still
fails, prompt the local operator to repair/re-pair and retry once. The probe does
not perform pairing itself and never places host, endpoint, pairing code, serial,
or mDNS identity into shareable logs or durable memory.

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_V5_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_ADB_ENDPOINT_DEBUG_V6_2026_09_15:MEMORY:BEGIN -->
## ADB endpoint-debug rule

When automatic ADB recovery disagrees with a manually successful `adb connect`,
inspect the exact selected endpoint before changing pairing, mDNS, router, or
scan architecture again. Literal host/port output is allowed only in an explicit
local terminal debug mode and must remain excluded from shareable logs and
durable memory.

<!-- PRIVYHUB_ADB_ENDPOINT_DEBUG_V6_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_ADB_ENDPOINT_WATCH_V7_2026_09_15:MEMORY:BEGIN -->
## ADB scanner observability rule

When validating concurrent endpoint discovery, absence of a port from an
"open-candidate" log is not evidence that it was skipped. Use the explicit
watch-port instrumentation to distinguish not-in-range/not-completed from a
completed CLOSED/UNREACHABLE result. Literal endpoints remain local-only.

<!-- PRIVYHUB_ADB_ENDPOINT_WATCH_V7_2026_09_15:MEMORY:END -->
