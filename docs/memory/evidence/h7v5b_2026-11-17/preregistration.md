# H7-V5b — pre-registration (hashed at step 9, before step 10; unattended; nothing perceptual; nothing adopted)

Task: `handoffs/H7-V5B_UNLOCKED_AGAIN_TASK.md` — B132's sketch (`SESSION_B_DONE_2026-11-17AT.md` §"H7-V5 again") on
B128's steps 1-20 with H7-V5's changes 4-6 and the new task's changes (12b on **slot 9**; T88 then T89 in one
companion). T88 = H7's 2-player PS1 title; T89 = the users' N64 four-player title; each under its cheat setup. Both
bench flags for the task only (twenty lines, back to eighteen). Before: 228 files, no `.state8`.

- **3-6:** the rules folder as H7-V5 left it (checked at stage 1, `pre/rules_check.md`).
- **10:** the board launched by the hub → `active`, `paused`; `bench-release` → released. **11:** `party-minigames` →
  two entries, 2 and 4 players.
- **12:** T88, seats 1,2 → `playing`; `minigame_launch` `"cheat": true, "profile_matches": true`; `status`
  `cheat_session.profile_id` T88's setup; `watching` **`"recognise_s": 15.0`, `"begin": "setup"`, loaded**; the load
  line naming `.state8` under T88's setup; **`recognised` true inside 15.0 s** (its `after_s` recorded); no
  `picture_failed` row.
- **12b:** `save-state?slot=9` → **400 "not during a mini game: nothing was saved"**; `load-state?slot=9` → **400 "not
  during a mini game: nothing was loaded"**; two `minigame_state_refused` rows (save, load; state playing); no "Saving
  state" / "Loading state" line from them; still `playing`; **T88's setup's files every sha256 = step 8's**.
- **13:** the kept end P1 by hand into T88's setup folder (the scratch removed at once) → **`ended`, `end_P1`, scores
  [1, 0] within 8 s**; the end → ended, RetroArch gone, `launch_kind` godot. **14:** seats 2,1 with end P2 → **`end_P2`,
  [0, 1]**; the end. **15:** seats 1,2 with the kept mid-fight → **still `playing` 45 s later, no `ended`**; the end →
  `given_up` "ended before a result (board)".
- **16:** T89, seats 1,2,3,4 → `playing`; `cheat` / `profile_matches` true; `watching` `"recognise_s": 15.0`, `"begin":
  "setup"`; **`recognised` true inside 15.0 s** (its `after_s` recorded); `picture_failed` rows recorded (any);
  `h7-result` `last` start distance recorded.
- **17:** paused (`GET_STATUS` PAUSED that second — else no load), the kept results_1 into T89's setup folder, the
  scratch removed at once, unpaused → **`ended`, class `end`, places [1, 2, 3, 4], scores [4, 3, 2, 1] within 8 s**;
  the end. **18:** seats 3,1,4,2 → **places [1, 2, 3, 4], scores [4, 3, 2, 1], seats [3, 1, 4, 2]**; the end.
- **19:** `stop` → the board quits by F10, exit 0; no board, Godot or RetroArch process left.
- **20:** both setups' slots and slot pictures and every normal state and save **before = after** (every sha256); no
  `.state8` (0 after each load). Recorded, not a cell: the setups' in-game saves, which differ.
- A `recognised` false → that title NOT MET with the cause named, no retry; the other title still run.
- **MET** = every one of 3-6, 10-12, 12b and 13-20. MET → PP-H4 may be offered; NOT MET → not.
