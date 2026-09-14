---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: aa82ff13e01d5d16cf334d667f8f17e7537cae56
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

## Checkpoint transition

C1.1 and the native-stream public-status privacy hotfix are checkpointed/pushed.
Before deeper Phase C implementation, apply the accepted remote-foundation
architecture/roadmap documentation update.
