---
memory_schema: 2
as_of: 2026-09-17
---

# Active Investigations and Queued Work

## Active — D-131 non-blocking TV-entry state sync

D-130 measured:

- total TV entry: 24,525 ms;
- initial cached catalog: 7 ms;
- Linux TV-state sync: 24,214 ms;
- post-sync catalog: 3 ms;
- UI render: 291 ms.

Classification: `D130_TV_ENTRY_STATE_SYNC_DOMINANT`.

D-131 preserves the Linux-authoritative state operation but removes it from the
first TV-home render critical path. The cached/local TV home renders first; the
same pull/import continues on the existing network executor and reconciles the
TV UI after completion.

Canonical investigation:
`D131_NONBLOCKING_TV_ENTRY_STATE_SYNC.md`.

## Queued after D-131

1. corrected/expanded EPG coverage/status presentation;
2. focused TV/media regression and D5 checkpoint.
