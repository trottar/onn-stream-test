# H7-V6b — pre-registration (hashed at step 3, before the board is launched; nothing perceptual; nothing adopted)

Task: `handoffs/H7-V6B_CLEAN_WINDOW_BENCH_TASK.md` — B142's steps 1-10 (`SESSION_B_DONE_2026-11-17AW.md` §"H7-V6 —
again") with B138's paused proof, each party launch's two config keys, the window grabbed once a second through each
preparation, and Cowork's changes 1-7. T88 = H7's 2-player PS1 title; T89 = the users' N64 four-player title; each
under its cheat setup. B112's bench; both bench flags for the task only. **A verdict per title:** T88 = steps 5, 6, 8;
T89 = step 9; 4 and 10 belong to both (step 7 dropped, as B142). Before: 228 files, no `.state8`.

- **4:** the board launched and released; the list's one printed line **`[(2, True), (4, True)]`**.
- **Each party launch:** right after its `minigame_launch` row, `privyhub-session.cfg` carries exactly
  `video_font_enable = "false"` and `menu_show_load_content_animation = "false"`.
- **Each preparation (after a launch or a practice's way back):** **one `minigame_frame_advance` row, `"changed": true,
  "paused": true`** (`frames`, `batches`, `moved`, `mute_ms` recorded); `minigame_ready` after it; `watching` **with
  no `label_mask`**, `"begin": "setup"`; **no `minigame_route` / `minigame_stream` before its go**; **`PAUSED` at every
  paused-proof second from its `minigame_watch` row to its go**.
- **5 (T88, seats 1,2, held):** `"starting"` → `ready` with **`prepare_s` ≤ 5 s**; `minigame_start` `"hold": true`;
  `minigame_launch` `"cheat": true, "profile_matches": true`; `recognised` true (the read's second recorded).
  **Held 180 s** — every answer `starting` / `ready`. **The go** → taken → `playing`; `minigame_go` `held_s` ≥ 180;
  **no `minigame_reloaded`**; route; stream `"switched": false` (bench); the first proof word after the go `PLAYING`.
  The kept end P1 by hand → **`end_P1` [1, 0]**; the end.
- **6 (T88, seats 2,1):** a go at once → **`remembered`**; again → **`already`**; → `playing` by itself (no
  `minigame_reloaded`); the kept end P2 → **`end_P2` [0, 1]**.
- **8 (T88 practices):** held → `ready`; `go?practice=1` → `practice` true → `playing`; the kept end P1 during it →
  still `playing`, no scores; **by time** back to `ready` with `practices` 1 (`minigame_practice_end` `"by": "time"`; a
  frame-advance row after it `"changed": true`; `minigame_ready` `"after_practice": true`); a second practice by time →
  `practices` 2; a real go, **no `minigame_reloaded`** → the kept end P1 → **`end_P1` [1, 0]**; the end.
- **9 (T89, seats 3,1,4,2, held):** **`ready` with `prepare_s` ≤ 6 s**; the two keys; one frame-advance row as above
  (its `frames` recorded); one practice by time → `practices` 1; a real go (no reload) → results_1 by hand while
  PAUSED → **places [1, 2, 3, 4], scores [4, 3, 2, 1], seats [3, 1, 4, 2]**; the end.
- **The hand loads:** every scratch `.state8` removed right after its load reply (0 after each); an N64 load only after
  `GET_STATUS` PAUSED that second.
- **Every read** of every preparation recorded (second, class, distances, the first `start`); every frame-advance row
  whole; the window's pictures once a second per preparation into the git-ignored `runtime/h7v6b_frames/`.
- **10:** the board closed (F10, exit 0); nothing left; **the setups' slots and slot pictures and every normal state
  and save before = after** (every sha256); no `.state8`; the setups' in-game saves recorded (not a cell).
- **A title's first preparation given up** → that title NOT MET; its remaining steps not run; **pass T** for it
  (measurements, not a cell); the other title's steps still run.
- **T88 MET** = 4, 5, 6, 8, the keys, frame-advance rows, paused proof for T88's preparations, the hand loads and 10;
  **T89 MET** = 4, 9, the same for its preparations, the hand loads and 10. T88 MET → PP-H3c may be offered; both →
  PP-H4 after it.
