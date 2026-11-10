---
memory_schema: 1
as_of: 2026-11-10
baseline_commit: c514c543
---

# B84 — the cheat picker as PrivyHub's own screen (NOT installed; default on, `debug.privyhub.cheat_picker=0` = today's dialog)

**Result:** `evidence/B84_CHEAT_PICKER_2026-11-10.md`.

- **Apply:** `git apply evidence/b84_2026-11-10/b84.diff` (on `c514c543`), then `b85.diff`, `b86.diff`.
- **Live:** with APK `c801caab…` (pinned at `PrivyHub/app/build/queue_ae_built/`), installed at HOME-12 resumed.
- **Off:** `adb shell setprop debug.privyhub.cheat_picker 0`.
- **Rollback:** `git apply -R` in order (86, 85, 84); `85220f99…` is the APK on the onn.
