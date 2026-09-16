---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Current Development State

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:CURRENT:BEGIN -->
## D-086 Linux controller parity checkpoint — runtime validated

D-085 is now **RUNTIME VALIDATED** on the representative Linux -> onn path.

User runtime acceptance after restarting the patched companion:

- three different games were launched;
- three different input profiles were exercised;
- all three ran with correct gameplay controls;
- this covers the normal/default RetroArch autoconfig path and multiple named
  gameplay-profile paths in the integrated Linux product flow.

This supersedes the earlier broad Linux controller blocker and the earlier
generic "PS1 analog controller mode" next-step language. Do not reopen PHI1,
uinput permissions, uinput control generation, RetroArch udev discovery, or the
D-pad frontend mapping without new contradictory evidence.

The confirmed Linux gameplay-input architecture is now:

`Android InputDevice -> PHI1 -> Linux uinput -> RetroArch udev -> Default/A8 gameplay profile -> core/game`

D-084 remains part of the accepted architecture: A8 source semantics are
platform-neutral and the final source-token adapter is host-specific. D-085
corrected the Linux udev hat representation inherited by both default
autoconfig and the D-084 Linux A8 adapter.

### Immediate next Phase-D work

**PS1 multiplayer / multitap parity on Linux is ACTIVE.**

The historical Windows Phase-A baseline remains authoritative for intended
behavior: manual Multitap On/Off, Port 1 enabled / Port 2 disabled, Players 3/4
available in CTR, and four independent controllers were runtime validated.

Current Linux report: multitap does not work. The exact failure boundary is not
yet classified.

Next work must use one narrow diagnostic before production changes:

1. verify the selected game's stored `ps1_multitap` override;
2. verify the generated content-specific Beetle PSX HW `.opt` contains Port 1
   enabled and Port 2 disabled;
3. verify P1-P4 Linux uinput pads are configured by RetroArch for that launch;
4. determine whether Players 3/4 become available and whether four controllers
   remain independently routed.

Do not continue broader Phase-D work until this multiplayer regression is
classified or explicitly deferred.
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:CURRENT:END -->

<!-- PRIVYHUB_D085_LINUX_UDEV_HAT_MAPPING:CURRENT:BEGIN -->
## D-085 Linux RetroArch udev D-pad correction — development patch

The controller investigation was reconstructed against the older Phase-A and
D-076 evidence instead of treating the newest summary as sufficient.

Authoritative distinction:

- Windows PHI1 -> ViGEm/XInput reached real 1P/2P/4P gameplay validation.
- D-076 Linux reached host-side managed RetroArch integration: P1-P4 device
  creation/enumeration, clean PHI1 updates, meta controls, Save/Load, and
  teardown.
- D-076's own acceptance record still listed actual gameplay controls as pending.
  Host integration was later being over-read as gameplay validation.

The exact Linux uinput measurement remains valid: the D-pad is emitted as
`ABS_HAT0X/ABS_HAT0Y`. The error was at the RetroArch udev binding boundary.
The four project autoconfigs encoded those hats as ordinary axes `6/7`.
RetroArch udev autoconfig semantics represent D-pad hats as
`h0up/h0down/h0left/h0right`.

D-085 changes only:
- P1-P4 project udev D-pad binds from `input_*_axis = +/-6/7` to
  `input_*_btn = h0...`;
- the D-084 Linux A8 source translator to use the same udev hat tokens;
- the existing A8 deterministic probe so it rejects the old Linux-axis form.

Buttons, sticks, triggers, PHI1, Android input, Linux uinput event generation,
Windows XInput behavior, PS1 Digital/DualShock selection, audio/video/networking,
and emulator lifecycle are unchanged.

Status: **DEVELOPMENT PATCH; ONN GAMEPLAY VALIDATION REQUIRED**.

First runtime discriminator after install: default-profile Crash must regain
D-pad movement. Analog behavior remains subject to the existing PS1
Digital/DualShock per-game controller mode and must not be conflated with this
D-pad correction.
<!-- PRIVYHUB_D085_LINUX_UDEV_HAT_MAPPING:CURRENT:END -->

