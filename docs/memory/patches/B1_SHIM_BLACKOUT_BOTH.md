---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: aa884a3
---

# B1 — the shim's blackout on both directions (`blackout-<D>s@both|@down`)

**Result: BUILT behind `PRIVYHUB_IMPAIRMENT`, proved in process; NOT ADOPTED; no stream.** Session B, 2026-10-22
(`handoffs/QUEUE_2026-10-22B.md` B1). Record: `evidence/B1_SHIM_BLACKOUT_BOTH_2026-10-22.md`. Nothing committed.

- **What it does:** the downlink is dark for D s every P s at `@post-fec`, and with `@both` the uplink too:
  - controller packets, consumed and taken as never arrived;
  - the heartbeat, not recorded;
  - the client-health report, a 503 and not accepted.

  All on one shared wall-clock scheduler. The new counters are `dropped_blackout` and `uplink_dropped`.
- **Flag absent:** the module is not imported (three guarded imports). The hooked functions' AST, with the hook
  removed, is identical to HEAD's.
- **The files** (`evidence/b1_2026-10-22/b1.diff`; `predecessors/`): `companion/impairment.py` (predecessor
  `1fe144379083bf36
e1ca123b22883c1d`), `native_session_io.py` (+11), `plugins/games.py` (+11), `privyhub_service.py` (+14),
  `tests/impairment/test_blackout.py` (new). The after-hashes are in `after_sha256.txt`.
- **Validation:**
  - impairment 29 OK; the recovery suite 17 OK; every regression suite green but C3-F1's pre-existing error;
  - the proof: all MET (downlink spans 4.0 s at 10 / 30 / 50 s, 20.0 %; uplink gaps 4.0 s, 3 silence callbacks;
    both directions within 14 ms; flag absent identical).
- **Rollback (written, not applied):** copy the four predecessors back from `evidence/b1_2026-10-22/predecessors/`
  and remove `tests/impairment/test_blackout.py`.
