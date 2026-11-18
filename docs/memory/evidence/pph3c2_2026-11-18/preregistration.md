# PP-H3c (second try) — pre-registration (hashed before part 1; nothing perceptual; nothing adopted)

Task: `handoffs/PP-H3C_SOLO_TWO_PADS_TASK.md` — B138's §PP-H3c (`SESSION_B_DONE_2026-11-17AV.md`) with B142's rows
(`SESSION_B_DONE_2026-11-17AW.md`) and Cowork's changes 1-8. T88 = H7's 2-player PS1 title under "T88's cheat setup".
One person, two pads paired to the onn. Both bench flags for the task only.

**The second try** (the first, `PP_H3C_2026-11-18.md`, stopped by the user at the adb question after part 1 was met).
**Stage 1 (read before this hash, 03:32Z):** the window; H7-V6b's and the stopped PP-H3c records committed (`d57e5836`);
this repo's ten greps 1 each; the board's repo clean at `4140949`, `f8d92e38` its ancestor, the five methods 5,
`game/minigame_screens.gd` there, `hub_minigame.gd` `e580c3e1…`, `hub_minigame_check.gd` `76018a20…`, `first_here` 1;
**adb: the onn a `device`; `--check` ok, the APK `ca53df0d…` CONFIRMED.** Nothing of part 1 before this hash.

**Part 1 — the gate:** (a) in a scratch copy of the board's tree, Godot headless: `checks/hub_minigame_check.gd` PASS
(81) and `checks/step25_before_minigame.gd` PASS; (b) the rules folder as H7-V5b left it (read only); (c) before: cell
U's files (count, every sha256), no `.state8`, the rows' line counts; (d) both drop-ins, twenty lines; (e) one held T88
start on the bench (the board launched and released, `bench=1`): `ready` (the two keys after the launch, a
frame-advance row `"changed": true, "paused": true`, no `label_mask`, `PAUSED` every second from the watch row to the
go) → the go → `playing`, no `minigame_reloaded` → the kept end P1 by hand → `end_P1` [1, 0] → the end; the board
closed. **Not met → no line asks the user to pick up a pad.**

**The streamed self-proof** (part 2, on the user's "ready", no `bench`): `ready` with the frame-advance row, **no
`minigame_route` / `minigame_stream` before the go**, `PAUSED` every second, the stream's last `Capture:` line still
the board's window; the go → `minigame_stream` `"switched": true, "planned": true` → `playing`; at once
`party-minigame-end` → the board back (`minigame_stream` board `"switched": true`). Not met → no play.

**The cells (MET = part 1 with the self-proof and all of these):**
- **F** — at all three load screens, `PAUSED` at every paused-proof second from the watch row to the go; no
  `minigame_reloaded` at any go.
- **R** — `recognised` true for each preparation (none given up).
- **S** — one card (the board's log); `minigame_start` with the two-player token.
- **PS / PT** — `minigame_practice_end` `"by": "start_button"`, then `"by": "time"` with `practice_s` ≥ 90; no
  `minigame_ended` between a practice's go and its end.
- **M** — the real match: `minigame_ended` with an end class and its scores, and the board's log crediting that seat.
- **H** — Home / RESUME: `minigame_taken` home / resume, the mini game still `playing` after, then ended as M.
- **E** — END: everything ended; `status` idle.
- **W** — every party launch's config carries `video_font_enable = "false"` and `menu_show_load_content_animation =
  "false"`.
- **U** — the setups' slots and slot pictures and every normal state and save before = after (every sha256); the
  setups' in-game saves recorded before and after, not a cell.

**Recorded, no bar:** each `prepare_s`, `held_s`, `frames`, `mute_ms`; the user's words (change 6's one question);
the window's pictures through every preparation into the git-ignored `runtime/pph3c_frames/`.
