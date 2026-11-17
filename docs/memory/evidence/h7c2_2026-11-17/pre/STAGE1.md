# H7-C2 stage 1 (2026-11-17 02:45:48-02:49Z, unattended; outside 04:30-05:30Z and not within 45 min before it)

- **This repo** at **`0528701b`** (queue AR committed), clean but for this record; only the two units; no game;
  **eighteen lines; `--check` ok** (adb up, the APK `ca53df0d…` CONFIRMED) (`head.txt`, `units_before.txt`,
  `check_before.json`, `eighteen.txt`).
- **The cheat launch from loopback** (`cheat_launch.md`): `POST launch?id=…&cheat_source=…&cheat_indexes=…` — the
  onn's own call, its fields read from `cheat-profiles`; RetroArch reads and writes states in the setup's own
  `states/<core>/`; the hub's LOAD goes through the setup's slot 0. **It can be made from loopback** — the run goes on.
- **Read only, hashed** (`kept_hashes.txt`): T88's cheat setup slot 1 `be4aa243…` (+ picture), T89's cheat setup
  slot 1 `78c53af3…` (+ picture); T88's kept end P1 `a0efb49b…`, end P2 `ef011ec5…`, mid-fight `45dc8522…`;
  T89's kept begin `bc8ff296…`, results_1 `e8efe35f…` (both kept folders = their `SHA256SUMS`).
- **The bench flag for the task only:** B99's `.conf` byte for byte; daemon-reload; the companion restarted 02:47:56Z,
  its MainPID serving; **nineteen lines** (`PRIVYHUB_H7=1`); the keeper not restarted (`dropin.txt`, `nineteen.txt`).
- **The picture keeper** (H7-C1's, the visible window of class `retroarch`, one a second, full window, JPEG q90,
  `index.csv`, niced 10): `runtime/h7_frames/t88_c2_20261117T024815Z/` and `runtime/h7_frames/t89_c2_20261117T024815Z/` — `git check-ignore`
  → `.gitignore:5:runtime/` for both before any file.
- **Before:** 173 save-state files under `data/games` (the states root 109; seven cheat setups' and a mod setup's; PS2's),
  no `.state8`; every setup's in-game save hashed (recorded); `launch_orphaned` 2; the drive; the profiles
  (`saves_before.txt`, `drive_before.txt`, `profiles_before.txt`, `orphan_mark.txt`).
