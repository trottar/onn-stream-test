# Linux Native Baseline — 2026-09-15

Status: **D1 BASE PLATFORM CAPABILITIES VALIDATED / RETROARCH RUNTIME NOT YET INSTALLED**

Baseline predecessor:

`894136397d9e1a8a3e8c8c22ba7c193b6dd17b9c`

Host:

- HP EliteDesk 805 G6 Mini
- AMD Ryzen 5 PRO 4650G
- 6 cores / 12 threads
- 16 GB class RAM
- 256 GB NVMe
- integrated Renoir / Radeon Vega graphics

Operating system:

- Debian GNU/Linux 13.7 (trixie)
- kernel `6.12.107+deb13-amd64`
- Xfce desktop
- X11 session
- hostname `PrivyHub`

## GPU / video acceleration

Kernel graphics driver:

`amdgpu`

DRM devices observed:

- `/dev/dri/card0`
- `/dev/dri/renderD128`

VAAPI:

- libva 2.22 / VA-API 1.22
- Mesa radeonsi Renoir driver
- direct DRM VAAPI initialization succeeds against `/dev/dri/renderD128`
- H.264 Constrained Baseline encode exposed
- H.264 Main encode exposed
- H.264 High encode exposed
- HEVC Main/Main10 encode also exposed

Debian FFmpeg:

- version `7.1.5-0+deb13u1`
- `vaapi` available
- `drm` available
- `h264_vaapi` available
- `hevc_vaapi` available
- `x11grab` available
- `kmsgrab` available

Synthetic hardware encode validation:

- 1280x720
- 60 fps source
- H.264 High profile
- target/max bitrate 7000 kbps
- GOP 15
- B-frames 0
- 300 frames encoded over 5 seconds
- FFmpeg exit code 0
- approximately 11.5x real-time synthetic encode speed

The 7000 kbps values here reproduce the existing Windows reference workload only
for capability validation. They are not yet accepted as Linux production tuning.

## Exact-window capture

FFmpeg `x11grab` exact-window capture was validated using X11 `window_id`.

Validated chain:

`X11 exact window -> x11grab -> NV12 upload -> VAAPI -> H.264`

Probe result:

- source window was viewable
- exact window dimensions captured
- 60 fps requested
- 300 frames encoded over 5 seconds
- H.264 High profile
- FFmpeg exit code 0

The first probe failed because the diagnostic retained a trailing comma in the
`xprop` window ID. Corrected probe `06v2` removed the comma and passed. This was
a probe defect, not a capture/backend failure.

RetroArch-specific window lifecycle behavior remains unvalidated. In particular:

- fullscreen behavior
- resize behavior
- minimize/unmap behavior
- occlusion behavior
- exact RetroArch window discovery

must be measured later rather than inferred from the terminal-window probe.

## Audio

Installed desktop audio server:

`PulseAudio 17.0`

PipeWire is not currently installed/running.

A temporary dedicated PulseAudio null sink was created and its monitor source
captured with FFmpeg.

Validated conceptual path:

`application -> PrivyHub-only PulseAudio sink -> sink monitor -> FFmpeg`

Probe result:

- temporary sink created
- monitor source created
- test tone routed to isolated sink
- monitor captured successfully
- stereo PCM output
- FFmpeg capture exit code 0
- non-silent captured signal measured

The temporary sink used 44.1 kHz while the capture output was 48 kHz, so
production configuration should use a native 48 kHz PrivyHub sink to avoid
unnecessary resampling.

No persistent audio configuration was created.

## Controllers

Kernel configuration:

`CONFIG_INPUT_UINPUT=m`

`uinput` module loading succeeded.

Current `/dev/uinput` permissions are root-only and require a later persistent
permission/service design.

Temporary Python/evdev probes successfully created Linux virtual gamepads.

Single-controller result:

- virtual event device created
- Linux joystick handler created
- probe exit code 0

Four-controller result:

- P1 -> event19 / js0
- P2 -> event20 / js1
- P3 -> event21 / js2
- P4 -> event22 / js3
- all four devices existed simultaneously
- creation/enumeration order was deterministic in this probe
- probe exit code 0

This validates the kernel/device mechanism needed to replace ViGEm with Linux
uinput while preserving the existing PHI1 protocol.

Production requirements still to validate:

- exact button mappings
- trigger/axis semantics
- four-player RetroArch enumeration
- controller creation before RetroArch input initialization
- stable persistent permissions

## RetroArch availability

Debian repository:

- RetroArch frontend available as `1.20.0+dfsg-2+b1`

Debian packages do not provide parity with the currently required PrivyHub core
set.

Current PrivyHub systems require Linux equivalents of:

- FCEUmm
- bsnes
- BlastEm libretro
- Beetle/Mednafen PSX HW

Therefore a project-owned Linux RetroArch/core runtime remains the leading
deployment approach rather than relying entirely on Debian-packaged cores.

