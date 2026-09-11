# PrivyHub

PrivyHub is an experimental local-first media, gaming, and smart-home platform
built around an isolated IoT network. The current prototype uses an onn Android
TV device as the first client and a Windows companion host as the temporary
server/streaming platform. The roadmap moves the core server toward dedicated
Linux infrastructure after the current native-streaming architecture work.

## Current development state

- Phase A — Games / emulator subsystem: **complete and checkpointed**
- Phase B — Diagnostics + clean native baseline: **complete and checkpointed**
- Phase C — Adaptive native streaming: **active**
- Current technical item: **C1 explicit stream profiles**
- C1 inventory: **complete**
- Next technical classification: `C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`

The first C1 implementation is intentionally narrow: extract the validated
static native stream parameters into an explicit profile without changing
runtime behavior. A GUI selector, bitrate adaptation, adaptive FEC, or a broad
streaming-framework rewrite comes later.

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

Validated path:

`Windows Graphics Capture -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Reference profile behavior:

- 1280x720;
- 60 fps;
- 7000 kbps target bitrate;
- GOP 15;
- no B-frames;
- 8 data + 1 XOR FEC;
- RTP payload type 96;
- 1200-byte packet size.

Process-specific Windows audio and the PHI1/ViGEm P1-P4 controller path are
separate from the video transport and are preserved during C1.

The current Windows/network prototype has a deeply measured UDP burst/gap/
duplication pathology outside normal application pacing. It is **deferred**, not
treated as a product buffering requirement. Replay the saved acceptance suite on
representative Linux/network infrastructure after the Linux baseline exists.

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
