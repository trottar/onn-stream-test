# H7-C2 — the cells (`preregistration.md`, sha256 `214c5a0e…`, hashed 02:48:15Z; the run 02:48:58-02:53:22Z, unattended)

| cell | what was read | met |
| --- | --- | --- |
| **L** — the launches | T88: `launch?id=…&cheat_source=0&cheat_indexes=…` (the onn's call from `cheat-profiles`) → 200 in 1.66 s, `active`, `paused`, `cheat_session` `profile_id` = **T88's cheat setup's**, activation verified; T89: the same → 200 in 2.39 s, `profile_id` = **T89's cheat setup's**, activation verified (`session_rows.md`); each `stop` → 200, RetroArch gone within 1 s; nothing left running (no RetroArch, Godot or encoder) | **met** |
| **D** — the loads | seven loads (T88: slot 1, end P1, end P2, mid-fight; T89: slot 1, results_1, begin), **each answered `LOAD_STATE_SLOT 8` (4-16 ms) and its load line naming the scratch 30-57 ms after the send** (16,777,240 / 16,793,440 bytes); every N64 load at `GET_STATUS` **PAUSED** (slot 1 paused at the launch; the two later ones paused by `PAUSE_TOGGLE` first, `PLAYING` after); **every scratch removed** (`t88_run.txt`, `t89_run.txt`) | **met** |
| **K** — the pictures | T88 141, T89 102; one a second, **no gap** (largest steps 1.01 / 1.00 s); every load's stretch inside its run: T88 41 / 40 / 40 / 20, T89 41 / 41 / 20 (`loads.md`, `keeper_t88.md`, `keeper_t89.md`) | **met** |
| **U** — nothing of the users' touched | **173 save-state files before = after, every name and sha256** (the states root 109; T88's and T89's cheat setups 4 each; every other setup the same); **no `.state8` anywhere**; recorded: every setup's in-game save the same hash before and after (`saves_before.txt`, `saves_close.txt`) | **met** |

**MET** — L, D, K and U.

**The screens (for Cowork's labels, not cells; `loads.md`):** T88 — the users' cheat slot 1, **the kept end P1 and end
P2 (locked when pictured in H7-V1) show the unlocked grid under the cheat setup**; the mid-fight is a fight. T89 — the
users' cheat slot 1 unlocked; results_1 the results screen; **the kept begin stays locked under the cheat setup**.
