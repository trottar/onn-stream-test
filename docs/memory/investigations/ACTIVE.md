---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 45ef51f9e583b459752dd5ea83163f54171e68c7
---

# Active Investigations

This file contains only current active/queued work. The exact pre-Part-3
`ACTIVE.md` is preserved as superseded deep memory at:

`docs/memory/history/ACTIVE_INVESTIGATIONS_SUPERSEDED_THROUGH_2026-09-11.md`

Resolved Phase A and Phase B investigation detail is summarized in `CLOSED.md`
and remains fully recoverable from that deep-memory snapshot, dated memory,
evidence, patch history and Git history.

## Docs/memory normalization

**Status:** COMPLETE / CHECKPOINTED / PUSHED

Part 1 current-state alignment and Part 2 durable-memory curation are
checkpointed/pushed.

Part 3 normalizes decision IDs and investigation state. After independent
validation/checkpoint, Part 4 refreshes top-level project docs and ledgers.

This work changes no production/runtime behavior.

## C1 explicit stream profile schema design

**Status:** RUNTIME VALIDATED / CHECKPOINTED / PUSHED

C1 inventory is complete:

`C1_INVENTORY_COMPLETE`

Design classification:

`C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA` — **COMPLETE**

Implementation classification:

`C1_IMPLEMENT_STATIC_REFERENCE_PROFILE_EXTRACTION` — **RUNTIME VALIDATED / CHECKPOINTED / PUSHED**

Do not rerun the inventory unless source changes invalidate it.

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

## Architecture transition

C1.1 and the native-stream public-status privacy hotfix are checkpointed/pushed.

The accepted remote-foundation architecture/roadmap documentation update is
checkpointed/pushed.

Continue Phase C with D-059 as a design constraint: future WAN reuse is
required; WAN implementation remains deferred to Phase G.

## C2 end-to-end telemetry contract

**Status:** ACTIVE — C2.1 INVENTORY COMPLETE / C2.2 DESIGN CHECKPOINTED / PUSHED

Inventory:

`C2_INVENTORY_COMPLETE_EXISTING_FOUNDATION_WITH_GAPS`

Design:

`C2_DESIGN_MINIMAL_STREAM_TELEMETRY_V1`

Next:

`C2_IMPLEMENT_STREAM_TELEMETRY_V1`

No adaptive controller yet.

Implementation must preserve D-059/D-060 and the existing video/audio/controller
wire/lifecycle behavior.

## C2 telemetry v1 runtime validation

**Status:** CLOSED / RUNTIME VALIDATED 2026-09-14

Validated:
- `privyhub_stream_telemetry_v1` live endpoint;
- receiver jitter;
- control-path round trip;
- sender deltas/timing;
- signed queue-depth delta;
- absence of adaptation fields;
- normal picture/process-audio/controller behavior;
- Pause/Resume, Save/Load and End/teardown.

See `evidence/C2_STREAM_TELEMETRY_RUNTIME_VALIDATED_2026-09-14.md`.

C3 adaptive bitrate is next after checkpoint/push.

## C3 fixed-bitrate characterization

**Active.**

First candidate: 6000 kbps — **VALIDATED**.

Next question: is fixed 5000 kbps acceptable at unchanged 720p60/GOP15/B-frames0/FEC8?

Evidence must include post-cycle C2 telemetry, final decoder-session report and
focused manual image-quality/stutter observation.

See `C3_FIXED_BITRATE_CHARACTERIZATION.md`.

## 6000 result / 5000 next

6000 kbps: **VALIDATED CANDIDATE**.

Video/gameplay acceptance:
- movement/gameplay fine;
- receiver recovered cleanly;
- one decoder drop and one queue-overflow drop retained as raw evidence.

Audio:
- audible stutter observed;
- not attributed to 6000;
- receiver simultaneously showed queue overflow trimming and prolonged
  starvation/concealment;
- existing audio/transport burstiness remains deferred to Linux + Home-Opal
  replay.

Next single candidate: 5000 kbps.

## C3 5000 characterization active

**Active / runtime evidence pending.**

5000 kbps is the only current lower candidate.

Validated levels remain 7000 and 6000 kbps.

The known audio queue burst/gap pathology is explicitly out of scope for bitrate
rejection unless new 5000-specific evidence establishes causation. Detailed
audio counters are still captured for comparison.

## 5000 disposition / 5500 bracket test

5000 kbps is **not accepted** as a ladder candidate.

Primary reason: definite increase in steady-state visual stutters during
extended focused play compared with the validated settings.

Image clarity was subjectively good/clearer and restart recovery was clean, so
5000 remains useful as the lower side of the bitrate bracket rather than being
classified as an encoder-start failure.

Active next question:
**Does 5500 kbps recover the smoothness of 6000 while retaining the lower
bandwidth target?**
