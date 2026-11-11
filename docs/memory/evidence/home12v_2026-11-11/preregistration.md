# HOME-12V — pre-registration (written and hashed at stage 1, before any cell's data)

Source of the rows: `handoffs/SESSION_B_DONE_2026-11-11AH.md` §"A — HOME-12V, a short check" (B's words, used as
written) with the task's additions (`handoffs/HOME-12V_LIST_YELLOW_SNES_TASK.md`). T-labels in `LABELS.txt`. The APK
under test: `ca53df0dac787607af749492393b5f343e3df775cd4581d44342a1a81ecd590d` (queue AH, B92); the predecessor
`218d9a82d564e0d63e8bc6cd5b8e9de95bddb033e8f6d0635dd870e19f62cd53` (CONFIRMED at HOME-12U) preserved in
`home12v_previous/`.

## The CONFIRMED rule, in two parts

- **(a) The APK** `ca53df0d…` is **CONFIRMED on its own cell**: **C58** valid and met, with every property empty (the
  twenty, read at the start and the close) → the pin moves in the three places (`tools/e1_suite.py` `EXPECT_APK`,
  `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test; green; B92's patch note indexed). **C58 not met (or not
  valid) → `218d9a82…` reinstalled from `home12v_previous/`, read back, paired, the user told why.**
- **(b) The hub cell C59** (an SNES cheat from the list that matches the game file, seen in-game) decides **B90's SNES
  part only**; met or not, it **does not roll the APK back**.
- **The optional H7 step** (the user's word after C59: "skip" or a game) **carries no verdict** and changes nothing on
  the hub: a save state the user makes through SAVE, read for its existence, size and time; nothing run with B93's
  tool; the state not copied or changed.

## The cells

| cell | the user does | you should see | hub read | met |
| --- | --- | --- | --- | --- |
| **C58** T86's profile, the APK's cell (B92) | Options → Input Profile → own profile → Edit Player 1 Mapping; compare the picture's yellow buttons with the list; change nothing; Back; END | the picture's yellow buttons, and the list's rows for those buttons yellow too | the profiles file's bytes before = after (sha256) | the user's line: yes, the same rows yellow in the list |
| **C59** T87, the hub's cell → B90's SNES part | Extras → Cheats → New Cheat Session; the list named (the one matching the game file); tick the cheat named; Start; END | the game starts; the cheat's effect plain on screen | RetroArch's log: the cheat-file line from snes9x's folder, `Applying cheat changes.`; `activation_mode` "staged", `activation_verified` true (RetroArch's flag, not the core's); the launch's seconds; no `launch_orphaned`; the code's form (RAM / ROM; the spelling) | **the user's line alone** (the effect seen). Not met → B90's SNES part stays not confirmed; nothing else changes |

## Stage-1 reads (recorded, not gates)

- Queue AH's commit touches nothing under `companion/` → no companion restart.
- The stray-RetroArch read: RetroArch processes with no game active = 0.
- T87's pick: the matching list (third source), position 12, Pro Action Replay RAM, two lines — a form B92's bench
  covered (Game Genie avoided).
- This sitting's watcher calls `active-cheats` with POST only; the record states the count of `GET active-cheats` rows
  in the journal during the sitting (expected 0).

## Validity rules

- A cell is **valid** only with the APK `ca53df0d…` read back on the onn at its stage and every one of the twenty
  properties empty (read at stage 1 after the install and at the close; no `setprop` anywhere in this sitting).
- The hub as at stage 1: eighteen `PRIVYHUB_` lines, `--check` ok apart from the APK line (MISMATCH expected while
  `ca53df0d…` is on the onn and the pin is `218d9a82…`), no `e3_flag.conf`.
- The user's pads on the onn (Bluetooth), nothing asked on the hub. The user's line decides; the hub reads are recorded
  either way.
- A cell the user cannot run (a fault outside the cell's item) is **not valid**, not met; for (a) a not-valid C58 counts
  as not met.
- Not decided here: anything beyond C58 / C59.
