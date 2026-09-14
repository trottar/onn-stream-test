---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 0c31c100ec721d687aff6aedbd79bc0cf9343810
---

# Current Development State

## Checkpoint

- Branch: `main`
- Predecessor synchronized checkpoint for the remote-foundation promotion: `0c31c100ec721d687aff6aedbd79bc0cf9343810`
- Part 1 current-state alignment: **CHECKPOINTED / PUSHED**
- Part 2 durable-memory curation/deep history: **CHECKPOINTED / PUSHED**
- Part 3 decision/investigation normalization: **CHECKPOINTED / PUSHED**
- Part 4 top-level docs/ledgers refresh: **CHECKPOINTED / PUSHED**
- Docs/memory cleanup Parts 1-4: **COMPLETE / CHECKPOINTED**
- Minor Games cleanup (startup metadata/art reconciliation + Alpha catalog removal): **RUNTIME VALIDATED / CHECKPOINTED / PUSHED**
- Phase A: **COMPLETE / PUSHED**
- Phase B: **COMPLETE / PUSHED**
- Phase C: **ACTIVE**

C1 minimal schema design: **COMPLETE / CHECKPOINTED / PUSHED**

C1.1 static reference profile extraction: **RUNTIME VALIDATED / CHECKPOINTED / PUSHED**

Native-stream status privacy hotfix: **LIVE ENDPOINT VALIDATED / CHECKPOINTED / PUSHED**

Next work: remote-foundation architecture/roadmap documentation update before deeper Phase C implementation.

## Active technical step

**C1 — explicit stream profiles**

Inventory result:

`C1_INVENTORY_COMPLETE`

Design classification:

`C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA` — **COMPLETE**

Implementation classification:

`C1_IMPLEMENT_STATIC_REFERENCE_PROFILE_EXTRACTION` — **RUNTIME VALIDATED / CHECKPOINTED / PUSHED**

Do not rerun the inventory unless source changes invalidate it.

## C1 reference stream

Validated path:

`Windows Graphics Capture -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Reference values:

- 1280x720;
- 60 fps;
- 7000 kbps target;
- GOP 15;
- B-frames 0;
- FEC group size 8;
- RTP payload type 96;
- packet size 1200 bytes.

Backend policy also includes NVENC `p1`, ultra-low-latency tuning, CBR, a 1000k
buffer and yuv420p. Those are not automatically portable profile semantics.

## C1 ownership findings

- `companion/native_stream.py` — capture/session setup, reference
  quality constants, encoder/backend policy and RTP/FEC/session setup.
- `companion/native_fec_relay.py` — relay/FEC behavior and
  duplicated transport assumptions.
- Android `NativeStreamActivity.kt` — duplicated width/height/fps and endpoint
  constants.
- Android `RtpH264Receiver.kt` — receive/FEC buffering.

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

## First C1 acceptance boundary

The first implementation is behavior-preserving static extraction only:

- same 1280x720 @ 60 fps;
- same 7000 kbps target;
- same GOP 15;
- same 8+1 FEC contract;
- no GUI selector;
- no adaptive controller;
- no generalized backend framework;
- no capture/audio/controller/lifecycle redesign.

Representative regression must preserve picture, process audio, controller,
Pause/Resume, Save/Load, End/teardown and validated game/profile behavior.

## Runtime coverage to preserve

Runtime validated:

- extensive PS1 path;
- SNES normal Games path;
- 1P/2P/4P controller routing;
- Crash Bash/CTR Port-1-only manual multitap;
- Save/Load and prior saves;
- pause/resume/frozen preview;
- process audio / host coexistence;
- cheats/mods/A8 profiles;
- native streaming and teardown;
- Phase B diagnostics/Self-Test/support bundle/retention;
- native-only post-Sunshine/Moonlight regression.

Declared no-fixture gaps:

- NES — supported/configured, no local A9 fixture;
- Genesis — supported/configured, no local A9 fixture.

## Preservation boundaries

Do not reopen without new evidence:

- WGC capture;
- H.264 NVENC low-latency path;
- native process audio;
- UDP/FEC transport;
- Android hardware AVC decode;
- PHI1/ViGEm P1-P4;
- Save/Load/Pause/End;
- A8 profiles;
- PS1 Port-1-only multitap;
- Phase B diagnostics/support-bundle behavior.

## Roadmap

`docs/ROADMAP.md` roadmap v4 is authoritative.

- D — Media Library / VOD / Live TV UX
- E — Linux Migration / Native Linux Baseline
- F — Linux Core Resource Characterization & Optimization
- G — Secure Remote Access / Portable Client Foundation
- H — Extended Emulation & User-Content Import
- I — Home Infrastructure / Broader Plugin Expansion
- J — Local Intelligence / Voice / Privacy-Aware AI

Phase C remains active. Its profiles, telemetry, adaptation/FEC behavior and
streaming boundaries must be reusable for future WAN work without implementing
WAN overlay/auth/travel-router behavior during Phase C.

Home trust boundary: home Opal.

Ordinary household network: upstream only.

Tailscale is the preferred first overlay candidate, not the permanent contract.
No permanent travel-router model is selected yet.

Before Phase G WAN characterization, replay the deferred UDP suite on the
representative `Linux + home Opal + onn` path.

## Debugging and privacy rule

Use:

**one narrow hypothesis -> one targeted diagnostic/probe -> fresh evidence ->
inspect raw measurements -> one coherent patch**

Never ask the user to provide or paste network addresses. Shareable diagnostics
must avoid or redact them.

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

Representative game runtime regression confirmed picture, process audio,
controller input, Pause/Resume, Save/Load and End/teardown with the
reference profile/status values preserved.

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

The live native-stream status endpoint passed the bounded privacy validator:
no network identifiers, absolute paths or unsafe keyed values were exposed.

## Remote-foundation architecture decision

D-059 is accepted.

Remote implementation remains **PLANNED ONLY**.

Future Phase G separates client identity, session identity, reachable
media/audio/controller endpoints, overlay/path state and PrivyHub application
authorization. Source/request IP is not durable client identity.

Future WAN adaptation protects interactivity by degrading quality before
queue/buffer growth creates runaway latency.

The current reference session planning envelope is roughly 10-11 Mbps outbound;
this does not change the stable PCM audio path.

Documentation update status: **CHECKPOINTED / PUSHED**.

## Next technical work after architecture checkpoint

The remote-foundation architecture/roadmap promotion is checkpointed/pushed.

Resume deeper Phase C implementation under D-059. Do not implement WAN overlay,
remote authentication or travel-router routing in Phase C.
