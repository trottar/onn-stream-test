---
memory_schema: 1
as_of: 2026-09-15
status: paused
---

# Linux -> onn UDP Egress Investigation

## Question

Why does the first integrated Linux/onn native-game stream fail stabilization
despite healthy RetroArch launch, exact X11 capture and near-60-fps VAAPI encode?

## Current answer

The failure is reproducibly associated with Linux UDP socket/network pressure:
large `SndbufErrors` and `RcvbufErrors`, video send-call stalls, and thousands of
failed sends from the independent nonblocking RT audio sender. The exact
subsystem below the socket API is not yet isolated.

## Ruled out as primary cause

- RetroArch launch/save path;
- Linux exact-window discovery;
- VAAPI encode throughput;
- Android software-decoder fallback;
- small default socket maxima;
- USB 2-speed limitation;
- USB runtime autosuspend;
- rtw88 deep LPS;
- ordinary mac80211/NetworkManager powersave.

Ordinary LPS remains a real secondary driver defect because disabling Wi-Fi
powersave suppressed the kernel's repeated LPS-exit warnings, but the transport
failure persisted.

## Current host

Representative Wi-Fi adapter:

- Realtek RTL8822BU, USB VID:PID `0bda:b812`;
- `rtw_8822bu`;
- USB SuperSpeed 5000 Mb/s;
- USB runtime autosuspend disabled.

Kernel has emitted repeated `firmware failed to leave lps state` and one rtw
register access timeout.

## Next probe

Use the preserved standalone UDP transport laboratory for
**Linux -> onn, idle** before changing production streaming.

Requirements:

- 5 ms cadence;
- ~1000-byte datagrams;
- >=20 seconds;
- nonblocking Linux sender timing;
- Android kernel arrival timestamps;
- no RetroArch/MediaCodec/native-stream load;
- no IP printed or requested.

The first Linux wrapper attempt stopped at local address discovery with
`ONN_ADDRESS_DISCOVERY_FAILED`; repair only that diagnostic wrapper seam first.

## Deferred production changes

Do not yet change:

- bitrate;
- FEC;
- Android stabilization thresholds;
- decoder policy;
- production audio queueing;
- production video relay semantics.

Also track the Android auto-open gate as a separate confirmed compatibility bug:
`host_window_policy.window_found` is Windows-only and must not prevent Linux
native-stream handoff when the Linux backend is authoritative.

<!-- PRIVYHUB_D079R1_MEMORY_CHECKPOINT_LINUX_IDLE_UDP_TEST_A_2026_09_15:INVESTIGATION:BEGIN -->
## 2026-09-15 Test A — resume criterion met

The preserved Linux -> onn idle synthetic probe reproduced the same class of
external-path pathology that caused the 2026-09-07 Windows investigation to be
deferred pending Linux migration.

Key result:

- Linux sender clean at ~5 ms;
- zero missing successful unique packets;
- Android kernel strongly bursty/gapped;
- **2626 same-sender-stamp duplicates on 3993 unique packets**;
- only 7 Linux send-buffer errors and zero receive-buffer errors.

This means the production stream's thousands of socket errors are not required
for the underlying network behavior. Load magnifies the problem, but the base
path is already abnormal when idle.

Do not treat duplicate delivery as a normal wireless property. As in the older
investigation, without a lower-boundary capture the exact duplicating component
is not yet identified.

The old low-latency Android Wi-Fi lock has already been tested against the
forward-path pathology and did not materially improve it. Do not reopen that
resolved experiment without new evidence.

### Next narrow hypothesis

The representative environment may reproduce the pathology bidirectionally, as
the older Windows prototype did.

**Targeted probe:** Test B, onn -> Linux idle:

- Android nonblocking DatagramChannel sender;
- 5 ms cadence;
- Linux UDP receiver;
- compare Android send-completion intervals with Linux receive intervals;
- count same-stamp duplicates and unique loss;
- no game/native-stream load.

If reverse traffic is also strongly distorted/duplicated, the shared unresolved
region remains network infrastructure + endpoint radio/driver interactions
rather than a Linux-only forward sender implementation.

<!-- PRIVYHUB_D079R1_MEMORY_CHECKPOINT_LINUX_IDLE_UDP_TEST_A_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D079R2_MEMORY_CHECKPOINT_LINUX_REVERSE_IDLE_UDP_TEST_B_2026_09_15:INVESTIGATION:BEGIN -->
## 2026-09-15 Test B — bidirectional reproduction

The second deferred resume criterion is now met.

