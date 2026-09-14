---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 0c31c100ec721d687aff6aedbd79bc0cf9343810
---

# Current Handoff

## Repository state

Authoritative local root:

`L:\Projects\onn-stream-test`

Local source is authoritative between checkpoints. GitHub is reference/history
unless a clean synchronized checkpoint is being verified.

Predecessor synchronized checkpoint for the remote-foundation promotion:

`0c31c100ec721d687aff6aedbd79bc0cf9343810`

Part 1, Part 2 and Part 3 docs/memory cleanup are checkpointed/pushed.

Part 4 top-level docs/ledgers refresh is checkpointed/pushed.

The focused docs/memory cleanup Parts 1-4 is complete.

The minor Games startup/catalog cleanup is runtime validated and checkpointed:
- startup reconciliation detected the changed library and reconciled 124/124 games;
- 39 artwork files were downloaded, 80 were reused from cache, and 5 had no usable artwork;
- a later startup returned `SKIPPED_CURRENT` with 124 discovered / 124 metadata entries;
- the player-facing `Native Streaming Alpha` catalog node is removed;
- native-stream status/start/stop endpoints and `NativeStreamActivity` remain preserved;
- normal game picture/audio/controller regression passed.

C1 schema design and its durable-memory update are checkpointed/pushed.

C1.1 static reference profile extraction is runtime validated and checkpointed/pushed.

The native-stream public-status privacy hotfix is live-endpoint validated and checkpointed/pushed.

Next work: remote-foundation architecture/roadmap documentation update before deeper Phase C implementation.

Do not rerun the completed C1 inventory unless source changes invalidate it.

## Development position

- Phase A — Games / emulator subsystem: **COMPLETE / PUSHED**
- Phase B — Diagnostics + clean native baseline: **COMPLETE / PUSHED**
- Phase C — Adaptive native streaming: **ACTIVE**
- C1 inventory: **COMPLETE / `C1_INVENTORY_COMPLETE`**
- Part 4 docs refresh: **COMPLETE / CHECKPOINTED / PUSHED**

## C1 design direction

Reference path:

