# PP-H3 part 2 — the sitting's cells (`preregistration_part2.md`, sha256 `5ac54f0c…`, hashed 20:19:48Z; the sitting 20:19-20:34Z)

The user's lines verbatim (`user_lines.txt`; the title's name in one line replaced by `<the title>`): "Ready"; "Player 1
won and PrivyParty gave win to player 1"; "<the title> is stuck paused" (taken as "stuck"); "There was no end I had to
go to stop up top". (The pre-registration's mark said 64 party rows; the file held 63 — the sitting's rows are from
line 64.)

| cell | what was read | met |
| --- | --- | --- |
| **M1** — match 1 (P1 to win) | `minigame_ended` **`end_P1`, scores [1, 0]** for seats [1, 2] (20:27:33.6Z); **the board's own log: "PrivyParty: hub mini game: scores [1, 0] for seats 1,2"**; the user: **"Player 1 won and PrivyParty gave win to player 1"** | **met** |
| **M2** — match 2 (P2 to win) | the start stuck after `minigame_route` (20:29:19Z): no stream switch, no watch, never `playing`; the companion stopped answering; no result; the user's "stuck" | **not met** |
| **X** — the hand-overs | match 1: **one** `minigame_stream` "switched": true (in, 3.588 s on the host) and the back **"switched": false, "the stream is not up"**; the recovery acted at both hand-overs (three `client_stall` / `desync_pause` / `resumed` on the way in; a stall, a 5-s handover and a full encoder restart on the way back — the board's picture back 7.2 s after `ended`); the onn's session did not end; no new `launch_orphaned`. Match 2: no switch at all (stuck) | **not met** |
| **K** — no key to the board during a match | match 1: no board `pause` / `resume` / `quit` row between `minigame_playing` (20:25:41.5Z) and `minigame_end` (20:27:34.467Z) — but the recovery's `pause` (Escape) reached the board 0.24 s after `minigame_end` and its `resume` 6.1 s later; match 2: no `minigame_playing` | met for match 1 as written; match 2 not reached |
| **H** — Home / RESUME in match 2 | not reached (the title never released; the user never pressed Home in a playing match) | **not met** (not run) |
| **E** — END quit the board by F10 | **no END**: the onn offered none (the user left from the onn's own top bar); at the close A sent F10 to the board's window — **the board exited normally, code 0** (read from the kernel while it waited unreaped by the stuck companion); RetroArch did not answer two `QUIT`s on its command port and was **ended with SIGKILL** by the companion's restart (systemd's stop timeout, 20 s) | **not met** (as pre-registered) |
| **U** — nothing of the user's touched | saves 161 before = after, every name and hash; no `.state8`; the pictures 116 files / 15,039,288 bytes; the board repo clean before and after | **met** |

**Recorded, no bar:** the hand-over in 3.6 s on the host, the client's stalls 0.4-0.5 s; the way back ~7.2 s (by the
recovery); select screen → `ended` ~2 s (K = 3); the title at 59.8 fps median, 2 packets lost, 7,000 kbit/s; the
bitrate then **stepped to 5,000** by the recovery's escalation after the hand-back; while the title played the encoder
41 %, **Godot 98 %**, RetroArch 51 %, graphics 51 % (`stream_rows.md`).

**Verdict: NOT MET** — part 1 met; M1 and U met; M2, X, H and E not met: **the second mini game's start hung the
companion** (a lock held between the pads' route and the stream switch), and **the first hand-back found the stream
already down** (the title's stop took the stream with it) so the recovery, not the switch, brought the board back.
