---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 65d02012409440d5559c14beb2b28268b0b225bc
---

# Current Handoff

## Repository state

Authoritative local root:

`L:\Projects\onn-stream-test`

Local source is authoritative between checkpoints. GitHub is reference/history
unless a clean synchronized checkpoint is being verified.

Last synchronized checkpoint before this local Part 4 install:

`65d02012409440d5559c14beb2b28268b0b225bc`

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

Resume technical work at:

`C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`

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

Keep backend/session policy outside the first portable profile unless evidence
requires otherwise.

First profile concept:

`native_game_720p60_reference`

First implementation is static extraction only. No GUI selector, adaptation or
generic framework in that patch.

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

`docs/ROADMAP.md` roadmap v3 is authoritative.

After C:

- D Media Library / VOD / Live TV UX
- E Linux Migration / Native Linux Baseline
- F Linux Core Resource Characterization & Optimization
- G Extended Emulation & User-Content Import
- H Home Infrastructure / Client / Plugin Expansion
- I Local Intelligence / Voice / Privacy-Aware AI

Phase E uses the HP EliteDesk 805 G6 as the Linux reference machine. Phase F
characterizes/optimizes PS1-and-below before cheaper Prototype 2 hardware is
selected.

OpenBIOS is retired as a dedicated phase. Users provide ROM/ISO/BIOS/firmware/
keys through the future import boundary.

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
