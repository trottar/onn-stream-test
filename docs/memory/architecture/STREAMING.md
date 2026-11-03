---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 45ef51f9e583b459752dd5ea83163f54171e68c7
---

# Native Streaming Architecture

> **Status (2026-11-03):** "The Linux pipeline as built" below is current, read from `companion/` and the adoption
> records. The 2026-09-14 text after it (Windows capture / NVENC / PCM, Phase C direction) is kept as the
> "Windows-era design (superseded)" history; the C1 profile and the readiness gate in it still hold. Current state:
> `docs/memory/CURRENT.md`, `docs/REMOTE_TRUST.md` §9-§15.

## The Linux pipeline as built (2026-11-03)

```text
RetroArch window (headless X display) -> x11grab -> h264_vaapi (one ffmpeg) -> RTP to loopback
  -> FEC relay (8+1 XOR) -> UDP video -> onn hardware AVC decoder
game audio (dedicated PulseAudio sink) -> PCM s16le 48 kHz -> Opus -> UDP audio (duplicated) -> onn
onn controllers -> PHI1 UDP -> uinput gamepads (four) -> RetroArch
```

- **Capture** (`companion/native_stream.py`): ffmpeg `-f x11grab -window_id <the managed RetroArch window>` at the
  profile's 60 fps, on the headless display (H2). The window is found with `xdotool`; capture is fail-closed (no
  whole-desktop fallback). On Linux the capture is an input of the encoder process, so a restart replaces both.
- **Encoder:** `h264_vaapi`, profile high, from `native_game_720p60_reference` (`companion/native_stream_profiles.py`):
  1280x720, 60 fps, 7000 kbit/s target and max, GOP 15, no B-frames, `-max_frame_size` 90,000 bytes (D-BASE-P6a).
  Adopted line 5 (`PRIVYHUB_SNES_CAPTURE_FIX=output_rate`, E4-S5D) adds an output `-r 60`. `h264_vaapi` takes its
  rate control at init only, so a bitrate step needs a new encoder process.
- **RTP relay and FEC** (`companion/native_fec_relay.py`): ffmpeg sends RTP only to loopback; the relay is the sole
  sender to the onn (video UDP 48100) and adds one XOR parity datagram (`PHF1` v1) per 8 data packets (`xor8_1`,
  the default; C4 kept 8+1). The `xor8_2` Reed-Solomon arm (`PRIVYHUB_FEC_SCHEME`) is a default-off comparison.
- **Audio** (`companion/native_session_io.py`, `companion/audio_codec.py`): a per-game PulseAudio null sink, read
  by ffmpeg `-f pulse` as s16le 48 kHz stereo; with adopted line 8 (G-A2) it is encoded with libopus (128 kbit/s,
  10-ms frames, `PHA1` version 2) and sent on UDP 48101. Each datagram is sent twice, the copy ~20 ms later
  (D-BASE-P10); the audio cushion is 12 / 17 packets (queue target / capacity, D-BASE-P9). A client that did not declare
  Opus is refused at stream start.
- **Controllers:** PHI1 full-state packets on UDP 48102 into four Linux `uinput` gamepads (`CONTROLLERS.md`).
- **The live ladder** (adopted line 1, C3-L4, `ADAPTIVE_BITRATE.md`): one transition per event over
  5000 / 5500 / 6000 / 7000 kbit/s at 720p60 on the LAN. On a remote-class session line 13 (G-A9) gives the remote
  ladder 4000 / 5000 / 5500 / 6000 / 7000 (`companion/remote_ladder.py`), the 4000 floor start, the 7000 cap and
  the WAN telemetry; the LAN starts at 7000.
- **The step in place** (adopted line 14, G-A10, `companion/step_in_place.py`): the new encoder starts beside the
  old one and, from its first IDR, the relay rewrites its packets onto the old stream (same SSRC, next sequence
  number), so the onn sees one IDR and no resync; with no splice within 2 s the old restart runs.
