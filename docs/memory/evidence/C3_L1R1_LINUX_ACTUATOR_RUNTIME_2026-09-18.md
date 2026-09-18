---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 094b638a575d0f1acd141193d52a136af39248a2
---

# C3.L1R1 Linux encoder-only actuator runtime evidence

## Classification

**RUNTIME VALIDATED / MEASUREMENT CORRECTION CONFIRMED / C3.L0 BOUNDARY MET**

Trigger: `C3_ACTUATOR_CYCLE_TRIGGERED`, problems none.
Finalize: `C3_ACTUATOR_CONTINUITY_EVIDENCE_CAPTURED`, problems none.

## The correction is confirmed

| Run | spawn | first RTP resume | delta |
| --- | ---: | ---: | ---: |
| `C3.L1` (defective baseline) | 215.007 ms | 215.017 ms | 0.010 ms |
| `C3.L1R1` (corrected baseline) | 115.145 ms | 267.069 ms | **151.924 ms** |

The RTP poll sleeps 10 ms between checks, so a 0.010 ms delta was impossible as
a real measurement and was the defect signature. The corrected run shows roughly
152 ms of genuine video silence after the replacement encoder was spawned.

`encoder_down_ms`, `rtp_silence_after_spawn_ms` and
`rtp_baseline_residual_packets` are returned by the host but not printed by
`tools/probe_c3_actuator_continuity.py`, which extracts only three video fields.
Known limitation, recorded, not patched.

## Host cycle measurements

Pre-cycle: 5.116 Mbps, 61.692 fps, queue depth 0. Delivered bitrate differs from
run 1's 7.379 Mbps because of scene content, not a regression; the 7000 kbps
profile value is a ceiling.

| Measurement | Value |
| --- | ---: |
| `host_ffmpeg_spawn_ms` | 115.145 |
| `host_first_rtp_resume_ms` | 267.069 |
| `host_verified_ms` | 1020.049 |
| FEC RTP packets delta | 721 |
| FEC send errors delta | 0 |
| audio packets delta | 204 |
| audio send errors delta | 0 |
| controller packets delta | 438 |
| controller bad packets delta | 0 |
| recovered mbps / fps | 5.116 / 61.692 |
| recovered waiting for IDR | False |
| recovered queue depth | 0 |
| recovered output gap | 5 ms |

## Session decoder report

| Measurement | Value |
| --- | ---: |
| session duration | 64,842 ms |
| sequence resyncs | 2 |
| SSRC changes | 1 |
| packets dropped waiting for IDR | 123 |
| resync to IDR | 24 ms |
| max resync to IDR | 191 ms |
| waiting for IDR at end | False |
| IDR frames | 255 |
| lost packets | 33 |
| FEC recovered packets | 1 |
| FEC unrecoverable groups | 2 |
| decoder rendered frames | 3,631 |
| decoder dropped frames | 27 |
| decoder queue-overflow drops | 27 |
| decoder max output gap | 287 ms |
| decoder max receive-to-decode | 298 ms |
| audio packets | 12,873 |
| audio lost packets | 7 |
| audio write errors | 0 |
| audio underruns | 110 |
| controller packets sent | 27,980 |
| controller send errors | 0 |

## Lifecycle preservation: PASSED, reproduced

Second consecutive clean cycle. FEC relay, process audio, persistent controller
and emulator all continued. Zero FEC send errors, zero audio write errors, zero
controller send errors. Exactly one SSRC change. Receiver not waiting for IDR at
end.

## Authoritative interruption comparison

`decoder_max_output_gap_ms`, measured on the receiver independently of the host
probe:

| Run | Backend | Gap |
| --- | --- | ---: |
| Windows D-062 same-bitrate | WGC + NVENC | 791 ms |
| Windows D-070 bidirectional | WGC + NVENC | 1,059 ms |
| Linux `C3.L1` same-bitrate | x11grab + VAAPI | 318 ms |
| **Linux `C3.L1R1` same-bitrate** | **x11grab + VAAPI** | **287 ms** |

Two Linux runs at 287 and 318 ms bracket the cost consistently. Against the
directly comparable Windows D-062 run, Linux is ~2.5-2.75x better.

The `C3.L0` pre-registered boundary is met on the authoritative measure.

## The gap is dominated by IDR wait

`max_resync_to_idr_ms` 191 ms with 123 packets dropped waiting for IDR, against
0 dropped on both Windows runs. GOP 15 at 60 fps is a 250 ms keyframe interval,
so the wait is approximately one GOP.

Process spawn is 115 ms; video silence is ~152 ms; decoder gap is 287 ms. The
dominant term is the receiver waiting for the replacement encoder's first usable
IDR, not process creation.

Whether an explicit immediate-IDR request on the replacement encoder would
shrink this is the strongest open lead for `C3.L2`. It is **not** authorized by
this evidence and would require its own hypothesis and probe.

## Focused gameplay observation

Supplied by the user, 2026-09-18:

> The gameplay was pretty good. There is always the occasional stutter that
> happens, but definitely playable. It is still obvious that it is a streamed
> game which I would like to minimize as much as possible.

Interpretation: the cycle did not produce a reported freeze. The occasional
stutter is described as pre-existing baseline behavior and is not attributed to
the actuator cycle. The standing preference to minimize perceptible streaming
artifacts is a constraint on `C3.L2`, which must weigh a ~287 ms automatic
interruption against it.

## Disposition

- Linux encoder-only restart: **runtime validated**, reproduced across two runs;
- interruption cost: **287-318 ms decoder output gap**, dominated by IDR wait;
- `C3.L0` boundary: **met**; D-070's rejection does not transfer to Linux;
- Linux actuator classification: belongs to `C3.L2`, **not decided here**;
- automatic bitrate controller: still **blocked**.

## Not established

Bidirectional or upward transitions, any Linux bitrate ladder, acceptability of
a ~290 ms automatic mid-game interruption, and whether an immediate-IDR request
would reduce it.

## Privacy

No network addresses printed or persisted; the probe confirmed both on both
phases.
