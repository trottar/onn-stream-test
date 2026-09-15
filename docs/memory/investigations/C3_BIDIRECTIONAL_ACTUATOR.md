---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 9d7da2ccc47cc78a19f7128161859a1c5f308174
status: development_diagnostic_runtime_validation_pending
---

# C3 bidirectional actuator validation

## Narrow question

Can the already-accepted backend-neutral video-only restart actuator transition
both down and back up across validated C3 ladder levels while preserving game,
FEC, process-audio and controller continuity?

## Why this probe exists

Existing fixed-bitrate characterization validated only transitions beginning at
7000 kbps and moving downward.

An adaptive controller must also recover upward after sustained clean telemetry.

Do not enable automatic adaptation until the upward leg is runtime validated.

## Diagnostic sequence

One loopback-only tool performs:

`7000 -> 6000 -> 7000`

The existing shared video-only restart implementation is generalized rather than
copied.

The tool requires two consecutive clean existing C2 telemetry samples after the
downshift before it is allowed to attempt the upshift.

Clean diagnostic recovery uses the already-validated startup/readiness envelope:
- telemetry available/fresh with deltas;
- receiver not waiting for IDR;
- recent FPS >=45;
- rendered frames advancing;
- zero new decoder drops/queue-overflow drops;
- queue depth zero;
- output gap <=120 ms;
- receive-to-decode <=150 ms.

This is a probe sequencing guard, not yet the production controller policy.

## Preservation boundary

The probe must not:
- enable automatic bitrate decisions;
- change resolution/FPS/GOP/B-frames/FEC;
- restart FEC/audio/controller;
- pause or restart the game/emulator;
- expose a non-loopback bitrate control endpoint;
- use the deferred audio burst/gap pathology as an automatic rejection reason.

## Runtime evidence

Capture:
- host first-RTP/verification time for both legs;
- fresh post-transition C2 interval telemetry;
- final decoder-session resync/SSRC/drop/latency evidence;
- audio/controller error continuity;
- focused user observation of whether either transition is visibly disruptive.

Runtime validation pending.

## Runtime disposition — D-070

The probe completed both directions and recovered.

Measured first-RTP restart gaps:
- 7000 -> 6000: 952.789 ms;
- 6000 -> 7000: 837.313 ms.

Focused play observed approximately one second of frozen gameplay during one
transition.

Final max decoder output gap: 1,059 ms.

The downshift fresh recovery intervals contained no decoder drop/overflow
deltas. The first fresh upshift interval contained one drop and one overflow;
later intervals were clean.

Conclusion:
**bidirectional functionality validated; seamless automatic use rejected.**

Close this investigation. Next investigate live bitrate reconfiguration without
encoder replacement.
