---
memory_schema: 1
as_of: 2026-11-19
baseline_commit: f52ce75b (+ G6-HM1 / HM2 uncommitted)
---

# G6-HM3 — the portrait handheld screen with an inert touch pad (client source; candidate APK, tablet only)

**Result:** `evidence/G6_HM3_PORTRAIT_SCREEN_2026-11-19.md`.

- **Files:**
  - `NativeStreamActivity.kt`: the hooks H1–H9, each defaulting to today's code. 9 lines are replaced, as listed in
    the record.
  - `HandheldStreamActivity.kt` (new).
  - `TouchPadState.kt`: `drawn()` added.
  - `AndroidManifest.xml`: one new `<activity>`; today's entry is byte for byte the same.
  - `MainActivity.kt`: the Settings choice (touchscreen devices only) and the launch's choice.
- **Diff:** `evidence/g6_hm3_2026-11-19/g6_hm3.diff`, relative to the G6-HM2 tree.
- **Switch:** Settings → "Handheld game screen" on a touchscreen device. It is off by default, and absent without a
  touchscreen. `HandheldStreamActivity.TOUCH_LIVE = false` keeps the pad inert until G6-HM4.
- **APK:** candidate `1d658a3f…`, for the tablet only. The onn keeps `ca53df0d…`; its confirmation is a separate task.
- **Rollback:** `git apply -R docs/memory/evidence/g6_hm3_2026-11-19/g6_hm3.diff` (checked with `--check`). On the
  tablet, untick the Settings choice, or reinstall `ca53df0d…`.