Reverse idle traffic produced:

- 4000/4000 Android successful sends;
- 3894 unique Linux arrivals;
- 106 unique losses;
- 476 same-stamp duplicate arrivals;
- strong sender-clean -> receive burst/gap transformation;
- zero Linux sender-buffer errors during the reverse run.

The current representative path therefore reproduces the old problem in both
directions. A Linux-only sender implementation cannot explain the result.

### Active boundary

Shared unresolved region:

- home Opal routing/bridging/AP/offload/firmware path;
- Linux Wi-Fi driver/firmware/radio receive/transmit internals;
- onn Wi-Fi driver/firmware/radio internals;
- RF scheduling/retransmission interactions among those components.

Do not claim any one device is the cause without a lower-boundary observation.

### Next hypothesis

If packet identities/timing are clean on one side of the Opal and already
duplicated/distorted on the other, the router/AP boundary can localize which
side of the shared path introduces the anomaly.

First determine whether router-side capture is available from the Linux host
using the locally discovered default gateway, without disclosing addresses.
If available, run one direction at a time and capture only the diagnostic UDP
port at the relevant router interfaces.

<!-- PRIVYHUB_D079R2_MEMORY_CHECKPOINT_LINUX_REVERSE_IDLE_UDP_TEST_B_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D079R3_MEMORY_CHECKPOINT_OPAL_SSH_CAPABILITY_2026_09_15:INVESTIGATION:BEGIN -->
## Router capability probe

The shared-path investigation reached the router-localization stage.

Read-only Linux-side capability results:

- default gateway discovered locally;
- SSH port 22 reachable;
- local SSH client present;
- batch authentication unavailable.

This means router-boundary localization is potentially available but requires
interactive authentication. Next inspect only:

- whether `tcpdump` is installed;
- interface names needed to identify bridge/radio boundaries;
- no addresses, MACs, SSIDs, credentials, or payload content.

<!-- PRIVYHUB_D079R3_MEMORY_CHECKPOINT_OPAL_SSH_CAPABILITY_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D079R4_MEMORY_CHECKPOINT_OPAL_SSH_RSA_NEGOTIATION_2026_09_15:INVESTIGATION:BEGIN -->
## Router SSH negotiation

Router-side capture is not yet blocked by authentication. The current blocker
is earlier: the Opal offers only an `ssh-rsa` host key, which the Linux OpenSSH
client does not accept by default.

Use `HostKeyAlgorithms=+ssh-rsa` only for the local router diagnostic invocation.
If authentication then succeeds, inspect `tcpdump` and interface names and
continue to router-boundary capture.

<!-- PRIVYHUB_D079R4_MEMORY_CHECKPOINT_OPAL_SSH_RSA_NEGOTIATION_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D079R5_MEMORY_CHECKPOINT_OPAL_AUTH_CAPABILITIES_2026_09_15:INVESTIGATION:BEGIN -->
## Authenticated router capabilities

The router-localization path is viable. Authenticated root SSH is confirmed.

Available:
- `iw`;
- `br-lan`;
- `wlan0`;
- `wlan1`.

Unavailable:
- `tcpdump`.

Before adding a capture package, inspect the router's package manager/feed
state, free overlay space, bridge members, and sanitized wireless roles. This
must remain read-only. If a compatible `tcpdump-mini` package is later
installed, record it as a temporary diagnostic change and remove it after the
boundary capture unless there is a deliberate decision to retain it.

<!-- PRIVYHUB_D079R5_MEMORY_CHECKPOINT_OPAL_AUTH_CAPABILITIES_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D079R6_MEMORY_CHECKPOINT_OPAL_CAPTURE_READINESS_2026_09_15:INVESTIGATION:BEGIN -->
## Router capture-readiness result

Router boundary capture is technically plausible:

- authenticated SSH works;
- `opkg` and `libpcap` exist;
- overlay has ample free space;
- LAN bridge and both radio interfaces are visible.

`tcpdump` is absent and package lists are empty. The next probe must distinguish
"not cached" from "not available" by temporarily refreshing package indexes and
restoring the prior zero-list state. It should also identify endpoint radio
membership so the eventual capture can be limited to the correct bridge/radio
boundary.

<!-- PRIVYHUB_D079R6_MEMORY_CHECKPOINT_OPAL_CAPTURE_READINESS_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D079R7_MEMORY_CHECKPOINT_OPAL_SSH_COMMAND_TRANSPORT_2026_09_15:INVESTIGATION:BEGIN -->
## SSH invocation-shape result

