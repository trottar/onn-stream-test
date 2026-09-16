---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Current Development State

<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:CURRENT:BEGIN -->
## D-110 D5.3 Linux EPG service/cache seam

D-109 is runtime validated.

Measured local acquisition success:
- official portable Node 24.21.0 verified and removed after diagnostic use;
- upstream EPG checkout/setup passed;
- three independent sites produced real programme data;
- setup cost: 77.42 seconds;
- disposable upstream tree: 445,831,397 bytes;
- representative uncached grabs: approximately 7-8 seconds each.

Therefore local EPG acquisition is technically viable, but rebuilding the
toolchain per request is not a viable production pattern.

D-110 adds the smallest Linux production seam:
- companion `epg` plugin behind the existing `/plugins/<plugin>/<action>` API;
- persistent rebuildable toolchain under ignored `data/epg`;
- no system Node/npm installation;
- lazy/explicit bootstrap so companion startup remains fast;
- exact feed-aware channel identity only;
- 24-hour guide-metadata cache;
- 6-hour positive / 30-minute negative programme cache;
- stale-cache fallback on refresh failure.

Android remains unchanged in D-110.

D5.3 remains ACTIVE until the D-110 endpoint/bootstrap/cache runtime probe
passes. If it passes, D-111 may connect the existing Android EPG repository to
the Linux endpoint while retaining onn local cache/offline behavior.
<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:CURRENT:END -->

<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:CURRENT:BEGIN -->
## D-109 D5.3 portable-Node acquisition diagnostic

D-108 completed cleanly with:
`D108_ENVIRONMENT_NODE_UNSUPPORTED`.

Measured host environment:
- Git 2.47.3;
- Node unavailable;
- npm unavailable.

D-108 stopped before upstream checkout, npm setup, onn snapshot, or programme
acquisition. This is an environment boundary, not an EPG acquisition failure.

Do not install Node system-wide merely to continue the diagnostic.

D-109 supplies an official checksum-verified Node 24.21.0 Linux runtime inside
temporary probe state, invokes the exact installed D-108 probe under that
temporary PATH, captures the D-108 result, then removes the portable runtime.

No production EPG architecture change until D-109 runtime evidence is reviewed.
<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:CURRENT:END -->

<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:CURRENT:BEGIN -->
## D-108 D5.3 EPG local-grabber viability

D-107 completed successfully.

Authoritative feed-aware measurements:
- built-in `iptv_org`: 3,017 meaningful IDs;
- 1,218 exact canonical guide matches (40.3712%);
- 1,475 built-in IDs have guide metadata at the base-channel level;
- current public hosted guide sources still cover only 2 canonical IDs.

Therefore D5.3 is no longer blocked by a general catalog-identity failure.
The active boundary is programme acquisition.

D-108 is diagnostic-only:
use the current upstream IPTV-org EPG grabber in disposable temporary state on a
small exact-matched sample, measure real XMLTV programme output, and remove all
temporary toolchain/cache/output state afterward.

Do not make a companion or Android production EPG architecture change until
D-108 runtime evidence is reviewed.
<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:CURRENT:END -->

<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:CURRENT:BEGIN -->
## D-107 D5.3 EPG feed-aware identity correction

D-106 completed, but its built-in sparse-coverage classification is superseded.

Valid D-106 raw measurements:
- 3,169 meaningful onn channel IDs;
- 117 synthetic `tv_stream_*` IDs;
- built-in `iptv_org` has 3,017 meaningful IDs and 2,973 overlaps with the
  current English playlist.

Invalid D-106 inference:
the probe compared composite playlist IDs directly with only guide `channel`.

Current IPTV-org contracts define stream identity as `<channel_id>` or
`<channel_id>@<feed_id>`, while API guide records expose `channel` and `feed`
separately.

D-107 is diagnostic-only and recomputes metadata coverage using canonical
`channel@feed` identity. Public hosted-source availability remains only two
channels and is unchanged by this correction.

Do not make another Android or Linux EPG production change until D-107 is
reviewed.
<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:CURRENT:END -->

<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:CURRENT:BEGIN -->
## D-106 D5.3 EPG provider/identity diagnostic

D-105 completed successfully.

Measured metadata coverage of the current onn catalog:
- 3,286 unique nonblank channel IDs;
- 89 exact guide-metadata matches (2.7085%);
- 86 English exact matches (2.6172%);
- 0 matched channels with a currently hosted XML/GZIP source.

This is too little coverage to justify a Linux-local grabber as a broad EPG
solution yet.

Important identity correction:
`TvRepository` falls back to generated `tv_stream_*` IDs when `tvg-id` is
missing, while its own `meaningfulChannelId()` logic explicitly excludes those
IDs from logical channel identity.

D-106 is diagnostic-only. It measures meaningful versus synthetic IDs by
provider and independently measures guide coverage of the built-in IPTV-org
English playlist.

No production EPG change until that split is measured.
<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:CURRENT:END -->

<!-- PRIVYHUB_D105_D5_EPG_LOCAL_SOURCE_VIABILITY:CURRENT:BEGIN -->
## D-105 D5.3 EPG upstream-availability correction

Fresh post-D-104R2 runtime evidence did **not** increase guide coverage:
- 180,681 `guides.json` rows still reduced to 2 supported XML/GZIP mappings;
- onn still held 2 EPG mappings and 0 programmes;
- those 2 mappings intersected none of the 3,286 onn TV channel IDs.

Current official IPTV-org guide-worker status corroborates the result: one
green public worker currently covers 2 channels; the other listed workers are
down with 0 channels.

Therefore the earlier D-103 `schema/format divergence` classification was too
broad. The authoritative first boundary is now upstream hosted-source
availability, not Android GZIP support.

D-104R2 remains a compatible development change but is **not D5.3 runtime
acceptance**.

Next: run D-105, which measures guide metadata/catalog identity coverage before
the `sources[]` availability filter and ranks the guide sites covering the onn
catalog. Do not make another Android EPG parser change until that evidence is
reviewed.
<!-- PRIVYHUB_D105_D5_EPG_LOCAL_SOURCE_VIABILITY:CURRENT:END -->

<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:CURRENT:BEGIN -->
## D-104 D5.3 EPG source-format compatibility repair

D5.2 diagnostic evidence is complete.

D-103 measured the first divergent boundary:
- `guides.json` fetch succeeded;
- 180,681 guide entries were returned;
- the current Android XML-only source gate accepted only 2 mappings;
- the onn EPG DB contained the same 2 mappings and 0 programmes;
- neither mapping intersected the 3,286 nonblank channel IDs in the onn TV DB.

D-104 is the narrow D5.3 repair:
- keep XML as preferred source;
- accept GZIP as a fallback source;
- detect gzip by stream magic and decompress before the existing XMLTV parser;
- version the mapping-source parser in EPG meta so the old 2-row cache refreshes
  automatically after upgrade;
- keep JSON guide parsing and fuzzy channel matching deferred.

