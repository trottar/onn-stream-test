# Project status — 2026-09-14

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:PROJECT_STATUS:BEGIN -->
## 2026-09-16 Linux controller checkpoint update

This section supersedes older status language below where it conflicts.

- Phase D is **ACTIVE**, not "NEXT".
- The normal Linux Games path now launches and streams successfully on the HP
  EliteDesk Linux server.
- Linux gameplay input is runtime validated across three games and three input
  profiles after D-084/D-085.
- The current Games controller backend is native Linux
  `PHI1 -> uinput -> RetroArch udev`; Windows/ViGEm remains a preserved reference
  backend, not the active Linux implementation.
- The next D4 issue is PS1 multiplayer/multitap parity. The feature was
  previously runtime validated on Windows but currently does not work on Linux.
- Remaining Phase C work stays paused until the Phase-D Linux baseline is
  sufficiently complete.

The next diagnostic should classify multitap override/core-option/frontend/game
topology before any multiplayer production change.
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:PROJECT_STATUS:END -->

## Goal

PrivyHub is an experiment in building a local-first smart-home/media environment
inside a dedicated PrivyHub network/trust domain.

The home Opal is that domain boundary. The ordinary household router/Wi-Fi is
upstream connectivity only. Trusted server/client/device infrastructure belongs
behind the Opal.

The current implementation uses an onn Android TV client and Windows companion.
The roadmap moves core server responsibilities to dedicated Linux
infrastructure while preserving validated client/application behavior and later
adds an optional secure remote/portable-client foundation.

## Current development position

| Phase | Status |
| --- | --- |
| A — Games / emulator subsystem | COMPLETE / checkpointed |
| B — Diagnostics + clean native baseline | COMPLETE / checkpointed |
| C — Adaptive native streaming | Windows portable boundary reached; adaptation continues on Linux |
| D — Linux Migration / Native Linux Baseline | NEXT |
| E — Linux Core Resource Characterization & Optimization | Planned after D |
| F — Media Library / VOD / Live TV UX | Planned after E |
| G — Secure Remote Access / Portable Client Foundation | Future after F |
| H — Extended Emulation & User-Content Import | Future after G |
| I — Home Infrastructure / Broader Plugin Expansion | Future |
| J — Local Intelligence / Voice / Privacy-Aware AI | Future |

Predecessor synchronized checkpoint for this documentation promotion:

`0c31c100ec721d687aff6aedbd79bc0cf9343810`

C1.1 static reference profile extraction and the native-stream public-status
privacy hotfix are runtime validated, checkpointed and pushed.

The active technical phase remains **Phase C adaptive native streaming**. Phase C
must now be developed with explicit future-remote reuse in mind, but it does not
implement WAN overlay/auth/travel-router behavior.

## Current topology

```text
Internet / ordinary household upstream
              |
          home Opal
   PrivyHub trust/network domain
      |                   |
companion / Linux hub    onn / PrivyHub devices
```

Older Prototype-1 split-network evidence is historical test topology, not the
current product trust model.

Future remote clients use a travel-router trusted LAN plus a secure overlay back
to the Linux hub. Overlay transport remains separate from PrivyHub application
authentication/authorization.

## Working application areas

### TV / IPTV

The existing TV stack is stable enough to preserve while streaming work
continues. Phase F owns the remaining channel normalization, EPG matching/cache,
guide diagnostics and UX work. Basic playback must not depend on guide success.

### Local sources and VOD

The companion supports local live/browser/camera sources and dynamically scanned
VOD media. Control and media planes remain separate. Recursive local-first
artwork/metadata work is scheduled for Phase F.

### Games / emulation

Managed cores:

- NES — FCEUmm;
- SNES — bsnes;
- Genesis — BlastEm;
- PlayStation — Beetle PSX HW.

Phase A is complete.

Runtime coverage:

- PS1 — extensive;
- SNES — runtime exercised;
- NES — supported/configured, no local A9 fixture;
- Genesis — supported/configured, no local A9 fixture.

