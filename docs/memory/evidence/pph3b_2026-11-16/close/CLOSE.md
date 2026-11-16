# PP-H3b close (2026-11-16 22:12:31-22:13Z, unattended; after the user's "ended")

- The watchers stopped (the route watcher's last line 22:12:30Z). The board had already quit by END (F10, exit 0);
  no Godot, RetroArch or encoder process (`processes_close.txt`).
- **Both drop-ins removed** (moved to A's off-repo working folder — nothing deleted); daemon-reload; **the companion
  restarted in 0.43 s — its journal: stopping, stopped, started; no SIGKILL** (`restart_at.txt`,
  `restart_journal.txt`). The new MainPID serving; **eighteen lines, the same as before; `--check` ok**
  (`check_close.json`, `eighteen.txt`).
- **The routes gone:** `party-minigames` 400 "Unknown Games plugin action: party-minigames"; `bench-release` 400
  "Unknown Games plugin POST action: bench-release"; `h7-result` 400 (`routes_close.txt`). **The board's entry gone**
  from the systems answer. The keeper not restarted; only the two units (`units_close.txt`).
- **The saves:** 161 before = after, every name and sha256; no `.state8` (`saves_close.txt`). **The pictures** 116
  files / 15,039,288 bytes, unchanged. **The board's repo** clean before and after (`--ignored` the same). **The drive
  before = after; no profile changed**; `launch_orphaned` 2 → 2.
- The sidecar (rules folder) and the board's config (renderer `gl_compatibility`) stay off the repo. No
  `e3_flag.conf`; both bench flags absent.
