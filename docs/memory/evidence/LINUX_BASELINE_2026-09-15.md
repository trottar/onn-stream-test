# Linux Native Baseline — 2026-09-15

Status: **D1 LINUX BASE PLATFORM / RETROARCH / NATIVE VIDEO ARCHITECTURE VALIDATED**

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

## Managed PID to X11 window identity

Baseline 29 launched real SNES content through EmulatorManager and used the
manager-owned RetroArch PID as the X11 ownership anchor.

Observed:
- exactly one visible X11 window belonged to the managed PID;
- `_NET_WM_PID` exactly matched the EmulatorManager PID;
- WM_CLASS was `retroarch`;
- the game window was `IsViewable`;
- the game window had valid capture dimensions;
- shutdown remained graceful.

The AppImage process executable resolved through `/proc/<pid>/exe` to the
temporary AppImage mount. Therefore executable-path equality is not an
appropriate Linux ownership check.

Result: **MANAGER-OWNED PID -> EXACT X11 RETROARCH WINDOW VALIDATED**

Linux native capture should fail closed around the manager-owned PID and must
never broaden to whole-desktop capture.

## Single-process Linux video path through existing FEC relay

Baseline 30 exercised:

managed RetroArch -> exact X11 window -> FFmpeg x11grab -> Renoir VAAPI H.264
-> RTP loopback -> existing NativeVideoFecRelay -> local UDP receiver.

Observed:
- 300 frames over 5 seconds at real-time speed;
- H.264 High, 1280x720, 60 fps;
- FFmpeg exit code 0;
- 4,010 RTP packets accepted by the existing relay;
- 605 PHF1 parity packets emitted across 605 groups;
- zero skipped relay packets;
- zero relay send errors;
- downstream receiver observed all 4,010 RTP and 605 PHF1 packets;
- game shutdown remained graceful.

Result: **SINGLE-PROCESS X11GRAB -> VAAPI -> RTP -> EXISTING FEC RELAY VALIDATED**

Linux does not require a WGC-style raw-frame bridge. The preferred native-video
shape is one FFmpeg capture/encode process feeding the existing portable FEC
relay.

## VAAPI RTP Android bootstrap compatibility

Baseline 31 inspected the actual H.264 RTP packetization produced by the
validated Linux VAAPI path.

Observed:
- 4,027 RTP packets;
- 606 PHF1 FEC packets;
- SPS present through STAP-A;
- PPS present through STAP-A;
- IDR present through STAP-A and FU-A;
- Android bootstrap shape compatibility: true;
- FFmpeg exited successfully;
- game shutdown remained graceful.

Result: **LINUX VAAPI RTP BOOTSTRAP IS COMPATIBLE WITH THE EXISTING ANDROID RECEIVER**

No Android video-protocol change and no Linux WGC-equivalent raw-frame bridge
are required.

## D-074 production Linux native-video runtime validation

The first production Linux native-video backend was installed and exercised
against a real managed SNES session.

Observed:
- stream ready: true;
- stream active: true;
- capture backend: `x11grab_window`;
- encoder: `h264_vaapi`;
- exact managed RetroArch window selected;
- stream remained active after five seconds;
- 4,500 RTP packets traversed the existing FEC relay;
- 680 PHF1 parity packets traversed the existing FEC relay;
- zero skipped relay packets;
- zero relay send errors;
- downstream diagnostic receiver observed the same RTP/FEC packet counts;
- stream teardown returned inactive;
- RetroArch shutdown remained graceful.

FFmpeg sustained approximately 60 fps and terminated normally via SIGTERM during
managed stream teardown.

Result: **D-074 LINUX NATIVE VIDEO BACKEND HOST-SIDE RUNTIME VALIDATED**

This validates the production host path:
managed RetroArch PID -> exact X11 window -> x11grab -> VAAPI H.264 ->
existing RTP/FEC relay.

Android, audio, controller, FEC format, and emulator lifecycle were unchanged.
Full onn/Android E2E remains a later integration validation boundary.

## Managed RetroArch PID to isolated PulseAudio route

Baseline 32 launched real SNES content through EmulatorManager and resolved the
managed RetroArch PID to its PulseAudio playback stream.

Observed:
- exactly one sink-input matched the managed RetroArch PID;
- a temporary dedicated PrivyHub null sink was created at s16le stereo 48 kHz;
- the exact managed sink-input moved successfully into that sink;
- the dedicated monitor captured useful non-silent PCM;
- three-second capture produced 574,396 bytes;
- PCM peak was 8,958 and RMS was 1,154.454;
- the original sink restoration was requested successfully;
- RetroArch shutdown remained graceful;
- the temporary sink unloaded successfully.

