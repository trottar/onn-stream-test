# HOME-5: pre-registration (written and hashed before the first SAVE, 2026-11-08)

Sources: `handoffs/SESSION_B_DONE_2026-11-08R.md` §A (B's stages, strings, hub reads and rows C12'a-d, used as B
states them), `handoffs/HOME-5_PS2_SAVE_TASK.md`, `B51_PS2_SAVESTATES_PINE_2026-11-08.md`,
`HOME_4_PLUS_2026-11-08.md` (C12 and the user's lines), `G_A13_VOD_LOG_ADOPTION_2026-11-07.md` (the adoption form).

**The state:** APK `cfe0211c…a65f` CONFIRMED on the onn; the eleven `debug.privyhub.*` properties empty throughout
(no `setprop` in this run); fifteen adopted lines (`e1_suite.ADOPTED`) + the user's bench flag `b49-ps2.conf`
(`PRIVYHUB_PS2=1`) = sixteen `PRIVYHUB_` lines live; B51's host code live from the stage-1 restart (16:09:24Z, after
the B51 commit `7d4b067b`). `data/games/ps2/sstates/` empty before (0 files). The drive read-only.

## The rows (B's table, pre-registered)

| row | pass when |
| --- | --- |
| C12'a SAVE | HTTP 200; the onn `Saved Slot 1 - …`; the game log `PS2 save: slot 1 pine 0x09 ok; file complete <s>s` with s ≤ 10; a new / changed `.01.p2s` on the hub |
| C12'b the list | after Stop and relaunch, Slot 1 listed with the save's date and size |
| C12'c LOAD | HTTP 200; `Loaded Slot 1 - …`; `PS2 load: slot 1 pine 0x0a ok`; **the user: the game continues from the save** |
| C12'd the files | the state file under `data/games/ps2/sstates/` only; the drive's folders unchanged; `savestates: "pine"` on the `ps2_session` row |

Hub reads beside the rows (B §A): PCSX2's own log `Saved state to slot 1.` / `Loaded state from slot 1.` (read in
place); the PS1 slot index (`privyhub_state_slots.json`, read in place, the key not copied) holding the title's slot 1;
the load's `confirmed` or `visual` (`verification: visual_required`), the user's line deciding. **The save's write time
`<s>` is recorded; over 5 s, a note for B.**

## Validity

- **The save made with PrivyHub's SAVE button** (Game State → Save → Slot 1), not an in-game save; the load with
  PrivyHub's LOAD (Game State → Load → Slot 1) after Back, Stop and a relaunch of the same PS2 title from the list.
- The properties empty; sixteen lines live; no game or movie at the restarts; 5 GHz.
- The user's lines are the gate on anything on screen; a row's absence is itself the reading.
- A step the user could not do, or that left the app, is invalid, not failed.

## G-A14's condition

- **C12'a, C12'b, C12'c and C12'd all met** (the continuation by the user's line) → `PRIVYHUB_PS2=1` adopted as the
  **sixteenth** line (the user's "PS2 always on — yes", 2026-11-08) in G-A13's applied form as B §A stage 4 writes it:
  `PS2` in `ADOPTED` with the comment `G-A14 (adopted 2026-11-08, the user)`, `drop_in_ps2` required in `ok`, the
  wording files, `ADOPTED_E3` as it is; `patches/G-A14_PS2_ADOPTION.md` checked and applied; `git diff --check` clean;
  `e1_suite --self-test`, `test_e1_remote`, `test_c3_l4_nft_night`, `tests/ps2_session` green; `ps2.conf` written,
  `b49-ps2.conf` removed, `daemon-reload`, restart; sixteen lines read back; `--check` ok on sixteen; `flags_absent`;
  the off switch stated.
- **Else:** `b49-ps2.conf` **left as the user set it** (the user's decision overrides B's "remove"); fifteen adopted
  lines; `--check`'s result stated honestly (not ok on the environ: the extra line is the user's bench flag); the
  failed row named.
- C13 (the hold / stall through PINE): not run (B51 kept those uses off); the user's question after, with the
  measured save time.

Nothing else adopted; nothing committed.
