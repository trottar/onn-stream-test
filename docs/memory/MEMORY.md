---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Curated Project Memory

<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:MEMORY:BEGIN -->
## Linux PS1 multitap parity is runtime validated

On 2026-09-16 the user confirmed Crash Bash with Multitap On launches correctly,
Players 3/4 are available, and all four remotes independently control the four
players.

Durable interpretation:
- Linux reproduces the previously validated Windows Port-1 multitap behavior;
- D-087's XDG/user RetroArch Config-root adapter is correct;
- D-087R1's external-path metadata fix is correct;
- PS1 multitap is no longer an active Linux regression;
- lower PHI1/uinput/udev/A8 controller paths remain preserved and accepted.

Next Games work is broad normal-use D4 regression/acceptance, not another
multitap-specific patch.
<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:MEMORY:END -->

<!-- PRIVYHUB_D087R1_LINUX_PS1_MULTITAP_METADATA_PATH:MEMORY:BEGIN -->
## External RetroArch paths must not be forced repo-relative

Linux RetroArch's XDG/user Config tree is intentionally outside the PrivyHub
repository. Once an external path is selected and validated against its trusted
Config root, metadata/logging must not subsequently call
`relative_to(project_root)` on it.

PS1 multitap `options_file` metadata:
- Windows portable runtime: retain existing project-relative form;
- Linux: `retroarch-config/...`, relative to the trusted RetroArch Config root.

Do not encode a specific Linux home directory into product metadata.
<!-- PRIVYHUB_D087R1_LINUX_PS1_MULTITAP_METADATA_PATH:MEMORY:END -->

<!-- PRIVYHUB_D087_LINUX_PS1_MULTITAP_CONFIG_PATH:MEMORY:BEGIN -->
## RetroArch Config-directory portability rule

Do not assume RetroArch's `config/<core>/*.opt` tree is adjacent to the emulator
executable on every host.

- Windows portable runtime: `<retroarch executable dir>/config`
- Linux AppImage: `$XDG_CONFIG_HOME/retroarch/config` when set, otherwise
  `~/.config/retroarch/config`

PS1 multitap's content-specific `.opt` adapter must resolve this host Config
root before locating/copying `Beetle PSX HW.opt`.

A failure in this pre-launch materialization layer does not invalidate the
runtime-validated PHI1/uinput/udev/A8 controller path.
<!-- PRIVYHUB_D087_LINUX_PS1_MULTITAP_CONFIG_PATH:MEMORY:END -->

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:MEMORY:BEGIN -->
## Linux controller parity accepted; multiplayer remains separate

On 2026-09-16, after D-085, the user tested three different games using three
different input profiles and reported all three ran correctly.

Durable interpretation:

- Linux PHI1 -> uinput -> RetroArch udev gameplay input is runtime accepted for
  the tested single-game/profile paths.
- The D-085 `ABS_HAT0X/Y` -> RetroArch `h0*` correction is runtime validated.
- Default RetroArch autoconfig and named A8 profile application both have
  integrated gameplay evidence.
- D-084's platform-aware A8 adapter is retained, with D-085's Linux hat
  correction authoritative over D-084's initial D-pad table.
- Earlier D-076 host-side "configured" evidence must not be mistaken for
  gameplay acceptance; D-085 supplies the missing gameplay acceptance.

PS1 multitap/multiplayer is a separate active Linux regression. Windows Phase A
proved the intended behavior, including CTR Port-1 multitap and four independent
players. Linux must reproduce that behavior without changing the now-validated
single-player/default/A8 controller path.
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:MEMORY:END -->

<!-- PRIVYHUB_D085_LINUX_UDEV_HAT_MAPPING:MEMORY:BEGIN -->
## Linux RetroArch udev hat rule

Do not derive RetroArch `udev` autoconfig tokens directly from Linux
`/dev/input/js*` axis indexes.

The PrivyHub uinput D-pad is correctly emitted as `ABS_HAT0X/ABS_HAT0Y`.
For RetroArch's `udev` frontend those directions must be bound as:
`h0up`, `h0down`, `h0left`, `h0right`.

