---
memory_schema: 1
as_of: 2026-11-07
baseline_commit: d9fd9688
---

# HOME-3 — the CONFIRMED APK hash: queue N's APK

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-11-06 / 07;
`handoffs/HOME-3_DEFAULTS_PROMPT_VOD_TASK.md`; record `evidence/HOME_3_DEFAULTS_PROMPT_VOD_2026-11-06.md`).

- **The APK:** **`8ba4d996a96c14d01b1e368c20e656f767062d34b17b9308d984b8c43834605f`** (queue N; `adb install -r`
  2026-11-06 23:47Z, `Success`; read back; the pairing survived), copied to
  `PrivyHub/app/build/home3_installed/app-debug.apk`. It replaces HOME-2's `0132b944…`, kept at `home2_installed/`
  (both gitignored).
- **Why CONFIRMED:** the pre-registered rule (CL-B7 §6). Every cell was valid, and today's behaviours held wherever no
  flag was set (B42's defaults aside); C6 not met and C5'' (a)'s two short rows bear on their questions, not on the
  rule. The eleven properties are empty on the onn.
- **The pinned hash** (`evidence/home3_2026-11-06/pin/home3_pin.diff`, `predecessors/`, `predecessor_sha256.txt`,
  `after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK` (+ three comment lines);
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` (+ two comment lines);
  - `tools/test_c3_l4_nft_night.py` `AdoptedApk` expects the new hash (the test renamed
    `test_the_preflight_expects_the_home3_queue_n_apk`).
- **Gates** (`pin/tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK;
  `git diff --check` clean; `--check` ok, CONFIRMED.
- Nothing adopted (every property empty); nothing committed.
