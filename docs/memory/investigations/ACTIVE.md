---
memory_schema: 1
as_of: 2026-09-15
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Active Investigations and Queued Work

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
