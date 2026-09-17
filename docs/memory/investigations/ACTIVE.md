---
memory_schema: 2
as_of: 2026-09-17
---

# Active Investigations and Queued Work

## Active — D-135 TV-state executor isolation

D-134 raw evidence:

- total Favorites load: 24,382 ms;
- named stage sum: 1,530 ms;
- residual/unmeasured interval: 22,852 ms.

The D-134 classifier called UI render dominant only because 844 ms was the
largest named stage. That classifier omitted pre-executor queue wait.

Source inspection confirms the queue hypothesis: D-131's long Linux state pull
remains inside the same single-thread `networkExecutor` used by `openTvPage()`.

D-135 moves TV-state push/pull work onto its own single-thread executor so state
authority remains serialized while navigation is no longer blocked.

## Queued after D-135

1. focused TV/media regression;
2. D5 checkpoint/closeout.
