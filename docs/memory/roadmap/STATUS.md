---
memory_schema: 1
as_of: 2026-09-15
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Roadmap Status

<!-- PRIVYHUB_D119_TV_ENTRY_TRIGGER:ROADMAP:BEGIN -->
## D5.4 TV-state sync — top-level entry trigger diagnostic active

Core Linux/onn synchronization: bidirectionally runtime validated.

D-119: diagnostic-only measurement of true top-level TV entry versus the already
validated Refresh-triggered pull.

D5.4 remains ACTIVE for:
1. trigger/UX resolution;
2. conflict/last-sync diagnostics;
3. focused TV/media regression.
<!-- PRIVYHUB_D119_TV_ENTRY_TRIGGER:ROADMAP:END -->

<!-- PRIVYHUB_D118_PULL_ACCEPTANCE:ROADMAP:BEGIN -->
## D5.4 TV-state sync — core bidirectional path runtime validated

D-115 authority: accepted.

D-116 seed/push: accepted.

D-117/D-118 Linux-to-onn pull: accepted; D-118 corrects a diagnostic classifier
that contradicted restored revision/hash parity.

D5.4 remains ACTIVE only for trigger/UX, conflict diagnostics, and focused media
regression before closure.
<!-- PRIVYHUB_D118_PULL_ACCEPTANCE:ROADMAP:END -->

<!-- PRIVYHUB_D117_PULL_VALIDATION:ROADMAP:BEGIN -->
## D5.4 TV-state sync — pull validation active

D-115 Linux authority: runtime validated.

D-116 seed + onn-to-Linux push: runtime validated.

D-117 Linux-to-onn pull/restore: active diagnostic.

D5.4 remains ACTIVE until D-117 is measured.
<!-- PRIVYHUB_D117_PULL_VALIDATION:ROADMAP:END -->

<!-- PRIVYHUB_D116_TV_STATE_SYNC:ROADMAP:BEGIN -->
## D5.4 TV-state sync — D-116 runtime validation pending

D-115 Linux authority: runtime validated.

D-116 Android seed/pull/push integration: development patch.

Acceptance requires:
- Linux authority seeded from existing onn durable state;
- local/remote durable-state parity;
- post-seed revisioned push of a real user change;
- runtime-only TV health/recency excluded from Linux state.

D5.4 remains ACTIVE.
<!-- PRIVYHUB_D116_TV_STATE_SYNC:ROADMAP:END -->

<!-- PRIVYHUB_D115_TV_STATE_AUTHORITY:ROADMAP:BEGIN -->
## D5.4 TV-state sync — D-115 Linux authority development

**Status:** ACTIVE / Linux authority runtime validation next.

D-115 implements the persistent revisioned Linux TV-state API.

Android synchronization is not yet enabled.

Next after D-115 runtime acceptance:
D-116 Android bootstrap/pull/push around the validated Linux state contract.
<!-- PRIVYHUB_D115_TV_STATE_AUTHORITY:ROADMAP:END -->

<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:ROADMAP:BEGIN -->
## D5.4 TV-state sync — ACTIVE

D5.3 EPG data flow is runtime validated.

D-113 stream-identity integrity audit is closed without a generic production
heuristic.

Current policy for known semantically bad sources is user/manual Hide, not
playback failure.

D5.4 is now the active implementation substep:
Linux-authoritative durable TV user-state synchronization with onn-local
fail-soft operation.

`manual_hidden` is explicitly part of the durable contract.
<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:ROADMAP:END -->

<!-- PRIVYHUB_D113_D5_STREAM_IDENTITY:ROADMAP:BEGIN -->
## D5 EPG — data path accepted; stream-identity integrity audit active

D-111/D-112 establish a functioning readable Program Guide.

D-113 is a bounded post-acceptance integrity audit because a current upstream
stream is mislabeled and its video content does not match its advertised guide
identity.

This is not an EPG transport regression.

**Active:** D-113 stream identity audit.

**Next:** D5.4 TV-state ownership/sync after the D-113 policy decision.
<!-- PRIVYHUB_D113_D5_STREAM_IDENTITY:ROADMAP:END -->

<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:ROADMAP:BEGIN -->
## D5.3 EPG — runtime validated / accepted

D-111 passed end-to-end Android companion EPG validation.

D5.3 EPG data flow is accepted.

D-112 is a small Program Guide newline/readability polish and does not reopen
D5.3 architecture.

**Next after D-112 visual confirmation:** D5.4 TV-state ownership/sync.
<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:ROADMAP:END -->

