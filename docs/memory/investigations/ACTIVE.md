---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Active Investigations and Queued Work

<!-- PRIVYHUB_D124A_SPLIT_DB_FIX:ACTIVE:BEGIN -->
## ACTIVE — D-124A correction pending rerun

D-124's first runtime attempt did not test the latency hypothesis.

It failed in diagnostic code because a TV-database query referenced the
EPG-only `programmes` table.

D-124A fixes only that measurement and adds direct split-database self-test
coverage.

The original D-124 latency hypothesis remains active and unclassified until the
corrected report is produced.
<!-- PRIVYHUB_D124A_SPLIT_DB_FIX:ACTIVE:END -->

<!-- PRIVYHUB_D124_EPG_LATENCY:ACTIVE:BEGIN -->
## ACTIVE — D-124 TV/EPG latency

Narrow hypothesis:
EPG acquisition/cache misses materially contribute to slow TV/guide loading.

D-124 measures external/database stages only.

Possible outcomes:
- slow companion guide fetch -> inspect/acquire/cache path;
- poor Android programme-cache coverage -> inspect prefetch/cache strategy;
- expensive representative SQLite shape -> inspect query/index plan;
- external stages fast -> instrument Android category/guide/render path.

Guide-style paged Favorites/category UX remains queued until the timing evidence
is known.
<!-- PRIVYHUB_D124_EPG_LATENCY:ACTIVE:END -->

<!-- PRIVYHUB_D123_D54_CLOSURE:ACTIVE:BEGIN -->
## ACTIVE — post-D5.4 TV EPG performance / guide UX

D5.4 is closed/runtime validated.

Active question:
where is the observed Live TV / guide loading latency actually spent?

First action must be diagnostic-only timing instrumentation.

Do not combine the timing probe with the guide UI redesign.

Queued after evidence:
1. fix/expand EPG coverage diagnostics;
2. paged guide-style channel/category UI;
3. performance/runtime validation.
<!-- PRIVYHUB_D123_D54_CLOSURE:ACTIVE:END -->

<!-- PRIVYHUB_D122_MEDIA_REGRESSION:ACTIVE:BEGIN -->
## D5.4 ACTIVE — D-122 final regression gate

Synchronization-specific runtime acceptance is complete through D-121.

Active work is limited to regression confirmation of mature media paths.

No new D5.4 feature or architectural change should begin before this gate is
classified.

If clean, close D5.4 and advance the roadmap.
<!-- PRIVYHUB_D122_MEDIA_REGRESSION:ACTIVE:END -->

<!-- PRIVYHUB_D121_CONFLICT_DIAGNOSTICS:ACTIVE:BEGIN -->
## D5.4 ACTIVE — D-121 conflict diagnostics

Core bidirectional sync, normal top-level trigger, and last-success diagnostics
are runtime validated.

One synchronization acceptance question remains:
controlled stale Android durable write -> Linux rejection -> visible conflict
metadata -> authoritative recovery.

D-121 is diagnostic-only and must be reviewed before any conflict-policy change.

After D-121 passes, move to focused TV/media regression and D5.4 closure.
<!-- PRIVYHUB_D121_CONFLICT_DIAGNOSTICS:ACTIVE:END -->

<!-- PRIVYHUB_D120_SYNC_DIAGNOSTICS:ACTIVE:BEGIN -->
## D5.4 ACTIVE — D-120 sync diagnostics

D-119 closed the trigger question successfully.

Current narrow boundary:
make the already-validated state synchronization observable without changing its
semantics.

D-120 adds last-success and last-conflict metadata plus status-dialog display.

Next only after D-120 runtime acceptance:
exercise one controlled stale-revision conflict and confirm the conflict is
visible while Linux remains protected.
<!-- PRIVYHUB_D120_SYNC_DIAGNOSTICS:ACTIVE:END -->

<!-- PRIVYHUB_D119_TV_ENTRY_TRIGGER:ACTIVE:BEGIN -->
## D5.4 ACTIVE — D-119 top-level TV-entry trigger

Core state contract is accepted and must not be reopened without contradictory
evidence.

Active hypothesis:
the earlier apparent pull miss may have been caused by navigation that did not
actually execute `openTvHome()`.

D-119 distinguishes:
- true top-level TV entry reliably invokes sync; or
- top-level TV entry misses sync with healthy ADB and a newer Linux revision.

