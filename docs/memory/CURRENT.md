---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: e65e8f89604ce325e6e3e0537d0287070b8996c5
---

# Current Development State

## Checkpoint

- Branch: `main`
- Current pushed checkpoint: `e65e8f89604ce325e6e3e0537d0287070b8996c5`
- Commit message: `Checkpoint: complete Phase A emulator subsystem`
- Working tree after checkpoint: clean
- Phase A: COMPLETE / pushed

## Current runtime coverage

Runtime validated:
- SNES normal Games path;
- extensive PS1 path;
- 1P/2P/4P controller routing;
- Crash Bash and CTR Port-1-only multitap;
- Save/Load;
- pause/resume/frozen preview;
- host coexistence/audio lifecycle;
- cheats/mods/input profiles;
- native streaming and teardown;
- persistent wireless-ADB recovery.

Declared no-fixture gaps:
- NES: zero local games at A9; supported/configured, not runtime validated.
- Genesis: zero local games at A9; supported/configured, not runtime validated.

## Active roadmap

`docs/ROADMAP.md` v2 is authoritative for post-Phase-A sequencing.

Next phase: **Phase B — Diagnostics & Clean Native Baseline**.

Immediate next work:
1. inventory existing production telemetry/probes;
2. define a unified diagnostic event/health schema;
3. add GUI Diagnostics / Self-Test / sanitized support bundle;
4. inventory and remove Sunshine/Moonlight legacy;
5. run focused native-only regression;
6. checkpoint the clean-native architecture.

Subsequent roadmap:
- Phase C: adaptive native streaming, explicit profiles, path telemetry,
  bitrate adaptation, 1080p60 and generalized sources;
- Phase D: VOD/media-library artwork and metadata UX;
- Phase E: resource benchmarking, inexpensive Linux tiers and capability scaling;
- Phase F: optional OpenBIOS/open-platform portability track;
- Phase G: broader smart-home, storage, remote-PC-game and handheld expansion.

## Preservation boundaries

Do not reopen or refactor validated Phase A paths without evidence:
- WGC native game capture;
- H.264 NVENC low-latency path;
- native process audio;
- UDP/FEC transport;
- Android hardware AVC decode;
- PHI1/ViGEm P1-P4 controller chain;
- Save/Load/Pause/End lifecycle;
- A8 profiles;
- PS1 Port-1-only multitap.

## Debugging rule

Use:
**one narrow hypothesis -> one targeted diagnostic/probe -> fresh evidence ->
inspect raw measurements -> one coherent patch**.

Never ask for or log network addresses.
