# HOME-3 stage 1 (2026-11-06 23:45-23:48Z, unattended)

- **Preconditions met** (`preconditions.txt`, `client_before.json`, `properties_before.txt`, `check_before.json`,
  `diag_check_before.txt`):
  - fourteen lines; `--check` ok with `0132b944…` CONFIRMED; no `e3_flag.conf`; no game;
  - `privyhub-companion` and `privyhub-diag` active, no other `privyhub-*` unit;
  - one device paired, identity v2, Hub host empty; the newest `token_issued` lan; 5 GHz (5180 MHz);
  - the eleven properties empty (HOME-2's ten plus `player_prompt`); adb connected (one device; no address written);
  - HEAD `d9fd9688` ("Queue N done; HOME-3 handoff"), queue N committed, the tree clean.
- **Pre-registration:** `../preregistration.md`, sha256 `5125ee74…b728`, hashed 23:46:45Z, before the install.
- **The install** (23:47:0xZ):
  - `0132b944…` kept at `home2_installed/`; `fcd924c2…` (`cl_b14_installed/`) and `554ccf61…` (`home1_installed/`)
    preserved (hashes checked, `apk_sha256.txt`);
  - `queue_n_built/app-debug.apk` → `home3_installed/`, sha256 `8ba4d996…605f` = B's; the signer the same as
    `0132b944…`'s; `apksigner verify` OK (`signer.txt`);
  - `adb install -r` Success; read back `8ba4d996…605f`, paired, identity v2, Hub host empty
    (`client_after_install.json`); **the eleven properties empty** (`properties_after_install.txt`).
- **The companion restart** 23:47:20Z (`companion_restart.txt`): active; `privyhub-diag` active; fourteen lines;
  `--check` reads MISMATCH on the APK only (preflight ok, PS1 files identical, no RetroArch / encoder, MainPID on 8765),
  as the pin rule says until the close. The journal since the restart: no error or traceback line.