Only the second outcome justifies a production lifecycle/trigger patch.
<!-- PRIVYHUB_D119_TV_ENTRY_TRIGGER:ACTIVE:END -->

<!-- PRIVYHUB_D118_PULL_ACCEPTANCE:ACTIVE:BEGIN -->
## D5.4 ACTIVE — core synchronization validated

Core TV durable-state synchronization is now bidirectionally runtime validated.

Do not reopen seed/push/pull mechanics without new contradictory evidence.

Remaining bounded D5.4 questions:
1. make the user-visible synchronization trigger unambiguous/reliable;
2. surface revision conflicts/last-sync diagnostics adequately;
3. run focused TV/media regression before D5.4 closure.

D-117 marker testing is closed.
<!-- PRIVYHUB_D118_PULL_ACCEPTANCE:ACTIVE:END -->

<!-- PRIVYHUB_D117_PULL_VALIDATION:ACTIVE:BEGIN -->
## D5.4 ACTIVE — D-117 Linux-to-onn pull validation

D-116 seed + push is runtime validated.

One narrow acceptance gap remains:
initialized/newer Linux state -> onn.

D-117 changes only a harmless display-name preference, verifies the pull, then
restores and verifies again.

Do not add further synchronization features until this existing pull path is
measured.
<!-- PRIVYHUB_D117_PULL_VALIDATION:ACTIVE:END -->

<!-- PRIVYHUB_D116_TV_STATE_SYNC:ACTIVE:BEGIN -->
## D5.4 ACTIVE — D-116 Android sync runtime validation

Linux TV-state authority is runtime validated.

Active boundary:
prove the onn can seed, pull, and push the durable projection without syncing
runtime health/recency data.

Use a real user mutation (`manual_hidden` on the known-bad 10 Bold source) to
prove a post-seed revisioned push.

Do not expand to multi-client merge semantics until this one-client contract is
runtime validated.
<!-- PRIVYHUB_D116_TV_STATE_SYNC:ACTIVE:END -->

<!-- PRIVYHUB_D115_TV_STATE_AUTHORITY:ACTIVE:BEGIN -->
## D5.4 active — Linux state authority runtime validation

D-115 is the active implementation boundary.

Validate before Android changes:
- bounded JSON-body plugin POST path;
- durable-only normalization;
- atomic state persistence;
- monotonic revision assignment;
- idempotent identical writes;
- stale-revision conflict protection;
- exact probe cleanup/restoration.

Do not enable Android automatic sync until this boundary passes.
<!-- PRIVYHUB_D115_TV_STATE_AUTHORITY:ACTIVE:END -->

<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:ACTIVE:BEGIN -->
## D5.4 ACTIVE — Linux-authoritative TV-state synchronization

D-113 stream-identity audit is closed at current scope.

No generic semantic-identity classifier is justified by the current heuristic.

D5.4 now becomes active.

Narrow implementation boundary:
1. inventory the exact existing Android TV export/import JSON contract;
2. establish Linux persistent versioned TV-state storage/API;
3. preserve onn-local operation when Linux is unavailable;
4. synchronize durable user intent without copying SQLite DBs;
5. include `manual_hidden` so user-confirmed bad-source decisions persist.

Runtime observations/health counters remain outside the first generalized sync
contract until explicit merge semantics exist.
<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:ACTIVE:END -->

<!-- PRIVYHUB_D113_D5_STREAM_IDENTITY:ACTIVE:BEGIN -->
## D5 active — stream semantic identity integrity

EPG transport/acquisition/cache is accepted.

Active narrow question:
how broad are feed-ID/display-name contradictions in the current built-in IPTV
catalog?

D-113 audits official feed metadata against the current onn catalog.

If contradictions are systemic, design a generic `identity_suspect` state that
can suppress misleading EPG without conflating it with playback failure.

If isolated, prefer targeted quarantine/override rather than a broad heuristic.

D5.4 TV-state sync remains queued behind this integrity checkpoint.
<!-- PRIVYHUB_D113_D5_STREAM_IDENTITY:ACTIVE:END -->

<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:ACTIVE:BEGIN -->
## D5.3 accepted; D-112 presentation polish active

D-111 established end-to-end companion-backed Android EPG and D5.3 is runtime
accepted.