D-103 is updated to measure the post-D-104 XML/GZIP rules.

Status after installation/build: development patch only. Runtime EPG acceptance
still requires an onn Program Guide request followed by a fresh D-103 result.

D-104 installer history: the first D-104 package rolled back before build,
commit, push, or APK installation because its post-patch validator searched
for a literal escaped `\\n` sequence in Kotlin. D-104R2 corrects only that
installer validation defect; the intended Kotlin compatibility change is
unchanged.

D-104R1 installer history: R1 also rolled back before commit, push, or APK
installation because the repository tracks `PrivyHub/gradlew` as mode `100644`,
so direct `./gradlew` execution is not permitted on Linux. D-104R2 preserves
that tracked mode and invokes the wrapper with `sh ./gradlew` instead.
<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:CURRENT:END -->


<!-- PRIVYHUB_D103_D5_EPG_INGESTION_PROBE:CURRENT:BEGIN -->
## D-103 D5.2 EPG ingestion diagnostic

D5.1 Live TV catalog/category/playback acceptance remains complete.

D5.2 is now a diagnostic-only probe:
- reproduce the current Android `guides.json` mapping parser on Linux;
- measure every acceptance/rejection stage;
- compare guide IDs with the same English IPTV-org playlist used by Android;
- when ADB `run-as` is available, inspect temporary read-only snapshots of the
  onn TV/EPG SQLite state;
- sample bounded XMLTV sources only after mapping/catalog intersection exists.

No production TV, EPG, companion, or playback behavior changes in D-103.

Next evidence:
`logs/tv/d103_epg_ingestion_probe.txt`.
<!-- PRIVYHUB_D103_D5_EPG_INGESTION_PROBE:CURRENT:END -->



<!-- PRIVYHUB_D102_D5_TV_SYNC_CHECKPOINT:CURRENT:BEGIN -->
## D-102 D5 Live TV acceptance, EPG defect, and TV-state synchronization

This is the authoritative D5 resume point as of 2026-09-16. Older D5/current
blocks below remain historical evidence and must not override this state.

### Runtime accepted

- D5 external/removable VOD storage remains **COMPLETE / runtime validated**.
- D5.1 Live TV catalog/categories and normal channel playback are
  **COMPLETE / runtime validated** on the onn client.
- The established onn TV UI survived the Linux migration.

Fresh onn `Catalog / EPG Status`:
- language: English;
- country: All Countries;
- streams: 3356;
- favorites: 22;
- reliable: 49;
- hidden: 4;
- enabled providers: 3;
- catalog refreshed: 2026-09-16 15:55:38 local;
- EPG mappings: 2;
- cached programmes: 0.

The Program Guide action exists and executes, but no tested channel currently
shows actual schedule data. Therefore EPG data is **NOT ACCEPTED**.

### Accepted architecture direction

Linux becomes the durable authority for TV **user state**. The onn retains a
local cache for responsive operation and temporary sync-outage tolerance.

Do not copy Android SQLite databases between devices. Reuse/version the existing
Android TV export/import representation as the first synchronization boundary.

Durable user intent includes, where supported by the current Android model:
providers/enabled state, favorites, favorite groups/order, manual hidden state,
custom channel profile overrides, auto-hide protection, and selected
language/country preferences.

Downloaded channel catalogs and EPG mappings/programmes are derived/cacheable
data. Runtime observations such as recent viewing and stream-health counters
need explicit merge semantics before becoming generalized multi-client
authority.

### D5 substeps

- D5.1 — **COMPLETE / runtime validated:** Live TV catalog/categories/playback.
- D5.2 — **ACTIVE / next:** diagnostic-only EPG ingestion stage probe.
- D5.3 — **PENDING:** repair first evidenced EPG divergence and validate guide.
- D5.4 — **PENDING:** finalize TV state ownership/sync contract.
- D5.5 — **PENDING:** companion durable TV state store/API.
- D5.6 — **PENDING:** onn <-> Linux state synchronization.
- D5.7 — **PENDING:** sync persistence/convergence/runtime acceptance.
- D5.8 — **PENDING:** integrated VOD + TV + EPG + diagnostics/Self-Test regression.
- D5.9 — **PENDING:** D5 checkpoint/closeout.

Immediate next step: D5.2 must measure the existing EPG pipeline from upstream
guide fetch through mapping acceptance, current catalog identity matching,
XMLTV fetch and programme matching. Make no production guide change until fresh
evidence identifies the first divergent boundary.

Scope remains bounded: do not reopen validated VOD without regression evidence;
do not port legacy browser/camera runners for D5; browser/app and camera/live
native-source work remains C6 after D7/D8. Full TV data-model/guide UX redesign
remains later media/TV work.
<!-- PRIVYHUB_D102_D5_TV_SYNC_CHECKPOINT:CURRENT:END -->

<!-- PRIVYHUB_D101R1_BROWSER_CAMERA_C6_RECLASSIFICATION:CURRENT:BEGIN -->
## D-101 browser/camera source work reclassified to C6

The D5 external/removable VOD storage seam is runtime validated.

Browser/camera work is reclassified:
- do not port the old Windows browser/camera runners merely to satisfy D5;
- finish D5 with VOD + Live TV/EPG + diagnostics/Self-Test;
- finish D7/D8 Linux baseline acceptance;
- then return to remaining Phase C work on Linux;
- C6 builds browser/app and camera/live sources on the generalized native
  capture -> profile/encoder -> transport/FEC -> client-decoder contract.

Rationale:
- browser streaming is strategically useful for the eventual stationary/headless
  server role;
- reusing the native decoder/telemetry/profile/transport infrastructure is a
  substantial improvement over the original runner path;
- the current Linux Prototype 1 has no representative camera hardware, so
  local-camera parity should not block D5;
- future onn-attached Bluetooth keyboard/mouse input is a useful C6 browser
  control target, not a D5 restoration requirement;
- broader smart-home camera/device integration remains Phase I.

Current next step:
D5 Live TV/EPG + diagnostics acceptance.
<!-- PRIVYHUB_D101R1_BROWSER_CAMERA_C6_RECLASSIFICATION:CURRENT:END -->

### D-101R1 local-roadmap correction

The earlier D-101 attempt failed before modification because its
installer incorrectly required `ROADMAP.md` at the Linux repository
root. The roadmap file reviewed in chat was uploaded reference material;
the repo's durable roadmap state is maintained in
`docs/memory/roadmap/STATUS.md`.

D-101R1 records the same accepted reclassification entirely through the
actual durable-memory/decision files and does not create or require a
new root-level roadmap file.

<!-- PRIVYHUB_D100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE:CURRENT:BEGIN -->
## D-100 external VOD hotplug runtime acceptance

The configurable/removable external-VOD storage seam is runtime validated on
the Linux Prototype-1 host and onn client.

Validated end-to-end sequence:
- external VOD connected: normal library and playback work;
- physical unplug with no Linux/file-manager interaction: Companion remains
  available and the VOD library cleanly shows no movies;
