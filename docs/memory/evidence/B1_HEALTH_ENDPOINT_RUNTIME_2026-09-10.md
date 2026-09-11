---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B1.3 read-only health endpoint runtime validation

Fresh runtime probe classification:

`B1_HEALTH_ENDPOINT_CONFIRMED`

Measurements:

- endpoint: `GET /diagnostics/health`;
- overall health: healthy / info;
- component count: 11;
- Games status available: true;
- host telemetry available: true;
- host telemetry source: `latest_history`;
- resource availability: available;
- resource measurement scope: `last_session`;
- resource sample count: 41;
- new resource sampler started: false;
- benchmark thresholds applied: false;
- forbidden privacy keys present: false;
- network identifier values present: false.

Conclusion:

The companion health endpoint is runtime validated. It survives companion
restart and correctly recovers the prior resource sample set as `last_session`
instead of presenting it as live data.

Next: audit the exact Android client metric/network/cadence source before adding
client decoder/network feedback.