Active narrow polish:
replace the literal `\n` Program Guide row separator with an actual newline.

This does not reopen EPG acquisition or matching investigations.

Next development boundary after the visual check is D5.4 TV durable-state sync.
<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:ACTIVE:END -->

<!-- PRIVYHUB_D111_D5_ANDROID_COMPANION_EPG:ACTIVE:BEGIN -->
## D5.3 active — Android companion EPG consumption

Linux acquisition/cache is accepted from D-110.

The active boundary is Android consumption.

D-111 must prove:
- existing companion host configuration reaches port 8765 EPG plugin;
- exact feed-aware channel ID survives the Android request;
- Linux programmes populate the existing onn EPG SQLite database;
- Program Guide renders the resulting schedule;
- local cache continues to work independently after population.

No TV catalog/provider rewrite and no TV-state sync change in D-111.
<!-- PRIVYHUB_D111_D5_ANDROID_COMPANION_EPG:ACTIVE:END -->

<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:ACTIVE:BEGIN -->
## D5.3 active — Linux EPG production seam

D-109 closed the technical-viability question with real multi-site programme
output.

The active boundary is now the companion service/cache implementation.

D-110 runtime-validates:
- side-effect-free companion startup;
- persistent rebuildable EPG bootstrap;
- exact feed-aware acquisition;
- positive programme cache;
- stable plugin API behavior.

Do not modify Android EPG networking in the same patch. D-111 owns that boundary
after Linux validation.
<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:ACTIVE:END -->

<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:ACTIVE:BEGIN -->
## D5.3 active — temporary EPG toolchain environment

D-108 did not reach local programme acquisition because Node/npm is absent from
the Linux host.

The active question is still D-108's question:
can representative exact-matched channels produce real XMLTV locally?

D-109 removes only the environment blocker using a verified portable Node
runtime in temporary state. It reuses D-108 rather than creating parallel
acquisition logic.

No system Node installation and no production EPG implementation before this
evidence.
<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:ACTIVE:END -->

<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:ACTIVE:BEGIN -->
## D5.3 active — local programme acquisition

D-107 closed the feed-aware identity question sufficiently for D5:
the built-in provider has 1,218 exact canonical matches out of 3,017 meaningful
IDs (40.3712%).

Public hosted source coverage remains effectively unavailable.

Active narrow diagnostic:
test the pinned upstream IPTV-org grabber against a bounded multi-site sample of
exact-matched channels using disposable Linux state.

No production cache/service implementation before D-108 establishes actual
programme yield and environment/toolchain viability.
<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:ACTIVE:END -->

<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:ACTIVE:BEGIN -->
## D5.3 active — feed-aware guide identity

D-106 established that synthetic IDs are only a small part of the catalog, but
its built-in zero-overlap result used the wrong identity representation.

Upstream stream IDs can contain `@feed`; guide records carry that feed in a
separate field.

Active narrow diagnostic:
recompute built-in and onn metadata coverage with canonical `channel@feed`
identity.

D-107 is read-only. No fuzzy matching, local guide generation, or Android EPG
mapping change before its result.
<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:ACTIVE:END -->

<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:ACTIVE:BEGIN -->
## D5.3 active — provider / channel identity

D-105 found only 89 exact guide-metadata matches among 3,286 nonblank onn
channel IDs.

The next question is whether that denominator contains many synthetic
`tv_stream_*` fallback identities, and whether the built-in IPTV-org playlist
itself has similarly sparse guide metadata coverage.

D-106 is the active diagnostic-only probe.

Do not implement local EPG generation, fuzzy guide matching, or another Android
parser change before D-106 evidence.
<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:ACTIVE:END -->

<!-- PRIVYHUB_D105_D5_EPG_LOCAL_SOURCE_VIABILITY:ACTIVE:BEGIN -->
## D5.3 active — EPG local-source viability

D-104R2 runtime evidence invalidated the assumption that source compression was
the main remaining blocker.

Measured state:
- guide metadata rows: 180,681;
- source-backed mappings accepted: 2;
- onn mappings: 2;
- programmes: 0;
- exact/case-insensitive intersection with onn channel IDs: 0;
- official public guide workers currently cover 2 channels total.

Active narrow question:
does guide metadata itself cover the onn catalog before source availability is
applied?