- client refresh during absence succeeds;
- reinsertion with no Linux/file-manager interaction: VOD automatically
  repopulates;
- Continue Watching reappears and resumes successfully;
- second physical unplug again produces the same clean empty-VOD state;
- client refresh succeeds at each transition.

Earlier acceptance already established:
- stable logical source identity for Aviator;
- source-start HTTP 200 while storage is present;
- logical `/vod` HTTP byte-range serving;
- managed companion lifecycle cleanup;
- absent-storage ENODEV no longer crashes catalog requests;
- absent-storage probing no longer blocks long enough to make Android report
  Companion unavailable;
- stale Continue Watching fails cleanly while storage is absent;
- media/control services remain available independently of removable VOD.

D5 storage substep status: **COMPLETE / runtime validated**.

D5 overall remains **ACTIVE**. Next:
Linux browser/camera runner restoration, then integrated
VOD + Live TV/EPG + diagnostics acceptance.
<!-- PRIVYHUB_D100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE:CURRENT:END -->

<!-- PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1:CURRENT:BEGIN -->
## D-099 nonblocking removable-VOD presence

D-098 eliminated the ENODEV traceback, but absent-drive timing proved path-based checks were still activating the missing systemd automount: `/status` took ~3s, `/sources` and stale source-start exceeded 12s, Android reported Companion unavailable, and port 8000 was not listening.

D-099 checks the configured local fstab backing device under `/dev/disk/...` before touching the VOD mount path. Absent local media now reports unavailable immediately. Configured VOD path normalization is lexical rather than filesystem-dereferencing, and the Range server starts independently of removable VOD presence. Raw storage identifiers are never logged.
<!-- PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1:CURRENT:END -->

### D-099R1 installer pre-state correction

The first D-099 installer attempt failed before modification because predecessor
post-state was merged by hard-coded required/optional groups. Optional D-097 was
applied after newer D-098 and incorrectly replaced newer hashes for overlapping
durable-memory files.

D-099R1 changes installer validation only:
- collect the latest successful receipt for each installed predecessor;
- sort those receipts by actual receipt modification time;
- merge post-state in that chronological order;
- newest installed receipt wins for overlapping files.

The D-099 production payload is unchanged.

<!-- PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1:CURRENT:BEGIN -->
## D-098 absent removable-VOD resilience

Physical hotplug exposed a production defect after the configurable external
VOD boundary:

`GET /sources` could raise:
`OSError: [Errno 19] No such device`

The exception originated in `_scan_media_directory()` when `Path.exists()` was
called on the configured external VOD root while the systemd automount existed
but the physical filesystem was absent.

Additional runtime evidence:
- Companion/catalog behavior returns when the external disk is reinserted,
  confirming the UUID mount and logical `/vod` mapping are functioning.
- A saved Continue Watching item can also reach dynamic-source resolution while
  storage is absent; that path must fail cleanly without making Companion
  unavailable.

D-098 changes only the dynamic media scanner:
- filesystem `OSError` during initial dynamic-root availability checks returns
  no dynamic children;
- filesystem `OSError` anywhere in recursive enumeration/stat/resolve aborts
  that scan and publishes no partial dynamic index;
- `/sources` remains a valid control-API response while external VOD is absent;
- a stale dynamic source id resolves to the existing controlled CatalogError
  path rather than an uncaught filesystem exception;
- the next successful rescan after reinsertion repopulates the same logical
  source IDs.

The systemd mount architecture, Android client, Games, live media, and controller
paths are unchanged.
<!-- PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1:CURRENT:END -->

<!-- PRIVYHUB_D097_VOD_APPLIANCE_MODE:CURRENT:BEGIN -->
## D-097 removable VOD appliance mode

D-096/R3 established the first-class external VOD root and validated host
playback/lifecycle.

A real unplug/reinsert exercise then showed:
- when the automount unit was manually stopped for "eject", reinsertion could
  not recover until the automount was started again;
- once the automount was restarted, the library immediately returned in the onn
  GUI and playback worked without desktop/file-manager activation.

D-097 changes the operating model:
- the systemd automount remains permanently active;
- normal external VOD media mode is read-only;
- user-session/file-manager mounting is not part of the workflow;
- normal hotplug requires no Linux login or mount command;
- with storage absent, PrivyHub remains operational and VOD is unavailable;
- reinsertion is recovered by normal access to `/sources`/VOD, which activates
  the system automount.

Normal physical procedure after D-097:
1. stop VOD playback;
2. unplug the external VOD disk;
3. later plug it back in;
4. refresh/open VOD on the client.

No server-side command is part of that normal procedure.

Future maintenance/write mode is separate: adding/ripping media should use a
deliberate writable workflow and eventually expose a PrivyHub/onn "Safely
disconnect storage" action rather than relying on Linux shell access.
<!-- PRIVYHUB_D097_VOD_APPLIANCE_MODE:CURRENT:END -->

<!-- PRIVYHUB_D096R3_PROBE_LISTENER_LIFECYCLE:CURRENT:BEGIN -->
## D-096R3 listener-based lifecycle acceptance

Follow-up diagnostics after the D-096R2R1 probe established:
- no PrivyHub companion/range-server processes remained;
- port 8765 had no LISTEN socket;
- port 8000 had no LISTEN socket;
- neither port had an owning PID.

Therefore the D-096 storage/runtime lifecycle is not leaking processes or
listeners. The probe's raw bindability test was measuring a stricter socket
reuse condition than the lifecycle question.

D-096R3 changes only the probe:
- lifecycle success requires the managed companion process to exit;
- no PrivyHub companion/range-server process may remain;
- neither 8765 nor 8000 may have a LISTEN socket;
- a bounded wait remains for listener/process teardown;
- TIME_WAIT or other closed-connection state is not treated as a lifecycle
  failure;
- exit code is now based on exact classification equality, fixing the bug where
  `D096_STORAGE_BOUNDARY_NOT_CONFIRMED` incorrectly returned zero because its
  name also ended in `_CONFIRMED`.

Production media/storage code and stable mount configuration are unchanged.
<!-- PRIVYHUB_D096R3_PROBE_LISTENER_LIFECYCLE:CURRENT:END -->

<!-- PRIVYHUB_D096R2R1_PROBE_INSTALLER_PRESTATE:CURRENT:BEGIN -->
## D-096R2R1 installer pre-state correction

D-096R2 failed **before modification**.

Observed precheck rejection listed legitimate D-096 tracked changes:
- `companion/privyhub_service.py`
- `companion/range_server.py`
- `docs/memory/architecture/TV_MEDIA.md`
- `docs/memory/investigations/ACTIVE.md`
- `docs/memory/roadmap/STATUS.md`

Cause:
the R2 installer validated only the D-096R1 receipt when deciding which
uncommitted tracked files were expected. D-096R1 intentionally changed only the
storage helper and a subset of memory files, so the still-valid D-096 production
and memory changes were omitted from the allowed pre-state.

