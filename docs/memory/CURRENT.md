---
memory_schema: 1
as_of: 2026-09-15
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Current Development State
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
