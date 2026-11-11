# HOME-12U stage 1 (2026-11-11 05:29:50-05:33:35Z, unattended; no game, no movie)

- **The first read line (04:54Z) fell inside 04:30-05:30Z** → stopped after reads only (`WINDOW_STOP.md`). The second
  read line 05:29:50Z (`read_line_at.txt`); the reads ran to 05:30:01Z; **every state change from 05:30:01Z on**
  (outside the window).
- HEAD **`81ccd731`** (queue AG committed — B90 / B91's files in it; `head.txt`), the tree clean (`git_status_before.txt`:
  only this record's new dir).
- **Preconditions** (`check_before.json`, `client_before.json`, `properties_before.txt`, `drop_ins_before.txt`,
  `units_before.txt`, `tmp_free.txt`, `profiles_before*.txt`, `keeper.txt`): `/tmp` 5.1 GB free; eighteen lines /
  drop-ins, `--check` ok; **`85220f99…` CONFIRMED, read back**, paired, identity v2; the twenty properties empty
  (`../props20.sh`); only the two units; input profiles 5, assignments 6. The drive (`drive_before.txt`).
- **The companion restart 05:30:0xZ** (`restart_at.txt`; B90 live; no drop-in): eighteen environ lines
  (`environ_after_restart.txt`), `--check` ok (`check_after_restart.json`), the journal clean (`journal.txt`: 31 lines,
  0 error / warning / traceback; the raw journal off the repo), the reconcile `SKIPPED_CURRENT`; the keeper not
  restarted (its MainPID the same).
- **B90's read** (no state changed): `PRIVYHUB_CHEAT_STAGED=` count **0** (`b90_env.txt`); the fixture numbers from
  B90's record (not re-run); `tests/b90_cheat_staged` **10 OK** (`b90_tests.txt`); **the dry call** for T81 and C46's
  cheat (`b90_dry_call_t81.json`, counts only): raw 677, shown 588, 1 pick → **`real_indexes` 2 = `staged_entries` 2**,
  `enabled_true` 2, `enabled_false` 0, **`pulses_bound` 8** (2k + 4).
- **The 60-second rule's read** (`sixty_second_read.json`, `../launch_seconds.py`; the journal's launch-200 lines with
  no `cheat_source`, against each game log's opening time — a lower bound by under a second): PS1 494 launches, max 2 s;
  SNES 73, max 2 s; N64 10, max 2 s; PS2 23, max 3 s; GameCube 5, max 4 s; **none at 45 s or more** (none at 60); every
  launch matched to its log. Nothing for B.
- **T87:** the hub holds cached cheat lists for **4 SNES titles**; T87 chosen (`../LABELS.txt`) — 3 sources, the first
  21 entries, all General, no "must be on" code.
- **The install 05:32Z** (`install_at.txt`): `85220f99…` preserved in `home12u_previous/`; `queue_ag_built/` →
  `home12u_installed/`, **`218d9a82d564e0d63e8bc6cd5b8e9de95bddb033e8f6d0635dd870e19f62cd53`** (`apk_sha256.txt`); the
  signer `455bde4e…` the same, `apksigner verify` OK (`signer.txt`); `adb install -r` Success (`install.log`); read back
  `218d9a82…`, paired, identity v2 (`client_after_install.json`); **the twenty properties empty**
  (`properties_after_install.txt`). `--check` now MISMATCH on the APK line only (expected; `check_after_install.json`).
- T82's `ps2_patches.on` = `ws` before C55 (`t82_patches_before.txt`, HOME-12T's save). The recovery log's
  `launch_orphaned` rows: 0 (`orphan_mark.txt`). A read-only watcher off the repo from 05:33:05Z; the logs marked.
- **Pre-registration** `../preregistration.md` hashed 05:33:35Z (`../preregistration.sha256` `cf829053…`).