`WGC -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Reference behavior:

- 1280x720;
- 60 fps;
- 7000 kbps;
- GOP 15;
- B-frames 0;
- FEC group size 8;
- RTP PT 96;
- packet size 1200 bytes.

Reference profile `native_game_720p60_reference` is design-fixed as:

- `id`: `native_game_720p60_reference`
- `width`: 1280
- `height`: 720
- `fps`: 60
- `bitrate_kbps`: 7000
- `max_bitrate_kbps`: 7000
- `gop_frames`: 15
- `bframes`: 0
- `fec_group_size`: 8

Do not add `min_bitrate_kbps` in C1.1 because the validated baseline has no existing lower-bound behavior to preserve.

`fec_group_size` is portable C1 profile data and must validate to 1-8 because the current PHF1 marker mask is one byte.

Keep NVENC codec/preset/tune/RC/buffer/pixel-format policy, RTP payload type, packet size, ports, capture backend, audio, controller protocol and telemetry cadence outside the portable C1.1 profile.

C1.1 is companion-only static extraction. Preserve Android constants/startup ordering; keep existing top-level host status fields and add inspectable `profile_id` plus nested profile data. No selector, adaptation, generalized backend framework, capture/audio/input redesign or wire-format change.

## Regression contract

Representative C1 runtime validation must preserve:

- picture;
- process audio;
- controller input;
- Pause / Resume;
- Save / Load;
- End / teardown;
- validated game/profile behavior.

## Stable subsystems

Preserve unless fresh evidence requires change:

- WGC/NVENC native video;
- process-specific audio;
- UDP/FEC;
- Android hardware AVC;
- PHI1/ViGEm P1-P4;
- Save/Load/Pause/End;
- A8 profiles;
- PS1 manual Port-1-only multitap;
- Phase B diagnostics/Self-Test/support bundle/retention.

Coverage:

- PS1 — extensive;
- SNES — runtime exercised;
- NES — configured/supported, no local A9 fixture;
- Genesis — configured/supported, no local A9 fixture.

## Phase B result

Complete/runtime validated:

- health/resource model and endpoint;
- Android client health feedback;
- classifier corrections;
- bounded event history;
- Diagnostics / Self-Test GUI;
- sanitized support bundle;
- bounded/manual retention;
- Sunshine/Moonlight production/artifact removal;
- native-only regression and clean-native checkpoint.

Raw measurements outrank classifiers.

## Roadmap

`docs/ROADMAP.md` roadmap v4 is authoritative.

After C:

- D Media Library / VOD / Live TV UX
- E Linux Migration / Native Linux Baseline
- F Linux Core Resource Characterization & Optimization
- G Secure Remote Access / Portable Client Foundation
- H Extended Emulation & User-Content Import
- I Home Infrastructure / Broader Plugin Expansion
- J Local Intelligence / Voice / Privacy-Aware AI

Phase C must remain reusable for future WAN paths while WAN implementation stays
deferred to Phase G.

D-059 establishes:

- home Opal = PrivyHub trust/network domain;
- ordinary household network = upstream only;
- Tailscale = preferred first overlay candidate, not permanent contract;
- overlay transport != PrivyHub authorization;
- source/request IP != durable client identity;
- no permanent travel-router model selected yet;
- deferred UDP replay target = Linux + home Opal + onn.

Remote implementation is **PLANNED ONLY**.

The remote-foundation documentation update is **CHECKPOINTED / PUSHED**.

## Commands

Android build/install:

`.\tools\build_install_onn.ps1; cd L:\Projects\onn-stream-test`

Companion:

`python .\companion\privyhub_service.py`

Existing C1 inventory evidence:

`logs/streaming/c1_stream_profile_inventory.txt`

## Working rules

- Inspect exact current local source before patching.
- Use exact predecessor hashes/state.
- Back up changed files under `archive/patch_backups`.
- Validate deterministic output before delivery.
- Roll back exact bytes on deterministic validation failure.
- Keep install and checkpoint/push as separate stages.
- Update durable memory with meaningful work.
- Never ask for or expose network addresses in shareable diagnostics.

## C1.1 static reference profile extraction — development state

**Status:** RUNTIME VALIDATED / CHECKPOINTED / PUSHED

Implementation:
- added `companion/native_stream_profiles.py`;
- defines immutable `NativeStreamProfile`;
- defines `native_game_720p60_reference`;
- `NativeStreamManager` now derives the prior width/height/fps/bitrate/GOP/
  B-frame/FEC constants from that profile;
- FFmpeg `-maxrate` explicitly consumes `max_bitrate_kbps`;
- FFmpeg `-bf` explicitly consumes `bframes`;
- the FEC relay still uses the same 8-packet group through the profile-derived
  manager constant;
- native-stream status preserves existing top-level fields and adds
  `profile_id` plus nested `profile`.

Intentionally unchanged:
- Android source/startup ordering;
- WGC capture ownership;
- H.264 NVENC backend/preset/tune/RC/buffer/pixel format;
- RTP payload type, packet size and ports;
- FEC wire format;
- audio and controller paths;
- GUI/profile selection and adaptation.

Representative game runtime regression passed the C1.1 acceptance boundary.

## Native-stream status privacy hotfix — 2026-09-14

**Status:** LIVE ENDPOINT VALIDATED / CHECKPOINTED / PUSHED

A C1.1 runtime status review found that public native-stream status inherited the
process-audio helper's raw status object. That exposed a client network
identifier and an absolute local diagnostics path.

Root cause:
- `NativeAudioStreamer.status()` returned `_read_status()` wholesale as
  `helper_status`;
- the same method exposed its timing-log `Path` as an absolute string.

Hotfix boundary:
- raw helper JSON remains unchanged in local runtime/data storage;
- public `helper_status` is a recursively sanitized copy;
- network-address fields and valid embedded IPv4/MAC identifiers are redacted;
- helper path fields are redacted;
- public top-level `timing_log` is project-relative when available;
- public strings containing the project-root prefix use `<project-root>`.

Intentionally unchanged:
- process-audio capture/pacing/packetization and raw local diagnostics;
- video/FEC/controller behavior;
- Android;
- C1.1 profile values and stream behavior.

The live native-stream status endpoint passed the bounded privacy validator.

## Immediate continuation after remote-foundation checkpoint

Resume Phase C.

Preserve D-059:
- Phase C artifacts must remain reusable for future WAN paths;
- WAN overlay/auth/travel-router implementation remains Phase G work.
