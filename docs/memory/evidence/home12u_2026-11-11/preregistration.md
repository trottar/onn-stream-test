# HOME-12U — pre-registration (written and hashed at stage 1, before any cell's data)

Source of the rows: `handoffs/SESSION_B_DONE_2026-11-11AG.md` §"A — HOME-12, the fourth sitting" (B's words, used as
written) and the task `handoffs/HOME-12U_PARITY_FOURTH_TASK.md` (its two additions: C57, the 60-second read). T-labels in
`LABELS.txt`. The APK under test: `218d9a82d564e0d63e8bc6cd5b8e9de95bddb033e8f6d0635dd870e19f62cd53` (queue AG); the
predecessor `85220f99f92f893968647c185ed98e17456fe9e9bc9cc7bdb550c7c735c04864` preserved in `home12u_previous/`.

## The CONFIRMED rule, in two parts

- **(a) The APK** `218d9a82…` is **CONFIRMED on its own cells**: **C54**, **C55** and **C56** valid and met, with every
  property empty (the twenty, read at the start and the close) → the pin moves in the three places
  (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test; green; the patch
  notes indexed: B80's client part, B84, B86, B89, B91). **Any of the three not met (or not valid) → `85220f99…`
  reinstalled from `home12u_previous/`, read back, paired, the user told why.**
- **(b) The hub cells decide hub items only and do NOT roll the APK back:** **C46** (the N64 cheat seen in-game inside
  the onn's wait, the launch's seconds recorded) decides **B90 / B87**; **C57** (an SNES cheat seen in-game) decides
  **B90's SNES folder** (met, not met or not run).

## The cells

| cell | the user does | you should see | hub read | met |
| --- | --- | --- | --- | --- |
| **C54** T85, the APK's cell | Launch on Companion → Extras → Cheats → New Cheat Session; tick the one cheat named (k = 1); Start on the pad; END | the game starts; the cheat's effect in a fight | the launch → 200; RetroArch's log: the cheat-file line, then `Applying cheat changes.`; `activation_mode` "staged", `activation_verified` true, `activation_pulses` ≤ 2k + 4 = 6; no `launch_orphaned` row | the user's line: it starts and the cheat works |
| **C55** T82, the APK's cell | Launch on Companion → Extras → Patches…; is Widescreen already ticked; Save; read the bottom line; END | Widescreen already ticked; "Saved — used the next time this game starts" | `POST /plugins/games/ps2-patches?…ws=1 → 200` in the journal; `details`' `ps2_patches.on` holds `ws`; no game starts | the user's two lines: ticked; the saved message |
| **C56** T86's profile, the APK's cell (B91) | Options → Input Profile → own profile → Edit Player 1 Mapping; the picture on the left, the list on the right; change nothing; Back | the controller on the left half, its letters the size of the list's words; changed buttons in yellow; the list scrolls, the picture stays | the profiles file's bytes before = after (sha256) | **the user's line: readable from the couch** (anything said about crowded / overlapping letters recorded verbatim) |
| **C46** T81, the hub's cell → B90 / B87 only | Extras → Cheats → New Cheat Session; tick the cheat named (k = 2 with its "must be on" code); Start; END; about how long "Launching" showed | the game starts within the onn's wait; the cheat's effect in a fight | RetroArch's log: `Load game-specific cheatfile`, then `Applying cheat changes.`; `activation_mode` "staged", `activation_verified` true, `activation_pulses` ≤ 2k + 4 = 8; **the launch's seconds** (the request's arrival to its 200) recorded, inside 60 s; no `launch_orphaned` row; the staged folder held 2 files, each `staged_entries` long (counts only) | the user's line (the effect seen) **and** the 200 inside 60 s. Not met → B90 not confirmed; the APK's verdict unchanged. A `launch_orphaned` row → its reason and seconds recorded, and the status read showing no game |
| **C57** T87, the hub's cell → B90's SNES folder only | Extras → Cheats → New Cheat Session; tick the cheat named (k = 1); Start; END | the game starts; the cheat's effect on touching an enemy | RetroArch's log: the cheat-file line (read from the folder snes9x uses), `Applying cheat changes.`; `activation_mode` "staged", `activation_verified` true; the launch's seconds | the user's line (the effect seen). Not met → B90's SNES part not confirmed; nothing else changes |

## Stage-1 reads (recorded, not gates)

- B90: `PRIVYHUB_CHEAT_STAGED` count 0; `tests/b90_cheat_staged` 10 OK; the dry call for T81 and C46's cheat:
  `staged_entries` = `real_indexes` = 2, `enabled_true` 2, `enabled_false` 0, `pulses_bound` 8.
- The 60-second rule's read (`stage1/sixty_second_read.json`): no launch without cheats at 45 s or more on any system.

## Validity rules

- A cell is **valid** only with the APK `218d9a82…` read back on the onn at its stage and every one of the twenty
  properties empty (read at stage 1 after the install and at the close; no `setprop` anywhere in this sitting).
- The hub as at stage 1: eighteen `PRIVYHUB_` lines, `--check` ok apart from the APK line (MISMATCH expected while
  `218d9a82…` is on the onn and the pin is `85220f99…`), no `e3_flag.conf`, `PRIVYHUB_CHEAT_STAGED` absent (B90 on).
- The user's pads on the onn (Bluetooth), nothing asked on the hub. The user's line decides "met"; the hub read
  corroborates and is recorded either way; for C46 the 200 inside 60 s is also required.
- A user's pick other than the cheat named is valid for C46 / C57 (the cell asks for a cheat of that title seen
  in-game); its k and bound are taken from the launch's real indexes.
- A cell the user cannot run (a fault outside the cell's item) is **not valid**, not met; for (a) a not-valid APK cell
  counts as not met.
- Not decided here: anything beyond C54 / C55 / C56 / C46 / C57.
