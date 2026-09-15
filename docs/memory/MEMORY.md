---
memory_schema: 1
as_of: 2026-09-15
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Curated Project Memory

<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15 -->

This file contains durable facts and rules, not chronological patch history.
Detailed history belongs in `memory/`, evidence in `evidence/`, and superseded
states in Git/history. Current local source and fresh runtime evidence always
outrank this summary.

## Mission and trust model

PrivyHub is a local-first, privacy-preserving, modular smart-home/media system.
The home Opal is the PrivyHub network/trust domain; the ordinary household
network is upstream connectivity, not the trusted device domain. The architecture
moves from the current inexpensive onn Android TV client and prototype host
toward inexpensive Linux-capable server hardware and additional trusted clients
without mandatory cloud, subscriptions, or proprietary infrastructure.

Local deterministic control is the baseline. Optional external AI providers are
future explicit integrations only, with data minimization and no silent fallback.

## Development position

- Phase A Games/emulation: **COMPLETE / PUSHED**.
- Phase B diagnostics/clean-native baseline: **COMPLETE / PUSHED**.
- Phase C adaptive streaming: **PAUSED AT WINDOWS PORTABILITY BOUNDARY**.
- Phase D Linux migration/native Linux baseline: **ACTIVE**.
- After D: resume unfinished C on Linux, then Phase E Linux
  characterization/optimization, Phase F media/VOD/Live TV, Phase G remote.

Windows Phase-C evidence remains useful input but is not a Linux product
constant. Automatic bitrate adaptation is not implemented.

## Games and emulator baseline

RetroArch is the managed frontend. Supported/configured families are NES,
SNES, Genesis, and PS1. PS1 has the strongest runtime coverage; SNES has runtime
coverage; NES and Genesis support/configuration must not be called runtime
validated without a representative local fixture.

Stable user-facing behaviors include:

- Save/Load and protected normal save/state namespaces;
- Pause/Resume/End lifecycle;
- isolated cheats/mod profiles;
- A8 controller profiles;
- four-player controller routing;
- PS1 manual Port-1-only Multitap On/Off;
- local metadata/art and direct game launch.

PrivyHub's PS1 local-player ceiling is four. Do not auto-enable multitap from
metadata.

User ROM/ISO/BIOS/firmware/keys remain outside Git and support bundles.

## Native stream contracts

The client-facing native stream remains H.264 over RTP-sized UDP with the
existing XOR FEC framing and Android hardware AVC decoding. The reference
profile is `native_game_720p60_reference`:

- 1280x720;
- 60 fps;
- 7000 kbps reference/max;
- GOP 15;
- B-frames 0;
- FEC group size 8.

Portable profile semantics are separate from backend-specific capture/encoder
policy, RTP payload type, packet size, ports, audio, controller protocol, and
telemetry cadence.

C2 `privyhub_stream_telemetry_v1` reuses the existing 2-second client-health path
and adds measurement-only receiver jitter, control-path RTT, signed decoder
queue-depth change, and sender/FEC pressure timing. Do not add a second hot-loop
sampler when existing instrumentation can answer the question.

## Windows Phase-C evidence

The Windows native path is:

`WGC -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`.

Validated fixed bitrate levels were 7000, 6000, and 5500 kbps; 5000 kbps was
runtime tested and rejected because focused play showed more steady-state visual
stutter. These values are Windows/test-environment evidence only.

The backend-neutral `video_only_restart` actuator is bidirectionally functional
but not acceptable for seamless automatic gameplay adaptation: the measured
restart interruption is roughly one second. Preserve it for diagnostics,
startup/manual recovery, fallback, or backends without a better mechanism.

Startup stabilization is runtime validated. Gameplay remains paused until fresh
receiver/decoder readiness evidence passes. Automatic adaptation freezes while
stabilizing or paused.

Unfinished Phase C must resume on Linux: low-interruption bitrate actuation and
automatic controller, adaptive FEC or explicit deferral, 1080p60
characterization, generalized source abstraction, and final Phase-C checkpoint.

