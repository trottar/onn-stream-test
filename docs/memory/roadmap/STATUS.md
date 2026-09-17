---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 821796701d534e5cee127f43edf85342e1f7998c
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

### Development-only / superseded

- D-128 compact Now/Next text on generic channel tiles: Android build/install
  succeeded, but runtime probe returned `D128_GUIDE_STYLE_ROWS_NOT_OBSERVED` and
  the requested guide layout was not achieved.

### Active

**D-129 — single-column full-width TV guide result presentation: DEVELOPMENT
PATCH / RUNTIME VALIDATION NEXT.**

### Next

1. finish D-129 runtime acceptance;
2. correct/expand EPG coverage/status presentation;
3. focused TV/media regression;
4. checkpoint/close D5 bounded TV work;
5. continue the broader Linux roadmap without reopening the deferred UDP branch
   by default.
