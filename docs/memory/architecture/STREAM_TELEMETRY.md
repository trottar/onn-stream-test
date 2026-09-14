---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 45ef51f9e583b459752dd5ea83163f54171e68c7
---

# Stream Telemetry Architecture

## Status

**C2.1 inventory: COMPLETE**

**C2.2 minimal contract design: COMPLETE / CHECKPOINTED / PUSHED**

No adaptive bitrate/FEC controller is implemented by this design.

## Existing production foundation

Reuse the existing Phase-B client-health path:

- schema: `privyhub_client_health_v1`;
- report cadence: 2 seconds;
- cadence reuses the existing Android 500 ms metrics tick;
- companion store retains the latest normalized report plus one delta baseline.

Already-authoritative receiver/decoder measurements include:

- receiver-delivered Mbps and FPS;
- packet/loss counters;
- FEC recovered packets and unrecoverable groups;
- late/reordered and forward-gap counters;
- decoder queue depth;
- queue overflow and stale-output drops;
- queued/rendered/dropped frame counters;
- receive-to-decode timing;
- output-gap timing;
- decoder acceleration/capability flags.

Do not create a second hot-loop sampler.

## C2 adaptation-facing contract

Add a companion-side measurement snapshot:

`privyhub_stream_telemetry_v1`

The companion owns assembly of this contract from:

1. the normalized client-health report/delta; and
2. current native-stream/FEC-relay host status.

The contract is measurement-only. It contains no bitrate decision, congestion
classifier, hold-down timer or adaptation policy.

Conceptual shape:

```text
schema: privyhub_stream_telemetry_v1
available / fresh / age_ms
profile_id
sample_interval_ms
session_elapsed_ms

receiver:
  recent_mbps
  recent_fps
  packets_delta
  lost_packets_delta
  late_or_reordered_packets_delta
  forward_gap_events_delta
  interarrival_jitter_ms
  waiting_for_idr

fec:
  recovered_packets_delta
  unrecoverable_groups_delta
  group_size

sender:
  sent_bytes_delta
  send_calls_delta
  send_errors_delta
  send_call_avg_us
  send_call_max_us

latency:
  control_round_trip_ms
  receive_to_decode_ms
  output_gap_ms

decoder:
  queue_depth
  queue_depth_delta
  queued_frames_delta
  rendered_frames_delta
  dropped_frames_delta
  queue_overflow_drops_delta
  stale_output_drops_delta
  hardware_accelerated
  vendor_codec
  low_latency_enabled
```

Exact naming may follow established Python/Kotlin style, but these semantics are
the C2.2 contract.

## Missing-signal implementation rules

### RTP inter-arrival jitter

Measure jitter at the Android RTP receive boundary.

Use an RFC-3550-style EWMA based on the difference between:

- monotonic arrival spacing; and
- 90 kHz video RTP timestamp spacing.

Rules:

- original H.264 RTP data packets only;
- do not include PHF1 parity datagrams;
- do not treat reconstructed synthetic packets as new network arrivals;
- reset estimator state on SSRC/stream resync;
- report non-negative milliseconds;
- do not convert the old Windows/test-network pathology into a hard threshold.

This is an observation metric only.

### Control-path round trip

Reuse the existing 2-second client-health HTTP POST.

Measure elapsed monotonic time around a successful POST and include the previous
successful measurement in the next report.

Name/meaning must make clear that this is **control-path round trip**, not pure
UDP/video RTT.

Rules:

- no new echo endpoint;
- no new timer;
- first sample may be unavailable;
- failed POSTs do not replace the most recent successful sample;
- Phase G may later add overlay/path-specific latency without replacing this
  core field.

### Decoder queue growth

Do not add another Android queue metric.

Derive a signed queue-depth delta on the companion from consecutive accepted
client-health reports:

`current queue_depth - previous queue_depth`

Counter deltas remain non-negative; queue-depth delta is deliberately signed.

### Sender pressure / pacing

The production FEC relay forwards immediately and has no pacing deadline.
Therefore do **not** copy diagnostic-probe `pacing_lateness` semantics into the
live stream.

Instrument the actual relay `sendto()` boundary instead:

- successful send calls;
- bytes sent (data + parity);
- send errors;
- send-call total/average duration;
- maximum send-call duration.

Use monotonic/performance timing around `sendto()` only.

This measures sender/host pressure without adding a scheduler or altering packet
timing.

## Decoder starvation

Do not add a new explicit starvation counter in the first C2 implementation.

Existing measurements are sufficient inputs for later C3 inference:

- rendered-frame delta;
- recent FPS;
- output-gap timing;
- receive-to-decode timing;
- queue depth / queue-depth delta;
- queue overflow / stale drops.

The C2 contract records measurements, not a starvation classification.

## Compatibility

`privyhub_client_health_v1` remains the receiver-report transport.

C2 may add optional backward-compatible fields to that payload:

- `video.interarrival_jitter_ms`;
- control-path round-trip data.

The companion must accept older reports where these optional fields are absent.

Do not rename the existing schema merely to add optional measurement fields.

## Privacy / remote-readiness

The telemetry contract must contain no source/request IP identity.

Do not add overlay provider, travel-router or WAN session-routing state in C2.

Phase G may extend the contract with overlay/path metadata while retaining the
Phase-C core measurements.

## C2 implementation boundary

The first C2 production patch may touch only the minimum measurement/assembly
surfaces needed for this contract.

It must not change:

- encoded video parameters;
- packet format or RTP payload type;
- FEC algorithm/group semantics;
- audio path;
- controller path;
- capture backend;
- stream ports;
- game lifecycle;
- profile selection;
- bitrate or FEC adaptation.

## C2 telemetry v1 implementation

**Status:** COMPLETE / RUNTIME VALIDATED / CHECKPOINT PENDING

The public diagnostics surface is:

`GET /diagnostics/stream-telemetry`

Runtime validation confirmed the adaptation-facing measurement contract carries
fresh receiver, FEC, sender-pressure, control-path latency and decoder
measurements while containing no adaptation-decision fields.

This closes C2 measurement infrastructure. C3 may consume these measurements,
but C2 itself does not choose bitrate, classify congestion, apply hysteresis or
change FEC.
