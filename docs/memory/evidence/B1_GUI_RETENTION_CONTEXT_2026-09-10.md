---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B1.8 GUI/Self-Test + retention context result

Fresh classification:

`B1_GUI_SELF_TEST_RETENTION_CONTEXT_CAPTURED`

GUI:
- MainActivity: 14,437 lines;
- existing standalone diagnostic activities: 3;
- health endpoint available with 11 components;
- resource scope at capture: `last_session`;
- architecture disposition:
  `STANDALONE_DIAGNOSTICS_ACTIVITY_PREFERRED`.

Existing Self-Test inputs:
- health endpoint;
- debug harness;
- sanitized support-bundle tool;
- three Android transport-probe activities.

Retention pressure:
- `logs/transport_probe`: 322.048 MiB / high;
- `logs/transport_reverse`: 125.393 MiB / high;
- `logs/debug_bundles`: 23.728 MiB / moderate;
- other audited runtime families were low.

No retention files were deleted.

Conclusion:

Build a standalone Diagnostics activity as a thin consumer of the common health
contract. MainActivity should receive navigation only.

Introduce retention as a manual, dry-run-first allowlisted policy over measured
runtime-log families. Durable-memory evidence and patch backups are outside
normal retention scope. Automatic deletion is not enabled until the real
candidate plan is reviewed.
