---
memory_schema: 2
as_of: 2026-09-17
---

# Active Investigations and Queued Work

## Active — D-134 Favorites load latency

D-133 is runtime accepted. Remaining observed issue: Favorites entry can exceed
15 seconds.

Current source runs count/query, prefetch, rejected-guide prefetch and
`hydrateCompanionGuides()` before posting the Favorites UI. D-134 measures those
exact stages before any scheduling change.

## Queued after D-134

1. one narrow fix to the measured dominant stage;
2. focused TV/media regression;
3. D5 checkpoint/closeout.