<!-- PRIVYHUB_D084_LINUX_A8_PLATFORM_ADAPTER:CURRENT:BEGIN -->
## D-084 Linux A8 gameplay-profile adapter — development patch

Fresh source/memory reconciliation found a second controller issue distinct from
PS1 Digital-vs-DualShock mode.

A8 named gameplay profiles store platform-neutral physical control names, but
the A8.2 RetroArch adapter still translated those names with the original
Windows/XInput numeric layout. D-076 moved Linux controller output to
uinput/udev without changing A8 profile semantics. The project-owned Linux udev
autoconfig proves that Linux joystick numbering differs from XInput for X/Y,
Back/Start, triggers, right stick, D-pad, and Y-axis sign.

D-084 therefore keeps the A8 profile schema and Android editor unchanged while
making only the final RetroArch source-token translation host-specific:

- Windows -> existing XInput bindings, unchanged;
- Linux -> validated PrivyHub uinput/udev bindings.

The existing deterministic A8 adapter probe is made platform-aware and now
checks Linux face buttons, D-pad axis mapping, trigger/right-stick remapping,
legacy right-stick whole-axis mapping, and Back/Start numbering.

Status: **DEVELOPMENT PATCH; RUNTIME GAMEPLAY ACCEPTANCE PENDING**.

Next runtime check: restart the Linux companion, launch a game with an existing
custom input profile, and verify the configured gameplay permutation. Do not
change PHI1, Android controller transport, Linux uinput generation, or PS1
Digital/DualShock selection for this issue.
<!-- PRIVYHUB_D084_LINUX_A8_PLATFORM_ADAPTER:CURRENT:END -->

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:CURRENT:BEGIN -->
## D4 runtime reconciliation — 2026-09-16

**Status:** Phase D Linux migration remains active, but the newest runtime evidence
moves the immediate blocker beyond basic Linux host/network prerequisites.

Newest validated state:

- Linux companion service is reachable and normal game launch/streaming works
  after the temporary Windows-router path was corrected for ExpressVPN filter
  interference.
- `/dev/uinput` persistence is no longer an open deployment gap: `uinput` is
  loaded at boot through `/etc/modules-load.d/99-privyhub-uinput.conf`, the
  project udev ownership rule applies after reboot, and the PrivyHub account has
  the required realtime-priority allowance.
- Controller transport, Linux uinput injection, RetroArch pad discovery, and live
  `ABS_X` / `ABS_Y` analog events are all proven.
- The remaining controller issue is inside RetroArch/PS1 core controller-mode
  behavior (digital pad versus DualShock/analog session configuration), not
  Android transport, Linux permissions, uinput creation, or analog generation.
- The saved Linux/home-Opal UDP timing pathology remains a separate deferred
  transport investigation. Latest normal game streaming success does not prove
  that the older synthetic timing pathology disappeared, but it is no longer
  valid to treat basic Linux reachability or the Windows bridge as the current
  game-launch blocker.
- The repeated rtw88/LPS fault is real, but disabling ordinary LPS did not repair
  the failed stream run; do not treat LPS as the primary stream root cause.
- The Android/Linux auto-open compatibility fix is already represented by the
  current D4 handoff patch. Keep its dedicated runtime-acceptance status separate
  from the controller investigation.

### Temporary Windows/ExpressVPN bridge

The temporary topology uses Windows as the routed hop between the GL-iNet side
and Linux. `expressvpn-pkf` on the physical adapters was proven capable of
blocking that forwarded path.

Current development behavior with both physical-adapter bindings disabled:

- ExpressVPN disconnected: Windows Internet, Linux Internet, and PrivyHub local
  routing work.
- ExpressVPN connected: Windows Internet works, Linux still reaches its Windows
  gateway, but Linux Internet fails because Windows selects the ExpressVPN
  interface as its Internet route and the forwarded Linux traffic does not
  successfully traverse that VPN path.

