# B39 — flag absent = today: PROVEN

- **`proof_flag_absent.py` → `proof_flag_absent_output.txt`:** every line B39 adds to or removes from
  `NativeStreamActivity.kt` is classified by its enclosing context. All **13 changed lines** are in hold-only contexts:
  `beginSurfaceHold`, `endSurfaceHold`, the `holdExpiry` runnable after `val h = surfaceHold ?: return@Runnable`, and
  `onDestroy`'s `surfaceHold?.let { h -> … }`. 0 are elsewhere.
- **The callers are guarded:** `beginSurfaceHold` / `endSurfaceHold` are called only inside `surfaceHold?.let`, and
  `holdExpiry` is posted only from `beginSurfaceHold` and from itself.
- **`SurfaceHold.kt`:** its one `SurfaceHold(…)` construction is the activity's lazy, non-null only when
  `debug.privyhub.surface_hold` parses (absent / empty / `0` / junk = null).
- **In a test:** `HoldReportTest.absentTheLossCachesOnceAndTheNextStartPostsItUnchanged`. With no hold, the loss caches
  the report once and the next start posts it unchanged (today's path).
- **B32's own absent test `absentAThreeSecondLossIsTodaysRestart` is unedited and green.**
