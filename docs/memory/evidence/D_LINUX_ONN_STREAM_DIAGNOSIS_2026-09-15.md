---
memory_schema: 1
as_of: 2026-09-15
---

# Linux/onn Integrated Stream Diagnosis — 2026-09-15

## Classification

**ACTIVE / DEVELOPMENT DIAGNOSIS**

The first integrated Linux/onn game E2E proves the Linux emulator, save,
controller-preflight, exact-window capture and VAAPI encode path can run through
the normal product launch. The remaining stream failure is transport stability,
plus a separate Android auto-open compatibility bug.

## Integrated-path evidence

A real PS1 session:

- launched under the Linux platform-selected RetroArch runtime;
- loaded an existing save;
- exposed the managed X11 window;
- was selected by the Linux native capture backend;
- encoded with VAAPI near 60 fps;
- reached NativeStreamActivity when entered manually.

The Android handoff initially reported:

`Game ready, stream not opened`

with:

`The managed RetroArch window was not confirmed by the host-coexistence preflight.`

Source inspection shows MainActivity still gates automatic handoff on
`host_window_policy.window_found`, which is a Windows-only coexistence preflight.
Linux native-stream startup performs its own exact managed-window discovery
later and succeeded. Treat these as separate seams.

## Receiver symptoms

Fresh Android decoder telemetry from the first integrated attempt showed:

- substantial missing video packets and unrecoverable FEC groups;
- low recent delivered FPS;
- hardware/vendor H.264 decoder active;
- stale-output drops and long output/decode gaps;
- heavy audio loss/starvation/concealment.

The stabilization GUI correctly remained active because its clean-frame/fps/gap
requirements were not satisfied.

## Linux sender/socket evidence

Companion stream telemetry observed:

- zero explicit video send errors in the sampled interval;
- video send-call average in the millisecond range;
- a video send-call maximum near 785 ms;
- control-path RTT around 1.5 s in the same degraded period.

Linux audio timing from the same architecture showed:

- SCHED_RR priority 1 successfully applied;
- thousands of nonblocking UDP send failures in degraded integrated runs;
- cadence inflation and maximum gaps from hundreds of milliseconds to seconds.

Short before/after `/proc/net/snmp` probes repeatedly showed thousands of
additional `Udp:SndbufErrors` and many additional `Udp:RcvbufErrors`. Interface
`tx_errors` and `tx_dropped` did not increase during the measured runs.

The video path uses FFmpeg -> loopback UDP -> FEC relay -> onn. When outbound
relay progress stalls, loopback receive overflow is consistent with the large
`RcvbufErrors` increase.

## Falsified primary hypotheses

### Small socket ceilings

Default Linux `rmem_max`/`wmem_max` capped the relay's requested 2 MiB buffers.
A diagnostic raised both kernel ceilings to 4 MiB and confirmed effective
application buffers of 4,194,304 bytes as reported by Linux. The integrated run
did not improve; send failures/cadence worsened and receive errors remained
large. Do not adopt larger socket buffers as the root-cause fix.

### USB runtime autosuspend / USB speed

The Wi-Fi device is:

- Realtek `0bda:b812`;
- RTL8822BU;
- driver `rtw_8822bu`;
- USB speed 5000 Mb/s;
- USB runtime `power/control=on`;
- runtime active;
- zero accumulated runtime-suspended time.

USB autosuspend and a USB-2 link are not supported as primary causes.

### rtw88 deep LPS

`disable_lps_deep=Y` was applied temporarily and restored. UDP error deltas and
audio send failures remained materially unchanged. Deep LPS is not the primary
cause.

### Ordinary Wi-Fi powersave

Kernel logs repeatedly contain:

`firmware failed to leave lps state`

and one rtw register read timeout. The first attempted live NetworkManager
device reapply failed and therefore was not a valid test.

A second profile-level test set
`802-11-wireless.powersave=2`, reconnected the same profile and confirmed the
profile reported powersave disabled. During that test, no LPS/register failure
was logged. Nevertheless, UDP send/receive-buffer errors and audio send failures
remained severe. This proves ordinary LPS is a genuine RTL8822BU/rtw88 issue but
not the primary cause of the integrated stream collapse.

The original NetworkManager powersave value was restored after the test.

## Next discriminator

Run the repository's preserved Linux acceptance **Test A — Linux -> onn, idle**:

- 5 ms interval;
- approximately 1000-byte synthetic UDP datagrams;
- at least 20 seconds;
- nonblocking host sender timing;
- Android kernel receive timestamps;
- outside RetroArch, MediaCodec and production native streaming.

The first Linux shell wrapper attempt failed before sending because local onn
address discovery returned `ONN_ADDRESS_DISCOVERY_FAILED`. Correct that wrapper
without printing, persisting to shareable evidence, or asking the user for an IP.

