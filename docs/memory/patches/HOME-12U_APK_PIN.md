---
memory_schema: 1
as_of: 2026-11-11
baseline_commit: 81ccd731
---

# HOME-12U — the CONFIRMED APK hash: queue AG's APK

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-11-11; `handoffs/HOME-12U_PARITY_FOURTH_TASK.md`;
record `evidence/HOME_12U_PARITY_2026-11-11.md`).

- **The APK:** **`218d9a82d564e0d63e8bc6cd5b8e9de95bddb033e8f6d0635dd870e19f62cd53`** (queue AG: B5 … + B74 + B80's
  client part (PS2 Patches…) + **B84** the cheat picker + **B86 / B89 / B91** the mapping picture, beside the rows; B27 /
  B29 out; `adb install -r` 2026-11-11 05:32Z, `Success`; read back; the pairing survived), copied to
  `PrivyHub/app/build/home12u_installed/app-debug.apk`. It replaces HOME-11's `85220f99…`, kept at
  `home12u_previous/` (both gitignored).
- **Why CONFIRMED:** the pre-registered two-part rule, part (a): C54 (the picker launches a PS1 cheat), C55 (PS2
  Patches… opens with Widescreen ticked; Save answers) and C56 (the mapping picture readable from the couch — "Looks
  almost perfect"; the list's yellow is a new requirement for B, the user's) valid and met with every property empty
  (twenty; no property set this sitting). The hub cells (C46 met, C57 not met) decide hub items only.
- **The pinned hash** (`evidence/home12u_2026-11-11/pin/home12u_pin.diff`, `predecessors/`, `predecessor_sha256.txt`,
  `after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK` (+ three comment lines);
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` (+ two comment lines);
  - `tools/test_c3_l4_nft_night.py` `AdoptedApk` expects the new hash (renamed
    `test_the_preflight_expects_the_home12u_queue_ag_apk`).
- **Gates** (`pin/tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK;
  `tests/client_contract` 5 OK (and `tests/b90_cheat_staged` 10 OK at stage 1); `git diff --check` clean; `--check` ok,
  CONFIRMED on the new pin, eighteen lines.
- Nothing adopted; nothing committed.
