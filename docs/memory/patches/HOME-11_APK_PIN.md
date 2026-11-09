---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 2b5826ea
---

# HOME-11 — the CONFIRMED APK hash: queue AA's APK

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-11-09; `handoffs/HOME-11_DISC_SAFE_TASK.md`;
record `evidence/HOME_11_DISC_SAFE_2026-11-09.md`).

- **The APK:** **`85220f99f92f893968647c185ed98e17456fe9e9bc9cc7bdb550c7c735c04864`** (queue AA: B5 … + B54 + B67 + B70
  + B71 + B72 (a) + **B73** the paused bar fits + **B74** the disc change made safe; B27 / B29 out; `adb install -r`
  2026-11-09 18:56Z, `Success`; read back; the pairing survived), copied to
  `PrivyHub/app/build/home11_installed/app-debug.apk`. It replaces HOME-9's `5f72af4b…`, kept at `home11_previous/`
  (both gitignored).
- **Why CONFIRMED:** the pre-registered rule (CL-B7 §6): C40 (the four buttons whole, END on the screen), C41 (the set
  starts on disc 1 after a sitting left on disc 4; the bar "Disc 1"), C42 (the warning once, the change `ok`, no
  message the second time) and C43 (no pointer, the touchpad inert, SAVE · LOAD · END on one disc) valid and met with
  every property empty (seventeen; no property set this sitting).
- **The pinned hash** (`evidence/home11_2026-11-09/pin/home11_pin.diff`, `predecessors/`, `predecessor_sha256.txt`,
  `after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK` (+ three comment lines);
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` (+ two comment lines);
  - `tools/test_c3_l4_nft_night.py` `AdoptedApk` expects the new hash (renamed
    `test_the_preflight_expects_the_home11_queue_aa_apk`).
- **Gates** (`pin/tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK;
  `tests/b74_disc_safe` 22, `tests/b71_disc_swap` 21, `tests/ps2_session` 93, `tests/n64_session` 28,
  `tests/gamecube_session` 54 passed; `git diff --check` clean; `--check` ok, CONFIRMED, eighteen lines.
- Nothing adopted; nothing committed.
