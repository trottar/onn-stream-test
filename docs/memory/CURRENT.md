---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 65d02012409440d5559c14beb2b28268b0b225bc
---

# Current Development State

## Checkpoint

- Branch: `main`
- Last synchronized checkpoint: `65d02012409440d5559c14beb2b28268b0b225bc`
- Part 1 current-state alignment: **CHECKPOINTED / PUSHED**
- Part 2 durable-memory curation/deep history: **CHECKPOINTED / PUSHED**
- Part 3 decision/investigation normalization: **CHECKPOINTED / PUSHED**
- Part 4 top-level docs/ledgers refresh: **CHECKPOINTED / PUSHED**
- Docs/memory cleanup Parts 1-4: **COMPLETE / CHECKPOINTED**
- Minor Games cleanup (startup metadata/art reconciliation + Alpha catalog removal): **RUNTIME VALIDATED / CHECKPOINTED / PUSHED**
- Phase A: **COMPLETE / PUSHED**
- Phase B: **COMPLETE / PUSHED**
- Phase C: **ACTIVE**

Next work: technical C1 schema design.

## Active technical step

**C1 — explicit stream profiles**

Inventory result:

`C1_INVENTORY_COMPLETE`

Next classification:

`C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`

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

- `companion/games/native/native_stream.py` — capture/session setup, reference
  quality constants, encoder/backend policy and RTP/FEC/session setup.
- `companion/games/native/native_fec_relay.py` — relay/FEC behavior and
  duplicated transport assumptions.
- Android `NativeStreamActivity.kt` — duplicated width/height/fps and endpoint
  constants.
- Android `RtpH264Receiver.kt` — receive/FEC buffering.

Likely portable profile fields:

- `id`
- `width`
- `height`
- `fps`
- `bitrate_kbps`
- `max_bitrate_kbps`
- `gop_frames`
- `bframes`
- optional `fec_group_size`

Keep backend/session details outside the portable profile unless evidence
requires otherwise: codec/preset/tune/RC/buffer policy, RTP payload type,
packet size, ports, capture backend, audio, controller protocol and telemetry
cadence.

First concept: `native_game_720p60_reference`.

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

`docs/ROADMAP.md` roadmap v3 is authoritative.

- D — Media Library / VOD / Live TV UX
- E — Linux Migration / Native Linux Baseline
- F — Linux Core Resource Characterization & Optimization
- G — Extended Emulation & User-Content Import
- H — Home Infrastructure / Client / Plugin Expansion
- I — Local Intelligence / Voice / Privacy-Aware AI

OpenBIOS is not a dedicated phase. Users supply required game content through
the future import boundary.

HP EliteDesk 805 G6 is the Linux reference prototype, not the minimum target.
Cheaper Prototype 2 hardware is selected from Phase F evidence.

## Debugging and privacy rule

Use:

**one narrow hypothesis -> one targeted diagnostic/probe -> fresh evidence ->
inspect raw measurements -> one coherent patch**

Never ask the user to provide or paste network addresses. Shareable diagnostics
must avoid or redact them.
