---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B1.7 decoder classifier runtime validation

Fresh classification:

`B1_DECODER_CLASSIFIER_CONFIRMED`

Six stale-only intervals were observed.

Every interval had:
- ordinary decoder drops: 0;
- queue-overflow drops: 0;
- decoder health: healthy;
- event: `VIDEO-DECODER-LOW-LATENCY-SHEDDING`.

Stale-output deltas were 3, 8, 7, 8, 7 and 7 while rendered-frame deltas remained
111–117 per 2-second interval. Five intervals had healthy network state; one
interval independently had degraded network state while decoder health correctly
remained healthy.

Validation summary:
- stale-only intervals classified healthy: true;
- low-latency-shedding event used: true;
- direct decoder-local fault rule preserved by deterministic fixture: true;
- hardware-decoder requirement preserved: true;
- arbitrary stale/FPS threshold added: false;
- client feedback cadence changed: false;
- new sampler added: false.

Conclusion:

The B1 decoder classifier now separates decoder-local health from upstream
network health and preserves stale shedding as measurement context.
