---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 3107fb5
---

# CL-B2 — the CONFIRMED APK hash: G3-S2's identity APK

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A,
2026-10-16, under `QUEUE_2026-10-16`, as E3 / E4 changed the state tools).

- **What:** the onn's CONFIRMED APK is now G3-S2's debug APK,
  **`77011eefa538fb965e46ad1f25ddac99036e1d77557ba7b7a677dc5947807d9d`**
  (`adb install -r`; the device read back the same hash).
  - It replaces CL-B1's `de072762…835e`.
  - That APK is kept at `PrivyHub/app/build/g3_s2_preserved/app-debug.apk`
    (gitignored).
- **The state tools' pinned hash, three edits:**

  | file | predecessor sha256 (16) | after (16) | edit |
  | --- | --- | --- | --- |
  | `tools/e1_suite.py` | `07b568753f95e509` | `602d76964185cc22` | `EXPECT_APK` (+ one comment line) |
  | `tools/c3_l4_nft_night.py` | `5ac71eb4a1c7f08a` | `13e721d215cfe850` | `ADOPTED_APK_SHA256` (+ two comment lines) |
  | `tools/test_c3_l4_nft_night.py` | `2f064539f3a02ce8` | `11e5a6779b259347` | `AdoptedApk` expects the new hash |

- **Diff:** `evidence/cl_b2_2026-10-16/cl_b2_hash.diff`. Predecessors are in
  `evidence/cl_b2_2026-10-16/predecessors/`.
- **Validation:**
  - `py_compile` passed;
  - `tools/test_c3_l4_nft_night.py` passed 33 / 33;
  - `tools/e3_state.py` read ok, `apk: CONFIRMED`, five lines;
  - `git diff --check` was clean.
- **Not edited:** the evidence copies of older night scripts (history, as
  CL-B1 noted).
- **Rollback:**
  1. `adb install -r PrivyHub/app/build/g3_s2_preserved/app-debug.apk`.
  2. Copy the three predecessors back.

  It was written, not applied. The adoption is the user's.
- Record: `evidence/CL_B2_IDENTITY_APK_AND_LAN_SMOKE_2026-10-16.md`.
