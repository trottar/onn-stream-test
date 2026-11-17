# H7-C2 — pre-registration (hashed at the end of stage 1, before the first launch; nothing perceptual; nothing adopted)

Task: `handoffs/H7-C2_UNLOCKED_SCREENS_CAPTURE_TASK.md`. T88 = H7's 2-player PS1 title; T89 = the users' N64
four-player title. Unattended: no user, no onn, no pads; nothing pressed in a game. Bench flag `PRIVYHUB_H7=1` for the
task only (nineteen lines, back to eighteen). Per title, T88 first: the launch with its cheat setup by
`POST launch?id=…&cheat_source=…&cheat_indexes=…` (the onn's own call, from `cheat-profiles`) → the users' cheat slot 1
by hand into scratch slot 8 of the setup's `states/<core>/` (N64 only after `GET_STATUS` PAUSED) → `bench-release` →
40 s; then by hand (N64: `PAUSE_TOGGLE`, PAUSED, load, `PAUSE_TOGGLE` back) — T88: end P1 → 40 s, end P2 → 40 s,
mid-fight → 20 s; T89: results_1 → 40 s, begin → 20 s; then `stop`. Before: 173 save-state files, no `.state8`.

- **L — the launches:** each title launched with its cheat setup from loopback (the call's answer and the session's
  own row naming the setup — its `profile_id`), stopped at the end; nothing left running.
- **D — the loads:** every load above answered (`LOAD_STATE_SLOT 8`) and its load line in RetroArch's session log;
  no N64 load sent to a core not answering `PAUSED`; every scratch copy removed.
- **K — the pictures:** one a second through each run with no gap over 3 s while the game runs; each load's stretch
  inside its run (counts per stretch).
- **U — nothing of the users' touched:** every save-state file under the states root and every cheat setup's folder
  before = after (count and sha256); no `.state8` left anywhere; the in-game saves recorded (not cells).
- **MET** = L, D, K and U. What the screens show (the select screen's grid unlocked or locked on each loaded screen) is
  recorded in words for Cowork's labels — not a cell.
