---
memory_schema: 1
as_of: 2026-10-27
baseline_commit: 2cd392c
---

# B26 — nothing from the old encoder forwarded after the relay's stop (inside `PRIVYHUB_RESTART_FAST_UNLOCK=1`)

**Result: SETTLED + BUILT; `tests/restart_fast_unlock_relay` 5 green (the real FEC relay on loopback), B24's 10 and
B22's 13 unedited and green, every `tests/` suite green; the mutation caught 5 / 5; the adopted behaviour but the one
packet, PROVEN; no client change; no live run.** Record: `evidence/B26_RELAY_STOP_STRAY_PACKET_2026-10-27.md`. Diff:
`evidence/b26_2026-10-27/b26.diff`. Nothing committed.

- **Settled:**
  - CL-B14's 8-byte packet is the old encoder's next frame's first packet. The receive thread read it while
    `stop()` held the relay's lock (the post-fec shim's ≤ 50-ms join), then sent it once the lock was released.
  - Its row's time is the new `start()` closing that open frame, not a send at the old encoder's exit.
  - In CL-B14 it went to the stopped shim's closed port and **never reached the onn**. Without a shim, such a
    packet would reach the onn, where it counts only in `packets` / `bytes`.
- **Built:** `RestartFastUnlock._stop_relay`:
  - the relay's `_client` cleared under its lock, then its `stop()`, then the frame noted after the close dropped;
  - no new flag, row or field.
- **Files:** `companion/restart_fast_unlock.py` (+21 / −1); `tests/restart_fast_unlock_relay/` (new).
- **Apply:** `git apply evidence/b26_2026-10-27/b26.diff` (the tree already carries it, uncommitted). It takes
  effect at the next companion restart; it acts only under the adopted `PRIVYHUB_RESTART_FAST_UNLOCK=1` on a
  guarded start.
- **Rollback:** revert `companion/restart_fast_unlock.py` to HEAD (one call, one method).