Result: **MANAGED PID -> EXACT PULSEAUDIO STREAM -> ISOLATED MONITOR VALIDATED**

Linux native audio can preserve process isolation by moving only the
EmulatorManager-owned RetroArch sink-input into a dedicated PrivyHub sink.

## Linux PHA1 cadence diagnostic — initial pacer rejected

Baseline 33 combined the validated isolated PulseAudio route with a Python
absolute-deadline 5 ms PHA1 sender.

Capture/packet integrity passed:
- 1,000 packet opportunities;
- 1,000 packets sent;
- zero sender underflows;
- 1,000 packets received;
- zero malformed packets;
- zero sequence gaps;
- useful non-silent audio observed.

Timing did not pass:
- average send interval: 5.0 ms;
- 47 send intervals below 2 ms;
- 46 send intervals at or above 8 ms;
- send maximum: 12.5274 ms;
- receiver timing showed the same burst/gap pattern.

Result: **AUDIO SOURCE/PHA1 SHAPE VALID; SIMPLE PYTHON SLEEP PACER REJECTED**

The symmetric late-then-catch-up pattern indicates pacing scheduler jitter, not
PCM starvation. Do not reject the PulseAudio architecture from this result.

## Linux hybrid 5 ms audio pacer

Baseline 34 isolated the PHA1 sender timing from PulseAudio.

Observed:
- 1,000 packets sent and received;
- zero malformed packets;
- zero sequence gaps;
- send interval average 5.0 ms;
- send p95 5.0381 ms;
- send max 5.0786 ms;
- zero intervals below 2 ms;
- zero intervals at or above 8 ms;
- receiver timing remained similarly stable.

Result: **HYBRID MONOTONIC 5 MS PHA1 PACER VALIDATED**

Baseline 33's burst/gap behavior was caused by the simple sleep-based pacer,
not by the PulseAudio capture architecture.

## D-075 first production runtime — functional path passes, cadence rejected

D-075 production runtime validated routing, capture, PHA1 integrity, restoration,
and shutdown, but did not pass packet-cadence acceptance.

Observed:
- 1,140 packets sent and received;
- zero malformed packets and zero sequence gaps;
- zero send errors;
- useful non-silent PCM after gameplay resume;
- only two additional sender underflows after resume;
- original PulseAudio route restored;
- temporary sink removed;
- video remained active;
- graceful game shutdown.

Cadence remained unacceptable under the full production stream:
- send average 5.0007 ms;
- p95 7.9436 ms;
- 57 intervals below 2 ms;
- 55 intervals at or above 8 ms.

Result: **D-075 FUNCTIONAL AUDIO PATH VALIDATED / PRODUCTION CADENCE NOT ACCEPTED**

Do not commit D-075 yet. Next isolate the production NativeAudioStreamer from
the concurrent video/FEC workload.

## Linux audio GIL switch-interval diagnostic

Baseline 36 reran the installed D-075 audio backend in isolation with the
Python thread switch interval reduced from 5 ms to 1 ms.

Observed:
- audio remained active;
- zero send errors;
- zero malformed packets;
- zero sequence gaps;
- send average remained ~5 ms;
- 81 intervals below 2 ms;
- 73 intervals at or above 8 ms.

Result: **PYTHON THREAD SWITCH INTERVAL HYPOTHESIS REJECTED**

Reducing the interpreter switch interval did not remove the burst/gap pattern.

## Linux audio Event.wait versus sleep diagnostic

Baseline 37 replaced only the production pacer coarse Event.wait(1 ms)
stage with time.sleep(1 ms), matching Baseline 34 more closely.

Observed:
- 1,020 packets sent and received;
- zero malformed packets and zero sequence gaps;
- send average 5.0 ms;
- p95 8.0325 ms;
- 64 intervals below 2 ms;
- 60 intervals at or above 8 ms.

Result: **EVENT.WAIT PACER HYPOTHESIS REJECTED**

The cadence regression remains inside the production audio path and is not
explained by Event.wait versus time.sleep.

## Linux production audio sender stage timing

Baseline 38 instrumented the installed D-075 sender without changing project source.

The PCM buffer handoff was effectively free:
- lock-wait p95 0.0018 ms, max 0.0124 ms;
- lock-hold p95 0.0109 ms, max 0.0657 ms.

The dominant delay occurred before buffer access:
- wake-late average 0.4735 ms;
- wake-late p95 3.8561 ms;
- wake-late max 7.8806 ms;
- 96 wakeups at least 2 ms late.

