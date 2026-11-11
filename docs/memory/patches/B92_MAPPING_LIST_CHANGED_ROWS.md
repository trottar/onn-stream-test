---
memory_schema: 1
as_of: 2026-11-11
baseline_commit: af063475
---

# B92 — the mapping list's changed rows yellow (NOT installed; `debug.privyhub.mapping_picture=0` = today's editor)

**Result:** `evidence/B92_MAPPING_LIST_CHANGED_ROWS_2026-11-11.md`.

- **Apply:** `git apply evidence/b92_2026-11-11/b92.diff` (on `af063475`; client only).
- **Live:** with the APK `ca53df0d…` (`PrivyHub/app/build/queue_ah_built/`), pinned, NOT installed.
- **Off:** the property `0` (B86's gate).
- **Rollback:** `git apply -R evidence/b92_2026-11-11/b92.diff`; `218d9a82…` stays CONFIRMED until A's check decides.
