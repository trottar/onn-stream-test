---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 65d02012409440d5559c14beb2b28268b0b225bc
---

# Repository Code Map

## Root

- `PrivyHub/` — Android TV application.
- `companion/` — companion control/media/Games/native-stream implementation.
- `scripts/` — setup/start and supporting development helpers.
- `tools/` — build/install helpers, diagnostics, audits and targeted probes.
- `docs/` — feature documentation, roadmap, investigations and durable memory.
- `media/`, root game-content/runtime data, logs, archives and generated build
  output — operational/user data; intentionally outside normal source tracking.

Sunshine/Moonlight production integration and physical project artifacts were
removed in Phase B. Do not treat legacy streaming as a current architecture
path.

## Android

Primary application orchestration remains concentrated in `MainActivity.kt`.

Native stream components live under the Android streaming package and include:

- `NativeStreamActivity.kt` — native stream Activity/session-side constants;
- `RtpH264Receiver.kt` — RTP/H.264 receive and FEC buffering;
- native audio receive;
- controller sender;
- decoder/session telemetry.

Diagnostics include the standalone Diagnostics / Self-Test surface and bounded
health/event presentation.

## Companion

Important current paths include:

- `companion/privyhub_service.py` — HTTP service entry point and plugin lifecycle;
- `companion/plugins/games.py` — Games API/orchestration and launch preflight;
- `companion/games/emulator_manager.py` — RetroArch/game/profile/save/mod/cheat
  lifecycle;
- `companion/games/native/native_stream.py` — WGC/native stream session,
  reference quality constants, encoder/backend policy and transport/session
  setup;
- `companion/games/native/native_fec_relay.py` — video relay/FEC behavior;
- `companion/games/native/native_session_io.py` — process audio/controller
  session I/O;
- native WGC/process-audio helpers;
- diagnostics/health/resource/support-bundle/retention modules.

C1 inventory found that portable stream parameters are currently split between
the Windows native stream path and Android native stream Activity/receiver. The
first C1 change should extract a minimal explicit profile without redesigning
capture, audio, controller or lifecycle ownership.

## Durable memory

`docs/memory/` is the persistent development bridge:

- `CURRENT.md` / `CURRENT_HANDOFF.md` — immediate state;
- `MEMORY.md` — curated current durable facts;
- `architecture/`, `decisions/`, `evidence/`, `investigations/`, `patches/`,
  `repository/`, `roadmap/` — specific durable records;
- `history/` — superseded reference snapshots.

## Maintainability note

Several central files remain large, especially `MainActivity.kt`,
`emulator_manager.py` and `plugins/games.py`.

That is real modularization debt, but broad refactoring is not part of C1.
Preserve validated behavior and split modules only with a dedicated objective and
regression contract.
