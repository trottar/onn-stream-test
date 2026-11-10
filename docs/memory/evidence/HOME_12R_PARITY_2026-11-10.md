---
memory_schema: 1
as_of: 2026-11-10
status: HOME-12R DONE (session A; stage 1 2026-11-10 21:55-21:59Z unattended; the cells 22:00-22:20Z with the user at the TV; the close 22:20Z-). APK c801caab… installed with every property empty (twenty); C49 the picker MET (its first real run), C46 NOT RUN (the N64 cheat launch failed on the hub — RetroArch not yet holding the cheat file when the hub toggled), C47 GameCube cheat MET, C48 PS2 widescreen NOT MET (the client's Save is a POST the hub only accepts as GET), C50 the mapping picture MET (finding: "big poorly drawn"), the PS1 check MET → **c801caab… NOT CONFIRMED; 85220f99… reinstalled**. Nothing adopted; nothing committed
---

# HOME-12R — HOME-12 resumed: the picker, the cleaned lists, the picture

Task: `handoffs/HOME-12R_PARITY_RESUMED_TASK.md`; B's rows: `handoffs/SESSION_B_DONE_2026-11-10AE.md` §"A — HOME-12
resumed". The directory is `home12r_2026-11-10/`: `stage1/`, `c49/`, `c46/`, `c47/`, `c48/`, `c50/`, `ps1/`,
`close/`, `preregistration.md` and its `.sha256`, `LABELS.txt`, `props20.sh`, `drive_listing.py`, `title_check.*`,
`redact_check.txt`, `manifest.sha256`. Times are UTC. **T-labels** (`LABELS.txt`): T81 N64, T82 PS2, T83 GameCube
(HOME-12's); **T85** the PS1 title; **T86** a PS2 title of the user's own choosing (C50). No title, serial, game id,
code name or path is written; the name the user gave their new profile is withheld (it carries a game's name).

## The user's lines (verbatim)

- Stage 1: "Read _cowork_prompt.txt in the repo root and follow it as my prompt."
- C49: "Yes" / "General then player 1-4" / "Filter works as expected , left goes to top" / "Launched failed retroarch
  did not report cheat-index navigation state" / "Stage 2"; later "And yes the numbers followed as such".
- C47: "Stage 4" / "Cheat worked".
- C48: "Patches was selected and widescreen but launch failed with unknown games plugin post action: ps2-patches" /
  "Stage 5".
- C50: "1. It's a big poorly drawn controller at the top." / "2. Yes" / "3. I made specific controls for a game. But
  yes they become yellow" / "4. Much clearer" / "5. I loaded a game and the new controls work great" / "Stage 6".
- The PS1 check: "1. Yes" / "2. Okay (filter worked)" / "3. Cheat works" / "4. Player one was invincible and player 2
  was not. Game ended successfully".

## Stage 1 (`home12r_2026-11-10/stage1/STAGE1.md`)

HEAD `0de0b290` (queue AE `5cfe4c01` committed), the tree clean; `/tmp` 5.5 GB; eighteen lines, `--check` ok;
`85220f99…` CONFIRMED read back; the twenty properties empty; the two units. **The companion restart 21:56:11Z** (B85
live): eighteen lines, `--check` ok, the journal clean (33 lines, 0 error / warning), the keeper not restarted. **T81's
`cheat-catalog` exactly as B's rows:** `clean` true, raw 677, shown 588, hidden trigger 84 / enabler 1 / duplicate 4,
General 135 / Player 1 152 / Player 2 131 / Player 3 87 / Player 4 83; `raw=1` 677 with no `clean`. **The install
21:56Z:** `85220f99…` preserved in `home12r_previous/`; **`c801caabe6f121d979afa873668b0c48b47d310067cad8ec57cfa8cbdd48582b`**
in `home12r_installed/`, the signer `455bde4e…` the same, `apksigner verify` OK, `adb install -r` Success, read back,
paired, identity v2; the twenty properties empty. T85 chosen (one cleaned list of 12). Pre-registration hashed
21:58:01Z (`e13bfc34…`).

## The cells

| cell | read | result |
| --- | --- | --- |
| **C49** the picker on T81 (`c49/`) | **The picker's first real run worked:** Launch at the top, General then Player 1-4 with the hub's counts ("yes the numbers followed as such"), the filter, Left to the top. **The launch failed, hub side:** 503 "RetroArch did not report cheat-index navigation state"; RetroArch's log has no `[Cheats]` line at all (no cheat file loaded, no "Cheat #n"); the network command interface came up before the N64 core finished loading; content ran 0 s. A's reading (not proven): the hub's readiness wait answers before RetroArch loads the cheat file on the slower N64 core | **picker MET (B84; B85's sections on N64); the N64 cheat launch NOT MET** |
| **C46** the N64 cheat in-game (`c46/`) | no session formed | **NOT RUN → B78 not confirmed** |
| **C47** a GameCube cheat via the picker, T83 (`c47/`) | `GC cheats: 1 enabled`; `GameSettings/<id>.ini` written (`ActionReplay_Enabled`); `EnableCheats = True` for that launch; "Cheat worked" | **MET → B79** |
| **C48** PS2 widescreen, T82 (`c48/`) | the client's Patches… → Save sent **`POST ps2-patches`** → **400**: the hub handles `ps2-patches` only on its GET path ("Unknown Games plugin POST action"); B80's and B83's tests call the GET handler directly. No toggle saved, no launch | **NOT MET → B80 not confirmed** (a client / hub contract defect, present since queue AC) |
| **C50** the mapping picture (`c50/`) | B on the bottom / A on the right and the rows "Yes"; a change lights yellow; **"Much clearer"**; finding: **"a big poorly drawn controller"**. Done the user's way: a real profile for T86 instead of "Test", kept; T86 launched with it (`PS2 input profile: assigned overrides=1`, PCSX2 `[Pad1]` remapped live), "the new controls work great". No "Test" profile | **MET → B86** (finding for B) |
| **PS1 check** T85 (`ps1/`) | `clean` true; one index launched; RetroArch "Load game-specific cheatfile", the pick toggled on and read back on; `activation_verified` true; "Player one was invincible and player 2 was not" | **MET → B85 on the confirmed path** |

## What it decided

- **The CONFIRMED rule (CL-B7 §6):** C46 not run and C48 not met → **`c801caab…` NOT CONFIRMED.** `85220f99…`
  reinstalled from `home12r_previous/` (22:21Z), read back, paired; every property empty (twenty, with each APK on).
  The pin stays; nothing indexed. The user told why in plain words (the reply).
- **The items:** B84 met (the picker); B85 met (N64 sections; the PS1 path); B79 met (now through the picker); B86 met
  (with the drawing finding); **B78 not met** (the N64 cheat launch); **B80 not met** (POST vs GET).
- **HOME-12's three requirements:** the picker's button and the list's clutter — **met at the TV** (C49), but they
  ship only in the unconfirmed APK; the controller picture — **met** (C50), same.
- **For B (the next queue, three items):**
  1. **The N64 cheat launch:** the hub must not send `CHEAT_INDEX_PLUS` before RetroArch has loaded the game's cheat
     file (e.g. wait for its `Load game-specific cheatfile` line, or for the content to run) — tested on a real N64
     launch path, not only PS1's timing.
  2. **`ps2-patches` on the POST path** (or the client on GET), with a test through the real HTTP route the onn uses.
  3. **The picture:** smaller and better drawn ("a big poorly drawn controller").

## The close (`home12r_2026-11-10/close/CLOSE.md`)

`85220f99…` on the onn, paired; every property empty (twenty); the two units; nothing running; the drive's folders
before = after; eighteen lines, the drop-ins the same; `--check` ok, CONFIRMED. No "Test" profile; the user's own new
profile kept on T86. The hub keeps queue AE's host part live (B85's cleaned lists; committed by the user).

Left (not deleted): `PrivyHub/app/build/home12r_previous/`, `home12r_installed/`; `~/.cache/home12r_tmp/` (the
watcher's raw log, the label map, the candidate list — they carry titles and ids) and `~/home12_scripts/watch_r.py`.

Nothing adopted; nothing fetched; nothing written to the drive; nothing deleted; no sudo, nft or `setprop`; adb for the
install, the reinstall and state reads; nothing committed.
