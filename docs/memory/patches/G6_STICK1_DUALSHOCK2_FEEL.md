---
memory_schema: 1
as_of: 2026-11-20
baseline_commit: b2716e17
---

# G6-STICK1 — DualShock 2 stick feel (client source; candidate APK, tablet only)

**Result:** `evidence/G6_STICK1_DUALSHOCK2_FEEL_2026-11-20.md`.

- **Files:**
  - `TouchPadState.kt`:
    - `output()` sends `stickSent()` through `object Ds2Stick`: dead zone 0.1, full at 0.75 of the throw (the
      user's choice; first 0.9), the circle
      to the square, PCSX2's `AxisScale` 1.33 compensated, a full target sent as full;
    - `Ds2Stick.endToEnd` (the PCSX2 model, for the report);
    - `stickMagnitude`;
    - `class StickStats`;
  - `HandheldStreamActivity.kt`: the report's `stick_out_max`, `stick_diag_max`, `stick_edge_frac`, `stick_mag_hist`
    and `stick_mapping` (sampled at the 100-ms tick);
  - `G6Stick1Test.kt` (new, 7);
  - `G6TouchPs2Test.kt` (two tests updated to the new sent values, disclosed in the record).
- **Not changed:** `NativeStreamActivity.kt`, `MainActivity.kt`, the manifest, `PadSlots.kt`, `PointerGuard.kt`,
  `companion/`, `tools/`, `data/` (PCSX2's settings), the pins. No restart.
- **Diff:** `evidence/g6_stick1_2026-11-20/g6_stick1.diff` (predecessor / after sha256 beside it).
- **APK:** candidate `786cb2f8…` (full at 0.75; the first build `3d4a7203…`, full at 0.9, superseded before any run), for
  the tablet only. The onn keeps `ca53df0d…`.
- **Rollback:** `git apply -R docs/memory/evidence/g6_stick1_2026-11-20/g6_stick1.diff` (checked with `--check`). On
  the tablet, reinstall G6-SCREEN1b's `adcb1222…`.