<!-- PRIVYHUB_D111_D5_ANDROID_COMPANION_EPG:ROADMAP:BEGIN -->
## D5.3 EPG — Android companion integration

**Status:** ACTIVE / D-111 APK runtime validation next.

D-110 Linux EPG service/cache is runtime validated.

D-111 connects the existing Android EPG repository to that service while
retaining the onn local SQLite cache and previous fallback path.

If D-111 passes UI + DB evidence, D5.3 EPG data flow can be accepted.

D5.4 TV-state sync follows.
<!-- PRIVYHUB_D111_D5_ANDROID_COMPANION_EPG:ROADMAP:END -->

<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:ROADMAP:BEGIN -->
## D5.3 EPG — Linux service/cache seam

**Status:** ACTIVE / D-110 Linux runtime validation next.

D-109 proved local EPG acquisition across three independent sites.

D-110 moves that capability behind the existing companion plugin API with
persistent rebuildable toolchain/cache state.

Android remains unchanged until the Linux boundary passes.

D5.4 TV-state sync remains pending behind D5.3.
<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:ROADMAP:END -->

<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:ROADMAP:BEGIN -->
## D5.3 EPG — portable diagnostic environment

**Status:** ACTIVE / D-109 runtime evidence next.

D-108 was blocked only by absent host Node/npm and made no acquisition attempt.

D-109 supplies Node/npm temporarily without changing the appliance installation
and reuses D-108 to test actual local programme acquisition.

D5.4 TV-state sync remains pending behind D5.3.
<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:ROADMAP:END -->

<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:ROADMAP:BEGIN -->
## D5.3 EPG — local acquisition viability

**Status:** ACTIVE / D-108 runtime evidence next.

D-107 established useful feed-aware metadata coverage for the built-in provider
but confirmed that public hosted guide output is not presently broad enough.

D-108 is a diagnostic-only Linux-local grabber test.

D5.4 TV-state ownership/sync remains pending behind D5.3 acceptance.
<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:ROADMAP:END -->

<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:ROADMAP:BEGIN -->
## D5.3 EPG — feed-aware identity diagnostic

**Status:** ACTIVE / D-107 runtime evidence next.

D-106's raw identity-quality data is accepted, but its sparse built-in guide
coverage classification is superseded by the discovered channel/feed
representation mismatch.

D-107 recomputes coverage using the upstream canonical stream identity model.

D5.4 TV-state sync remains pending behind D5.3.
<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:ROADMAP:END -->

<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:ROADMAP:BEGIN -->
## D5.3 EPG — provider/identity diagnostic

**Status:** ACTIVE / D-106 runtime evidence next.

D-105 measured only 2.7085% exact metadata coverage of all nonblank onn channel
IDs. This is insufficient to commit to local EPG generation.

D-106 must first distinguish meaningful IDs, synthetic `tv_stream_*` IDs, and
provider-specific coverage.

D5.4 TV-state sync remains pending behind D5.3.
<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:ROADMAP:END -->

<!-- PRIVYHUB_D105_D5_EPG_LOCAL_SOURCE_VIABILITY:ROADMAP:BEGIN -->
## D5.3 EPG — upstream source availability

**Status:** ACTIVE / diagnostic correction.

D-104R2 is installed and pushed but did not change the runtime EPG result:
2 mappings / 0 programmes.

The current official IPTV-org public worker inventory also exposes only 2
channels, so D5.3 cannot be accepted as a parser-format repair.

Next checkpoint: D-105 guide-metadata/catalog coverage probe.

D5.4 TV-state sync remains pending behind D5.3.
<!-- PRIVYHUB_D105_D5_EPG_LOCAL_SOURCE_VIABILITY:ROADMAP:END -->

<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:ROADMAP:BEGIN -->
## D5.2 -> D5.3 EPG transition

**D5.2:** COMPLETE — diagnostic boundary measured.

D-103 proved the current XML-only source selector is the first EPG divergence.

**D5.3:** ACTIVE — D-104 development patch.

D-104 adds GZIP compatibility only. Runtime acceptance remains pending.

Required next evidence:
`updated onn APK -> Program Guide request -> fresh D-103 probe`.

D5.4 TV-state ownership/sync implementation remains blocked until D5.3 EPG
runtime acceptance is complete.
<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:ROADMAP:END -->


<!-- PRIVYHUB_D103_D5_EPG_INGESTION_PROBE:ROADMAP:BEGIN -->
## D5.2 EPG ingestion diagnostic

