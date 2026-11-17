# H7-D1 — the cells (`preregistration.md`, sha256 `0a23a873…`, hashed 05:53:37Z; the passes 05:55:37-06:01:50Z, unattended)

| cell | what was read | met |
| --- | --- | --- |
| **L** — the launches | four counted passes, each launched with its setup by the cheat query (200; `cheat_session.profile_id` the title's setup in the answer and in `status`); each stopped (`stop` 200), RetroArch gone; nothing left running | **met** |
| **D** — the loads | every `h7-start` answered `"begin": "setup"`, `loaded` true (load line 23.8-57.2 ms); the late N64 load sent only after `GET_STATUS` PAUSED (the early N64 load into the launch's paused core — the hub's own check passed); RetroArch's load line present in every pass, naming `.state8` under the setup's folder | **met** |
| **K** — the pictures | 45 pictures and 45 `index.csv` rows in each of the four keep folders (git-ignored) | **met** |
| **U** — nothing touched | 228 files before = after (every name and sha256, the setups' slots, pictures and in-game saves among them); no `.state8`; the rules folder before = after | **met** |

**MET** — L, D, K and U (the pictures exist). Disclosed: two uncounted attempts by A's driver (`passes.md`); the
drive / profiles / `launch_orphaned` compared against H7-V5's close, not a stage-1 read (`close/`).
