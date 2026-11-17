# H7-V5 stage 1 (2026-11-17 05:35-05:50Z, unattended; outside 04:30-05:30Z and not within 45 min before it)

- **Step 1:** this repo at **`927569ca`** (queue AS), clean but for this record; only the two units; no game;
  **eighteen lines, `--check` ok** (`head.txt`, `units_before.txt`, `check_before.json`, `eighteen.txt`).
- **Step 2:** the setups read as the onn reads them (`setups.md`): T88's cheat setup — one of the title's two, the one
  with slot 1 — source 0, indexes [9]; T89's — source 0, indexes [0, 6]; their slot 1 files **`be4aa243…`** /
  **`78c53af3…`** = H7-C2's.
- **Step 3:** T88's old spec renamed aside (`.endscreen.h7v3.json` / `.npz`); no T89 spec, sidecar or begin before —
  nothing to rename (`renames.txt`); both specs learnt. **Step 4:** the learn reports, the scores and the replays' end
  lines **equal to `h7v5_expected/` in every number** — only the seconds the learn took and the reading speed differ
  (`learn_and_score.md`, `learn_score/`).
- **Step 5:** the setups' slot 1 copied into the rules folder as each title's setup begin — before = after = the copy
  (`begins.txt`). **Step 6:** T88's sidecar renamed aside (`.party.normal.json`); both new sidecars with `cheat`
  (`sidecars.txt`).
- **Step 7:** B99's `.conf` and the party drop-in; daemon-reload; the companion restarted (its MainPID serving);
  **twenty lines** (`PRIVYHUB_H7=1`, `PRIVYHUB_PARTY=1`); the keeper not restarted (`dropins.txt`, `twenty.txt`).
- **Step 8:** 228 files under the states, saves and cheat-setup folders (the normal states 109, the normal saves 56,
  each setup's slots and pictures 4, its in-game save 1, its own records 2; every other setup 49); no `.state8`;
  `h7_results` 126 rows, `party` 228 (`before.txt`); the drive; the profiles; `launch_orphaned` 2.
