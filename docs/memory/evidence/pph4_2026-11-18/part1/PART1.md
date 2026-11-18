# PP-H4 part 1 — the gate on the bench (2026-11-18 18:38-18:46Z, nobody at the TV): MET

- **(a)** A scratch `git archive HEAD` of the board at `674407d`, Godot headless, its folders in the scratch (removed
  after; the board's repo status 0 lines): **`hub_minigame_check` PASS (97)**, `step25_before_minigame` PASS (108),
  `step26_sound_and_ready` PASS (117), `step27_winner_screen` PASS (56), `step8_modules` PASS (210) — every check changed
  since `e0ce8c4` among them (`checks.txt`).
- **(b)** The board launched on the bench → `active`; `bench-release` → `"released": true`. **B148: the test gave 0 →
  no `board_import` row** (none written).
- **(c)** `party-minigames` → two entries, players 4 and 2.
- **(d) T88 held, seats 1,2:** `starting`; **ready 2.5 s** after the start (`prepare_s` 1.267); `minigame_launch`
  `"cheat": true, "profile_matches": true`; the two keys `"false"`; frame advance 2 frames, `changed` / `paused` true,
  mute 330.3 ms; **PAUSED 18 / 18** from the watch row to the go; the go `taken` → `playing` (handover 0.082 s), no
  `minigame_reloaded`; the kept end P1 by hand (the scratch `.state8` removed at once) → **`ended` `end_P1` `[1, 0]`**;
  the end (`end_board`, the title stopped, the board alive).
- **(e) T89 held, seats 3,1,4,2:** ready **2.8 s** (`prepare_s` 1.309); the cheat row; the two keys `"false"`; frame
  advance 0 frames, `changed` / `paused` true, mute 180.4 ms; **PAUSED 11 / 11**; `go?practice=1` → `playing`
  `"practice": true`, `n` 1; no pad pressed anything, so **`minigame_practice_end` `"by": "time"`, `practice_s`
  90.001**, no `minigame_ended` inside; the board's window back; the watch again; frame advance 14 frames, mute 1153.0
  ms; **`minigame_ready` `"after_practice": true`** (`prepare_s` 1.201); **PAUSED 13 / 13**; the go → `playing`, no
  reload; `results_1` by hand while paused (PAUSE_TOGGLE → `PAUSED` → slot 8 → the scratch removed → PAUSE_TOGGLE) →
  **`ended` `end`, `"places": [1, 2, 3, 4]`, `"scores": [4, 3, 2, 1]`, seats `[3, 1, 4, 2]`**; the end.
- **(f)** The board quit by `stop` → F10, **exit 0** (0.41 s); nothing running; **every file of the before listing
  before = after** (228, every sha256); no `.state8`.

**Part 1 MET.** No `minigame_reloaded` in part 1. (The `minigame_stream` rows say `"switched": false`, "the stream is
not up" — the bench, nobody streaming.)