D-105 is diagnostic-only and answers that question. Production EPG architecture
must wait for the result.
<!-- PRIVYHUB_D105_D5_EPG_LOCAL_SOURCE_VIABILITY:ACTIVE:END -->

<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:ACTIVE:BEGIN -->
## D5.3 active — EPG GZIP source compatibility

D5.2's mapping-source diagnostic is resolved at its measured boundary.

Active development patch D-104:
- XML remains preferred;
- GZIP is accepted as fallback;
- compressed XML is decoded by gzip magic;
- existing exact guide identity rules remain unchanged.

Next evidence is runtime, not another speculative code change:
updated APK -> Program Guide request -> fresh D-103 probe.

If D-103 then reports a different first divergence, that becomes the next narrow
D5.3 investigation.
<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:ACTIVE:END -->


<!-- PRIVYHUB_D103_D5_EPG_INGESTION_PROBE:ACTIVE:BEGIN -->
## D5.2 active investigation — EPG ingestion

**Status:** D-103 diagnostic-only probe / runtime result next.

Narrow hypothesis boundary:
the current `2 mappings / 0 programmes` result may originate before programme
rendering, so measure upstream guide structure, parser acceptance, cache state,
catalog identity, and XML programme identity in order.

No production EPG change until the fresh D-103 log identifies the first
divergent stage.
<!-- PRIVYHUB_D103_D5_EPG_INGESTION_PROBE:ACTIVE:END -->



<!-- PRIVYHUB_D102_D5_TV_SYNC_CHECKPOINT:ACTIVE:BEGIN -->
## D5 current active investigation

**Closed / runtime accepted**
- external/removable VOD storage and hotplug behavior;
- Live TV catalog/categories/navigation;
- normal Live TV channel playback.

**Active — one narrow hypothesis**
The existing EPG ingestion/matching path is failing before usable programme
cache creation. Fresh onn state is 2 EPG mappings and 0 cached programmes.

**Next probe**
Measure:
upstream guide entries -> channel IDs -> source-bearing entries -> supported XML
sources -> accepted mappings -> current-catalog ID matches -> XMLTV fetch ->
matching programme records.

Do not patch EPG production logic until the first divergent boundary is
measured.

**Queued after EPG repair**
- Linux-authoritative TV user-state store/sync contract;
- onn synchronization and convergence validation;
- integrated media/diagnostics/Self-Test regression.

Browser/app and camera/live generalized native sources remain C6 after D7/D8.
<!-- PRIVYHUB_D102_D5_TV_SYNC_CHECKPOINT:ACTIVE:END -->

<!-- PRIVYHUB_D101R1_BROWSER_CAMERA_C6_RECLASSIFICATION:ACTIVE:BEGIN -->
## D5 active scope after storage acceptance

**Complete / runtime validated**
- configurable/removable VOD storage;
- zero-touch hotplug recovery;
- Continue Watching continuity.

**Active**
- Live TV/EPG acceptance;
- diagnostics/Self-Test/media regression.

**Reclassified / not a D5 blocker**
- browser/app native streaming -> C6 after D8;
- camera/live native streaming -> C6 after D8;
- broad smart-home camera integration -> Phase I.

Do not build temporary Linux browser/camera runners unless new evidence makes a
D5 compatibility requirement unavoidable.
<!-- PRIVYHUB_D101R1_BROWSER_CAMERA_C6_RECLASSIFICATION:ACTIVE:END -->

<!-- PRIVYHUB_D100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE:ACTIVE:BEGIN -->
## D5 current active work

External/removable VOD storage boundary:
**COMPLETE / runtime validated**.

Closed acceptance includes:
- stable configurable physical VOD root;
- stable logical identity;
- clean absent-storage behavior;
- nonblocking control/media services;
- zero-touch reinsert recovery;
- Continue Watching continuity across unplug/reinsert;
- repeated hotplug refresh on onn.

Current active D5 work:
**Linux browser/camera runner restoration**.

After runners:
integrated VOD + Live TV/EPG + diagnostics acceptance.
<!-- PRIVYHUB_D100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE:ACTIVE:END -->

<!-- PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1:ACTIVE:BEGIN -->
## D5 nonblocking absent-storage acceptance

**Status:** D-099 development patch / runtime validation next.

Acceptance: absent disk keeps `/status`, `/sources`, and stale source-start under 2 seconds; `storage.vod.available=false`; port 8000 remains available; reinsertion restores VOD automatically.
<!-- PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1:ACTIVE:END -->

