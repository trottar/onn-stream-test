---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 32abb425
---

# HOME-7 — the CONFIRMED APK hash: queue T's APK

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-11-08;
`handoffs/HOME-7_JOIN_PS2_N64_TASK.md`; record `evidence/HOME_7_HOLD_TO_JOIN_N64_2026-11-08.md`).

- **The APK:** **`9aa00ba2afe19a7f36b869454d7d5e683185dc97fc116cc6f8f75878bc5fe73f`** (queue T: queue O + B54
  hold-to-join and the multitap at once; `adb install -r` 2026-11-08 21:55Z, `Success`; read back; the pairing survived),
  copied to `PrivyHub/app/build/home7_installed/app-debug.apk`. It replaces HOME-4+'s `cfe0211c…`, kept at
  `home7_previous/` (both gitignored).
- **Why CONFIRMED:** the pre-registered rule (CL-B7 §6): C15, C16 and C17 valid and met with every property empty (no
  property was set this sitting). **Disclosed beside it:** after C17's switch to four ports, player 2 no longer works on
  that title (it reads player 2 from port 2 when the multitap is in), and the title's stored count now starts it with
  the multitap every time — to B; C17's met row (the game resumed at the save point with four ports) held. C18 / C20
  (PS2) and C21-C23 (N64) bear on B55 / B57 / G-A15, not on the rule.
- **The pinned hash** (`evidence/home7_2026-11-08/pin/home7_pin.diff`, `predecessors/`, `predecessor_sha256.txt`,
  `after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK` (+ three comment lines);
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` (+ two comment lines);
  - `tools/test_c3_l4_nft_night.py` `AdoptedApk` expects the new hash (renamed
    `test_the_preflight_expects_the_home7_queue_t_apk`).
- **Gates** (`pin/tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK;
  `tests/ps2_session` 93, `tests/n64_session` 28 passed; `git diff --check` clean; `--check` ok, CONFIRMED, on seventeen.
- Adopted beside it: G-A15 only (the user's word); nothing committed.
