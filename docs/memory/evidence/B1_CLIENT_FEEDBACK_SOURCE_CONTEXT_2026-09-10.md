---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B1.4 Android client-feedback source-context result

Fresh probe: `B1_CLIENT_FEEDBACK_SOURCE_CONTEXT_CAPTURED`.

Disposition: `METRICS_AND_PERIODIC_NETWORK_PRIMITIVES_EXIST`.

The exact Android source already has the 500 ms metrics tick, receive FPS/Mbps,
RTP/loss/FEC counters, decoder render/drop/queue/stale/timing counters,
HTTP/JSON primitives, background request threads, and lifecycle teardown.

Decision: do not add another timer or decoder sampler. Reuse the existing
metrics tick and publish a small whitelisted report at a slower bounded cadence.
