# PP-H1 close (2026-11-16 16:29Z, unattended)

- **Nothing left running:** no Godot executable (by command name), no emulator, no encoder (`processes_close.txt`); no
  game, no stream (`status_close.txt`). The X display as before (the game's window gone after each F10).
- **The companion and the keeper not restarted** (MainPIDs and start times as at stage 1; `units_close.txt`); only
  the two units. **Eighteen lines before = after; `--check` ok** as at stage 1 (`check_close.json`, `eighteen.txt`).
  No flag; no drop-in; no `e3_flag.conf`.
- **The board game's repo** (`board_repo_close.txt`): HEAD as before; **`git status --short` empty, as before**; with
  `--ignored` only Godot's cache `.godot/` (772 KB, git-ignored) — left in place. Its files not edited; nothing
  committed there.
- **The owner's pictures folder** (`pictures_close.txt`): 116 files, 15,039,288 bytes, the listing hash the same —
  before = after.
- **The hub's saves** (`saves_close.txt`): 161 before = after, every name and hash; no `.state8`; no emulator started.
- **Godot's own folders under home** (`godot_user_dirs_after.txt`): made by Godot itself during the runs (the game's
  user data, Godot's settings and cache) — absent before, left in place, nothing deleted.
- **Off both repos, A's:** the tools folder (Godot 4.7.2), A's working folder (the download, the scripts, the run
  outputs, two check pictures). Nothing written to the drive; nothing installed; nothing deleted.
