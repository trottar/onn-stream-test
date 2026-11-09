---
memory_schema: 1
as_of: 2026-11-09
status: HOME-10 DONE (session A; stage 1 2026-11-09 16:11-16:15Z unattended, stages 2-5 16:27-17:19Z with the user at the TV, the close 17:33Z-). APK 64d02f31… installed with every property empty (fifteen); C37 MET (N64, PS1, GameCube; both halves), C39 MET, B72 (e) MET, **C38 NOT MET** (the change back left the game black twice; END ~95 % off the screen with CHANGE DISC) → **64d02f31… NOT CONFIRMED; 5f72af4b… reinstalled** from home10_previous/, read back, paired. H4: the user's "Keep all games". Nothing adopted; nothing committed
---

# HOME-10: no pointers, "Change disc", the N64 card

Task: `handoffs/HOME-10_POINTERS_DISC_TASK.md`; B's rows: `handoffs/SESSION_B_DONE_2026-11-09Z.md` §A. The directory is
`home10_2026-11-09/`: `stage1/`, `c39/`, `c37/`, `stage3/`, `stage4/`, `c38/`, `close/`, `to_b.md`,
`preregistration.md` and its `.sha256`, `LABELS.txt`, `redact_check.txt`, `manifest.sha256`. Times are UTC. T-labels
(`LABELS.txt`): T14 the N64 title (HOME-9's T6), T15 the one-disc PS1 title, T16 the GameCube title, T17 the 4-disc set
(HOME-9's T13). No title, serial, game id or path is written.

## The user's lines (verbatim)

- Stage 1: "Read _cowork_prompt.txt in the repo root and follow it as my prompt."
- C39 / C37 N64: "Buttons at the top" / "Touchpad didn't do anything" / "Stage 2".
- The first PS1 start (T17, not a one-disc title): "Touchpad didn't do anything" / "There is now a disc change button.
  But it causes the end button to run off the screen"; then "Stage 3" with no game played (read as no step done).
- Stage 3 (T15): "Touchpad does nothing" / "No change disc shows" / "Stage 3".
- Stage 4 (T16): "I can reach end, it's just off the screen 95%" / "Nothing different, the intro cinematic continued to
  play" / "Stage 4" / "Touchpad does nothing".
- C38 (T17): "Multi disc game looks the same nothing changed"; "If I go to disc change then yes disc 2 is in tray.
  Swapped to disc 4, black screen"; "Still black screen. I ended and restarted. I let the cinematic start on disc 1
  then swapped to 4 and the cinematic continued. Seems I swapped discs too early?" / "Stage 5"; "Disc 4 was at title
  screen but swapping back to 1 is a black screen again."
- H4: **"Keep all games"**.

## Stage 1 (`stage1/STAGE1.md`)

- HEAD `aafbd811` (queue Z committed), the tree clean; `/tmp` 6.1 GB; eighteen lines, `--check` ok; `5f72af4b…`
  CONFIRMED on the onn; **the fifteen properties empty**; the two units.
- **The companion restart 16:12:58Z** (queue Z's host items live; no drop-in): eighteen lines, `--check` ok, the journal
  clean (33 lines, 0 error / warning), the keeper not restarted; "PlayStation (72)", "GameCube (27)".
- **The install 16:14Z:** `5f72af4b…` preserved in `home10_previous/`; `queue_z_built/` → `home10_installed/`,
  **`64d02f3149eb9f14ac829c800388751fbe0a350c66d5981984bb9a508b7285dd`**, the signer `455bde4e…` the same, `apksigner
  verify` OK; `adb install -r` Success; read back, paired, identity v2; the fifteen properties empty.
- The hub's pointer parked at 960 × 540 (`xdotool mousemove`); pre-registration hashed 16:15:18Z (`18e05fee…79d9`).

## The cells

| cell | read | result |
| --- | --- | --- |
| **C39** the N64 card (B72 (a)), T14 | "Buttons at the top": the card above the "Stabilizing" text, not through it (no photo). The first N64 start after the install, every property empty. `launch_ports` n64, **`layout face_c`**, `device_args` 1-4, `remap_binds` 8; `N64 remap: face_c … verified` | **MET → B72 (a)** |
| **C37** no pointer (B70), N64 / PS1 / GameCube | The hub's pointer read inside the RetroArch window (T14, T17) and the Dolphin window (T16); not read live on T15 (the game ended first; parked, unmoved). The encoder **`-draw_mouse 0`** once, before `-window_id`; with it and the adopted output `-r 60` out, the argv = C5-M1's pinned pre-B70 argv (T14, T16; also read on T17). The user, per game: "Touchpad didn't do anything" (N64, PS1 T17), "Touchpad does nothing" (PS1 T15, GameCube). No arrow, no dots, no Back | **MET → B70** (both halves) |
| **Stage 3** C38 one-disc, T15 | "No change disc shows"; `launch_ports` without `discs`; 12 heartbeats, none with `discs`; no `[Disc]` line. The status poll during the game not read live (it ended first) | **MET** (absent on one disc) |
| **Stage 4** B72 (e), T16 | Dolphin's per-launch log: `evdev/0/PrivyHub Virtual Gamepad P1` … `P4` and the X core pointer, **no `SDL/` device** (HOME-9 had `SDL/0-3`); `GC pads: P1=evdev/0 P2=evdev/0 P3=evdev/0 P4=evdev/0`, no MISMATCH; the Dolphin processes carry `SDL_JOYSTICK_BLACKLIST_DEVICES` / `SDL_GAMECONTROLLER_IGNORE_DEVICES` = `0x1209/0x5048`. `GC window: 2.1s`, `GC boot: cpu thread 1.0s`, the Continue's `GC load: … picture ok 0.9s` | **MET → B72 (e)** |
| **C38** "Change disc" (B71), T17 | The bar SAVE · LOAD · CHANGE DISC · END, the chooser with "disc 2 is in tray". **Five changes, all `ok` true** (1→2 953 ms, 2→4 1407 ms, 4→1 1855 ms, 1→4 1854 ms, 4→1 1855 ms; 1-3 steps, each confirmed by RetroArch's `Setting disc in tray: k/4`, `PS1 disc swap: i -> j`); paused until RESUME (read live once, 17:15:50Z); heartbeats follow the disc. The TV: the intro **carried on** after 1→2 and 1→4; **black** after 2→4, still black after the change back 4→1; **black** after 4→1 from disc 4's title screen. **END ~95 % off the screen** when CHANGE DISC is present. No real disc prompt reached | **NOT MET → B71** (the change back not carrying on; the bar's width) |

## What each cell decided

- **The CONFIRMED rule (CL-B7 §6):** C37's client half and C39 valid and met; **C38 valid and NOT MET** → **`64d02f31…`
  NOT CONFIRMED.** **`5f72af4b…` reinstalled** from `home10_previous/` at 17:33:02Z (`adb install -r -d` Success), read
  back, paired, identity v2, the fifteen properties empty (`close/`). The pin is not moved; `64d02f31…` stays in
  `home10_installed/` and `queue_z_built/`. The user was told why at the TV (the change back never recovered the game;
  END ~95 % off the screen).
- C37 → B70 met on both halves (the host half `-draw_mouse 0` is live on the hub whatever the APK; the client half comes
  back with the next APK). C39 → B72 (a) met. Stage 4 → B72 (e) met. C38 → B71: the host's `disc-swap` is right on
  every change (sequence, steps, index, the pause kept); the TV result and the bar are not.
- **What the user loses with the reinstall** until the next APK: the touchpad pointer is back on the onn (the hub's
  arrow stays out: that is the host's), the N64 card's old place, CHANGE DISC gone from the bar (the host action is
  idle, nothing calls it).

## H4 — the user's answer

"Keep all games" — read as **(a), every title on the drive offered**, "selected" dropped: ENHANCED = PS2 + GameCube
(B's suggestion; (d)'s caveat beside PS2 stays B's to write until a heavy title's long play is read).

## To B (`to_b.md`)

1. **The paused bar with CHANGE DISC is too wide:** END ~95 % off the screen (reachable by the D-pad). The four buttons
   must fit (B71's client).
2. **A change outside the game's own prompt can leave a black screen, and the change back does not recover it:** 2→4
   during the intro → black, 4→1 → still black; 4→1 at disc 4's title screen → black. 1→2 and 1→4 during the intro
   carried on. Not settled at the TV whether this is the game's own reaction to the lid opening (as on a console) or
   the swap's sequence on Beetle (eject / steps 0.4 s apart / close while paused). The user's question: "Seems I
   swapped discs too early?" A test at a real disc prompt needs a save near one (the user has none).
3. RetroArch restores the last disc used at the next launch (seen: 2/4 and 4/4 starts); the bar's "Disc i of n" is
   right, but a set left on a late disc starts there.
4. Readings: the status poll's `paused` after a change was read live once (true); the others' were not (the onn leaves
   the stream for the bar).

## The close (`close/`)

Every property empty (fifteen, `properties_close.txt`); the two units; nothing running (no RetroArch, Dolphin, PCSX2,
encoder or AppImage helper); the drive's folders before = after (`drive_after.txt` = `stage1/drive_before.txt`);
`5f72af4b…` read back on the onn, paired. Eighteen lines (drop-ins the same), `--check` ok, CONFIRMED.

Left (not deleted): `PrivyHub/app/build/home10_previous/` and `home10_installed/` (the two APKs).

Nothing committed.
