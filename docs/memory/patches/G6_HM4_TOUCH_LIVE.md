---
memory_schema: 1
as_of: 2026-11-19
baseline_commit: 7fb2518a
---

# G6-HM4 — the PS2 touch controls live, the main app's 2 columns upright (client source; candidate APK, tablet only)

**Result:** `evidence/G6_HM4_TOUCH_LIVE_2026-11-19.md`.

- **Files:**
  - `TouchPadState.kt`: the PS2 layout (addendum B2), the sticks, L3 / R3;
  - `HandheldStreamActivity.kt`: `TOUCH_LIVE` true, End on B2's place, the report keys;
  - `HandheldInput.kt`: `catalogColumns`;
  - `MainActivity.kt`: +11, inside `useHandheldGameScreen()`;
  - the new test `G6TouchPs2Test.kt`.
- **Not changed:** `NativeStreamActivity.kt`, `AndroidManifest.xml`, `PadSlots.kt`, `PointerGuard.kt`,
  `PlayerPrompt.kt`, `NativeControllerSender.kt`, `companion/`, `tools/`.
- **Diff:** `evidence/g6_hm4_2026-11-19/g6_hm4.diff`.
- **Switch:** the Settings choice "Handheld game screen" on a touchscreen device (off by default; absent without a
  touchscreen). The onn never enters these paths.
- **APK:** candidate `12bb09e7…`, for the tablet only. The onn keeps `ca53df0d…`.
- **Rollback:** `git apply -R docs/memory/evidence/g6_hm4_2026-11-19/g6_hm4.diff` (checked with `--check`). On the
  tablet, reinstall G6-HM3's `1d658a3f…` or untick the Settings choice.