The router capability investigation is not blocked by SSH authentication.

Known-good:
- quoted remote command;
- interactive password auth;
- `HostKeyAlgorithms=+ssh-rsa`.

Known-bad in this environment:
- feeding the remote diagnostic script over SSH stdin/heredoc.

Subsequent router probes should preserve the known-good quoted-command form so
transport/invocation behavior is not confused with router/network evidence.

<!-- PRIVYHUB_D079R7_MEMORY_CHECKPOINT_OPAL_SSH_COMMAND_TRANSPORT_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D080_OPAL_DUAL_BOUNDARY_PROBE_01_2026_09_15:INVESTIGATION:BEGIN -->
## D080 narrow hypothesis

The same-stamp duplicates are introduced either:

1. before/at the Linux-facing Opal radio boundary;
2. between the two Opal radio netdev boundaries;
3. after the onn-facing Opal radio boundary.

D080 measures all three possibilities with the existing forward UTP1 probe.
Do not tune production streaming until this evidence is inspected.

<!-- PRIVYHUB_D080_OPAL_DUAL_BOUNDARY_PROBE_01_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D080R1_OPAL_DUAL_BOUNDARY_ANALYZER_FAIL_CLOSED_2026_09_15:INVESTIGATION:BEGIN -->
## D080 capture-observability issue

The next hypothesis is diagnostic, not architectural:

**Either the radio PCAPs contain zero packet records, or they contain records at
a link layer/frame form where the current UTP1 payload scan does not find the
probe payload.**

Do not perform another network run until the existing PCAPs answer this.

D080R1 reports:
- total PCAP records;
- linktype;
- file bytes;
- matched UTP1 count;
and refuses localization when router UTP1 coverage is absent/insufficient.

<!-- PRIVYHUB_D080R1_OPAL_DUAL_BOUNDARY_ANALYZER_FAIL_CLOSED_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D080R2_MEMORY_CHECKPOINT_EMPTY_OPAL_PCAPS_2026_09_15:INVESTIGATION:BEGIN -->
## Next hypothesis after empty radio PCAPs

Narrow hypothesis:

The Opal may be forwarding Linux<->onn traffic through network/hardware
acceleration or another proprietary fast path that bypasses ordinary per-radio
Linux packet-capture visibility.

This hypothesis concerns **capture visibility first**, not the duplicate root
cause.

Targeted next diagnostic:

- read `firewall.@defaults[*].flow_offloading` and
  `flow_offloading_hw` if present;
- inspect sanitized acceleration-related UCI keys;
- list acceleration/fast-path kernel modules and processes/services;
- do not modify any value;
- do not expose addresses, SSIDs, MACs, or credentials.

Only after measuring current state should a reversible acceleration-off
experiment be considered.

<!-- PRIVYHUB_D080R2_MEMORY_CHECKPOINT_EMPTY_OPAL_PCAPS_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D081_OPAL_ACCELERATION_OFF_DUAL_BOUNDARY_PROBE_2026_09_15:INVESTIGATION:BEGIN -->
## D081 narrow hypothesis

Active Opal acceleration/fast-path forwarding may explain per-radio tcpdump
blindness and may contribute to UDP burst/duplicate pathology. D081 tests this
causally with one temporary 0/0 offload repeat and exact restore.

<!-- PRIVYHUB_D081_OPAL_ACCELERATION_OFF_DUAL_BOUNDARY_PROBE_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D081R1_MEMORY_CHECKPOINT_ACCELERATION_OFF_FALSIFIED_2026_09_15:INVESTIGATION:BEGIN -->
## D081 outcome and next hypothesis

Ruled out as primary cause / mitigation:
- OpenWrt `flow_offloading`;
- OpenWrt `flow_offloading_hw`.

Both were disabled together and the transport still failed severely. Per-radio
tcpdump remained completely blind.

`sfhnat` remained loaded, so the next hypothesis is that Siflower vendor
forwarding/switch/Wi-Fi code provides a separate fast path or capture-bypassing
path not controlled by those UCI settings.

Next diagnostic must be read-only:
- enumerate `sfhnat` module parameters and exposed proc/sysfs control nodes;
- identify installed Siflower HNAT/switch packages and modules;
- locate scripts/configs that reference the vendor fast path;
- inspect only sanitized acceleration-related firewall hooks/control names;
- do not unload `sfhnat`, restart wireless, or modify switch state yet.