## Linux host architecture — D073 through D078

The Linux reference prototype uses Debian 13 on Renoir `amdgpu`.

Durable Linux facts:

- VAAPI H.264 encoding works on the Renoir render node with stock Debian FFmpeg.
- Exact X11 window capture using `x11grab -window_id` works for real RetroArch
  gameplay. The target must remain mapped; minimizing/unmapping kills exact-window
  capture, while ordinary occlusion does not.
- The project-owned RetroArch 1.22.2 Linux AppImage and required FCEUmm, bsnes,
  BlastEm, and Beetle/Mednafen PSX HW Linux cores load successfully.
- Existing `EmulatorManager` readiness, launch, loopback control, save flush, and
  graceful shutdown work on Linux. Preserve that lifecycle/control surface.
- Linux native video is intentionally single-process:
  `owned X11 window -> FFmpeg x11grab -> VAAPI H.264 -> loopback RTP -> existing FEC relay`.
  Do not create a Linux WGC-equivalent raw-frame bridge.
- Linux process audio uses the EmulatorManager-owned RetroArch PID to identify
  one PulseAudio sink-input, move it to a dedicated temporary PrivyHub sink, and
  capture the monitor at 48 kHz stereo.
- PHA1 remains PCM S16LE stereo, 48 kHz, 240 frames/5 ms, with the existing
  16-byte v1 header.
- Under active RetroArch, the Linux PHA1 sender thread must obtain `SCHED_RR`
  priority 1 before emission. If that policy cannot be acquired, fail the Linux
  audio subpath rather than silently use the known-jittery fallback.
- Canonical PHI1/XUSB state remains host-independent. Linux converts it to four
  `evdev.UInput` gamepads; Windows retains ViGEm VX360.
- Linux uinput mapping and four project-owned RetroArch udev autoconfig profiles
  are validated. The generated Linux session config rewrites the portable
  project-relative autoconfig directory to its absolute project-owned path.
- D-077 adds trusted platform-aware runtime/core selection while preserving the
  Windows descriptor as the base mapping.
- D-078 makes companion media-server startup platform-aware: Windows keeps the
  PowerShell wrapper; Linux launches `companion/range_server.py` directly.

Temporary development ACL/RT-priority setup is not the production permission
model. Persistent service-scoped `/dev/uinput` access and `LimitRTPRIO=1` (or
equivalent) remain required. Never grant broad `CAP_SYS_NICE` to the general
Python interpreter.

## Integrated Linux/onn boundary

The first integrated Linux/onn PS1 run proved that the normal product path can:

- select the Linux runtime;
- launch managed RetroArch;
- load an existing save;
- create Linux virtual controllers;
- discover the exact managed X11 window;
- encode the intended native stream near 60 fps with VAAPI.

Therefore the current integrated failure is not evidence that RetroArch,
exact-window capture, or VAAPI encode is broken.

A separate Android compatibility bug prevents automatic stream entry on Linux:
`MainActivity` still requires the Windows-only
`host_window_policy.window_found`. Manual entry proves the Linux backend can
subsequently find the window. Treat this as a confirmed handoff bug ready for a
narrow fix.

The integrated PS1 run also reported missing `scph5501.bin`. Restore
user-provided BIOS content before final PS1 acceptance; it was not the transport
failure cause.

## Representative transport evidence

The old Prototype-1 UDP pathology has now been reproduced on the representative
Linux + home Opal + onn path while idle and in both directions.

Linux -> onn idle Test A:

- 3993 successful unique sends;
- zero unique loss;
- 2626 same-stamp duplicate Android arrivals;
- Android kernel arrival timing strongly bursty/gapped;
- only 7 Linux `SndbufErrors` and zero `RcvbufErrors`.

onn -> Linux idle Test B:

- 4000/4000 Android sends successful;
- 3894 unique Linux arrivals;
- 106 unique losses;
- 476 same-stamp duplicates;
- strong receive burst/gap transformation;
- Linux sender-buffer errors are not involved in this direction.

