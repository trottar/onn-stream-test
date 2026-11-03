---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 20a1112831f47b0c44104d547123395a89964b8a
---

# C3 fixed-bitrate characterization

## Status

**COMPLETE / 5500 KBPS VALIDATED / WINDOWS FIXED ENVELOPE FROZEN**

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

## 5500 kbps midpoint candidate

**Runtime evidence pending.**

Question: is fixed 5500 kbps acceptable at unchanged
1280x720@60/GOP15/B-frames0/FEC8?

Method:
- begin from the 7000 reference;
- perform one loopback-only 7000 -> 5500 video cycle;
- preserve FEC/audio/controller/game ownership;
- capture post-cycle C2 telemetry;
- capture the final Android decoder-session report;
- retain detailed audio queue/starvation counters without using the separately
  deferred burst/gap pathology as an automatic failure;
- require enough focused steady-state play after transition to distinguish
  startup effects from persistent visual stutter.

Decision boundary:
- pass -> 5500 becomes a validated candidate and the lower envelope can be
  reconsidered below/at 5500;
- fail on steady-state smoothness -> retain 6000 as the lowest validated level
  and bracket the floor between 5500 and 6000 or stop further descent,
  depending on severity.

## 5500 kbps runtime result

Classification: **VALIDATED LOWER CANDIDATE / CURRENT WINDOWS FLOOR**

Final result:
`C3_FIXED_5500_EVIDENCE_CAPTURED_WITH_FINDINGS`

Whole-session measurements:
- duration 76,085 ms;
- sequence resyncs 1;
- SSRC changes 1;
- packets dropped waiting for IDR 0;
- resync-to-IDR 44 ms;
- waiting for IDR at end false;
- lost video packets 43;
- FEC recovered packets 5;
- unrecoverable FEC groups 12;
- rendered frames 4,088;
- decoder dropped frames 57;
- queue-overflow drops 57;
- max output gap 1,026 ms;
- max rx-to-decode 1,036 ms;
- audio lost packets 31;
- audio write errors 0;
- audio underruns 247;
- audio stale drops 1,252;
- audio concealed underruns 1,372;
- audio prolonged starvation events 178;
- controller send errors 0.

Stored post-cycle telemetry samples:
- elapsed 5,502 ms: rendered +116, dropped +0, overflow +0, queue depth 0;
- elapsed 7,509 ms: rendered +69, dropped +0, overflow +0, queue depth 0;
- elapsed 9,514 ms: rendered +112, dropped +0, overflow +0, queue depth 0;
- elapsed 11,522 ms: rendered +116, dropped +0, overflow +0, queue depth 0;
- elapsed 13,530 ms: rendered +111, dropped +0, overflow +0, queue depth 0;
- elapsed 15,536 ms: rendered +114, dropped +0, overflow +0, queue depth 0.

Post-cycle sampled totals:
- rendered +638;
- dropped +0;
- overflow +0.

Focused observation:
- initial lag remained for a few seconds;
- it recovered;
- after recovery the stream ran very nicely / was great.

Interpretation:
the sampled post-cycle interval is clean and matches the focused steady-state
observation. The 57 final whole-session drops are preserved but cannot be
localized by the existing evidence outside that sampled window; do not claim
they were all startup drops.

Decision:
accept 5500 as the current Windows C3 lower ladder level. End further
fixed-floor binary search in this environment and proceed to the adaptive
controller. Revalidate the fixed envelope on Linux.
