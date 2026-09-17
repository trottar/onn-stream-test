---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 634bc0affc17f9f4317df896a0068c61f8f2afc3
---

# Roadmap Status

## Current position

D5 TV/EPG work is at final performance/regression closeout.

### Complete / runtime validated

- External/removable VOD.
- Live TV catalog/categories/playback.
- Linux EPG and Android guide cache.
- D5.4 Linux-authoritative TV state.
- D-125/D-126 EPG non-blocking/prefetch behavior.
- D-127 incorrect-guide intent.
- D-129 single-column guide.
- D-131 non-blocking first TV render.
- D-133 EPG status accuracy.

### Diagnostics closed

- D-130: top-level entry blocked on state sync.
- D-132: guide coverage classification.
- D-134: Favorites raw timings exposed ~22.85 s executor queue contention;
  classifier's UI-dominant label was incomplete.

### Active

**D-135 — isolate serialized TV-state synchronization from navigation executor.**

### Next

1. runtime-validate D-135;
2. focused TV/media regression;
3. close D5 bounded TV work;
4. continue broader Linux roadmap.
