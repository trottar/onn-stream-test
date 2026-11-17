# H7-V6 — pre-registration (hashed at step 3, before the board is launched; nothing perceptual; nothing adopted)

Task: `handoffs/H7-V6_PREPARE_BEHIND_BOARD_TASK.md` — B138's steps 1-10 (`SESSION_B_DONE_2026-11-17AV.md` §"H7-V6")
with Cowork's six changes. T88 = H7's 2-player PS1 title; T89 = the users' N64 four-player title; each under its
cheat setup. B112's bench; both bench flags for the task only. **A verdict per title:** T88 = steps 5-8, T89 = step 9;
4 and 10 belong to both. Before: 228 files, no `.state8`.

- **4:** the board launched and released; the list's one printed line **`[(2, True), (4, True)]`**.
- **5 (T88, seats 1,2, held):** `ready` with **`prepare_s` ≤ 20 s**; `minigame_start` `"hold": true`;
  `minigame_launch` `"cheat": true, "profile_matches": true`; **one `minigame_frame_advance` `"frames": 2, "paused":
  true`, `"mute_ms"` < 1000**; `minigame_ready`; **no `minigame_route` / `minigame_stream` before the go**; `watching`
  `"recognise_s": 15.0, "begin": "setup", "label_mask": true`; `recognised` true. **Held 180 s** — every answer
  `starting` / `ready`. **The go** → taken → `playing`; `minigame_go` `held_s` ≥ 180, `remembered` false; **no
  `minigame_reloaded`**; then route, stream (switched false on the bench), playing; the first proof word after the go
  `PLAYING`. The kept end P1 by hand → **`end_P1` [1, 0]**; the end.
- **6 (T88, seats 2,1):** a go at once → **`remembered`**; again → **`already`**; → `playing` by itself once ready;
  `minigame_go` `remembered` true; no `minigame_reloaded`; the kept end P2 → **`end_P2` [0, 1]**.
- **7 (T88, seats 1,2):** after the `minigame_frame_advance` row, the kept mid-fight by hand into scratch slot 8 and one
  `FRAMEADVANCE` (A's only) → **`given_up` "…the title's start screen was not recognised"** ~15 s after the watch row;
  no `minigame_route`, no `minigame_stream`; RetroArch gone; `status` godot.
- **8 (T88 practices):** held → `ready`; `go?practice=1` → `practice` true → `playing`; the kept end P1 during it →
  still `playing`, no scores; **by time** back to `starting` → `ready`, `practices` 1 (`minigame_practice_end` `"by":
  "time"`; a `minigame_frame_advance` after it; `minigame_ready` `"after_practice": true`); a second practice →
  `practices` 2; a real go, **no `minigame_reloaded`** → the kept end P1 → **`end_P1` [1, 0]**; the end.
- **9 (T89, seats 3,1,4,2, held):** **`ready` with `prepare_s` ≤ 15 s** (read paused, the label's corner masked); one
  frame-advance row as in 5; one practice by time → `practices` 1; a real go (no reload) → results_1 by hand while
  PAUSED → **places [1, 2, 3, 4], scores [4, 3, 2, 1], seats [3, 1, 4, 2]**; the end. If its preparation is given up
  "not recognised": its reads recorded, T89 stopped there, no retry → T89 NOT MET.
- **The paused proof, every preparation:** one `GET_STATUS` word a second from each `minigame_watch` row to its go —
  **`PAUSED` every time**; a `PLAYING` or no answer in that stretch → NOT MET for that title (with its second).
- **Every paused read recorded** (`run/reads.md`): from `watching` to `recognised`, each read's second, class and
  distances; the first `start`.
- **The hand loads:** every scratch `.state8` removed at once (0 after each); an N64 load only after `GET_STATUS`
  PAUSED that second; A's own `FRAMEADVANCE` only in step 7.
- **10:** the board closed (F10, exit 0); nothing left; **the setups' slots and slot pictures and every normal state
  and save before = after** (every sha256); no `.state8`; the setups' in-game saves recorded (not a cell).
- **T88 MET** = 4, 5-8, the paused proof for T88's preparations, the hand loads and 10 met; **T89 MET** = 4, 9, its
  paused proof, the hand loads and 10 met. T88 MET → PP-H3c may be offered; both → PP-H4 after it.