D-096R2R1 corrects installer validation only:
- load both successful D-096 and D-096R1 receipts;
- treat their post-state paths as one expected installed stack;
- for overlapping files, use the newer D-096R1 hash;
- for D-096-only files, require the exact D-096 post-state hash;
- reject any tracked/staged modification outside that combined stack.

The R2 lifecycle-aware probe itself is unchanged.
<!-- PRIVYHUB_D096R2R1_PROBE_INSTALLER_PRESTATE:CURRENT:END -->

<!-- PRIVYHUB_D096R1_STORAGE_DEVICE_DISCOVERY:CURRENT:BEGIN -->
## D-096R1 storage-device discovery correction

The D-096 application boundary installed successfully, but the first root-level
storage configuration attempt rolled back before persistent modification.

Failure:
`blkid -s UUID -o value systemd-1`

Cause:
the helper used `findmnt -T <path>` and treated its SOURCE as the underlying
block device. With the current systemd/desktop automount stack, findmnt reported
the synthetic automount source `systemd-1` instead of the real partition.

D-096R1 changes only storage-device discovery:
- `stat()` the resolved VOD target to obtain its actual filesystem device number;
- map that major:minor identifier to the real block partition through `lsblk`;
- derive the current mountpoint from that block device's mountpoints;
- use only the real `/dev/...` partition for UUID lookup.

D-096 production media-root/range-server changes are preserved unchanged.

Runtime storage configuration must be retried before D-096 acceptance.
<!-- PRIVYHUB_D096R1_STORAGE_DEVICE_DISCOVERY:CURRENT:END -->

<!-- PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE:CURRENT:BEGIN -->
## D-096 configurable VOD storage boundary

D5 external-storage evidence now supports a first-class storage boundary.

D-095 established:
- the current external VOD filesystem is exFAT;
- it has a stable filesystem UUID;
- it is hotplug-capable;
- it is currently mounted by the desktop/user automount layer;
- systemd/systemd-mount tooling is available;
- `/etc/fstab` does not already own that filesystem.

D-096 changes the architecture so bulk VOD no longer depends on the repo-local
`media/vod/movies` symlink:
- `data/storage.json` selects an optional physical VOD root;
- default behavior remains project `media/vod`;
- logical `/vod/...` paths and generated source IDs remain unchanged;
- `media/live` remains on the internal project media root;
- the Linux Range server maps `/vod/...` to the configured VOD root;
- `/status` and `/sources` explicitly report VOD storage configured/mode/available;
- the storage setup helper discovers the current filesystem UUID locally and
  creates a stable systemd/fstab automount at `/mnt/privyhub-media`;
- raw filesystem UUID is not written to PrivyHub logs/receipts;
- the temporary desktop-path VOD symlink is removed only after stable mount and
  local storage config validate successfully.

The deterministic mount configuration uses the filesystem UUID rather than a
desktop label/path. It is `nofail` + systemd automount, so boot remains possible
when the drive is absent and later access can activate the mount when it returns.

Runtime acceptance next:
install D-096, configure the stable mount, run the D-096 managed lifecycle
probe, then test onn playback and physical eject/reinsert recovery.
<!-- PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE:CURRENT:END -->

<!-- PRIVYHUB_D094_EXTERNAL_STORAGE_REMOUNT:CURRENT:BEGIN -->
## D-094 external-storage remount behavior

Fresh D5 runtime evidence clarified the remaining external-VOD storage boundary.

Observed sequence:
1. external drive ejected;
2. VOD symlink target became unavailable;
3. `/sources` correctly returned zero VOD sources;
4. drive was physically reconnected but remained unmounted;
5. opening the drive in the Linux file manager caused the OS desktop storage
   layer to mount it;
6. the existing VOD symlink immediately became valid again;
7. PrivyHub dynamic rescanning repopulated the movie library without a companion
   restart;
8. onn movie playback worked normally again.

Interpretation:
- PrivyHub dynamic catalog recovery is already working when the configured
  filesystem path becomes available again;
- the missing behavior is deterministic OS-level storage mounting, not catalog
  rescanning;
- the appliance must not depend on a desktop file-manager click to activate
  removable storage.

Next D5 storage implementation should separate responsibilities:
- OS/service layer owns deterministic mounting at a stable path;
- PrivyHub owns explicit bulk-media-root configuration and availability state;
- unavailable configured storage must be distinguishable from an empty library;
- when the root returns, normal rescanning should repopulate automatically.
<!-- PRIVYHUB_D094_EXTERNAL_STORAGE_REMOUNT:CURRENT:END -->

<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:CURRENT:BEGIN -->
## D-093R2 D5 external-VOD runtime validation

D-092 is **RUNTIME VALIDATED** on the normal onn client path.

Validated sequence:
external movie storage -> temporary VOD symlink -> dynamic catalog ->
source-start health -> port-8000 playback -> onn Media3 -> normal playback UX.

Fresh runtime result:
- D-092 source-start probe returned HTTP 200 and `ready: true`;
- the representative external movie that previously failed at source-start now
  plays normally on the onn;
- video/audio playback is working;
- Continue Watching was explicitly tested and works.

The previous HTTP 503 `VOD source is unavailable` failure is closed.

Checkpoint-installer history:
- D-093 rolled back cleanly because it expected the wrong D5 roadmap heading;
- D-093R1 rolled back cleanly because it validated a marker that its roadmap
  insert did not contain;
- D-093R2 supersedes both failed checkpoint attempts.

Architectural status:
- the current symlink is acceptable as a temporary Prototype-1 compatibility
  path;
- it is not the permanent storage abstraction;
- the next D5 storage task is a first-class configurable external/bulk media
  root that preserves stable library identity and clean unavailable-storage
  behavior.

Other D5 work remains:
- Linux-native browser/live runner;
- Linux-native camera runner;
- integrated TV/EPG/media/diagnostics acceptance.
<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:CURRENT:END -->

<!-- PRIVYHUB_D092_DYNAMIC_VOD_SYMLINK_HEALTH:CURRENT:BEGIN -->
## D-092 dynamic VOD symlink health boundary

Fresh Android evidence classified the current VOD failure before ExoPlayer/media
fetch:

- onn POSTed the dynamic VOD source start request;
- companion returned HTTP 503;
- response error was `VOD source is unavailable`;
- no port-8000 media request followed.

Root cause is in companion `_vod_is_healthy()`:
dynamic scanning records the resolved target in `_filesystem_path`, then health
validation requires that resolved path to remain beneath project `MEDIA_ROOT`.
A directory symlink to external storage therefore passes discovery and HTTP Range
serving but is rejected during source-start health validation.

D-092 changes only this dynamic-source health rule:
- scanner-generated dynamic VOD validates through its lexical catalog path under
  `MEDIA_ROOT`;
- that path must resolve to the exact `_filesystem_path` recorded by the scanner;
- static/configured VOD retains the existing resolved `MEDIA_ROOT` containment
  rule.

