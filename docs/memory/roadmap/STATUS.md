---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 6da5c4506128b2518370de0f46e7b719bd967850
---

# Roadmap Status

## Current position

D5 media/TV work is at its final bounded usability/closeout sequence.

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

### Development-only / superseded

- D-128 compact Now/Next text on generic tiles: superseded after runtime UI
  target failure.

### Runtime evidence

- D-130: `D130_TV_ENTRY_STATE_SYNC_DOMINANT`; 24,214 ms of a 24,525 ms cached
  TV-entry path was synchronous TV-state sync.

### Active

**D-131 — non-blocking top-level TV-state synchronization: DEVELOPMENT PATCH /
RUNTIME VALIDATION NEXT.**

### Next

1. finish D-131 runtime acceptance;
2. correct/expand EPG coverage/status presentation;
3. focused TV/media regression;
4. checkpoint/close D5 bounded TV work;
5. continue the broader Linux roadmap without reopening the deferred UDP branch
   by default.
