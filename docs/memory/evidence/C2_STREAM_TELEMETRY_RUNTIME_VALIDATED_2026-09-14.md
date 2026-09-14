---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 47d3cf54220146c1d727e2a0491111f6d7dea6c9
---

# C2 stream telemetry runtime validation

## Result

**C2_STREAM_TELEMETRY_RUNTIME_PASS**

C2 telemetry v1 is **COMPLETE / RUNTIME VALIDATED / CHECKPOINT PENDING**.

## Automated checks

All runtime validator checks passed:

- schema;
- available/fresh;
- reference profile;
- client delta;
- inter-arrival jitter;
- control-path round trip;
- sender delta/bytes/calls/errors/average/max;
- queue depth and signed queue-depth delta;
- no adaptation-decision fields.

## Representative measurements

- sample interval: 2000 ms;
- receiver recent Mbps: 7.457503200420356;
- receiver recent FPS: 61.35262987276094;
- inter-arrival jitter: 2.399 ms;
- lost packets delta: 0;
- recovered FEC packets delta: 0;
- unrecoverable FEC groups delta: 0;
- control-path round trip: 42 ms;
- receive-to-decode: 30 ms;
- output gap: 20 ms;
- queue depth: 0;
- queue-depth delta: 0;
- sender bytes delta: 2086042;
- sender calls delta: 1929;
- sender errors delta: 0;
- average sender call: 33.18926905132194 us;
- max sender call: 820.7 us.

These are measurements from one representative interval, not adaptation
thresholds or acceptance limits.

## Manual regression

The representative game session passed:

- picture;
- process audio;
- controller input;
- Pause/Resume;
- Save/Load;
- End/teardown.

## Privacy / architecture

No network address was printed by the C2 validator, and the public telemetry
contract contains no source/request address identity field.

C2 remains measurement-only. It does not implement bitrate decisions,
congestion classification, hysteresis, hold-down, adaptive FEC, WAN overlay or
session routing.

**Next after checkpoint/push:** C3 adaptive bitrate.
