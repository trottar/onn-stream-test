---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 20a1112831f47b0c44104d547123395a89964b8a
---

# C3 fixed-bitrate characterization

## Status

**ACTIVE / 5000 KBPS NOT ACCEPTED / NEXT 5500 KBPS BRACKET TEST**

## Question

Does the validated 1280x720@60 stream remain technically and visually
acceptable at a fixed 6000 kbps while preserving GOP15, B-frames0 and FEC8?

6000 kbps is a **diagnostic candidate**, not a production ladder entry.

## Method

Start each characterization session from the validated 7000 kbps reference
stream.

Use the accepted `video_only_restart` actuator boundary to change video only to
6000 kbps. Preserve:
- 1280x720;
- 60 fps;
- GOP 15;
- B-frames 0;
- FEC group size 8;
- process audio;
- persistent controller;
- emulator/game lifecycle.

Capture:
- active host bitrate after the cycle;
- multiple fresh C2 telemetry intervals;
- receiver delivered Mbps/FPS/jitter;
- decoder queue and latency measurements;
- FEC/audio/controller error deltas;
- final Android decoder-session report;
- focused user visual-quality/stutter observation.

Do not classify 6000 as accepted merely because the encoder starts. Manual
quality and technical continuity both matter.

## Next decision

If 6000 is acceptable, record it as a validated candidate and choose exactly one
lower test point next.

If 6000 is unacceptable, do not descend further. Characterize between 6000 and
7000 instead.

No production minimum or automatic adaptation is created by this probe.

## 6000 kbps runtime result

Classification: **VALIDATED CANDIDATE**

Final probe:
`C3_FIXED_6000_EVIDENCE_CAPTURED_WITH_FINDINGS`

The findings were one decoder dropped frame and one decoder queue-overflow drop.
They did not produce an observed gameplay/movement problem and do not by
themselves reject 6000.

Key video/session evidence:
- duration 51,477 ms;
- sequence resyncs 1;
- SSRC changes 1;
- resync-to-IDR 52 ms;
- packets dropped waiting for IDR 0;
- waiting for IDR at end false;
- lost video packets 25;
- FEC recovered 6;
- unrecoverable FEC groups 5;
- rendered frames 2,823;
- decoder dropped frames 1;
- queue-overflow drops 1;
- max output gap 1,016 ms;
- max rx-to-decode 1,025 ms.

Focused observation: movement and everything else was fine; audio was somewhat
stuttery.

Detailed audio report:
- packets 10,190;
- lost packets 11;
- stale drops 868;
- queue depth 8; max queue depth 8;
- underruns 186;
- concealed loss packets 10;
- concealed underruns 922;
- prolonged starvation events 104;
- smooth latency trims 868;
- crossfaded packets 550;
- max queue residence 53 ms;
- average queue residence 26.581176308236806 ms;
- startup prefill 100 ms;
- audio write errors 0.

Interpretation: simultaneous full-queue trimming and prolonged starvation shows
the existing burst/gap timing pathology. The accepted 7000 actuator run already
contained substantial audio loss/underrun totals. Do not attribute this audio
behavior to the 6000 bitrate change.

Next candidate: 5000 kbps.

## 5000 kbps candidate

**Runtime evidence pending.**

Question: does fixed 5000 kbps remain technically and visually acceptable at
unchanged 1280x720@60, GOP15, B-frames0 and FEC8?

Method:
- begin at the 7000 reference;
- perform one loopback-only 7000 -> 5000 video-cycle;
- preserve FEC/audio/controller/game ownership;
- capture post-cycle C2 telemetry;
- capture the final Android decoder-session report;
- include detailed audio queue/starvation counters without using the already
  deferred burst/gap pathology as an automatic bitrate failure;
- require focused visual/gameplay observation.

If 5000 passes, record it as the next validated candidate and choose one lower
point. If it fails on bitrate-specific evidence, stop descending and bracket
between 5000 and 6000.

## 5000 kbps runtime disposition

Classification: **RUNTIME TESTED / NOT ACCEPTED AS LADDER CANDIDATE**

Final result:
`C3_FIXED_5000_EVIDENCE_CAPTURED_WITH_FINDINGS`

Runtime measurements:
- session duration 57,498 ms;
- sequence resyncs 1;
- SSRC changes 1;
- packets dropped waiting for IDR 0;
- resync-to-IDR 17 ms;
- waiting for IDR at end false;
- lost video packets 100;
- FEC recovered packets 6;
- unrecoverable FEC groups 15;
- rendered frames 3,080;
- decoder dropped frames 11;
- decoder queue-overflow drops 11;
- max output gap 1,010 ms;
- max receive-to-decode 1,019 ms;
- audio write errors 0;
- controller send errors 0.

Focused observation:
- image definitely appeared clearer;
- initial lag was still present;
- after it settled, gameplay could run very nicely/smoothly;
- extended play nevertheless showed definitely more visual stutters than the
  other validated bitrate settings;
- possible slightly worse input lag was uncertain.

Decision: the definite steady-state visual-stutter regression is sufficient to
withhold ladder acceptance at 5000. Audio burst/gap counters are retained but
remain a separate deferred issue.

Current bracket: 5000–6000 kbps.
Next single candidate: 5500 kbps.
