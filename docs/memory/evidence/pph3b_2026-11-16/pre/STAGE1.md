# PP-H3b stage 1 (2026-11-16 21:49:25-21:53Z, unattended; outside 04:30-05:30Z and not within 45 min before it)

- **This repo** at **`363f538f`** (queue AQ: B114, B115, B116, the task), clean but for this record; only the two units
  (`privyhub-companion`, `privyhub-diag`; no system unit); no game; **eighteen lines; adb up; `--check` ok; the APK
  `ca53df0d…` CONFIRMED** (`head.txt`, `check_before.json`, `processes_before.txt`, `status_before.txt`).
- **The board's repo** at **`f1adc44`** ("the board draws at 10 fps while the hub's game is on the TV, with its check")
  — B116's two files committed, newer than `820673c`; `minigames/hub_minigame.gd` `4706a28b…`,
  `checks/hub_minigame_check.gd` `c09036b7…` (as B named them); `git status --short` empty, `--ignored` only `.godot/`
  (`board_repo_before.txt`).
- **The sidecar** for T88 in the rules folder, as PP-H3: `<id>.party.json` = `{"players": 2, "scores": {"end_P1": [1,
  0], "end_P2": [0, 1]}}` (`dcabc105…`); **the board's config** renderer `gl_compatibility` (`sidecar_and_config.txt`).
- **Both drop-ins** (B99's `.conf` byte for byte; PP-H2's / PP-H3's `privyhub-party.conf`); daemon-reload; **the
  companion restarted 21:51:32Z — MainPID serving 8765, its start after HEAD's commit time (21:48:22Z), so it runs
  queue AQ's code**; **twenty lines, the two new `PRIVYHUB_H7=1` and `PRIVYHUB_PARTY=1`**; the keeper not restarted
  (`dropins.txt`, `restart_at.txt`, `twenty.txt`, `check_with_flags.json`).
- **The onn** (`onn_offers.md`): Games → "PrivyParty (1)" (last) → "PrivyParty" → Launch on Companion → Start Fresh
  (no Continue, no recovery save); Sony pads, confirm = ✕ (the lobby's start), back = ○, map = △; the paused bar RESUME
  PLAYING · SAVE · LOAD · END. **How the board picks:** unchanged since PP-H3 — a shuffled bag of "Button mash" and "On
  the hub", one of each two mini games the hub's; nothing sets it without editing the board — the board's draw.
- **Before:** 161 save files, no `.state8`; the pictures 116 files / 15,039,288 bytes; both repos clean; `party.jsonl`
  84 rows; bitrate rows 5,985; recovery log 2,310; `launch_orphaned` 2 (`saves_before.txt`, `pictures_before.txt`,
  `log_marks.txt`, `drive_before.txt`, `profiles_before.txt`).
