---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 13ccff5 (+ B21 + B22)
---

# B23 — `PRIVYHUB_LINK_RECOVERY_WAN=1`: the hold's H and the stall's threshold per path class (WAN-R1)

**Result: BUILT; `tests/link_recovery_wan` 22 green; absent proven (AST); the replay of G4-S4's control-gap log 0
false holds at H 950 and 450; no live run.** Record: `evidence/B23_LINK_RECOVERY_WAN_THRESHOLDS_2026-10-24.md`. Diff:
`evidence/b23_2026-10-24/b23.diff`. Nothing committed.

- **The sets:**
  - `lan` as wired (950 / 400);
  - **`remote-direct` 450 / 200** (WAN-R1 direct: H ≥ 250 / stall ≥ 200 for ≤ 1 false fire / 10 min; H clamped to 450
    so the silence save stays at 400, 50 ms before the hold);
  - `remote-relayed` / `remote-unknown` as wired (relayed not answerable; no-peer / unknown).
- **The class:** the overlay address test (G5-S3's `routing_evidence_of`) and the overlay provider's path, read on a
  daemon thread at the start and every 10 s.
- **A guard:** on direct, the first non-drop hold (< 3 s) reverts the session to the wired values.
- **The rows:** `link_recovery_wan_config` at the wire; `link_recovery_config` (`at` `session`, `wan` {set, path,
  hold_ms, stall_ms, why}) at each set applied.
- **Files:** `companion/link_recovery_wan.py` (new), `companion/plugins/games.py`, `tests/link_recovery_wan/` (new).
- **Rollback:** remove the line; or revert the files above.
