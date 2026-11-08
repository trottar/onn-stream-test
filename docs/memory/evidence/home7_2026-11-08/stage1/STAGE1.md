# HOME-7+N64 stage 1 (2026-11-08 21:53-21:57Z, unattended)

- The message began "go N64." (the core fetch allowed), then the read line. HEAD `32abb425` (queue V committed), the
  tree clean.
- **Preconditions** (`check_before.json`, `client_before.json`, `properties_before.txt`, `drop_ins_before.txt`,
  `tmp_free.txt`): `/tmp` 6.6 GB free; seventeen lines (sixteen + `b56-import.conf`), `--check` not ok on the environ
  only (`PRIVYHUB_IMPORT=1`, the bench flag); `cfe0211c…` CONFIRMED; the eleven properties empty; the two units.
- **The N64 core** (`n64_core_fetch.txt`): stable 1.22.2 lists no per-core files → the nightly per-core zip (200,
  2719493 B, last-modified 2026-11-07 09:26 GMT); zip sha256 `35b91ceb…10d1`; `.so` sha256 `26f2b4ec…775e` (7554344 B);
  into `runtime/emulators/retroarch/cores-linux/` (gitignored); `n64_core_check --keys` → bundled, 12 / 12 keys, exit 0;
  nothing started.
- **The N64 folder:** `N64_DIR=` added to the gitignored paths file (the path not copied); the drive's N64 folder 13
  files, 331350016 B, listing hash recorded (`n64_folder_before.txt`).
- `b56-import.conf` removed; the bench drop-in `b59-n64.conf` (`b59-n64.conf.copy`); `daemon-reload`, restart
  (`restart_at.txt`, after the queue V commit): **seventeen** lines (`PRIVYHUB_N64=1` the bench flag; `--check` not ok
  on the environ only, named); the journal clean; the list "PlayStation (80)", "Nintendo 64 (13)".
- **The install** (`install_at.txt`): `cfe0211c…` preserved in `home7_previous/`; `queue_t_built/` → `home7_installed/`,
  `9aa00ba2…` = B's, the signer `455bde4e…` the same, `apksigner verify` OK; `adb install -r` Success; read back, paired,
  identity v2; the eleven properties empty.
- **Pre-registration** `../preregistration.md` hashed (`../preregistration.sha256`).
