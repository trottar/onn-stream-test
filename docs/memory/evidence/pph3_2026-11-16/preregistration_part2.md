# PP-H3 part 2 — the sitting's pre-registration (hashed after part 1 was fully met, before the first line)

Part 1 MET (`part1/cells.md`): the list one entry with 2 players; seats 1,2 → `end_P1` [1, 0]; seats 2,1 → `end_P2`
[0, 1]; the title gone and the board back each time; the board's own script's draw line and `[0, 0]`; the board quit by
F10 with exit code 0; no key to the board during a mini game; nothing of the user's touched. Both flags stay on.

The user at the TV with the onn and two pads paired to the onn; nothing asked on the hub; the lines as the handoff
gives them (the first match plain; Home and RESUME in the second). T88 = H7's 2-player PS1 title. The watchers from
before the first line: the status, the party rows, the board's own log, the recovery log, the CPU of the encoder,
Godot and RetroArch, once a second, read only, off the repo. Marks before the sitting: `party.jsonl` 64 rows; the
recovery log, the bitrate rows and `launch_orphaned` (2) read again at the first line.

## The cells — nothing perceptual; nothing here adopts anything

- **M1, M2 — the result:** for each match the hub's `minigame_ended` row names the class and scores that make **the
  user's winner** the winner (scores in the order of the seats the board sent), **and the board's own log credits that
  seat** (its `PrivyParty: hub mini game: scores … for seats …` line); the user's two lines verbatim.
- **X — the hand-overs:** between each `minigame_start` and `minigame_end` the onn's stream session did not end but
  for the user's own Home; **two `minigame_stream` rows "switched": true per match**; no stall row, no recovery row, no
  new `launch_orphaned`.
- **K — no key to the board during a match:** no board `pause` / `resume` / `quit` row between `minigame_playing` and
  `minigame_end`.
- **H — Home paused the title and RESUME resumed it**, in the second match (the title's rows; the status paused true,
  then false).
- **E — END quit the board by F10**, exit code 0, no `sigterm` row.
- **U — nothing of the user's touched:** the saves before = after (count and hashes), no `.state8`; the pictures' count
  and bytes unchanged; the board repo's `git status --short` after = before.
- **Recorded, no bar:** the seconds each hand-over took on the host (the `minigame_stream` rows) and what the client
  reported; the seconds from the select screen's return to `ended` and from `ended` to the board's picture; how many
  board rounds passed before each emulator mini game; frames a second, the bitrate's level, loss; the encoder's,
  Godot's and RetroArch's CPU while the title plays.
- **"stuck"** at any time: the rows and the status read, one plain sentence, the step (`party-minigame-end` if a mini
  game is on, else END); the match it happened in recorded **not met**. **"close":** END if a game runs, then the close.

**MET** = part 1 met and M1, M2, X, K, H, E and U met. Anything else NOT MET.