<!-- PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1:ACTIVE:BEGIN -->
## D5 removable-storage absent-state resilience

**Status:** D-098 development patch / hotplug E2E next.

Acceptance:
- no uncaught `OSError` from absent external VOD;
- `/sources` HTTP 200 while disk is absent;
- stale Continue Watching/source start fails cleanly;
- Companion remains available after stale source attempt;
- reinsertion restores dynamic VOD automatically;
- logical IDs and Continue Watching identity remain stable.

D-097 read-only/permanent-automount policy remains the intended appliance
operating model when installed.
<!-- PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1:ACTIVE:END -->

<!-- PRIVYHUB_D097_VOD_APPLIANCE_MODE:ACTIVE:BEGIN -->
## D5 removable VOD hotplug acceptance

**Status:** D-097 development patch / final removable-storage E2E next.

Acceptance:
- normal VOD mount is read-only;
- UUID automount remains active while disk is absent;
- no Linux command required for normal unplug/reinsert;
- unplug after playback stops removes/unavailable library cleanly;
- reinsertion plus client VOD access remounts/repopulates automatically;
- source identity/Continue Watching remain stable;
- no desktop/file-manager activation.

After acceptance, checkpoint storage work and continue D5 Linux browser/camera
runner restoration.
<!-- PRIVYHUB_D097_VOD_APPLIANCE_MODE:ACTIVE:END -->

<!-- PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE:ACTIVE:BEGIN -->
## D5 stable VOD storage runtime acceptance

**Status:** DEVELOPMENT PATCH D-096 / RUNTIME VALIDATION NEXT

Acceptance gates:
- configured storage status is explicit and available;
- old representative VOD source ID remains stable;
- source-start and HTTP Range pass from the configured physical root;
- normal onn playback and Continue Watching remain intact;
- storage absence does not prevent companion/live server startup;
- after drive return, deterministic system automount restores the configured
  path without a desktop/file-manager click;
- catalog repopulates automatically with stable logical IDs.

Browser/camera Linux runner work remains queued after this storage boundary.
<!-- PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE:ACTIVE:END -->

<!-- PRIVYHUB_D094_EXTERNAL_STORAGE_REMOUNT:ACTIVE:BEGIN -->
## D5 stable bulk-media root and storage availability

**Status:** ACTIVE / NEXT

Validated:
- external VOD normal playback;
- Continue Watching;
- dynamic source-start health;
- automatic library repopulation once the external filesystem path becomes
  available again.

Still missing:
1. deterministic OS-level mount at a stable path;
2. explicit PrivyHub bulk-media-root configuration;
3. unavailable-root state distinct from empty library.

Do not depend on desktop file-manager activation or user-label automount paths.

The next implementation/probe should preserve the existing default local media
root while introducing a stable configurable storage boundary.
<!-- PRIVYHUB_D094_EXTERNAL_STORAGE_REMOUNT:ACTIVE:END -->

<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:ACTIVE:BEGIN -->
## D5 configurable bulk-media root

**Status:** ACTIVE / NEXT

D-092 external-VOD compatibility is runtime validated, including normal playback
and Continue Watching.

Next narrow implementation goal:
make the bulk media root configurable without depending on a repo-local symlink.

Required behavior:
- default remains project `media/` when no override exists;
- external root is explicit/configurable;
- dynamic scanning and media serving use the same selected root;
- lightweight PrivyHub state remains internal where practical;
- stable content/source identity survives storage relocation where possible;
- unavailable external storage is reported as unavailable, not interpreted as
  authoritative library deletion;
- no mandatory cloud or proprietary dependency.

Do not mix browser/camera runner migration into the storage-root patch.
<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:ACTIVE:END -->

<!-- PRIVYHUB_D092_DYNAMIC_VOD_SYMLINK_HEALTH:ACTIVE:BEGIN -->
## D5 dynamic external-VOD source-start

**Status:** DEVELOPMENT PATCH D-092 / RUNTIME VALIDATION NEXT

First failing boundary:
`cataloged dynamic VOD -> POST source start -> _vod_is_healthy()`.

Pre-patch result:
HTTP 503 before any port-8000 media request.

D-092 fixes only the scanner-generated dynamic-symlink health mismatch.