Next runtime gate:
restart companion, run the D-092 source-start probe, then retry Aviator on the
onn if source-start is confirmed.
<!-- PRIVYHUB_D092_DYNAMIC_VOD_SYMLINK_HEALTH:CURRENT:END -->

<!-- PRIVYHUB_D091_D5_MEDIA_BASELINE:CURRENT:BEGIN -->
## D-091 D5 Linux media baseline and external-VOD boundary

D5 is ACTIVE.

Fresh read-only Linux baseline evidence:
- control API and `/sources` respond normally;
- 91 dynamic VOD sources were visible;
- an ordinary VOD byte-range request returned HTTP 206;
- diagnostics health, stream telemetry, Self-Test, and IPTV categories endpoints
  were reachable;
- Linux media-server startup remains the D-078 direct-Python path;
- browser and camera source runners remain PowerShell and are still Linux
  portability seams.

External-VOD symlink boundary evidence:
- the current `media/vod/movies` symlink resolves to mounted external storage;
- a representative movie is readable both through the symlink and resolved
  target;
- the exact movie appears in `/sources`;
- the existing port-8000 media server returns a correct one-byte HTTP 206 Range
  response for that exact movie.

Classification:
`D5_VOD_SYMLINK_HOST_RANGE_PATH_HEALTHY`.

Interpretation:
the external disk, filesystem permissions, symlink traversal, catalog generation,
and host-side Range serving are not the current playback failure boundary.

The symlink remains a temporary development arrangement, not the intended D5
storage architecture. D5 still needs an explicit configurable bulk-media root.

Immediate next diagnostic:
reproduce one failing symlinked movie on the onn and inspect only new sanitized
port-8000 access records. This distinguishes client URL/network failure from
Media3/container/codec failure.
<!-- PRIVYHUB_D091_D5_MEDIA_BASELINE:CURRENT:END -->

<!-- PRIVYHUB_D090_D4_LINUX_GAMES_ACCEPTANCE:CURRENT:BEGIN -->
## D-090 D4 Linux Games acceptance — runtime validated

D4 normal-use Games acceptance is complete on the representative Linux -> onn
path.

Fresh final regression evidence:
- Games library/search/art remained normal;
- SNES launched normally with video, audio, input, analog-to-D-pad convenience,
  and clean End/uinput teardown;
- PS1 launched normally with video/audio/input, paused frozen-preview controls,
  Save/Load, resume, and clean End/uinput teardown;
- a validated cheat-profile session passed;
- the validated IPS mod path passed;
- a non-default named A8 input profile passed;
- a fresh game launch after repeated End/cleanup cycles passed;
- D-088 four-player PS1 Port-1 multitap evidence remains accepted.

Coverage limitation:
- NES library count was 0;
- Genesis library count was 0;
- therefore neither family is claimed as Linux runtime validated by this D4 run.
  They remain configured/supported with explicit no-fixture skips.

Final classification:
`D4_FINAL_GAMES_REGRESSION_CONFIRMED_WITH_NO_FIXTURE_SKIPS`

### Immediate next Phase-D work

**D5 media/server restoration is ACTIVE / NEXT.**

Preserve the D5 Prototype-1 storage constraint: bulk VOD may live on external
storage, small PrivyHub state should remain internal where practical, and
temporary external-root unavailability must not be interpreted as library
deletion.
<!-- PRIVYHUB_D090_D4_LINUX_GAMES_ACCEPTANCE:CURRENT:END -->

<!-- PRIVYHUB_D089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT:CURRENT:BEGIN -->
## D5 storage constraint recorded before media restoration

Phase D remains at **D4 final normal-use Games regression/acceptance**.

Before D5 begins, preserve this deployment constraint:

- the current Linux Prototype 1 has a comparatively small internal system disk;
- bulk VOD/movie content will temporarily live on a simple external hard drive;
- PrivyHub must not require large media libraries to be copied into the project
  tree or internal system disk;
- catalog/metadata/cache/runtime state should remain small and internal where
  practical;
- an unavailable/unmounted external media root must be treated as storage
  unavailable, not as authoritative deletion of the library;
- D5 should keep media-root selection portable so the same library can later
  move to dedicated server/storage infrastructure without redesigning VOD.

No production behavior changes in this checkpoint.
<!-- PRIVYHUB_D089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT:CURRENT:END -->

<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:CURRENT:BEGIN -->
## D-088 PS1 multitap Linux runtime validation

D-087 + D-087R1 are now **RUNTIME VALIDATED**.

Integrated Linux -> onn acceptance:
- Crash Bash launches with PrivyHub Multitap On;
- Players 3 and 4 are available in-game;
- four physical remotes/controllers each control independently;
- the historical Windows Port-1-only multitap behavior is reproduced on Linux.

This closes the active Linux PS1 multiplayer/multitap regression. Preserve:
- host-aware RetroArch Config-root resolution from D-087;
- external Config-path metadata handling from D-087R1;
- D-085 lower controller path;
- Port-1 enabled / Port-2 disabled product semantics.

### Immediate next Phase-D work

D4 remains active only for final normal-use Games regression/acceptance across
the required PS1-and-below behavior set. After D4 is accepted, proceed to D5
media/server restoration according to `docs/ROADMAP.md`.

Do not reopen multitap or the lower controller stack without contradictory new
evidence.
<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:CURRENT:END -->

<!-- PRIVYHUB_D087R1_LINUX_PS1_MULTITAP_METADATA_PATH:CURRENT:BEGIN -->
## D-087R1 Linux multitap metadata-path correction — development patch

D-087 correctly moved Linux Beetle PSX HW core-option reads/writes to the active
XDG/user RetroArch Config directory. Runtime then exposed a second project-root
assumption later in the same function.

Observed after D-087:
- the Linux game-specific `.opt` target was correctly selected under RetroArch's
  user Config tree;
- launch then failed while serializing `options_file` because the code still
  called `target_options.relative_to(self.project_root)`.

That field is returned/logged metadata; it is not used for the file write.
D-087R1 preserves Windows project-relative metadata and represents Linux as
`retroarch-config/<core>/<game>.opt`, relative to the already-validated Config
root.

No core-option contents, multitap topology, controller, A/V, network, or
lifecycle behavior changes.

Status: **DEVELOPMENT PATCH; MULTITAP RUNTIME VALIDATION PENDING**.
<!-- PRIVYHUB_D087R1_LINUX_PS1_MULTITAP_METADATA_PATH:CURRENT:END -->

<!-- PRIVYHUB_D087_LINUX_PS1_MULTITAP_CONFIG_PATH:CURRENT:BEGIN -->
## D-087 Linux PS1 multitap core-options path — development patch

The Linux multitap failure is now classified before RetroArch startup.

Observed launch error:
`Beetle PSX HW core-options file is unavailable for multitap launch`

Targeted filesystem/config evidence:
- project-managed RetroArch config contains no explicit `rgui_config_directory`;
- Linux RetroArch's active Beetle options are under the normal user Config tree:
  `~/.config/retroarch/config/Beetle PSX HW/Beetle PSX HW.opt`;
