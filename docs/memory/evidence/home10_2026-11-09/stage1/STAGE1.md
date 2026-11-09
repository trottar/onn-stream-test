# HOME-10 stage 1 (2026-11-09 16:11-16:15Z, unattended; outside 04:30-05:30Z)

- The read line ~16:11Z (`read_line_at.txt`). HEAD `aafbd811` (queue Z committed: B70-B72), the tree clean
  (`git_status_before.txt`: only this record's own new dir, made first).
- **Preconditions** (`check_before.json`, `client_before.json`, `properties_before.txt`, `drop_ins_before.txt`,
  `units_before.txt`, `tmp_free.txt`): `/tmp` 6.1 GB free; **eighteen** lines / drop-ins, `--check` ok;
  **`5f72af4b…` CONFIRMED, read back on the onn**, paired, identity v2; **the fifteen properties empty**; only the two
  units; no game, no movie. The drive's folders (`drive_before.txt`, counts / bytes / listing hashes only).
- **The companion restart 16:12:58Z** (`restart_at.txt`; queue Z's host items live, no drop-in, nothing adopted):
  eighteen environ lines (`environ_after_restart.txt`), `--check` ok (`check_after_restart.json`), the drop-ins the
  same, the journal clean (`journal.txt`: 33 lines, 0 error / warning / traceback); the keeper not restarted
  (`keeper_before.txt` read again unchanged). The list (`systems_nodes.txt`): **"PlayStation (72)"**, **"GameCube (27)"**.
- **The install 16:14Z** (`install_at.txt`): `5f72af4b…` preserved in `home10_previous/`; `queue_z_built/` →
  `home10_installed/`, **`64d02f3149eb9f14ac829c800388751fbe0a350c66d5981984bb9a508b7285dd`** (`apk_sha256.txt`); the
  signer `455bde4e…` the same, `apksigner verify` OK (`signer.txt`); `adb install -r` Success (`install.log`); read back
  `64d02f31…`, paired, identity v2 (`client_after_install.json`); **the fifteen properties empty**
  (`properties_after_install.txt`).
- **The hub's pointer** parked at the screen's middle, 960 × 540 of 1920 × 1080 (`pointer_parked.txt`); read inside
  the game window at each stage.
- The logs' positions marked (`log_marks.txt`).
- **Pre-registration** `../preregistration.md` hashed 16:15:18Z (`../preregistration.sha256`, `18e05fee…79d9`).
