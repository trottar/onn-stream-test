---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 93047ce05399744d461a2ad451fa5604c5f268a9
---

# Current Handoff

The authoritative resumable state is `../CURRENT.md`.

- D-136 automated regression failed only with `D122_TV_STATE_PARITY_FAILED`.
- D-133 and D-135 gates remained clean.
- D-122 reuses D-116's local TV-state projection.
- D-116 still omits D-127 schema-v2 durable guide-intent fields while the Linux
  canonical normalizer includes them.
- D-137 repairs only that diagnostic projection.

Resume by rerunning D-136 after D-137 installs.
