---
memory_schema: 1
as_of: 2026-09-16
patch: D-099R1_PRESTATE_RECEIPT_ORDER
durable_memory_updated: true
---

# D-099R1 predecessor receipt ordering

The original D-099 installer failed before modification.

Cause:
its pre-state validator merged required predecessor receipts first and optional
D-097 last. For overlapping memory files, that allowed an older D-097 hash to
replace newer D-098 state.

Correction:
- discover the latest successful receipt for each predecessor;
- sort by actual receipt modification time;
- merge post-state in chronological order;
- newest installed receipt wins on overlapping files.

Production D-099 code payload:
unchanged.