Acceptance:
- source-start probe returns HTTP 200 / ready true for Aviator;
- onn then reaches and plays the movie normally, or fresh evidence identifies
  the next boundary.

Do not alter Android playback or range serving unless source-start first passes.
<!-- PRIVYHUB_D092_DYNAMIC_VOD_SYMLINK_HEALTH:ACTIVE:END -->

<!-- PRIVYHUB_D091_D5_MEDIA_BASELINE:ACTIVE:BEGIN -->
## D5 VOD onn playback boundary

**Status:** ACTIVE / NEXT DIAGNOSTIC

Host-side external-VOD path is healthy through HTTP Range.

One narrow unresolved question:
when the onn attempts the exact failing symlinked movie, does a matching GET/HEAD
reach the media server and receive HTTP 200/206?

Use the D-091 request-boundary probe before any production change.

Interpretation:
- matching successful request -> inspect Android Media3/container/codec error;
- no request -> inspect client URL/network construction;
- matching HTTP error -> inspect media-server path response.

Do not modify external storage or introduce codec work before this boundary is
measured.
<!-- PRIVYHUB_D091_D5_MEDIA_BASELINE:ACTIVE:END -->

<!-- PRIVYHUB_D090_D4_LINUX_GAMES_ACCEPTANCE:ACTIVE:BEGIN -->
## Phase D / D5 media-server restoration

**Status:** ACTIVE / NEXT

D4 normal-use Games acceptance is closed by D-090.

Next scope is D5 only:
- companion/control API;
- VOD;
- Live TV/EPG;
- browser/live source where active;
- camera source where active;
- diagnostics/Self-Test;
- Phase-C profile/telemetry/stabilization infrastructure;
- existing media state/cache and working playback paths.

Prototype-1 storage rule:
bulk VOD may live on external storage. Do not make the internal NVMe the media
capacity requirement. Treat unavailable external storage as unavailable storage,
not authoritative deletion.

Do not reopen D4 Games internals unless new regression evidence appears.
<!-- PRIVYHUB_D090_D4_LINUX_GAMES_ACCEPTANCE:ACTIVE:END -->

<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:ACTIVE:BEGIN -->
## Phase D / D4 normal-use Games acceptance

**Status:** ACTIVE / NEXT

The dedicated PS1 multiplayer/multitap investigation is closed by D-088 runtime
evidence.

Remaining D4 work is the representative normal-use Games regression/acceptance
required by the roadmap, including the already-established paths for launch,
video/audio/input, saves/states, pause/resume, profiles/cheats/mods, metadata/art,
and teardown/recovery.

Do not create new multiplayer architecture work unless regression evidence
requires it.
<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:ACTIVE:END -->

<!-- PRIVYHUB_D087R1_LINUX_PS1_MULTITAP_METADATA_PATH:ACTIVE:BEGIN -->
## PS1 multiplayer / multitap Linux — D-087R1 follow-up

**Status:** ACTIVE / DEVELOPMENT PATCH

D-087 resolved the Config-root lookup and exposed a second prelaunch portability
error in metadata only. D-087R1 removes that remaining project-root assumption.

Next discriminator: does the game reach multiplayer selection? If yes, continue
with Players 3/4 and four-controller independence checks.
<!-- PRIVYHUB_D087R1_LINUX_PS1_MULTITAP_METADATA_PATH:ACTIVE:END -->

<!-- PRIVYHUB_D087_LINUX_PS1_MULTITAP_CONFIG_PATH:ACTIVE:BEGIN -->
## PS1 multiplayer / multitap Linux — first boundary classified

**Status:** ACTIVE / DEVELOPMENT PATCH D-087

First divergence from the Windows Phase-A reference:
`stored multitap state -> core-options materialization`.

Linux failed before RetroArch because the adapter searched the Windows portable
Config directory. The Linux Beetle seed exists in the user/XDG RetroArch Config
tree. D-087 corrects only that path seam.

Acceptance after D-087:
- game launches with Multitap On;
- Port 1 enabled / Port 2 disabled in content-specific `.opt`;
- Players 3/4 available;
- four independent controllers.
<!-- PRIVYHUB_D087_LINUX_PS1_MULTITAP_CONFIG_PATH:ACTIVE:END -->

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:ACTIVE:BEGIN -->
## PS1 multiplayer / multitap parity on Linux

**Status:** ACTIVE / NEXT

