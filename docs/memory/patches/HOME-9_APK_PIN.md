---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 1bf0a76c
---

# HOME-9 — the CONFIRMED APK hash: queue X's APK

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-11-09; `handoffs/HOME-9_GC_TASK.md`; record
`evidence/HOME_9_GC_2026-11-09.md`).

- **The APK:** **`5f72af4b65ebf4bf434668f4ef26c52885be02fb8f5400d63e7b4e548bcdca32`** (queue X: queue T + B67 — the N64
  layout card, "This game supports 2 players", the stored count capped, the start gate's re-arm; `adb install -r`
  2026-11-09 05:42Z, `Success`; read back; the pairing survived), copied to
  `PrivyHub/app/build/home9_installed/app-debug.apk`. It replaces HOME-7's `9aa00ba2…`, kept at `home9_previous/` (both
  gitignored).
- **Why CONFIRMED:** the pre-registered rule (CL-B7 §6): C29 (the card once, gone at the first press, not back) and C31
  ("This game supports 2 players", players 1 / 2, `capable` false `capped_from` 4) valid and met with every property
  empty (twelve; no property set this sitting). Beside it: the card overlaps the details line under it (→ B); the
  re-arm was not exercised (no link drop at a start).
- **The pinned hash** (`evidence/home9_2026-11-09/pin/home9_pin.diff`, `predecessors/`, `predecessor_sha256.txt`,
  `after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK` (+ three comment lines);
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` (+ two comment lines);
  - `tools/test_c3_l4_nft_night.py` `AdoptedApk` expects the new hash (renamed
    `test_the_preflight_expects_the_home9_queue_x_apk`).
- **Gates** (`pin/tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK;
  `tests/ps2_session` 93, `tests/n64_session` 28, `tests/gamecube_session` 54 passed; `git diff --check` clean;
  `--check` CONFIRMED.
- Adopted beside it: G-A16 only (the user's word); nothing committed.