No RetroArch frontend or PrivyHub emulator runtime has been installed yet.

## APT / clock bootstrap

Initial Debian installation contained no configured APT sources.

Standard Debian trixie repositories were configured:

- trixie
- trixie-updates
- trixie-security
- main
- non-free-firmware

The initial security-repository signature failure was caused by an incorrect
system clock inherited from the previous Windows RTC state.

`systemd-timesyncd` was installed and NTP enabled.

Validated state:

- system clock synchronized: yes
- NTP service: active
- RTC stored as UTC

Do not weaken APT signature verification.

## Current architecture conclusion

The Linux host has now demonstrated viable replacements for the core
Windows-specific streaming primitives:

- WGC exact-HWND capture candidate -> X11 exact-window capture
- NVENC H.264 -> Renoir VAAPI H.264
- Windows process-loopback audio candidate -> isolated PulseAudio sink monitor
- ViGEm -> Linux uinput

These are capability validations, not yet production implementation acceptance.

Next step:

**establish the project-owned Linux RetroArch/core runtime and then validate the
real RetroArch window, audio-routing, controller-enumeration, and game lifecycle
against these backend candidates.**

## RetroArch Linux runtime validation

Pinned frontend:

- RetroArch 1.22.2
- Git revision `86c77bf`
- build date 2026-09-07
- Linux x86-64 AppImage
- AppImage executes successfully on Debian 13 without additional FUSE setup
- frontend archive SHA-256:
  `eb11234bc632238792b1187da9ff60f0bb0215d64479d7ccc58f0498bf1da928`

Required Linux cores staged and dependency-checked:

- `fceumm_libretro.so`
  SHA-256 `9be9deeb159c7898944c688dcb414f4cfdaff73276db493c8890577a2099dcf6`
- `bsnes_libretro.so`
  SHA-256 `ab1306145a383a3b6d41e4e89874673980f3b1c6c7a90d92030017163511b4f8`
- `blastem_libretro.so`
  SHA-256 `44f7216250915cc00ed911993c762f19d0f09af01ab1a79f0335857fd04f15a3`
- `mednafen_psx_hw_libretro.so`
  SHA-256 `25176f77c060cf74c4561f745bab181d9bb6b620591f92f82ad0d53c1cc7fb56`

`ldd` reported no missing shared libraries for any of the four cores.

All four cores were then loaded by the pinned RetroArch frontend in separate
verbose runtime probes. Each initialized libretro API version 1 and exposed
valid video/audio geometry before the bounded diagnostic timeout terminated the
frontend.

Observed warnings:

- missing `libgamemode.so` is optional and does not block core operation;
- Wayland connection failure is expected because the validated desktop session
  uses X11; RetroArch continued through its X11 backend.

Result:

**RETROARCH 1.22.2 + ALL FOUR REQUIRED LINUX CORES LOAD SUCCESSFULLY**

This establishes the project-owned Linux frontend/core runtime foundation.
Game/content lifecycle integration remains unvalidated.

## RetroArch four-controller preflight validation

Four PrivyHub uinput gamepads were created before RetroArch startup.

RetroArch 1.22.2 selected the Linux `udev` joypad driver and enumerated all four
devices distinctly:

- Pad #0 -> PrivyHub Virtual Gamepad P1 -> event19
- Pad #1 -> PrivyHub Virtual Gamepad P2 -> event20
- Pad #2 -> PrivyHub Virtual Gamepad P3 -> event21
- Pad #3 -> PrivyHub Virtual Gamepad P4 -> event22

This validates the required startup ordering architecture:

`create P1-P4 virtual controllers -> start RetroArch -> enumerate four pads`

RetroArch reported each device as `not configured`. This is an autoconfiguration /
button-mapping gap, not a device-enumeration or permissions failure.

The production Linux controller backend may therefore preserve the existing PHI1
protocol and replace ViGEm with uinput. Persistent uinput permission and exact
RetroArch button/axis mappings remain to be established.


## RetroArch udev autoconfig validation

Baseline 17v2 validated that a PrivyHub uinput device with the full production-candidate capability set matches a local udev autoconfig profile and is configured in RetroArch port 1.

Result: **UDEV AUTOCONFIG DISCOVERY AND MATCHING VALIDATED**

## Real SNES launch validation

A copied SNES title was launched with the pinned RetroArch 1.22.2 frontend and bsnes Linux core.

- content loaded successfully
- X11 video rendered successfully
- PulseAudio output was audibly correct
- runtime lasted approximately 11 seconds before the bounded timeout
- core/game teardown completed cleanly

Result: **REAL SNES VIDEO + AUDIO + CONTENT LIFECYCLE VALIDATED**

## Real-game exact-window VAAPI capture

Baseline 19 validated real RetroArch gameplay through exact X11 window capture, aspect-preserving 1280x720 conversion, and Renoir VAAPI H.264 High encoding at 60 fps in real time.

