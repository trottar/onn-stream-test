# Diagnostic inventory and future acceptance tests

## Purpose

The transport diagnostics created during the 2026-09 investigation are intentionally separate from production streaming. Preserve them through the Linux transition. Their value is that they let a new host/network platform be tested before production audio behavior is changed.

## Current diagnostic paths

The local working tree created during the investigation should contain some or all of the following diagnostic components. The pre-push audit helper reports whether they exist and whether Git tracks them.

### Forward external UDP probe

Expected components:

- Android `UdpTransportProbeActivity`;
- `companion/diagnostics/udp_transport_probe.py`;
- `tools/run_udp_transport_probe.ps1`.

Path tested:

```text
host userspace sender
  -> host networking stack / NIC boundary
  -> network infrastructure / Wi-Fi
  -> Android kernel UDP arrival
  -> Android userspace
```

Important modes developed during the investigation include Android kernel receive timestamps, optional Android Wi-Fi low-latency lock, and Windows PktMon boundary capture.

### Android-local loopback probe

Expected components:

- Android `UdpLoopbackProbeActivity`;
- `tools/run_udp_loopback_probe.ps1`.

Path tested:

```text
Android sender -> 127.0.0.1 UDP -> Android kernel timestamp -> Android receiver
```

This bypasses the external network and is useful for distinguishing Android local scheduling/socket behavior from wireless delivery.

### Reverse UDP probe

Expected components:

- Android `UdpReverseTransportProbeActivity`;
- `companion/diagnostics/udp_reverse_transport_probe.py`;
- `tools/run_udp_reverse_transport_probe.ps1`.

Final sender design uses nonblocking `DatagramChannel` and records actual send-completion timing. Windows records receive timing; optional PktMon confirms whether duplicates/timing behavior exists before Windows userspace.

Path tested:

```text
Android sender
  -> Android Wi-Fi / network path
  -> network infrastructure
  -> Windows NIC / networking stack
  -> Windows userspace receiver
```

## Linux infrastructure acceptance suite

Run these tests before modifying production audio for the Linux phase.

### Test A — Linux -> onn, idle

- 5 ms interval;
- approximately 1000-byte UDP datagrams;
- at least 20 seconds / 4000 packets;
- sequence numbers and actual sender timestamps;
- timestamp as close to Linux NIC egress as practical;
- timestamp Android kernel receive arrival;
- deduplicate by sequence for interval analysis, but report duplicates separately.

Record:

- sender interval p50/p95/p99/max;
- kernel receive interval p50/p95/p99/max;
- count of receive intervals <2 ms;
- count of receive intervals >=20 ms;
- packet loss;
- duplicate deliveries;
- reordered packets;
- sender-clean 4-6 ms intervals transformed into <2 ms or >=20 ms arrivals.

### Test B — onn -> Linux, idle

Use the reverse probe semantics:

- Android nonblocking send completion is the primary sender boundary;
- timestamp Linux ingress as close to the NIC as practical;
- timestamp Linux userspace receive separately;
- report unique packets and duplicates independently.

### Test C — repeat under native-stream load

Only after A and B are understood, repeat while native video and controller traffic are active.

### Test D — production audio

Finally run the normal process-specific audio path. Compare production arrival statistics with the synthetic probe before changing queue/buffer policy.

## Acceptance guidance

There is no product requirement that every packet arrive exactly every 5 ms over Wi-Fi. Some jitter is expected. What should trigger renewed root-cause investigation is behavior resembling the prototype pathology:

- large systematic transformation of clean sender intervals into sub-2 ms bursts and >=20 ms gaps;
- very high duplicate UDP delivery rates;
- long arrival stalls on an otherwise idle local network;
- divergence already visible at a kernel/NIC boundary before the application receiver.

Do not make the 2026 Windows prototype's measured duplicate/jitter rates into hard universal thresholds. Establish Linux baseline data first.

## Privacy when saving diagnostics

Sanitized summaries should avoid storing or committing:

- IP addresses;
- MAC addresses;
- Wi-Fi identifiers;
- device GUIDs;
- payload/media contents;
- local usernames or absolute private paths where unnecessary.

Raw captures belong under ignored diagnostic/log directories and should not be committed by default.
