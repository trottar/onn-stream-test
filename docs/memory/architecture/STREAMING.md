---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 8f25763fca012257a3695ede03004fc9a368966a
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