Durable conclusions:

- game/native-stream load is not required for the base pathology;
- a Linux-only sender implementation cannot explain the bidirectional result;
- production `SndbufErrors`/`RcvbufErrors` under game load amplify an already
  abnormal path but are not required for it;
- do not normalize large same-stamp duplicate delivery as ordinary Wi-Fi
  behavior;
- the unresolved region is shared network/radio/driver infrastructure until a
  lower-boundary measurement proves otherwise.

## Opal/router diagnostic disposition

Router-localization work established useful bounds but did not identify the
root duplicating component.

Validated evidence:

- Linux and onn are bridged through the home Opal wireless path.
- Ordinary `tcpdump`/AF_PACKET observations on both radio interfaces and on
  `br-lan` were completely blind during confirmed synthetic endpoint traffic.
- Disabling exposed OpenWrt software and hardware flow-offload flags did not fix
  transport and did not restore capture visibility; do not productize
  acceleration-off as a workaround.
- Proprietary Siflower FMAC/switch/HNAT components are present.

D083 and D083R1 are **invalid as networking evidence**. The first collected too
few counter samples and masked analyzer failure; the revision depended on
`nohup`, which the router does not provide. A smoke classifier also contradicted
raw `/proc/mounts`; raw evidence wins.

D082 is the last valid router-boundary result. The Opal/Siflower reverse-
engineering branch is paused. Do not continue by default. Re-enter only for a
bounded product-level measurement that can change a decision, or move the
transport discriminator to a different representative network/router.

## Diagnostics and evidence rules

Phase B diagnostics are stable and include health/resource status, Android
client feedback, corrected decoder/network classifier semantics, bounded event
history, Diagnostics/Self-Test UI, sanitized support bundles, and bounded manual
retention.

Rules:

- raw measurements outrank classifiers;
- stale-output shedding alone is informational unless decoder-local failure is
  present;
- do not infer success from `git status` when a dedicated receipt/probe exists;
- do not suppress startup stderr when process startup is the hypothesis;
- diagnostic runners fail closed on missing/insufficient evidence;
- do not turn an unproven diagnostic hypothesis into architecture.

## Repository and patch discipline

Commit source/configuration, durable engineering memory, reusable diagnostics,
and curated/sanitized evidence. Keep ROMs/ISOs, saves/states, emulator runtimes,
ordinary logs, patch backups, APK/build output, private ADB target cache, media
libraries, and raw network-bearing evidence out of Git.

Meaningful patches must verify predecessor state, reject wrong state before
modification, back up changed files, validate installed output, run applicable
compile/build checks plus `git diff --check`, and restore exact predecessor bytes
on post-write failure. Exit code is the authoritative command success signal;
warning text alone is not failure.

Every meaningful patch updates the affected durable-memory files and declares
`durable_memory_updated: true`.

## Privacy and network handling

Never ask the user to provide or paste IP addresses. Diagnostics may discover
addresses locally when required, but must not print or persist them in
shareable evidence. Overlay transport and future PrivyHub application
authorization are separate; source/request IP is not durable client identity.

## Deferred product work

- Linux/Opal transport root cause: paused after D083 closeout; re-entry condition
  is bounded product value or a different representative network path.
- Automatic C3 bitrate adaptation and C4 adaptive FEC: resume on Linux only.
- 1080p60 and generalized source abstraction: remaining Phase C on Linux.
- Media/VOD/Live TV polish: Phase F.
- Secure remote/portable-client foundation: Phase G; Tailscale is a first
  candidate, not a permanent dependency.
- Extended emulation/user-content import: Phase H.
- Broader home infrastructure: Phase I.
- Local intelligence/voice/privacy-aware AI: Phase J.

Maintainability debt remains in large files such as `MainActivity.kt`,
`emulator_manager.py`, and `games.py`. Avoid broad refactors while behavior is
stable.
