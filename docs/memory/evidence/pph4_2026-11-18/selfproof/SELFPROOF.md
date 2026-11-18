# PP-H4 the streamed self-proof — the user alone (2026-11-18 19:19-19:21Z): MET

- Line 1 sent at 18:47Z; **nothing streamed by A until the user's "ok"** (19:19Z). The user launched the board from the
  onn at 19:19:25Z: **no `board_import` row** (B148's test 0); the board released at the lobby.
- After "ok": T88 held, seats 1,2 (no `bench`) → ready 2.6 s after the start (`prepare_s` 1.292), the cheat row, frame
  advance 2 frames `changed` / `paused` true, mute 356.0 ms, PAUSED from the watch row to the go (`paused_proof.txt`);
  the go → **switch 1** to the title (`planned`, `switched`, 3.506 s); `playing`; **the title held 6 s**; the end
  (`given_up` "ended before a result (board)" — A's own end, as planned) → **switch 2** to the board (`planned`,
  `switched`, 1.676 s); the board alive.
- **S on both switches (read; switch 1's next starts 6.4 s after it):** switch 1 — sound 1.4 s after T (depth 10),
  underrun rises max 0, lost 0, max arrival gap 3310 ms → met; switch 2 — sound 1.4 s after T (depth 8), 15 rows to 30 s,
  rises max 0, lost 0, max gap 1482 ms → met (`s_read.txt`, `heartbeat_audio.tsv`). **S MET.**
- The band in none of the 3 encoder argv lines since N_ENC (the board, the title, the board).
