---
memory_schema: 1
as_of: 2026-11-10
baseline_commit: 051bb4d0
---

# B89 — the mapping picture redrawn and smaller (NOT installed; `debug.privyhub.mapping_picture=0` = today's editor)

**Result:** `evidence/B89_MAPPING_PICTURE_REDRAWN_2026-11-10.md`.

- **Apply:** `git apply evidence/b89_2026-11-10/b89.diff` (after `b88.diff`).
- **Live:** with APK `3f21e2c6aa8caa517b0a76b69701b853ada890a99dbde3295b62551f34e223b1` (pinned at `PrivyHub/app/build/queue_af_built/`), installed at HOME-12's third sitting.
- **Off:** `adb shell setprop debug.privyhub.mapping_picture 0`.
- **Rollback:** `git apply -R` in order (89, 88, 87).
