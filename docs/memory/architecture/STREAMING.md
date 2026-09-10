---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Native Streaming Architecture

## Current Games baseline

Video path:

`managed RetroArch window -> Windows Graphics Capture -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC decoder`.

Stable reference profile is 1280x720 at 60 fps, approximately 7 Mbps, low-latency P1 encoder behavior, GOP 15, no B-frames, and roughly 1200-byte RTP payload sizing.

Capture is fail-closed: failure to identify the managed game window must not silently broaden capture to the desktop.

## Audio

The host captures the exact managed RetroArch process through process-specific Windows loopback. Android uses a deliberately small low-latency PCM queue. A4 lifecycle recovery is runtime validated; do not reopen without regression evidence.

## Future

Phase C will make 720p60 and 1080p60 explicit profiles and generalize capture/source infrastructure for Games, browser/application streams, cameras, and other live sources. Generalization should follow the proven Games implementation rather than replace it prematurely.
