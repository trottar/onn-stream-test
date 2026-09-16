---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Active Investigations and Queued Work

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:ACTIVE:BEGIN -->
## 2026-09-16 active reconciliation

This section supersedes older Phase-D queued bullets where they conflict with
newer runtime evidence.

### RetroArch PS1 analog controller mode

**Status:** ACTIVE / NARROWLY ISOLATED

Proven below the RetroArch/core layer:

- Android controller packets arrive;
- Linux PHI1 injection works;
- four-pad uinput architecture remains valid;
- RetroArch detects `PrivyHub Virtual Gamepad P1`;
- the virtual pad exposes the expected absolute axes;
- live `ABS_X` / `ABS_Y` values change.

Next diagnostic scope is only PS1 controller mode/core/session configuration
(digital PlayStation pad versus DualShock/analog behavior).

### Linux normal-use acceptance

**Status:** QUEUED AFTER ANALOG FIX

Rerun launch, video, process audio, controller, Pause/Resume, Save/Load, and End.
Persistent uinput module/ownership and realtime-priority prerequisites are
already validated and are no longer active setup tasks.

### Android auto-open handoff

Keep the already-installed D4 handoff fix on its own acceptance track. Do not
conflate a remaining auto-open runtime check with the controller-mode issue.

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:ACTIVE:END -->

<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15 -->

This file contains only current active/queued work. Completed chronology belongs
in `CLOSED.md`/evidence/history. The paused transport root-cause branch belongs
in `DEFERRED.md`.

## Phase D Linux normal-use parity

**Status:** ACTIVE

Validated host/product seams:

- D-073 Linux host/emulator baseline;
- D-074 exact-window X11/VAAPI video;
- D-075/D-075R1 PulseAudio process audio and RT sender requirement;
- D-076/R1/R2 PHI1/uinput controller runtime + managed autoconfig;
- D-077 platform-aware normal product runtime selection;
- D-078 Linux companion media-server startup;
- integrated PS1 launch/save-load/window-discovery/VAAPI encode boundary.

Remaining Phase-D work that does not require reopening router diagnosis:

1. fix Android automatic stream handoff so Linux does not depend on the
   Windows-only `host_window_policy.window_found` preflight;
2. establish persistent service-scoped `/dev/uinput` permission;
3. establish persistent RT-priority allowance for the Linux PHA1 sender;
4. restore user-provided PS1 BIOS before final PS1 acceptance;
5. rerun representative normal-path regressions when a usable transport path is
   available.

## Android Linux auto-open handoff

**Status:** CONFIRMED BUG / READY FOR NARROW PATCH

Evidence already proves the Linux native backend can discover the managed X11
window after the legacy Windows preflight reports false. No new diagnostic is
needed before fixing the gate.

Preserve all transport, decoder, video, audio, controller, save/load, and game
lifecycle behavior.

## Remaining Phase C on Linux

**Status:** QUEUED AFTER PHASE-D BASELINE

Do not skip these items:

- low-interruption Linux bitrate actuator + automatic controller;
- C4 adaptive FEC or explicit evidence-backed deferral;
- C5 1080p60 capability characterization;
- C6 generalized native source abstraction;
- C7 final Phase-C checkpoint.

Windows fixed-ladder/restart evidence is input evidence only, not a Linux
constant.
