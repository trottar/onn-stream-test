---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: f7962f667dfcbd80425db0d0ed8bff0e3c44ec4c
---

# C3 video-only restart runtime validation

## Classification

**ACCEPTED INITIAL C3 ACTUATOR STRATEGY**

- Windows implementation: **runtime validated**
- Backend-neutral `video_only_restart` strategy: **accepted**
- Linux implementation: **not yet runtime validated**
- Production adaptive controller: **not implemented**
- Production bitrate ladder/minimum: **not yet defined**

## Runtime probe

Final result:

`C3_ACTUATOR_CONTINUITY_EVIDENCE_CAPTURED`

Problems:

`<none>`

Representative session measurements:

- session duration: 40,009 ms;
- sequence resyncs: 1;
- SSRC changes: 1;
- packets dropped waiting for IDR: 0;
- resync-to-IDR: 17 ms;
- max resync-to-IDR: 17 ms;
- waiting for IDR at session end: false;
- IDR frames: 145;
- decoder rendered frames: 2,131;
- decoder dropped frames: 0;
- decoder queue-overflow drops: 0;
- decoder max output gap: 791 ms;
- decoder max receive-to-decode: 800 ms;
- audio write errors: 0;
- controller send errors: 0.

Whole-session totals also included 198 lost video packets, 6 recovered FEC
packets, 22 unrecoverable FEC groups, 54 lost audio packets and 316 audio
underruns. Those whole-session totals are **not attributed entirely to the
actuator cycle**.

## Focused user-experience observation

Focused play continued for several minutes after the probe.

Observed:
- play felt normal;
- possible slight stutter was not distinguishable from existing occasional
  baseline stutter;
- no clear freeze was observed;
- no black frame was observed;
- no audio interruption was observed;
- no controller stall was observed.

This supports practical viability but does not prove an imperceptible or
zero-interruption transition. The measured 791/800 ms maxima remain
authoritative evidence.

## Architecture conclusion

D-063 accepts `video_only_restart` as the initial **backend-neutral** C3 actuator
strategy.

The Windows runtime implementation uses WGC + FFmpeg/NVENC. That exact
implementation is not portable to Linux.

Linux must implement the same controller-facing boundary using the selected
Linux capture/encoder backend while preserving, where supported:

- FEC/transport ownership;
- process audio;
- persistent controller;
- game/emulator lifecycle;
- receiver resync/IDR recovery.

Equivalent continuity validation is required on Linux before Linux actuator
acceptance.

## Next

Run fixed-bitrate characterization at 1280x720@60, GOP15, B-frames0 and FEC8.
Only runtime-accepted fixed levels may become the production bitrate ladder and
minimum.
