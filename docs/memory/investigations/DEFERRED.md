---
memory_schema: 1
as_of: 2026-09-15
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Deferred / Paused Investigations

<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15 -->

## Linux + home Opal + onn UDP transport root cause

**Status:** PAUSED AFTER D083 CLOSEOUT

The old Prototype-1 pathology was successfully replayed on the representative
Linux path and reproduced bidirectionally while idle. Therefore it is no longer
valid to describe this as merely an old Windows/test-environment issue.

Established:

- severe burst/gap transformation and same-stamp duplication occur without game
  load in both directions;
- a Linux-only sender implementation cannot explain it;
- standard Opal `wlan0`, `wlan1`, and `br-lan` tcpdump/AF_PACKET observation
  points were zero-record during confirmed traffic;
- disabling exposed OpenWrt software/hardware flow-offload flags did not repair
  the transport or capture visibility;
- proprietary Siflower networking components remain in the unresolved region;
- D083/D083R1 are invalid as networking evidence;
- D082 is the last valid router-boundary measurement.

Do not continue open-ended router/vendor reverse engineering. Reopen only when:

1. a single bounded measurement would change a product/roadmap decision; or
2. the preserved synthetic suite can be run on a different representative
   network/router path.

Production bitrate/FEC/decoder thresholds must not be tuned to hide this
unresolved environment/path behavior.

## Game Session banner latency

A prior multi-second appearance delay is UI-lifecycle polish, not a current
blocker. Do not perturb stable game/audio/controller lifecycle without a
focused diagnostic.

## BPS/UPS/XDelta mod specifics

Supported through the existing path but not separately promoted unless a real
mod/runtime failure is observed.

## Full clean-machine Windows bootstrap

Comprehensive Windows clean-machine reproducibility is deferred. Linux normal-
use parity is Phase D and representative Linux sizing belongs to Phase E.
