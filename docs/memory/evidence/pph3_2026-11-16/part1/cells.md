# PP-H3 part 1 — the cells (`preregistration_part1.md`, sha256 `5622ca89…`, hashed 20:17:30Z; run 20:17:37-20:19:08Z, unattended)

| cell | what was read | when (UTC) | met |
| --- | --- | --- | --- |
| **P6** — the board by itself, released | `launch` 200 in 1.7 s: active, paused, `launch_kind` godot (window by class 0.8 s, sound by pid, pads P1-P4); `bench-release` → `"released": true`; the status unpaused | 20:17:37-20:17:41 | **met** |
| **P7** — the list | `party-minigames` → one entry `mg_e2c501a2f027`, **`"players": 2`** | 20:17:41 | **met** |
| **P8** — seats 1,2 | `starting` → **`playing`, `recognised` true at 8.3 s**; the active window the title's (its AppImage process), 1920 × 1080 at 0, 0; rows `minigame_route` {"1": 1, "2": 2}, `minigame_stream` switched false ("the stream is not up"), `minigame_watch` loaded, `minigame_playing` | 20:17:49-20:17:57 | **met** |
| **P9** — the end P1 state by hand | `LOAD_STATE_SLOT 8` answered; RetroArch's load line (16,777,240 bytes, the scratch) 41 ms after the send, 20:18:04.854Z; the copy removed → **`ended`, `end_P1`, `scores` [1, 0]** (`minigame_ended` 20:18:10.333Z, **5.5 s** after the load line) | 20:18:04-20:18:10 | **met** |
| **P10** — the end | `party-minigame-end` → `"ended": true` (0.23 s); **RetroArch gone**; the active window the board's (Godot); the status `launch_kind` godot; a second end → **`"again": true`**; rows `minigame_restore` (board alive), `minigame_stream` window board, `minigame_end` by board | 20:18:17-20:18:19 | **met** |
| **P11** — seats 2,1, the end P2 state | `playing`, `recognised` true at 8.3 s; route {"1": 2, "2": 1}; the load line 20:18:39.289Z → **`ended`, `end_P2`, `scores` [0, 1]** (20:18:44.776Z, **5.5 s**; the scores in the order of the seats given — seat 2 first); the end → `"ended": true`, RetroArch gone, the board in front | 20:18:30-20:18:46 | **met** |
| **P12** — the 15-minute give-up | **not run** (the handoff's change 1) | — | not run |
| **P13** — the board's own script, headless | A's copy of B's driver, off both repos, Godot's folders redirected to a scratch folder: `PrivyParty: hub mini game: a draw: the hub gave it up (the mini game did not start: the stream is not up)` and **`DRIVER [0, 0]`**, exit 0; rows start → launch → route → stream (not up) → `minigame_given_up` → restore → end; RetroArch gone; the board repo still clean (no file appeared) | 20:18:56-20:18:58 | **met** |
| **P14** — the board quit | `stop` → `party_exit` "quit 0": F10 → `exited` code 0 in 0.31 s; no `sigterm` | 20:19:07 | **met** |
| **K1** — no key to the board | 0 board `pause` / `resume` / `quit` rows between any `minigame_playing` and `minigame_end` (three mini games) | — | **met** |
| **U1** — nothing of the user's | saves 161 before = after, every name and hash; no `.state8`; the pictures 116 files / 15,039,288 bytes, the same | 20:19:08 | **met** |

**Part 1 MET** → part 2's pre-registration, the watchers, the sitting's first line (both flags left on).
