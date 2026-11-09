# HOME-11: pre-registration (written and hashed before Stage 2, 2026-11-09)

Sources: `handoffs/SESSION_B_DONE_2026-11-09AA.md` §A (stage 1, C40-C43, the hub reads, the "You should see" lines and
the replies — used exactly), `handoffs/HOME-11_DISC_SAFE_TASK.md`, `B73_PAUSED_BAR_2026-11-09.md`,
`B74_DISC_CHANGE_SAFE_2026-11-09.md`, `HOME_10_POINTERS_DISC_2026-11-09.md` (T15 / T17; what failed).

**The state at hashing:** HEAD `2b5826ea` (queue AA `6885189c` and queue AB / B75 `2b5826ea` committed), the tree clean
apart from this record's own new dir; `/tmp` 5.9 GB free; eighteen adopted lines, `--check` ok; the companion restarted
18:54:51Z (B74's host part live; no drop-in, nothing adopted; the keeper not restarted), the journal clean (33 lines,
0 error / warning / traceback), "PlayStation (72)"; **T17's details carry `discs` 4** (the only 4-disc set: 66 PS1
details without `discs`, 5 with 2, 1 with 4); **T17's record's `image_index` 0** (the number only); APK
**`85220f99f92f893968647c185ed98e17456fe9e9bc9cc7bdb550c7c735c04864`** installed 18:56Z (`adb install -r` Success),
read back, paired, identity v2, the signer `455bde4e…` the same as `5f72af4b…` (preserved in `home11_previous/`);
**the seventeen properties empty** (HOME-10's fifteen + `debug.privyhub.paused_bar_fit`, `debug.privyhub.disc_safe`),
no `setprop` at any point. The user is at the TV with the onn and the pads paired to the onn over Bluetooth; nothing
is asked of the user on the hub.

T-labels (HOME-10's; `LABELS.txt`): **T15** = the one-disc PS1 title; **T17** = the 4-disc set. No title, serial, game
id or path is written.

## The cells (B's rows)

**C43 — C37's client half on this APK (T15, one disc).** You should see: no arrow and no dots; the touchpad does nothing
(no click, no Back); the Back bar reads **SAVE · LOAD · END**, as before, with no DISC. Hub: `launch_ports` without
`discs` / `start_disc`; no `PS1 start disc` line; the encoder still `-draw_mouse 0`. **Met:** the user's line. **A
pointer seen** → to B (the onn's arrow or dots mean the client half). **Decides B70's client half** (→ the CONFIRMED
rule).

**C40 — the paused bar on a set (T17), and C41's first half (Start on disc 4).** You should see: the Extras list
"Cheats", "Mods", **"Start on disc…"**, then "Disc 1" … "Disc 4"; the game starting from disc 4; the bar **SAVE · LOAD ·
DISC · END, all four whole on the screen**, END not cut; under PAUSED, **"Disc 4 of 4"**. Hub reads: `launch_ports`
`discs 4`, **`start_disc 4`**, **`launched_disc 4`**; the game log `PS1 start disc: 4 of 4 (record set)` and RetroArch's
own `Setting disc in tray: 4/4`; after END, the record's `image_index` **3** (RetroArch's own save at close; the number
only). **Met (C40):** the user's line that all four buttons are on the screen and END is whole (a photo is welcome).
**Decides B73** (→ the CONFIRMED rule).

**C41 — the set starts on disc 1 (T17, left on disc 4 by the stage above).** Hub reads: the game log `PS1 start disc: 1
of 4 (record set)`, then RetroArch's own `Setting disc in tray: 1/4` as the launch line (**without B74 it would read
4/4**); `launch_ports` `start_disc 1`, `launched_disc 1`; heartbeat rows `disc 1`. You should see: "Disc 1 of 4" on the
bar. **Met:** the launch line 1/4 after a sitting that ended on disc 4; the bar's "Disc 1 of 4". **Decides B74** (the
host half read whatever the APK; the bar's line → the CONFIRMED rule).

**C42 — the warning, then a change during the intro (T17, the same sitting).** You should see: the first DISC: "Change
disc" with **"Change discs only when the game asks for the next one — changing at any other time can freeze the
game"**, and the buttons "I understand" / "Cancel"; after "I understand": the chooser "Disc 1 (in the tray)", "Disc 2"
…; "Changing to disc 2…", then **"Disc 2 of 4 — if the game freezes, use LOAD or END"**; after RESUME: the intro
carrying on (as HOME-10's 1 → 2); the second DISC: **straight to the chooser, no message**. Hub reads: the `disc_swap`
row `ok true`, `from_disc 1`, `disc 2`, `steps 1`, **`launched_disc 1`**; `PS1 disc swap: 1 -> 2`; RetroArch's
`Ejected` / `2/4` / `Closed`; the status still paused before RESUME. **Met:** the message once with the exact text,
then the chooser; the change `ok`; the line; no message the second time. **The game's reaction is recorded, not
scored**: carrying on is expected, as at HOME-10; if it freezes, END (or LOAD) works, as the message says (B74: a
change outside the game's prompt is the game's business). **Decides B74** (client item → the CONFIRMED rule).

## Validity

The seventeen properties empty throughout (read at the close); the eighteen lines unchanged; the user's actions as
described, from the onn with the pads on the onn; the user's lines are the gate on anything on screen; a row's absence
is itself the reading; a step the user could not do, or that left the app, is invalid, not failed; C41 is valid only
after a sitting that ended on disc 4 (the record's `image_index` 3 read after C40's END). No capture of the TV by the
hub.

## The rules

- **The CONFIRMED rule (CL-B7 §6) for `85220f99…`:** C40, C41, C42 and C43 valid and met with every property empty →
  **`85220f99…` CONFIRMED**; the pin moves in the three places (`tools/e1_suite.py` `EXPECT_APK`,
  `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test), the tests green, the patch note indexed. Otherwise
  `5f72af4b…` is reinstalled from `home11_previous/`, read back and paired, and the user told why.
- C41's host half (the launch line) is read from the hub whatever the APK.
- **The verdicts:** C40 → B73; C41 / C42 → B74; C43 → B70's client half. A pointer seen → B.
- **Phase H:** the user's answer to the close question recorded verbatim, or "pending". Nothing adopted.
