# The stream's rows in the sitting (the bitrate rows after the mark 5,752; the recovery log after 2,265)

| stretch | from-to (UTC) | samples | fps median | lowest | < 50 | lost | PRESSURE | acted / level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| the board, before match 1 | 20:22:30-20:25:36 | 91 | 59.8 | 0.0 (the start) | 1 | 55 | 5 | 0 / 7,000 |
| **the title, match 1** | 20:25:41-20:27:33 | 58 | **59.8** | 51.8 | 0 | 2 | 5 | 0 / 7,000 |
| the hand-back to the board | 20:27:33-20:27:45 | 6 | 30.9 | 0.0 | 3 | 0 | 3 | — |
| the board, after match 1 | 20:27:45-20:29:18 | 46 | 59.8 | 51.9 | 0 | 3 | 0 | **5,000 after the recovery's escalation** (20:27:46) |
| match 2's start to the end | 20:29:18-20:33 | 0 | — | — | — | — | — | the rows stopped (the companion stuck) |

- **The hand-over in (match 1), 20:25:36.6Z `minigame_start` → 20:25:41.4Z `minigame_stream` "switched": true, 3.588 s
  on the host** (the capture restarted for the title's process; `ssrc_change` 20:25:41.355). **What the client did:**
  three `client_stall` rows (20:25:41.6-20:25:42.0, age 425-533 ms) → the recovery's `desync_pause` and `resumed`
  ("stall_quiet", 1.4 s / 0.2 s / 0.2 s) — the recovery acted on the title three times as the picture changed over;
  the session went on. The watch: the kept begin loaded (53.9 ms), `recognised` true at 4.0 s.
- **The hand-back (match 1):** `minigame_ended` 20:27:33.600Z (the title's `ended` row 20:27:33.456Z, 112 reads) →
  `minigame_restore` 20:27:34.231Z → **`minigame_stream` "switched": false, "the stream is not up" (20:27:34.467Z)** —
  the stream had gone down as the title stopped, before the switch back. Then the onn's session (still open) stalled:
  **`client_stall` / `desync_pause` 20:27:34.712Z** — the recovery paused the board's session (**an Escape to the board,
  party `pause` row 20:27:34.703Z**, 0.24 s after `minigame_end`); **`stall_handover_v2` after 5.08 s, `encoder_restart`
  (full start) 20:27:40.765Z → `resumed` 20:27:40.835Z (an Escape to the board, `resume` row)** — the board's picture back
  **~7.2 s after `minigame_ended`** by the recovery, not by the mini game's switch. The bitrate's recovery escalation then
  stepped the level to 5,000.
- **Match 2's start (20:29:18.3Z):** `minigame_start` → `minigame_launch` (pid owned) → `minigame_route` {"1": 1,
  "2": 2} (20:29:19.4Z) — **then nothing**: no `minigame_stream`, no watch, no `minigame_playing`; the title stood at its
  launch's pause ("<the title> is stuck paused", the user, 20:29:53Z). The companion stopped answering: `status`,
  `party-minigame-result` and `party-minigame-end` timed out (10 s); 208 of its 214 threads waiting on a lock (futex)
  — **a lock held by the mini game's start** (between the route and the stream switch) **that every route waits on**.
  The bitrate rows stopped at 20:29:18. The recovery: no row until **`gave_up_saved` 20:31:20.6Z** (its give-up save
  refused: "Saving and loading are not offered for the board game; nothing was sent."), then the user left the game from
  the onn's own top bar (`session_ended` 20:32:56Z). **No new `launch_orphaned` (2 → 2).**
- **The three CPUs** (`status_watch.tsv`, medians): the board before match 1 — encoder 42 %, Godot 21 %, graphics 21 %;
  **while the title played — encoder 41 %, Godot 98 %, RetroArch 51 %, graphics 51 %** (the board kept drawing behind
  the title at a full core); the board after — encoder 39 %, Godot 23 %, graphics 29 %.
- **From the select screen's return to `ended`:** no pictures kept (keep off); by K = 3 at a read a second, ~2 s. **From
  `ended` to the board's picture:** ~7.2 s (above). **Board rounds before match 1:** not in the board's log (it logs the
  seed and the hub's result only); the user started the game 20:23:36Z-ish and the hub mini game came at 20:25:36Z.
