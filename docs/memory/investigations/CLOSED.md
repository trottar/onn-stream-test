---
memory_schema: 1
as_of: 2026-09-15
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Closed Investigations

<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:CLOSED:BEGIN -->
## Linux PS1 multiplayer / multitap regression — closed

**Status:** RUNTIME VALIDATED 2026-09-16

Root portability fixes:
- D-087: Linux RetroArch Config tree uses the active XDG/user Config directory
  rather than the Windows executable-adjacent portable path;
- D-087R1: external Linux Config paths are represented safely in metadata rather
  than forced through `relative_to(project_root)`.

Runtime acceptance:
- Crash Bash launched with Multitap On;
- Players 3/4 were available;
- four remotes/controllers were independently routed.

Classification:
`LINUX_PS1_MULTITAP_FOUR_PLAYER_PARITY_CONFIRMED`
<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:CLOSED:END -->

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:CLOSED:BEGIN -->
## Linux gameplay controller regression — closed for tested profiles

**Status:** RUNTIME VALIDATED 2026-09-16

D-085 corrected the Linux RetroArch udev D-pad mapping from joystick-axis
`+/-6/7` assumptions to the udev hat tokens `h0up/h0down/h0left/h0right`, and
aligned the Linux A8 adapter with the same frontend representation.

After restart, the user tested three different games with three different input
profiles and reported correct gameplay in all three.

Closed preservation boundary:
- Android -> PHI1;
- Linux uinput generation;
- RetroArch udev detection/autoconfig;
- D-085 default D-pad translation;
- D-084/D-085 named-profile translation.

This closure does not include PS1 multitap/four-player topology. That remains an
active separate investigation.
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:CLOSED:END -->

<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15 -->

## Stable closed work

Do not reopen absent fresh contradictory evidence:

- A4 game-audio/host lifecycle recovery and coexistence;
- A8 mapping assignment boundary and P1-P4 profile/editor behavior;
- A6 transient artwork disappearance;
- cheat/mod namespace isolation;
- Phase A A9 regression/checkpoint and PS1 Port-1-only multitap validation;
- NES/Genesis A9 no-fixture identity issue;
- wireless ADB recovery/stale-cache correction;
- Phase B health/client-feedback/classifier/Diagnostics/Self-Test/support-bundle/
  retention work;
- Sunshine/Moonlight active-edge, artifact, and device-package removal;
- B5/B6 native-only regression and clean-native checkpoint;
- C1 inventory and C1.1 static profile extraction;
- C2 telemetry implementation/runtime validation;
- Windows fixed-bitrate characterization;
- Windows bidirectional restart-actuator characterization.

Exact older chronology is preserved in Git and `history/`.

## D083 router netdev-counter branch

**Status:** CLOSED AS INVALID DIAGNOSTIC BRANCH

D083 and D083R1 did not produce valid networking measurements. The first run had
insufficient samples and a false-success wrapper; the revision relied on
`nohup`, unavailable on the router. A smoke classifier also contradicted raw
mount evidence.

The underlying UDP root cause is not closed; it is **paused/deferred** in
`DEFERRED.md`. D082 remains the last valid router-boundary evidence.