NES and Genesis are not runtime validated merely because configuration exists.

## Native game-streaming baseline

Validated path:

`Windows Graphics Capture -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Reference behavior:

- 1280x720 at 60 fps;
- 7000 kbps target/max;
- GOP 15;
- no B-frames;
- FEC group size 8;
- process-specific PCM audio;
- PHI1/ViGEm controller path.

Reference profile:

`native_game_720p60_reference`

C1.1 made the reference stream parameters explicit without changing validated
behavior.

Phase C continues with telemetry/adaptation/generalization. Its contracts must
remain reusable by future Phase G WAN operation.

## Phase C remote-readiness rule

Future Phase G depends on Phase C producing reusable:

- named profiles and capability gates;
- goodput/loss/FEC/jitter/RTT/pacing/queue telemetry;
- explainable adaptation decisions;
- source/capture -> profile/encoder -> transport/FEC -> decoder boundaries.

Do not implement remote overlay/auth/travel-router routing in Phase C.

For future WAN adaptation, degrade quality before allowing queue/buffer growth
to create runaway latency.

The current reference session is roughly 10-11 Mbps outbound as a planning
estimate once video, 8+1 parity, PCM16 stereo audio and packet/tunnel overhead
are considered. This does not change the stable audio path.

## Deferred UDP infrastructure root cause

The older Windows/current-network prototype exhibited severe packet timing
transformation and duplication in both directions.

Preserve the validated native path and diagnostics. Do not tune product
buffering around that environment.

Replay the saved acceptance suite on the representative:

`Linux + home Opal + onn`

path after Linux migration and before WAN characterization.

If the representative path is clean, treat the older anomaly as environment
specific unless new evidence contradicts that. If it reproduces, investigate
the representative local path before layering WAN jitter/loss on top.

## Linux and remote direction

Phase D establishes Linux-native functional parity on the HP EliteDesk 805 G6
reference machine.

Phase E optimizes and characterizes PS1-and-below, then selects cheaper
Prototype 2 hardware from evidence.

Phase F resumes Media Library / VOD / Live TV UX work on the representative
Linux foundation.

Phase G establishes secure optional remote access and portable clients on that
mature Linux/Core baseline before heavier emulator families are introduced.

Tailscale is the preferred first overlay candidate, not the permanent contract.
No permanent travel-router model is selected yet.

Phase H then adds user-content import and N64/GameCube/PS2 characterization.
Users supply ROM/ISO/BIOS/firmware/keys; PrivyHub keeps that content outside Git
and support bundles.

## Security boundary

Future remote operation separates:

- secure network transport/overlay;
- PrivyHub client/session identity;
- application authentication/authorization;
- reachable media/audio/controller endpoints;
- overlay/path state.

Source/request IP is not durable client identity.

Remote access must not flatten or expose the ordinary household LAN.

## Current constraints and debt

Open/deferred work that does not invalidate the current baseline includes:

- Windows-specific server/capture/audio implementation before Phase D;
- older-network UDP pathology pending representative Linux + home Opal + onn
  replay;
- Android cleartext/exported diagnostic surfaces and immature companion auth;
- minimal conventional CI;
- large orchestration files;
- remaining Phase F media/EPG/guide UX work;
- all Phase G remote functionality, which is planned only.

See `KNOWN_ISSUES.md` and durable memory for detailed evidence/state.

## Architecture checkpoint state

The remote-foundation topology/roadmap promotion is **CHECKPOINTED / PUSHED**.

Git HEAD is the authoritative synchronized checkpoint.

Next technical work returns to Phase C under D-059.

## Linux-first sequencing clarification

Phase C is not complete. The Windows implementation reached a portability
boundary and deliberately stopped before the remaining adaptive-streaming work.

Next execution sequence:

`Phase D Linux baseline -> remaining Phase C on Linux -> Phase E -> Phase F`

The remaining Phase C items are automatic bitrate control, adaptive FEC
disposition, 1080p60 characterization, generalized source abstraction and the
final Phase C checkpoint.
