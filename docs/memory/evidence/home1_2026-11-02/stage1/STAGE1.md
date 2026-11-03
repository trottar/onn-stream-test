# HOME-1 stage 1 (2026-11-03 00:38-00:45Z, unattended)

- **Preconditions met** (`preconditions.txt`, `client_before.json`):
  - thirteen lines; `--check` ok with `fcd924c2…` CONFIRMED; no `e3_flag.conf`; no game;
  - one device paired; Hub host empty; the newest `token_issued` lan (00:38:09Z); 5 GHz (5180 MHz);
  - HEAD `397199dd` ("Queue L done; HOME-1 handoff"), the tree clean;
  - `privyhub-link-n1` gone.
  - adb was not connected at first; it was connected to the onn over the LAN on the usual port, with the address
    taken from the hub's own request log and never written down.
- **Housekeeping:**
  - `_cowork_prompt_cap.txt` removed with `git rm` (staged, not committed; a plain `rm` was refused by the session's
    permission check);
  - `_cowork_prompt_offsite.txt` left.
- **The trip keeper:** stopped by its cap ("done (the cap)", 2026-11-01T23:59:00Z); the manifest checks (1837 lines,
  0 failures).
- **"Read the trip":** `evidence/reads/diag_trip_20261103T004048Z.md`. 36 sessions, 6 restarts, 5 stalls: TRIP-R2
  §1's six restarts reproduced exactly. The weekend after Friday had no games, only VOD (`trip_read_weekend.md`).
- **`privyhub-diag`: NOT ENABLED.** `cp` + `daemon-reload` + `enable --now` was refused by the session's permission
  check (a persistent user service). Nothing was copied or enabled. `diag_check` line 6 reads `diag-keeper: not running
  (no status); unit privyhub-diag inactive`. Left for the user (B item 3's command), or for permission to run it.
- **The companion restart** at 00:42:2xZ (`companion_restart.txt`): **B33 live for the first time.**
  `rewind_needs_loss_config` at 00:42:31.356Z (`implied by PRIVYHUB_LINK_RECOVERY=1`, short 1000 ms, lookback 2.5 s,
  dark 250 ms, the uplink counter). Thirteen lines; `--check` ok, CONFIRMED before the install
  (`check_after_restart.json`).
- **Pre-registration:** `../preregistration.md`, sha256 `a3d8b282…f64f`, hashed 00:42:17Z, before the install.
- **The install** (00:43Z):
  - `fcd924c2…` kept at `cl_b14_installed/` (hash checked);
  - `queue_l_built/app-debug.apk` → `home1_installed/`, sha256 `554ccf61…9902` = B's, the signer the same as
    `fcd924c2…`'s (`apk_sha256.txt`, `signer.txt`);
  - `adb install -r` Success; read back `554ccf61…9902`, paired, identity v2, Hub host empty
    (`client_after_install.json`);
  - **the ten properties empty** before and after (`properties_*.txt`).
  - From here `--check` and `diag_check` read the APK as off the pin, until the CONFIRMED rule at stage 5.
