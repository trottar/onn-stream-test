---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 144e5c7 (+ B5-B7 uncommitted)
---

# B1b — `blackout-<D>s@both` also drops the client's `native-stream-desync`

**Result: BUILT; proof ALL MET; NOT ADOPTED; no run.** Record: `evidence/B1B_SHIM_GATE_2026-10-22.md`. Nothing committed.

- **The change:** one guarded statement in the plugin's desync branch (`_impairment_uplink.drop("desync")`). The
  client does not retry the POST.
- **What still passes:** start / stop (the suite), ready (a dropped ready ends the client's session), the stop-time
  report, UI actions.
- **Already dropped:** the controller and B7 stall datagrams, the heartbeat, client-health.
- **Files:** `companion/plugins/games.py` (+3); `tests/impairment/test_blackout.py` (the hook-shape test now expects
  heartbeat + desync).
- **Validation performed:**
  - the in-process proof;
  - `tests/impairment` 29 and the hold / stall suites;
  - the AST identical without the guard;
  - `git diff --check` clean;
  - the redact check.
