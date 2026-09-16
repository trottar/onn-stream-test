---
memory_schema: 1
as_of: 2026-09-16
patch: D-096R2R1_PROBE_INSTALLER_PRESTATE
durable_memory_updated: true
---

# D-096R2R1 probe installer pre-state correction

Supersedes:
D-096R2 installer attempt, which failed before modification.

Cause:
R2 validated only D-096R1 post-state paths and therefore rejected legitimate
still-uncommitted D-096 production/memory changes.

Correction:
- load D-096 and D-096R1 successful receipts;
- merge expected post-state paths;
- newer D-096R1 post-state overrides D-096 for overlapping paths;
- verify all merged hashes;
- reject any tracked/staged path outside the merged stack.

Probe behavior:
unchanged from D-096R2:
bounded 8765/8000 release wait and lifecycle cleanup required for confirmed
classification.

Production code changed:
none.
