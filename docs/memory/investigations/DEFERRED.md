---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Deferred / Paused Investigations

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:DEFERRED:BEGIN -->
## Temporary Windows bridge + ExpressVPN forwarding

**Status:** DEFERRED BY DESIGN — 2026-09-16

The development topology temporarily routes Linux through the Windows PC.
ExpressVPN changes that host's routing/filtering in ways that are not required
by the intended product architecture.

Validated bounds:

- `expressvpn-pkf` on the physical Windows adapters can block the routed
  PrivyHub path;
- with both physical bindings disabled and ExpressVPN disconnected, Windows and
  Linux both have Internet and PrivyHub local routing works;
- with ExpressVPN connected, Windows Internet still works and Linux still
  reaches its Windows gateway, but Linux Internet fails;
- Windows forwarding remains enabled in both states;
- no active Windows `NetNat` or ICS sharing object explains the behavior;
- the selected Windows Internet route moves to the ExpressVPN interface while
  the VPN is active.

Decision: do not redesign the temporary bridge. Disconnect ExpressVPN whenever
Linux requires upstream Internet. Reopen only if Windows-as-router unexpectedly
becomes a product requirement.

## Linux hard-freeze observation

**Status:** DEFERRED UNTIL RECURRENCE WITH EVIDENCE

One hard freeze occurred while RetroArch was active and the onn game stream had
been left paused/stale for an extended period. No kernel evidence established a
memory leak, GPU fault, or driver cause. Do not treat any candidate cause as
confirmed.

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:DEFERRED:END -->

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

**This entry is NOT the in-session packet loss, and 2026-09-22 separated
them.** The loss measured under real game load on the production path was
traced to the encoder's per-frame burst and fixed by a 90,000-byte frame
cap (`D-BASE-P6`, `P6a`, `S3`) — see `docs/KNOWN_ISSUES.md` Entry 2. **That
closes nothing here.** This entry's signature is **same-stamp
duplication and bidirectional transformation without game load**, and
`late_or_reordered_packets` is **0 across 11 M packets** in every capped
and uncapped session on record, so the two faults do not even share a
symptom. The synthetic suite has still never been replayed on the post-`B2`
topology.

**Reopen condition 1 was exercised once, 2026-09-21 (`D-BASE-B2`), and the
entry stays PAUSED.** Battery `B2` was the bounded measurement: no
router-side capture, nothing installed on the Opal, client telemetry only.
It moved the host off the **Windows PC** — which had been in the path for
every session on disk, a fact not known when the "representative Linux
path" wording above was written — and onto the production topology (host
wired into the Opal, onn wireless, one hop). **The burst shrank and stayed
bursty**: loss/min median 16.6 against 46.3, and 4.46 packets per
forward-gap event against 11.17, where uniform loss would give ~1.0. The
two arms **overlap**, so nothing here implicates or exonerates the Windows
PC, and nothing speaks to the Opal itself — the alternate-AP arm was not
run. Same-stamp duplication was not re-measured on the wire. Record:
`../evidence/B2_HOST_ON_OPAL_2026-09-21.md`.

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

## Thermal pause on the link-drop recovery state machine

**Deferred by the user, 2026-09-21, at the same time `D-BASE-T1` was
authorized.** The idea: give the recovery state machine a thermal trigger,
so that when the onn reports a severe thermal status the host pauses the
game (the overlay reading "Cooling down…") and resumes it through the
existing stabilization gate once the status drops — the same pause and the
same gate the link-drop path already uses, on a different trigger.

**Not built, on purpose.** No threshold can be chosen before anyone knows
what the onn actually reports under load, and a pause is exactly the kind
of intervention that is worse than the problem if it fires on a number that
never mattered. `D-BASE-T1` installs the telemetry that would answer it:
`thermal_status`, `thermal_headroom` and `thermal_zones_c` in every
heartbeat, and a `thermal` block in every session report.

**As of 2026-09-22 no threshold has been reached.** `D-BASE-T1` recorded
`thermal_status` **0 (NONE) throughout**, and the onn reports **no zones
and no headroom at all** — an absence of the device, not of the search.
The host side plateaus: hottest sensor 54 -> 60 °C over ten minutes, and
`D-BASE-S3` confirmed the plateau over three hours. **Still deferred.**

**Reopen when the telemetry shows a threshold is ever reached** — that is,
when a recorded session has `thermal_status` at or above
`THERMAL_STATUS_SEVERE` (3), or headroom at or above 1.0, or a zone whose
maximum would justify one. Until a session on disk shows that, there is
nothing to trigger on and the item stays here. Thresholds are the user's
decision once the numbers exist.
