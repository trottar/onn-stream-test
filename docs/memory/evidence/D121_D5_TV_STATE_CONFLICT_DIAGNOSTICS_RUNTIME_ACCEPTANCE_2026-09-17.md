# D-121 — D5.4 stale-write conflict diagnostics runtime acceptance — 2026-09-17

**Status:** runtime validated / accepted

Final classification matched the target:

`D121_CONFLICT_PROTECTION_AND_DIAGNOSTICS_RUNTIME_VALIDATED`

The controlled stale-write test matched all expected targets:

- Linux was advanced by one diagnostic revision while the onn retained the
  previous remembered revision;
- one real onn Favorite mutation attempted the production stale push;
- Linux rejected the stale write;
- Linux authoritative prepared state remained unchanged by that write;
- D-120 conflict diagnostics recorded the stale base and newer Linux revision;
- Linux original user-state content was restored at a later monotonic revision;
- normal TV Refresh pulled the restored authority back to the onn;
- exact Linux/onn durable-state parity was restored;
- the temporary local Favorite mutation was discarded by the authoritative
  recovery path.

This accepts D5.4 stale-write protection and conflict observability.

No production conflict-policy change is required.
