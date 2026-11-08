# HOME-5 stage 1 (2026-11-08 16:08-16:12Z, unattended)

- The read line at ~16:08Z (outside 04:30-05:30Z). HEAD `7d4b067b` (B51 committed), the tree clean.
- **Checks** (`check_before.json`, `client_before.json`, `properties_before.txt`, `diag_check_before.txt`,
  `drop_ins_before.txt`): fifteen adopted lines (`e1_suite.ADOPTED`); `cfe0211c…` CONFIRMED on the onn, paired,
  identity v2; the eleven properties empty; `privyhub-companion` and `privyhub-diag` active, no other unit; 5 GHz; no
  game, no movie. **`--check`: not ok on the environ only** — the one extra line is `PRIVYHUB_PS2=1`, the user's bench
  flag (every other preflight key true; PS1 files identical; no RetroArch / encoder; MainPID on 8765).
- **`b49-ps2.conf` present** (`[Service]` / `Environment=PRIVYHUB_PS2=1`, `b49-ps2.conf.copy`), not rewritten.
- **The restart** 16:09:2xZ (`daemon-reload`, restart; companion start 16:09:24Z, after the B51 commit at 16:07:58Z):
  **sixteen** `PRIVYHUB_` lines (`environ_after_restart.txt`); the journal since: 30 lines, 0 error / traceback /
  exception; "PlayStation 2 (115)" listed. B51 live.
- **Before** (`before_listing.json`; listings gitignored under `data/games/ps2/probe/home5/`): `data/games/ps2/sstates/`
  0 files; the drive: BIOS 3 entries, games 119 entries, equal to HOME-4+'s after-listing; the PS1 slot index 9650 B,
  mtime 2026-10-31.
- **Pre-registration** `../preregistration.md` hashed (`../preregistration.sha256`), before the first SAVE.
