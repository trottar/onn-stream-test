---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B1.2 unified health/resource model runtime validation

Fresh runtime probe classification:

`B1_HEALTH_MODEL_SNAPSHOT_CAPTURED`

Idle-state normalized result:

- overall health: healthy / info;
- 11 components emitted;
- companion and media server healthy;
- game/stream/capture/transport/audio/controller/network/decoder correctly idle;
- host resource telemetry healthy and available from the last session;
- resource sample cadence: 2.0 seconds;
- resource sample count: 41;
- logical CPU count: 8;
- capture CPU host average/max: 6.382 / 7.846 percent;
- capture working-set average/max: 82.362 / 86.469 MiB;
- encoder CPU host average/max: 9.05 / 11.395 percent;
- encoder working-set average/max: 125.815 / 132.656 MiB;
- GPU utilization unavailable;
- encoder-engine utilization unavailable;
- host total/available RAM unavailable;
- capacity classification: unclassified;
- stream-profile fit: unclassified;
- benchmark thresholds applied: false.

Interpretation:

The common health/resource model agrees with the actual idle system state and
successfully reuses existing session telemetry without adding a sampler. The
resource contract is suitable as the stable base for later Phase E benchmark
classification, but current measurements are not sufficient to define hardware
tiers.

Next: expose the validated model through a read-only companion endpoint.
