---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: e92bc42988f744191ae1321b05aaa04663222209
---

# C3.L2a E2 — the actuator's first IDR is accepted in 27 ms

## Classification

**RUNTIME VALIDATED / C3.L2a ANSWERED / IDR-WAIT HYPOTHESIS FALSIFIED**

Source: one encoder-only actuator cycle against the `C3.L2b` client, collected
with `tools/collect_game_session_diagnostics.py`. Session duration 63,719 ms,
`client_profiler_version` 0.12.2.

## The instrumentation worked

| Field | Value |
| --- | ---: |
| `slow_event_retained` | 94 |
| `slow_event_capacity` | 128 |
| `slow_event_retained_marked` | 30 |
| `slow_event_capacity_marked` | 64 |

The recent buffer did not overflow this time, and the new
`stream_discontinuities` and `first_idr_after_discontinuity` arrays are present
and populated. The `C3.L2a` E1 pass failed because the row explaining the gap
had been evicted; that condition did not recur.

## The answer

Three discontinuities were recorded, one of them the actuator cycle:

| `elapsed_ms` | type | jump packets |
| ---: | --- | ---: |
| 22,852 | sequence_resync | 133 |
| **43,443** | **ssrc_change (the actuator cycle)** | 0 |
| 48,545 | sequence_resync | 194 |

First IDR accepted after each:

| `elapsed_ms` | after | `resync_to_idr_ms` | AU complete | FEC recovered | unrecoverable group |
| ---: | --- | ---: | --- | --- | --- |
| 23,047 | resync | 195 | true | false | false |
| **43,471** | **actuator cycle** | **27** | **true** | **false** | **false** |
| 48,756 | resync | 210 | true | false | false |

**The replacement encoder's first keyframe was accepted 27 ms after the SSRC
change, complete, with no FEC repair and no unrecoverable group.** It is the
fastest of the three, by a factor of seven.

The IDR-wait hypothesis is falsified. `C3.L1R1`'s "request an immediate IDR"
lead was already premise-corrected by `C3.L2`; this closes it with measurement.
So is the damaged-first-keyframe candidate: the AU was complete and FEC did not
have to repair it.

## Where the session's real gaps came from

| `elapsed_ms` | `rx_to_decode_ms` | `feed_delay_ms` | `codec_ms` | `app_queue_depth` | `output_gap_ms` |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 23,103 | 368 | 0 | 367 | 0 | **359** |
| 48,808 | 362 | 0 | 361 | 3 | **352** |
| 55,682 | 218 | 0 | 217 | 1 | 209 |
| 56,898 | 190 | 0 | 189 | 4 | 180 |
| 63,353 | 183 | 0 | 183 | 0 | 172 |

The two largest gaps follow the two **sequence resyncs** at 22,852 and 48,545,
not the cycle at 43,443. In both, `output_gap_ms` tracks `codec_ms` to within
8 ms with feed delay at zero — decoder time on a single frame.

**Nothing registered at or near 43,443.** The actuator cycle produced no slow
event at all in a session whose worst gap was 359 ms.

Session context: `max_output_gap_ms` 359, `max_codec_ms` 367,
`max_rx_to_decode_ms` 368, rendered 3,346, dropped 62, queue-overflow drops 62,
`low_latency_enabled` **false** on `c2.realtek.video.avc.decoder`.

## What this settles, and what it does not

Settled: the Linux encoder-only actuator does not impose an IDR wait. Its
keyframe is accepted promptly and intact. The 287-318 ms figure from `C3.L1` /
`C3.L1R1` was never demonstrated to be actuator cost, and this run shows the
actuator producing no measurable gap while ordinary resyncs produce 359 and
352 ms.

Not settled: whether `video_only_restart` is acceptable for automatic in-game
adaptation. That is `C3.L2`'s decision and it stands. This is one cycle in one
session; it removes the mechanism that was assumed to make the actuator
expensive, but acceptance needs repetition and a focused gameplay observation.

Also not established: why this session recorded 530 lost packets and 38
sequence-gap AU drops against zero unrecoverable FEC groups. Transport
conditions differed from the `C3.L1R1` run. Out of scope here; noted so a later
reader does not treat the two sessions as like-for-like.

## Defect found in the C3.L2b reporting

`slow_event_retained_marked` reports 30 of 64, but the marked rows are not
emitted — the array is empty in the report. The count is kept and the contents
are dropped.

It did not block this conclusion, because `stream_discontinuities` and
`first_idr_after_discontinuity` carry what was needed. It does mean the marked
window cannot yet be inspected row by row. Recorded in `docs/KNOWN_ISSUES.md`;
not fixed here.

## Negative results

- The IDR-wait explanation, carried through `C3.L1`, `C3.L1R1` and the `C3.L2`
  registration of `C3.L2a`, is wrong. Three records reasoned from a session
  maximum that belonged to a different event.
- The damaged-first-keyframe candidate is also wrong for this cycle.
- `C3.L2b` shipped with a reporting defect that its own first use exposed.

## Privacy

No network addresses appear in this record. The bundle redacts IPv4 on ingest.
