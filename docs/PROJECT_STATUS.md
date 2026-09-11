# Project status — 2026-09-11

## Goal

PrivyHub is an experiment in building a local-first smart-home/media environment
where inexpensive clients live on an isolated IoT network and trusted
host/server infrastructure provides local services.

The current prototype uses an onn Android TV device and a Windows companion host.
The roadmap moves core server responsibilities to dedicated Linux
infrastructure while preserving validated client/application behavior.

## Current development position

| Phase | Status |
| --- | --- |
| A — Games / emulator subsystem | COMPLETE / checkpointed |
| B — Diagnostics + clean native baseline | COMPLETE / checkpointed |
| C — Adaptive native streaming | ACTIVE |
| D — Media Library / VOD / Live TV UX | Planned after C |
| E — Linux Migration / Native Linux Baseline | Planned |
| F — Linux Core Resource Characterization & Optimization | Planned |
| G — Extended Emulation & User-Content Import | Planned |
| H — Home Infrastructure / Client / Plugin Expansion | Planned |
| I — Local Intelligence / Voice / Privacy-Aware AI | Planned |

Current technical item: **C1 explicit stream profiles**.

C1 inventory completed with:

`C1_INVENTORY_COMPLETE`

Next technical classification:

`C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`

The first implementation is a behavior-preserving static extraction, not an
adaptive-controller or generic-framework rewrite.

## Current topology

Conceptually:

```text
Internet
  |
trusted household network
  |
trusted host / future Linux server
  |
isolated IoT gateway
  |
onn Android TV client and future IoT devices
```

The consumer networking hardware used by the first prototype is test
infrastructure, not a permanent architectural dependency.

## Working application areas

### TV / IPTV

The existing TV stack is stable enough to preserve while streaming work
continues. It already includes catalog/state/provider/EPG functionality, search,
favorites, recents, hidden channels, ordering/grouping, backups, preview and
playback behavior.

It is not considered finished. Phase D owns the remaining product work:
stable channel identity/deduplication, favorites/search/pagination polish, EPG
matching/cache/timezone diagnostics, guide UX and robust unmatched-channel
handling. Playback must not depend on guide metadata success.

### Local sources and VOD

The companion supports local live/browser/camera sources and dynamically scanned
VOD media. Control and media planes remain separate. Recursive local-first
artwork/metadata work is scheduled for Phase D.

### Games / emulation

Managed cores:

- NES — FCEUmm;
- SNES — bsnes;
- Genesis — BlastEm;
- PlayStation — Beetle PSX HW.

Phase A is complete.

Validated behavior includes:

- PS1 1P/2P/4P controller routing;
- four physical Android controllers to four ViGEm/XInput slots;
- A8 P1-P4 input profiles/editor;
- Crash Bash and CTR manual Port-1-only Multitap On/Off;
- Save/Load with prior-save preservation;
- pause/resume/frozen preview;
- process-specific audio and host coexistence;
- direct launch/readiness/fail-closed behavior;
- metadata/art;
- isolated cheats and mods;
- normal End/teardown.

Coverage boundary:

- PS1 — extensive runtime coverage;
- SNES — runtime exercised;
- NES — supported/configured, but no local A9 fixture;
- Genesis — supported/configured, but no local A9 fixture.

NES and Genesis must not be promoted to runtime-validated status until
representative fixtures are actually exercised.

## Native game-streaming baseline

Validated path:

`Windows Graphics Capture -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Reference behavior:

- 1280x720 at 60 fps;
- H.264 NVENC;
- 7000 kbps target bitrate;
- P1 / ultra-low-latency backend policy;
- GOP 15;
- no B-frames;
- 1200-byte RTP packet sizing;
- 8 data + 1 XOR FEC;
- Windows Graphics Capture of the exact PrivyHub-managed game window;
- Android hardware AVC decode.

Process audio uses process-specific Windows loopback capture and a dedicated UDP
audio path. Controller transport uses PHI1 UDP plus persistent ViGEm VX360
devices.

C1 will make the portable stream parameters explicit while preserving this
runtime behavior.

## Phase B diagnostics / clean-native baseline

Phase B is complete and runtime/manual validated.

It delivered:

- unified health/resource model;
- `GET /diagnostics/health`;
- 2-second Android client feedback using the existing metrics cadence;
- corrected decoder/network classifier semantics;
- bounded event history;
- Diagnostics / Self-Test GUI;
- sanitized support-bundle collection;
- bounded/manual diagnostic retention;
- Sunshine/Moonlight production-edge and physical artifact removal;
- native-only regression after legacy removal;
- clean-native repository checkpoint.

Raw measured evidence outranks classifier output when they disagree.

## Deferred UDP infrastructure root cause

The Windows/current-network prototype exhibited severe packet timing
transformation and duplication outside normal application pacing in both
directions. The investigation localized the issue beyond normal application
send/receive pacing but did not identify one responsible device/firmware layer.

Decision:

- preserve the validated native video/audio/input baseline;
- preserve the transport diagnostics;
- do not tune product buffering around this specific environment;
- establish the representative Linux baseline first;
- replay the acceptance suite during Linux characterization;
- resume root-cause work earlier only if it becomes a real blocker.

Detailed evidence:
`investigations/2026-09-07-udp-transport.md`.

## Linux direction

Phase E moves core server responsibilities to the HP EliteDesk 805 G6 Linux
reference machine. That machine is a reference prototype, not the minimum target.

Phase F then performs representative resource/transport characterization and
optimization with PS1-and-below before cheaper Prototype 2 hardware is selected.

Future user-content import expects the user to supply ROM/ISO/BIOS/firmware/keys.
PrivyHub validates/hashes/copies content into the runtime layout while keeping it
out of Git and support bundles.

## Current constraints and debt

Open/deferred work that does not invalidate the current baseline includes:

- Windows-specific server/capture/audio implementation before Phase E;
- current-network UDP pathology pending representative Linux/network replay;
- Android cleartext/exported diagnostic surfaces and immature companion auth;
- minimal conventional CI;
- large orchestration files such as `MainActivity.kt`, `emulator_manager.py` and
  `plugins/games.py`;
- clean-machine/bootstrap representation that is less mature than the current
  working prototype;
- remaining Phase D media/EPG/guide UX work.

See `KNOWN_ISSUES.md` and `memory/repository/DEBT.md`.
