---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 9d7da2ccc47cc78a19f7128161859a1c5f308174
---

# C3 bidirectional actuator runtime disposition

## Classification

**BIDIRECTIONAL RECOVERY VALIDATED / VIDEO-ONLY RESTART REJECTED FOR SEAMLESS AUTOMATIC ADAPTATION**

## Probe sequence

`7000 -> 6000 -> 7000 kbps`

The existing video-only restart actuator completed both legs.

## Final session

- duration: 55,443 ms
- sequence resyncs: 2
- SSRC changes: 2
- packets dropped waiting for IDR: 0
- resync-to-IDR: 61 ms
- max resync-to-IDR: 61 ms
- waiting for IDR at end: false
- lost video packets: 3
- FEC recovered packets: 1
- FEC unrecoverable groups: 1
- decoder rendered frames: 2,938
- decoder dropped frames: 7
- decoder queue-overflow drops: 7
- max decoder output gap: 1,059 ms
- max receive-to-decode: 1,074 ms
- audio lost packets: 10
- audio write errors: 0
- audio underruns: 222
- controller packets sent: 23,916
- controller send errors: 0

Audio counters remain observational under the separately deferred audio
burst/gap investigation.

## Downshift: 7000 -> 6000

Host:
- first RTP resume: 952.789 ms
- host verification: 1,715.798 ms

Fresh post-transition samples:

| elapsed ms | FPS | rendered delta | dropped delta | overflow delta | queue | output gap ms | rx->decode ms |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 11562 | 0.0 | 67 | 0 | 0 | 0 | 5 | 16 |
| 13570 | 59.7952 | 108 | 0 | 0 | 0 | 11 | 20 |
| 15577 | 61.8292 | 113 | 0 | 0 | 0 | 15 | 25 |

The first sample has a zero recent-FPS value while rendered frames advanced;
subsequent fresh intervals were near 60 FPS and clean.

## Upshift: 6000 -> 7000

Host:
- first RTP resume: 837.313 ms
- host verification: 1,597.242 ms

Fresh post-transition samples:

| elapsed ms | FPS | rendered delta | dropped delta | overflow delta | queue | output gap ms | rx->decode ms |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 17585 | 69.7800 | 74 | 1 | 1 | 0 | 2 | 14 |
| 19592 | 59.8147 | 113 | 0 | 0 | 0 | 2 | 13 |
| 21599 | 61.8027 | 115 | 0 | 0 | 0 | 10 | 22 |

The first fresh upshift interval recorded one decoder drop and one queue-overflow
drop. Later samples were clean.

## Focused observation

During one shift, gameplay visibly froze for roughly one second and then
recovered. Outside that transition interruption, gameplay was fine.

## Interpretation

The post-transition sampled windows recover quickly and are mostly clean, but
the host produces no new RTP for roughly 0.84-0.95 seconds while replacing the
encoder. This directly matches the scale of the observed freeze and the final
~1.06-second decoder output-gap maximum.

Therefore the problem is the restart boundary itself, not evidence of sustained
instability at either 6000 or 7000.

## Disposition

- `video_only_restart`: bidirectionally functional.
- `video_only_restart` for automatic active-game adaptation: **NOT ACCEPTED**.
- retain for diagnostics/startup/manual recovery/fallback only.
- automatic bitrate controller remains blocked.
- next actuator investigation: live bitrate reconfiguration without encoder
  process replacement.
