---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 93047ce05399744d461a2ad451fa5604c5f268a9
---

# Roadmap Status

## Current position

D5 TV/media work remains at the final regression gate.

### Runtime validated

- Live TV / VOD baseline.
- Linux EPG + Android guide.
- D5.4 Linux-authoritative TV state.
- D-129/D-133 guide presentation.
- D-131/D-135 navigation/state executor performance.

### Current regression finding

D-136 failed only because the inherited D-116 projection used by D-122 is stale
for TV user-state schema v2. This is a diagnostic false negative, not yet a
production-state regression.

### Active

**D-137 — update D-116 canonical local projection for schema-v2 guide intent.**

### Next

1. rerun D-136 fresh;
2. if clean, manual Live TV / guide / VOD smoke;
3. close D5 bounded TV/media work.
