# H7-V6 — the cells per title (`preregistration.md`, sha256 `07a17e2f…`, hashed 23:16:14Z; the run 23:16:42-23:18:01Z)

| step | what was read | T88 | T89 |
| --- | --- | --- | --- |
| **4** — the board, the list | launched (`active`, `paused`, godot) and released; the list's line **`[(2, True), (4, True)]`** | met | met |
| **5** — T88 held | `minigame_start` `"hold": true`; `minigame_launch` `"cheat": true, "profile_matches": true`; `minigame_watch`; **one `minigame_frame_advance` (2 frames, paused, 163.9 ms)**; `watching` `"recognise_s": 15.0, "begin": "setup", "label_mask": true`; no route, no stream — **but no `ready`: `given_up` "the title's start screen was not recognised" at 15.0 s** (last read `other`, screen 0.1641 vs 0.082) | **NOT MET** | — |
| **6-8** — the remembered go, never the start, practices | not run (T88's preparation given up; no retry) | not met (not run) | — |
| **9** — T89 held | `"hold": true`; `cheat` / `profile_matches` true; one frame advance (2, paused, 196.7 ms); `watching` 15.0, setup, `label_mask` true — **but no `ready`: `given_up` "not recognised" at 15.0 s** (last read `other`, start 0.2367 vs 0.0932); the practice, the go and the results not run | — | **NOT MET** |
| **The paused proof** | **PAUSED at all 15 seconds** of each preparation (`paused_proof.md`) | met | met |
| **The hand loads** | none sent (no `ready`); no `.state8` at any time | met | met |
| **10** — the close of the board, the files | `stop` → F10, exit 0; nothing left; **228 files before = after**; no `.state8`; no in-game save changed (recorded) | met | met |

**T88 NOT MET; T89 NOT MET** — each title's paused preparation was given up "not recognised" at 15.0 s, its own begin
loaded, the title paused throughout. PP-H3c is not offered.
