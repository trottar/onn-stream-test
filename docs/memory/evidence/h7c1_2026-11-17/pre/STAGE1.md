# H7-C1 stage 1 (2026-11-17 00:28-00:33Z, unattended; outside 04:30-05:30Z and not within 45 min before it)

- **This repo** at **`0408fddc`** (PP-H3b committed, with this task), clean but for this record; only the two units;
  no game, no movie; **eighteen lines** (no flag in this task); adb up; **`--check` ok; the APK `ca53df0d…` CONFIRMED**
  (`head.txt`, `units_before.txt`, `check_before.json`, `eighteen.txt`).
- **The game:** the user's N64 four-player fighting title, its name in the git-ignored title file — **T89** (the next
  unused label; T88 is H7's 2-player PS1 title). The onn's offers (`onn_offers.md`): "Nintendo 64 (13)", Down 3 /
  Right 1, `max_players` 4 and four ports → **four pads can join**; `continue_available` true (slot 1 holds a save) →
  Start Fresh; **slots 2 and 3 empty → two SAVEs asked (start → 2, first results → 3)**; Sony pads, A = ✕, B = □, Z = L2,
  Start = OPTIONS, the left stick.
- **The keeper** (`picture_keeper.py`, H7-V2's, its window fixed to the visible window of class `retroarch`): one
  picture a second while RetroArch runs, JPEG q90, full window, `index.csv`; the run folder
  `runtime/h7_frames/t89_c1_20261117T003035Z/` — `git check-ignore` → `.gitignore:5:runtime/` before any file; niced 10;
  off the repo. Ready, started with the first line (it keeps nothing until RetroArch runs).
- **The watchers:** the status once a second (PP-H3b's watch: the stream's counters, the encoder's and RetroArch's
  CPU); the recovery log and the bitrate log from their marks (`pad_slots`, `launch_ports`, stalls, the level).
- **Before:** 161 save files, no `.state8`; T89's 4 (slot 1 + its picture, the hub's own `.state` + picture); the
  in-game `.srm` and the hub's slot index hashed (outside the save-state rule, recorded); the drive; the profiles;
  `launch_orphaned` 2; recovery log 2,354 rows, bitrate 6,483 (`saves_before.txt`, `srm_before.txt`,
  `drive_before.txt`, `profiles_before.txt`, `log_marks.txt`).