- both multitap keys exist there and are disabled.

Root cause: `_prepare_ps1_multitap_options()` still used the Windows portable
layout `runtime executable parent / config` and required that directory to live
under the project root. That is correct for the old Windows runtime and wrong for
the Linux AppImage.

D-087 changes only host Config-root selection:
- Windows keeps executable-adjacent `config` exactly as before;
- Linux uses `$XDG_CONFIG_HOME/retroarch/config` when XDG_CONFIG_HOME is set,
  otherwise `~/.config/retroarch/config`;
- per-game `.opt` output remains constrained beneath that selected Config root;
- existing Port-1-only materialization and all controller/A-V/lifecycle behavior
  remain unchanged.

Status: **DEVELOPMENT PATCH; MULTITAP RUNTIME VALIDATION PENDING**.

Next: restart companion, enable Multitap for a known four-player PS1 game,
launch, verify Players 3/4, then verify four independent controllers.
<!-- PRIVYHUB_D087_LINUX_PS1_MULTITAP_CONFIG_PATH:CURRENT:END -->

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:CURRENT:BEGIN -->
## D-086 Linux controller parity checkpoint — runtime validated

D-085 is now **RUNTIME VALIDATED** on the representative Linux -> onn path.

User runtime acceptance after restarting the patched companion:

- three different games were launched;
- three different input profiles were exercised;
- all three ran with correct gameplay controls;
- this covers the normal/default RetroArch autoconfig path and multiple named
  gameplay-profile paths in the integrated Linux product flow.

This supersedes the earlier broad Linux controller blocker and the earlier
generic "PS1 analog controller mode" next-step language. Do not reopen PHI1,
uinput permissions, uinput control generation, RetroArch udev discovery, or the
D-pad frontend mapping without new contradictory evidence.

The confirmed Linux gameplay-input architecture is now:

`Android InputDevice -> PHI1 -> Linux uinput -> RetroArch udev -> Default/A8 gameplay profile -> core/game`

D-084 remains part of the accepted architecture: A8 source semantics are
platform-neutral and the final source-token adapter is host-specific. D-085
corrected the Linux udev hat representation inherited by both default
autoconfig and the D-084 Linux A8 adapter.

### Immediate next Phase-D work

**PS1 multiplayer / multitap parity on Linux is ACTIVE.**

The historical Windows Phase-A baseline remains authoritative for intended
behavior: manual Multitap On/Off, Port 1 enabled / Port 2 disabled, Players 3/4
available in CTR, and four independent controllers were runtime validated.

Current Linux report: multitap does not work. The exact failure boundary is not
yet classified.

Next work must use one narrow diagnostic before production changes:

1. verify the selected game's stored `ps1_multitap` override;
2. verify the generated content-specific Beetle PSX HW `.opt` contains Port 1
   enabled and Port 2 disabled;
3. verify P1-P4 Linux uinput pads are configured by RetroArch for that launch;
4. determine whether Players 3/4 become available and whether four controllers
   remain independently routed.

Do not continue broader Phase-D work until this multiplayer regression is
classified or explicitly deferred.
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:CURRENT:END -->

<!-- PRIVYHUB_D085_LINUX_UDEV_HAT_MAPPING:CURRENT:BEGIN -->
## D-085 Linux RetroArch udev D-pad correction — development patch

The controller investigation was reconstructed against the older Phase-A and
D-076 evidence instead of treating the newest summary as sufficient.

Authoritative distinction:

- Windows PHI1 -> ViGEm/XInput reached real 1P/2P/4P gameplay validation.
- D-076 Linux reached host-side managed RetroArch integration: P1-P4 device
  creation/enumeration, clean PHI1 updates, meta controls, Save/Load, and
  teardown.
- D-076's own acceptance record still listed actual gameplay controls as pending.
  Host integration was later being over-read as gameplay validation.

The exact Linux uinput measurement remains valid: the D-pad is emitted as
`ABS_HAT0X/ABS_HAT0Y`. The error was at the RetroArch udev binding boundary.
The four project autoconfigs encoded those hats as ordinary axes `6/7`.
RetroArch udev autoconfig semantics represent D-pad hats as
`h0up/h0down/h0left/h0right`.

D-085 changes only:
- P1-P4 project udev D-pad binds from `input_*_axis = +/-6/7` to
  `input_*_btn = h0...`;
- the D-084 Linux A8 source translator to use the same udev hat tokens;
- the existing A8 deterministic probe so it rejects the old Linux-axis form.

Buttons, sticks, triggers, PHI1, Android input, Linux uinput event generation,
Windows XInput behavior, PS1 Digital/DualShock selection, audio/video/networking,
and emulator lifecycle are unchanged.

Status: **DEVELOPMENT PATCH; ONN GAMEPLAY VALIDATION REQUIRED**.

First runtime discriminator after install: default-profile Crash must regain
D-pad movement. Analog behavior remains subject to the existing PS1
Digital/DualShock per-game controller mode and must not be conflated with this
D-pad correction.
<!-- PRIVYHUB_D085_LINUX_UDEV_HAT_MAPPING:CURRENT:END -->

<!-- PRIVYHUB_D084_LINUX_A8_PLATFORM_ADAPTER:CURRENT:BEGIN -->
## D-084 Linux A8 gameplay-profile adapter — development patch

Fresh source/memory reconciliation found a second controller issue distinct from
PS1 Digital-vs-DualShock mode.

A8 named gameplay profiles store platform-neutral physical control names, but
the A8.2 RetroArch adapter still translated those names with the original
Windows/XInput numeric layout. D-076 moved Linux controller output to
uinput/udev without changing A8 profile semantics. The project-owned Linux udev
autoconfig proves that Linux joystick numbering differs from XInput for X/Y,
Back/Start, triggers, right stick, D-pad, and Y-axis sign.

D-084 therefore keeps the A8 profile schema and Android editor unchanged while
making only the final RetroArch source-token translation host-specific:

- Windows -> existing XInput bindings, unchanged;
- Linux -> validated PrivyHub uinput/udev bindings.

The existing deterministic A8 adapter probe is made platform-aware and now
checks Linux face buttons, D-pad axis mapping, trigger/right-stick remapping,
legacy right-stick whole-axis mapping, and Back/Start numbering.

Status: **DEVELOPMENT PATCH; RUNTIME GAMEPLAY ACCEPTANCE PENDING**.

Next runtime check: restart the Linux companion, launch a game with an existing
custom input profile, and verify the configured gameplay permutation. Do not
change PHI1, Android controller transport, Linux uinput generation, or PS1
Digital/DualShock selection for this issue.
<!-- PRIVYHUB_D084_LINUX_A8_PLATFORM_ADAPTER:CURRENT:END -->

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:CURRENT:BEGIN -->
## D4 runtime reconciliation — 2026-09-16

**Status:** Phase D Linux migration remains active, but the newest runtime evidence
moves the immediate blocker beyond basic Linux host/network prerequisites.

