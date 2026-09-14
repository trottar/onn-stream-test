---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 45ef51f9e583b459752dd5ea83163f54171e68c7
---

# Roadmap Status

## Current position

| Phase | Status | Current meaning |
| --- | --- | --- |
| A — Games / Emulator Subsystem | **COMPLETE / PUSHED** | Runtime-validated native game, controller, Save/Load, profile and PS1 multitap baseline |
| B — Diagnostics & Clean Native Baseline | **COMPLETE / PUSHED** | Diagnostics/Self-Test/support bundle/retention complete; Sunshine/Moonlight removed; native regression passed |
| C — Adaptive Native Streaming | **ACTIVE** | Profiles/telemetry/adaptation with future-Phase-G WAN reuse in mind |
| D — Media Library / VOD / Live TV UX | PLANNED | Media-library and substantial Live TV/EPG/guide work |
| E — Linux Migration / Native Linux Baseline | PLANNED | Move core server path to Linux reference prototype |
| F — Linux Core Resource Characterization & Optimization | PLANNED | Optimize and size PS1-and-below on Linux |
| G — Secure Remote Access / Portable Client Foundation | FUTURE AFTER F | Overlay/provider abstraction, travel-router trusted LAN, WAN identity/auth and off-site Core validation |
| H — Extended Emulation & User-Content Import | FUTURE AFTER G | Safe content import, then N64/GameCube/PS2 local + remote regression |
| I — Home Infrastructure / Broader Plugin Expansion | FUTURE | Home Assistant/devices, cameras/microphones, storage and broader clients/providers |
| J — Local Intelligence / Voice / Privacy-Aware AI | FUTURE | Local-first intelligence with optional explicit external providers |

`docs/ROADMAP.md` roadmap v4 is authoritative for phase definitions.

## Completed item: C1 explicit stream profiles

### Inventory

**COMPLETE**

Result:

`C1_INVENTORY_COMPLETE`

Reference stream:
- 1280x720;
- 60 fps;
- 7000 kbps;
- GOP 15;
- B-frames 0;
- 8+1 XOR FEC;
- H.264 NVENC over the native RTP-sized UDP path;
- Android hardware AVC decode.

### Design

`C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA` — **COMPLETE**

### C1.1 implementation

`C1_IMPLEMENT_STATIC_REFERENCE_PROFILE_EXTRACTION` — **RUNTIME VALIDATED / CHECKPOINTED / PUSHED**

The first profile patch should:
1. name the existing reference behavior explicitly;
2. separate portable profile semantics from backend/wire/session mechanics;
3. make the active profile inspectable;
4. preserve current stream behavior exactly;
5. avoid a GUI selector or adaptive controller until the static profile is
   runtime validated.

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

## C1 acceptance gate

**Result: PASSED / CHECKPOINTED / PUSHED**

Before C2:
- explicit reference profile is active and visible to diagnostics/status;
- stream remains 720p60 / 7000 kbps / GOP15 / 8+1 FEC;
- normal picture/audio/controller operation passes;
- Pause/Resume, Save/Load and End/teardown pass;
- no regression in existing game/profile behavior.

## Active item: C2 end-to-end transport telemetry

### C2.1 inventory

**COMPLETE**

Result:

`C2_INVENTORY_COMPLETE_EXISTING_FOUNDATION_WITH_GAPS`

Existing production foundation already provides receiver Mbps/FPS, loss/FEC
counters, decoder queue state, stale/overflow drops, rendered continuity and
receive/decode/output-gap timing.

### C2.2 minimal design

`C2_DESIGN_MINIMAL_STREAM_TELEMETRY_V1` — **COMPLETE / CHECKPOINTED / PUSHED**

Use a companion-side `privyhub_stream_telemetry_v1` measurement snapshot.

Add only:
- receiver RFC-style inter-arrival jitter;
- control-path round trip from the existing client-health POST;
- signed decoder queue-depth change;
- FEC-relay send pressure/timing.

No second telemetry loop and no adaptive controller.

### Next implementation

`C2_IMPLEMENT_STREAM_TELEMETRY_V1`

Acceptance before C3:
- contract is inspectable;
- optional new client fields tolerate older reports;
- measurements remain fail-open and do not disturb gameplay;
- no transport/wire/profile behavior changes;
- representative runtime telemetry is captured and reviewed.

## Post-C direction

Accepted continuation:

`D -> E -> F -> G Remote -> H Extended Emulation -> I Home Infrastructure -> J Intelligence`

Constraints:

- Live TV remains Phase D work.
- HP EliteDesk 805 G6 is the Linux reference prototype, not the minimum target.
- Choose cheaper Prototype 2 hardware from measured Phase F evidence.
- Phase F Core sizing remains PS1-and-below.
- Phase G establishes secure remote/portable-client infrastructure before
  heavier emulator families.
- Phase H establishes user-content import before later-console feasibility work.
- Phase C artifacts must remain reusable by Phase G without implementing WAN
  plumbing during C.
- Tailscale is the preferred first overlay candidate, not the permanent
  architecture contract.
- Source/request IP is not durable client identity.
- No permanent travel-router model is selected yet.
- Replay deferred UDP evidence on Linux + home Opal + onn before WAN
  characterization.
- OpenBIOS is not a dedicated project phase.

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

## Immediate repository action

Implement and runtime-validate `C2_IMPLEMENT_STREAM_TELEMETRY_V1`.

Do not begin adaptive bitrate until the C2 telemetry contract is validated.

## C2 implementation state

`C2_IMPLEMENT_STREAM_TELEMETRY_V1` — **COMPLETE / RUNTIME VALIDATED /
CHECKPOINT PENDING**

The live telemetry contract and representative gameplay regression passed on
2026-09-14.

**Next:** C3 adaptive bitrate after checkpoint/push of this validated C2 + ADB
tooling state.
