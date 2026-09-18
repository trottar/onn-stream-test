---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 310596dd0cc3ff22f3fe46e2eb025d052da90ec0
---

# C1/C2 Linux revalidation

## Classification

**RUNTIME VALIDATED / LINUX STREAMING BASELINE ESTABLISHED**

This record supersedes the 2026-09-18 checkpoint stub, which asserted `PASS`
without preserving any measurement. The measurements below are the authoritative
Linux known-good baseline that C3 reasons against.

## C1 — Linux profile and backend validation

Result: **PASS**

Validated surfaces:

- profile `native_game_720p60_reference` applied on the Linux backend;
- capture backend `x11grab_window`;
- encoder backend `h264_vaapi`;
- transport `rtp_udp_xor_fec`;
- Linux fail-closed render-node behavior.

Fail-closed behavior confirmed: `_linux_vaapi_device()` returns `None` unless
exactly one accessible DRM render node exists, and the start path refuses rather
than guessing when GPU selection is ambiguous. Missing `DISPLAY` or missing
`xdotool` also refuse before modification.

## C2 — Stream telemetry runtime validation

Result: **PASS**

Validated: telemetry schema, freshness, receiver metrics, sender metrics,
jitter, queue depth, decoder timing, control round trip, and the absence of
adaptation fields.

### Representative Linux baseline

| Measurement | Value |
| --- | ---: |
| receiver bitrate | ~5.94 Mbps |
| receiver FPS | ~59.45 |
| interarrival jitter | 0.337 ms |
| packet loss | 0 |
| FEC recovered packets | 0 |
| control round trip | 91 ms |
| receive-to-decode | 31 ms |
| decoder queue depth | 0 |

### Reading notes

Receiver delivered bitrate of ~5.94 Mbps against a 7000 kbps encoder target is
expected and is not evidence of degradation. The target is a ceiling for a
low-motion emulator scene, not a floor, and the measurement is receiver-side
delivered goodput.

Zero loss with zero FEC recovery means the 8+1 XOR parity had nothing to repair
during the sample. It does not establish FEC correctness under loss; that
remains covered by earlier FEC evidence and by future adverse-condition work.

Control round trip of 91 ms is the control-path HTTP POST measurement defined in
`architecture/STREAM_TELEMETRY.md`. It is explicitly **not** video RTT and must
not be compared against the 31 ms receive-to-decode figure as if both measured
the same path.

Queue depth 0 with FPS near 60 and zero drops is the clean steady state. A C3
controller must reason from fresh interval deltas in this shape rather than from
cumulative whole-session totals.

## Failures and negative results

No failures were recorded during this revalidation.

Recording that explicitly matters: the absence of a failure section in the
superseded stub made it impossible to tell whether the run was clean or whether
failures had simply not been written down.

## Known gap discovered after this validation

The C3.L0 source audit found that `_host_telemetry.start()` is never called on
the Linux start path. Sender-side host resource telemetry is therefore inactive
on Linux even though `status()` still publishes a `host_telemetry` section.

This does not invalidate the C2 result above. The C2 contract's sender metrics
come from the FEC relay `sendto()` boundary, which does run on Linux. The gap is
recorded in `docs/KNOWN_ISSUES.md` and is a Phase E prerequisite.

## Disposition

C1 and C2 are complete on Linux. Phase C advances to C3.

The Windows 5500/6000/7000 bitrate ladder is **not** carried forward as a Linux
constant. See `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`.

## Privacy

No network addresses are recorded here.
