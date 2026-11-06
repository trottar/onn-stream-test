---
memory_schema: 1
as_of: 2026-11-06
baseline_commit: 795d80d4
---

# B42 — the screen-loss hold and stable slots on by default (`0` / `off` off)

**Result: BUILT; JVM 6 new (201 / 201, three runs); a mutation fails 5; `0` / `off` = the CONFIRMED build's absent
PROVEN; host suites as the baseline; NOT ADOPTED (no host line); no live run.** Record:
`evidence/B42_HOLD_AND_SLOTS_DEFAULT_ON_2026-11-06.md`. Nothing committed.

- **Built:** the user's G-A11 / G-A12 "yes" (2026-11-06).
  - `SurfaceHoldFlag.parse`: absent / empty / junk → the 12-s bound; `1` / a bound 10000-30000 as before; `0` / `off` →
    off. A failed read → on.
  - `PadSlotsFlag.parse`: stable unless `off` / `0`. A failed read → stable.
  - B32 / B34 / B38 / B39's behaviour unchanged; the activity byte-identical.
- **Host:** no change. Every session from this APK sends `pad_slots`, so B38's changed-only counter is on for every
  session (the heartbeat's `updates_by_player` = changes, `packets_by_player` = the old count).
- **Files:** `SurfaceHold.kt` / `PadSlots.kt` (the flag objects only); `HoldAndSlotsDefaultOnTest.kt` (new); the flag
  lines in `SurfaceHoldTest`, `PadSlotsTest`, `VirtualRemoteNoSlotTest` moved (disclosed).
- **Apply:** `git apply evidence/b42_2026-11-06/b42.diff` from the repo root (the coordinator integrates it).
- **Rollback:** `setprop debug.privyhub.surface_hold 0` / `setprop debug.privyhub.pad_slots off` on the onn; or revert the
  two flag objects.
