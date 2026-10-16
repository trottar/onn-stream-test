---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 92e388e
---

# CL-B3 — the CONFIRMED APK hash: G3-S3's hardened identity APK

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-10-16,
`handoffs/G-A1_ADOPTION_AND_CL-B3_TASK.md` §2, as CL-B2 did).

- **What:** the onn's CONFIRMED APK is now G3-S3's debug APK,
  **`59f736d29b96700253a178efa5efd0cd8846858a89d32848a0994586712bf65f`**
  (`adb install -r` at 17:24Z, `Success`; the device read back the same hash).
  - It replaces CL-B2's `77011eef…7d9d`.
  - That APK is kept at `PrivyHub/app/build/g3_s3_preserved/app-debug.apk`
    (gitignored; its sha256 re-read at install time: `77011eef…`).
  - The app's data survived `-r`: the device secret, the pairing (the
    client's device id is in the hub's store) and the settings.
- **The state tools' pinned hash, three edits:**

  | file | predecessor sha256 (16) | after (16) | edit |
  | --- | --- | --- | --- |
  | `tools/e1_suite.py` | `c1afa74184e1cbb1` (G-A1's after) | `3dcc355d740a9f4a` | `EXPECT_APK` (+ two comment lines) |
  | `tools/c3_l4_nft_night.py` | `13e721d215cfe850` | `4ef6005b8c9a08a9` | `ADOPTED_APK_SHA256` (+ two comment lines) |
  | `tools/test_c3_l4_nft_night.py` | `11e5a6779b259347` | `f69e1f5280012800` | `AdoptedApk` expects the new hash |

- **Diff:** `evidence/cl_b3_2026-10-16/cl_b3_hash.diff`. Predecessors are in
  `evidence/cl_b3_2026-10-16/predecessors/`.
- **Validation:**
  - `py_compile` passed;
  - `tools/test_c3_l4_nft_night.py` passed 33 / 33;
  - `tools/e3_state.py` read ok, `apk: CONFIRMED`, seven lines;
  - `git diff --check` was clean.
- **Rollback (written, not applied):**
  1. `adb install -r PrivyHub/app/build/g3_s3_preserved/app-debug.apk`.
  2. Copy the three predecessors back.

  CL-B2's APK signs the v1 canon, which the host still accepts.
- Record: `evidence/CL_B3_HARDENED_APK_LAN_2026-10-16.md`.