UDP send calls were normally short but had occasional measured scheduling-sized excursions:
- send-call p95 0.0646 ms;
- send-call max 5.844 ms;
- 14 measured calls at least 2 ms.

Result: **PCM BUFFER LOCK CONTENTION REJECTED**

The primary cadence failure is sender-thread wake lateness before shared-buffer access.
Next isolate whether managed RetroArch workload alone causes that wake lateness.

## Pure 5 ms pacer under active RetroArch workload

Baseline 39 reran the previously stable Baseline-34 hybrid pacer while only
adding an active managed RetroArch game. PulseAudio routing, FFmpeg audio,
PCM buffering, native video, and FEC were absent.

Observed:
- 1,000 packets sent and received;
- zero malformed packets and zero sequence gaps;
- send average 5.0 ms;
- send p95 8.6571 ms;
- 55 intervals below 2 ms;
- 55 intervals at or above 8 ms;
- graceful game shutdown.

Result: **NORMAL-SCHEDULER 5 MS USERSPACE PACER NOT RELIABLE UNDER ACTIVE RETROARCH**

Active RetroArch workload alone reproduces the D-075 burst/gap pattern.
PulseAudio, FFmpeg capture, PCM locking, video, and FEC are not required to cause it.

## Lowest-priority real-time pacer under active RetroArch

Baseline 40 repeated the pure 5 ms pacer under active managed RetroArch but
changed only the pacing thread scheduling policy to SCHED_RR priority 1.

Observed sender timing:
- 1,000 packets sent;
- average 5.0 ms;
- p95 5.0346 ms;
- max 5.0756 ms;
- zero intervals below 2 ms;
- zero intervals at or above 8 ms;
- zero malformed packets or sequence gaps.

Result: **SCHED_RR PRIORITY 1 RESTORES RELIABLE 5 MS SENDER PACING UNDER RETROARCH**

Normal Linux scheduling under active RetroArch is the established cause of
D-075 sender wake lateness. Do not continue tuning PulseAudio, FFmpeg, PCM
locking, Python switch intervals, or the hybrid deadline loop.
## Baseline 41 — thread-local real-time sender scheduling

Baseline 41 promoted only the dedicated pacing thread to `SCHED_RR` priority 1
while leaving the process main thread at `SCHED_OTHER`.

Observed:
- main thread remained `SCHED_OTHER`, priority 0;
- sender thread became `SCHED_RR`, priority 1;
- 1,000 packets sent and 1,000 received;
- zero malformed packets and zero sequence gaps;
- send average 5.0 ms;
- send p95 5.0318 ms;
- send max 5.116 ms;
- zero send intervals below 2 ms;
- zero send intervals at or above 8 ms;
- graceful game shutdown.

Result: **THREAD-LOCAL SCHED_RR/1 PACER VALIDATED**

This is the production scheduler boundary for the D-075R1 correction. The
persistent privilege grant is not part of D-075R1; service-scoped
`RLIMIT_RTPRIO=1` remains the preferred deployment mechanism.

## D-075R1 Linux native-audio production runtime

D-075R1 production runtime revalidation passed.

Observed:
- Linux managed-process PulseAudio isolation remained functional;
- audio sender thread successfully entered SCHED_RR priority 1;
- companion/main execution remained outside that RT scheduling change;
- audio remained active across paused startup and gameplay resume;
- 1,039 PHA1 packets were sent and received;
- zero send errors;
- zero malformed packets;
- zero receiver sequence gaps;
- 532 non-silent packets were observed after resume;
- sender interval average 4.9999 ms;
- sender interval p95 5.0397 ms;
- sender interval max 8.0572 ms;
- one interval below 2 ms;
- one interval at or above 8 ms;
- original PulseAudio route restored after stream stop;
- dedicated temporary sink removed;
- native video remained active during the test;
- RetroArch shutdown remained graceful.

Probe classification:
**d075r1_runtime_validated=True**

Result:
**D-075R1 LINUX NATIVE AUDIO BACKEND RUNTIME VALIDATED**

The established Linux native-audio design is managed RetroArch PID -> exact
PulseAudio sink-input -> dedicated 48 kHz stereo PrivyHub sink -> monitor
capture -> PCM16/PHA1 v1 -> sender-thread-only SCHED_RR priority 1.

Normal SCHED_OTHER pacing under active RetroArch was experimentally rejected.
Do not reopen the PulseAudio, Python GIL, buffer-lock, Event.wait, or ordinary
pacer investigations without contradictory new runtime evidence.
