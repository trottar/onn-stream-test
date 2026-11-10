---
memory_schema: 1
as_of: 2026-11-10
baseline_commit: c514c543
---

# B86 — the mapping editor's controller picture and one set of letters (NOT installed; default on, `debug.privyhub.mapping_picture=0` = today's editor)

**Result:** `evidence/B86_MAPPING_PICTURE_2026-11-10.md` (the APK's files there too).

- **Apply:** `git apply evidence/b86_2026-11-10/b86.diff`, after `b85.diff`.
- **Live:** with APK `c801caabe6f121d979afa873668b0c48b47d310067cad8ec57cfa8cbdd48582b`, installed at HOME-12 resumed.
- **Off:** `adb shell setprop debug.privyhub.mapping_picture 0`.
- **Display only:** no stored mapping changes.
- **Rollback:** `git apply -R` in order (86, 85, 84).
