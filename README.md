# PrivyHub

PrivyHub is an experimental local-first media, gaming, and smart-home platform
built around an isolated IoT network. The prototype is an onn Android TV client
and a **Linux companion host** (HP EliteDesk) wired directly into the network
boundary router. The Windows companion is a preserved reference implementation,
not the running server.

## Current development state

- Phase A — Games / emulator subsystem: **complete and checkpointed**
- Phase B — Diagnostics + clean native baseline: **complete and checkpointed**
- Phase D — Linux migration / native Linux baseline: **active**
- Phase C — Adaptive native streaming: **suspended** behind baseline stream
  health
- Current technical item: **`D-BASE` baseline stream health** —
  [`docs/memory/investigations/BASELINE_STREAM_HEALTH.md`](docs/memory/investigations/BASELINE_STREAM_HEALTH.md)

**C1 explicit stream profiles are done.** The reference parameters live in
`companion/native_stream_profiles.py` as `native_game_720p60_reference`, and
`native-stream-status` reports the profile in force plus any environment
override. What replaced C1 as the active item is measuring and fixing the
stream baseline, not adaptation: adaptation is not built on a baseline that is
not healthy.

## Current prototype

The project currently includes:

- local media/VOD serving;
- camera and browser/live sources;
- a mature TV/IPTV catalog and EPG stack with remaining Phase D UX work;
- NES, SNES, Genesis, and PlayStation emulation through a project-managed
  RetroArch runtime;
- validated 1P/2P/4P controller routing with A8 input profiles;
- PS1 Port-1-only manual Multitap On/Off with Crash Bash and CTR runtime
  validation;
- Save/Load, pause/resume, direct launch, metadata/art, cheats and mods;
- native low-latency game video, process audio, controller transport and
  teardown;
- Diagnostics / Self-Test, health/resource telemetry, support bundles and
  bounded diagnostic retention.

Current runtime coverage is strongest on PS1. SNES was runtime exercised. NES
and Genesis are configured/supported but had no local A9 fixtures, so they are
not claimed as runtime validated.

## Native game-streaming baseline

Validated path, Linux (the production one):

`x11grab of the managed RetroArch window -> H.264 VAAPI -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Windows Graphics Capture -> NVENC remains as a preserved reference path.

Reference profile behavior (`native_game_720p60_reference`):

- 1280x720;
- 60 fps;
- 7000 kbps target bitrate;
- GOP 15;
- no B-frames;
- **maximum frame size 90,000 bytes** (Linux `h264_vaapi` only);
- 8 data + 1 XOR FEC;
- RTP payload type 96;
- 1200-byte packet size.

Process-specific audio and the P1-P4 controller path (PHI1 -> uinput ->
RetroArch udev on Linux) are separate from the video transport.

**The frame cap is a transport parameter, not a quality knob.** The packet
loss on the wireless hop was traced to a per-frame micro-burst meeting the
access point's per-station queue — one frame in a hundred is 80-plus packets
emitted back to back. Capping the frame bounds the burst: it removed 100 % of
the >= 80-packet frames and 7-9x of the loss, with achieved bitrate, frame rate
and encoder CPU unchanged, and held over a three-hour soak. The encoder is
CBR, so it spends the same bits; the cap only changes when it may spend them.
`PRIVYHUB_ENC_MAX_FRAME_SIZE=0` reproduces the uncapped behavior for
comparison. Records:
[`D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md`](docs/memory/evidence/D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md),
[`D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`](docs/memory/evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md),
[`D_BASE_S3_CAP_SOAK_2026-09-22.md`](docs/memory/evidence/D_BASE_S3_CAP_SOAK_2026-09-22.md).

A separate and still **paused** issue is the synthetic UDP
burst/gap/duplication pathology seen without game load. It is not a
Windows-only artifact — it reproduced from a Linux sender too — but it has
never been replayed on the current topology, and it is not treated as a
product buffering requirement. See
[`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md).

## Documentation

Start with:

- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) — current validated state and
  active development position;
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — authoritative Linux-first roadmap v3;
- [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) — open/deferred issues and debt;
- [`docs/README.md`](docs/README.md) — documentation map;
- [`docs/memory/CURRENT.md`](docs/memory/CURRENT.md) — immediate development
  state and next step;
- [`docs/memory/MEMORY.md`](docs/memory/MEMORY.md) — curated durable project
  facts/rules;
- [`docs/memory/evidence/RUNTIME_VALIDATION.md`](docs/memory/evidence/RUNTIME_VALIDATION.md)
  — runtime-validation ledger.

## Network ports used by the current prototype

| Purpose | Port |
| --- | ---: |
| Companion control API | TCP 8765 |
| Media serving | TCP 8000 |
| Native game video | UDP 48100 |
| Native game audio | UDP 48101 |
| Native controller input | UDP 48102 |
| Local video FEC relay input | UDP 48110 on loopback only |
| Forward synthetic transport diagnostic | UDP 48120 |
| Android-local loopback diagnostic | UDP 48121 |

Diagnostic ports and implementation details may evolve; production code should
not depend on diagnostic-only paths.

## Project principles

- Local-first and privacy-oriented operation.
- IoT devices isolated behind a dedicated network boundary.
- Prefer modular, replaceable, hardware-agnostic components.
- Preserve validated subsystems while testing one layer at a time.
- Prefer current local source and fresh measured evidence over stale summaries.
- Do not broaden capture from the managed game window to the desktop as a
  fallback.
- Do not encode quirks of the current test environment into product architecture
  without representative evidence.
- Keep user ROM/ISO/BIOS/firmware/keys and private network-bearing data out of
  Git and shareable support bundles.
