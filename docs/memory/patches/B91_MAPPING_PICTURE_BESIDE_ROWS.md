---
memory_schema: 1
as_of: 2026-11-11
baseline_commit: d1df1f86
---

# B91 — the mapping picture beside the rows, its labels at the rows' text size (NOT installed; `debug.privyhub.mapping_picture=0` = today's editor)

**Result:** `evidence/B91_MAPPING_PICTURE_BESIDE_ROWS_2026-11-11.md`.

- **Apply:** `git apply evidence/b91_2026-11-11/b91.diff` (on `d1df1f86`; client only).
- **Live:** with an APK carrying it — the queue's APK (`evidence/b91_2026-11-11/apk_sha256.txt`), pinned, NOT installed.
- **Off:** `adb shell setprop debug.privyhub.mapping_picture 0` (B86's gate: no picture, today's editor).
- **Rollback:** `git apply -R evidence/b91_2026-11-11/b91.diff`; the confirmed APK (`85220f99…`) stays on the onn until
  A's sitting decides.
