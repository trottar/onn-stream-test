# H7-V2 stage 1 (2026-11-16 03:22:19-03:28:41Z, unattended; outside 04:30-05:30Z; no game, no movie)

- The read line 03:22Z. HEAD **`17f8d95c`** (queue AM committed — `tools/h7_endscreen.py`, `companion/h7_minigame.py`,
  `companion/plugins/games.py` and both tests in HEAD; `head.txt`); the tree clean but for this record's folder.
- **Preconditions** (`check_before.json`, `apk_readback.txt`, `units_before.txt`, `keeper.txt`, `status_before.txt`):
  only the two units; no game; eighteen lines. **adb was down at the read line** (no device listed — `--check` read not
  ok on `adb` and the APK only, every host field holding, as KNOWN_ISSUES' note after a network change); **`adb connect`
  from the hub** (as HOME-4+; the address off the repo); then `--check` **ok**, **the APK `ca53df0d…` read back
  CONFIRMED** (adb read only; no install, no setprop).
- **The spec** (`learn_report.json`, `score.json`, `spec_and_state.txt`): B102's `learn` on H7-V1's frames with Cowork's
  labels, **all frames** (no `--half`) → the rules folder under the hub's id for T88. **start, end_P1, end_P2 and the
  screen "separable"; `usable` true**; gaps 51.1 / 51.6 / 51.0 (the screen 24.6); the screen mask 16,496 px (85.9 %),
  the outcome mask 124 px (the tally's patch); learn 3.5 s. **Score: 788 / 788, 72 / 72, 74 / 74, 218 / 218 right;
  `other_read_as_screen` 0**; least margin 50.8 (needed 25.4); read median 1.07 ms. `.endscreen.json` `98e22dc3…`,
  `.endscreen.npz` `08ad0ac1…`. **The kept "begin" state** beside it (already there from H7-L2): `361e4007…` = the
  kept file's.
- **The bench drop-in** (`dropin.txt`, `nineteen.txt`, `check_with_flag.json`): B99's `.conf` byte for byte;
  daemon-reload; the companion restarted 03:26:17Z, its MainPID serving 8765; **nineteen lines, the nineteenth
  `PRIVYHUB_H7=1`**; `--check` not ok on the environ only; the keeper not restarted.
- **Both routes** (`routes_first.txt`): `h7-result` `{"ok": true, "state": "no_game"}`; `h7-start` 400 "no game is
  running".
- **What the onn will offer** (`onn_offers.md`): `continue_available` **false** (Start Fresh either way); "PlayStation
  (72)"; the game 62nd of 72 → Down 20, Right 1; the pads Sony → "hold ✕"; the join lines; the paused bar: Up to the bar,
  Right to END.
- **Before** (`saves_before.txt`, `log_marks.txt`, `orphan_mark.txt`, `drive_before.txt`, `profiles_before.txt`): **161**
  save files (T88's 4: the Continue-named copy, slot 9 and their pictures; slots 1-3 none); no `.state8` anywhere;
  bitrate rows 4,902; recovery log 2,078, `launch_orphaned` 2 (both before this sitting); `h7_results` absent.
  (161, not H7-L2's 151: this listing's own rule, every `.state*` / `.p2s*` / `sstates` file under the hub's games data;
  before = after is judged on this listing.)
- **Pre-registration** hashed 03:28:31Z (`f4ce89bb…`). **The watcher** (`h7-result`, GET only, once a second, off the
  repo) and **the picture keeper** (the game's window once a second while RetroArch runs, JPEG q90, `index.csv`, under
  `runtime/h7_frames/` in a new run folder — `git check-ignore` → `.gitignore:5:runtime/` before the first file;
  niced) from 03:28:38Z.
