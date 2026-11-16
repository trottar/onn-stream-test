# PP-H3b part 2 — pre-registration (hashed after part 1 was met, before the sitting's first line; nothing perceptual)

Task: `handoffs/PP-H3B_MINIGAME_RETRY_TASK.md` — B's §"A — PP-H3b" part 2 (`SESSION_B_DONE_2026-11-16AQ.md`), with the
handoff's changes 3-6. Part 1 MET (`part1/cells.md`). T88 = H7's 2-player PS1 title. The user at the TV with the onn
and two pads paired to the onn over Bluetooth; nothing asked on the hub. Four mini games: match 1 (Player 1 to win),
match 2 (Player 2 to win), match 3 (Player 1 to win, Home and RESUME PLAYING once during it), the fourth (END at its
character select screen). Marks at part 2's start (`pre/marks_part2.txt`): `party.jsonl` 162, bitrate rows 5,989,
recovery log 2,323, `launch_orphaned` 2. Nothing here adopts anything.

- **M1, M2, M3 — the result:** each match's `minigame_ended` names the class and scores that make **the user's winner**
  the winner (seats as the board sent them), **and the board's own log credits that seat** ("PrivyParty: hub mini
  game: scores [..] for seats .."); the user's lines verbatim. A match with a "stuck" is not met.
- **X — every hand-over planned, both ways, in all four mini games:** two `minigame_stream` rows per mini game
  `"switched": true, "planned": true` (window minigame, then board; END's has only the first) and a
  `minigame_switch_window` row for each; between each `minigame_start` and `minigame_end` **no recovery row that acts**
  (`client_stall`, `desync_pause`, `stall_handover_v2`, `encoder_restart`, `resumed`, `gave_up_saved`; M3's Home /
  RESUME bring only `session_ended` / `session_started`), **no board key row** (`pause` / `resume` / `quit` — but END's
  own `quit`), **no bitrate step** (no `escalation_armed`, no `transition` in the bitrate log), no new
  `launch_orphaned`. **Recorded, no bar:** each switch's `seconds`, each window's stalls not taken, the held frame each
  way (from each `minigame_stream` row's start to the client's first frame of the new stream, from the stream and client
  rows), from `ended` to the board's first frame, what the client reported, and how it looked if the user says —
  verbatim, not judged.
- **R — every route within 2 s throughout:** every `route_watch.tsv` line from the read line to the close `ok` 1 and
  `seconds` < 2.0 (the maximum per route and per stretch recorded). Checked live: a line with `ok` 0 or ≥ 2.0 s while
  the user plays is said at the user's next message in one plain sentence, R recorded not met, and the lines go on.
- **H — Home / RESUME in M3:** `minigame_taken` home → the status `paused` true (the title's pause; no board key), then
  `minigame_taken` resume_start / resume_ready → `paused` false; the match then ends with its result.
- **E — END during the fourth hub mini game** (the title on the TV): `minigame_given_up` "ended from the onn" and
  `minigame_taken` "end" → `minigame_title_stopped` → `minigame_end` "onn" → the board's `quit` and `exited` **code 0**;
  RetroArch gone (within 10 s; its own exit as the title's game log ends it, or "killed" if the hub had to); `status` →
  `active` false; no board, Godot or RetroArch process left.
- **C — Godot's CPU behind the title recorded** (the status watch's median `godot_cpu` while each `minigame_playing`
  stood, beside PP-H3's 98 % and the board's own figure in front; no bar).
- **U — nothing of the user's touched:** the saves before = after (count and hashes), no `.state8`; the pictures
  unchanged; the board repo's status after = before.
- **MET** = part 1 met and M1, M2, M3, X, R, H, E, U met.
