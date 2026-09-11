---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: a6dbf627dd32af7da975bf01a679350810026ca3
---

# Current Development State

## Checkpoint

- Branch: `main`
- Checkpoint scope: Part 1 current-state repair plus completed C1 inventory/memory/probe
- Checkpoint parent: `a6dbf627dd32af7da975bf01a679350810026ca3`
- Phase B clean-native baseline and Linux-first roadmap v3 are established
- Phase C is active; C1 inventory is captured in Git before schema implementation
- Part 2 docs/memory curation: **CHECKPOINTED / PUSHED**
- Part 3 decisions/investigations normalization: **CHECKPOINTED / PUSHED**
- Administrative next: **Part 4 top-level docs/ledgers refresh**
- Technical next remains `C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA` after focused docs cleanup
- Phase A: **COMPLETE / PUSHED**
- Phase B: **COMPLETE / PUSHED**
- Phase C: **ACTIVE**

Do not reset or replace the current local C1 work from GitHub. Local source and
fresh runtime evidence remain authoritative between checkpoints.

## Active step

**C1 — explicit stream profiles**

C1 stream-parameter inventory is complete.

Result:

`C1_INVENTORY_COMPLETE`

with no reported inventory failures.

Immediate next step:

`C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`

Do not rerun the inventory unless new source changes invalidate its evidence.

## C1 reference stream

Current validated native game path:

`Windows Graphics Capture -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Reference values:
- 1280x720
- 60 fps
- 7000 kbps target bitrate
- GOP 15
- B-frames 0
- FEC group size 8
- RTP payload type 96
- packet size 1200 bytes

Current encoder implementation also uses NVENC `p1`, ultra-low-latency tuning,
CBR, a 1000k buffer and yuv420p. Those are backend policy, not automatically
portable profile semantics.

## C1 ownership findings

- `companion/games/native/native_stream.py`
  - capture/session setup;
  - quality constants;
  - encoder/backend policy;
  - RTP/FEC/session ports.
- `companion/games/native/native_fec_relay.py`
  - relay/FEC behavior and duplicated transport assumptions.
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/NativeStreamActivity.kt`
  - duplicated width/height/fps and endpoint constants.
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/RtpH264Receiver.kt`
  - receive/FEC buffering behavior.

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

Keep backend/session details outside the portable profile unless later evidence
requires otherwise:
- NVENC codec/preset/tune/RC/buffer settings;
- RTP payload type and packet size;
- ports;
- capture backend;
- audio implementation;
- controller/input protocol;
- telemetry cadence.

First profile concept:

`native_game_720p60_reference`

## C1 acceptance boundary

The first C1 implementation must be behavior preserving:
- same 1280x720 @ 60 fps output;
- same 7000 kbps target;
- same GOP 15;
- same 8+1 FEC contract;
- no GUI profile selector yet;
- no adaptive controller yet;
- no generalized backend framework;
- no capture/audio/controller/lifecycle redesign.

Runtime regression must preserve:
- picture;
- process audio;
- controller input;
- Pause / Resume;
- Save / Load;
- End / teardown;
- validated game/profile behavior.

## Runtime coverage to preserve

Runtime validated:
- SNES normal Games path;
- extensive PS1 path;
- 1P/2P/4P controller routing;
- Crash Bash and CTR Port-1-only multitap;
- Save/Load and prior saves;
- pause/resume/frozen preview;
- process audio and host coexistence;
- cheats/mods/input profiles;
- native streaming and teardown;
- persistent wireless-ADB recovery;
- Phase B diagnostics/Self-Test/support bundle/retention;
- native-only post-Sunshine/Moonlight regression.

Declared no-fixture gaps:
- NES: supported/configured, but no local A9 fixture and therefore not runtime validated.
- Genesis: supported/configured, but no local A9 fixture and therefore not runtime validated.

## Preservation boundaries

Do not reopen validated paths without new evidence:
- WGC capture;
- H.264 NVENC low-latency path;
- native process audio;
- UDP/FEC transport;
- Android hardware AVC decode;
- PHI1/ViGEm P1-P4 controller chain;
- Save/Load/Pause/End lifecycle;
- A8 input profiles;
- PS1 Port-1-only multitap;
- Phase B diagnostics and sanitized support-bundle behavior.

## Active roadmap

`docs/ROADMAP.md` roadmap v3 is authoritative.

Post-C sequence:
- D — Media Library / VOD / Live TV UX
- E — Linux Migration / Native Linux Baseline
- F — Linux Core Resource Characterization & Optimization
- G — Extended Emulation & User-Content Import
- H — Home Infrastructure / Client / Plugin Expansion
- I — Local Intelligence / Voice / Privacy-Aware AI

OpenBIOS is not a dedicated roadmap phase. Required ROM/ISO/BIOS/firmware
content is user supplied through the future import boundary.

The HP EliteDesk 805 G6 is the Linux reference prototype, not the minimum target.
Prototype 2 hardware should be selected from Phase F evidence.

## Debugging and privacy rule

Use:

**one narrow hypothesis -> one targeted diagnostic/probe -> fresh evidence ->
inspect raw measurements -> one coherent patch**

Never ask the user to provide or paste network addresses. Shareable diagnostics
must avoid or redact them.
