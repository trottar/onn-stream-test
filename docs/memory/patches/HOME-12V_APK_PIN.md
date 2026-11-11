---
memory_schema: 1
as_of: 2026-11-11
baseline_commit: 6595152b
---

# HOME-12V — the CONFIRMED APK hash: queue AH's APK

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-11-11; `handoffs/HOME-12V_LIST_YELLOW_SNES_TASK.md`;
record `evidence/HOME_12V_PARITY_2026-11-11.md`).

- **The APK:** **`ca53df0dac787607af749492393b5f343e3df775cd4581d44342a1a81ecd590d`** (queue AH: queue AG's
  `218d9a82…` + **B92** the changed buttons' rows yellow in the mapping list; `adb install -r` 2026-11-11 07:33Z,
  `Success`; read back; the pairing survived), copied to `PrivyHub/app/build/home12v_installed/app-debug.apk`. It
  replaces HOME-12U's `218d9a82…`, kept at `home12v_previous/` (both gitignored).
- **Why CONFIRMED:** the pre-registered two-part rule, part (a): C58 (the same rows yellow in the list as on the picture;
  "Looks great") valid and met with every property empty (twenty; no property set this sitting). The hub cell C59 (met)
  decides B90's SNES part only.
- **The pinned hash** (`evidence/home12v_2026-11-11/pin/home12v_pin.diff`, `predecessors/`, `predecessor_sha256.txt`,
  `after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK` (+ three comment lines);
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` (+ two comment lines);
  - `tools/test_c3_l4_nft_night.py` `AdoptedApk` expects the new hash (renamed
    `test_the_preflight_expects_the_home12v_queue_ah_apk`).
- **Gates** (`pin/tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK;
  `tests/client_contract` 5 OK; `git diff --check` clean; `--check` ok, CONFIRMED on the new pin, eighteen lines.
- Nothing adopted; nothing committed.
