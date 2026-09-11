---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: a6dbf627dd32af7da975bf01a679350810026ca3
---

# Current Handoff

## Repository state

Authoritative local root:

`L:\Projects\onn-stream-test`

Local source is authoritative between checkpoints. GitHub is reference/history
unless explicitly requested otherwise.

Part 1 + C1 inventory checkpoint parent:

`a6dbf627dd32af7da975bf01a679350810026ca3`

The completed C1 inventory memory/probe is checkpointed together with the Part 1
current-state repair so it cannot be lost during Part 2 curation.

Immediate next work is **Part 2 docs/memory curation**. Do not begin C1
production implementation until that focused cleanup is complete.

## Development position

- Phase A — Games / emulator subsystem: **COMPLETE / PUSHED**
- Phase B — Diagnostics + clean native baseline: **COMPLETE / PUSHED**
- Phase C — Adaptive native streaming: **ACTIVE**
- Current item: **C1 explicit stream profiles**
- C1 inventory: **COMPLETE**
- Immediate next classification: `C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`

Do not rerun the C1 inventory unless source changes invalidate it.

## C1 inventory result

`C1_INVENTORY_COMPLETE`

No inventory failures were reported.

Validated native game path:

`WGC -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Reference behavior:
- 1280x720
- 60 fps
- 7000 kbps
- GOP 15
- B-frames 0
- FEC group size 8
- RTP payload type 96
- packet size 1200 bytes
- NVENC `p1` / ultra-low-latency / CBR / 1000k buffer / yuv420p

Ownership:
- `native_stream.py` owns capture/session setup, quality constants, encoder policy,
  RTP/FEC/session ports.
- `native_fec_relay.py` owns relay/FEC behavior and duplicates part of the wire contract.
- `NativeStreamActivity.kt` duplicates width/height/fps and endpoint constants.
- `RtpH264Receiver.kt` owns receive/FEC buffering.

## C1 design direction

The first implementation should be a narrow behavior-preserving extraction, not
a generic streaming-framework rewrite.

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

Keep outside the portable profile unless later evidence requires them:
- NVENC codec/preset/tune/RC/buffer settings;
- RTP payload type / packet size;
- ports;
- capture backend;
- audio implementation;
- controller/input protocol;
- telemetry cadence.

First profile concept:

`native_game_720p60_reference`

Do not expose a GUI selector in the first C1 patch. Do not add bitrate adaptation
until the explicit static profile is independently validated.

## C1 regression contract

The first C1 patch must reproduce:
- 1280x720 @ 60 fps;
- 7000 kbps;
- GOP 15;
- 8+1 FEC;
- the same WGC/NVENC path;
- the same Android hardware decoder path.

Representative runtime validation must confirm:
- picture;
- audio;
- controller;
- Pause / Resume;
- Save / Load;
- End / teardown;
- prior game/profile behavior.

## Stable subsystems

Do not disturb without evidence:
- WGC native capture;
- NVENC low-latency encoding;
- process audio;
- UDP/FEC;
- Android hardware AVC decode;
- PHI1/ViGEm P1-P4;
- Save/Load/Pause/End;
- A8 controller profiles;
- PS1 Port-1-only multitap;
- Phase B diagnostics / Self-Test / support-bundle pipeline.

PS1 has the strongest game runtime coverage, including 1P/2P/4P, Crash Bash and
CTR multitap, Save/Load, cheats/mods and input mapping. SNES was runtime
exercised. NES and Genesis were supported/configured but had no local A9 fixture.

## Phase B result

Phase B delivered and validated:
- unified health/resource model;
- read-only health endpoint;
- 2-second Android client feedback reusing the existing metrics cadence;
- corrected decoder/network classifier semantics;
- bounded event history;
- Diagnostics / Self-Test GUI;
- sanitized support-bundle collection;
- manual bounded retention;
- Sunshine/Moonlight production-edge and artifact removal;
- focused native-only regression;
- clean-native repository checkpoint.

Raw measured evidence outranks classifier output when they disagree.

## Roadmap

`docs/ROADMAP.md` roadmap v3 is authoritative.

After C:
- D Media Library / VOD / Live TV UX
- E Linux Migration / Native Linux Baseline
- F Linux Core Resource Characterization & Optimization
- G Extended Emulation & User-Content Import
- H Home Infrastructure / Client / Plugin Expansion
- I Local Intelligence / Voice / Privacy-Aware AI

Phase D includes remaining Live TV identity/deduplication,
favorites/search/pagination, EPG matching/cache/timezone diagnostics and guide UX.

Phase E moves the core server to the HP EliteDesk 805 G6 Linux reference machine.
Phase F performs representative Linux optimization/resource characterization
with PS1-and-below before selecting cheaper Prototype 2 hardware.

OpenBIOS is retired from the roadmap. Future game-content import assumes users
supply ROM/ISO/BIOS/firmware/keys; PrivyHub validates/hashes/copies them into the
runtime layout and keeps them out of Git/support bundles.

Local deterministic control remains the baseline for later intelligence work.
External AI providers may be explicit user-configured options with privacy/data
minimization and no silent fallback.

## Commands

Android build/install:

`.\tools\build_install_onn.ps1; cd L:\Projects\onn-stream-test`

Companion:

`python .\companion\privyhub_service.py`

Existing C1 inventory evidence:

`logs/streaming/c1_stream_profile_inventory.txt`

## Working rules

- Inspect exact current local source before patching.
- Preserve current uncommitted C1 work.
- Use exact predecessor hashes/state in installers.
- Back up changed files under `archive/patch_backups`.
- Validate generated output before delivery.
- Roll back exact bytes on deterministic validation failure.
- Update durable memory with meaningful work.
- Never ask for or expose network addresses in shareable diagnostics.
