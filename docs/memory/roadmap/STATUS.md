---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 0c9d1aee1f4d9d65c2ee15729a52fbbb32861dd8
---

# Roadmap Status

## Current position

D5 media/TV work is in final bounded EPG usability/closeout work.

### Complete / runtime validated

- Linux Games representative baseline.
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

- D-130 measured the old TV-entry bottleneck as synchronous TV-state sync.

### Active

**D-132 — Favorites EPG coverage/status classification: DIAGNOSTIC / RUNTIME
MEASUREMENT NEXT.**

### Next

1. classify remaining guide-coverage gaps;
2. make at most one bounded evidence-driven coverage/status change;
3. focused TV/media regression;
4. checkpoint/close D5 bounded TV work;
5. continue broader Linux roadmap.
