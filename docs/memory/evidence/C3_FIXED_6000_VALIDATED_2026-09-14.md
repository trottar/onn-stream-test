---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 20a1112831f47b0c44104d547123395a89964b8a
---

# C3 fixed 6000 kbps runtime validation

## Classification

**VALIDATED LOWER BITRATE CANDIDATE**

- Reference/max: 7000 kbps — validated
- 6000 kbps: **validated lower candidate**
- Production minimum: **unset**
- Next candidate: 5000 kbps
- Automatic controller: **not implemented**

## Fixed parameters

- resolution: 1280x720
- frame rate: 60 fps
- GOP: 15
- B-frames: 0
- FEC group size: 8

## Runtime result

Final probe:

`C3_FIXED_6000_EVIDENCE_CAPTURED_WITH_FINDINGS`

Findings:
- one decoder dropped frame;
- one decoder queue-overflow drop.

Measurements:
- session duration: 51,477 ms;
- sequence resyncs: 1;
- SSRC changes: 1;
- packets dropped waiting for IDR: 0;
- resync-to-IDR: 52 ms;
- waiting for IDR at end: false;
- lost video packets: 25;
- FEC recovered packets: 6;
- FEC unrecoverable groups: 5;
- decoder rendered frames: 2,823;
- decoder dropped frames: 1;
- decoder queue-overflow drops: 1;
- decoder max output gap: 1,016 ms;
- decoder max receive-to-decode: 1,025 ms;
- audio lost packets: 11;
- audio underruns: 186;
- audio write errors: 0;
- controller packets sent: 22,376;
- controller send errors: 0.

## Focused observation

Movement and gameplay were fine.

Audio was somewhat stuttery.

## Detailed audio evidence

The decoder-session audio report recorded:

- packets: 10,190;
- lost packets: 11;
- PCM bytes: 9,835,200;
- write errors: 0;
- stale drops: 868;
- queue depth: 8;
- max queue depth: 8;
- track buffer frames: 960;
- buffered ms: 10;
- underruns: 186;
- low-latency mode: true;
- concealed loss packets: 10;
- concealed underruns: 922;
- prolonged starvation events: 104;
- smooth latency trims: 868;
- crossfaded packets: 550;
- max queue residence: 53 ms;
- average queue residence: 26.581176308236806 ms;
- queue target packets: 3;
- queue capacity packets: 8;
- startup prefill: 100 ms.

The simultaneous full-queue trimming and prolonged starvation/concealment
indicate burst/gap timing behavior rather than simple insufficient average
capacity.

## Comparison with accepted 7000 actuator session

The accepted 7000 session already recorded:
- 54 lost audio packets;
- 316 audio underruns;
- 198 lost video packets;
- 22 unrecoverable FEC groups.

The 6000 session recorded lower whole-session totals for each of those counters.
Therefore the evidence does not support attributing the audible audio stutter
to the 6000 video bitrate.

## Decision

D-064 validates 6000 kbps as the first lower C3 bitrate candidate.

The audio burst/gap pathology remains a separate known issue and stays deferred
for representative Linux + Home-Opal replay.

Next: characterize 5000 kbps as exactly one lower candidate. Do not define the
production minimum or automatic controller yet.
