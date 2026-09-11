---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B1.1 diagnostics inventory result

Fresh local probe classification:

`B1_DIAGNOSTICS_INVENTORY_CAPTURED`

Key measurements:

- 198 tracked files scanned;
- existing debug harness modes: GameSmear, CollectLatest, TransportHistory,
  AudioHistory;
- share-bundle protections present for IPv4/IPv6/MAC redaction, raw PktMon
  exclusion and SHARE_ME packaging;
- 15 existing versioned diagnostic/telemetry schemas found;
- common `subsystem + severity + event_code + health` contract: absent;
- health aggregator candidates: 0;
- Android transport diagnostic activities: 3;
- unified GUI diagnostics surface: absent;
- decoder, host telemetry, audio timing and capture diagnostic artifacts all
  exist;
- host telemetry contains a bounded `MAX_SAMPLES` mechanism;
- no directory-level retention policy was established by the inventory.

Local storage pressure is already material:
- forward transport history: ~338 MB;
- reverse transport history: ~131 MB;
- debug bundles: ~25 MB.

Conclusion:

PrivyHub should not create a parallel logging stack. B1.2 should introduce a
small common health/resource normalization model that consumes existing status
and telemetry. Detailed subsystem artifacts remain the evidence source. A
separate bounded directory-retention policy is required later in B1.