This is **DEFERRED BY DESIGN**. It is a limitation of the temporary
Windows-as-router development topology, not a PrivyHub/Linux product defect.
Use ExpressVPN disconnected when Linux requires upstream Internet. Do not spend
more Phase-D time redesigning this bridge.

### Diagnostic precedence

Older ADB recovery diagnostics remain preserved in durable memory, but the newest
normal companion/game runtime succeeded. Do not let stale ADB probe resume notes
displace the current RetroArch analog issue unless ADB installation/recovery
actually fails again.

### Immediate next technical work

1. Narrow RetroArch PS1 controller-mode investigation only.
2. After analog movement is corrected, run the normal Linux game regression
   (launch -> video/audio/controller -> pause/resume -> Save/Load -> End).
3. Keep the saved UDP/router branch paused unless fresh evidence from normal use
   requires reopening it.
4. Restore user-provided PS1 BIOS before final PS1 acceptance if still absent.

### Do not reopen without new evidence

- ICS experimentation;
- Windows Firewall as the routed-path cause;
- Linux `/dev/uinput` permission/module-load debugging;
- Linux realtime-priority persistence debugging;
- ExpressVPN forwarding on the temporary Windows bridge;
- rtw88 ordinary-LPS tuning as the primary stream fix.

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:CURRENT:END -->

<!-- D4_LINUX_HANDOFF_FIX_01_CURRENT -->
## D4 Linux game handoff fix — development patch installed; runtime validation pending

- Unchanged Android baseline built successfully on Linux before this patch.
- PS1 slot load reached RetroArch and completed while the session remained intentionally paused; the client then lost the control response and did not finish launch handoff.
- Linux reports the legacy Windows host-window policy unsupported, so Android must not require `window_found` when that policy is unsupported.
- Patch scope: Android handoff gating, one bounded retry for idempotent load-state transport failures, and IPv4 redaction in game-facing errors.
- Next: install APK and runtime-test PS1 launch -> Load Save -> automatic native-stream handoff/resume.


<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15 -->

This file is the current-state entry point only. Detailed chronology belongs in
`memory/2026-09-15.md`, specific runtime facts belong in `evidence/`, and
superseded states remain recoverable from Git/history. When this file conflicts
with newer local source or fresh runtime evidence, the newer local evidence wins.

## Development position

| Phase | Status | Current meaning |
| --- | --- | --- |
| A — Games / Emulator | **COMPLETE / PUSHED** | Stable normal-use emulator/game baseline. |
| B — Diagnostics / Clean Native Baseline | **COMPLETE / PUSHED** | Diagnostics, support bundle, retention, and native-only cleanup complete. |
| C — Adaptive Streaming | **PAUSED AT PORTABILITY BOUNDARY** | Profiles, telemetry, startup stabilization, Windows fixed ladder, and restart-actuator evidence exist; automatic adaptation is unfinished and resumes on Linux. |
| D — Linux Migration / Native Linux Baseline | **ACTIVE** | Core Linux host/runtime seams are validated; integrated Linux/onn streaming reaches an external transport blocker. |
| E — Linux Characterization / Optimization | **PLANNED AFTER D + REMAINING C** | Resource sizing and optimization on representative Linux. |
| F — Media / VOD / Live TV UX | **PLANNED** | Resume media polish on Linux. |
| G+ | **FUTURE** | Remote foundation, extended emulation/import, home infrastructure, local intelligence. |

Execution order remains:

`D Linux baseline -> remaining C on Linux -> E -> F -> G`

## Phase D — validated Linux foundation

The following are established and should not be reopened without contradictory
evidence:

- Debian/Renoir Linux baseline with working H.264 VAAPI encode.
- Project-owned RetroArch 1.22.2 Linux AppImage and required NES/SNES/Genesis/PS1
  Linux cores load successfully.
- Existing `EmulatorManager` lifecycle is portable enough to preserve.
- D-074 Linux video backend: exact managed X11 RetroArch window -> `x11grab` ->
  VAAPI H.264 -> existing RTP/FEC contract.
