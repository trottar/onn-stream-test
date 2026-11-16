# PP-H3 close (2026-11-16 20:33:44-20:35:30Z, unattended; after the user left the game from the onn's top bar)

- The companion was stuck (no route answered since 20:29:19Z; 208 of 214 threads waiting on a lock). A's watcher
  stopped. **F10 to the board's window** by xdotool (20:33:58Z) → **the board exited normally, code 0** (left as a
  zombie: its parent, the stuck companion, did not reap it). **RetroArch's own `QUIT`** twice on its command port
  (20:34:09Z, 20:34:29Z) → no exit (it stood paused at its launch). (`manual_stop.txt`)
- **Both drop-ins removed** (moved to A's off-repo working folder — nothing deleted); daemon-reload; the companion
  restart (20:34:52Z) took **20.6 s**: the stuck main process did not stop and systemd ended the service's processes
  with **SIGKILL** at its 20-s stop timeout — RetroArch, its launcher and the two encoder processes among them
  (`restart_journal.txt`). The new MainPID serving; **eighteen lines, the same as before; `--check` ok**
  (`check_close.json`, `eighteen.txt`).
- **The routes gone:** `party-minigames` 400 "Unknown Games plugin action: party-minigames"; `bench-release` 400
  "Unknown Games plugin POST action: bench-release"; `h7-result` 400 (`routes_close.txt`). **The board's entry gone**
  from the systems answer. **No board, Godot or RetroArch process left.** The keeper not restarted; only the two units.
- **The saves:** 161 before = after, every name and sha256; no `.state8` (`saves_close.txt`). **The pictures** 116
  files / 15,039,288 bytes, unchanged. **The board's repo** clean before and after (`--ignored` the same). **The drive
  before = after; no profile changed**; `launch_orphaned` 2 → 2.
- The sidecar (rules folder) and the board's config (renderer `gl_compatibility`) stay off the repo.