Newest validated state:

- Linux companion service is reachable and normal game launch/streaming works
  after the temporary Windows-router path was corrected for ExpressVPN filter
  interference.
- `/dev/uinput` persistence is no longer an open deployment gap: `uinput` is
  loaded at boot through `/etc/modules-load.d/99-privyhub-uinput.conf`, the
  project udev ownership rule applies after reboot, and the PrivyHub account has
  the required realtime-priority allowance.
- Controller transport, Linux uinput injection, RetroArch pad discovery, and live
  `ABS_X` / `ABS_Y` analog events are all proven.
- The remaining controller issue is inside RetroArch/PS1 core controller-mode
  behavior (digital pad versus DualShock/analog session configuration), not
  Android transport, Linux permissions, uinput creation, or analog generation.
- The saved Linux/home-Opal UDP timing pathology remains a separate deferred
  transport investigation. Latest normal game streaming success does not prove
  that the older synthetic timing pathology disappeared, but it is no longer
  valid to treat basic Linux reachability or the Windows bridge as the current
  game-launch blocker.
- The repeated rtw88/LPS fault is real, but disabling ordinary LPS did not repair
  the failed stream run; do not treat LPS as the primary stream root cause.
- The Android/Linux auto-open compatibility fix is already represented by the
  current D4 handoff patch. Keep its dedicated runtime-acceptance status separate
  from the controller investigation.

### Temporary Windows/ExpressVPN bridge

The temporary topology uses Windows as the routed hop between the GL-iNet side
and Linux. `expressvpn-pkf` on the physical adapters was proven capable of
blocking that forwarded path.

Current development behavior with both physical-adapter bindings disabled:

- ExpressVPN disconnected: Windows Internet, Linux Internet, and PrivyHub local
  routing work.
- ExpressVPN connected: Windows Internet works, Linux still reaches its Windows
  gateway, but Linux Internet fails because Windows selects the ExpressVPN
  interface as its Internet route and the forwarded Linux traffic does not
  successfully traverse that VPN path.

This is **DEFERRED BY DESIGN**. It is a limitation of the temporary
Windows-as-router development topology, not a PrivyHub/Linux product defect.
Use ExpressVPN disconnected when Linux requires upstream Internet. Do not spend
more Phase-D time redesigning this bridge.

### Diagnostic precedence

Older ADB recovery diagnostics remain preserved in durable memory, but the newest
normal companion/game runtime succeeded. Do not let stale ADB probe resume notes
displace the current RetroArch analog issue unless ADB installation/recovery
actually fails again.

### Immediate next technical work

1. Narrow RetroArch PS1 controller-mode investigation only.
2. After analog movement is corrected, run the normal Linux game regression
   (launch -> video/audio/controller -> pause/resume -> Save/Load -> End).
3. Keep the saved UDP/router branch paused unless fresh evidence from normal use
   requires reopening it.
4. Restore user-provided PS1 BIOS before final PS1 acceptance if still absent.

### Do not reopen without new evidence

- ICS experimentation;
- Windows Firewall as the routed-path cause;
- Linux `/dev/uinput` permission/module-load debugging;
- Linux realtime-priority persistence debugging;
- ExpressVPN forwarding on the temporary Windows bridge;
- rtw88 ordinary-LPS tuning as the primary stream fix.

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:CURRENT:END -->

<!-- D4_LINUX_HANDOFF_FIX_01_CURRENT -->
## D4 Linux game handoff fix — development patch installed; runtime validation pending

- Unchanged Android baseline built successfully on Linux before this patch.
- PS1 slot load reached RetroArch and completed while the session remained intentionally paused; the client then lost the control response and did not finish launch handoff.
- Linux reports the legacy Windows host-window policy unsupported, so Android must not require `window_found` when that policy is unsupported.
- Patch scope: Android handoff gating, one bounded retry for idempotent load-state transport failures, and IPv4 redaction in game-facing errors.
- Next: install APK and runtime-test PS1 launch -> Load Save -> automatic native-stream handoff/resume.


<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15 -->

This file is the current-state entry point only. Detailed chronology belongs in
`memory/2026-09-15.md`, specific runtime facts belong in `evidence/`, and
superseded states remain recoverable from Git/history. When this file conflicts
with newer local source or fresh runtime evidence, the newer local evidence wins.

## Development position

| Phase | Status | Current meaning |
| --- | --- | --- |
| A — Games / Emulator | **COMPLETE / PUSHED** | Stable normal-use emulator/game baseline. |
| B — Diagnostics / Clean Native Baseline | **COMPLETE / PUSHED** | Diagnostics, support bundle, retention, and native-only cleanup complete. |
| C — Adaptive Streaming | **PAUSED AT PORTABILITY BOUNDARY** | Profiles, telemetry, startup stabilization, Windows fixed ladder, and restart-actuator evidence exist; automatic adaptation is unfinished and resumes on Linux. |
| D — Linux Migration / Native Linux Baseline | **ACTIVE** | Core Linux host/runtime seams are validated; integrated Linux/onn streaming reaches an external transport blocker. |
| E — Linux Characterization / Optimization | **PLANNED AFTER D + REMAINING C** | Resource sizing and optimization on representative Linux. |
| F — Media / VOD / Live TV UX | **PLANNED** | Resume media polish on Linux. |
| G+ | **FUTURE** | Remote foundation, extended emulation/import, home infrastructure, local intelligence. |

Execution order remains:

`D Linux baseline -> remaining C on Linux -> E -> F -> G`

## Phase D — validated Linux foundation

The following are established and should not be reopened without contradictory
evidence:

- Debian/Renoir Linux baseline with working H.264 VAAPI encode.
- Project-owned RetroArch 1.22.2 Linux AppImage and required NES/SNES/Genesis/PS1
  Linux cores load successfully.
- Existing `EmulatorManager` lifecycle is portable enough to preserve.
- D-074 Linux video backend: exact managed X11 RetroArch window -> `x11grab` ->
  VAAPI H.264 -> existing RTP/FEC contract.
- D-075/D-075R1 Linux process audio: PulseAudio isolated sink/monitor plus a
  sender thread that must obtain `SCHED_RR` priority 1 before PHA1 emission.
- D-076/R1/R2 Linux controller path: PHI1 -> four uinput pads, project-owned udev
  autoconfig, managed absolute autoconfig path, Save/Load/Pause/End host runtime
  validated.
- D-077 normal `GamesPlugin -> EmulatorManager` Linux runtime/core selection is
  host validated.
- D-078 normal Linux companion media-server startup uses Python
  `range_server.py`; Windows retains the PowerShell wrapper.
- Integrated PS1/onn launch crossed the emulator/runtime/capture boundary:
  existing save load, managed X11 window discovery, controller preflight, and
  near-60-fps VAAPI encoding all worked.

## Current blockers and known gaps

### 1. Linux/onn transport blocker

The deferred UDP pathology was reproduced on the representative Linux + home
Opal + onn environment while idle, in both directions.

