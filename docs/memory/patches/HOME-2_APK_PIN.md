---
memory_schema: 1
as_of: 2026-11-06
baseline_commit: 1f7a6fd8
---

# HOME-2 — the CONFIRMED APK hash: queue M's APK

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-11-06; `handoffs/HOME-2_HOLD_PADS_VOD_TASK.md`;
record `evidence/HOME_2_HOLD_PADS_VOD_2026-11-03.md`).

- **The APK:** **`0132b94430d40e4e5ae78d2679fbee085f4f44273a804bc0ce8dcd040bdae24f`** (queue M; `adb install -r` at
  16:32Z, `Success`; read back; the pairing survived), copied to `PrivyHub/app/build/home2_installed/app-debug.apk`. It
  replaces CL-B14's `fcd924c2…`, kept at `cl_b14_installed/` (both gitignored).
- **Why CONFIRMED:** the pre-registered rule (CL-B7 §6). C1', C4' and C5' were all valid, and today's behaviours held
  wherever no flag was set; C5' not met bears on G-A13, not on the rule. The ten properties are empty on the onn.
- **The pinned hash** (`evidence/home2_2026-11-03/pin/home2_pin.diff`, `predecessors/`, `predecessor_sha256.txt`,
  `after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK` (+ three comment lines);
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` (+ two comment lines);
  - `tools/test_c3_l4_nft_night.py` `AdoptedApk` expects the new hash (the test renamed
    `test_the_preflight_expects_the_home2_queue_m_apk`).
- **Gates** (`pin/tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK;
  `git diff --check` clean; `--check` ok, CONFIRMED.
- Nothing adopted (every property empty); nothing committed.
