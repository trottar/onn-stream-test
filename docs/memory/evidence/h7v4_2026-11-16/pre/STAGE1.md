# H7-V4 stage 1 (2026-11-16 15:35:07-15:39Z, unattended; outside 04:30-05:30Z; no game, no movie)

- The read line 15:35Z. HEAD **`f19c8987`** (H7-V3 committed; the H7-V4 task in it); the tree clean but for this
  record's folder.
- **Preconditions** (`check_before.json`, `eighteen.txt`, `units_before.txt`, `status_before.txt`): only the two units;
  no game; RetroArch 0; **eighteen lines; `--check` ok; adb up** (no `adb connect` needed); **the APK `ca53df0d…`
  CONFIRMED** (read back by `--check`; no install, no setprop).
- **The spec is H7-V3's, not learnt again** (`spec_and_state.txt`, `score.json`, `score_vs_h7v3.diff`): json
  `06058b7b…`, npz `922415bc…`; `score` with B's four arguments = H7-V3's in every count (H7-V1 1,152 / 1,152; live
  495 / 507, 12 `unknown`; `other_read_as_screen` 0) — the only difference the timing field `read_ms.worst`. The kept
  begin beside it `361e4007…`; the kept end P1 `a0efb49b…` and end P2 `ef011ec5…` (read only) — as H7-V3's.
- **The bench drop-in** (`dropin.txt`, `nineteen.txt`, `check_with_flag.json`): B99's `.conf` byte for byte
  (`5497a0ee…`); daemon-reload; the companion restarted 15:37:22Z, its MainPID serving; **nineteen lines, the
  nineteenth `PRIVYHUB_H7=1`**; `--check` not ok on the environ only; the keeper not restarted.
- **The routes** (`routes_first.txt`): `no_game`; 400 "no game is running"; `{"ok": true, "watch": "none"}`.
- **The onn** (`onn_offers.md`): `continue_available` false (Start Fresh); "PlayStation (72)"; 62nd of 72 → Down 20,
  Right 1; Sony pads → ✕; the join lines; the paused bar.
- **Before** (`saves_before.txt`, `log_marks.txt`, `orphan_mark.txt`, `h7_frames_before.txt`, `drive_before.txt`,
  `profiles_before.txt`): 161 save files (T88's 4; slots 1-3 none); no `.state8`; bitrate rows 5,263; recovery log
  2,166; `launch_orphaned` 2; `h7_results` 11 rows (the eleventh this stage's route check).
- **The result watcher** (GET `h7-result` once a second, and the game's status every 10 s, off the repo) from
  15:38:33Z. **The self-proof script** (off the repo) ready: B101's load step by hand as in H7-V3 (the hub's own scratch
  path and the command port read from this session; copy → `LOAD_STATE_SLOT 8` → the load line → the copy removed).
- **Pre-registration hashed** (`prereg_hashed_at.txt`).