Result: **REAL RETROARCH WINDOW -> X11GRAB -> VAAPI H.264 VALIDATED**

## X11 minimize lifecycle

Baseline 20v2 proved that exact-window x11grab capture terminates when the RetroArch target is minimized/unmapped. Capture stopped at 113 frames (~1.88 s) when the window became IsUnMapped. XShm acquisition failed, fallback X11 GetImage also failed, and restoring the window did not resume capture. FFmpeg still exited 0 after flushing the partial stream, so exit status alone is not sufficient stream-health evidence.

Result: **RETROARCH CAPTURE WINDOW MUST REMAIN MAPPED**

## X11 occlusion lifecycle

Baseline 21 kept the RetroArch game window mapped while fully covering it with another mapped X11 window. Exact-window VAAPI capture continued successfully, producing valid 1280x720 H.264 with 177 frames and 29 unique decoded frames during the 3-second probe.

The direct SSIM sub-check produced no reported result, so it is not treated as evidence. The dynamic decoded-frame count demonstrates that capture was not reduced to the static covering window.

Result: **MAPPED-BUT-OCCLUDED RETROARCH CAPTURE REMAINS LIVE**

## Python/runtime boundary

Baseline 22 imported all current native-stream and emulator-manager Python modules successfully on Debian.

Result: **NO TOP-LEVEL PYTHON IMPORT BLOCKERS ON LINUX**

Windows dependencies are runtime-gated rather than preventing the companion modules from loading.

## NativeStreamManager Linux status boundary

Baseline 23 constructed `NativeStreamManager` and queried status successfully on Linux.

Observed:
- manager construction succeeds;
- system FFmpeg is discovered;
- manager remains inactive and fail-closed;
- current video/audio/controller status still advertises Windows-specific backend semantics;
- Linux native-stream implementation is not yet present.

Result: **EXISTING MANAGER/CONTROL SURFACE IS REUSABLE, BACKEND IMPLEMENTATIONS REQUIRE PLATFORM SUBSTITUTION**

## Platform-boundary source audit

Baseline 24 identified five Linux migration surfaces:
- video capture/encode;
- audio capture;
- controller output;
- host telemetry;
- emulator runtime/config selection.

The emulator lifecycle itself is mostly platform-neutral; Windows host-window behavior is gated.

## Linux emulator runtime descriptor

Baseline 25 substituted only Linux RetroArch executable/core paths in a temporary emulator descriptor.

Observed:
- Linux RetroArch executable installed: true
- all four required Linux cores installed: true
- only readiness failure was the absent project-owned RetroArch config

Result: **EMULATOR MANAGER ACCEPTS THE LINUX RUNTIME LAYOUT**

## Windows durable RetroArch state migration

The external Windows project backup contained the authoritative persistent RetroArch state.

Portable state migrated:
- saves
- states
- cheat profiles
- mod profiles
- controller overrides
- PrivyHub state-slot metadata
- empty system directory

Generated Windows configuration was intentionally excluded.

Source and destination manifests both covered 129 files and matched byte-for-byte.

Manifest SHA-256:
`6de3fa8b67d5a0ee21ace20af9347b5cf0f5997f3a9d410fcd23d6410b18280c`

Result: **WINDOWS DURABLE RETROARCH STATE MIGRATED TO LINUX WITHOUT DATA CHANGES**

## Linux managed RetroArch configuration

A Linux project-owned `data/games/retroarch/retroarch.cfg` was created using:
- Linux project paths;
- PulseAudio;
- 48 kHz audio;
- windowed rendering;
- existing PrivyHub hotkey assignments;
- migrated save/state/system storage.

The user's global `~/.config/retroarch/retroarch.cfg` is not part of the production design.

## EmulatorManager Linux readiness

Baseline 27:

- `ready=True`
- `retroarch_installed=True`
- `retroarch_configured=True`
- `missing_cores=[]`
- `runtime_error=None`

Result: **EXISTING EMULATOR MANAGER READINESS MODEL WORKS ON LINUX**

## EmulatorManager real Linux lifecycle

Baseline 28 launched a real SNES title through `EmulatorManager`.

Observed:
- game ID `game_snes_84cbb2d09db83cb9`
- RetroArch command state `PLAYING`
- process remained active during the run
- Linux host-window policy safely reported unsupported/not-Windows
- `SAVE_FILES` confirmed
- graceful shutdown succeeded through POSIX `SIGTERM`
- no network-QUIT fallback required
- manager returned inactive after stop

Result: **EXISTING EMULATOR MANAGER LAUNCH/CONTROL/FLUSH/STOP LIFECYCLE RUNTIME-VALIDATED ON LINUX**

The emulator lifecycle layer is not a Linux migration blocker. Preserve it unless later save/state/profile regression evidence requires a change.
