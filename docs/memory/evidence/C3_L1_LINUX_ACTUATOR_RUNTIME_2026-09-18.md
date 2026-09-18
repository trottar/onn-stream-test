---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: a9885ea356de38fcda3d22637f73c4f60d6b24de
---

# C3.L1 Linux encoder-only actuator runtime evidence

## Classification

**RUNTIME EVIDENCE CAPTURED / HOST RESUME MEASUREMENT DEFECTIVE / DECODER GAP
AUTHORITATIVE / LINUX MATERIALLY BETTER THAN WINDOWS**

Probe results:

- trigger: `C3_ACTUATOR_CYCLE_TRIGGERED`, problems none;
- finalize: `C3_ACTUATOR_CONTINUITY_EVIDENCE_CAPTURED`, problems none.

The cycle completed and the session recovered. Focused gameplay observation is
**not yet supplied** and is required before `C3.L2` classification.

## Pre-cycle state

- receiver 7.379 Mbps, 59.717 fps, decoder queue depth 0;
- profile `native_game_720p60_reference` at the 7000 kbps reference.

## Host cycle measurements

| Measurement | Value |
| --- | ---: |
| `host_ffmpeg_spawn_ms` | 215.007 |
| `host_first_rtp_resume_ms` | 215.017 |
| `host_verified_ms` | 966.861 |
| FEC RTP packets delta | 654 |
| FEC send errors delta | 0 |
| audio packets delta | 193 |
| audio send errors delta | 0 |
| controller packets delta | 408 |
| controller bad packets delta | 0 |
| post-cycle samples | 4 |
| recovered mbps / fps | 7.379 / 59.717 |
| recovered waiting for IDR | False |
| recovered queue depth | 0 |
| recovered output gap | 11 ms |

## Session decoder report

| Measurement | Value |
| --- | ---: |
| session duration | 65,296 ms |
| sequence resyncs | 2 |
| SSRC changes | 1 |
| packets dropped waiting for IDR | 118 |
| resync to IDR | 24 ms |
| max resync to IDR | 241 ms |
| waiting for IDR at end | False |
| IDR frames | 256 |
| lost packets | 39 |
| FEC recovered packets | 1 |
| FEC unrecoverable groups | 1 |
| decoder rendered frames | 3,655 |
| decoder dropped frames | 19 |
| decoder queue-overflow drops | 19 |
| decoder max output gap | 318 ms |
| decoder max receive-to-decode | 327 ms |
| audio packets | 12,980 |
| audio lost packets | 4 |
| audio write errors | 0 |
| audio underruns | 115 |
| controller packets sent | 27,749 |
| controller send errors | 0 |

## Lifecycle preservation: confirmed

FEC relay, process audio, the persistent controller and the emulator session
all continued across the cycle. Zero FEC send errors, zero audio write errors,
zero controller send errors. Exactly one SSRC change, consistent with one
encoder replacement. The receiver was not waiting for an IDR at session end.

This is the `C3.L1` acceptance objective and it passed.

## Defect: `host_first_rtp_resume_ms` is not video resume time

**Do not cite 215 ms as the Linux interruption cost.**

`host_ffmpeg_spawn_ms` is 215.007 and `host_first_rtp_resume_ms` is 215.017 —
0.010 ms apart, while the probe's RTP poll sleeps 10 ms between checks. The
first poll therefore succeeded immediately.

Root cause: the probe captured its RTP baseline from the FEC status snapshot
read during precondition checks, **before** the old encoder was killed. Packets
the old encoder delivered between that read and the kill pushed the counter
above the baseline, so the very first poll after spawning the replacement was
satisfied by old-encoder packets. The reported figure is encoder spawn time
wearing the label of video resume time.

Corrected in `C3.L1R1`: the baseline is taken after the kill returns, the
residue is reported as `rtp_baseline_residual_packets`, and
`rtp_silence_after_spawn_ms` plus `encoder_down_ms` are added. A regression
test constructs a cycle where the replacement produces no video at all; the
defective probe reports success, the corrected probe raises
`replacement_rtp_did_not_resume`.

### The Windows probe shares the same pattern

`companion/diagnostics/c3_actuator_probe.py` takes its baseline from the same
pre-kill snapshot. The Windows evidence did not record `ffmpeg_spawn_ms`, so
whether its 837-953 ms figures were similarly collapsed onto spawn time cannot
be checked retrospectively.

Windows is the outgoing platform and its probe is not modified. Treat the
Windows "first RTP resume" figures as **pipeline re-establishment time**, not
as verified video-resume time, and compare them with Linux only on that basis.

## Authoritative comparison: decoder output gap

`decoder_max_output_gap_ms` is measured on the Android receiver, independently
of the host probe, and is unaffected by the baseline defect. It is the honest
upper bound on the visible interruption.

| Run | Backend | Max decoder output gap |
| --- | --- | ---: |
| D-062 same-bitrate cycle | Windows WGC + NVENC | 791 ms |
| D-070 bidirectional cycle | Windows WGC + NVENC | 1,059 ms |
| **C3.L1 same-bitrate cycle** | **Linux x11grab + VAAPI** | **318 ms** |

Against the directly comparable Windows run (D-062, same-bitrate cycle, same
decoder implementation), Linux is **2.5x better**: 318 ms against 791 ms.

This matches the topology prediction recorded by `C3.L0`: Linux replaces one
process with no pipe handoff and no capture-metadata first-frame wait, while
Windows replaces a capture bridge and an encoder and re-handshakes a pipe
between them.

318 ms is nevertheless roughly 19 frame intervals at 60 fps. It is materially
better, not negligible.

## Where the Linux gap comes from

`max_resync_to_idr_ms` is 241 ms and `packets_dropped_waiting_for_idr` is 118.
Both Windows runs recorded 0 packets dropped waiting for IDR.

GOP is 15 frames at 60 fps, so a keyframe interval is 250 ms. The 241 ms
maximum resync-to-IDR is approximately one full GOP, and it accounts for most
of the 318 ms output gap.

This is a specific, actionable finding rather than diffuse instability: the
interruption is dominated by waiting for the replacement encoder's first usable
IDR, not by process spawn. Whether an explicit immediate-IDR request on the
replacement encoder would shorten it is an open question for `C3.L2`, and is
**not** authorized by this evidence.

The 19 decoder dropped frames and 19 queue-overflow drops are consistent with
one interruption of this scale.

## Disposition against the pre-registered C3.L0 boundary

`C3.L0` pre-registered: interruption materially below the Windows 0.84-0.95 s
reopens Linux actuator classification.

On the authoritative decoder-gap measure, 318 ms against 791 ms is materially
below. **The boundary is met on the measured evidence.**

Therefore:

- D-070's rejection of `video_only_restart` for automatic in-game adaptation
  **does not automatically transfer to Linux**;
- Linux actuator classification is **reopened** and belongs to `C3.L2`;
- the automatic bitrate controller remains **blocked** pending that
  classification.

## Not established by this evidence

- the true Linux video-resume time, pending a `C3.L1R1` re-run;
- focused gameplay observation: whether a freeze was perceptible and for how
  long. `C3.L2` must not be classified without it;
- acceptability of a ~318 ms hitch for automatic mid-game adaptation;
- any Linux bitrate ladder. The Windows 5500/6000/7000 levels remain
  unvalidated on Linux and belong to `C3.L3`;
- anything about bidirectional or upward transitions, which were not exercised.

## Privacy

No network addresses were printed or persisted. The probe confirmed both.
