---
memory_schema: 1
as_of: 2026-11-11
status: HOME-12V DONE (session A; stage 1 2026-11-11 07:32-07:34Z unattended; the cells 07:52Z-07:58Z and the optional H7 step 07:59Z-08:09Z with the user at the TV; the close 08:09Z-). APK ca53df0d… installed with every property empty (twenty); C58 the changed rows yellow in the mapping list MET → **ca53df0d… CONFIRMED, the pin moved**; C59 an SNES cheat from the matching list MET (~2 s) → B90's SNES part met; the optional H7 step run — a 2-player PS1 save state made (the user's pick), player 1 won. Nothing adopted; nothing committed
---

# HOME-12V — the list's yellow, an SNES cheat from the matching list, and H7's first save state

Task: `handoffs/HOME-12V_LIST_YELLOW_SNES_TASK.md`; B's rows: `handoffs/SESSION_B_DONE_2026-11-11AH.md` §"A — HOME-12V,
a short check" (with the task's additions). The directory is `home12v_2026-11-11/`: `stage1/`, `c58/`, `c59/`, `h7/`,
`close/`, `pin/`, `preregistration.md` and its `.sha256`, `LABELS.txt`, `props20.sh`, `drive_listing.py`,
`title_check.*`, `redact_check.txt`, `manifest.sha256`. Times are UTC. **T-labels** (`LABELS.txt`): T86 the user's own
profile's game, T87 the SNES title, **T88 the game the user named for H7**. No title, serial, game id, code name, cheat
name or path.

## The user's lines (verbatim)

- **The words that set this task** (recorded as the task asks): to session B — "H6 only has a few quick fixes so let's
  do that then into h7"; to Cowork, on HOME-12U's C56 — **"Letters were great."** (this closes C56's open note:
  `218d9a82…`'s CONFIRMED stood on the user's word).
- Stage 1: "Read _cowork_prompt.txt in the repo root and follow it as my prompt."
- C58: "Looks great" / "Stage 2".
- C59: "Yep cheat worked".
- The H7 step: "[T88] vs mode" / "[T88] is 2 player test and  [a second PS1 title] can be the 4 player test" / "Player 1 and [the player-1 character] wins! (I saved begin in slot 3 and end in slot 2).
  Can you erase these saves when you don't need them?"

(A title or a game's character the user says in a verbatim line is replaced by its label in brackets — HOME-12R's rule.)

## Stage 1 (`home12v_2026-11-11/stage1/STAGE1.md`)

HEAD `6595152b` (queue AH committed), the tree clean; **queue AH touches 0 files under `companion/` → no restart**;
`/tmp` 5.1 GB; eighteen lines, `--check` ok; `218d9a82…` CONFIRMED read back; the twenty properties empty; the two
units. **The stray-RetroArch read: 0** RetroArch processes, no game active (B92's `retroarch_left: 1` not seen now;
nothing stopped). **T87's pick:** the list matching the game file (the third of three), a Pro Action Replay RAM write in
two lines (benched; Game Genie avoided), its effect on a counter on screen. **The install 07:33Z:** `218d9a82…`
preserved in `home12v_previous/`; **`ca53df0dac787607af749492393b5f343e3df775cd4581d44342a1a81ecd590d`** in
`home12v_installed/`, the signer `455bde4e…` the same, `apksigner verify` OK, `adb install -r` Success, read back,
paired; the twenty properties empty. Pre-registration hashed 07:34:37Z (`d01344fe…`).

## The cells

| cell | read | result |
| --- | --- | --- |
| **C58** T86's profile, the list's yellow (`c58/`) | no POST from the onn; the profiles file untouched (sha256 = stage 1's); "Looks great" | **MET** (B92; HOME-12U's list requirement answered) |
| **C59** T87, an SNES cheat (`c59/`) | the matching list (`cheat_source=2`); **the code: RAM, Pro Action Replay spelling, two parts**; launch 200 in **~2 s**; the file in snes9x's folder, `Load game-specific cheatfile` → `Applying cheat changes.`; `activation_mode` "staged", `activation_pulses` 1, `activation_verified` true (RetroArch's flag); no `launch_orphaned`; "Yep cheat worked" | **MET** (the user's line) |

**`GET active-cheats` rows during the sitting: 0** (POST 460, all A's watcher on loopback) — HOME-12U's "seen in
passing" was A's own old watcher, as B found.

## The optional H7 step (`home12v_2026-11-11/h7/H7.md`; no verdict)

Run on the user's word. **The user picked a PS1 title (T88), not SNES** — B93's tool takes PS1 and RetroArch's memory
read on Beetle PSX HW was measured, so A took the pick; the user also set **T88 as the 2-player test and a second PS1
title as the 4-player test**. Launch with players joined 2 (200); PS1 / Beetle PSX HW; **the "begin" state: `save-state
slot=3` → 200, a new state 1,678,205 bytes at 08:03:38Z**; the "end" state: `slot=2` → 200, 2,184,533 bytes at
08:08:47Z; the user's END. **The result: "Player 1 and [the player-1 character] wins!"** (no score number). Nothing run with B93's tool; the states
not copied or changed. **The user asked the two saves erased when no longer needed** — open, for the task after the
proof runs.

## What it decided

- **(a) The APK:** C58 valid and met with every property empty (twenty) → **`ca53df0d…` CONFIRMED.** The pin moved in
  the three places (`home12v_2026-11-11/pin/`; tests green: e1 self-test, `test_c3_l4_nft_night` 33, `test_e1_remote`
  21, `tests/client_contract` 5); `patches/HOME-12V_APK_PIN.md` and B92 indexed. On the onn: `ca53df0d…`.
- **(b) The hub:** C59 met → **B90's SNES part met** (with HOME-12U's C57: the SNES path works; that code was a ROM
  `address:value` line from a non-matching list).
- **H6:** HOME-12U's two open items closed (the list's yellow; the SNES cheat). What stays open: the PS2 disc change
  (designed); a second source for PS2 / GameCube details and the art misses; the user's own cheat files;
  `activation_verified` reads RetroArch's flag, not the core's.
- **H7 (begun on the user's word, 2026-11-11):** B93's tool (fixture-proved); **the first real state made** (T88,
  2-player, player 1 won). **For B / next:** find the memory address(es) that decide the fight's winner (rounds or
  health per player) by comparing the "begin" and "end" states (to be designed — the tool runs from a state, it does not
  search); then A runs the tool from slot 3 three times and the winner must be player 1; after that, erase T88's two
  saves (the user's request). The 4-player proof: the user's second PS1 title, another night.

## The close (`home12v_2026-11-11/close/CLOSE.md`)

`ca53df0d…` on the onn, paired, CONFIRMED on the new pin; every property empty (twenty); the two units; the companion
not restarted this sitting; nothing running; the drive's folders before = after; eighteen lines, the drop-ins the
same; `--check` ok; no profile changed; no `launch_orphaned` row.

Left (not deleted): `PrivyHub/app/build/home12v_previous/`, `home12v_installed/`; T88's two save states (the user's);
`~/.cache/home12v_tmp/` (the watcher's raw log, the private label map, the catalog read, the states listing — they carry
titles, ids and paths) and `~/home12_scripts/watch_v.py`.

Nothing adopted; nothing fetched; nothing written to the drive; nothing deleted; no sudo, nft or `setprop`; adb for the
install and state reads; nothing committed.
