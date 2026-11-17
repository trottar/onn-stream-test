# H7-V5b — the cells (`preregistration.md`, sha256 `a5b943b8…`, hashed 06:58:17Z; the run 06:58:24-07:01:05Z, unattended)

| step | what was read | met |
| --- | --- | --- |
| **3-6** | the rules folder as H7-V5 left it — both specs' numbers, both begins, both sidecars' `cheat`; checked read only, before = after at the close (`pre/rules_check.md`, `close/rules_folder_close.txt`) | **met** |
| **10** | the board launched (`active`, `paused`, godot, 1.7 s); `bench-release` → released | **met** |
| **11** | two entries, 4 and 2 players | **met** |
| **12** | T88 seats 1,2: `minigame_launch` `"cheat": true, "profile_matches": true`; `status` the setup; `watching` **`"recognise_s": 15.0`**, `"begin": "setup"`, loaded; the load line naming the scratch in T88's setup; **`recognised` true at 10.0 s**; no `picture_failed` | **met** |
| **12b** | `save-state?slot=9` / `load-state?slot=9` → **400** with B's lines; two `minigame_state_refused` rows; no RetroArch save / load line; still `playing`; **T88's setup's files byte-equal** (`saveload.md`) | **met** |
| **13** | end P1 by hand → **`ended`, `end_P1`, [1, 0]** (6 s after the load); the end → RetroArch gone, `launch_kind` godot | **met** |
| **14** | seats 2,1, end P2 → **`end_P2`, [0, 1]**; the end | **met** |
| **15** | seats 1,2, the mid-fight → **still `playing` 45 s later**, no `ended`; the end → **`given_up` "ended before a result (board)"** | **met** |
| **16** | T89 seats 1,2,3,4: `cheat` / `profile_matches` true; `status` the setup; `watching` `"recognise_s": 15.0`, `"begin": "setup"`; **`recognised` true at 2.0 s**; **no `picture_failed`**; `last` start 0.0257 | **met** |
| **17** | paused (`GET_STATUS` PAUSED), results_1 by hand, the scratch removed, unpaused → **`ended`, `end`, places [1, 2, 3, 4], scores [4, 3, 2, 1]** (2.2 s after the load); the end | **met** |
| **18** | seats 3,1,4,2 → recognised 2.0 s; results_1 the same way → **places [1, 2, 3, 4], scores [4, 3, 2, 1], seats [3, 1, 4, 2]**; the end | **met** |
| **19** | `stop` → `party_exit` "quit 0": F10, `exited` code 0 in 0.36 s; no board, Godot or RetroArch process | **met** |
| **20** | **228 files before = after, every sha256** (both setups' slots and pictures, every normal state and save); **no `.state8`** (0 after each load); recorded: **neither setup's in-game save changed** | **met** |

**MET** — every step. PP-H4 may be offered.
