---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 020d86a0c0792653e2ce4d976244098981419648
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

### Active

**D-128 — guide-style paged Favorites/category presentation rev3: DEVELOPMENT PATCH /
RUNTIME VALIDATION NEXT.**

### Next

1. finish D-128 runtime acceptance;
2. correct/expand EPG coverage/status presentation;
3. focused TV/media regression;
4. checkpoint/close D5 bounded TV work;
5. continue the broader Linux roadmap without reopening the deferred UDP branch
   by default.
