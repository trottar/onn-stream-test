# HOME-12R stage 1 (2026-11-10 21:55-21:59Z, unattended; outside 04:30-05:30Z; no game, no movie)

- The read line ~21:55Z (`read_line_at.txt`). HEAD **`0de0b290`** (queue AE `5cfe4c01` committed; then the ROADMAP H7
  note; `head.txt`), the tree clean (`git_status_before.txt`: only this record's new dir).
- **Preconditions** (`check_before.json`, `client_before.json`, `properties_before.txt`, `drop_ins_before.txt`,
  `units_before.txt`, `tmp_free.txt`, `profiles_before.txt`): `/tmp` 5.5 GB free (`TMPDIR` on the main disk); eighteen
  lines / drop-ins, `--check` ok; **`85220f99…` CONFIRMED, read back**, paired, identity v2; the twenty properties
  empty (`../props20.sh`); only the two units; input profiles 4, none called "Test". The drive (`drive_before.txt`).
- **The companion restart 21:56:11Z** (`restart_at.txt`; B85 live; no drop-in): eighteen environ lines
  (`environ_after_restart.txt`), `--check` ok (`check_after_restart.json`), the journal clean (`journal.txt`: 33 lines,
  0 error / warning / traceback; the raw journal off the repo), the reconcile `SKIPPED_CURRENT`; the keeper not
  restarted (`keeper.txt`).
- **T81's `cheat-catalog`** (`t81_catalog_counts.json`, counts only): one source, `clean` true, `raw_count` 677,
  `shown_count` 588, `hidden` trigger 84 / enabler 1 / duplicate 4 (header 0), groups general 135 / player1 152 /
  player2 131 / player3 87 / player4 83 — **as B's rows**; with `raw=1` 677 entries and no `clean` key — as B's rows.
- **The install 21:56Z** (`install_at.txt`): `85220f99…` preserved in `home12r_previous/`; `queue_ae_built/` →
  `home12r_installed/`, **`c801caabe6f121d979afa873668b0c48b47d310067cad8ec57cfa8cbdd48582b`** (`apk_sha256.txt`); the
  signer `455bde4e…` the same, `apksigner verify` OK (`signer.txt`); `adb install -r` Success (`install.log`); read back
  `c801caab…`, paired, identity v2 (`client_after_install.json`); **the twenty properties empty**
  (`properties_after_install.txt`).
- **T85 chosen** (`../LABELS.txt`) and each label's needs read (`needs.json`): T81 588 shown in five sections; T82
  `ps2_patches` ws / ni / 60, none on; T83 one cleaned source of 44 (General), the code at position 8 (Action Replay);
  T85 one cleaned source of 12 (General 6 / Player 1 3 / Player 2 3), the cheat at position 8 (Player 1). Every label
  on the Default profile.
- **Seen at the watcher's start:** the emulators' pad files still carry HOME-12's last launches (PCSX2 `[Pad1]` Square /
  Triangle swapped; `GCPad1` from the user's other profile) — each is rewritten from the game's profile (Default) at
  its next launch. `Dolphin.ini` `EnableCheats = False`; no Dolphin `GameSettings/` or PCSX2 `gamesettings/` file;
  `cheat_runtime/` empty; the three drop-in folders present, empty.
- A read-only watcher off the repo from 21:57Z (`watcher_started_at.txt`); the logs marked (`log_marks.txt`).
- **Pre-registration** `../preregistration.md` hashed (`../preregistration.sha256`, `prereg_hashed_at.txt`).
