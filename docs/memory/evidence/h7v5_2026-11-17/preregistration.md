# H7-V5 — pre-registration (hashed at step 9, before step 10; unattended; nothing perceptual; nothing adopted)

Task: `handoffs/H7-V5_UNLOCKED_UNATTENDED_TASK.md` — B128's steps 1-20 (`SESSION_B_DONE_2026-11-17AS.md` §"H7-V5")
with Cowork's six changes. T88 = H7's 2-player PS1 title; T89 = the users' N64 four-player title; each under its
cheat setup with the users' slot 1 as the begin, from the board's own mini-game routes on B112's bench. Both bench
flags for the task only (twenty lines, back to eighteen).

- **3-4 (stage 1, already read):** both specs learnt equal to `h7v5_expected/` number for number; the scores and the
  replays' end lines the same (`pre/learn_and_score.md`). **5-6:** the begins copied (before = after = the copy); the
  sidecars written, nothing overwritten (renamed aside, listed).
- **10:** the board launched by the hub → `active`, `paused`; `bench-release` → released.
- **11:** `party-minigames` → **two entries, `"players"` 2 and 4**.
- **12:** T88, seats 1,2 → `playing`, **`recognised` true within 20 s of the start**; `status` `cheat_session.profile_id`
  = T88's setup; `minigame_launch` **`"cheat": true, "profile_matches": true`**; `h7_results` `watching` **`"begin":
  "setup"`, `"loaded": true`**; RetroArch's load line naming `.state8` under T88's setup's `states/`. **The seconds from
  the load to `recognised` recorded.** A `recognised` false → T88 stopped there (`party-minigame-end`), NOT MET with the
  cause named, no retry; T89 still run.
- **13:** the kept end P1 by hand into T88's setup folder → **`ended`, `end_P1`, `"scores": [1, 0]` within 8 s**; the
  end → `"ended": true`, RetroArch gone, `launch_kind` godot.
- **14:** seats 2,1 with the kept end P2 → **`end_P2`, `"scores": [0, 1]`**; the end.
- **15:** seats 1,2 with the kept mid-fight → **still `playing` 45 s later, no `ended`**; the end → `given_up` "ended
  before a result (board)".
- **16:** T89, seats 1,2,3,4 → `playing`, **`recognised` true within 20 s** (the seconds recorded); `cheat_session`
  T89's setup; `minigame_launch` `"cheat": true, "profile_matches": true`; `watching` `"begin": "setup"`. A `recognised`
  false → as 12.
- **17:** paused (`PAUSE_TOGGLE`, **`GET_STATUS` PAUSED that second — else no load**), the kept results_1 into T89's
  setup folder, `LOAD_STATE_SLOT 8`, the scratch removed, `PAUSE_TOGGLE` → **`ended`, class `end`, `"places": [1, 2, 3,
  4]`, `"scores": [4, 3, 2, 1]` within 8 s**; the end.
- **18:** seats 3,1,4,2, the same → **`"places": [1, 2, 3, 4]`, `"scores": [4, 3, 2, 1]`, `"seats": [3, 1, 4, 2]`**; the
  end.
- **19:** `stop` → the board quits by F10, exit code 0; no board, Godot or RetroArch process left.
- **20 (change 5):** **the cell** — both setups' slots and slot pictures, and every normal state and save, **before =
  after** (every sha256); **no `.state8` anywhere**, and 0 after each load. **Recorded, not a cell** — the setups' in-game
  saves before and after, which differ (each mini game's stop flushes them, B127).
- **MET** = every one of 3-6 and 10-20. MET → PP-H4 may be offered; NOT MET → it is not.
