# Project status — 2026-09-07

## Goal

PrivyHub is an experiment in building a local-first smart-home/media environment in which inexpensive client devices live on an isolated IoT network and trusted host/server infrastructure provides local services. The current onn Android TV prototype is the first client and test platform. The planned Linux phase is intended to turn temporary Windows-host functionality into more portable, product-representative infrastructure.

## Current topology

Conceptually:

```text
Internet
  |
trusted household network
  |
trusted host / future server
  |
isolated IoT gateway
  |
onn Android TV client and future IoT devices
```

The exact consumer networking hardware used by the first prototype is test-environment infrastructure, not a permanent architectural dependency.

## Working application areas

### TV / IPTV

The TV stack is considered mature enough to leave stable while other platform work proceeds. It includes catalog pagination, SQLite-backed state, hidden channels, favorites, recents, search, reliability information, EPG, channel surfing/fullscreen behavior, grouping/order/overrides, provider handling, backups, preview behavior, and optional discovery helpers.

### Local sources

The companion supports local live/browser/camera sources and dynamically scanned VOD media. The control plane and media plane remain separate.

### Games

Current emulation targets:

- NES — FCEUmm;
- SNES — bsnes;
- Genesis — BlastEm;
- PlayStation — Beetle PSX HW;
- RetroArch 1.22.2 x64 as the project-managed Windows emulator runtime.

Two-player controller input has been verified using two virtual Xbox 360 controllers on the host.

## Native game streaming baseline

### Video — preserve unless new evidence requires change

- 1280x720 at 60 fps;
- H.264 NVENC;
- FFmpeg 8.0.1 pinned for the current GTX 970 / Maxwell-era Windows test host;
- 7 Mbps CBR;
- P1 / ultra-low-latency encoder configuration;
- GOP 15;
- no B-frames;
- 1200-byte RTP packet sizing;
- 8 data + 1 XOR FEC;
- approximately 12 ms loss-only FEC hold;
- Windows Graphics Capture of the exact PrivyHub-managed RetroArch window;
- Android hardware AVC decoding (`c2.realtek.video.avc.decoder` on the current onn prototype).
- observed combined host cost around 13-15% CPU in the stable prototype; occasional Android codec-stall clusters are tracked separately from the UDP audio investigation.

The capture path is intentionally fail-closed: inability to identify the managed game window must not silently broaden capture to the desktop.

### Audio — production baseline

Host capture:

- process-specific Windows WASAPI loopback targeting the exact RetroArch PID;
- NAudio 3.0.1 / .NET-based helper;
- 48 kHz stereo PCM16;
- normal source callbacks are approximately 10 ms / 480 frames;
- each callback is split into two 5 ms / 240-frame UDP packets;
- nonblocking UDP transport to port 48101.

Android receiver:

- 5 ms / 240-frame packet units;
- queue capacity: 8 packets / 40 ms;
- target queue: 3 packets / 15 ms;
- startup prefill timeout: 100 ms;
- low-latency AudioTrack target approximately 960 frames;
- bounded loss concealment, crossfade, and stale trimming.

This receiver is intentionally **not enlarged** to hide the current prototype's network-path pathology. See the UDP investigation.

Rejected production-audio experiments that should not be casually reintroduced:

- host v0.23 `SelectWrite` retry around nonblocking UDP: WouldBlock was not meaningfully recovered;
- Android v0.12.3 additional grace behavior;
- Android v0.12.4 AudioTrack-head top-up behavior;
- Android v0.12.5 / v0.12.5.1 periodic notification-clock/telemetry variants.

The stable process-audio sender lineage at this checkpoint is v0.22 and the stable Android production receiver lineage is v0.12.2.

### Input

Controller transport uses UDP port 48102 and is independent of the video/audio transports.

## Current decision: defer UDP infrastructure root cause

The first Windows/consumer-Wi-Fi prototype exhibits severe packet timing transformation and duplication outside application code in both directions. The investigation localized the problem to the physical/network-infrastructure path but did not identify a single responsible device or firmware layer.

Decision:

- preserve the current production video/audio/input baseline;
- preserve the transport diagnostic suite;
- do not spend further prototype time tuning the application around this specific environment;
- rerun the transport acceptance suite early in the dedicated Linux infrastructure phase;
- resume root-cause work only if representative Linux infrastructure reproduces the pathology.

Detailed evidence: `docs/investigations/2026-09-07-udp-transport.md`.

## Planned next infrastructure phase

The Linux phase should prioritize:

1. reproducible host setup on inexpensive Linux-capable hardware;
2. known and controllable network interfaces/drivers;
3. clean separation of persistent media/data from replaceable application/runtime components;
4. remote-access design that preserves the local-first security model;
5. immediate replay of the saved UDP acceptance suite before changing the audio design.

## Deferred cleanup

### Sunshine / Moonlight legacy

Sunshine/Moonlight were useful earlier scaffolding but native streaming has superseded them for the current experiment. Legacy scripts and `StreamManager` integration still exist in the pushed baseline. Remove them in a dedicated cleanup change so the cleanup does not get mixed with transport experiments.

### Repository portability

A pre-push audit found that required Python source under `companion/games/` was being hidden by an unanchored `games/` ignore rule. Python resolves the Games plugin imports from `companion/games/`, while repository-root `/games/` is the local ROM/content library.

This checkpoint corrects the ignore rule to `/games/`, preserving the content exclusion while allowing `companion/games/` source to be tracked. Include the companion game-package Python source in this checkpoint and verify that no repository-root game content is staged.

See `docs/REPOSITORY_AUDIT_2026-09-07.md`.