**Status:** PROBE READY / RUNTIME EVIDENCE NEXT

D5.1 Live TV remains complete/runtime validated.

D-103 is diagnostic-only. Acceptance requires fresh stage measurements before
D5.3 chooses any EPG production repair.

Next:
`D5.2 probe -> inspect first divergent boundary -> D5.3 narrow repair`.
<!-- PRIVYHUB_D103_D5_EPG_INGESTION_PROBE:ROADMAP:END -->



<!-- PRIVYHUB_D102_D5_TV_SYNC_CHECKPOINT:ROADMAP:BEGIN -->
## D5 authoritative substep status — 2026-09-16

**D5 remains ACTIVE.**

- D5 storage: **COMPLETE / runtime validated**.
- D5.1 Live TV catalog/categories/playback: **COMPLETE / runtime validated**.
- D5.2 EPG ingestion diagnostic: **ACTIVE / NEXT**.
- D5.3 existing EPG path repair/acceptance: **PENDING**.
- D5.4 TV state ownership/sync contract: **PENDING**.
- D5.5 Linux durable TV state store/API: **PENDING**.
- D5.6 onn <-> Linux synchronization: **PENDING**.
- D5.7 synchronization runtime acceptance: **PENDING**.
- D5.8 integrated VOD/TV/EPG/diagnostics/Self-Test regression: **PENDING**.
- D5.9 D5 checkpoint: **PENDING**.

Accepted architecture: Linux becomes durable authority for TV user state while
onn keeps a local cache. Derived catalog/EPG data stays rebuildable/cacheable.

After D5:
`D7 -> D8 -> remaining Phase C (including C6) -> E`.

Do not pull browser/camera runner work back into D5.
<!-- PRIVYHUB_D102_D5_TV_SYNC_CHECKPOINT:ROADMAP:END -->

<!-- PRIVYHUB_D101R1_BROWSER_CAMERA_C6_RECLASSIFICATION:ROADMAP:BEGIN -->
## D5 scope reclassification

External VOD storage: **COMPLETE / runtime validated**.

D5 next:
**Live TV/EPG + diagnostics/Self-Test acceptance.**

Browser/app and camera/live Linux-native streaming are moved out of D5 and into
the remaining C6 work after D8, where they will use the generalized native
source/decoder/transport infrastructure.

Expected sequence:
`D5 -> D7 -> D8 -> remaining C (including C6) -> E`.
<!-- PRIVYHUB_D101R1_BROWSER_CAMERA_C6_RECLASSIFICATION:ROADMAP:END -->

### D-101R1 local-roadmap correction

The earlier D-101 attempt failed before modification because its
installer incorrectly required `ROADMAP.md` at the Linux repository
root. The roadmap file reviewed in chat was uploaded reference material;
the repo's durable roadmap state is maintained in
`docs/memory/roadmap/STATUS.md`.

D-101R1 records the same accepted reclassification entirely through the
actual durable-memory/decision files and does not create or require a
new root-level roadmap file.

<!-- PRIVYHUB_D100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE:ROADMAP:BEGIN -->
## D5 storage substep

**COMPLETE / runtime validated — 2026-09-16**

Validated:
- external configurable bulk VOD;
- stable logical identity;
- hotplug absence without Companion failure;
- zero-touch reinsert recovery;
- Continue Watching continuity;
- repeated client refresh across transitions.

D5 remains ACTIVE.

**Next:** Linux browser/camera runners, followed by integrated
VOD + Live TV/EPG + diagnostics acceptance.
<!-- PRIVYHUB_D100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE:ROADMAP:END -->

<!-- PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1:ROADMAP:BEGIN -->
## D5 absent-VOD timeout closure

D-099 addresses the remaining Android Companion-unavailable timeout after D-098 fixed the crash. Pending runtime validation: fast absent-state control responses, stale Continue Watching failure without service loss, port 8000 availability, and automatic reinsert recovery.
<!-- PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1:ROADMAP:END -->

<!-- PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1:ROADMAP:BEGIN -->
## D5 external-VOD resilience

D-098 closes the control-API crash discovered during physical removable-storage
testing.

Pending runtime validation:
absent disk `/sources`, stale Continue Watching, companion survival, and
reinsert/recovery.

After acceptance, checkpoint the D5 storage seam and continue Linux
browser/camera runner restoration.
<!-- PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1:ROADMAP:END -->

<!-- PRIVYHUB_D097_VOD_APPLIANCE_MODE:ROADMAP:BEGIN -->
## D5 removable-storage appliance mode

