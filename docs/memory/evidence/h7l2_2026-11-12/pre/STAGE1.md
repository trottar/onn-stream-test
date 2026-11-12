# H7-L2 stage 1 (2026-11-12 06:25:08-06:27:21Z, unattended; outside 04:30-05:30Z; no game, no movie)

- The read line 06:25Z. HEAD **`d030aeab`** (queue AL committed — B100 / B101's files and the routes; `head.txt`,
  `al_committed.txt`); the tree clean.
- **Preconditions** (`check_before.json`, `apk_readback.txt`, `units_before.txt`, `keeper.txt`, `status_before.txt`):
  only the two units; no game; eighteen lines, `--check` ok; **the APK `ca53df0d…` read back CONFIRMED** (adb read only).
- **The bench drop-in** (`dropin.txt`, `nineteen.txt`): B99's `.conf` byte for byte; daemon-reload; the companion
  restarted 06:26Z, serving 8765; **nineteen lines, the nineteenth `PRIVYHUB_H7=1`**; `--check` not ok on the environ
  only; the keeper not restarted.
- **The mini game in place** (`minigame_copies.txt`): T88's kept `rule.json` (`1584bf23…`) and kept "begin" state
  (`361e4007…`) copied into the rules folder under the hub's id — each copy's sha256 = the kept file's.
- **Both routes** (`routes_first.txt`): `h7-read` `{"ok": true, "running": false}`; `h7-contest` `{"ok": true,
  "contest": null}`.
- **What the onn will offer** (`onn_offers.md`): `continue_available` **false**; the start box Start Fresh · Load Save ·
  Extras; "PlayStation (72)"; the game 62nd of 72, row 21 of a 3-column grid, the middle tile; the pads Sony ("✕" for
  B's "A"); the paused bar's Left-once to RESUME PLAYING.
- **Before** (`saves_before.txt`, `log_marks.txt`, `orphan_mark.txt`, `drive_before.txt`, `profiles_before.txt`): 151
  save files (T88's 4: the Continue-named copy, slot 9 and their pictures); no `.state8` anywhere; bitrate rows 1,911;
  recovery log 1,435, `launch_orphaned` 0; `h7_reads` 442; `h7_contests` absent.
- **Pre-registration** hashed 06:27:19Z (`908604a0…`); **both watchers** from 06:27:21Z (GET only, once a second, off the repo).
