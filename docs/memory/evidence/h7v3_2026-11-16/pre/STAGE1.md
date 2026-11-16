# H7-V3 stage 1 (2026-11-16 15:00:48-15:07:12Z, unattended; outside 04:30-05:30Z; no user, no onn, no pads)

- The read line 15:00Z (`read_line_at.txt`). HEAD **`7f4f9727`** (queue AN committed — B104's `tools/h7_endscreen.py`,
  B105's `companion/h7_minigame.py` and `plugins/games.py`, the H7-V3 task; `head.txt`); the tree clean but for this
  record's folder (`git_status_before.txt`).
- **Preconditions** (`check_before.json`, `eighteen.txt`, `units_before.txt`, `status_before.txt`): only
  `privyhub-companion` and `privyhub-diag`; no game; RetroArch 0; **eighteen lines; `--check` ok** (adb up; the APK
  `ca53df0d…` CONFIRMED — read only, nothing installed, no setprop).
- **The spec** (`learn_report.json`, `score.json`, `replay_k3.jsonl`, `spec_and_state.txt`): the version-1 spec's two
  files renamed aside first (`<id>.endscreen.v1.json` / `.v1.npz`, = H7-V2's `98e22dc3…` / `08ad0ac1…`; nothing
  deleted); then B's command exactly — `learn runtime/h7_frames/t88 …/t88/labels.json runtime/h7_frames
  …/h7v2_20261116_run/labels.json <rules folder>/<id>.endscreen.json` (11.76 s). **= B104's arrangement 3 in every
  number:** every class separable; screen threshold **0.0902**; start **0.1007**, end_P1 **0.1032**, end_P2
  **0.0990**; margin needed **0.0929**; masks **13,756 / 97 px**; `unlike_label` **3 / 4 / 5**; version **2**.
  **Score** (the same four arguments): H7-V1 **1,152 / 1,152**; live **495 / 507**, the 12 others `unknown`;
  **`other_read_as_screen` 0**. **Replay** `--k 3`: `ended` **end_P1 at 153.03 s** (the screen from 151.02) and
  **end_P2 at 420.03 s** (from 418.03). Spec json `06058b7b…`, npz `922415bc…`.
- **The states:** the kept "begin" beside it `361e4007…` (= the kept file's); the kept end P1 `a0efb49b…`, end P2
  `ef011ec5…`, mid-fight P1-ahead `45dc8522…`, mid-fight P2-ahead `183f4071…` — each = H7-V1's `SHA256SUMS`; read only.
- **The bench drop-in** (`dropin.txt`, `nineteen.txt`, `check_with_flag.json`): B99's `.conf` byte for byte
  (`5497a0ee…`); daemon-reload; the companion restarted 15:05:38Z, its MainPID serving 8765; **nineteen lines, the
  nineteenth `PRIVYHUB_H7=1`**; `--check` not ok on the environ only; the keeper not restarted.
- **The routes** (`routes_first.txt`): `h7-result` `{"ok": true, "state": "no_game"}`; `h7-start` 400 "no game is
  running"; `h7-stop` `{"ok": true, "watch": "none"}`.
- **Before** (`saves_before.txt`, `log_marks.txt`, `orphan_mark.txt`, `h7_frames_before.txt`, `drive_before.txt`,
  `profiles_before.txt`): **161** save files (T88's 4; slots 1-3 none; every other game's 157 joined hash `b18dbe63…` =
  H7-V2's); no `.state8`; bitrate rows 5,258; recovery log 2,140; **`launch_orphaned` 2**; `h7_results` 9 rows (the
  ninth this stage's route check); `runtime/h7_frames/`: `h7v2_20261116_run`, `t88`.
- **Pre-registration** hashed **15:07:12Z** (`d649ebb7…`).
