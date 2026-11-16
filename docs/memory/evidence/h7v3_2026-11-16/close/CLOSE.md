# H7-V3 close (2026-11-16 15:08:53-15:09:30Z, unattended)

- The game stopped by A's `POST /plugins/games/stop` 15:08:53.653Z (200); the stream never started (inactive); no
  watch was ever started (nothing to stop); A's two GET pollers stopped (0 left); RetroArch 0.
- **The drop-in removed** from the companion's drop-in folder (moved to A's off-repo working folder — nothing
  deleted); daemon-reload; the companion restarted 15:09:27Z, its MainPID serving 8765; **eighteen lines, `--check` ok**
  (`check_close.json`; adb up, the APK `ca53df0d…` CONFIRMED, RetroArch 0, encoder 0).
- **The three routes gone** (`routes_close.txt`): `h7-result` 400 "Unknown Games plugin action: h7-result"; `h7-start`
  400 "Unknown Games plugin POST action: h7-start"; `h7-stop` 400 "Unknown Games plugin POST action: h7-stop".
- The keeper (`privyhub-diag`) not restarted (MainPID as before); only the two units (`units_close.txt`).
- **The saves:** 161 before = 161 after, **the full listing (every name and sha256) identical**; T88's 4 unchanged;
  **no `.state8` anywhere** (`saves_close.txt`). **The drive before = after** (`drive_same.txt`); **no profile
  changed** (`profiles_close.txt`). The launch counted as a play in the library's history (last played, play count),
  as every launch does — not a save, not a profile.
- **The rules folder kept** (off the repo, nothing deleted): the version-2 spec (`06058b7b…` / `922415bc…`), the
  version-1 files beside it (`<id>.endscreen.v1.json` / `.v1.npz`), B99's `.json`, the state `361e4007…` — 6 files.
- **The keep folders:** none — the watcher never started (`h7_frames_after.txt`: `h7v2_20261116_run`, `t88`, as
  before; `git check-ignore` on `runtime/h7_frames/t88` → `.gitignore:5:runtime/`).
- No `e3_flag.conf`; the bench flag absent; nothing adopted; nothing committed.