If idle synthetic traffic already produces host would-block/SndbufErrors, the
problem is independent of production game streaming. If idle synthetic is
clean, proceed to the documented under-native-stream-load repeat.

## Separate acceptance item

Beetle PSX HW reported missing `scph5501.bin`. The core still launched and the
save loaded, so this is not the current transport cause. Restore the BIOS before
final PS1 acceptance.

<!-- PRIVYHUB_D079R1_MEMORY_CHECKPOINT_LINUX_IDLE_UDP_TEST_A_2026_09_15:EVIDENCE:BEGIN -->
## Standalone idle Test A result

Session:

`logs/transport_probe/linux_idle_20260915_094026`

Configuration:

- direction: Linux -> onn;
- idle system / no game;
- 20 s;
- 5 ms packet cadence;
- ~1000-byte datagrams;
- nonblocking Linux sender;
- Android kernel receive timestamps.

Measurements:

| Metric | Result |
| --- | ---: |
| Planned host sends | 4000 |
| Successful host sends | 3993 |
| Host would-block | 7 |
| Host send p95 | ~5.015 ms |
| Host send max | ~30.008 ms |
| Host send-call max | ~128.785 us |
| Android unique arrivals | 3993 |
| Missing successful unique sends | 0 |
| Android duplicate arrivals | **2626** |
| Same-stamp duplicates | **2626** |
| Conflicting-stamp duplicates | 0 |
| Android kernel p95 | ~18.357 ms |
| Android kernel max | ~792.302 ms |
| Host 4-6 ms -> kernel <2 ms | 2116 |
| Host 4-6 ms -> kernel >=20 ms | 190 |
| `SndbufErrors` delta | +7 |
| `RcvbufErrors` delta | +0 |

The application-minus-kernel interval delta remained comparatively small,
confirming the large timing transformation was already present at Android's
kernel receive boundary.

Conclusion:

The representative Linux path reproduces the previously deferred transport
pathology while idle. The large duplicate count and kernel-level burst/gap
transformation cannot be attributed to RetroArch, native capture/encode,
production audio, MediaCodec, or Android application scheduling.

The sender did have seven would-block attempts, but every successfully sent
unique packet arrived. Those seven events therefore do not explain the 2626
duplicate deliveries or the large kernel timing distortion.

<!-- PRIVYHUB_D079R1_MEMORY_CHECKPOINT_LINUX_IDLE_UDP_TEST_A_2026_09_15:EVIDENCE:END -->

<!-- PRIVYHUB_D079R2_MEMORY_CHECKPOINT_LINUX_REVERSE_IDLE_UDP_TEST_B_2026_09_15:EVIDENCE:BEGIN -->
## Standalone idle Test B result

Session:

`logs/transport_reverse/linux_reverse_idle_20260915_094554`

Configuration:

- direction: onn -> Linux;
- idle system / no game;
- 20 s Android sender;
- 5 ms target cadence;
- 4000 planned ~1000-byte datagrams;
- Android nonblocking DatagramChannel;
- Linux UDP receiver.

Measurements:

| Metric | Result |
| --- | ---: |
| Android sender attempts | 4000 |
| Android successful sends | 4000 |
| Linux unique arrivals | 3894 |
| Missing unique packets | 106 |
| Linux duplicates | **476** |
| Same-stamp duplicates | **476** |
| Android send p95 | ~6.275 ms |
| Android send max | ~29.424 ms |
| Linux receive p95 | ~18.143 ms |
| Linux receive max | ~173.722 ms |
| Sender 4-6 ms -> Linux <2 ms | 1312 |
| Sender 4-6 ms -> Linux >=20 ms | 126 |
| `SndbufErrors` delta | +0 |
| `RcvbufErrors` delta | +120 |

Conclusion:

The idle transport pathology is bidirectional in the representative environment.
This reverse result cannot be attributed to the Linux production sender or
Linux `SndbufErrors` because Android is the sender and Linux recorded zero
additional send-buffer errors.

Taken with Test A, the shared unresolved region is the home network/AP/routing
path and endpoint radio/driver internals. Router-side boundary capture is the
next useful localization step.

<!-- PRIVYHUB_D079R2_MEMORY_CHECKPOINT_LINUX_REVERSE_IDLE_UDP_TEST_B_2026_09_15:EVIDENCE:END -->

<!-- PRIVYHUB_D080_OPAL_DUAL_BOUNDARY_PROBE_01_2026_09_15:EVIDENCE:BEGIN -->
## Opal package and radio mapping

Measured:

- `opkg_update=SUCCESS`;
- `package_candidate=tcpdump-mini`;
- `package_candidate=tcpdump`;
- package lists before/after restore: 0 / 0;
- Linux radio: `wlan0`;
- onn radio: `wlan1`.

