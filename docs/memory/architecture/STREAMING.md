---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: aa82ff13e01d5d16cf334d667f8f17e7537cae56
---

# Native Streaming Architecture

## Current Games baseline

Video path:

`managed RetroArch window -> Windows Graphics Capture -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC decoder`.

Stable reference profile is 1280x720 at 60 fps, approximately 7 Mbps, low-latency P1 encoder behavior, GOP 15, no B-frames, and roughly 1200-byte RTP payload sizing.

Capture is fail-closed: failure to identify the managed game window must not silently broaden capture to the desktop.

## Audio

The host captures the exact managed RetroArch process through process-specific Windows loopback. Android uses a deliberately small low-latency PCM queue. A4 lifecycle recovery is runtime validated; do not reopen without regression evidence.

## C1 explicit-profile design

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

## Future

After the static reference profile is runtime validated, later Phase C work may add client-side profile consumption, additional profiles, telemetry and adaptation. Generalization should follow the proven Games implementation rather than replace it prematurely.

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

The live native-stream status endpoint passed the bounded privacy validator.
