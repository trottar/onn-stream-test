---
memory_schema: 1
as_of: 2026-09-15
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Current Handoff

<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15 -->

## Resume point

Current work is **Phase D Linux migration / native Linux baseline**. Phase C is
not complete; it is paused at the Windows portability boundary and resumes on
Linux after the Phase-D baseline is usable.

Authoritative Phase-D Linux root:

`/home/privyhub/Projects/onn-stream-test`

The older Windows checkout is reference/history unless explicitly synchronized for a cross-platform regression. Linux local source and fresh runtime evidence outrank GitHub. GitHub checkpoint
`88c797ea3a7659035ef4a45380789cfe8c5cbc53` is the predecessor reference for
this memory normalization only.

## What already works on Linux

Do not reopen these without contradictory evidence:

- project-owned RetroArch Linux runtime/cores;
- existing EmulatorManager lifecycle and graceful End;
- D-074 exact owned X11 window -> x11grab -> VAAPI video backend;
- D-075R1 PulseAudio isolated process audio with sender-thread `SCHED_RR/1`;
- D-076/R1/R2 PHI1 -> four uinput controllers + managed project autoconfig;
- D-077 normal product runtime/core selection;
- D-078 normal Linux companion media-server startup;
- integrated PS1 launch, existing save load, exact X11 discovery, and near-60-fps
  VAAPI encode.

Windows remains a separate validated backend; do not damage it while finishing
Linux parity.

## Current integrated blocker

The representative Linux + home Opal + onn path reproduces severe UDP
burst/gap/duplication while idle in **both directions**.

Forward Test A:
- 3993 successful unique Linux sends;
- zero unique loss;
- 2626 same-stamp Android duplicates.

Reverse Test B:
- 4000 successful Android sends;
- 3894 unique Linux arrivals;
- 106 missing;
- 476 same-stamp duplicates.

This rules out a Linux-only sender and shows game/native-stream load is not
required. Production socket errors under load are secondary amplification.

Router work then showed zero-record packet captures at `wlan0`, `wlan1`, and
`br-lan` despite active endpoint traffic. Disabling exposed OpenWrt flow-offload
flags did not help. Proprietary Siflower networking components remain present.

D083/D083R1 are invalid as networking evidence. D082 is the last valid router
result. The router/Siflower reverse-engineering branch is **PAUSED**. Do not run
another router diagnostic by default.

Re-enter transport localization only if:

1. one bounded measurement would change a product decision; or
2. the same preserved synthetic suite can be run on a different representative
   network/router path.

## Separate confirmed Linux compatibility bug

Android automatic stream handoff still requires the Windows-only
`host_window_policy.window_found`. On Linux this can be false even though the
native backend later finds the correct X11 window.

This explains `Game ready, stream not opened` before manual banner entry. The
bug is confirmed and ready for a narrow code fix; no more diagnosis is needed.

**Next production patch after memory cleanup:** fix this Linux auto-open gate
without touching transport, video, audio, controllers, decoder policy, bitrate,
or FEC.

## Other Phase-D gaps

- Persistent service-scoped `/dev/uinput` access.
- Persistent `RLIMIT_RTPRIO=1`/equivalent for the Linux audio sender; do not use
  broad `CAP_SYS_NICE` on Python.
- Restore user-provided PS1 `scph5501.bin` before final PS1 acceptance.
- Final representative Android/onn E2E remains transport-blocked.

## Do not do next

Do not:

- tune Android stabilization thresholds to hide the transport problem;
- change bitrate/FEC based on the current failure;
- alter decoder policy;
- replace validated x11grab/VAAPI, PulseAudio, PHI1/uinput, or EmulatorManager
  lifecycle paths;
- continue open-ended Opal/Siflower reverse engineering;
- ask the user for an IP address.

## Roadmap

Execution order:

`Phase D Linux baseline -> remaining Phase C on Linux -> Phase E Linux characterization -> Phase F media/VOD/Live TV -> Phase G remote`

Windows C3 evidence to carry forward:
- explicit reference profile and C2 telemetry contract;
- startup stabilization;
- fixed 5500/6000/7000 ladder as test-environment evidence;
- 5000 rejected;
- restart-based actuator works bidirectionally but causes ~1 s visible
  interruption and is not the automatic actuator.

## Proven Linux command

From `/home/privyhub/Projects/onn-stream-test`:

`python3 ./companion/privyhub_service.py`

Do not substitute the historical Windows PowerShell build/install command into the Linux handoff.

For game-stream diagnosis, prefer existing logs and
`tools/collect_game_session_diagnostics.py` before adding new probes.

## Working rules

- one narrow hypothesis -> one targeted diagnostic -> fresh evidence -> one
  coherent patch;
- raw measurements outrank classifiers;
- restart the companion after Python changes before runtime judgment;
- preserve network privacy; never request or expose addresses;
- meaningful fixes update durable memory in the same work.
