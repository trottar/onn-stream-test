# HOME-12T stage 1 (2026-11-10 23:44-23:47Z, unattended; outside 04:30-05:30Z; no game, no movie)

- The read line 23:44:36Z (`read_line_at.txt`). HEAD **`904d88fc`** (queue AF **`da2d580f`** committed — B87-B89's
  files in it; then the ROADMAP H7 note; `head.txt`), the tree clean (`git_status_before.txt`: only this record's new
  dir).
- **Preconditions** (`check_before.json`, `client_before.json`, `properties_before.txt`, `drop_ins_before.txt`,
  `units_before.txt`, `tmp_free.txt`, `profiles_before.txt`, `profiles_before_sha256.txt`): `/tmp` 5.3 GB free;
  eighteen lines / drop-ins, `--check` ok; **`85220f99…` CONFIRMED, read back**, paired, identity v2; the twenty
  properties empty (`../props20.sh`, HOME-12R's); only the two units; input profiles 5 (HOME-12R's 4 + the user's own
  kept at C50). The drive (`drive_before.txt`).
- **The companion restart 23:44:52Z** (`restart_at.txt`; B87 + B88 live; no drop-in): eighteen environ lines
  (`environ_after_restart.txt`), `--check` ok (`check_after_restart.json`), the journal clean (`journal.txt`: 32 lines,
  0 error / warning / traceback; the raw journal off the repo), the reconcile `SKIPPED_CURRENT`; the keeper not
  restarted (`keeper.txt`: its MainPID the same before and after).
- **B88's read** (no state changed): `POST /plugins/games/ps2-patches` on loopback with no id → **400**, body
  "Missing game id" (`b88_post_code.txt`; the route exists); `python3 -m unittest discover -s tests/client_contract -v`
  → **5 OK** (`client_contract.txt`).
- **B87's read** (counts only, `b87_read.txt`): T81's content name holds a dot inside → **yes**; `PRIVYHUB_CHEAT_READY`
  in the companion's environment → 0 (absent; B87 on by default).
- **The install 23:46Z** (`install_at.txt`): `85220f99…` preserved in `home12t_previous/` (HOME-12R's preserved copy,
  same bytes); `queue_af_built/` → `home12t_installed/`,
  **`3f21e2c6aa8caa517b0a76b69701b853ada890a99dbde3295b62551f34e223b1`** (`apk_sha256.txt`); the signer `455bde4e…` the
  same, `apksigner verify` OK (`signer.txt`); `adb install -r` Success (`install.log`); read back `3f21e2c6…`, paired,
  identity v2 (`client_after_install.json`); **the twenty properties empty** (`properties_after_install.txt`).
  `--check` now reads the APK line MISMATCH (the pin is still `85220f99…`; expected), the preflight ok
  (`check_after_install.json`).
- **The picks** (`../LABELS.txt`, names off the repo): T85's cheat — HOME-12R's (position 8, Player 1); T81's — position
  2 in Player 1, the only match of its one-word filter. The catalog reads (`cheat-catalog`, POST, as the client) for
  T85 and T81: `clean` true, 12 and 588 shown — as HOME-12R.
- **Seen at the watcher's start** (state left by HOME-12R, not changed here): PCSX2 `[Pad1]` carries the user's own
  profile's remap (rewritten from the game's profile at its next launch); `Dolphin.ini` `EnableCheats = True` and one
  Dolphin `GameSettings/` file from C47; no PCSX2 `gamesettings/` file; `cheat_runtime/` absent; the three drop-in
  folders empty.
- A read-only watcher off the repo from 23:46:52Z (`watcher_started_at.txt`; HOME-12R's script, copied); the logs
  marked (`log_marks.txt`).
- **Pre-registration** `../preregistration.md` hashed 23:47:17Z (`../preregistration.sha256` `72ec6ceb…`,
  `prereg_hashed_at.txt`).