This enables dual-boundary UTP1 capture around the Opal bridge/radio path.

<!-- PRIVYHUB_D080_OPAL_DUAL_BOUNDARY_PROBE_01_2026_09_15:EVIDENCE:END -->

<!-- PRIVYHUB_D080R1_OPAL_DUAL_BOUNDARY_ANALYZER_FAIL_CLOSED_2026_09_15:EVIDENCE:BEGIN -->
## D080 first runtime result — invalid router classification

Session:
`logs/transport_probe/opal_dual_boundary_20260915_102045`

Valid endpoint facts:

- host successful sends: 2971;
- Android unique arrivals: 2971;
- Android duplicates: 5291;
- Android missing successful unique sends: 0.

Invalid router inference:

- Linux-facing router matched UTP1: 0;
- onn-facing router matched UTP1: 0;
- prior classifier output:
  `ROUTER_BOUNDARIES_CLEAN_DUPLICATION_DOWNSTREAM_OF_ONN_FACING_BOUNDARY`.

Because neither router boundary actually observed UTP1 traffic, that
classification is unsupported and explicitly withdrawn.

<!-- PRIVYHUB_D080R1_OPAL_DUAL_BOUNDARY_ANALYZER_FAIL_CLOSED_2026_09_15:EVIDENCE:END -->

<!-- PRIVYHUB_D080R2_MEMORY_CHECKPOINT_EMPTY_OPAL_PCAPS_2026_09_15:EVIDENCE:BEGIN -->
## D080R1 corrected PCAP observability result

Session:
`logs/transport_probe/opal_dual_boundary_20260915_102045`

Router capture facts:

| Boundary | PCAP bytes | Records | Linktype | UTP1 matches |
| --- | ---: | ---: | ---: | ---: |
| Linux-facing radio | 24 | 0 | 1 (Ethernet) | 0 |
| onn-facing radio | 24 | 0 | 1 (Ethernet) | 0 |

Endpoint facts from the same run:

- host successful sends: 2971;
- Android unique arrivals: 2971;
- Android duplicates: 5291;
- Android missing successful unique sends: 0.

Conclusion:

The per-radio Opal tcpdump/libpcap boundaries were blind to the active bridged
traffic in this run. The result does not localize duplicate generation.

<!-- PRIVYHUB_D080R2_MEMORY_CHECKPOINT_EMPTY_OPAL_PCAPS_2026_09_15:EVIDENCE:END -->

<!-- PRIVYHUB_D081_OPAL_ACCELERATION_OFF_DUAL_BOUNDARY_PROBE_2026_09_15:EVIDENCE:BEGIN -->
## Opal acceleration state before controlled experiment

Measured: `flow_offloading=1`, `flow_offloading_hw=1`, `sfhnat` loaded,
`cls_flow` loaded. This follows the D080R1 result where both radio PCAPs were
24-byte header-only files during active endpoint traffic.

<!-- PRIVYHUB_D081_OPAL_ACCELERATION_OFF_DUAL_BOUNDARY_PROBE_2026_09_15:EVIDENCE:END -->

<!-- PRIVYHUB_D081R1_MEMORY_CHECKPOINT_ACCELERATION_OFF_FALSIFIED_2026_09_15:EVIDENCE:BEGIN -->
## D081 acceleration-off runtime evidence

Session:
`logs/transport_probe/opal_dual_boundary_20260915_135211`

Test state:
- flow offloading = 0;
- hardware flow offloading = 0;
- `sfhnat` module = loaded.

Endpoint result:
- host successful sends = 3131;
- Android unique arrivals = 2944;
- Android duplicates = 5224;
- Android missing successful unique sends = 187.

Router observation:
- Linux-facing PCAP = 24 bytes / 0 records;
- onn-facing PCAP = 24 bytes / 0 records.

Restore:
- flow offloading = 1;
- hardware flow offloading = 1;
- restore verified successfully.

Conclusion:
Disabling the exposed flow-offload flags neither repaired the UDP path nor made
the per-radio Linux capture boundaries visible.

<!-- PRIVYHUB_D081R1_MEMORY_CHECKPOINT_ACCELERATION_OFF_FALSIFIED_2026_09_15:EVIDENCE:END -->

<!-- PRIVYHUB_D081R2_MEMORY_CHECKPOINT_SIFLOWER_INVENTORY_2026_09_15:EVIDENCE:BEGIN -->
## Siflower vendor module inventory

Valid read-only observations:

- `sf16a18_hb_fmac` loaded;
- `sf16a18_lb_fmac` loaded;
- `sf16a18_rf` loaded;
- `sf_eswitch` loaded;
- `sfax8_factory_read` loaded;
- `sfax8_netlink` loaded;
- `sfhnat` loaded;
- `/sys/module/sfhnat/parameters` has no exposed parameters;
- `/sys/module/sfhnat/drivers/platform:sf_hnat` exists;
- `bridge` command unavailable.

