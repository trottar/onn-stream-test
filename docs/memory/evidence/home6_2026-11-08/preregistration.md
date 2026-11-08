# HOME-6: pre-registration (written and hashed before the user's first SAVE, 2026-11-08)

Sources: `handoffs/SESSION_B_DONE_2026-11-08S.md` §A (B's stages, strings, hub reads and rows, used as B states
them), `handoffs/HOME-6_PS2_LOAD_TASK.md`, `B52_PS2_LOAD_2026-11-08.md`, `B53_PCSX2_LOG_PER_LAUNCH_2026-11-08.md`,
`HOME_5_PS2_SAVE_2026-11-08.md`, `G_A13_VOD_LOG_ADOPTION_2026-11-07.md` (the adoption form).

**The state:** APK `cfe0211c…a65f` CONFIRMED; the eleven `debug.privyhub.*` properties empty throughout (no `setprop`);
fifteen adopted lines + the user's bench flag `b49-ps2.conf` = sixteen `PRIVYHUB_` lines; B52 / B53 live from the
companion restart (17:26:57Z, after the queue S commit `4aa08d3d`); `privyhub-diag` restarted 17:27:04Z (B50's PS2
label and B53's copy live). HOME-5's slot-1 `.p2s` (16:13:57Z, made with MTVU on) is kept on the hub and unusable; the
user's new save replaces it (PCSX2 keeps the old one as `.p2s.backup`). `data/games/ps2/logs/` absent before (made at
the first launch). The drive read-only.

## C12'' — SAVE, Stop, relaunch, LOAD (B §A stage 2)

- **You should see:** (1) `Saved Slot 1 - <date> - <size>`; (2) after Back, **Stop**, the same game started again,
  Back → Game State → **Load → Slot 1**: `Loading state slot 1...`, then `Loaded Slot 1 - …` (a few seconds); (3) after
  **Resume, the game continues from where you saved** (the gate: the user's line).
- **Pass (hub reads):**
  - the game log `PS2 save: slot 1 pine 0x09 ok; file complete <s>s`, `PS2 pcsx2-log: <name>`, and **`PS2 load: slot 1
    pine 0x0a ok; picture ok <s>s`**;
  - the per-launch PCSX2 log present, with `ELF Loading:` before the load, `Loaded state from slot 1.`, and **0 `TLB
    Miss` after it**;
  - after the Resume, the encoder's frame sizes varying (`native_frame_sizes.jsonl`);
  - the drive unchanged;
  - **the user's line: the game continued from the save.**
- **Measured beside it (a reading, not a pass row):** the CPU with MTVU off — `pidstat -t -p <PCSX2 pid> 1` over a
  minute of play after the Resume; the EE thread's mean / max beside H3-P2's (mean 28-31 %, max 62 %), the busiest
  core. B expects an EE peak toward ~85-100 % of a core in a heavy title.

## C14 — the in-game load once more (B §A stage 3)

- **You should see:** `Loaded Slot 1 - …`, then after Resume the game back at the save.
- **Pass:** a second `PS2 load: slot 1 pine 0x0a ok; picture ok <s>s`; 0 `TLB Miss` after it; **the user's line.**

## Validity

- **PrivyHub's SAVE / LOAD buttons only** (Game State → Save / Load → Slot 1), not an in-game save or load; C12'''s
  load after Back, **Stop** and a relaunch of the same title from the list; C14's load in the same launch after some
  play.
- The properties empty; sixteen lines live; no game or movie at the restarts; 5 GHz.
- The user's lines are the gate on anything on screen; a row's absence is itself the reading. A step the user could not
  do, or that left the app, is invalid, not failed.

## G-A14's condition

- **C12'' and C14 both met** → `PRIVYHUB_PS2=1` adopted as the **sixteenth** line (the user's "PS2 always on — yes",
  2026-11-08) in G-A13's applied form as B §A stage 4 writes it: `PS2` in `ADOPTED` with the comment `G-A14 (adopted
  2026-11-08, the user)`, `drop_in_ps2` required in `ok`, the wording files, `ADOPTED_E3` as it is;
  `patches/G-A14_PS2_ADOPTION.md` checked (`git apply --check`) and applied; `git diff --check` clean; `e1_suite
  --self-test`, `test_e1_remote`, `test_c3_l4_nft_night`, `tests/ps2_session` green; `ps2.conf` written, `b49-ps2.conf`
  removed, `daemon-reload`, restart (no game, no movie); sixteen lines read back; `--check` ok on sixteen;
  `flags_absent`; the off switch stated.
- **Else:** the bench flag left as the user set it; fifteen adopted lines; `--check` stated honestly; the failed row
  named (the load's picture, a `TLB Miss`, or the user's line).
- At the close in either case: the keeper's first copy since its restart read back (`sessions.jsonl` PS2 rows `system:
  ps2`, `raw/ps2logs__*` present).

Nothing else adopted; nothing committed.
