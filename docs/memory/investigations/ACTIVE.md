---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: db59209578fc628fc602e707f5f7cd9091949edc
---

# Active Investigations

This file contains only current active/queued work. The exact pre-Part-3
`ACTIVE.md` is preserved as superseded deep memory at:

`docs/memory/history/ACTIVE_INVESTIGATIONS_SUPERSEDED_THROUGH_2026-09-11.md`

Resolved Phase A and Phase B investigation detail is summarized in `CLOSED.md`
and remains fully recoverable from that deep-memory snapshot, dated memory,
evidence, patch history and Git history.

## Docs/memory normalization

**Status:** COMPLETE / CHECKPOINTED / PUSHED

Part 1 current-state alignment and Part 2 durable-memory curation are
checkpointed/pushed.

Part 3 normalizes decision IDs and investigation state. After independent
validation/checkpoint, Part 4 refreshes top-level project docs and ledgers.

This work changes no production/runtime behavior.

## C1 explicit stream profile schema design

**Status:** QUEUED / NEXT TECHNICAL WORK

C1 inventory is complete:

`C1_INVENTORY_COMPLETE`

Next technical classification:

`C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`

Do not rerun the inventory unless source changes invalidate it. Do not begin the
C1 production patch until the focused docs/memory cleanup reaches its intended
checkpoint.

The first C1 implementation remains a behavior-preserving static extraction:
no GUI selector, adaptive controller or generalized streaming framework.