The prior `input_up_axis = "-7"` / `input_left_axis = "-6"` form came from the
Linux joystick API measurement and was a frontend-translation error.

Keep the validated non-hat Linux layout unchanged:
- left stick axes 0/1;
- LT/RT axes 2/5;
- right stick axes 3/4;
- canonical face/shoulder/select/start/thumb button mapping.

Validation-boundary rule: RetroArch reporting a controller "configured" proves
profile matching/enumeration, not that every gameplay binding in that profile is
correct. Linux controller parity requires actual onn gameplay validation.
<!-- PRIVYHUB_D085_LINUX_UDEV_HAT_MAPPING:MEMORY:END -->

<!-- PRIVYHUB_D084_LINUX_A8_PLATFORM_ADAPTER:MEMORY:BEGIN -->
## A8 portability rule — platform-neutral profiles, platform-specific RetroArch binds

A8 profile JSON is intentionally host-agnostic: sources such as `a`, `x`,
`right_stick_left`, and `l2` mean physical/canonical controller controls, not
RetroArch numeric button or axis indices.

The final A8 session adapter must translate those canonical tokens through the
active host controller frontend:

- Windows ViGEm/XInput uses the established A8 XInput tables.
- Linux PrivyHub uinput/udev uses the measured Linux joystick layout represented
  by `data/games/retroarch/autoconfig/udev/PrivyHub Virtual Gamepad P1.cfg`.

Never reuse Windows numeric XInput indices as Linux udev indices merely because
PHI1/XUSB semantics upstream are identical. D-076 preserved semantic transport,
not frontend numbering.

The immutable `Default` A8 profile still emits no explicit gameplay binds and
continues to rely on the host-specific RetroArch autoconfig.
<!-- PRIVYHUB_D084_LINUX_A8_PLATFORM_ADAPTER:MEMORY:END -->

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:MEMORY:BEGIN -->
## D4 Linux post-migration durable facts — 2026-09-16

### Persistent Linux controller prerequisites are resolved

`uinput` must be loaded persistently at boot, not merely configured by a udev
rule. The validated development host uses:

`/etc/modules-load.d/99-privyhub-uinput.conf`

with `uinput`, plus the project ownership rule for `/dev/uinput`. After reboot
the device ownership is correct and the PrivyHub user retains the required
realtime-priority allowance. Treat the older "persistent uinput / RT priority
still required" bullets as superseded by this evidence.

### Controller fault boundary

If buttons work and live Linux event monitoring shows changing `EV_ABS` values
for `ABS_X`/`ABS_Y`, do not return to Android transport, network transport,
uinput permissions, or analog-generation code by default. The current PS1
movement failure is isolated to RetroArch/core/session controller mode and
mapping behavior.

### rtw88 LPS is not the primary current stream cause

A run with ordinary LPS successfully disabled still produced severe socket
pressure (`SndbufErrors`, `RcvbufErrors`, and audio send errors). The repeated
rtw88 LPS fault is genuine but did not explain the stream failure by itself.
Do not productize LPS-off as the primary fix without new evidence.

### Temporary Windows router and ExpressVPN

The Windows PC is a development routing bridge, not the intended PrivyHub
network architecture. ExpressVPN has two independently observed effects:

1. its `expressvpn-pkf` binding on physical adapters can block forwarded
   Wi-Fi-to-Ethernet traffic;
2. even with those physical bindings disabled, an active VPN moves Windows'
   Internet route to the ExpressVPN interface, while Linux-forwarded Internet
   traffic does not successfully traverse that VPN path.

Local Linux-to-Windows reachability remains healthy in the second case. This is
a temporary-topology limitation, not a Linux/PrivyHub defect. Defer further
work; disconnect ExpressVPN when the Linux development host requires upstream
Internet.

### Android signing migration is separate from runtime behavior

