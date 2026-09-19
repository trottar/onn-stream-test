---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: e1c37768718030af7266e2d37dad5473166e2987
---

# C3.L2a E1 — first-IDR evidence pass over the C3.L1R1 decoder report

## Classification

**EVIDENCE PASS COMPLETE / QUESTION NOT ANSWERED / INSTRUMENTATION DEFECT FOUND**

No new runtime run. This record analyses evidence already collected during the
`C3.L1R1` session, via
`python3 tools/collect_game_session_diagnostics.py --root <repo>`.

## Source identity

The bundle's decoder section is the `C3.L1R1` session. Every cross-check matches
`evidence/C3_L1R1_LINUX_ACTUATOR_RUNTIME_2026-09-18.md`: `duration_ms` 64,842;
`packets_dropped_waiting_for_idr` 123; `max_resync_to_idr_ms` 191;
`max_output_gap_ms` 287; rendered 3,631; dropped 27; audio packets 12,873;
audio underruns 110; controller packets 27,980.

Profile as reported by the client: `encoder_gop_frames` 15,
`encoder_bitrate_kbps` 7000, `fec_group_size` 8, `capture_backend`
`x11grab_window`, `host_metadata_complete` true.

## The question could not be answered, and the reason is a measurement defect

`C3.L2a` asks why the receiver's first accepted IDR is late after an
encoder-only cycle. Answering it needs the per-event row for the 287 ms output
gap.

That row does not exist any more.

| Field | Value |
| --- | ---: |
| `slow_event_retained` | 128 |
| `slow_event_capacity` | 128 |
| earliest retained `elapsed_ms` | 35,421 |
| latest retained `elapsed_ms` | 64,813 |

The slow-event list is a fixed-capacity ring. It is full, and it retains only
the last ~29.4 s of a 64.8 s session. `max_output_gap_ms` is a cumulative
maximum, so the event it names has no surviving row, and the largest retained
`output_gap_ms` is 238 ms.

This is a measurement, not an inference: the report states its own retention and
capacity.

**Consequence:** every session that produces more than 128 slow events after an
actuator cycle discards the cycle's evidence before the report is written. The
`C3.L1` and `C3.L1R1` runs could not have preserved it. Re-running the existing
probe unchanged would not preserve it either.

## What the retained window does establish

The retained rows are ordinary gameplay with no actuator activity. In them,
output gap tracks codec time almost exactly, with the frame fed immediately and
nothing queued.

| `elapsed_ms` | `rx_to_decode_ms` | `feed_delay_ms` | `codec_ms` | `codec_in_flight` | `app_queue_depth` | `output_gap_ms` |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 59,237 | 248 | 0 | 247 | 1 | 0 | **238** |
| 38,399 | 212 | 0 | 211 | 1 | 0 | **200** |
| 63,088 | 144 | 1 | 142 | 1 | 0 | 133 |
| 43,901 | 132 | 0 | 131 | 2 | 1 | 123 |
| 43,074 | 129 | 1 | 127 | 2 | 0 | 119 |
| 48,544 | 133 | 3 | 130 | 1 | 0 | 119 |

Feed delay at or near zero, one or two frames in flight and an empty app queue
mean the client was not waiting for packets and was not backed up. The time was
spent inside the decoder on a single frame.

Session-level corroboration, from the same report:

| Field | Value |
| --- | ---: |
| `spike_20_ms` | 2,696 |
| `spike_50_ms` | 285 |
| `spike_80_ms` | 80 |
| `spike_250_ms` | 2 |
| `max_codec_ms` | 297 |
| `max_rx_to_decode_ms` | 298 |
| `stale_output_drops` | 184 |
| `queue_overflow_drops` | 27 |
| `max_queue_depth` | 4 |
| `codec_name` | `c2.realtek.video.avc.decoder` |
| `hardware_accelerated` | true |
| `low_latency_enabled` | **false** |

2,696 spikes at or above 20 ms against 3,847 queued frames, on a stream whose
frame interval is 16.7 ms, is a decoder that is routinely slower than real time
on this device.

## The consequence for the C3.L2 classification

Steady-state play in the same session, with no actuator involved, produced
output gaps of 238 ms and 200 ms. The actuator cycle's figure is 287 ms.

