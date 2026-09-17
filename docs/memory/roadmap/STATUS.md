---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 6866ee1a2b9e6dab7e0490796a7d6de74860788a
---

# Roadmap Status

## Current position

D5 TV/EPG work is at final performance/regression closeout.

### Complete / runtime validated

- External/removable VOD.
- Live TV catalog/categories/playback.
- Linux EPG and Android guide cache.
- D5.4 Linux-authoritative TV state.
- D-125 non-blocking EPG misses.
- D-126 Android prefetch.
- D-127 incorrect-guide intent.
- D-129 single-column guide.
- D-131 non-blocking top-level TV entry.
- D-133 EPG status accuracy.

### Diagnostics closed

- D-130 top-level TV-entry bottleneck.
- D-132 guide coverage classification.

### Active

**D-134 — Favorites load latency stage probe.**

### Next

1. measure Favorites dominant stage;
2. one bounded performance fix if needed;
3. focused TV/media regression;
4. close D5 bounded TV work.
