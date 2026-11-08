# HOME-4+ stage 1 (2026-11-08, unattended; reads 04:44-04:47Z, the install and restart 05:31Z)

- **The window:** the read line came at ~04:43Z, inside 04:30-05:30Z. Read-only checks and the pre-registration ran
  then; the install, the drop-ins and the restart were held until 05:31Z. The user was told ("nothing yet").
- **Checks** (`preconditions.txt`, `check_before.json`, `client_before.json`, `properties_before.txt`,
  `diag_check_before.txt`, `drop_ins_before.txt`, `environ_before.txt`, `memcards_before.sha256`):
  - fifteen lines; `--check` ok with `8ba4d996…` CONFIRMED (after `adb connect` from the hub; adb was down at first);
  - the eleven properties empty; `privyhub-companion` and `privyhub-diag` active, no other `privyhub-*` unit;
  - HEAD `9682a38e` (B50 committed; the first read line stopped on B50 uncommitted), the tree clean;
  - one device paired, identity v2, Hub host empty; 5 GHz (5180 MHz); no game, no movie;
  - the paths file and the one AppImage present;
  - the drive: BIOS folder 3 files, games folder 118 files + 1 old subfolder; sizes and mtimes equal to H3-P2's
    (listings gitignored under `data/games/ps2/probe/home4/`);
  - the memory cards: both `47ebe237…8358` (all `0xFF`, `formatted: False`).
- **Pre-registration:** `../preregistration.md`, sha256 `5650f097…9f12`, hashed 04:47:14Z, before the install.
- **The install** (05:31:2xZ): `8ba4d996…` kept at `home3_installed/`; `queue_o_built/app-debug.apk` →
  `home4_installed/`, sha256 `cfe0211c…a65f` = B's; the signer `455bde4effefd742…` the same as `8ba4d996…`'s;
  `apksigner verify` OK; `adb install -r` Success; read back `cfe0211c…a65f`, paired, identity v2, Hub host empty
  (`client_after_install.json`); **the eleven properties empty** (`properties_after_install.txt`).
- **The bench drop-ins** (B's printf lines exactly; copies `b49-ps2.conf.copy`, `b47-vod-drop.conf.copy`),
  `daemon-reload`, restart 05:31:57Z: **seventeen** `PRIVYHUB_` lines (`environ_after_restart.txt`: the fifteen +
  `PRIVYHUB_PS2=1` + `PRIVYHUB_VOD_DROP_TEST=1`); both units active; the journal since: 34 lines, 0 error / traceback
  / exception (`journal.txt`); the host's games list has **"PlayStation 2 (115)"** (`systems_nodes.txt`).
- `--check` after (`check_after_restart.json`): `ok` false as expected — the APK MISMATCH (the pin is `8ba4d996…`
  until the close) and the environ ≠ ADOPTED (the two bench lines); PS1 files identical, no RetroArch / encoder,
  MainPID on 8765, adb true, no game.
