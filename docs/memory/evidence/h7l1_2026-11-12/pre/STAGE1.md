# H7-L1 stage 1 (2026-11-12 00:03:08-00:04:38Z, unattended; outside 04:30-05:30Z; no game, no movie)

- The read line 00:03:08Z. HEAD **`b2699494`** (queue AK committed — B98 / B99's files and the route in it; `head.txt`,
  `ak_committed.txt`); the tree clean (`git_status_before.txt`).
- **Preconditions** (`check_before.json`, `apk_readback.txt`, `units_before.txt`, `keeper.txt`, `status_before.txt`):
  only the companion and `privyhub-diag`; no game active; eighteen lines, `--check` ok; **the APK on the onn read back
  `ca53df0d…` CONFIRMED** (adb, read only; no install). The drive (`drive_before.txt`); input profiles (`profiles_before.txt`).
- **The bench drop-in for the sitting only** (`dropin.txt`, `nineteen.txt`): `b99-h7-live-read.conf` byte for byte as B
  wrote it; daemon-reload; the companion restarted 00:03Z (`restart_at.txt`), its MainPID serving 8765; **nineteen lines
  read back, the nineteenth `PRIVYHUB_H7=1` — the bench flag**; `--check` not ok on the environ only (every other item
  as before; `check_with_flag.json`); the keeper not restarted.
- **The rule in place** (`rule_copy.txt`): T88's kept `rule.json` copied into the rules folder under the hub's id for T88
  (the id and the path off the repo); its sha256 = the kept file's (`1584bf23…`). The kept folder's five copies read back OK.
- **The route** (`route_first.txt`): 200 `{"ok": true, "running": false}`.
- **The Continue check** (`continue_check.txt`): T88's Continue copy = the kept `end_p2_b` copy by hash (`183f4071…`; the
  user's last save, mid-fight, player 2 ahead, H7-P3's 110 / 140) → **L0 runs**. T88's slots 1-3 still empty (H7-P3).
- **The marks** (`log_marks.txt`, `orphan_mark.txt`): adaptive bitrate rows 1,722; recovery log rows 1,356,
  `launch_orphaned` 0; `h7_reads.jsonl` absent; game logs 955; the journal mark 00:03:29Z.
- **The presses to Resume** (from the client's source, `MainActivity.kt` / `PausedBar.kt`): the paused bar reads, left to
  right, the RESUME PLAYING picture of the paused game, SAVE, LOAD, END (no DISC: a one-disc game) — **from SAVE, one press
  Left, then OK** resumes. Where the focus lands on coming back to PrivyHub is not set by the bar (the app restores the
  list's last tile), so that part is not counted; the user reaches SAVE as at HOME-12V.
- **Pre-registration** `../preregistration.md` hashed 00:04:35Z (`8c86a703…`).
- **The watcher** from 00:04:36Z (GET only, once a second, its output off the repo; `watcher_started_at.txt`).