D-097 is the final storage-operability step before external-VOD checkpoint:
read-only normal VOD serving with permanently active UUID automount and zero
Linux interaction for routine unplug/reinsert.

Pending: physical E2E unplug/reinsert validation from the onn client.

After acceptance: checkpoint D5 storage seam, then proceed to Linux
browser/camera runners and integrated TV/EPG/media/diagnostics validation.
<!-- PRIVYHUB_D097_VOD_APPLIANCE_MODE:ROADMAP:END -->

<!-- PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE:ROADMAP:BEGIN -->
## D5 configurable storage boundary

**Status:** D-096 development implementation / runtime validation next.

Implemented:
- separate physical VOD root;
- stable logical VOD identity;
- Linux range-server `/vod` mapping;
- explicit storage availability state;
- deterministic UUID-based Linux mount helper.

Pending validation:
- host boundary probe;
- onn playback / Continue Watching;
- unplug/replug recovery without desktop activation.

After acceptance:
continue D5 with Linux browser/camera runners and integrated media/TV diagnostics.
<!-- PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE:ROADMAP:END -->

<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:ROADMAP_STATUS:BEGIN -->
## 2026-09-16 D5 external-VOD checkpoint

**D5 remains ACTIVE.**

Completed/runtime validated within D5:
- Linux companion/control baseline;
- dynamic VOD catalog;
- HTTP byte-range serving;
- external-storage-backed VOD through the normal onn path;
- dynamic source-start health for scanner-mediated external-storage symlinks;
- Continue Watching on the validated external VOD path;
- diagnostics/telemetry/Self-Test endpoint reachability;
- IPTV category endpoint reachability.

D-093 and D-093R1 checkpoint attempts both rolled back cleanly for installer-only
documentation validation defects. D-093R2 is the corrected checkpoint.

Next D5 implementation:
**first-class configurable bulk-media root**.

Still pending after that:
- Linux browser/live source runner;
- Linux camera source runner;
- integrated VOD/TV/EPG/diagnostics acceptance.
<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:ROADMAP_STATUS:END -->

<!-- PRIVYHUB_D090_D4_LINUX_GAMES_ACCEPTANCE:ROADMAP:BEGIN -->
## 2026-09-16 D4 Linux Games acceptance

**D4 is COMPLETE / RUNTIME ACCEPTED WITH EXPLICIT NO-FIXTURE SKIPS.**

Accepted Linux Games coverage:
- library/search/art;
- SNES normal-use launch/gameplay/End;
- PS1 normal-use A/V/input, pause/resume, Save/Load, End;
- cheats;
- IPS mods;
- named A8 input profiles;
- teardown/recovery;
- PS1 four-player Port-1 multitap from D-088.

Explicitly not claimed:
- NES runtime validation — no local fixture;
- Genesis runtime validation — no local fixture.

Phase D remains ACTIVE and advances to **D5 media/server restoration**.

Execution remains:
`D5 -> D6 reconciliation of already-replayed UDP branch -> D7 -> D8 -> remaining C on Linux -> E`
<!-- PRIVYHUB_D090_D4_LINUX_GAMES_ACCEPTANCE:ROADMAP:END -->

<!-- PRIVYHUB_D089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT:ROADMAP:BEGIN -->
## 2026-09-16 D5 storage constraint

**Phase D remains ACTIVE at D4 final Games regression.**

D5 media/server restoration follows D4 acceptance.

Prototype-1 D5 storage constraint:
- bulk VOD/movie data may reside on an external hard drive;
- internal disk space must not be treated as the required media-library capacity;
- media-root handling should remain portable toward later dedicated storage;
- temporary media-root unavailability must be handled separately from library
  deletion.

This is a planning constraint only; D5 implementation/validation has not begun.
<!-- PRIVYHUB_D089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT:ROADMAP:END -->

<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:ROADMAP:BEGIN -->
## 2026-09-16 D4 multiplayer checkpoint

**Phase D remains ACTIVE.**

Runtime validated inside D4:
- integrated Linux gameplay controller parity across three games / three input
  profiles;
- PS1 Port-1 multitap/four-player parity in Crash Bash with four independent
  remotes/controllers.

Remaining D4 scope before normal-use Games parity is complete:
- representative final Games regression/acceptance across required lifecycle and
  feature paths.

After D4 acceptance, proceed to D5 media/server restoration.
<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:ROADMAP:END -->

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:ROADMAP:BEGIN -->
## 2026-09-16 D4 controller checkpoint

