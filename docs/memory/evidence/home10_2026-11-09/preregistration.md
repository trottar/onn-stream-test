# HOME-10: pre-registration (written and hashed before Stage 2, 2026-11-09)

Sources: `handoffs/SESSION_B_DONE_2026-11-09Z.md` §A (stage 1, C37-C39, the hub reads, the "You should see" lines and
the replies — used exactly), `handoffs/HOME-10_POINTERS_DISC_TASK.md`, `B70_POINTERS_2026-11-09.md`,
`B71_CHANGE_DISC_2026-11-09.md`, `B72_SMALL_READINGS_2026-11-09.md`, `HOME_9_GC_2026-11-09.md` (the state before).

**The state at hashing:** HEAD `aafbd811` (queue Z committed: B70-B72), the tree clean; eighteen adopted lines,
`--check` ok; queue Z's host items live from the stage-1 companion restart (16:12:58Z; no drop-in, nothing adopted;
the keeper not restarted); APK **`64d02f3149eb9f14ac829c800388751fbe0a350c66d5981984bb9a508b7285dd`** installed on the
onn (16:14Z), read back, paired, identity v2, the signer the same as `5f72af4b…` (preserved in `home10_previous/`);
**the fifteen properties empty** (HOME-9's twelve + `debug.privyhub.pointer_hide`, `debug.privyhub.disc_change`,
`debug.privyhub.n64_card_top`), no `setprop` at any point; "PlayStation (72)", "GameCube (27)". The hub's X pointer
parked at the middle of the screen (960, 540) by `xdotool mousemove`.

T-labels (assigned as the titles come; `LABELS.txt`): T14 = the N64 title of Stage 2; T15 = the one-disc PS1 title of
Stage 3; T16 = the GameCube title of Stage 4; T17 = the multi-disc PS1 set of Stage 5. No title, serial, game id or
path is written.

## The cells (B's rows)

**C39 — the N64 card (B72 (a); first, at the first N64 start on the new APK).** You should see: the card "A = ✕, B = □,
C-buttons = right stick …" at the top of the screen, and the "Stabilizing game…" text with its resolution / FPS line
**under it, not through it**. It goes at the first press. Hub: `launch_ports` (system n64, `layout face_c`). **Valid:**
the first N64 start after the install, every property empty. **Met:** the user's line (or photo): the card is not over
the details line (the card shows once on this APK, by its own `shown_top` key). **Decides B72 (a)** (client item → the
CONFIRMED rule).

**C37 — no pointer in a game (B70; N64 now, then PS1 and GameCube).** A, before each game's stream: the hub's X pointer
over the game window on purpose (`xdotool mousemove` to the middle of the screen, read back by `xdotool
getmouselocation` inside the window). Hub reads: the encoder's command line (`pgrep -a ffmpeg`) carries
**`-draw_mouse 0`**; nothing else in it moves (the argv with the pair taken out = today's form, `PRIVYHUB_CAPTURE_POINTER=1`'s).
You should see: no arrow and no touch dots, before or after the touchpad is swiped and pressed; the touchpad press does
nothing (no click, no Back, no menu); the remote and the pads work as before. **Valid:** every property empty; the
hub's pointer read inside the window. **Met:** the user's line, per game, for N64, PS1 and GameCube. **A pointer seen**
→ to B, with which one (the hub's arrow = the host half; the onn's arrow or dots = the client half). **Decides B70**
(the client half → the CONFIRMED rule; the host half read whatever the APK).

**Stage 3 — PS1 (C37's PS1 line; C38's one-disc check).** You should see: no pointer; the Back bar reads **SAVE · LOAD ·
END**, with **no CHANGE DISC**. Hub: the status poll has no `discs` key; `launch_ports` has no `discs`.

**Stage 4 — GameCube (C37's GameCube line; B72 (e)).** Hub reads: Dolphin's per-launch log `Added device:
evdev/0/PrivyHub Virtual Gamepad P1` … `P4` and **no `SDL/` device**; `GC pads: P1=evdev/0 …` with no MISMATCH; the
launch's environment carries the two SDL hints (`SDL_JOYSTICK_BLACKLIST_DEVICES` / `SDL_GAMECONTROLLER_IGNORE_DEVICES`
= `0x1209/0x5048`). **Met:** the user's no-pointer line; only the evdev four in Dolphin's log. **Decides B72 (e)**.

**C38 — "Change disc" on a multi-disc PS1 title (B71).** Hub reads: the launch's own `[Disc] Setting disc in tray: i/n`
in the game log (the starting disc; RetroArch may restore the last one used); `launch_ports` `discs n` / `disc i`;
heartbeat rows with `discs` / `disc`; per change the `disc_swap` row (`ok true`, `from_disc`, `disc`, `steps`, `ms`),
the game log `PS1 disc swap: i -> j`, RetroArch's `Ejected …`, `Setting disc in tray: j/n` and `Closed …` lines, and
the `GET_STATUS` after it still PAUSED; `state_reply` rows for any SAVE / LOAD of the sitting (B72 (g)). You should see:
the bar SAVE · LOAD · **CHANGE DISC** · END and "Disc 1 of 4" (or "of 2") under PAUSED; the chooser "Disc 1 (in the
tray)", "Disc 2" …; "Changing to disc 2…", then "Disc 2 of 4"; after RESUME the game reads disc 2 (its own "wrong
disc" message, it carrying on, or at a real disc prompt the prompt satisfied); after the change back the game carries
on; RetroArch's own short notice ("Setting disc in tray …") may show for a moment after the resume — listed, not a
fault. **Valid:** every property empty; the swaps made from the paused bar. **Met:** the entry present here and absent
on Stage 3's one-disc game; both changes `ok true` and the game's state unchanged (still paused) until RESUME; the
user's line that the game took the disc (at a real prompt: the prompt satisfied). A `could not change the disc` reply
→ to B, with the rows. **Decides B71** (client item → the CONFIRMED rule; the host half read whatever the APK).

## Validity

The fifteen properties empty throughout (read at the close); the eighteen lines unchanged; the user's actions as
described; the user's lines are the gate on anything on screen; a row's absence is itself the reading; a step the
user could not do, or that left the app, is invalid, not failed. No capture of the TV by the hub.

## The rules

- **The CONFIRMED rule (CL-B7 §6) for `64d02f31…`:** C37's client half (no onn arrow / dots, the touchpad press inert —
  N64, PS1 and GameCube), C38 and C39 valid and met with every property empty → **`64d02f31…` CONFIRMED**; the pin
  moves in the three places (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its
  test), the tests green, the patch note indexed. Otherwise `5f72af4b…` is reinstalled from `home10_previous/`, read
  back and paired, and the user told why.
- C37's host half (`-draw_mouse 0`) is read from the hub whatever the APK.
- **The verdicts:** C37 → B70, C38 → B71, C39 → B72 (a); Stage 4's Dolphin log → B72 (e). A pointer seen → B with
  which one.
- **H4:** the user's answer on the "selected PS2 / GameCube" tier recorded verbatim, or "pending". Nothing adopted.
