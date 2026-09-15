---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 0f0f58ef24646a72ff1aa6b769395d8d8dd06a1b
---

# C3 fixed 5500 kbps runtime validation

## Classification

**VALIDATED LOWER CANDIDATE / CURRENT WINDOWS C3 FLOOR**

Windows C3 fixed ladder:
- 7000 kbps — high/reference;
- 6000 kbps — medium;
- 5500 kbps — low/current Windows floor.

Excluded:
- 5000 kbps — runtime tested / not accepted.

Production adaptive controller: **not yet implemented**.

## Fixed parameters

- resolution: 1280x720;
- frame rate: 60 fps;
- GOP: 15;
- B-frames: 0;
- FEC group size: 8.

## Final runtime result

`C3_FIXED_5500_EVIDENCE_CAPTURED_WITH_FINDINGS`

Measurements:
- session duration: 76,085 ms;
- sequence resyncs: 1;
- SSRC changes: 1;
- packets dropped waiting for IDR: 0;
- resync-to-IDR: 44 ms;
- waiting for IDR at end: false;
- lost video packets: 43;
- FEC recovered packets: 5;
- unrecoverable FEC groups: 12;
- decoder rendered frames: 4,088;
- decoder dropped frames: 57;
- decoder queue-overflow drops: 57;
- decoder max output gap: 1,026 ms;
- decoder max receive-to-decode: 1,036 ms;
- audio lost packets: 31;
- audio write errors: 0;
- audio underruns: 247;
- audio stale drops: 1,252;
- audio max queue depth: 8;
- audio concealed loss packets: 13;
- audio concealed underruns: 1,372;
- audio prolonged starvation events: 178;
- audio smooth latency trims: 1,252;
- audio crossfaded packets: 826;
- audio max queue residence: 49 ms;
- audio average queue residence: 26.381640217936635 ms;
- controller packets sent: 32,960;
- controller send errors: 0.

## Stored post-cycle telemetry inspection

The characterization state already contained six fresh post-cycle C2 samples:

| session elapsed ms | rendered delta | dropped delta | overflow delta | queue depth | output gap ms | rx-to-decode ms |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5,502 | 116 | 0 | 0 | 0 | 12 | 22 |
| 7,509 | 69 | 0 | 0 | 0 | 6 | 15 |
| 9,514 | 112 | 0 | 0 | 0 | 28 | 38 |
| 11,522 | 116 | 0 | 0 | 0 | 19 | 30 |
| 13,530 | 111 | 0 | 0 | 0 | 28 | 36 |
| 15,536 | 114 | 0 | 0 | 0 | 4 | 14 |

Sampled totals:
- rendered delta: 638;
- dropped delta: 0;
- overflow delta: 0.

The tool captured its telemetry baseline before invoking the bitrate cycle and
then retained fresh samples after that baseline advanced. These are therefore
post-cycle interval measurements.

## Focused observation

- initial lag remained for a few seconds;
- the stream recovered;
- after recovery it ran very nicely / was great.

No persistent steady-state visual-stutter problem like the 5000 run was
reported.

## Evidence limitation

The final decoder-session report contains 57 whole-session decoder
drops/overflows, while the stored 5.5–15.5-second post-cycle interval contains
zero corresponding deltas.

The current evidence does not timestamp those 57 events outside the sampled
window. Do not claim they all happened during startup or the actuator
transition.

## Decision

D-066 validates 5500 kbps as the current Windows C3 lower level.

Freeze the Windows controller ladder at 5500/6000/7000 and stop fixed-floor
binary search in this environment.

Proceed next to adaptive bitrate controller implementation.

Linux migration must revalidate the actuator and fixed envelope.

Audio burst/gap remains separately deferred to Linux + Home Opal.