<!-- PRIVYHUB_D081R1_MEMORY_CHECKPOINT_ACCELERATION_OFF_FALSIFIED_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D081R2_MEMORY_CHECKPOINT_SIFLOWER_INVENTORY_2026_09_15:INVESTIGATION:BEGIN -->
## Vendor fast-path source/control discovery

The UCI flow-offload flags are already falsified as the primary cause and the
loaded Siflower stack remains the active investigation.

Before modifying any vendor component, map:
- exact `.ko` path for each loaded Siflower module;
- package ownership (`opkg search`);
- module version/description/depends information (`modinfo`, when available);
- sysfs holders/dependencies.

This is a read-only architectural probe. No module unload/reload, wireless
restart, switch change, or HNAT control write is justified yet.

<!-- PRIVYHUB_D081R2_MEMORY_CHECKPOINT_SIFLOWER_INVENTORY_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D082_OPAL_BRIDGE_BOUNDARY_PROBE_2026_09_15:INVESTIGATION:BEGIN -->
## D082 narrow hypothesis

Hypothesis:
the Siflower forwarding path may bypass per-radio AF_PACKET capture while still
passing through the Linux `br-lan` master observation point.

Probe:
capture only `br-lan` during the existing Linux->onn UTP1 synthetic run.

No module or network setting changes are part of this experiment.

<!-- PRIVYHUB_D082_OPAL_BRIDGE_BOUNDARY_PROBE_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D083_OPAL_NETDEV_COUNTER_PROBE_2026_09_15:INVESTIGATION:BEGIN -->
## D083 narrow hypothesis

Hypothesis:
the Siflower vendor forwarding path may bypass AF_PACKET capture but still
update standard Linux netdev accounting for `wlan0`, `wlan1`, and/or `br-lan`.

Probe:
sample `/sys/class/net/<iface>/statistics/*` once per second across idle,
synthetic traffic, and tail periods.

Interpretation:
- strong radio counter deltas despite empty PCAPs: capture-hook bypass with
  normal/partial netdev accounting;
- little/no counter signal: forwarding likely occurs below/outside ordinary
  netdev accounting;
- bridge counters move too: bridge-master accounting exists despite AF_PACKET
  blindness.

Counters are aggregate and cannot locate duplicate packet identity.

<!-- PRIVYHUB_D083_OPAL_NETDEV_COUNTER_PROBE_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D083R1_NETDEV_SAMPLER_LIFETIME_FIX_2026_09_15:INVESTIGATION:BEGIN -->
## D083R1 diagnostic correction

Narrow hypothesis for the failed evidence collection:
the finite router sampler died when its SSH setup session ended because it was
launched as an ordinary background subshell.

D083R1 tests that hypothesis by detaching the same sampler with `nohup` and
requiring substantial sample coverage before analysis. It also fixes the
runner's false-success exit behavior.

The architectural D083 hypothesis remains unchanged until a valid counter run
is obtained.

<!-- PRIVYHUB_D083R1_NETDEV_SAMPLER_LIFETIME_FIX_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_D083_CLOSEOUT_INVALID_DIAGNOSTICS_2026_09_15:INVESTIGATION:BEGIN -->
## D083 investigation closeout

Status: **PAUSED / INVALID DIAGNOSTIC BRANCH**

D083 architectural question (whether hidden forwarding updates ordinary netdev
counters) remains unanswered.

Invalidated:
- D083 first measurement;
- D083R1 first measurement;
- `tmp_noexec=YES` smoke classifier;
- unproven statement that SSH teardown was the specific cause of the original
  D083 sampler loss.

Still valid:
- D082 and earlier endpoint/router evidence;
- all tested AF_PACKET capture points (`wlan0`, `wlan1`, `br-lan`) were
  zero-record during confirmed endpoint traffic;
- disabling exposed OpenWrt software/hardware flow-offload flags did not repair
  transport or capture visibility;
- representative Opal uses proprietary Siflower FMAC/eswitch/HNAT components.

Do not continue by default into Siflower reverse engineering. Re-entry requires
a bounded hypothesis whose result changes a product/roadmap decision.

<!-- PRIVYHUB_D083_CLOSEOUT_INVALID_DIAGNOSTICS_2026_09_15:INVESTIGATION:END -->

<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15:INVESTIGATION -->
## Current disposition after D083 closeout

**Status: PAUSED.** The representative transport pathology is established, but
the Opal/Siflower vendor-specific root-cause branch is not the default next task.
D082 is the last valid router-boundary evidence. Re-entry requires either one
bounded measurement that changes a product/roadmap decision or a different
representative network/router environment.
