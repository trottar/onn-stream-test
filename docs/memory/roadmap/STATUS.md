---
memory_schema: 1
as_of: 2026-09-15
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Roadmap Status

<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:ROADMAP:BEGIN -->
## 2026-09-16 D4 multiplayer checkpoint

**Phase D remains ACTIVE.**

Runtime validated inside D4:
- integrated Linux gameplay controller parity across three games / three input
  profiles;
- PS1 Port-1 multitap/four-player parity in Crash Bash with four independent
  remotes/controllers.

Remaining D4 scope before normal-use Games parity is complete:
- representative final Games regression/acceptance across required lifecycle and
  feature paths.

After D4 acceptance, proceed to D5 media/server restoration.
<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:ROADMAP:END -->

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:ROADMAP:BEGIN -->
## 2026-09-16 D4 controller checkpoint

**Phase D remains ACTIVE.**

Newly runtime validated:
- Linux integrated game launch/stream path;
- Linux gameplay controller path across three games / three input profiles;
- default and named input-profile behavior after D-084/D-085;
- persistent uinput prerequisite and RT-priority prerequisite remain closed.

Immediate D4 blocker before broader regression:
- **PS1 multiplayer / multitap parity on Linux**.

Historical Windows Phase-A multitap acceptance is the behavioral reference.
Linux debugging must first classify stored override -> generated Beetle `.opt`
-> P1-P4 frontend configuration -> in-game Players 3/4 availability.

Execution order remains:

`finish D4 multiplayer/normal-use parity -> finish remaining Phase D -> resume remaining C on Linux -> E -> F -> G`
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:ROADMAP:END -->

<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15 -->

`docs/ROADMAP.md` defines phase scope. This file records the current execution
position and overrides older embedded "next" statements in historical notes.

## Current position

| Phase | Status | Current meaning |
| --- | --- | --- |
| A — Games / Emulator Subsystem | **COMPLETE / PUSHED** | Stable emulator/game baseline. |
| B — Diagnostics & Clean Native Baseline | **COMPLETE / PUSHED** | Diagnostics and native-only cleanup complete. |
| C — Adaptive Native Streaming | **PAUSED AT WINDOWS PORTABILITY BOUNDARY** | C1/C2/startup stabilization and Windows fixed-ladder/actuator evidence retained; automatic adaptation unfinished. |
| D — Linux Migration / Native Linux Baseline | **ACTIVE** | Core Linux host seams validated; integrated stream reaches representative transport blocker. |
| E — Linux Core Characterization / Optimization | **PLANNED AFTER D + REMAINING C** | Size/optimize PS1-and-below on Linux. |
| F — Media Library / VOD / Live TV UX | **PLANNED** | Resume media/guide polish on Linux. |
| G — Secure Remote / Portable Client Foundation | **FUTURE** | Overlay/provider abstraction, WAN identity/auth, off-site validation. |
| H — Extended Emulation / User Content Import | **FUTURE** | Safe import then later-console characterization. |
| I — Home Infrastructure / Broader Plugins | **FUTURE** | Devices, cameras, storage, broader clients. |
| J — Local Intelligence / Voice / Privacy-Aware AI | **FUTURE** | Local-first intelligence; optional explicit external providers. |

Execution order:

`D Linux baseline -> remaining C on Linux -> E -> F -> G -> H -> I -> J`

## Phase C carry-forward

Complete/retained:

- explicit `native_game_720p60_reference` profile;
- C2 `privyhub_stream_telemetry_v1` measurement contract;
- startup stabilization/readiness gate;
- Windows fixed bitrate evidence: 5500/6000/7000 validated, 5000 rejected;
- bidirectional restart actuator capability, with ~1 s interruption proving it
  unsuitable for seamless automatic play.

Still required on Linux before Phase E:

- acceptable low-interruption bitrate actuation and automatic controller;
- adaptive FEC or explicit deferral;
- 1080p60 characterization;
- generalized native source abstraction;
- Phase-C final checkpoint.

## Phase D progress

Validated:

- Linux host/emulator baseline;
- project-owned Linux RetroArch runtime and cores;
- exact-window X11/VAAPI native video;
- PulseAudio process isolation and RT sender requirement;
- PHI1/uinput P1-P4 controller path and managed autoconfig;
- normal product platform runtime selection;
- normal Linux companion media-server startup;
- integrated PS1 launch/save-load/window-discovery/VAAPI encode.

Pending:

- Android Linux-neutral automatic stream handoff;
- persistent production permissions for uinput and RT priority;
- user-provided PS1 BIOS restoration;
- representative integrated stream acceptance.

## Transport disposition

The deferred UDP problem was replayed on Linux + home Opal + onn and reproduced
bidirectionally while idle. Standard router AF_PACKET capture points are blind
to the confirmed WLAN-to-WLAN traffic. Exposed OpenWrt flow-offload flags are
not the fix. D083/D083R1 are invalid measurements; D082 is the last valid router
result.

The Opal/Siflower root-cause branch is **PAUSED**, not the default next task.
Re-enter only for a bounded product-level discriminator or on a different
representative network/router path.

## Immediate development step

After this memory normalization, implement the narrow Android/Linux auto-open
compatibility fix. Do not use that patch to alter transport, bitrate/FEC,
decoder policy, or the validated Linux capture/audio/controller backends.
