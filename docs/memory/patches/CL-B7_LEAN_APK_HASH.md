---
memory_schema: 1
as_of: 2026-10-19
baseline_commit: d3a8ee3
---

# CL-B7 — the CONFIRMED APK hash: CL-B7P's lean-drain flag APK

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-10-19; `handoffs/CL-B7_OPUS_CLIENT_THREADS_AB_TASK.md`;
record `evidence/CL_B7_OPUS_CLIENT_THREADS_AB_2026-10-19.md` §6).

- **The APK:** **`93d29b4a38d224fddbcf261dab72b40f1290f009b7dc506d60eb3104071e1624`** (CL-B7P's build; `adb install -r`
  at 16:56Z, `Success`; read back; the pairing survived). It replaces CL-B5's `043891e1…1607`, kept at
  `PrivyHub/app/build/cl_b7_preserved/app-debug.apk`; the installed one is copied to
  `PrivyHub/app/build/cl_b7_installed/app-debug.apk` (both gitignored).
- **Why CONFIRMED:** the pre-registered rule. All three CL-B7 arms were valid, and arm 2 (the property absent) read as
  today: no `decode_mode` key. The flag-absent path is CL-B5's drain by construction. `debug.privyhub.opus_decode` is
  empty on the onn.
- **The pinned hash** (`evidence/cl_b7_2026-10-19/cl_b7_hash.diff`, `predecessors/`, `predecessor_sha256.txt`,
  `after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK` (+ two comment lines);
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` (+ two comment lines);
  - `tools/test_c3_l4_nft_night.py` `AdoptedApk` expects the new hash.
- **Gates** (`tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK;
  `git diff --check` clean; `--check` ok, CONFIRMED.
- Nothing adopted (the lean flag is not set); nothing committed.
