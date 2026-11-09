# SESSION B — done, 2026-11-09 AB (QUEUE_2026-11-09AB: B75 the feature-parity matrix; run 18:20-18:45Z)

- **Baseline:** `6885189c` (queue AA committed). The first attempt this day stopped at the check because queue AA was
  uncommitted; after the user's commit, `git status --short` was empty (`logs/b75_git_status.txt`).
- **Not done:**
  - no code, no test, nothing adopted, nothing committed;
  - no companion or keeper restart, no adb, no sudo, no nft, no stream;
  - **no emulator started.** PCSX2's and Dolphin's AppImages were only listed with `7z` and streamed into memory for
    strings and section counts. Nothing was extracted to disk. The N64 core's file was read as data;
  - nothing fetched (the databases named, not queried);
  - nothing written to the drive; `privyhub-diag` and `~/privyhub_diag/` untouched; KNOWN_ISSUES untouched;
  - nothing of A's touched.
- **Written:**
  - `docs/memory/architecture/H6_PARITY_MATRIX_2026-11-09.md`: the matrix, the gaps, the reading, the order, the
    questions;
  - this file; one line in `SESSION_B_STATUS.txt`; **one pointer line** in `docs/ROADMAP.md` (at the end of §H4);
  - `logs/b75_git_status.txt`.

## The matrix in counts (23 rows, each a per-game feature PS1 / SNES have on the onn today)

| | present | missing | impossible |
|---|---|---|---|
| **N64** (RetroArch) | 13 | 6 | 4 (no discs ×2, one pad type, four ports built in) |
| **PS2** (PCSX2 2.8.2) | 13 | 9 | 1 (DualShock 2 covers PS1's pad choice) |
| **GameCube** (Dolphin 2609b) | 12 | 9 | 2 (one pad type, four ports built in) |

**Present on all three:** favourites, recently played / Continue / play count, search, Start Fresh, Load Save, the
recovery prompt, SAVE / LOAD / END, the hold's return, the stall resume, hold-to-join, the Players override.

## Findings the user should know

- **Artwork:** the hub's fetcher (RetroArch's database + thumbnail server) knows NES / SNES / Genesis / PS1 only, so
  N64 / PS2 / GameCube have no box art, details or players data.
- **Custom controls:** Input Profiles apply through RetroArch, so on N64 too by the code. **On PS2 and GameCube the onn
  shows "Input Profile" but the launch ignores it.**
- **Cheats:** the hub's cached index of RetroArch's cheat database has **N64, no PS2, no GameCube**.
  - **Dolphin ships about 4,990 named Action Replay / Gecko codes** in its bundled per-game settings (GameCube and Wii
    together), on the hub already.
  - PCSX2 names no cheat feed. Its bundled patches are widescreen / 60-fps / no-interlace, and they are **on the hub,
    off**.
  - PS1's own drop-in cheat folder is list-only.
- **"NEW"** shows on no system today (its flag is not adopted).
- **Play time, fast-forward, screenshots, a rewind button, per-game core options / AV settings:** on no system, so not
  parity gaps.

## The suggested order (a suggestion; the user ranks)

1. **Artwork + details** for N64 / PS2 / GameCube (G1, M, host only).
2. **Custom controls**: the N64 look (S), then PS2 (M) and GameCube (M).
3. **Cheats**: N64 from RetroArch (S), then GameCube from Dolphin's bundled codes (M), then the PS2 drop-in (M ×2).
4. Then, if wanted: PS2 widescreen (S), the GameCube disc change (S-M), Mods on N64 / GameCube (M), the PS2 disc change
   (M-L), "NEW" (M).

## The questions (one per gap)

1. **G1:** fetch N64 / PS2 / GameCube box art and details from RetroArch's library as for PS1 (each title's name is sent)?
2. **G2:** PS2 / GameCube use the **same** Input Profiles you already made, or separate ones per system?
3. **G3a:** fetch N64 cheats from RetroArch's database as PS1's (each matched title's name is sent)?
4. **G3b:** GameCube cheats from Dolphin's built-in codes only, or also Dolphin's code download (the game's id is sent)?
5. **G3c:** a per-game drop-in folder for your PS2 `.pnach` files; and should it also make your own `.cht` files
   launchable on PS1 / SNES?
6. **G5:** PS2's widescreen patches offered per game; Mods on N64 / GameCube at all?
7. **G6:** does any GameCube or PS2 title you play span two discs?
8. **G7:** the "NEW" tag at all?

**Next:** the user's ranking and answers. Then the full §H6 text goes in the ROADMAP and the first item is queued.