Two readings are open and this evidence cannot separate them:

1. the cycle caused a 287 ms gap, of which only the excess over the session's own
   worst-case decoder spike — roughly 50 ms — is attributable to the actuator;
2. the 287 ms maximum was itself a decoder spike, occurring anywhere in the
   session including before the retained window, and the actuator's contribution
   is smaller still or not separately visible.

Either way, the premise that the interruption is a large, distinctly
actuator-shaped artifact is **not supported by this evidence**. The `C3.L2`
decision does not change: it was made conservatively, it authorizes the actuator
for every non-automatic use, and the only thing it withholds is automatic
in-game adaptation. But the reason to revisit it is now stronger than the reason
recorded in `C3.L2` itself.

Do not restate 287-318 ms as "the cost of the actuator" without this
qualification.

## Other findings in the same report

- **`max_frames_between_idr` is 27, against `encoder_gop_frames` 15.** Keyframe
  spacing is not uniform, so the worst-case wait for a keyframe is ~450 ms at
  60 fps, not the 250 ms the "one GOP" reasoning assumed. Any argument built on
  a 250 ms GOP interval understates its own worst case.
- **The damaged-first-keyframe mechanism is real in this session.**
  `fec_recovered_idr_packets` 1, `fec_unrecoverable_groups` 2,
  `sequence_gap_au_drops` 4, `incomplete_au_drops` 3, `fec_gap_holds` 6,
  `fec_hold_timeouts` 4, `max_forward_gap_packets` 13, `lost_packets` 33. FEC
  repaired one IDR packet. None of this can be tied to the cycle without the
  evicted row.
- **The encoder swap is not visible in the host log.** The bundle's native video
  section is the last 500 lines of `logs/games/native_video_alpha.log`. It shows
  three FFmpeg runs, each with its own start banner and a frame counter starting
  at 31. The final run counts continuously to frame 3,242 / 54.03 s with no
  reset and its x11grab input start, 1789756804.855, matches the decoder
  session's own start within ~2 ms. Either the probe's replacement encoder does
  not write to this log, or the swap fell outside the retained tail. This is an
  instrumentation question to settle from probe source, not a claim that no swap
  occurred — the receiver recorded exactly one SSRC change.
- **Audio is doing a large amount of concealment.** `prolonged_starvation_events`
  102, `concealed_underruns` 929, `stale_drops` 872, `smooth_latency_trims` 872,
  `crossfaded_packets` 452, against only 7 lost packets and 0 write errors. Not
  C3 scope, and not a transport-loss problem; recorded because it is a plausible
  part of the pre-existing perceived streaming quality.

## Negative results

- The `C3.L2a` question is **not answered**. The evidence needed existed during
  the run and was discarded by a ring buffer before the report was written.
- Re-running `tools/probe_c3_actuator_continuity.py` unchanged would not answer
  it either. That is why no re-run is requested.
- No production defect was found. The ring buffer is diagnostic-only.
- The `C3.L1` / `C3.L1R1` runs remain valid for what they claimed: lifecycle
  preservation, reproduced twice, and a bounded worst-case decoder output gap.
  What they cannot support is attribution of that gap to the actuator.

## What must change before the question can be answered

The decoder session report must retain the cycle. Minimum:

1. preserve slow events around a marked window, or raise and segment the ring so
   that early events are not evicted by later ordinary spikes;
2. anchor the SSRC change and the sequence resyncs in `elapsed_ms`, so a reader
   can locate the cycle in the timeline at all;
3. report per-event IDR context for the first accepted IDR after an SSRC change:
   whether its access unit was complete and whether its FEC group was
   recoverable.

That is diagnostic-only client work: `client_profiler_version` is 0.12.2 and the
change is to the report, not to decoder configuration, resolution, frame rate or
any streaming constant. It requires a real Gradle build and its own patch.

`low_latency_enabled` being false on this codec is a separate candidate with its
own hypothesis. It is **not authorized** here and must not be folded into a
diagnostics patch: it changes decoder configuration, which is production client
behavior.

## Privacy

The bundle redacts IPv4 addresses to `<IP_REDACTED>` on ingest. No network
addresses are recorded here.
