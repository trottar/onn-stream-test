---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 85cfc89e6327c156df4d9d6fa3bbf7f6b3ac577b
---

# Roadmap Status

## Current position

D5 media/TV work is at the final bounded EPG presentation and regression step.

### Complete / runtime validated

- External/removable VOD storage and hotplug behavior.
- Live TV catalog/categories/playback.
- Linux EPG acquisition and Android guide consumption/cache.
- D5.4 Linux-authoritative TV durable-state synchronization.
- D-125 non-blocking EPG cache-miss handling.
- D-126 Android Favorites/visible-page EPG prefetch.
- D-127 durable incorrect-guide intent/recheck.
- D-129 single-column full-width TV guide.
- D-131 non-blocking TV-entry state synchronization.

### Superseded

- D-128 compact Now/Next treatment on generic tiles.

### Runtime diagnostics closed

- D-130: old TV-entry delay was synchronous TV-state sync.
- D-132: 21 Favorites = 11 current, 5 schedule-gap with future guide, 5 no coverage.

### Active

**D-133 — accurate schedule-gap versus unavailable-guide presentation:
DEVELOPMENT PATCH / RUNTIME VALIDATION NEXT.**

### Next

1. runtime-validate D-133;
2. focused TV/media regression;
3. checkpoint/close D5 bounded TV work;
4. continue broader Linux roadmap.
