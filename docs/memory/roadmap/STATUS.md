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
CHECKPOINTED / PUSHED**

The live telemetry contract and representative gameplay regression passed on
2026-09-14.

**Next:** C3 actuator continuity diagnostic under D-062.

## Active item: C3 adaptive bitrate

### C3.1 source/policy audit

`C3_DESIGN_CONTROLLER_ACTUATOR_BOUNDARY` — **COMPLETE**

Decision: D-062.

### Next diagnostic

`C3_ACTUATOR_CONTINUITY_PROBE`

Keep bitrate unchanged at 7000 kbps and test one prospective video-only actuator
cycle before automatic adaptation or a production minimum bitrate is defined.

## C3 actuator continuity diagnostic state

`C3_ACTUATOR_CONTINUITY_PROBE` — **RUNTIME VALIDATED / INITIAL ACTUATOR
STRATEGY ACCEPTED / CHECKPOINT PENDING**

The probe is companion-only and holds bitrate at 7000 kbps. Android remains
unchanged.

Next: capture runtime evidence plus manual picture/audio/controller/
Pause/Resume/Save/Load/End behavior, then choose the actuator boundary.

## C3 actuator accepted

`video_only_restart` — **ACCEPTED INITIAL C3 STRATEGY / WINDOWS RUNTIME
VALIDATED / LINUX REVALIDATION REQUIRED**

No production minimum bitrate or adaptive controller exists yet.

### Next

`C3_FIXED_BITRATE_CHARACTERIZATION`

Characterize lower fixed bitrates while preserving 1280x720@60, GOP15,
B-frames0 and FEC8. Only evidence-backed levels may enter the production ladder.

## C3 fixed-bitrate characterization

`C3_FIXED_6000_CHARACTERIZATION` — **RUNTIME VALIDATED CANDIDATE**

6000 kbps is the first validated lower bitrate candidate. It is a validated
candidate, not yet the production minimum.

`C3_FIXED_5000_CHARACTERIZATION` — **RUNTIME TESTED / NOT ACCEPTED AS LADDER CANDIDATE**

The known audio burst/gap pathology remains separate from bitrate
characterization and stays deferred for representative Linux + Home-Opal
replay.

## C3 fixed 5000 characterization installed

Validated bitrate candidates:
- 7000 kbps;
- 6000 kbps.

5000 kbps:
**DEVELOPMENT DIAGNOSTIC INSTALLED / RUNTIME EVIDENCE PENDING**

No production minimum is set. Automatic bitrate control remains unimplemented.

Audio burst/gap pathology remains deferred to Linux + Home Opal and is reported,
not silently treated as a 5000 failure.

## C3 5000 disposition / 5500 next

Validated bitrate candidates:
- 7000 kbps;
- 6000 kbps.

5000 kbps:
**RUNTIME TESTED / NOT ACCEPTED**

Primary reason: more steady-state visual stutters during focused extended play.

Current lower-bound bracket:
**5000–6000 kbps**

Next:
`C3_FIXED_5500_CHARACTERIZATION` — **RUNTIME VALIDATED LOWER CANDIDATE / WINDOWS FLOOR**

Production minimum remains unset. Automatic bitrate control remains
unimplemented. Audio burst/gap pathology remains deferred to Linux + Home
Opal.

## C3 fixed 5500 characterization installed

Current bitrate state:
- 7000 kbps: validated;
- 6000 kbps: validated;
- 5000 kbps: runtime tested / not accepted;
- 5500 kbps: **DEVELOPMENT DIAGNOSTIC INSTALLED / RUNTIME EVIDENCE PENDING**.

Pre-test bracket: **5000–6000 kbps**.

Production minimum remains unset. Automatic bitrate control remains
unimplemented.

Audio burst/gap pathology remains deferred to Linux + Home Opal and is reported,
not silently treated as a 5500 failure.

## C3 fixed ladder frozen for Windows controller prototype

Validated fixed levels:
- 7000 kbps — high/reference;
- 6000 kbps — medium;
- 5500 kbps — low/current Windows floor.

Excluded:
- 5000 kbps — runtime tested / not accepted.

`C3_FIXED_BITRATE_CHARACTERIZATION` — **COMPLETE / WINDOWS RUNTIME VALIDATED**

`C3_ADAPTIVE_BITRATE_CONTROLLER` — **NEXT / NOT YET IMPLEMENTED**

The 5500 final report contains 57 whole-session decoder drops/overflows, while
the stored 5.5–15.5-second post-cycle telemetry window contains zero drop/overflow
deltas across 638 rendered frames. Preserve both facts.

Audio burst/gap pathology remains deferred to Linux + Home Opal.

Linux migration must revalidate the actuator/fixed envelope.
