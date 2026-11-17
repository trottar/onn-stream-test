# H7-D1 — pre-registration (hashed at stage 1, before the first launch; nothing perceptual; nothing adopted)

Task: `handoffs/H7-D1_START_SCREEN_PICTURES_TASK.md`. T88 = H7's 2-player PS1 title; T89 = the users' N64 four-player
title; each under its cheat setup. Four passes — T88 early, T88 late, T89 early, T89 late — each with
`h7-start?keep=1&bench=1`. **Early** = the board's order: the launch with the cheat query (its answer waited for), at
once `h7-start`, at once `bench-release`. **Late** = the launch, `bench-release` at once, 15 s, `PAUSE_TOGGLE` until
`GET_STATUS` PAUSED, `h7-start`, `PAUSE_TOGGLE` back (`PLAYING`). Each pass 45 reads (`h7-result` once a second), then
`h7-stop` and `stop`. Bench flag `PRIVYHUB_H7=1` only (nineteen lines, back to eighteen). Before: 228 files, no `.state8`.

- **L — the launches:** each pass launched with its setup (`status`'s `cheat_session.profile_id` the title's setup),
  stopped at its end; nothing left running.
- **D — the loads:** each `h7-start` answered `"begin": "setup"`; no N64 load sent unless `PAUSED`; RetroArch's load
  line read for each (its absence a finding, recorded, not a failed cell).
- **K — the pictures:** each pass's keep folder holds ≥ 40 pictures with an `index.csv` row each.
- **U — nothing of the users' touched:** every file before = after (the setups' in-game saves recorded, not a cell);
  no `.state8`.
- **MET** = L, D, K and U. MET says the pictures exist; it says nothing about why the start was missed — the findings
  (the load line and its time, `recognised`, every read's class and distances, the first `start` read, the least start
  distance) are measurements for Cowork, not cells.
