# H7-C1 — pre-registration (hashed at the end of stage 1, before the launch; nothing perceptual; nothing adopted)

Task: `handoffs/H7-C1_FOUR_PLAYER_CAPTURE_TASK.md`. T89 = the user's N64 four-player fighting title. Four people at
the TV with four pads paired to the onn; nothing asked on the hub; **no flag — eighteen lines throughout**. Five
four-player matches, each with a set finishing order (M1: P1, P2, P3, P4; M2: P2, P3, P4, P1; M3: P3, P4, P1, P2; M4:
P4, P1, P2, P3; M5, all the same character: P1, P3, P2, P4). **Two SAVEs asked** (slots 2 and 3 empty, slot 1 holds a
save): the start → slot 2 (`begin`), the first results screen → slot 3 (`results_1`); no slot for `results_2`.
Before: 161 save files, T89's 4, no `.state8`; `launch_orphaned` 2; recovery log 2,354, bitrate 6,483 rows.

- **J — four seats:** the recovery log's `pad_slots` rows show four pads joined; the launch's `launch_ports` row shows
  four ports.
- **K — the pictures kept:** the keeper writes one picture a second from the launch to the END, **no gap over 3 s
  while the game runs** (gaps listed), each match's results screen inside the run (by the users' line times); its cost
  (grab and save ms, CPU) recorded.
- **S — the stream as a normal session's:** no stall (no `client_stall` row), no recovery act (`desync_pause`,
  `stall_handover_v2`, `encoder_restart`, `resumed`, `gave_up_saved`), no new `launch_orphaned`; **frames a second
  median ≥ 55** (the client's heartbeats / the bitrate samples); the bitrate's level and loss recorded beside PP-H3b's
  (four pads' uplink, recorded).
- **V — the SAVEs kept off the repo:** each SAVE the users made (the hub's own save row and the slot file's new hash)
  **copied, not moved**, with its picture, into `~/privyhub_h7/t89/` as `begin`, `results_1` with `SHA256SUMS`; the
  users' slots stay as they made them.
- **U — nothing else of the user's touched:** every other game's saves before = after (count and hashes); T89's files
  before + exactly the users' SAVEs after (slot 1 and the hub's own `.state` unchanged); no `.state8`; the drive and
  the profiles before = after. Recorded, not a cell: the game's in-game `.srm` (the game may write its own records) and
  the hub's slot index.
- **MET** = J, K, S, V (two SAVEs) and U. The finishing orders are recorded from the users' lines verbatim — labels to
  be, not cells; a match played otherwise is recorded as played.
