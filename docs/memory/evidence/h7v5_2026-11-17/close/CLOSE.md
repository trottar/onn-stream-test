# H7-V5 close (2026-11-17 05:43:33-05:46Z, unattended)

- The board quit at step 19 (F10, exit 0); **nothing running** (`processes_close.txt`).
- **Both drop-ins removed** (moved to A's off-repo working folder — nothing deleted); daemon-reload; **the companion
  restarted — its journal: stopping, stopped, started; no SIGKILL** — its MainPID serving; **eighteen lines, the same as
  before; `--check` ok** (`restart_journal.txt`, `check_close.json`, `eighteen.txt`).
- **Both routes gone:** `party-minigames` 400 "Unknown Games plugin action: party-minigames"; `bench-release` 400
  "Unknown Games plugin POST action: bench-release" (`routes_close.txt`). The keeper not restarted.
- **The drive before = after; no profile changed**; `launch_orphaned` 2 → 2.
- **The rules folder** (`rules_folder.txt`, ids replaced): both specs (B126's), both setups' begins, both sidecars with
  `cheat` stay, with T88's renamed-aside spec (`.endscreen.h7v3.*`) and sidecar (`.party.normal.json`) beside them;
  nothing deleted. No `e3_flag.conf`; both bench flags absent.
