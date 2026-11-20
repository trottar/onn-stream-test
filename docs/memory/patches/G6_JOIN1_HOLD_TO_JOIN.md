---
memory_schema: 1
as_of: 2026-11-20
baseline_commit: 6cfdb746
---

# G6-JOIN1 — hold any touch button to be P1 (client source; candidate APK, tablet only)

**Result:** `evidence/G6_JOIN1_HOLD_TO_JOIN_2026-11-20.md`.

- **Files:**
  - `TouchPlayerRules.kt`: `class TouchHoldJoin`. A touch control held `PlayerPrompt.HOLD_MS` (500 ms) during the
    countdown, P1 free, joins at once and cancels the countdown; otherwise the countdown's own join at 5 s.
  - `TouchPadState.kt`: `output(skip)`, the output without the given controls; `output()` = `output(emptySet())`.
  - `HandheldStreamActivity.kt`:
    - the hold rule on every touch event and tick;
    - the joining controls kept out of what is sent until lifted;
    - the line "Hold any button to join · P1 in 5…";
    - the report's `p1_join_via` and `p1_join_hold_ms`.
  - `G6Join1Test.kt` (new, 7).
- **Not changed:** `PlayerPrompt.kt`, `NativeStreamActivity.kt`, `MainActivity.kt`, the manifest, `PadSlots.kt`,
  `PointerGuard.kt`, `companion/`, `tools/`, `data/`, the pins. No restart.
- **Diff:** `evidence/g6_join1_2026-11-20/g6_join1.diff` (predecessor / after sha256 beside it).
- **APK:** candidate `6d2fff76…`, for the tablet only. The onn keeps `ca53df0d…`.
- **Rollback:** `git apply -R docs/memory/evidence/g6_join1_2026-11-20/g6_join1.diff` (checked with `--check`). On the
  tablet, reinstall G6-STICK1's `786cb2f8…`.
