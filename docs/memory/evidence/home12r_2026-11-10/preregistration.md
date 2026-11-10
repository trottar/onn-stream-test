# HOME-12R — pre-registration (hashed before the user's "Stage 2")

Task: `handoffs/HOME-12R_PARITY_RESUMED_TASK.md`; B's rows: `handoffs/SESSION_B_DONE_2026-11-10AE.md` §"A — HOME-12
resumed", used exactly. APK under test: **`c801caabe6f121d979afa873668b0c48b47d310067cad8ec57cfa8cbdd48582b`** (queue
AE: B84 the cheat picker, B86 the mapping picture, on `de6682db…`'s contents). The CONFIRMED one: `85220f99…` (kept in
`home12r_previous/`). Labels (`LABELS.txt`): **T81** N64, **T82** PS2, **T83** GameCube (HOME-12's), **T85** the PS1
title (new). No title, serial, game id, disc id, code name or path is written in the record.

**The first real run of two screens:** the picker (B84) and the picture (B86) were never drawn by a test. If either
does not open, is cut off, or cannot be driven with the remote and the pad, it is recorded with the user's line as a
finding for B, the sitting carries on with the cells that do not depend on it, and the rule below decides the APK.

## The cells (B's rows)

| cell | the user does | you should see | hub reads (valid) | met |
| --- | --- | --- | --- | --- |
| **C49** the picker on T81 | Launch on Companion → Extras → Cheats → New Cheat Session; reads out whether Launch is at the top and the sections with their numbers; filter → OK → a word; ticks one; Left then OK (or Start) | "Launch Cheat Session · Cancel · 0 selected" at the top; General (135), Player 1 (152), Player 2 (131), Player 3 (87), Player 4 (83), closed; the filter narrows; "1 selected"; Left → OK launches | (stage 1: `clean` true, raw 677, shown 588, hidden trigger 84 / enabler 1 / duplicate 4, the five groups as above; `raw=1` 677, no `clean`) the launch's `cheat_indexes` (count); the session's enabled indexes (count: the pick + 1 "must be on"); the staged file under `cheat_runtime/Mupen64Plus-Next/`; RetroArch's cheat toggles checked (PS1's check: the session verified) | the user's line says usable; the sections read out match the counts; the launch reached in a few presses |
| **C46** that N64 cheat in-game | plays; says whether it works | the cheat's effect | the same launch (C49's) | the user's line (the visible effect); the cheat's name not recorded |
| **C47** a GameCube cheat on T83 | Extras → Cheats → New Cheat Session, ticks the one named (position 8 of 44, General), Launch (Left then OK); END | its effect at a race's start | the game log `GC cheats: 1 enabled`; the user dir's `GameSettings/<id>.ini` written (section names only; none at stage 1); `Dolphin.ini` `EnableCheats = True` for that launch (`False` at stage 1) | the user's line |
| **C48** PS2 widescreen on T82 (B80; the APK's own cell from queue AC) | Launch on Companion → Extras → Patches… → Widescreen → Save → Start Fresh; END | the picture fills the TV from side to side | the details' `ps2_patches` with `ws` on (stage 1: ws / ni / 60 available, none on); the game log `PS2 patches: ws=on …`; the game's settings file `EnableWideScreenPatches = true` (the key only; no file at stage 1). A 60 fps toggle exists there — noted, not scored | the user's line (the picture fills the TV) |
| **C50** the mapping picture | any game → Options → Input Profile → Create New Profile "Test" → Edit Player 1 Mapping; looks; changes one button; Cancel; deletes Test | the outline; Bottom B, Right A, Left Y, Top X; rows "Bottom (✕) → B" …; one change highlighted at once | after the delete, `input_profiles.json` holds no "Test" profile, the profile count as at stage 1 (4) | the user's line says clearer; the profile deleted |
| **PS1 check** T85 | Extras → Cheats → New Cheat Session; the list tidy with Launch at the top; ticks the one named (position 8, Player 1); launches; END | the list; its effect in a fight | `cheat-catalog` for T85 `clean` true (stage 1: one source, 12 shown); the launch's enabled indexes; RetroArch's toggles checked | the list opens; the cheat works (the user's line) |

## Validity

- **Every property empty — twenty** (HOME-12's eighteen + `debug.privyhub.cheat_picker` +
  `debug.privyhub.mapping_picture`), read at the install and at the close; no `setprop`; adb for the install and state
  reads only.
- A cell is valid when the hub's launch is the named label's (the status' game id / its game log, read off the repo),
  the hub reads are taken for that launch, and the user's line is about it. A launch of another title, or a line about
  something else → asked once more in plain words; if still not, the cell is recorded **not valid** with the reason.
- **A step done another way** (another cheat, another button, another path) **is recorded and the readings stay
  independent of it** (HOME-12's precedent). The user's words verbatim. No cell re-scored after its line.
- A screen that does not open / is cut off / cannot be driven → a finding for B with the user's line; the cells that do
  not depend on it go on.
- Nothing adopted, committed, fetched, written to the drive or deleted; no `e3_flag.conf`.

## The CONFIRMED rule (CL-B7 §6)

- **C49, C46, C47, C48 and C50 valid and met, and the PS1 check met, with every property empty (twenty) at the install
  and the close → `c801caab…` CONFIRMED**: the pin moves in the three places (`tools/e1_suite.py` `EXPECT_APK`,
  `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test), the tests green, the patch notes indexed.
- **Otherwise:** `85220f99…` reinstalled from `home12r_previous/`, read back, paired; the user told why in plain words.

## What each cell decides

C49 → **B84** (+ **B85** on N64); C46 → **B78**; C47 → **B79**; C48 → **B80**; C50 → **B86**; the PS1 check → **B85**
on the confirmed path. HOME-12's three requirements close where their cell is met (the picker's button and the list's
clutter: C49; the controller picture: C50).
