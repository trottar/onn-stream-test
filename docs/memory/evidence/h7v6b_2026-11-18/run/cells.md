# H7-V6b — the cells, per title (pre-registered `preregistration.md`, hashed 02:13:06Z)

## Both titles (steps 4 and 10)

| cell | read | met |
| --- | --- | --- |
| 4 — the board | launched (200, `active`, `paused`, `godot`, 1.59 s) and released; the list's one line `[(2, True), (4, True)]` | **met** |
| 10 — the close of the board | `stop` → F10, exit code 0; Godot 0, RetroArch 0 | **met** |
| 10 — the users' files | 228 files before = after (every sha256: the setups' slots and slot pictures, every normal state and save); no `.state8` | **met** |
| the setups' in-game saves (recorded, not a cell) | T88's and T89's before = after — no in-game save changed | — |

## T88 (steps 5, 6, 8)

| cell | read | met |
| --- | --- | --- |
| the two keys, each launch (3) | `video_font_enable = "false"`, `menu_show_load_content_animation = "false"` after each `minigame_launch` (`config_keys.md`) | **met** |
| 5 — held start | `starting`; `minigame_start` `"hold": true`; `minigame_launch` `cheat` / `profile_matches` true | **met** |
| 5 — ready ≤ 5 s | `ready` seen 3.0 s after the start (polled once a second; the row 2.1 s); **`prepare_s` 1.276** | **met** |
| 5 — frame advance | `frames` 2, `batches` 2, `moved` 0.585, **`changed` true**, `mute_ms` 332.3, **`paused` true** | **met** |
| 5 — the read | `watching` with **no `label_mask`**, `begin` setup; **`start` at the first read, 1.0 s** (start 0.0118, screen 0.0038) | **met** |
| 5 — no route / stream before the go | none between the watch row and the go | **met** |
| 5 — held 180 s | 182 answers, every one `starting` / `ready`; **the paused proof PAUSED 184 / 184** | **met** |
| 5 — the go | `taken` → `playing`; `minigame_go` `held_s` 183.148, `remembered` false; **no `minigame_reloaded`**; route; stream `switched` false (the bench); the next proof word `PLAYING` | **met** |
| 5 — the end | the kept end P1 by hand → **`end_P1` [1, 0]**; the end (`by` board) | **met** |
| 6 — remembered, already | at once `remembered` (`preparing`), again `already`; `playing` by itself 3.0 s after the start; `minigame_go` `remembered` true, `held_s` 0.002; **no `minigame_reloaded`**; PAUSED 1 / 1 | **met** |
| 6 — the end | the kept end P2 → **`end_P2` [0, 1]** | **met** |
| 8 — practice 1 by time | `practice` true → `playing`; the kept end P1 during it → still `playing`, no scores; `minigame_practice_end` `by` time 90.01 s → `ready`, **`practices` 1**; a frame-advance row after it `changed` true, `paused` true; `minigame_ready` `after_practice` true | **met** |
| 8 — practice 2 by time | `by` time 90.003 s → `ready`, **`practices` 2**; frame advance `changed` true | **met** |
| 8 — the real go | `taken`; **no `minigame_reloaded`**; the kept end P1 → **`end_P1` [1, 0]** | **met** |
| the paused proof, T88's five preparations | PAUSED 184 / 184, 1 / 1, 2 / 2, 3 / 3, 3 / 3 — no other word | **met** |
| the hand loads (4) | every scratch removed at once, `.state8` 0 after each | **met** |
| pictures | step 5: **none** (the monitor had no `DISPLAY` — A's fault, `pictures.md`); steps 6 and 8: 1 + 3 + 3 + 3 | not a cell |

**T88: MET.**

## T89 (step 9)

| cell | read | met |
| --- | --- | --- |
| the two keys | both `"false"` after its `minigame_launch` | **met** |
| held start | `"hold": true`; `cheat` / `profile_matches` true | **met** |
| ready ≤ 6 s | `ready` seen 3.0 s after the start; **`prepare_s` 1.308** | **met** |
| frame advance | **`frames` 0**, `batches` 1, `moved` 0.7812, **`changed` true**, `mute_ms` 177.9, **`paused` true** | **met** |
| the read | no `label_mask`; **`start` at the first read, 1.0 s** (start 0.0067) | **met** |
| no route / stream before the go | none | **met** |
| one practice by time | `by` time 90.001 s → `ready`, **`practices` 1**; frame advance `changed` true (14 frames, mute 1154.3 ms); `after_practice` true | **met** |
| the real go | `taken`; **no `minigame_reloaded`** | **met** |
| results | results_1 by hand while PAUSED → **places [1, 2, 3, 4], scores [4, 3, 2, 1], seats [3, 1, 4, 2]** | **met** |
| the paused proof (2 preparations) | PAUSED 2 / 2, 2 / 2 | **met** |
| the hand load (1, N64) | `PAUSE_TOGGLE` → `PAUSED` → loaded → resumed; scratch removed, `.state8` 0 | **met** |
| pictures | 3 + 3 | not a cell |

**T89: MET.**

Pass T: not run (no preparation given up).
