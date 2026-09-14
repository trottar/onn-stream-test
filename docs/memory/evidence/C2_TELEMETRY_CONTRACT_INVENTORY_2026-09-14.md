---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 45ef51f9e583b459752dd5ea83163f54171e68c7
---

# C2 Telemetry Contract Inventory

**Result:** `C2_INVENTORY_COMPLETE_EXISTING_FOUNDATION_WITH_GAPS`

**Classification:** SOURCE/CONTRACT INVENTORY — NO RUNTIME BEHAVIOR CHANGE

The probe was run against synchronized local/origin checkpoint:

`45ef51f9e583b459752dd5ea83163f54171e68c7`

## Existing foundation

Confirmed present:

- 2-second client-health cadence from the existing metrics loop;
- companion feedback endpoint/store;
- receiver-delivered Mbps;
- packet-loss counters;
- FEC recovered/unrecoverable counters;
- decoder queue snapshot;
- stale-output drops;
- rendered continuity/FPS;
- receive-to-decode and output-gap timing.

## Requirement classification

- delivered bitrate/goodput — **PRESENT_RECEIVER_SIDE**
- packet loss — **PRESENT**
- FEC recoveries/unrecoverable groups — **PRESENT**
- jitter/inter-arrival — **PARTIAL_PROXY**
- RTT/echo latency — **MISSING**
- sender pacing — **DIAGNOSTIC_ONLY**
- queue/buffer growth — **PARTIAL_SNAPSHOT**
- decoder starvation — existing measurements are sufficient as **PROXY INPUTS**;
  there is no explicit starvation counter
- stale-frame drops — **PRESENT**
- rendered-frame continuity — **PRESENT**

## Gap set before adaptive bitrate

The implementation gap is narrowed to:

- explicit inter-arrival jitter;
- scoped control-path round trip;
- production sender-pressure timing;
- signed queue-depth change.

No second telemetry loop is required.

## Design result

C2.2 adopts `privyhub_stream_telemetry_v1` as a companion-side,
measurement-only contract assembled from existing client health plus native
host/FEC-relay status.

See:

`docs/memory/architecture/STREAM_TELEMETRY.md`

No adaptive controller is part of C2.2.
