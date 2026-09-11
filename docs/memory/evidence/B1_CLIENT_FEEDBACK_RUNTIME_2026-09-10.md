---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B1.5 Android client-health feedback runtime result

Fresh classification:

`B1_CLIENT_FEEDBACK_CONFIRMED`

Measurements:

- feedback sequence: 56;
- interval: 2,000 ms;
- age: 1,849 ms;
- serialized payload: 631 bytes;
- recent video receive rate: 59.70697583586243 FPS;
- recent video receive bitrate: 8.083767263067973 Mbps;
- FEC recovered packet delta: 0;
- FEC unrecoverable group delta: 0;
- decoder stale-output drop delta: 9;
- decoder queue-overflow drop delta: 0;
- normalized network path: healthy / `NET-PATH-CLIENT-HEALTHY`;
- normalized decoder: degraded / `VIDEO-DECODER-CLIENT-DEGRADED`;
- new Android metrics timer: false;
- new resource sampler: false;
- persistent client-health log: false;
- benchmark thresholds: false;
- privacy checks: passed.

Interpretation:

The B1.5 client-feedback transport and normalized network path are runtime
validated. The decoder classifier is intentionally not accepted as a product
performance conclusion yet because one 2-second interval contained 9
stale-output drops while receive cadence remained ~59.7 FPS, network/FEC showed
no impairment, and queue overflow remained zero.

Per project rule, raw measurements take priority when a classifier may be too
sensitive. B1.6 will measure rendered-frame cadence, stale-output share,
ordinary decoder drops, queue overflow, queue depth, receive→decode delay and
output gaps over multiple consecutive intervals before changing the classifier.
