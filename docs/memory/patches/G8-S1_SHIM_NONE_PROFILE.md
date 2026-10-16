---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 64d9489
---

# G8-S1 — the impairment shim accepts `none` (the control profile)

**Result: APPLIED** (session A, 2026-10-16, before G8-S1's pre-registration; the user's decision: "Add `none` to the
shim").

- **Why:** G8-S1's control cells run `PRIVYHUB_IMPAIRMENT=none@post-fec,seed=1`, the shim in the path with no stage, to
  measure its own cost.
  - G8-P1's `parse()` rejects `none` ("unknown profile 'none'"), so the FEC sender's `start()` would have raised and the
    control cells could not stream.
  - G8-P1's proof built the `none` profile directly in code (`Profile(names=("none",))`), never through the flag.
- **What:** `companion/impairment.py` `PROFILES` gains `"none": {}` (+ one comment line). Every stage's parameter stays
  at its zero default, so the shim relays in order: the same path as G8-P1's proof "none" row. No other line changed.
  - `tests/impairment/test_impairment.py`: the profile-set assertion includes `none`.
  - A new test, `test_none_through_the_flag`: the flag value parses to `none`, post-fec, seed 1, every stage zero, and
    2000 offers pass in order.

  | file | predecessor sha256 (16) | after (16) |
  | --- | --- | --- |
  | `companion/impairment.py` | `1c2512aecb18da34` | `1fe144379083bf36` |
  | `tests/impairment/test_impairment.py` | `c19898cb747a398f` | `e1ca123b22883c1d` |

- **Diff:** `evidence/g8_s1_2026-10-16/g8_s1_shim_none.diff`; predecessors in `evidence/g8_s1_2026-10-16/predecessors/`.
- **Validation:**
  - `tests/impairment`: 14 / 14 (13 + the new one);
  - `tests/overlay`, `session_identity`, `wan_telemetry` and `wan_adaptation`: all OK (`shim_tests_*.txt`);
  - `git diff --check` clean.
  - With the flag absent the module is not imported (G8-P1's guard), so the adopted state is untouched.
  - The running companion picks the change up at each cell's restart.
- **Revert:** copy the two predecessors back.
- Record: `evidence/G8_S1_LAUNCH_2026-10-16.md`.
