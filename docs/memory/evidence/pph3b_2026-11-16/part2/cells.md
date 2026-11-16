# PP-H3b part 2 — the cells (`preregistration_part2.md`, sha256 `3230644e…`, hashed 21:56:45Z; the sitting 21:56:51-22:12:20Z)

The user at the TV with the onn and two pads paired to the onn; nothing asked on the hub. The board launched from the
onn 21:58:15Z (Start Fresh), both pads joined 21:58:23Z; "ready" 21:58:57Z. The board drew its hub mini game as its
1st (22:00:02Z), 2nd (22:04:29Z), 3rd (22:07:03Z) and 4th (22:11:56Z) hub mini game; no "stuck", no "left".

| cell | what was read | met |
| --- | --- | --- |
| **M1** | seats [1, 2]; `minigame_ended` **`end_P1` [1, 0]** 22:01:45.514Z (Player 1's side won); the board's log **"scores [1, 0] for seats 1,2"** → seat 1; the user: "Player 1 and the board gave to player 1" | **met** |
| **M2** | seats [1, 2]; **`end_P2` [0, 1]** 22:06:13.872Z; the board **"scores [0, 1] for seats 1,2"** → seat 2; the user: "Player 2 and player 2" | **met** |
| **M3** | seats **[2, 1]** (the board's order: seat 2 on the title's port 1, seat 1 on port 2 — "player 1 was on the opposite side this time"); **`end_P2` [0, 1]** 22:08:55.814Z = port 2 won = seat 1; the board **"scores [0, 1] for seats 2,1"** → seat 1; the user: "Player 1 and player 1 but player 1 was on the opposite side this time" | **met** |
| **X** | **seven `minigame_stream` rows `"switched": true, "planned": true`** (M1-M3 in and back; M4 in — END's has only the first), **seven `minigame_switch_window` rows**; between each `minigame_start` and `minigame_end`: **no recovery row that acts** (the recovery log's rows in the sitting: `pad_slots`, `launch_ports`, `remote_config`, `party_session`, `input_hold_skipped_paused`, `state_save_skipped`, and `session_end_bye` / `session_ended` / `session_started` only at M3's Home / RESUME and at END); **no board key row** (no `pause` / `resume` / `quit` but END's own `quit`); **no bitrate step** (no `escalation_armed` / `transition` row; the level 7000 throughout); `launch_orphaned` 2 → 2. The held frame on the onn **0.46-0.58 s** each way; the host's switch 1.7-2.0 s (M2's 3.5 / 3.6 s); `stream_rows.md` | **met** |
| **R** | `route_watch.tsv` from part 1's start (21:53:03Z) to the close (22:12:30Z): **6,492 lines, every one `ok` 1, none ≥ 2.0 s**; the maximum — part 1: `status` 1.502, `party-minigame-result` 0.002, `native-stream-status` 0.014 s; the sitting (4,512 lines): **`status` 1.503, `party-minigame-result` 0.008, `native-stream-status` 1.502 s**; nothing said to the user (no line crossed) | **met** |
| **H** | M3: `minigame_taken` home 22:08:04.680Z → the status `paused` true (22:08:05Z; the title's pause, no board key) → `minigame_taken` resume_start 22:08:07.141Z, resume_ready 22:08:11.156Z → `paused` false (22:08:11Z); the onn's join came back and both pads held (`pad_slots` P1 22:08:09.6Z, P2 22:08:11.7Z); the match then ended with its result (22:08:55.814Z) | **met** |
| **E** | M4 at its select screen: `minigame_taken` home 22:12:08.651Z, then **`minigame_given_up` "ended from the onn" and `minigame_taken` "end"** 22:12:12.436Z → **`minigame_title_stopped`** 22:12:12.614Z → **`minigame_end` "onn"** → the board's **`quit` F10** → **`exited` code 0** (0.47 s); RetroArch gone (its game log ends as the three before it; no "killed"); `status` → `active` false; no board, Godot or RetroArch process left | **met** |
| **C** (no bar) | Godot's CPU (median, % of one core) **behind the title: M1 17 %, M2 17 %, M3 17 %, M4 18 %** (PP-H3: 98 %); **the board in front: 22-24 %**; RetroArch 43-47 %, the encoder 37-42 %, graphics 28-30 % behind the title | recorded |
| **U** | the saves 161 = 161, every name and hash; no `.state8`; the pictures 116 files / 15,039,288 bytes, the same; the board repo's status after = before (`--ignored` `.godot/` only) | **met** |

**Part 2: M1, M2, M3, X, R, H, E, U met; C recorded. With part 1 met → MET.**

**How it looked (the user's words):** none given beyond the match lines.
