# PP-H3c (second try) — the cells (pre-registered `preregistration.md`, hashed 03:32:39Z; nothing perceptual)

| cell | read | met |
| --- | --- | --- |
| **Part 1** | (a) PASS (81), PASS (107); (b) the rules folder as H7-V5b left it; (c) 228 files, no `.state8`; (d) twenty lines; (e) the bench start ready (`prepare_s` 1.268), the two keys, frame advance `changed` / `paused`, no `label_mask`, PAUSED 4 / 4, no reload, **end_P1 [1, 0]**, the board quit (exit 0) | **met** |
| **The streamed self-proof** | ready (`prepare_s` 1.304); **no route / stream before the go**; the stream's capture still the board's window at ready; PAUSED 3 / 3; the go → `minigame_stream` **`switched` true, `planned` true** (1.834 s) → `playing`; `party-minigame-end` → the board back (`minigame_stream` `switched` true, the capture the board's window again) | **met** |
| **F** — no press before the go | PAUSED **6 / 6, 6 / 6, 78 / 78, 20 / 20** at the four load screens; **no `minigame_reloaded`** at any go | **met** |
| **R** — the start read | `recognised` true at the first read (1.0 s) in every preparation; none given up | **met** |
| **S** — the selection | the board asked the list and then started with **the two-player token** at both choices (the companion's journal, compared at run time, the token not recorded); `minigame_start` `players` 2, `hold` true; the list holds one two-player entry. **The board's log carries no card line** — "one card" read from the list the board was given, not from its log; who picked not recorded | **met (read from the hub's side)** |
| **PS / PT** — the practices | `"by": "start_button"` (79.65 s), then **`"by": "time"`, `practice_s` 90.001**; no `minigame_ended` inside either practice | **met** |
| **M** — the real match scored | `minigame_ended` **end_P1 [1, 0]** (03:43:27Z); the board's log "scores [1, 0] for seats 1,2" — seat 1 credited; the user: "P1, P1" (and again for the second real match, 03:51:50Z) | **met** |
| **H** — Home / RESUME | `minigame_taken` home (03:41:46Z), resume_start, resume_ready (03:42:00Z), still `playing`, then ended as M | **met** |
| **E** — END | the board paused / resumed, quit by F10, `exited` code 0; nothing running; `status` idle | **met** |
| **W** — the window clean | all four party launches' config: `video_font_enable = "false"`, `menu_show_load_content_animation = "false"` (`config_keys.txt`) | **met** |
| **U** — the users' files | 228 files before = after (every sha256); no `.state8`; **no in-game save changed** (recorded, not a cell) | **met** |

**MET.** Recorded, no bar: `prepare_s` 1.21-1.32 s; `held_s` 5.654, 4.873, 76.618, 18.837; `frames` 2 at every preparation; `mute_ms` 358-379.
