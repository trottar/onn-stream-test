---
memory_schema: 1
as_of: 2026-09-16
patch: D-094_D5_EXTERNAL_STORAGE_REMOUNT_EVIDENCE
durable_memory_updated: true
---

# D-094 external-storage remount evidence

Purpose:
record the D5 eject/reinsert runtime result and narrow the configurable-storage
implementation.

Production code changed:
none.

Runtime finding:
- drive reinsertion did not restore the filesystem mount automatically;
- file-manager access activated the mount;
- once mounted, PrivyHub repopulated the VOD library automatically;
- playback worked again.

Next:
deterministic OS mount ownership + configurable PrivyHub bulk-media root +
explicit unavailable-storage state.
