# HOME-2 stage 1 (2026-11-06 16:30-16:33Z, unattended)

- **Preconditions met** (`preconditions.txt`, `client_before.json`, `properties_before.txt`):
  - fourteen lines; `--check` ok with `fcd924c2…` CONFIRMED; no `e3_flag.conf`; no game;
  - `privyhub-companion` and `privyhub-diag` active, no other `privyhub-*` unit;
  - one device paired, identity v2, Hub host empty; the newest `token_issued` lan; 5 GHz (5180 MHz);
  - the ten properties empty; adb connected (one device; no address written);
  - HEAD `1f7a6fd8` ("Docs cleanup (audit option b)"), the docs pass committed, the tree clean.
- **Pre-registration:** `../preregistration.md`, sha256 `4d42eb50…6b8f`, hashed 16:31:46Z, before the install.
- **The install** (16:32:0xZ):
  - `fcd924c2…` kept at `cl_b14_installed/`, `554ccf61…` at `home1_installed/` (hashes checked);
  - `queue_m_built/app-debug.apk` → `home2_installed/`, sha256 `0132b944…e24f` = B's; the signer the same as
    `fcd924c2…`'s; `apksigner verify` OK (`apk_sha256.txt`, `signer.txt`);
  - `adb install -r` Success; read back `0132b944…e24f`, paired, identity v2, Hub host empty
    (`client_after_install.json`); **the ten properties empty** (`properties_after_install.txt`).
- **The companion restart** 16:32:10Z (`companion_restart.txt`): active; `privyhub-diag` active; fourteen lines;
  `--check` reads MISMATCH on the APK only (preflight ok, PS1 files identical, no RetroArch / encoder, MainPID on 8765),
  as the pin rule says until stage 5. The journal since the restart: no error or traceback line.