Invalid evidence:
the `siflower_packages` subsection failed with
`awk: Unexpected end of string` and must not be interpreted.

<!-- PRIVYHUB_D081R2_MEMORY_CHECKPOINT_SIFLOWER_INVENTORY_2026_09_15:EVIDENCE:END -->

<!-- PRIVYHUB_D082_OPAL_BRIDGE_BOUNDARY_PROBE_2026_09_15:EVIDENCE:BEGIN -->
## Siflower module ownership

Measured package/module mapping:

- `sfhnat.ko` -> `kmod-sf_hnat 4.14.90-1`;
- `sf_eswitch.ko` -> `kmod-sf_eswitch 4.14.90-1`;
- `sfax8_netlink.ko` -> `kmod-sf_netlink 4.14.90-1`;
- `sf16a18_rf.ko` -> `kmod-sf_smac 4.14.90-1`;
- `sfax8_factory_read.ko` -> `kmod-sfax8-factory-read 4.14.90-0`.

FMAC module files were not found by normal module lookup. RF/factory modules
have holders in the Wi-Fi stack.

This supports using `br-lan` as the next safe observation point instead of
unloading vendor wireless modules.

<!-- PRIVYHUB_D082_OPAL_BRIDGE_BOUNDARY_PROBE_2026_09_15:EVIDENCE:END -->

<!-- PRIVYHUB_D083_OPAL_NETDEV_COUNTER_PROBE_2026_09_15:EVIDENCE:BEGIN -->
## D082 bridge-boundary runtime evidence

Session:
`logs/transport_probe/opal_bridge_20260915_141216`

Measured:
- host successful sends = 3661;
- `br-lan` PCAP bytes = 24;
- `br-lan` PCAP records = 0;
- matched UTP1 = 0;
- Android unique = 3661;
- Android duplicates = 2371;
- Android missing successful unique = 0;
- classification = `BRIDGE_CAPTURE_EMPTY`.

Conclusion:
the ordinary Linux bridge-master AF_PACKET observation point is blind to this
active WLAN-to-WLAN traffic, matching earlier per-radio capture blindness.

<!-- PRIVYHUB_D083_OPAL_NETDEV_COUNTER_PROBE_2026_09_15:EVIDENCE:END -->

<!-- PRIVYHUB_D083R1_NETDEV_SAMPLER_LIFETIME_FIX_2026_09_15:EVIDENCE:BEGIN -->
## D083 first attempt — invalid counter evidence

Runtime facts:
- host sender: 3780 / 4000 successful sends;
- counter setup reported OK;
- retrieved CSV: fewer than two rows;
- analyzer raised `ValueError: counter sample file has fewer than two rows`;
- wrapper printed `d083_probe_exit_code=0`.

The zero exit was a diagnostic-runner bug, not successful analysis. No netdev
counter conclusion is valid from this run.

<!-- PRIVYHUB_D083R1_NETDEV_SAMPLER_LIFETIME_FIX_2026_09_15:EVIDENCE:END -->

<!-- PRIVYHUB_D083_CLOSEOUT_INVALID_DIAGNOSTICS_2026_09_15:EVIDENCE:BEGIN -->
## D083/D083R1 — invalid diagnostics

### D083

Observed:
- host sender = 3780 / 4000 successful sends;
- counter retrieval yielded fewer than two rows;
- analyzer raised `ValueError: counter sample file has fewer than two rows`;
- runner printed exit 0.

Classification:
**INVALID DIAGNOSTIC — no netdev-counter conclusion.**

### D083R1

Observed:
- `counter_setup=FAILED:sampler_not_running`;
- probe exit = 1.

Follow-up capability evidence:
- `nohup_command=UNAVAILABLE`;
- `busybox_nohup=UNAVAILABLE`.

The D083R1 runner was built around `nohup`, so that launch mechanism was
unsupported on the router.

### Smoke-test classifier correction

Raw mount evidence:
`tmpfs /tmp tmpfs rw,nosuid,nodev,noatime 0 0`

The same smoke test printed `tmp_noexec=YES`.
Those statements conflict. The raw mount evidence is authoritative; the
derived `tmp_noexec=YES` result is invalid.

Direct shell control:
- `direct_shell_lines=4`;
- header plus three intended counter samples were written.

`direct_shell_rc=1` came from the smoke script's final shell status and is not
evidence that the three counter reads failed.

No networking conclusion may be derived from D083, D083R1, or this smoke test.

<!-- PRIVYHUB_D083_CLOSEOUT_INVALID_DIAGNOSTICS_2026_09_15:EVIDENCE:END -->