**Phase D remains ACTIVE.**

Newly runtime validated:
- Linux integrated game launch/stream path;
- Linux gameplay controller path across three games / three input profiles;
- default and named input-profile behavior after D-084/D-085;
- persistent uinput prerequisite and RT-priority prerequisite remain closed.

Immediate D4 blocker before broader regression:
- **PS1 multiplayer / multitap parity on Linux**.

Historical Windows Phase-A multitap acceptance is the behavioral reference.
Linux debugging must first classify stored override -> generated Beetle `.opt`
-> P1-P4 frontend configuration -> in-game Players 3/4 availability.

Execution order remains:

`finish D4 multiplayer/normal-use parity -> finish remaining Phase D -> resume remaining C on Linux -> E -> F -> G`
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:ROADMAP:END -->

<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15 -->

`docs/ROADMAP.md` defines phase scope. This file records the current execution
position and overrides older embedded "next" statements in historical notes.

## Current position

| Phase | Status | Current meaning |
| --- | --- | --- |
| A — Games / Emulator Subsystem | **COMPLETE / PUSHED** | Stable emulator/game baseline. |
| B — Diagnostics & Clean Native Baseline | **COMPLETE / PUSHED** | Diagnostics and native-only cleanup complete. |
| C — Adaptive Native Streaming | **PAUSED AT WINDOWS PORTABILITY BOUNDARY** | C1/C2/startup stabilization and Windows fixed-ladder/actuator evidence retained; automatic adaptation unfinished. |
| D — Linux Migration / Native Linux Baseline | **ACTIVE** | Core Linux host seams validated; integrated stream reaches representative transport blocker. |
| E — Linux Core Characterization / Optimization | **PLANNED AFTER D + REMAINING C** | Size/optimize PS1-and-below on Linux. |
| F — Media Library / VOD / Live TV UX | **PLANNED** | Resume media/guide polish on Linux. |
| G — Secure Remote / Portable Client Foundation | **FUTURE** | Overlay/provider abstraction, WAN identity/auth, off-site validation. |
| H — Extended Emulation / User Content Import | **FUTURE** | Safe import then later-console characterization. |
| I — Home Infrastructure / Broader Plugins | **FUTURE** | Devices, cameras, storage, broader clients. |
| J — Local Intelligence / Voice / Privacy-Aware AI | **FUTURE** | Local-first intelligence; optional explicit external providers. |

Execution order:

`D Linux baseline -> remaining C on Linux -> E -> F -> G -> H -> I -> J`

## Phase C carry-forward

Complete/retained:

- explicit `native_game_720p60_reference` profile;
- C2 `privyhub_stream_telemetry_v1` measurement contract;
- startup stabilization/readiness gate;
- Windows fixed bitrate evidence: 5500/6000/7000 validated, 5000 rejected;
- bidirectional restart actuator capability, with ~1 s interruption proving it
  unsuitable for seamless automatic play.

Still required on Linux before Phase E:

- acceptable low-interruption bitrate actuation and automatic controller;
- adaptive FEC or explicit deferral;
- 1080p60 characterization;
- generalized native source abstraction;
- Phase-C final checkpoint.

## Phase D progress

Validated:

- Linux host/emulator baseline;
- project-owned Linux RetroArch runtime and cores;
- exact-window X11/VAAPI native video;
- PulseAudio process isolation and RT sender requirement;
- PHI1/uinput P1-P4 controller path and managed autoconfig;
- normal product platform runtime selection;
- normal Linux companion media-server startup;
- integrated PS1 launch/save-load/window-discovery/VAAPI encode.

Pending:

- Android Linux-neutral automatic stream handoff;
- persistent production permissions for uinput and RT priority;
- user-provided PS1 BIOS restoration;
- representative integrated stream acceptance.

## Transport disposition

The deferred UDP problem was replayed on Linux + home Opal + onn and reproduced
bidirectionally while idle. Standard router AF_PACKET capture points are blind
to the confirmed WLAN-to-WLAN traffic. Exposed OpenWrt flow-offload flags are
not the fix. D083/D083R1 are invalid measurements; D082 is the last valid router
result.

The Opal/Siflower root-cause branch is **PAUSED**, not the default next task.
Re-enter only for a bounded product-level discriminator or on a different
representative network/router path.

## Immediate development step

After this memory normalization, implement the narrow Android/Linux auto-open
compatibility fix. Do not use that patch to alter transport, bitrate/FEC,
decoder policy, or the validated Linux capture/audio/controller backends.
