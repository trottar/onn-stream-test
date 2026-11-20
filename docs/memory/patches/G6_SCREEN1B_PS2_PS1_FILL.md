---
memory_schema: 1
as_of: 2026-11-20
baseline_commit: 27b3c937
---

# G6-SCREEN1b — PS2 and PS1 fill the 4:3 handheld box (hub, opt-in; client source; candidate APK, tablet only)

**Result:** `evidence/G6_SCREEN1B_PS2_PS1_FILL_2026-11-20.md`.

- **Hub files (opt-in; a launch without `display=handheld` is identical, `no_field_identity_check.txt`):**
  - `companion/ps2_patches.py`: `handheld_toggles`, `handheld_line`, `journal_game_ini` / `restore_journal`
    (`data/games/ps2/handheld_ws_journal.json`), `settings_read_in_log`;
  - `companion/games/emulator_manager.py`: `launch(display=…)`. Inside the PS2 branch only:
    - `_launch_pcsx2(handheld=True)` journals and writes the title's game settings with the widescreen patch off,
      and puts them back before returning (and on its failure paths);
    - every PS2 launch first puts back a journal a crash left;
    - `status()` adds `"widescreen": false` only for a handheld PS2 session;
  - `companion/plugins/games.py`: the launch action passes `display="handheld"` only when the request has it;
  - `companion/relaunch_ports.py`: a handheld PS2 session's multitap relaunch carries it;
  - `tests/g6_screen1b/test_g6s1b.py` (12 tests).
- **Client files:**
  - `MainActivity.kt`: the launch URL's added term `HandheldGeometry.launchSuffix(useHandheldGameScreen())`;
  - `HandheldInput.kt`: `Fill` (crop 4:3 / stretch PS1 / none), `fill()`, `ps1Content()` (`202,0,876x720`, from
    C5-M4's measurement), the stretch's surface, `launchSuffix`;
  - `HandheldStreamActivity.kt`: the fill, H12's override, the report;
  - `NativeStreamActivity.kt`, **hook only:** H12 `onGameWidescreen` (no-op default; one call after H10);
  - `G6Screen1bTest.kt` (5 tests).
- **Not changed:** the manifest, `PadSlots.kt`, `PointerGuard.kt`, `tools/`, `patch_toggles.json`, the pins.
- **Diff:** `evidence/g6_screen1b_2026-11-20/g6_screen1b.diff` (predecessor / after sha256 beside it).
- **APK:** candidate `adcb1222…`, for the tablet only. The onn keeps `ca53df0d…`.
- **The companion's restart** (the user's, after the commit, only when no game is playing):

  ```bash
  curl -s localhost:8765/plugins/games/status | grep -q '"active": false' || echo "STOP: a game is running"
  systemctl --user restart privyhub-companion
  MP=$(systemctl --user show -p MainPID --value privyhub-companion)
  ss -lntp | grep ':8765 ' | grep -q "pid=$MP," && echo "8765 owned by $MP"
  ```

- **Rollback:** `git apply -R docs/memory/evidence/g6_screen1b_2026-11-20/g6_screen1b.diff` (checked with `--check`),
  then the same restart. On the tablet, reinstall SCREEN1's `e4263fd9…` (or G6-HM4b's `965d4f19…`). If a crash left
  `data/games/ps2/handheld_ws_journal.json` behind, the next PS2 launch puts it back (this code). After a rollback,
  delete it only once its files are back.