- D-075/D-075R1 Linux process audio: PulseAudio isolated sink/monitor plus a
  sender thread that must obtain `SCHED_RR` priority 1 before PHA1 emission.
- D-076/R1/R2 Linux controller path: PHI1 -> four uinput pads, project-owned udev
  autoconfig, managed absolute autoconfig path, Save/Load/Pause/End host runtime
  validated.
- D-077 normal `GamesPlugin -> EmulatorManager` Linux runtime/core selection is
  host validated.
- D-078 normal Linux companion media-server startup uses Python
  `range_server.py`; Windows retains the PowerShell wrapper.
- Integrated PS1/onn launch crossed the emulator/runtime/capture boundary:
  existing save load, managed X11 window discovery, controller preflight, and
  near-60-fps VAAPI encoding all worked.

## Current blockers and known gaps

### 1. Linux/onn transport blocker

The deferred UDP pathology was reproduced on the representative Linux + home
Opal + onn environment while idle, in both directions.

Linux -> onn Test A:
- 3993 successful unique sends;
- zero unique loss;
- 2626 same-stamp duplicate Android arrivals;
- strong kernel-level burst/gap transformation.

onn -> Linux Test B:
- 4000 successful Android sends;
- 3894 unique Linux arrivals;
- 106 unique losses;
- 476 same-stamp duplicate arrivals;
- strong receive burst/gap transformation.

This rules out a Linux-only sender implementation and proves that game/capture
load is not required for the base pathology. Production socket errors under
load are an amplification, not a prerequisite.

Router localization then established:
- `wlan0`, `wlan1`, and `br-lan` AF_PACKET/tcpdump observations were zero-record
  during confirmed endpoint traffic;
- disabling exposed OpenWrt software/hardware flow-offload flags did not repair
  transport and did not restore packet-capture visibility;
- proprietary Siflower forwarding components remain present;
- D083/D083R1 produced no valid networking evidence and are explicitly invalid.

**Disposition:** the Opal/Siflower reverse-engineering branch is **PAUSED**.
D082 is the last valid router-boundary result. Do not issue another router
probe by default. Re-entry requires either a bounded measurement that changes a
product decision or a different representative network/router environment.

### 2. Android Linux auto-open compatibility bug

`MainActivity` still gates automatic native-stream handoff on the Windows-only
`host_window_policy.window_found`. Linux can report that legacy preflight false
while the authoritative Linux backend subsequently finds the correct X11
window. This is a confirmed compatibility bug; it does not need more diagnosis.

### 3. Linux deployment permissions

Host development validation used temporary access for `/dev/uinput` and
`RLIMIT_RTPRIO=1`. Persistent production/service-scoped permissions remain to be
implemented. Do not grant broad `CAP_SYS_NICE` to the Python interpreter.

### 4. PS1 BIOS migration gap

The integrated Linux PS1 run reported missing `scph5501.bin`. The core still
launched and an existing save loaded, so this was not the transport cause.
Restore user-provided BIOS content before final PS1 acceptance.

## Immediate next work

Do **not** resume open-ended router debugging.

The next production change after this memory normalization is the narrow
Android/Linux auto-open handoff fix, because its root cause is already proven and
it is independent of the paused transport investigation. Preserve the validated
Linux video/audio/controller/runtime paths while making that change.

In parallel, final Linux acceptance still requires persistent service
permissions and restoration of the user-provided PS1 BIOS. Representative stream
acceptance remains blocked until the transport environment is either bounded by
a product-level discriminator or tested on another representative network path.

## Preservation boundaries

Do not change these merely because the current integrated stream is unstable:

- Android stabilization thresholds;
- bitrate/FEC policy;
- decoder policy;
- PHI1/PHA1 wire formats;
- Linux x11grab/VAAPI capture/encode path;
- Linux PulseAudio isolation architecture;
- Linux uinput controller mapping;
- Save/Load/Pause/Resume/End lifecycle.

## Operational rules

