---
memory_schema: 1
as_of: 2026-11-19
baseline_commit: 43016a37
---

# G6-HM4b — the sticks' throw 0.875 × (client source; candidate APK, tablet only)

**Result:** `evidence/G6_HM4B_SHORTER_STICKS_2026-11-19.md`.

- **Files:**
  - `TouchPadState.kt`: `Ps2TouchLayout`'s stick constants (`STICK_R_HM4` 132, `STICK_THROW` 0.875, `STICK_R` 115.5,
    `STICK_PRESS_R` 158.4, `STICK_HIT` = press / ring);
  - `G6TouchPs2Test.kt`: the stick tests at the new radius, plus one new test.
- **Not changed:** every other file, the onn's paths, `companion/`, `tools/`.
- **Diff:** `evidence/g6_hm4b_2026-11-19/g6_hm4b.diff`.
- **APK:** candidate `965d4f19…`, for the tablet only. The onn keeps `ca53df0d…`.
- **Rollback:** `git apply -R docs/memory/evidence/g6_hm4b_2026-11-19/g6_hm4b.diff` (checked with `--check`). On the
  tablet, reinstall G6-HM4's `12bb09e7…`.
