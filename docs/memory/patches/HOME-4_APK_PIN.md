---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 9682a38e
---

# HOME-4+ — the CONFIRMED APK hash: queue O's APK

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-11-08;
`handoffs/HOME-4_PLUS_CHOOSER_PS2_VOD_TASK.md`; record `evidence/HOME_4_PLUS_2026-11-08.md`).

- **The APK:** **`cfe0211ca36071901a8be3ea9f77855109cd957c3950903669997d6a0b10a65f`** (queue O: queue N + B46 the
  player chooser + B47 the movie retry default-on; `adb install -r` 2026-11-08 05:31Z, `Success`; read back; the
  pairing survived), copied to `PrivyHub/app/build/home4_installed/app-debug.apk`. It replaces HOME-3's `8ba4d996…`,
  kept at `home3_installed/` (both gitignored).
- **Why CONFIRMED:** the pre-registered rule (CL-B7 §6). Every cell that ran was valid (C7, C9, C8 and its off check,
  C10 (a) / (b) and its off check), and today's behaviours held where a property was `0` (`player_prompt` `0`: no
  chooser and no `players_chosen` / `ports_set` / `pad_claims`; `vod_retry` `0`: no `vod_*` rows and today's error
  path — the status line hidden behind the full-screen player, disclosed). C11 (met) / C12 (not run, the user's
  choice) are PS2 cells: they bear on B50 / G-A14, not on the rule. The eleven properties are empty on the onn.
- **The pinned hash** (`evidence/home4_2026-11-08/pin/home4_pin.diff`, `predecessors/`, `predecessor_sha256.txt`,
  `after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK` (+ three comment lines);
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` (+ two comment lines);
  - `tools/test_c3_l4_nft_night.py` `AdoptedApk` expects the new hash (the test renamed
    `test_the_preflight_expects_the_home4_queue_o_apk`).
- **Gates** (`pin/tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK;
  `tests/ps2_session` 55 passed; `git diff --check` clean; `--check` ok, CONFIRMED, on fifteen lines.
- Nothing adopted (G-A14 not: C12 not met); nothing committed.
