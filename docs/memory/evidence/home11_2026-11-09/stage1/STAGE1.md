# HOME-11 stage 1 (2026-11-09 18:53-18:57Z, unattended; outside 04:30-05:30Z)

- The read line ~18:53Z (`read_line_at.txt`). HEAD `2b5826ea` (queue AA `6885189c` = B73 / B74, queue AB `2b5826ea` =
  B75, committed; `head.txt`), the tree clean (`git_status_before.txt`: only this record's own new dir, made first).
- **Preconditions** (`check_before.json`, `client_before.json`, `properties_before.txt`, `drop_ins_before.txt`,
  `units_before.txt`, `tmp_free.txt`): `/tmp` 5.9 GB free; **eighteen** lines / drop-ins, `--check` ok; **`5f72af4b…`
  CONFIRMED, read back on the onn**, paired, identity v2; **the seventeen properties empty**; only the two units; no
  game, no movie. The drive's folders (`drive_before.txt`, counts / bytes / listing hashes only).
- **The companion restart 18:54:51Z** (`restart_at.txt`; B74's host part live, no drop-in, nothing adopted): eighteen
  environ lines (`environ_after_restart.txt`), `--check` ok (`check_after_restart.json`), the drop-ins the same, the
  journal clean (`journal.txt`: 33 lines, 0 error / warning / traceback; the raw journal kept off the repo, it carries
  paths); the keeper not restarted (`keeper_before.txt` read again unchanged). The list (`systems_nodes.txt`):
  **"PlayStation (72)"**.
- **T17's details carry `discs` 4** (`t17_details_discs.txt`: of the 72 PS1 details, 66 without `discs`, 5 with 2, 1
  with 4 — T17, the only 4-disc set). **T17's record's `image_index` 0** (`t17_ldci_index.txt`; the hub's one record,
  the number only; `../ldci_index.sh`).
- **The install 18:56Z** (`install_at.txt`): `5f72af4b…` preserved in `home11_previous/`; `queue_aa_built/` →
  `home11_installed/`, **`85220f99f92f893968647c185ed98e17456fe9e9bc9cc7bdb550c7c735c04864`** (`apk_sha256.txt`); the
  signer `455bde4e…` the same, `apksigner verify` OK (`signer.txt`); `adb install -r` Success (`install.log`); read back
  `85220f99…`, paired, identity v2 (`client_after_install.json`); **the seventeen properties empty**
  (`properties_after_install.txt`; `../props17.sh`).
- A read-only watcher started 18:56:38Z (off the repo): the games status on change and each encoder's argv once
  (redacted); read into the cells.
- The logs' positions marked (`log_marks.txt`).
- **Pre-registration** `../preregistration.md` hashed 18:57:13Z (`../preregistration.sha256`, `3dec65f9…ef4b`).
- Seen after the hashing, not this session's: `_cowork_prompt_b.txt` modified and `handoffs/QUEUE_2026-11-09AC.md`
  new (`git_status_after_stage1.txt`) — another session's; untouched.
