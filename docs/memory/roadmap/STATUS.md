---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 0206017cfd8f0fc57decb7a5e9e8632e6a4f6cdd
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

**D-127 — durable incorrect-guide mark/recheck.**

### Next

1. guide-style paged Favorites/category UI;
2. correct/expand EPG coverage/status presentation;
3. focused TV/media regression;
4. checkpoint/close D5 bounded TV work;
5. continue the broader Linux roadmap without reopening the deferred UDP branch
   by default.

Browser/app and camera/live generalized native-source work remains outside this
bounded D5 closeout.
