---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: c01bb79ddbf6763a48ce9487ee31cdb8aef9aef6
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

### Active

**D-127 — durable incorrect-guide mark/recheck: DEVELOPMENT PATCH / RUNTIME
VALIDATION NEXT.**

### Next

1. finish D-127 runtime acceptance;
2. guide-style paged Favorites/category UI;
3. correct/expand EPG coverage/status presentation;
4. focused TV/media regression;
5. checkpoint/close D5 bounded TV work;
6. continue the broader Linux roadmap without reopening the deferred UDP branch
   by default.

Browser/app and camera/live generalized native-source work remains outside this
bounded D5 closeout.
