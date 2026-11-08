# HOME-6 stage 1 (2026-11-08 17:26-17:30Z, unattended)

- The read line at ~17:26Z (outside 04:30-05:30Z). **`/tmp`: 7.0 GB free** (`tmp_free.txt`; B's leftovers removed
  earlier at the user's go). HEAD `4aa08d3d` (queue S committed: B52 / B53), the tree clean.
- **Checks** (`check_before.json`, `client_before.json`, `properties_before.txt`, `drop_ins_before.txt`): fifteen
  adopted lines + the bench flag = sixteen `PRIVYHUB_` lines; `--check` not ok **on the environ only, the one extra
  line `PRIVYHUB_PS2=1` being the user's bench flag** (every other preflight key true; PS1 files identical; no RetroArch
  / encoder; MainPID on 8765); `cfe0211c…` CONFIRMED, paired; the eleven properties empty; only the two units; no game,
  no movie.
- **Restarts** (`restarts.txt`): the companion 17:26:58Z (start 17:26:57Z, after the commit at 17:23:07Z: B52 / B53
  live) — sixteen lines, the journal since: 32 lines, 0 error / traceback / exception, "PlayStation 2 (115)" listed;
  **`privyhub-diag` 17:27:04Z** (B50 / B53 live; its first copy read at the close).
- **HOME-5's state file:** one `.01.p2s` (16181232 B, 16:13:57Z) kept on the hub, unusable (MTVU on).
- **Before** (`before_listing.json`; listings gitignored under `data/games/ps2/probe/home6/`): `data/games/ps2/logs/`
  absent; the drive: BIOS 3, games 119 entries, equal to HOME-5's after. The hub's PCSX2 ini still `vuThread = true`
  (B52 writes `false` per launch).
- **Pre-registration** `../preregistration.md` hashed (`../preregistration.sha256`), before the user's save.
