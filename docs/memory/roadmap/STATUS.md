---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 7d2d5a17d3b568161fccb00cdaeefd22798dca5c
---

# Roadmap Status

## Current position

D5 TV/media work is at the final regression gate.

### Complete / runtime validated

- External/removable VOD.
- Live TV catalog/categories/playback.
- Linux EPG and Android guide cache.
- D5.4 Linux-authoritative TV state.
- D-125/D-126 EPG background behavior.
- D-127 incorrect-guide intent.
- D-129 single-column guide.
- D-131 non-blocking first TV render.
- D-133 EPG status accuracy.
- D-135 TV-state executor isolation / fast Favorites.

### Diagnostics closed

- D-130 top-level TV-entry bottleneck.
- D-132 guide coverage.
- D-134 Favorites queue contention.

### Active

**D-136 — focused TV/media regression gate.**

### Next

1. automated regression baseline;
2. short manual Live TV / guide / VOD smoke;
3. record D5 closeout if clean;
4. continue broader Linux roadmap.
