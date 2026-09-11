---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 8f25763fca012257a3695ede03004fc9a368966a
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

**Status:** DESIGN COMPLETE / IMPLEMENTATION NEXT

C1 inventory is complete:

`C1_INVENTORY_COMPLETE`

Design classification:

`C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA` — **COMPLETE**

Next technical classification:

`C1_IMPLEMENT_STATIC_REFERENCE_PROFILE_EXTRACTION`

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
