# PP-H2 close (2026-11-16 17:54:39-17:55:10Z, unattended; the board already ended by the user's END)

- The watcher stopped (0 left); no board process left (no Godot executable), no emulator, no encoder
  (`processes_close.txt`).
- **The drop-in removed** (moved to A's off-repo working folder — nothing deleted); daemon-reload; the companion
  restarted 17:55:02Z, its MainPID serving; **eighteen lines, the same as before; `--check` ok** (`check_close.json`,
  `eighteen.txt`; adb up, the APK `ca53df0d…` CONFIRMED). **The board's entry gone** from the systems answer
  (`systems_close.txt`). The keeper not restarted; only the two units (`units_close.txt`). No `e3_flag.conf`.
- **The saves:** 161 before = after, every name and sha256; no `.state8` (`saves_close.txt`). **The pictures folder:**
  116 files, 15,039,288 bytes, the listing hash the same (`pictures_close.txt`). **The board's repo:** HEAD `d774402d`,
  `git status --short` empty before and after, `--ignored` the same (only its `.godot/` cache) (`board_repo_close.txt`).
  **The drive before = after; no profile changed.** `launch_orphaned` 2 → 2 (`log_marks_close.txt`).
- **The config file stays off the repo** (the companion's config home; its renderer left at `mobile` from the second
  run — read only when the flag is on).