Linux -> onn Test A:
- 3993 successful unique sends;
- zero unique loss;
- 2626 same-stamp duplicate Android arrivals;
- strong kernel-level burst/gap transformation.

onn -> Linux Test B:
- 4000 successful Android sends;
- 3894 unique Linux arrivals;
- 106 unique losses;
- 476 same-stamp duplicate arrivals;
- strong receive burst/gap transformation.

This rules out a Linux-only sender implementation and proves that game/capture
load is not required for the base pathology. Production socket errors under
load are an amplification, not a prerequisite.

Router localization then established:
- `wlan0`, `wlan1`, and `br-lan` AF_PACKET/tcpdump observations were zero-record
  during confirmed endpoint traffic;
- disabling exposed OpenWrt software/hardware flow-offload flags did not repair
  transport and did not restore packet-capture visibility;
- proprietary Siflower forwarding components remain present;
- D083/D083R1 produced no valid networking evidence and are explicitly invalid.

**Disposition:** the Opal/Siflower reverse-engineering branch is **PAUSED**.
D082 is the last valid router-boundary result. Do not issue another router
probe by default. Re-entry requires either a bounded measurement that changes a
product decision or a different representative network/router environment.

### 2. Android Linux auto-open compatibility bug

`MainActivity` still gates automatic native-stream handoff on the Windows-only
`host_window_policy.window_found`. Linux can report that legacy preflight false
while the authoritative Linux backend subsequently finds the correct X11
window. This is a confirmed compatibility bug; it does not need more diagnosis.

### 3. Linux deployment permissions

Host development validation used temporary access for `/dev/uinput` and
`RLIMIT_RTPRIO=1`. Persistent production/service-scoped permissions remain to be
implemented. Do not grant broad `CAP_SYS_NICE` to the Python interpreter.

### 4. PS1 BIOS migration gap

The integrated Linux PS1 run reported missing `scph5501.bin`. The core still
launched and an existing save loaded, so this was not the transport cause.
Restore user-provided BIOS content before final PS1 acceptance.

## Immediate next work

Do **not** resume open-ended router debugging.

The next production change after this memory normalization is the narrow
Android/Linux auto-open handoff fix, because its root cause is already proven and
it is independent of the paused transport investigation. Preserve the validated
Linux video/audio/controller/runtime paths while making that change.

In parallel, final Linux acceptance still requires persistent service
permissions and restoration of the user-provided PS1 BIOS. Representative stream
acceptance remains blocked until the transport environment is either bounded by
a product-level discriminator or tested on another representative network path.

## Preservation boundaries

Do not change these merely because the current integrated stream is unstable:

- Android stabilization thresholds;
- bitrate/FEC policy;
- decoder policy;
- PHI1/PHA1 wire formats;
- Linux x11grab/VAAPI capture/encode path;
- Linux PulseAudio isolation architecture;
- Linux uinput controller mapping;
- Save/Load/Pause/Resume/End lifecycle.

## Operational rules

- Authoritative Phase-D Linux root: `/home/privyhub/Projects/onn-stream-test`.
- The older Windows checkout is reference/history unless explicitly synchronized for a cross-platform regression.
- Current local source and fresh evidence outrank GitHub and summaries.
- Never ask the user to provide or paste IP addresses.
- Raw measurements outrank classifiers.
- Companion Python changes require a companion restart before runtime judgment.
- One narrow hypothesis -> one targeted probe -> fresh evidence -> one coherent
  patch.

<!-- PRIVYHUB_ADB_RECOVERY_PROBE_LINUX_PARITY_2026_09_15:CURRENT:BEGIN -->
## Active ADB diagnostic — Linux recovery parity

During D4 setup the Linux companion process/listeners/local API were healthy,
while the existing ADB audit found zero onn transports and zero TLS-connect
services. The v2 audit did not execute D-053 cached-target recovery. A narrow
v3 diagnostic patch now aligns the probe with the installer recovery sequence.
Status is **development patch / runtime validation pending**. Do not classify
the companion service as failed from ADB state alone.

<!-- PRIVYHUB_ADB_RECOVERY_PROBE_LINUX_PARITY_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_2026_09_15:CURRENT:BEGIN -->
## Active ADB diagnostic — ephemeral TLS-port recovery

Fresh Linux evidence shows Debian ADB 34.0.5, forced libadbmdns, and temporary
Google Platform Tools 37.0.1/LIBADBMDNS all observe zero TLS-connect services
while the onn remains paired. Windows previously recovered the same dual-radio
setup, so do not classify the Opal radio split as a permanent ADB blocker.

The current narrow hypothesis is a stale wireless-ADB endpoint: pairing survives
while Android restarts its TLS server on a new random port. The v4 diagnostic
adds single-private-host port refresh and paired-ADB verification. Status is
**development patch / runtime validation pending**.

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_V5_2026_09_15:CURRENT:BEGIN -->
## Active ADB diagnostic — v5 endpoint/range recovery

The v4 ephemeral-port diagnostic failed at runtime. A manual local `adb connect`
to the current onn endpoint succeeded immediately, proving pairing and basic
reachability remained healthy and locating the failure in PrivyHub endpoint
bootstrap/discovery.

The connected onn exposes no `service.adb.tls.port` value. Its kernel ephemeral
range was measured as 32768-60999. V5 treats that as representative-device
runtime evidence, learns/caches the live range whenever ADB is connected, scans
only the one privately known onn host and cached/measured range after staleness,
and prompts for repair/re-pair only after automatic recovery is exhausted.
Status remains **development patch / runtime validation pending**.

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_V5_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_ADB_ENDPOINT_DEBUG_V6_2026_09_15:CURRENT:BEGIN -->
## Active ADB diagnostic — literal endpoint debug

The v5 automatic endpoint recovery also failed at runtime while direct local
`adb connect <host>:<current-port>` continued to work. The active hypothesis is
therefore no longer pairing or TCP reachability; the exact endpoint selected by
the recovery probe must be observed directly.

The diagnostic now supports `--debug-endpoints`, which prints the literal cached
endpoint, resolved private host, scan range, open TCP candidates, each ADB
connect endpoint attempted, and its connect/get-state result to the local
terminal only. The normal shareable log remains redacted. Status is development
diagnostic / runtime validation pending.

<!-- PRIVYHUB_ADB_ENDPOINT_DEBUG_V6_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_ADB_ENDPOINT_WATCH_V7_2026_09_15:CURRENT:BEGIN -->
## Active ADB diagnostic — watch one known port

The literal endpoint debug proved that terminal output did not show every port
submitted to the concurrent TCP scan. A known-current port can therefore be
used as a narrow discriminator. `--debug-watch-port <port>` now reports whether
that exact port is in range, when its scan batch is scheduled, and whether its
TCP result is OPEN or CLOSED/UNREACHABLE. Runtime result remains pending.

<!-- PRIVYHUB_ADB_ENDPOINT_WATCH_V7_2026_09_15:CURRENT:END -->