`INSTALL_FAILED_UPDATE_INCOMPATIBLE` during Linux APK installation was traced to
different Android signing certificates between the already-installed package
and the Linux-built APK. Treat signing migration separately from game/runtime
debugging.

### Unresolved observations are not conclusions

A Linux hard freeze observed after a paused/stale game stream does not establish
a memory leak, GPU fault, or driver root cause without supporting kernel/runtime
evidence. Preserve the observation and reopen only if it recurs with measurable
evidence.

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:MEMORY:END -->

<!-- D4_LINUX_HANDOFF_FIX_01_MEMORY -->
## D4 Linux game handoff durable facts — 2026-09-15

- Linux Android build baseline is validated with the project unchanged before the D4 handoff patch.
- `load_state()` deliberately verifies RetroArch remains paused after loading during launch; a lost Android HTTP response can strand a correctly loaded session in the safe paused state.
- Require `host_window_policy.window_found` only when `host_window_policy.supported` is true.
- Retry only idempotent load-state transport failures, once; do not generalize to launch/save/end POSTs.
- User-visible game networking errors must redact literal IPv4 addresses.


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

<!-- PRIVYHUB_ADB_RECOVERY_PROBE_LINUX_PARITY_2026_09_15:MEMORY:BEGIN -->
## Wireless-ADB diagnostic parity rule

On Linux, `probe_adb_wireless_recovery.py` must follow the accepted D-053
bounded recovery semantics rather than only auditing mDNS/transport counts:
private cached target -> online transport -> mDNS connect -> reconnect offline ->
one ADB-server restart and bounded retry -> only then preserved-pairing Wireless
debugging Off/On. The private target may contain a network endpoint and must
never enter shareable logs, Git, or durable memory.

<!-- PRIVYHUB_ADB_RECOVERY_PROBE_LINUX_PARITY_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_2026_09_15:MEMORY:BEGIN -->
## Wireless-ADB endpoint-lifetime rule

Treat wireless-ADB pairing identity and `IP:port` endpoint as separate lifetimes.
The paired key may remain valid while the TLS listener restarts on a different
random port. A cached endpoint is therefore disposable. Recovery may reuse a
privately known host address, discover listening ports only on that one host,
and accept a new endpoint only after paired ADB authentication plus `get-state`
validation. Never expose or persist host/port values in shareable logs or durable
memory. mDNS remains useful but is not sufficient as the sole recovery path in
the representative environment.

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_V5_2026_09_15:MEMORY:BEGIN -->
## Wireless-ADB repair fallback rule

A successful manual `adb connect` after v4 failure proves that a recovery failure
must not be equated with lost pairing. Seed private endpoint host state whenever
ADB is online, learn the device's live `/proc/sys/net/ipv4/ip_local_port_range`,
and limit stale-port search to that one host/range. If bounded recovery still
fails, prompt the local operator to repair/re-pair and retry once. The probe does
not perform pairing itself and never places host, endpoint, pairing code, serial,
or mDNS identity into shareable logs or durable memory.

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_V5_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_ADB_ENDPOINT_DEBUG_V6_2026_09_15:MEMORY:BEGIN -->
## ADB endpoint-debug rule

When automatic ADB recovery disagrees with a manually successful `adb connect`,
inspect the exact selected endpoint before changing pairing, mDNS, router, or
scan architecture again. Literal host/port output is allowed only in an explicit
local terminal debug mode and must remain excluded from shareable logs and
durable memory.

<!-- PRIVYHUB_ADB_ENDPOINT_DEBUG_V6_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_ADB_ENDPOINT_WATCH_V7_2026_09_15:MEMORY:BEGIN -->
## ADB scanner observability rule

When validating concurrent endpoint discovery, absence of a port from an
"open-candidate" log is not evidence that it was skipped. Use the explicit
watch-port instrumentation to distinguish not-in-range/not-completed from a
completed CLOSED/UNREACHABLE result. Literal endpoints remain local-only.

<!-- PRIVYHUB_ADB_ENDPOINT_WATCH_V7_2026_09_15:MEMORY:END -->
