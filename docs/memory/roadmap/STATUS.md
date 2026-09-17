---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: bfc62a6c5b815ecbd9427af0117d5c22906e2998
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
- D-129 single-column full-width TV guide presentation.

### Development-only / superseded

- D-128 compact Now/Next text on generic channel tiles: superseded after runtime
  returned `D128_GUIDE_STYLE_ROWS_NOT_OBSERVED`.

### Active

**D-130 — top-level TV-entry latency stage probe: DIAGNOSTIC / RUNTIME
MEASUREMENT NEXT.**

### Next

1. measure D-130 and patch only the dominant TV-entry stage;
2. correct/expand EPG coverage/status presentation;
3. focused TV/media regression;
4. checkpoint/close D5 bounded TV work;
5. continue the broader Linux roadmap without reopening the deferred UDP branch
   by default.
