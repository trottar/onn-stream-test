# HOME-12 stage 1 (2026-11-10 03:13-03:20Z, unattended; outside 04:30-05:30Z; no game, no movie)

- The read line ~03:13Z (`read_line_at.txt`). HEAD **`e3ad4d36`** (ART-1R committed; `head.txt`), the tree clean
  (`git_status_before.txt`: only this record's own new dir, made first).
- **Preconditions** (`check_before.json`, `client_before.json`, `properties_before.txt`, `drop_ins_before.txt`,
  `units_before.txt`, `tmp_free.txt`): `/tmp` 5.7 GB free (`TMPDIR` on the main disk); **eighteen** environ lines /
  drop-ins, `--check` ok; **`85220f99…` CONFIRMED, read back on the onn**, paired, identity v2; **the eighteen
  properties empty** (`../props18.sh`: HOME-11's seventeen + `ps2_patches`); only the two units; no emulator running.
  The drive's folders (`drive_before.txt`, counts / bytes / listing hashes only).
- **The companion's code current — no restart** (`code_current.txt`): it has run since ART-1R's restart 03:02:16Z;
  `1739c816..e3ad4d36` changes nothing outside `docs/` and the prompt file. Read anyway: the eighteen environ lines
  (`environ_now.txt`), the journal since 03:02Z 0 error / warning / traceback, the reconcile `SKIPPED_CURRENT`.
- **The install 03:14Z** (`install_at.txt`): `85220f99…` preserved in `home12_previous/`; `queue_ac_built/` →
  `home12_installed/`, **`de6682dbaf00237c2f6477b68df4fa00e320c0a403ccb2d28863344dee86de28`** (`apk_sha256.txt`); the
  signer `455bde4e…` the same, `apksigner verify` OK (`signer.txt`); `adb install -r` Success (`install.log`); read
  back `de6682db…`, paired, identity v2 (`client_after_install.json`); **the eighteen properties empty**
  (`properties_after_install.txt`). (`--check` now reads the APK as not the pin — expected until the rule decides.)
- **The labels** (`../LABELS.txt`) and **each cell's needs read on the hub** (`needs.json`, labels only):
  T81 (N64): details with a year, a genre, 4 players, `box_art_available` true; one cheat list of 677 entries; the
  cheat picked at position 38, a single constant write. T82 (PS2): `box_art_available` true, no year / genre /
  players (as expected); `ps2_patches` available ws / ni / 60, on none. T83 (GameCube): `box_art_available` true, no
  year / genre / players; 44 Dolphin codes (Action Replay and Gecko); the code picked at position 8, Action Replay.
  Each label's Input Profile: Default. Profiles 4, none called "Swap". Read without a Cheats-list call (the GameCube
  count through the plugin's own reader in a separate process), so **the drop-in folders are still absent** — they
  appear at the user's first Cheats list (C46).
- The baselines (the watcher's first lines): PCSX2 `[Pad1]` Cross / Circle = FaceSouth / FaceEast; `GCPad1` A / X =
  SOUTH / EAST; `Dolphin.ini` `EnableCheats = False`; no Dolphin `GameSettings/` file; no PCSX2 `gamesettings/` file;
  `cheat_runtime/` empty.
- A read-only watcher started 03:19Z (off the repo, `watcher_started_at.txt`): the games status, the staged cheat
  files, the pad / cheat / settings keys, the emulator processes, each on change; read into the cells.
- The logs' positions marked (`log_marks.txt`).
- **Pre-registration** `../preregistration.md` hashed 03:20:16Z (`../preregistration.sha256`, `bc986326…22b8`).
