---
memory_schema: 1
as_of: 2026-11-21
baseline_commit: 45e8ec97
---

# G6-SWAP1 — face buttons up, right stick down (client source; candidate APK, tablet only)

**Result:** `evidence/G6_SWAP1_RIGHT_SIDE_SWAP_2026-11-21.md`.

- **Files:**
  - `TouchPadState.kt`: `layoutPs2`'s face diamond around (900, 295) and right stick at (900, 805);
    `Ps2TouchLayout.LAYOUT_VERSION` `"ps2-swap1"`;
  - `HandheldStreamActivity.kt`: the report's `layout_version`;
  - `G6Swap1Test.kt` (new, 5);
  - `G6TouchPs2Test.kt` and `G6Screen1Test.kt`: the tests pinning the five controls' old places, updated (disclosed in
    the record).
- **Not changed:** every other control, `NativeStreamActivity.kt`, `MainActivity.kt`, the manifest, `PadSlots.kt`,
  `PointerGuard.kt`, `companion/`, `tools/`, `data/`, the pins. No restart.
- **Diff:** `evidence/g6_swap1_2026-11-21/g6_swap1.diff` (predecessor / after sha256 beside it).
- **APK:** candidate `0a631e79…`, for the tablet only. The onn keeps `ca53df0d…`.
- **Rollback:** `git apply -R docs/memory/evidence/g6_swap1_2026-11-21/g6_swap1.diff` (checked with `--check`). On the
  tablet, reinstall G6-JOIN1's `6d2fff76…`.
