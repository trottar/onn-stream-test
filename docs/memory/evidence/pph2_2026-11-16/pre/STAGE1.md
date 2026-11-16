# PP-H2 stage 1 (2026-11-16 17:35:21-17:46:43Z, unattended; outside 04:30-05:30Z; no game, no movie)

- **This repo** (`head.txt`, `git_status_before.txt`): HEAD **`81e00de6`** (queue AO committed — B107, B108, the PP-H2
  task); the tree clean but for this record. Only the two units; no game, no stream, no Godot (`units_before.txt`,
  `status_before.txt`, `processes_before.txt`). **Eighteen lines; adb up (no connect needed); `--check` ok; the APK
  `ca53df0d…` CONFIRMED** (`check_before.json`, `eighteen.txt`).
- **The board's repo** (`board_repo_before.txt`): HEAD **`d774402d`** (the PC side's one commit since PP-H1, "Step 19
  check: do not depend on how many corners a short piece has" — `checks/step19_round_bodies.gd` only); clean. HEAD
  changed → **the import, then the 25 checks headless exactly as PP-H1: 25 of 25 PASS** (`checks.md`,
  `checks_results.tsv`; 17:35:44-17:45:22Z, 9.5 min).
- **The config file off the repo** (`config_fields.txt`): the companion's config home, fields godot, project,
  pictures, renderer (`gl_compatibility`); values never recorded.
- **The bench drop-in** (`dropin.txt`, `nineteen.txt`, `check_with_flag.json`): `privyhub-party.conf`,
  `Environment=PRIVYHUB_PARTY=1`; daemon-reload; the companion restarted 17:36:11Z, its MainPID serving; **nineteen
  lines, the nineteenth `PRIVYHUB_PARTY=1`**; `--check` not ok on the environ only; the keeper not restarted.
- **The onn** (`onn_offers.md`): Games → **"PrivyParty (1)"** (the last of eight systems) → the game **"PrivyParty"** →
  Launch on Companion → Start Fresh; Sony pads → ✕ / ○ / △; the board's confirm = ✕ (starts the game in its lobby),
  back = ○, map = △; the join lines; the paused bar.
- **The hub's own launch** (`selflaunch_answers.md`, `selflaunch_party_rows.jsonl`, `selflaunch_window.txt`,
  `selflaunch_audio.txt`, `selflaunch_joypads_headless.txt`; 17:45:33-17:46:03Z): the launch 200 in 1.7 s, active and
  paused, `launch_kind` godot; **W** the window by class PrivyParty in 0.79 s, **1920 × 1080 at 0, 0, fullscreen**;
  **A** one sink-input with the board's pid; **D** the `pads` row P1-P4 in event order 11-14; **Q** the stop → F10 →
  `quit 0`, `exited` code 0 in 0.31 s, no `sigterm` row. All met → the sitting. A's own headless joypad line: four
  devices, 0-3 = P1-P4 by their GUIDs (recorded, not a cell).
- **Before** (`saves_before.txt`, `pictures_before.txt`, `board_repo_before.txt`, `log_marks.txt`, `orphan_mark.txt`,
  `drive_before.txt`, `profiles_before.txt`): 161 save files, no `.state8`; the pictures 116 files, 15,039,288 bytes;
  bitrate rows 5,554; recovery log 2,199; `launch_orphaned` 2; `party.jsonl` 8 rows (stage 1's launch).
- **The watcher** (status, the stream's audio / video counters, the encoder's and Godot's CPU, the graphics busy
  share; once a second, read only, off the repo) from 17:46:16Z. **Pre-registration hashed 17:46:43Z (`77dbedb8…`).**
