# D-115 — D5.4 Linux TV-state authority runtime acceptance — 2026-09-17

**Status:** runtime validated / accepted

D-115 passed its real companion HTTP runtime probe.

Classification:

`D115_TV_STATE_AUTHORITY_RUNTIME_VALIDATED`

Measured behavior:

- authority initially uninitialized at revision 0;
- first bounded JSON write succeeded and produced revision 1;
- GET returned the persisted revision/state;
- runtime-only fields were absent from persisted user state;
- an identical write was idempotent and remained revision 1;
- a stale revision write returned `revision_conflict`;
- stale-write rejection preserved the authoritative state;
- the probe restored the exact predecessor state and removed its temporary
  `data/tv_state` directory because no state existed before the probe.

No Android database was modified.

D-115 is accepted as the Linux durable TV-state authority seam.

D-116 may now connect Android to this authority.
