# H7-D2 — pre-registration (hashed at stage 1, before the first launch; nothing perceptual; nothing adopted)

Task: `handoffs/H7-D2_PAUSED_WINDOW_PICTURES_TASK.md`. T88 = H7's 2-player PS1 title; T89 = the users' N64
four-player title; each under its cheat setup. **Pass P**, once per title (T88 then T89): the cheat launch on loopback,
`PAUSED`, no `bench-release`; `h7-start?keep=1&bench=1`; segments S0 (nothing, 12 s), S1 (2 frames), S2 (10), S3 (30),
S4 (90), S5 (210) — 6 s each, `FRAMEADVANCE` 60 ms apart —, S6 (3 s running, then paused, 6 s), S7 (running, 10 s),
`GET_STATUS` after each; `h7-stop`; `stop`. **Pass Q**, once per title: the board launched and released; a held start
(`bench=1&hold=1`; T88 seats 1,2, T89 seats 3,1,4,2); after the `minigame_frame_advance` row, 30 × `FRAMEADVANCE` 60 ms
apart; the result and `h7-result` once a second until `ready` (→ the go → `playing` → the end) or `given_up`
(recorded, no retry); the board closed after both. Both bench flags for the task only. Before: 228 files, no `.state8`.

- **L:** each launch under its setup (`cheat_session.profile_id` the title's), stopped at its end; nothing left running.
- **D:** each `h7-start` answered `"begin": "setup"`; no N64 load unless `PAUSED`; the status word after every segment
  recorded (a `PLAYING` before S6 a finding, recorded with its segment).
- **K:** each pass P's keep folder holds ≥ 55 pictures with an `index.csv` row each.
- **U:** every file before = after (the setups' in-game saves recorded, not a cell); no `.state8`.
- **MET** = L, D, K and U. MET says the pictures and reads exist — not why the start was missed, and not whether Q
  reached `ready`. Pass P's reads are **not masked** for RetroArch's "Paused." label (a plain `h7-start`); pass Q's are.
