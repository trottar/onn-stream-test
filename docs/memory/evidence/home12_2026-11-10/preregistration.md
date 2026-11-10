# HOME-12 — pre-registration (hashed before the user's "Stage 2")

Task: `handoffs/HOME-12_PARITY_TASK.md`; B's rows: `handoffs/SESSION_B_DONE_2026-11-09AC.md` §"A — HOME-12" (with
`_2026-11-10AD.md` §"A — HOME-12": B83 changed no cell) and the handoff's changes from ART-1R. APK under test:
**`de6682dbaf00237c2f6477b68df4fa00e320c0a403ccb2d28863344dee86de28`** (queue AC; B80's client part). The previous
CONFIRMED: `85220f99…` (kept in `home12_previous/`). Labels (`LABELS.txt`): **T81** the N64 title (C46), **T82** the
PS2 title (C45, C48), **T83** the GameCube title (C45, C47); the other PS2 game in C45 is the user's choice and gets
**T84** when its launch is read. No title, serial, game id, disc id, code name or path is written in the record.

## The cells (B's rows, with the handoff's changes)

| cell | the user does | hub reads (valid) | met |
| --- | --- | --- | --- |
| **C44** art / details | Games → N64: a few titles, one title's details; PS2 and GameCube: a look | the `details` of T81 / T82 / T83 carry `box_art_available` true (read at stage 1: true / true / true); T81's year, genre, players present (read at stage 1: a year, a genre, 4 players) | **the user's line per system:** N64 shows box art and the details show a year, a genre and players; PS2 and GameCube show box art on most titles. **Year / genre / players expected on N64 only** (RetroArch's database has none for PS2 / GameCube); a title among the misses (PS2 15, GameCube 3) showing no art is expected, not a fault |
| **C45** an Input Profile "Swap" (bottom ↔ right face buttons, Player 1) on T82 and T83; then another PS2 game | create, edit, save, Assign to This Game on T82; Start Fresh; the bottom button acts as the right one; END; the same profile assigned on T83; then another PS2 game (T84) | T82's game log `PS2 input profile: assigned overrides=1`, T83's `GC input profile: assigned overrides=1`, T84's `default overrides=0`; during T82's launch PCSX2's `[Pad1]` `Cross` / `Circle` read swapped (FaceEast / FaceSouth; at stage 1 FaceSouth / FaceEast); during T83's GCPadNew `GCPad1` `Buttons/A` / `Buttons/X` swapped (EAST / SOUTH; at stage 1 SOUTH / EAST); during T84's the stage-1 bindings | **the user's lines:** the swap acts swapped on T82 and on T83, and T84's buttons work as normal |
| **C46** an N64 cheat seen | T81 → Launch on Companion → Extras → Cheats → New Cheat Session, tick the cheat named (position 38 of 677, a single constant write; its visible effect: player 1's damage percent stays at 0 % in a match), Launch Cheat Session; END | the staged file under `cheat_runtime/Mupen64Plus-Next/` (one list, the ticked index enabled); RetroArch's cheat toggle verified (PS1's verification: the session's `activation_verified` / the toggle read back on); then the three drop-in folders (PS1, SNES, PS2) **present and empty** (absent at stage 1; made at the first Cheats list) | **the user's line:** the effect seen |
| **C47** a GameCube cheat from Dolphin's list | T83 → Extras → Cheats → New Cheat Session, tick the code named (position 8 of 44, an Action Replay code; its effect visible at a race's start), Launch Cheat Session; END | the game log `GC cheats: 1 enabled`; the user dir's `GameSettings/<id>.ini` written (section names only; absent at stage 1); `Dolphin.ini` `EnableCheats = True` for that launch; `False` at a plain launch — read at C45's T83 launch (before) and at the next plain launch if one happens in the sitting; if none follows, the file is left `True` until the next launch rewrites it (disclosed, not scored) | **the user's line:** the code works |
| **C48** PS2 widescreen (the APK's own cell) | T82 → Launch on Companion → Extras → Patches… → tick Widescreen → Save; Start Fresh; END | the details' `ps2_patches` for T82 with `ws` on (at stage 1: available ws / ni / 60, on none); the game log `PS2 patches: ws=on …`; the game's settings file `EnableWideScreenPatches = true` (the key only); a note: T82 offers a 60 fps toggle (offered, not scored) | **the user's line:** the picture fills the TV from side to side |

## Validity

- **Every property empty — eighteen** (HOME-11's seventeen + `debug.privyhub.ps2_patches`), read at the install and at
  the close; no `setprop`; adb for the install and state reads only.
- A cell is valid when the hub's launch is the named label's (its game log / the status' game id, read off the repo),
  the hub reads above are taken for that launch, and the user's line is about that game. A launch of another title, or
  the user's line about something else, → asked once more in plain words; if still not, the cell is recorded **not
  valid** with the reason.
- The user's words are recorded verbatim. A step done another way (another button, another path) is recorded and the
  readings stay independent of it. No cell is re-scored after its line.
- Nothing adopted, nothing committed, nothing fetched, nothing written to the drive, nothing deleted; no `e3_flag.conf`.

## The CONFIRMED rule (CL-B7 §6)

- **C44, C45, C46, C47 and C48 valid and met, with every property empty (eighteen) at the install and the close →
  `de6682db…` CONFIRMED**: the pin moves in the three places (`tools/e1_suite.py` `EXPECT_APK`,
  `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test), the tests green, the patch notes indexed
  (`patches/PATCH_INDEX.md`).
- **Otherwise:** `85220f99…` reinstalled from `home12_previous/`, read back, paired; the user told why.

## What each cell decides

C44 → **B76** (art + details for N64 / PS2 / GameCube); C45 → **B77** (Input Profiles on PS2 / GameCube); C46 →
**B78** (N64 cheats); C47 → **B79** (GameCube cheats from Dolphin's list); C48 → **B80** (PS2 patches; the APK's own
cell); the drop-in folders read in C46 → **B81**. A cell not met leaves its item "built, not confirmed at the TV" with
the reason; the APK's verdict follows the rule above.
