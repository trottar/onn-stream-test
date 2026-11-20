---
memory_schema: 1
as_of: 2026-11-20
baseline_commit: daf72e10
---

# G6-SCREEN1 — a 4:3 picture in portrait handheld mode (client source; candidate APK, tablet only)

**Result:** `evidence/G6_SCREEN1_4X3_PICTURE_2026-11-20.md`.

- **Files:**
  - `HandheldInput.kt` (`HandheldGeometry`): the 4:3 box (`videoBoxHeight(w)` = w · 3/4; `videoBoxHeight(w, h)` with
    the 16:9 fallback where the pad region would be under its reference shape); `CROP_4X3_SYSTEMS` = SNES, N64;
    `crop43`, `videoCrop`, `videoSourceRect`, `surfaceRect`;
  - `HandheldStreamActivity.kt`: the box lays the video surface out (cropped: 1600 x 900 centred; not: 1200 x 675 at
    the top); H10 / H11 overrides; the report's `video_crop` and `video_source_rect`;
  - `TouchPadState.kt`: `Ps2TouchLayout.REF_H` 1100, the cluster's y − 225 (`SHOULDER_Y` 549), End at x 1080;
  - `NativeStreamActivity.kt`, **hooks only:** H10 `onGameSystem` (no-op; one call after H5), H11
    `pausedFramePreview` (default: the replaced `createScaledBitmap(source, 480, 270, true)`), accessor
    `streamSurface`;
  - tests: `G6Screen1Test.kt` (new, 7); `G6TouchPs2Test.kt` and `G6TouchPadStateTest.kt` updated to the new geometry.
- **Not changed:** the manifest, `MainActivity.kt`, `PadSlots.kt`, `PointerGuard.kt`, `companion/`, `tools/`, the hub.
- **Diff:** `evidence/g6_screen1_2026-11-20/g6_screen1.diff` (predecessor / after sha256 beside it).
- **APK:** candidate `e4263fd9…`, for the tablet only. The onn keeps `ca53df0d…`.
- **Rollback:** `git apply -R docs/memory/evidence/g6_screen1_2026-11-20/g6_screen1.diff` (checked with `--check`). On
  the tablet, reinstall G6-HM4b's `965d4f19…`.
