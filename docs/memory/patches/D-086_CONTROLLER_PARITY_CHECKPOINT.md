---
memory_schema: 1
as_of: 2026-09-16
patch: D-086_CONTROLLER_PARITY_CHECKPOINT
durable_memory_updated: true
production_code_changed: false
---

# D-086 controller parity checkpoint

Purpose:
- promote D-085 from development patch to runtime-validated controller parity
  for the tested 3-game / 3-profile paths;
- reconcile current status/roadmap documents;
- open Linux PS1 multiplayer/multitap as the next Phase-D investigation.

No production code is modified.

Precondition:
- current Git HEAD remains the pushed predecessor checkpoint;
- a successful D-085 installation receipt exists;
- every D-085 recorded post-state SHA-256 still matches the local checkout.

Updated durable surfaces:
- CURRENT / MEMORY / daily / handoff;
- controller architecture;
- A8 documentation;
- roadmap status;
- active/closed investigations;
- PROJECT_STATUS / KNOWN_ISSUES / ROADMAP;
- D-085 runtime evidence;
- Linux multitap investigation record.

Next action after checkpoint push:
- diagnostic-only Linux adaptation of the prior PS1 multitap runtime probe.
