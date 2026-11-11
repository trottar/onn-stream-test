# HOME-12T — pre-registration (written and hashed at stage 1, before any cell's data)

Source of the rows: `handoffs/SESSION_B_DONE_2026-11-10AF.md` §"A — HOME-12, the third sitting" (B's words, used as written);
the task `handoffs/HOME-12T_PARITY_THIRD_TASK.md`. T-labels in `LABELS.txt`. The APK under test:
`3f21e2c6aa8caa517b0a76b69701b853ada890a99dbde3295b62551f34e223b1` (queue AF); the predecessor
`85220f99f92f893968647c185ed98e17456fe9e9bc9cc7bdb550c7c735c04864` preserved in `home12t_previous/`.

## The CONFIRMED rule, in two parts

- **(a) The APK** `3f21e2c6…` is **CONFIRMED on its own cells**: **C51**, **C52** and **C53** valid and met, with every
  property empty (the twenty, read at the start and the close) → the pin moves in the three places
  (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test; green; the patch
  notes indexed). **Any of the three not met (or not valid) → `85220f99…` reinstalled from `home12t_previous/`, read
  back, paired, the user told why.**
- **(b) Hub-side cells decide hub items only:** **C46** (the N64 cheat seen in-game) decides **B87**; met or not, it
  **does not roll the APK back**. C52's hub half (the POST → 200, stored, applied) decides **B88**.

## The cells

| cell | the user does (B's reply) | you should see | hub read | met |
| --- | --- | --- | --- | --- |
| **C51** T85, the APK's cell (picker launches a PS1 cheat) | Launch on Companion → Extras → Cheats → New Cheat Session; tick the one cheat named (position 8, Player 1); Start on the pad; END | the game starts; the cheat's effect in a fight | the launch → 200 in the journal; RetroArch's log: `Load game-specific cheatfile`, the picked index `on`; `activation_verified` true | the user's line: it starts and the cheat works |
| **C52** T82, the APK's cell + B88 | Launch on Companion → Extras → Patches…, tick Widescreen, Save; read the bottom line; Start Fresh; END | "Saved — used the next time this game starts"; the game in widescreen | `POST /plugins/games/ps2-patches?…ws=1 → 200` in the journal; `details`' `ps2_patches.on` holds `ws`; the game log `PS2 patches: ws=on …`; the game's settings file `EnableWideScreenPatches = true` (the key only) | the user's two lines: the saved message; the picture fills the TV side to side |
| **C53** T86's profile, the APK's cell (B89) | Options → Input Profile → own profile → Edit Player 1 Mapping; look at the picture; change nothing; Cancel | a small controller at the top (about a fifth of the screen), the rows below it; the profile's changed buttons in yellow | the profiles file's bytes before = after (sha256) | the user's line: size and drawing acceptable **and the labels readable from the couch**; "too small to read" → **not met** (the size rule's finding for B) |
| **C46** T81, the hub's cell → B87 only | Extras → Cheats → New Cheat Session; tick the cheat named (Player 1, found by the filter); Start; END | the game starts; the cheat's effect in a fight (or "cheats not ready" on the TV) | RetroArch's log: `Load game-specific cheatfile` present, then `Cheat #` lines, the picked index on; `activation_verified` true; the staged folder held two files (counts only) | the user's line (the effect seen). Not met → B87 not confirmed; the APK's verdict unchanged. On "cheats not ready": the log's order recorded (the cheat-file line yes / no; the first answered pulse's time after PLAYING) |

## Validity rules

- A cell is **valid** only with the APK `3f21e2c6…` read back on the onn at its stage and every one of the twenty
  properties empty (read at stage 1 after the install and at the close; no `setprop` anywhere in this sitting).
- The hub as at stage 1: eighteen `PRIVYHUB_` lines, `--check` ok apart from the APK line (MISMATCH expected while
  `3f21e2c6…` is on the onn and the pin is `85220f99…`), no `e3_flag.conf`, `PRIVYHUB_CHEAT_READY` absent (B87 on).
- The user's pads on the onn (Bluetooth), nothing asked on the hub. The user's line decides "met"; the hub read
  corroborates and is recorded either way. A hub read that contradicts a "met" line is recorded and decides nothing on
  its own for the APK cells.
- A cell the user cannot run (a fault outside the cell's item) is **not valid**, not met; for (a) a not-valid APK
  cell counts as not met.
- Not decided here: anything beyond C51 / C52 / C53 / C46.
