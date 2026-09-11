---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B1.6 decoder stale-output semantics result

Fresh classification:

`B1_DECODER_STALE_SEMANTICS_CAPTURED`

Eight consecutive client-health intervals were measured.

Summary:
- stale-output drops occurred in all 8 intervals;
- stale-output drops total: 50;
- rendered frames total: 913;
- ordinary decoder drops total: 0;
- queue-overflow drops total: 0;
- maximum decoder queue depth: 0;
- receive FPS median: 59.799;
- rendered FPS estimate median: 57.250;
- rendered FPS estimate range: 54.000–59.500;
- maximum stale share of decoder outputs: 6.7%;
- seven intervals had healthy network state;
- one interval had upstream network impairment:
  receive FPS 49.958, FEC unrecoverable 1, network dropped frame 1,
  RX-to-decode 77 ms, output gap 66 ms;
- waiting-for-IDR intervals: 0.

Conclusion:

The current rule `any stale output => decoder degraded` contradicts the measured
behavior. Stale-output shedding is a normal recurring part of the current
low-latency decoder policy and is not sufficient evidence of decoder-local
failure.

Do not introduce a guessed stale-count or FPS threshold. Classify direct
decoder-local failure from hardware-decoder absence, ordinary decoder drops or
queue overflow. Preserve stale-output count as an informational measurement and
event. Upstream path impairment remains attributed to the network component.
