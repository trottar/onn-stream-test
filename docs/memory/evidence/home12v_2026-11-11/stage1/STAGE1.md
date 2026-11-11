# HOME-12V stage 1 (2026-11-11 07:32:15-07:34:37Z, unattended; outside 04:30-05:30Z; no game, no movie)

- The read line 07:32:15Z (`read_line_at.txt`). HEAD **`6595152b`** (queue AH committed — B92 / B93's files in it;
  `head.txt`), the tree clean (`git_status_before.txt`: only this record's new dir).
- **No companion restart:** queue AH's commit touches **0** files under `companion/` (55 files; `ah_no_host_part.txt`);
  the companion runs since HOME-12U's restart (`companion_unit.txt`).
- **Preconditions** (`check_before.json`, `client_before.json`, `properties_before.txt`, `drop_ins_before.txt`,
  `environ_now.txt`, `units_before.txt`, `tmp_free.txt`, `profiles_before*.txt`, `keeper.txt`): `/tmp` 5.1 GB free;
  eighteen lines / drop-ins, `--check` ok; **`218d9a82…` CONFIRMED, read back**, paired; the twenty properties empty
  (`../props20.sh`); only the two units; input profiles 5, assignments 6. The drive (`drive_before.txt`).
- **The stray-RetroArch read** (`stray_retroarch.txt`): no game active; **RetroArch processes 0** (by name or command
  line; `--check` 0). B92's bench file's last line `retroarch_left: 1` is not seen now — nothing to stop.
- **T87's pick** (`../LABELS.txt`; the position off the repo too): the catalog as the client reads it (`POST
  cheat-catalog`) — 3 lists; the one whose name matches the game file (the third, 162 shown); a cheat at position 12, a
  **Pro Action Replay RAM write in two lines** (a form B92's bench covered; Game Genie avoided), its effect on the
  on-screen counter; one match for a three-character filter.
- **The install 07:33Z** (`install_at.txt`): `218d9a82…` preserved in `home12v_previous/`; `queue_ah_built/` →
  `home12v_installed/`, **`ca53df0dac787607af749492393b5f343e3df775cd4581d44342a1a81ecd590d`** (`apk_sha256.txt`); the
  signer `455bde4e…` the same, `apksigner verify` OK (`signer.txt`); `adb install -r` Success (`install.log`); read back
  `ca53df0d…`, paired, identity v2 (`client_after_install.json`); **the twenty properties empty**
  (`properties_after_install.txt`). `--check` MISMATCH on the APK line only (expected; `check_after_install.json`).
- The recovery log's `launch_orphaned` rows 0 (`orphan_mark.txt`); the logs marked (`log_marks.txt`); a read-only
  watcher off the repo from 07:34:17Z, calling `active-cheats` with **POST only**.
- **Pre-registration** `../preregistration.md` hashed 07:34:37Z (`../preregistration.sha256` `d01344fe…`).
