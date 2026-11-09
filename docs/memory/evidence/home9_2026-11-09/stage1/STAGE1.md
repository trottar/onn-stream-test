# HOME-9+GC stage 1 (2026-11-09 04:55-05:43Z, unattended)

- The read line at 04:55Z. HEAD `1bf0a76c` (queue Y committed: B69), the tree clean.
- **Preconditions** (04:55-04:57Z; `check_before.json`, `client_before.json`, `properties_before.txt`,
  `drop_ins_before.txt`, `units_before.txt`, `tmp_free.txt`): `/tmp` 6.3 GB free; seventeen lines, `--check` ok;
  **`9aa00ba2…` CONFIRMED, read back on the onn**, paired, identity v2; the twelve properties empty; only the two units;
  no game, no movie.
- **The window** (`window_exception.txt`): the read line came inside 04:30-05:30Z. Read-only items only until the
  user's answer ("Go now (Recommended)") arrived ~05:40Z; every state change ran after 05:30Z.
- **Read-only, before any change:** the library before (`library_before.txt`: 80 `.cue`, 0 `.m3u`); the `.m3u` plan
  (`m3u_plan_output.txt`): **S1-S6, 6 sets / 14 discs (2+2+4+2+2+2), one saved file on S1's discs**, 0 reported; the
  drive's folders (`drive_before.txt`: listing hashes only; the GameCube folder 28 files).
- **The bench drop-in** `b69-gamecube.conf` by B's printf (`b69-gamecube.conf.copy`); `daemon-reload`; **the companion
  restart 05:41:02Z** (queues X and Y live). Eighteen environ lines = the seventeen + `PRIVYHUB_GAMECUBE=1`
  (`environ_after_restart.txt`); **`--check` not ok on the environ only** (every `drop_in_*` true; the bench line
  named); the journal clean (`journal.txt`, no error / warning). No keeper restart.
- **The list** (`systems_nodes_before_m3u.txt`): "PlayStation (80)", "Nintendo 64 (13)", **"GameCube (27)"**.
- **The install** (`install_at.txt` 05:42:07Z): `9aa00ba2…` preserved in `home9_previous/`; `queue_x_built/` →
  `home9_installed/`, **`5f72af4b65ebf4bf434668f4ef26c52885be02fb8f5400d63e7b4e548bcdca32`** (`apk_sha256.txt`); the
  signer `455bde4e…` the same, `apksigner verify` OK (`signer.txt`); `adb install -r` Success (`install.log`); read
  back `5f72af4b…`, paired, identity v2 (`client_after_install.json`); **the twelve properties empty**
  (`properties_after_install.txt`).
- **The `.m3u` applied** (the user's "apply m3u", the whole, the card copy included; 05:42:25Z):
  `PRIVYHUB_IMPORT=1 python3 tools/library_m3u.py apply --migrate-states` → **written 6, already 0, copied 1**
  (`m3u_apply_output.txt`); the library after (`library_after.txt`): 80 `.cue` + **6 `.m3u`**, no disc moved;
  the list **"PlayStation (72)"** (`systems_nodes_after_m3u.txt`). **The way back:**
  `PRIVYHUB_IMPORT=1 python3 tools/library_m3u.py undo`.
- **Pre-registration** `../preregistration.md` hashed 05:43:16Z (`../preregistration.sha256`, `a7aefb9e…23e2`).