The prior broad Linux controller issue is closed for the tested default/A8
single-game paths: D-085 was runtime accepted across three games and three input
profiles.

Current separate regression:
- PS1 multitap does not work on Linux.

Known-good behavioral reference from Windows Phase A:
- manual Multitap On/Off;
- stored mode `port1`;
- `beetle_psx_hw_enable_multitap_port1 = "enabled"`;
- `beetle_psx_hw_enable_multitap_port2 = "disabled"`;
- Players 3/4 available in CTR;
- four controllers independently normal;
- classification `PS1_MULTITAP_ONOFF_CTR_CONFIRMED`.

Do not patch yet. First Linux diagnostic must capture the same semantic
boundaries without relying on Windows XInput APIs:

1. exact active game ID;
2. stored controller override and `ps1_multitap`;
3. generated content-specific Beetle PSX HW `.opt` and both multitap values;
4. P1-P4 Linux virtual-pad presence and RetroArch configuration in the same
   launch;
5. user-visible Players 3/4 availability and independent control.

The result should classify which boundary first diverges from the Windows
reference.
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:ACTIVE:END -->

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:ACTIVE:BEGIN -->
## 2026-09-16 active reconciliation

This section supersedes older Phase-D queued bullets where they conflict with
newer runtime evidence.

### RetroArch PS1 analog controller mode

**Status:** ACTIVE / NARROWLY ISOLATED

Proven below the RetroArch/core layer:

- Android controller packets arrive;
- Linux PHI1 injection works;
- four-pad uinput architecture remains valid;
- RetroArch detects `PrivyHub Virtual Gamepad P1`;
- the virtual pad exposes the expected absolute axes;
- live `ABS_X` / `ABS_Y` values change.

Next diagnostic scope is only PS1 controller mode/core/session configuration
(digital PlayStation pad versus DualShock/analog behavior).

### Linux normal-use acceptance

**Status:** QUEUED AFTER ANALOG FIX

Rerun launch, video, process audio, controller, Pause/Resume, Save/Load, and End.
Persistent uinput module/ownership and realtime-priority prerequisites are
already validated and are no longer active setup tasks.

### Android auto-open handoff

Keep the already-installed D4 handoff fix on its own acceptance track. Do not
conflate a remaining auto-open runtime check with the controller-mode issue.

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:ACTIVE:END -->

<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15 -->

This file contains only current active/queued work. Completed chronology belongs
in `CLOSED.md`/evidence/history. The paused transport root-cause branch belongs
in `DEFERRED.md`.

## Phase D Linux normal-use parity

**Status:** ACTIVE

Validated host/product seams:

- D-073 Linux host/emulator baseline;
- D-074 exact-window X11/VAAPI video;
- D-075/D-075R1 PulseAudio process audio and RT sender requirement;
- D-076/R1/R2 PHI1/uinput controller runtime + managed autoconfig;
- D-077 platform-aware normal product runtime selection;
- D-078 Linux companion media-server startup;
- integrated PS1 launch/save-load/window-discovery/VAAPI encode boundary.

Remaining Phase-D work that does not require reopening router diagnosis:

1. fix Android automatic stream handoff so Linux does not depend on the
   Windows-only `host_window_policy.window_found` preflight;
2. establish persistent service-scoped `/dev/uinput` permission;
3. establish persistent RT-priority allowance for the Linux PHA1 sender;
4. restore user-provided PS1 BIOS before final PS1 acceptance;
5. rerun representative normal-path regressions when a usable transport path is
   available.

## Android Linux auto-open handoff

**Status:** CONFIRMED BUG / READY FOR NARROW PATCH

Evidence already proves the Linux native backend can discover the managed X11
window after the legacy Windows preflight reports false. No new diagnostic is
needed before fixing the gate.

Preserve all transport, decoder, video, audio, controller, save/load, and game
lifecycle behavior.

## Remaining Phase C on Linux

**Status:** QUEUED AFTER PHASE-D BASELINE

Do not skip these items:

- low-interruption Linux bitrate actuator + automatic controller;
- C4 adaptive FEC or explicit evidence-backed deferral;
- C5 1080p60 capability characterization;
- C6 generalized native source abstraction;
- C7 final Phase-C checkpoint.

Windows fixed-ladder/restart evidence is input evidence only, not a Linux
constant.