- **Recovery and restarts:** recovery trigger v2 (line 4, E3-A3B), the link-recovery stack (line 10, G-A4), the fast
  restart and its unlock (lines 11-12, G-A5 / G-A7) — `docs/REMOTE_TRUST.md` §11-§13.
- **Readiness:** `native-stream-start` pauses the game; `native-stream-ready` resumes it after the client's
  readiness (`GAMES.md`).

## Windows-era design (superseded)

Kept as written on 2026-09-14 (headings demoted one level on 2026-11-03, text unchanged). The Windows capture, NVENC
and process-loopback PCM audio paths no longer run on the Linux hub.

### Current Games baseline

Video path:

`managed RetroArch window -> Windows Graphics Capture -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC decoder`.

Stable reference profile is 1280x720 at 60 fps, approximately 7 Mbps, low-latency P1 encoder behavior, GOP 15, no B-frames, and roughly 1200-byte RTP payload sizing.

Capture is fail-closed: failure to identify the managed game window must not silently broaden capture to the desktop.

### Audio

The host captures the exact managed RetroArch process through process-specific Windows loopback. Android uses a deliberately small low-latency PCM queue. A4 lifecycle recovery is runtime validated; do not reopen without regression evidence.

### C1 explicit-profile design

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

### Current Phase C direction

C1/C1.1 are complete.

C2 is active.

C2.1 inventory is complete and C2.2 minimal telemetry design is recorded in:

`docs/memory/architecture/STREAM_TELEMETRY.md`

Next production step:

`C2_IMPLEMENT_STREAM_TELEMETRY_V1`

Do not add adaptive bitrate until the measurement contract is implemented and
runtime validated.

### C1.1 static reference profile extraction — development state

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

### Native-stream status privacy hotfix — 2026-09-14

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

### Phase C future-remote readiness

Phase C remains a local streaming implementation phase, but its artifacts are
direct prerequisites for Phase G.

Preserve reusable contracts for:

- named profiles/capability gates;
- goodput/loss/FEC/jitter/RTT/pacing/queue telemetry;
- explainable adaptation reason codes;
- source/capture -> profile/encoder -> transport/FEC -> decoder boundaries.

Do not add overlay providers, travel-router handling or remote authentication in
Phase C.

Do not make new Phase C contracts depend on source/request address as durable
client identity.

Future WAN adaptation principle: degrade quality before queue/buffer growth is
allowed to create runaway latency.

Reference WAN planning estimate for the current 720p60 + PCM16 + 8+1 stream is
roughly 10-11 Mbps outbound per session. This is a planning estimate, not a
reason to alter the stable PCM audio path.

### C2 telemetry architecture

The adaptation-facing contract is `privyhub_stream_telemetry_v1`.

Reuse the existing Phase-B client-health report as the receiver source and
combine it companion-side with native-stream/FEC-relay sender status.

Missing measurements are limited to:
- receiver inter-arrival jitter;
- control-path round trip;
- signed decoder queue-depth change;
- sender `sendto()` pressure/timing.

The relay has no pacing deadline, so do not invent probe-style pacing lateness.
Measure real send pressure without changing transport scheduling.

See `architecture/STREAM_TELEMETRY.md` for exact semantics.

### User-facing stream readiness/status surface

Native startup has a full-screen readiness overlay separate from hidden
engineering telemetry. It shows only basic non-sensitive metadata: title,
resolution/FPS, bitrate, FEC, video state, audio state and controller state.

A pure Kotlin in-process `GameStreamStatusUi` snapshot/formatter is shared with
MainActivity's paused Game Session banner. Metadata is not persisted to disk.

No IPs/endpoints/ports/SSRC/sequence values are shown.

### Startup stabilization runtime result

The metadata-rich startup stabilization overlay and readiness release boundary
are accepted for the current Windows + onn path. The user reported successful
release and no initial gameplay lag after the companion process was restarted.

This remains a readiness gate, not a playback buffer; no intentional
steady-state latency is added.
