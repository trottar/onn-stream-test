# PP-H3 stage 1 (2026-11-16 20:15:44-20:17:30Z, unattended; outside 04:30-05:30Z and not within 30 min of it)

- **This repo** at **`8bb21700`** (queue AP: B110, B111, B112, the task), clean but for this record; only the two units;
  no game; **eighteen lines; adb up; `--check` ok; the APK `ca53df0d…` CONFIRMED** (`head.txt`, `units_before.txt`,
  `check_before.json`, `eighteen.txt`).
- **The board's repo** at **`820673c`** ("Hub mini game: play(players) asks the hub, with its check" — the two new
  files `minigames/hub_minigame.gd` `644f0541…` and `checks/hub_minigame_check.gd` `de4c9db0…` committed, **without
  their `.gd.uid` files**, which B said to commit with them; none appeared during the task); `git status --short`
  empty (`board_repo_before.txt`).
- **The sidecar** for T88 in the rules folder: `<id>.party.json` = `{"players": 2, "scores": {"end_P1": [1, 0],
  "end_P2": [0, 1]}}` (the spec's end classes); **the board's config** renderer set back to `gl_compatibility` (PP-H2's
  second run had left `mobile`) (`sidecar_and_config.txt`).
- **Both drop-ins** (B99's `.conf` byte for byte; PP-H2's `privyhub-party.conf`); daemon-reload; the companion restarted
  20:16:34Z, its MainPID serving; **twenty lines, the two new `PRIVYHUB_H7=1` and `PRIVYHUB_PARTY=1`**; the keeper not
  restarted (`dropins.txt`, `twenty.txt`).
- **The onn** (`onn_offers.md`): Games → "PrivyParty (1)" (last) → "PrivyParty" → Launch on Companion → Start Fresh;
  Sony pads, confirm = ✕ (the lobby's start), back = ○, map = △. **How the board picks a mini game:** a shuffled bag of
  every mini game fitting the player count, each once before repeats, shuffled from the game's random seed — for two
  players "Button mash" and "On the hub", so one of the first two mini games is the hub's; **no command-line word or
  config can set it without editing the board — the board's draw**.
- **Before:** 161 save files, no `.state8`; the pictures 116 files / 15,039,288 bytes; both repos clean; `party.jsonl`
  27 rows; bitrate rows 5,751; recovery log 2,264; `launch_orphaned` 2 (`saves_before.txt`, `pictures_before.txt`,
  `log_marks.txt`, `orphan_mark.txt`, `drive_before.txt`, `profiles_before.txt`).
- **Part 1's pre-registration hashed 20:17:30Z (`5622ca89…`).** Part 2's after part 1 was met, 20:19:48Z
  (`5ac54f0c…`); the watcher (status, stream counters, the encoder's, Godot's and RetroArch's CPU, graphics busy) from
  20:19:48Z.