- Authoritative Phase-D Linux root: `/home/privyhub/Projects/onn-stream-test`.
- The older Windows checkout is reference/history unless explicitly synchronized for a cross-platform regression.
- Current local source and fresh evidence outrank GitHub and summaries.
- Never ask the user to provide or paste IP addresses.
- Raw measurements outrank classifiers.
- Companion Python changes require a companion restart before runtime judgment.
- One narrow hypothesis -> one targeted probe -> fresh evidence -> one coherent
  patch.

<!-- PRIVYHUB_ADB_RECOVERY_PROBE_LINUX_PARITY_2026_09_15:CURRENT:BEGIN -->
## Active ADB diagnostic — Linux recovery parity

During D4 setup the Linux companion process/listeners/local API were healthy,
while the existing ADB audit found zero onn transports and zero TLS-connect
services. The v2 audit did not execute D-053 cached-target recovery. A narrow
v3 diagnostic patch now aligns the probe with the installer recovery sequence.
Status is **development patch / runtime validation pending**. Do not classify
the companion service as failed from ADB state alone.

<!-- PRIVYHUB_ADB_RECOVERY_PROBE_LINUX_PARITY_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_2026_09_15:CURRENT:BEGIN -->
## Active ADB diagnostic — ephemeral TLS-port recovery

Fresh Linux evidence shows Debian ADB 34.0.5, forced libadbmdns, and temporary
Google Platform Tools 37.0.1/LIBADBMDNS all observe zero TLS-connect services
while the onn remains paired. Windows previously recovered the same dual-radio
setup, so do not classify the Opal radio split as a permanent ADB blocker.

The current narrow hypothesis is a stale wireless-ADB endpoint: pairing survives
while Android restarts its TLS server on a new random port. The v4 diagnostic
adds single-private-host port refresh and paired-ADB verification. Status is
**development patch / runtime validation pending**.

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_V5_2026_09_15:CURRENT:BEGIN -->
## Active ADB diagnostic — v5 endpoint/range recovery

The v4 ephemeral-port diagnostic failed at runtime. A manual local `adb connect`
to the current onn endpoint succeeded immediately, proving pairing and basic
reachability remained healthy and locating the failure in PrivyHub endpoint
bootstrap/discovery.

The connected onn exposes no `service.adb.tls.port` value. Its kernel ephemeral
range was measured as 32768-60999. V5 treats that as representative-device
runtime evidence, learns/caches the live range whenever ADB is connected, scans
only the one privately known onn host and cached/measured range after staleness,
and prompts for repair/re-pair only after automatic recovery is exhausted.
Status remains **development patch / runtime validation pending**.

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_V5_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_ADB_ENDPOINT_DEBUG_V6_2026_09_15:CURRENT:BEGIN -->
## Active ADB diagnostic — literal endpoint debug

The v5 automatic endpoint recovery also failed at runtime while direct local
`adb connect <host>:<current-port>` continued to work. The active hypothesis is
therefore no longer pairing or TCP reachability; the exact endpoint selected by
the recovery probe must be observed directly.

The diagnostic now supports `--debug-endpoints`, which prints the literal cached
endpoint, resolved private host, scan range, open TCP candidates, each ADB
connect endpoint attempted, and its connect/get-state result to the local
terminal only. The normal shareable log remains redacted. Status is development
diagnostic / runtime validation pending.

<!-- PRIVYHUB_ADB_ENDPOINT_DEBUG_V6_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_ADB_ENDPOINT_WATCH_V7_2026_09_15:CURRENT:BEGIN -->
## Active ADB diagnostic — watch one known port

The literal endpoint debug proved that terminal output did not show every port
submitted to the concurrent TCP scan. A known-current port can therefore be
used as a narrow discriminator. `--debug-watch-port <port>` now reports whether
that exact port is in range, when its scan batch is scheduled, and whether its
TCP result is OPEN or CLOSED/UNREACHABLE. Runtime result remains pending.

<!-- PRIVYHUB_ADB_ENDPOINT_WATCH_V7_2026_09_15:CURRENT:END -->
