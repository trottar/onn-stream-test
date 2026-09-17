---
memory_schema: 2
as_of: 2026-09-17
---

# Active Investigations and Queued Work

## Active — D-132 Favorites EPG coverage/status classification

D-131 is runtime accepted:

`D131_TV_ENTRY_NONBLOCKING_SYNC_VALIDATED`

Measured first render 330 ms with Linux state sync continuing for 24,050 ms and
reconciling afterward. The user reports the TV home now loads in roughly one or
two seconds and other Live TV behavior appears normal.

D-132 does not change production behavior. It classifies visible Favorites guide
coverage from Android cache state and the existing Linux companion guide endpoint
so the final coverage/status UI work is evidence-driven.

Canonical investigation:
`D132_FAVORITES_EPG_COVERAGE.md`.

## Queued after D-132

1. one bounded EPG coverage/status production change, if evidence requires it;
2. focused TV/media regression;
3. D5 checkpoint/closeout.
