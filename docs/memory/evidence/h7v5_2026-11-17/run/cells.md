# H7-V5 — the cells (`preregistration.md`, sha256 `2199bb5b…`, hashed 05:42:10Z; the run 05:42:24-05:43:33Z, unattended)

| step | what was read | met |
| --- | --- | --- |
| **3-4** — the specs | both learnt equal to `h7v5_expected/` in every number (only the learn's own seconds and the reading speed differ); the scores and the replays' end lines identical (`pre/learn_and_score.md`) | **met** |
| **5** — the begins | the setups' slot 1 copied: before = after = the copy (`be4aa243…`, `78c53af3…`) | **met** |
| **6** — the sidecars | T88's renamed aside, both written with `cheat`; nothing overwritten (`pre/renames.txt`, `pre/sidecars.txt`) | **met** |
| **10** — the board | launched (`active`, `paused`, godot, 1.7 s); `bench-release` → released | **met** |
| **11** — the list | **two entries, 2 and 4 players** | **met** |
| **12** — T88 under its setup | `minigame_launch` `"cheat": true, "profile_matches": true`; `status` `cheat_session.profile_id` = T88's setup; `watching` `"begin": "setup"`, `"loaded": true`; the load line naming `.state8` under T88's setup — **but `recognised` false after 8.0 s** (last read `other`, screen 0.0916 vs 0.082) → `given_up` "the title's start screen was not recognised"; stopped (`party-minigame-end`), no retry (`recognise.md`) | **NOT MET** |
| **13-15** — T88's ends and mid-fight | not run (change 4) | **not met** (not run) |
| **16** — T89 under its setup | `minigame_launch` `"cheat": true, "profile_matches": true`; `cheat_session.profile_id` = T89's setup; `watching` `"begin": "setup"`, loaded — **but `recognised` false after 8.0 s** (last read `other`, start 0.3175 vs 0.0932) → `given_up`; stopped, no retry | **NOT MET** |
| **17-18** — T89's places | not run (change 4) | **not met** (not run) |
| **19** — the board's close | `stop` → `party_exit` "quit 0": F10, `exited` code 0 in 0.31 s; no board, Godot or RetroArch process | **met** |
| **20** — the users' files (the cell) | **228 files before = after, every sha256** — both setups' slots and slot pictures, every normal state and save; **no `.state8`** (0 after each start too). Recorded, not a cell: **neither setup's in-game save changed** (B127 expected a flush at each stop) (`after.txt`) | **met** |

**NOT MET** — steps 12 and 16: neither title's start was recognised within the hub's 8-s window under its cheat setup
(B's named risk); 13-15 and 17-18 not run. Everything else met. PP-H4 is not offered.
